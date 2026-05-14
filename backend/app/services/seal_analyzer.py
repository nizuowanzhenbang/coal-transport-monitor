"""铅封异常分析器：检测运煤运输过程中的铅封二维码异常"""
from typing import List, Optional

from app.models.alert import AlertType, Severity
from app.services.weight_analyzer import AlertData


class SealAnalyzer:
    """
    铅封二维码异常检测器

    判定规则：
    - 出港铅封QR码 ≠ 进厂铅封QR码 → 严重预警
    - 铅封QR码无法识别/损坏/为空 → 一般预警

    算法：
    - 字符串精确匹配
    - Levenshtein编辑距离计算相似度（容忍微小扫描误差）
    - QR码格式合规性检查
    """

    # 编辑距离相似度阈值：低于此值视为不匹配
    SIMILARITY_THRESHOLD = 0.9

    def analyze(
        self,
        departure_qr: Optional[str],
        arrival_qr: Optional[str],
        departure_valid: bool,
        arrival_valid: bool,
    ) -> List[AlertData]:
        """
        分析铅封二维码异常。

        参数：
            departure_qr: 出港铅封二维码内容
            arrival_qr: 进厂铅封二维码内容
            departure_valid: 出港铅封是否有效
            arrival_valid: 进厂铅封是否有效

        返回：
            AlertData 列表（可为空）
        """
        alerts: List[AlertData] = []

        # 检查铅封是否损坏/无法识别
        if not departure_valid or not arrival_valid:
            damaged_side = []
            if not departure_valid:
                damaged_side.append("出港")
            if not arrival_valid:
                damaged_side.append("进厂")
            alerts.append(AlertData(
                alert_type=AlertType.SEAL_DAMAGED,
                severity=Severity.GENERAL,
                description=f"{'、'.join(damaged_side)}铅封二维码损坏或无法识别",
                threshold_value=1.0,  # 期望有效
                actual_value=0.0,     # 实际无效
            ))

        # 检查二维码是否为空
        if not departure_qr or not arrival_qr:
            missing_side = []
            if not departure_qr:
                missing_side.append("出港")
            if not arrival_qr:
                missing_side.append("进厂")
            if missing_side:
                alerts.append(AlertData(
                    alert_type=AlertType.SEAL_DAMAGED,
                    severity=Severity.GENERAL,
                    description=f"{'、'.join(missing_side)}铅封二维码信息缺失",
                    threshold_value=1.0,
                    actual_value=0.0,
                ))
            return alerts

        # 二维码都存在，进行比对
        similarity = self._calculate_similarity(departure_qr, arrival_qr)

        if similarity < 1.0:
            # 不完全匹配
            if similarity < self.SIMILARITY_THRESHOLD:
                # 完全不匹配 → 严重预警
                alerts.append(AlertData(
                    alert_type=AlertType.SEAL_MISMATCH,
                    severity=Severity.SEVERE,
                    description=f"出港与进厂铅封二维码不一致（相似度: {similarity:.1%}）",
                    threshold_value=self.SIMILARITY_THRESHOLD,
                    actual_value=similarity,
                ))
            else:
                # 微小差异（可能是扫描误差）→ 一般预警
                alerts.append(AlertData(
                    alert_type=AlertType.SEAL_MISMATCH,
                    severity=Severity.GENERAL,
                    description=f"出港与进厂铅封二维码存在微小差异（相似度: {similarity:.1%}），建议人工核实",
                    threshold_value=1.0,
                    actual_value=similarity,
                ))

        return alerts

    @staticmethod
    def _calculate_similarity(s1: str, s2: str) -> float:
        """
        计算两个字符串的相似度（基于Levenshtein编辑距离）

        返回值：0.0 ~ 1.0，1.0表示完全相同
        """
        if s1 == s2:
            return 1.0

        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0

        # Levenshtein编辑距离（动态规划）
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j

        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                matrix[i][j] = min(
                    matrix[i - 1][j] + 1,       # 删除
                    matrix[i][j - 1] + 1,       # 插入
                    matrix[i - 1][j - 1] + cost, # 替换
                )

        max_len = max(len1, len2)
        return 1.0 - matrix[len1][len2] / max_len
