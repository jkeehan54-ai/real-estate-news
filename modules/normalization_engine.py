# normalization_engine.py


"""
BRN Normalization Engine

각 지표를 0~100 점수로 변환한다.
"""

from __future__ import annotations


class NormalizationEngine:

    @staticmethod
    def clamp(score: float) -> float:
        """0~100 범위 제한"""
        return round(max(0.0, min(100.0, score)), 2)

    @staticmethod
    def identity(value: float) -> float:
        """
        이미 0~100인 값
        """
        return NormalizationEngine.clamp(value)

    @staticmethod
    def reverse(value: float) -> float:
        """
        값이 낮을수록 좋은 지표
        예)
        미분양
        PF
        공실률
        """
        return NormalizationEngine.clamp(100.0 - value)

    @staticmethod
    def percentage(value: float) -> float:
        """
        퍼센트 값
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

        return score

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
        경매 낙찰률
        """

        score = value * 2

        return NormalizationEngine.clamp(score)

    @staticmethod
    def transaction_volume(value: float) -> float:
        """
        거래량

        현재는 단순 점수
        이후 5년 평균 대비 계산 예정
        """

        return NormalizationEngine.clamp(value)

    @staticmethod
    def unsold(value: float) -> float:
        """
        미분양
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
        위험도
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

        if "JEONSE" in indicator_id:
            return cls.jeonse_ratio(value)

        if "RATE" in indicator_id:
            return cls.interest_rate(value)

        if "AUCTION" in indicator_id:
            return cls.auction_rate(value)

        if "UNSOLD" in indicator_id:
            return cls.unsold(value)

        if "PERMIT" in indicator_id:
            return cls.permit(value)

        if "RISK" in indicator_id:
            return cls.risk(value)

        if "VOLUME" in indicator_id:
            return cls.transaction_volume(value)

        return cls.identity(value)
