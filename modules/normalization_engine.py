# normalization_engine.py


"""
BRN Normalization Engine

각 지표를 0~100 점수로 변환한다.
"""

from __future__ import annotations


class NormalizationEngine:
    """
    각 Indicator를 0~100 점수로 변환
    """

    @staticmethod
    def clamp(score: float) -> float:
        """0~100 범위 제한"""
        return round(max(0.0, min(100.0, score)), 2)

    @staticmethod
    def identity(value: float) -> float:
        """
        이미 0~100 범위인 값
        """
        return NormalizationEngine.clamp(value)

    @staticmethod
    def reverse(value: float) -> float:
        """
        값이 낮을수록 좋은 지표
        (미분양, PF, 공실률 등)
        """
        return NormalizationEngine.clamp(100.0 - value)

    @staticmethod
    def percentage(value: float) -> float:
        """
        일반 퍼센트
        """
        return NormalizationEngine.clamp(value)

    @staticmethod
    def jeonse_ratio(value: float) -> float:
        """
        전세가율

        60~70%를 가장 좋은 구간으로 평가
        """

        if value < 40:
            score = 20

        elif value < 50:
            score = 40

        elif value < 60:
            score = 70

        elif value <= 70:
            score = 100

        elif value <= 80:
            score = 80

        elif value <= 90:
            score = 60

        else:
            score = 40

        return NormalizationEngine.clamp(score)

    @staticmethod
    def interest_rate(rate: float) -> float:
        """
        기준금리

        낮을수록 높은 점수
        """

        score = 100 - (rate * 15)

        return NormalizationEngine.clamp(score)

    @staticmethod
    def auction_rate(value: float) -> float:
        """
        경매 낙찰가율
        """

        score = value * 2

        return NormalizationEngine.clamp(score)

    @staticmethod
    def transaction_volume(value: float) -> float:
        """
        거래량

        현재는 단순 점수
        이후 최근 평균 대비 계산 예정
        """

        return NormalizationEngine.clamp(value)

    @staticmethod
    def unsold(value: float) -> float:
        """
        미분양

        낮을수록 좋은 점수
        """

        score = 100 - value

        return NormalizationEngine.clamp(score)

    @staticmethod
    def permit(value: float) -> float:
        """
        인허가
        """

        return NormalizationEngine.clamp(value)

    @staticmethod
    def risk(value: float) -> float:
        """
        PF 위험도

        낮을수록 좋은 점수
        """

        score = 100 - value

        return NormalizationEngine.clamp(score)

    @classmethod
    def normalize(
        cls,
        indicator_id: str,
        value: float,
    ) -> float:
        """
        Indicator ID별 점수 계산
        """

        indicator_id = indicator_id.upper()

        # -------------------------
        # 가격지수
        # -------------------------
        if indicator_id in (
            "PRICE_INDEX",
            "SEOUL_PRICE_INDEX",
            "BUSAN_PRICE_INDEX",
        ):
            return cls.identity(value)

        # -------------------------
        # 전세가율
        # -------------------------
        if "JEONSE" in indicator_id:
            return cls.jeonse_ratio(value)

        # -------------------------
        # 기준금리
        # -------------------------
        if "RATE" in indicator_id:
            return cls.interest_rate(value)

        # -------------------------
        # 경매
        # -------------------------
        if "AUCTION" in indicator_id:
            return cls.auction_rate(value)

        # -------------------------
        # 미분양
        # -------------------------
        if "UNSOLD" in indicator_id:
            return cls.unsold(value)

        # -------------------------
        # 인허가
        # -------------------------
        if "PERMIT" in indicator_id:
            return cls.permit(value)

        # -------------------------
        # 위험도
        # -------------------------
        if "RISK" in indicator_id:
            return cls.risk(value)

        # -------------------------
        # 거래량
        # -------------------------
        if "VOLUME" in indicator_id:
            return cls.transaction_volume(value)

        # -------------------------
        # 정책점수
        # -------------------------
        if "POLICY" in indicator_id:
            return cls.identity(value)

        return cls.identity(value)
