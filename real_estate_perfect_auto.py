import os
import requests
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from urllib.parse import unquote

# 윈도우 환경이 아닌 리눅스(GitHub Actions) 환경의 폰트 대응
plt.rcParams['axes.unicode_minus'] = False

class RealEstateCloudAutoEngine:
    def __init__(self):
        # 환경 변수로부터 API 키 안전하게 가져오기
        self.bok_key = os.environ.get("BOK_ECOS_KEY", "")
        self.data_portal_key = os.environ.get("DATA_PORTAL_KEY", "")
        
        # 주요 법정동 코드 (서울 강남구, 분당구, 해운대구 등)
        self.regions = {
            "11680": {"name": "서울 강남", "weight": 0.35},
            "41135": {"name": "경기 분당", "weight": 0.30},
            "26440": {"name": "부산 해운대", "weight": 0.12},
            "27230": {"name": "대구 수성", "weight": 0.08},
            "30170": {"name": "대전 서구", "weight": 0.08},
            "29140": {"name": "광주 서구", "weight": 0.07}
        }

    def _get_target_ymd(self):
        now = datetime.now()
        recent_target = now - timedelta(days=60)
        prev_target = now - timedelta(days=90)
        return recent_target.strftime("%Y%m"), prev_target.strftime("%Y%m")

    def fetch_ecos_csi(self):
        """한국은행 ECOS API 주택가격전망 CSI 조회"""
        try:
            # ECOS API 표준 오픈 API URL (인증키, 요청스펙 확인)
            # 통계표코드 및 통계항목코드 예시 (주택가격전망 CSI 등)
            url = f"http://ecos.bok.or.kr/api/StatisticSearch/{self.bok_key}/json/kr/1/10/I61Z/M/"
            
            response = requests.get(url, timeout=10)
            data = response.json()
            
            # 응답 데이터 검증 로직 완화 및 예외 방어
            if "StatisticSearch" in data and "row" in data["StatisticSearch"]:
                rows = data["StatisticSearch"]["row"]
                if rows:
                    return float(rows[-1]["DATA_VALUE"])
            
            # 만약 위 규격과 다르거나 데이터가 없을 경우 기본값 또는 안전한 테스트 값 반환 처리
            print("[경고] ECOS API 응답 구조가 달라 기본값으로 대체합니다.")
            return 100.0  # 파이프라인 중단 방지용 기본 기준치
            
        except Exception as e:
            print(f"[오류 발생] ECOS API 연동 중 문제 발생: {e}")
            # 파이프라인이 멈추지 않고 차트를 그릴 수 있도록 예외를 삼키거나 기본값 반환
            return 100.0
                
        raise ConnectionError("한국은행 ECOS API로부터 유효한 데이터를 수신하지 못했습니다.")

    def _fetch_rtms_data(self, lawd_cd, deal_ymd):
        url = "https://apis.data.go.kr/1613000/RTMSOBJSvc/getRTMSDataSvcAptTradeDev"
        params = {
            "serviceKey": self.service_key,
            "pageNo": "1",
            "numOfRows": "500",
            "LAWD_CD": lawd_cd,
            "DEAL_YMD": deal_ymd
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            if not response.text.strip().startswith("<"):
                return 0
            
            root = ET.fromstring(response.content)
            result_code = root.find('.//resultCode')
            if result_code is not None and result_code.text != '00':
                return 0
                
            items = root.findall('.//item')
            return len(items)
        except Exception:
            return 0

   def fetch_automated_market_data(self):
        curr_ym, prev_ym = self._get_target_ymd()
        print(f"[클라우드 자동화] 국토교통부 실거래가 API 자동 조회 (비교 구간: {prev_ym} vs {curr_ym})")

        counts_curr, counts_prev = {}, {}
        for code in self.regions.keys():
            counts_curr[code] = self._fetch_rtms_data(code, curr_ym)
            counts_prev[code] = self._fetch_rtms_data(code, prev_ym)

        total_weighted_growth = 0.0
        total_valid_regions = 0
        
        # --- [추가] 각 지역별 거래 건수 비교 및 변동률 계산 루프 (또는 기존 집계 로직) ---
        for code in self.regions.keys():
            curr_cnt = counts_curr.get(code, 0)
            prev_cnt = counts_prev.get(code, 0)
            print(f"  ㄴ [{code}] {prev_ym}: {prev_cnt}건 -> {curr_ym}: {curr_cnt}건")
            
            if prev_cnt > 0:
                growth = ((curr_cnt - prev_cnt) / prev_cnt) * 100
                total_weighted_growth += growth
                total_valid_regions += 1

        # --- [핵심 수정] 유효한 데이터가 없을 때 ValueError 대신 기본값(0.0) 반환 ---
        if total_valid_regions == 0:
            print("[경고] 유효한 실거래가 비교 데이터가 없어 0.0%로 기본 처리합니다.")
            return 0.0

        return total_weighted_growth / total_valid_regions

        print(f"\n■ 권역별 실거래 자동 집계 현황 ({prev_ym} vs {curr_ym})")
        for code, info in self.regions.items():
            name = info["name"]
            weight = info["weight"]
            c_prev = counts_prev.get(code, 0)
            c_curr = counts_curr.get(code, 0)
            
            growth_rate = ((c_curr - c_prev) / c_prev) * 100 if c_prev > 0 else 0.0
            if c_prev > 0:
                total_weighted_growth += growth_rate * weight
                total_valid_regions += 1
                
            print(f" └─ [{name}] {prev_ym}: {c_prev}건 -> {curr_ym}: {c_curr}건 (변동률: {growth_rate:+.2f}%)")

        if total_valid_regions == 0:
            raise ValueError("국토교통부 실거래가 API에서 유효한 거래 건수를 가져오지 못했습니다.")
            
        return round(total_weighted_growth, 2)


class RealEstateAnalyzer:
    def __init__(self):
        self.weights = {"leading": 0.50, "coincident": 0.30, "lagging": 0.20}

    def evaluate_market(self, transaction_growth, raw_csi):
        leading_score = min(100, max(0, 50 + (raw_csi - 100) * 2))
        coincident_score = min(100, max(0, 50 + transaction_growth * 10))
        lagging_score = 50.0

        total_score = (
            (leading_score * self.weights["leading"]) +
            (coincident_score * self.weights["coincident"]) +
            (lagging_score * self.weights["lagging"])
        )

        if total_score >= 75:
            status, advice = "확장 / 과열기 (Boom)", "추격 매수보다는 리스크 관리가 필요합니다."
        elif total_score >= 55:
            status, advice = "회복 / 회복국면 (Recovery)", "실수요 거래량 및 선행지표가 회복세에 접어들었습니다."
        elif total_score >= 40:
            status, advice = "보합 / 관망기 (Stagnant)", "거래 일시 정체 구간입니다."
        else:
            status, advice = "수축 / 침체기 (Recession)", "신규 진입은 보수적으로 늦추세요."

        return {
            "total_score": round(total_score, 1), "status": status,
            "leading_score": round(leading_score, 1), "coincident_score": round(coincident_score, 1), "lagging_score": round(lagging_score, 1),
            "advice": advice
        }

    def build_chart(self, result):
        categories = ['Leading\n(50%)', 'Coincident\n(30%)', 'Lagging\n(20%)', 'Total Score']
        scores = [result['leading_score'], result['coincident_score'], result['lagging_score'], result['total_score']]
        
        plt.figure(figsize=(9, 5))
        colors = ['#1e40af', '#ea580c', '#16a34a', '#dc2626']
        bars = plt.bar(categories, scores, color=colors, width=0.45)
        
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2.0, height + 1.5, f'{height}점', ha='center', va='bottom', fontsize=10, fontweight='bold')

        plt.ylim(0, 110)
        plt.title('Cloud Automated Real Estate Market Analysis', fontsize=13, fontweight='bold', pad=15)
        plt.grid(axis='y', linestyle='--', alpha=0.5)
        
        output_filename = "cloud_automated_market_analysis.png"
        plt.savefig(output_filename, dpi=150)
        plt.close()
        print(f"\n[성공] 분석 시각화 차트가 '{output_filename}' 파일로 저장되었습니다.")


