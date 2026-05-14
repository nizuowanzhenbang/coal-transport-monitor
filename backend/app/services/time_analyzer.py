"""时间异常分析器：检测运煤运输过程中的超时异常"""
from typing import List

import numpy as np

from app.models.alert import AlertType, Severity
from app.services.weight_analyzer import AlertData
from app.config import settings


class TimeAnalyzer:
    """
    运输时间异常检测器

    判定规则：
    - 超时超过基准 + 60min → 严重预警
    - 超时超过基准 + 30min → 一般预警

    基准时长计算（历史中位数 + IQR去极值）：
    - 收集同路线最近N条记录的运输时长
    - 用IQR方法剔除极端值后取中位数作为基准
    - 历史数据不足时使用默认基准值
    """

    GENERAL_OVERTIME = settings.TIME_GENERAL_OVERTIME_MINUTES   # 30分钟
    SEVERE_OVERTIME = settings.TIME_SEVERE_OVERTIME_MINUTES     # 60分钟
    DEFAULT_BASELINE = settings.TIME_DEFAULT_BASELINE_MINUTES   # 240分钟
    MIN_HISTORY = settings.MIN_HISTORICAL_SIZE                   # 最少10条

    def analyze(self, transport, historical_records: List) -> List[AlertData]:
        """
        分析运输时长是否超时。

        参数：
            transport: TransportRecord 对象
            historical_records: 同路线历史运输记录列表

        返回：
            AlertData 列表（可为空）
        """
        alerts: List[AlertData] = []

        duration = transport.transport_duration
        if duration is None:
            return alerts

        # 计算历史基准时长
        baseline = self._calculate_baseline(historical_records)
        overtime = duration - baseline

        if overtime > self.SEVERE_OVERTIME:
            # 超时超过60分钟 → 严重预警
            alerts.append(
                AlertData(
                    alert_type=AlertType.TIME_EXCESSIVE,
                    severity=Severity.SEVERE,
                    description=(
                        f"运输时间严重超时！"
                        f"实际耗时 {duration} 分钟，路线基准 {baseline} 分钟，"
                        f"超出 {overtime} 分钟（严重阈值：{self.SEVERE_OVERTIME} 分钟）"
                    ),
                    threshold_value=float(baseline + self.SEVERE_OVERTIME),
                    actual_value=float(duration),
                )
            )
        elif overtime > self.GENERAL_OVERTIME:
            # 超时超过30分钟 → 一般预警
            alerts.append(
                AlertData(
                    alert_type=AlertType.TIME_EXCESSIVE,
                    severity=Severity.GENERAL,
                    description=(
                        f"运输时间超时！"
                        f"实际耗时 {duration} 分钟，路线基准 {baseline} 分钟，"
                        f"超出 {overtime} 分钟（一般阈值：{self.GENERAL_OVERTIME} 分钟）"
                    ),
                    threshold_value=float(baseline + self.GENERAL_OVERTIME),
                    actual_value=float(duration),
                )
            )

        return alerts

    def _calculate_baseline(self, historical_records: List) -> int:
        """
        使用中位数 + IQR方法计算路线基准运输时长。

        IQR（四分位距）方法：
        1. 计算Q1（25%分位数）和Q3（75%分位数）
        2. IQR = Q3 - Q1
        3. 剔除 [Q1-1.5*IQR, Q3+1.5*IQR] 范围之外的极端值
        4. 对剩余数据取中位数
        """
        if not historical_records:
            return self.DEFAULT_BASELINE

        valid_durations = [
            r.transport_duration
            for r in historical_records
            if r.transport_duration is not None and r.transport_duration > 0
        ]

        if len(valid_durations) < self.MIN_HISTORY:
            # 历史数据不足，使用默认基准
            if valid_durations:
                return int(np.median(valid_durations))
            return self.DEFAULT_BASELINE

        arr = np.array(valid_durations, dtype=float)
        q1 = np.percentile(arr, 25)
        q3 = np.percentile(arr, 75)
        iqr = q3 - q1

        # IQR法剔除异常值（中途停车等极端情况不纳入基准计算）
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        filtered = arr[(arr >= lower) & (arr <= upper)]

        if len(filtered) == 0:
            return int(np.median(arr))

        return int(np.median(filtered))
