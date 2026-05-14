"""风险检测引擎单元测试"""
import pytest
from datetime import datetime, timedelta

from app.models.transport import TransportRecord, RecordStatus
from app.models.alert import AlertType, Severity
from app.services.weight_analyzer import WeightAnalyzer, AlertData
from app.services.time_analyzer import TimeAnalyzer
from app.services.seal_analyzer import SealAnalyzer
from app.services.risk_engine import RiskEngine


# ---- 辅助工厂函数 ----

def make_transport(
    departure_net=30000.0,
    arrival_net=30000.0,
    duration_minutes=240,
    departure_time=None,
) -> TransportRecord:
    """创建测试用运输记录"""
    if departure_time is None:
        departure_time = datetime.utcnow() - timedelta(hours=5)
    arrival_time = departure_time + timedelta(minutes=duration_minutes)

    t = TransportRecord.__new__(TransportRecord)
    t.id = 1
    t.vehicle_id = 1
    t.departure_net_weight = departure_net
    t.arrival_net_weight = arrival_net
    t.departure_time = departure_time
    t.arrival_time = arrival_time
    t.weight_diff = round(arrival_net - departure_net, 2)
    t.weight_diff_ratio = round((arrival_net - departure_net) / departure_net, 6)
    t.transport_duration = duration_minutes
    return t


# ---- WeightAnalyzer 测试 ----

class TestWeightAnalyzer:
    """重量分析器测试"""

    def test_normal_weight_no_alert(self):
        """正常偏差应无预警"""
        analyzer = WeightAnalyzer()
        transport = make_transport(departure_net=30000, arrival_net=30010)
        alerts = analyzer.analyze(transport, [])
        weight_alerts = [a for a in alerts if a.alert_type in (AlertType.WEIGHT_SHORTAGE, AlertType.WEIGHT_OVERAGE)]
        assert len(weight_alerts) == 0

    def test_shortage_severe_alert(self):
        """亏吨超过3‰应触发严重预警"""
        analyzer = WeightAnalyzer()
        # 亏吨 5‰ (远超3‰)
        departure_net = 30000
        arrival_net = 30000 * (1 - 0.005)  # 29850
        transport = make_transport(departure_net=departure_net, arrival_net=arrival_net)
        alerts = analyzer.analyze(transport, [])
        severe = [a for a in alerts if a.severity == Severity.SEVERE]
        assert len(severe) >= 1
        assert severe[0].alert_type == AlertType.WEIGHT_SHORTAGE

    def test_overage_general_alert(self):
        """盈吨超过3‰应触发一般预警"""
        analyzer = WeightAnalyzer()
        # 盈吨 5‰
        departure_net = 30000
        arrival_net = 30000 * (1 + 0.005)  # 30150
        transport = make_transport(departure_net=departure_net, arrival_net=arrival_net)
        alerts = analyzer.analyze(transport, [])
        general = [a for a in alerts if a.severity == Severity.GENERAL]
        assert len(general) >= 1
        assert general[0].alert_type == AlertType.WEIGHT_OVERAGE

    def test_no_alert_within_threshold(self):
        """3‰以内应无预警"""
        analyzer = WeightAnalyzer()
        departure_net = 30000
        arrival_net = 30000 * (1 + 0.002)  # 2‰, 在阈值内
        transport = make_transport(departure_net=departure_net, arrival_net=arrival_net)
        alerts = analyzer.analyze(transport, [])
        assert len(alerts) == 0


# ---- TimeAnalyzer 测试 ----

