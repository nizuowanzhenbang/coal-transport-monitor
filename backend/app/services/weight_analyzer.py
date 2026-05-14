"""重量异常分析器：检测运煤运输过程中的重量亏损和盈余异常"""
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

from app.models.alert import AlertType, Severity
from app.config import settings


@dataclass
class AlertData:
    """分析器返回的预警数据（尚未写入数据库）"""
    alert_type: AlertType
    severity: Severity
    description: str
    threshold_value: float
    actual_value: float


class WeightAnalyzer:
    """
    重量异常检测器

    判定规则：
    - 亏吨：(出港净重 - 进厂净重) / 出港净重 > 3‰ → 严重预警
    - 盈吨：(进厂净重 - 出港净重) / 出港净重 > 3‰ → 一般预警

    进阶：动态阈值（Z-score）
    - 基于历史同路线运输的偏差率分布，计算均值μ和标准差σ
    - 偏差超过 μ-3σ 或 μ+3σ → 严重预警（动态）
    - 偏差超过 μ-2σ 或 μ+2σ → 一般预警（动态）
    - 固定阈值与动态阈值取较严格者（更容易触发预警的那个）
    """

    WEIGHT_THRESHOLD = settings.WEIGHT_DIFF_THRESHOLD          # 3‰
    K_GENERAL = settings.WEIGHT_DYNAMIC_K_GENERAL              # 2σ
    K_SEVERE = settings.WEIGHT_DYNAMIC_K_SEVERE                # 3σ
    MIN_HISTORY = settings.MIN_HISTORICAL_SIZE                  # 至少10条历史记录

    def analyze(
        self,
        transport,
        historical_records: List,
    ) -> List[AlertData]:
        """
        分析运输记录的重量偏差。

        参数：
            transport: TransportRecord 对象
            historical_records: 同路线的历史运输记录列表

        返回：
            AlertData 列表（可为空）
        """
        alerts: List[AlertData] = []

        # 数据完整性检查
        dep_net = transport.departure_net_weight
        arr_net = transport.arrival_net_weight
        if not dep_net or dep_net <= 0 or arr_net is None:
            return alerts

        ratio = transport.weight_diff_ratio
        if ratio is None:
            ratio = (arr_net - dep_net) / dep_net

        # ---- 固定阈值检测 ----
        if ratio < -self.WEIGHT_THRESHOLD:
            # 亏吨超过3‰，属于严重预警
            alerts.append(
                AlertData(
                    alert_type=AlertType.WEIGHT_SHORTAGE,
                    severity=Severity.SEVERE,
                    description=(
                        f"重量亏损超过固定阈值！"
                        f"出港净重 {dep_net:.1f}kg，进厂净重 {arr_net:.1f}kg，"
                        f"偏差率 {ratio * 1000:.2f}‰，超过阈值 3‰"
                    ),
                    threshold_value=-self.WEIGHT_THRESHOLD,
                    actual_value=ratio,
                )
            )
        elif ratio > self.WEIGHT_THRESHOLD:
            # 盈吨超过3‰，属于一般预警（存在替换货物或测量误差嫌疑）
            alerts.append(
                AlertData(
                    alert_type=AlertType.WEIGHT_OVERAGE,
                    severity=Severity.GENERAL,
                    description=(
                        f"重量盈余超过固定阈值！"
                        f"出港净重 {dep_net:.1f}kg，进厂净重 {arr_net:.1f}kg，"
                        f"偏差率 +{ratio * 1000:.2f}‰，超过阈值 3‰"
                    ),
                    threshold_value=self.WEIGHT_THRESHOLD,
                    actual_value=ratio,
                )
            )

        # ---- 动态阈值检测（Z-score）----
        valid_ratios = [
            r.weight_diff_ratio
            for r in historical_records
            if r.weight_diff_ratio is not None
        ]

        if len(valid_ratios) >= self.MIN_HISTORY:
            arr = np.array(valid_ratios, dtype=float)
            mu = float(np.mean(arr))
            sigma = float(np.std(arr))

            if sigma > 1e-8:  # 避免除以零
                z_score = (ratio - mu) / sigma

                # 动态严重阈值（3σ以外）
                if z_score < -self.K_SEVERE:
                    dyn_threshold = mu - self.K_SEVERE * sigma
                    # 仅在固定阈值未触发严重预警时补充
                    if not any(
                        a.alert_type == AlertType.WEIGHT_SHORTAGE
                        and a.severity == Severity.SEVERE
                        for a in alerts
                    ):
                        alerts.append(
                            AlertData(
                                alert_type=AlertType.WEIGHT_SHORTAGE,
                                severity=Severity.SEVERE,
                                description=(
                                    f"重量亏损统计异常！Z-score={z_score:.2f}，"
                                    f"偏差率 {ratio * 1000:.2f}‰ 超过历史 {self.K_SEVERE}σ 界限 "
                                    f"({dyn_threshold * 1000:.2f}‰)"
                                ),
                                threshold_value=dyn_threshold,
                                actual_value=ratio,
                            )
                        )
                elif z_score < -self.K_GENERAL:
                    dyn_threshold = mu - self.K_GENERAL * sigma
                    # 仅在固定阈值未触发亏吨预警时补充
                    if not any(a.alert_type == AlertType.WEIGHT_SHORTAGE for a in alerts):
                        alerts.append(
                            AlertData(
                                alert_type=AlertType.WEIGHT_SHORTAGE,
                                severity=Severity.GENERAL,
                                description=(
                                    f"重量偏低（动态预警）！Z-score={z_score:.2f}，"
                                    f"偏差率 {ratio * 1000:.2f}‰ 超过历史 {self.K_GENERAL}σ 界限 "
                                    f"({dyn_threshold * 1000:.2f}‰)"
                                ),
                                threshold_value=dyn_threshold,
                                actual_value=ratio,
                            )
                        )
                elif z_score > self.K_SEVERE:
                    dyn_threshold = mu + self.K_SEVERE * sigma
                    if not any(
                        a.alert_type == AlertType.WEIGHT_OVERAGE
                        and a.severity == Severity.SEVERE
                        for a in alerts
                    ):
                        alerts.append(
                            AlertData(
                                alert_type=AlertType.WEIGHT_OVERAGE,
                                severity=Severity.SEVERE,
                                description=(
                                    f"重量盈余统计异常！Z-score={z_score:.2f}，"
                                    f"偏差率 +{ratio * 1000:.2f}‰ 超过历史 {self.K_SEVERE}σ 界限 "
                                    f"({dyn_threshold * 1000:.2f}‰)"
                                ),
                                threshold_value=dyn_threshold,
                                actual_value=ratio,
                            )
                        )

        return alerts