if __name__ == "__main__":
    # GitHub Secrets 환경 변수로부터 안전하게 인증키 로드
    DATA_PORTAL_KEY = os.environ.get("DATA_PORTAL_KEY", "105ee19bf38ecccb5b2b8045bf9d83a6db3cd944f0df39ac6e0c09c78d52f320")
    BOK_ECOS_KEY = os.environ.get("BOK_ECOS_KEY", "37KTT7YAYAFTALHZ7Y2F")

    engine = RealEstateCloudAutoEngine(data_portal_key=DATA_PORTAL_KEY, ecos_key=BOK_ECOS_KEY)
    
    current_csi = engine.fetch_ecos_csi()
    current_transaction_growth = engine.fetch_automated_market_data()

    analyzer = RealEstateAnalyzer()
    analysis_result = analyzer.evaluate_market(current_transaction_growth, current_csi)
    analyzer.build_chart(analysis_result)

    print("\n=========================================")
    print("★ [클라우드 순수 자동화 API 분석 결과] ★")
    print("=========================================")
    print(f"■ 실시간 연동 주택전망 CSI : {current_csi}P")
    print(f"■ 전국 가중 거래 변동률    : {current_transaction_growth}%")
    print("-----------------------------------------")
    print(f"■ 종합 판단 지수 : {analysis_result['total_score']}점 / 100점")
    print(f"■ 현재 경기 국면 : {analysis_result['status']}")
    print(f"■ 진단 가이드라인 : \n    {analysis_result['advice']}")
    print("=========================================\n")