class TestTimeAnalyzer:
    """时间分析器测试"""

    def test_normal_time_no_alert(self):
        """正常时长应无预警"""
        analyzer = TimeAnalyzer()
        transport = make_transport(duration_minutes=240)  # 4小时
        alerts = analyzer.analyze(transport, [])
        time_alerts = [a for a in alerts if a.alert_type == AlertType.TIME_EXCESSIVE]
        assert len(time_alerts) == 0

    def test_severe_overtime_alert(self):
        """超时超过60分钟应触发严重预警"""
        analyzer = TimeAnalyzer()
        # 默认基准240分钟，这里设置340分钟（超100分钟）
        transport = make_transport(duration_minutes=340)
        alerts = analyzer.analyze(transport, [])
        severe = [a for a in alerts if a.severity == Severity.SEVERE]
        assert len(severe) >= 1

    def test_general_overtime_alert(self):
        """超时30-60分钟应触发一般预警"""
        analyzer = TimeAnalyzer()
        # 240 + 45 = 285分钟
        transport = make_transport(duration_minutes=285)
        alerts = analyzer.analyze(transport, [])
        general = [a for a in alerts if a.severity == Severity.GENERAL]
        assert len(general) >= 1


# ---- SealAnalyzer 测试 ----

class TestSealAnalyzer:
    """铅封分析器测试"""

    def test_matching_seals_no_alert(self):
        """匹配的铅封应无预警"""
        analyzer = SealAnalyzer()
        alerts = analyzer.analyze("SEAL-001", "SEAL-001", True, True)
        assert len(alerts) == 0

    def test_mismatch_severe_alert(self):
        """不匹配的铅封应触发严重预警"""
        analyzer = SealAnalyzer()
        alerts = analyzer.analyze("SEAL-001", "SEAL-999", True, True)
        severe = [a for a in alerts if a.severity == Severity.SEVERE]
        assert len(severe) >= 1
        assert severe[0].alert_type == AlertType.SEAL_MISMATCH

    def test_damaged_seal_general_alert(self):
        """铅封损坏应触发一般预警"""
        analyzer = SealAnalyzer()
        alerts = analyzer.analyze("SEAL-001", "SEAL-001", False, True)
        general = [a for a in alerts if a.severity == Severity.GENERAL]
        assert len(general) >= 1

    def test_missing_qr_alert(self):
        """QR码缺失应触发预警"""
        analyzer = SealAnalyzer()
        alerts = analyzer.analyze(None, "SEAL-001", True, True)
        assert len(alerts) >= 1

    def test_similarity_calculation(self):
        """测试Levenshtein相似度计算"""
        assert SealAnalyzer._calculate_similarity("abc", "abc") == 1.0
        assert SealAnalyzer._calculate_similarity("abc", "abd") > 0.5
        assert SealAnalyzer._calculate_similarity("abc", "xyz") < 0.5


# ---- RiskEngine 综合评分测试 ----

class TestRiskEngine:
    """风险引擎综合评分测试"""

    def test_no_alerts_zero_score(self):
        """无预警应评分为0"""
        engine = RiskEngine()
        score = engine.compute_risk_score([])
        assert score == 0.0

    def test_severe_alert_higher_score(self):
        """严重预警应比一般预警得分更高"""
        engine = RiskEngine()
        from app.models.alert import Alert

        general_alert = Alert.__new__(Alert)
        general_alert.alert_type = AlertType.WEIGHT_SHORTAGE
        general_alert.severity = Severity.GENERAL

        severe_alert = Alert.__new__(Alert)
        severe_alert.alert_type = AlertType.WEIGHT_SHORTAGE
        severe_alert.severity = Severity.SEVERE

        general_score = engine.compute_risk_score([general_alert])
        severe_score = engine.compute_risk_score([severe_alert])
        assert severe_score > general_score

    def test_multiple_alerts_cumulative(self):
        """多个预警应累积评分"""
        engine = RiskEngine()
        from app.models.alert import Alert

        alerts = []
        for atype, sev in [
            (AlertType.WEIGHT_SHORTAGE, Severity.SEVERE),
            (AlertType.TIME_EXCESSIVE, Severity.GENERAL),
            (AlertType.SEAL_MISMATCH, Severity.SEVERE),
        ]:
            a = Alert.__new__(Alert)
            a.alert_type = atype
            a.severity = sev
            alerts.append(a)

        score = engine.compute_risk_score(alerts)
        # 0.4*2 + 0.3*1 + 0.3*2 = 0.8 + 0.3 + 0.6 = 1.7
        assert score == 1.7
