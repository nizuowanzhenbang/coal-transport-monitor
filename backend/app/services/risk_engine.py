"""风险检测引擎：协调三大分析器，生成预警记录，计算综合风险评分"""
from typing import List
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.transport import TransportRecord, RecordStatus
from app.models.alert import Alert, AlertType, Severity
from app.models.seal import SealRecord, SealType
from app.models.vehicle import Vehicle
from app.services.weight_analyzer import WeightAnalyzer, AlertData
from app.services.time_analyzer import TimeAnalyzer
from app.services.seal_analyzer import SealAnalyzer


class RiskEngine:
    """
    综合风险检测引擎

    职责：
    1. 协调重量、时间、铅封三大分析器
    2. 将分析器返回的AlertData持久化为数据库Alert记录
    3. 更新运输记录的状态（NORMAL/ALERT/SEVERE）
    4. 计算综合风险评分

    风险评分公式：
        score = Σ(alert_weight × severity_factor)
    权重：重量0.4，时间0.3，铅封0.3
    系数：一般预警1.0，严重预警2.0
    """

    # 各类型预警的权重
    TYPE_WEIGHTS = {
        AlertType.WEIGHT_SHORTAGE: 0.4,
        AlertType.WEIGHT_OVERAGE: 0.4,
        AlertType.TIME_EXCESSIVE: 0.3,
        AlertType.SEAL_MISMATCH: 0.3,
        AlertType.SEAL_DAMAGED: 0.3,
    }

    # 严重程度系数
    SEVERITY_FACTORS = {
        Severity.GENERAL: 1.0,
        Severity.SEVERE: 2.0,
    }

    # 累计严重预警次数阈值，超过则高亮
    HIGHLIGHT_THRESHOLD = 3

    def __init__(self):
        self.weight_analyzer = WeightAnalyzer()
        self.time_analyzer = TimeAnalyzer()
        self.seal_analyzer = SealAnalyzer()

    def evaluate(
        self,
        transport: TransportRecord,
        db: Session,
    ) -> List[Alert]:
        """
        对一条运输记录执行完整的风险评估。

        流程：
        1. 获取该车辆的历史记录用于动态阈值计算
        2. 运行三大分析器
        3. 持久化预警记录
        4. 更新运输记录状态

        参数：
            transport: 待评估的运输记录
            db: 数据库会话

        返回：
            生成的Alert列表
        """
        # 获取同车辆的历史记录（排除当前记录）
        historical = (
            db.query(TransportRecord)
            .filter(
                TransportRecord.vehicle_id == transport.vehicle_id,
                TransportRecord.id != transport.id,
                TransportRecord.arrival_net_weight.isnot(None),
            )
            .order_by(TransportRecord.created_at.desc())
            .limit(100)
            .all()
        )

        # 获取铅封信息
        dep_seal = db.query(SealRecord).filter(SealRecord.id == transport.departure_seal_id).first()
        arr_seal = db.query(SealRecord).filter(SealRecord.id == transport.arrival_seal_id).first()

        # 收集所有分析器的预警数据
        all_alert_data: List[AlertData] = []

        # 1. 重量分析
        weight_alerts = self.weight_analyzer.analyze(transport, historical)
        all_alert_data.extend(weight_alerts)

        # 2. 时间分析
        time_alerts = self.time_analyzer.analyze(transport, historical)
        all_alert_data.extend(time_alerts)

        # 3. 铅封分析
        dep_qr = dep_seal.qr_code if dep_seal else None
        arr_qr = arr_seal.qr_code if arr_seal else None
        dep_valid = dep_seal.is_valid if dep_seal else True
        arr_valid = arr_seal.is_valid if arr_seal else True
        seal_alerts = self.seal_analyzer.analyze(dep_qr, arr_qr, dep_valid, arr_valid)
        all_alert_data.extend(seal_alerts)

        # 持久化预警记录
        created_alerts: List[Alert] = []
        for alert_data in all_alert_data:
            alert = Alert(
                transport_id=transport.id,
                alert_type=alert_data.alert_type,
                severity=alert_data.severity,
                description=alert_data.description,
                threshold_value=alert_data.threshold_value,
                actual_value=alert_data.actual_value,
            )
            db.add(alert)
            created_alerts.append(alert)

        # 更新运输记录状态
        if created_alerts:
            has_severe = any(a.severity == Severity.SEVERE for a in created_alerts)
            transport.status = RecordStatus.SEVERE if has_severe else RecordStatus.ALERT
            transport.alert_count = (transport.alert_count or 0) + len(created_alerts)

            # 累计严重预警检查
            severe_count = (
                db.query(Alert)
                .join(TransportRecord)
                .filter(
                    TransportRecord.vehicle_id == transport.vehicle_id,
                    Alert.severity == Severity.SEVERE,
                )
                .count()
            )
            transport.notes = (transport.notes or "") + f"\n累计严重预警: {severe_count}次"
        else:
            transport.status = RecordStatus.NORMAL

        db.commit()

        # 刷新获取ID
        for alert in created_alerts:
            db.refresh(alert)

        return created_alerts

    def compute_risk_score(self, alerts: List[Alert]) -> float:
        """
        计算综合风险评分。

        公式：score = Σ(type_weight × severity_factor)

        返回值范围：0.0 ~ 理论上限约2.0
        """
        if not alerts:
            return 0.0

        score = 0.0
        for alert in alerts:
            weight = self.TYPE_WEIGHTS.get(alert.alert_type, 0.2)
            factor = self.SEVERITY_FACTORS.get(alert.severity, 1.0)
            score += weight * factor

        return round(score, 2)
