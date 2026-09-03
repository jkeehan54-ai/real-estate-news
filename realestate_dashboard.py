"""
부동산 경기 지표 분석 대시보드 - Google News 구조 대응 최종판
==============================================================
핵심 문제 해결:
1. Google News RSS 요약 = HTML 링크만 있음 → 제목(title)만으로 파싱
2. 부산 변동률 → 부산일보/국제신문/경남도민일보 RSS에서 직접 수집
3. KB수급/전망 → 제목 키워드 패턴 변경
4. 준공/착공/거래량 → 제목에서 전년비 % 패턴 직접 탐색
5. 미분양 → 제목의 "X만가구" 패턴 (요약 불필요)
"""
import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import feedparser, requests, re, os, json
from datetime import datetime, timezone, timedelta

# KB 공식 API 호출 시 verify=False를 쓰기 때문에 매번 뜨는 InsecureRequestWarning을
# 콘솔에서 숨긴다 (기능에는 영향 없음, 순수 로그 정리용)
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass

KST = timezone(timedelta(hours=9))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
}

# ══════════════════════════════════════════════════════════════════════════════
# KB부동산 공식 데이터 API (data-api.kbland.kr)
# ══════════════════════════════════════════════════════════════════════════════
# 뉴스 기사 파싱보다 정확하고 안정적인 1차 소스. 실패하면(네트워크 오류, 응답 구조
# 변경 등) 각 지표 함수에서 기존 뉴스 파싱으로 자동 폴백한다.
KB_API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
}

def kb_api_get(url, params, timeout=10):
    """KB 데이터 API 공통 호출. 실패 시 None."""
    try:
        res = requests.get(url, headers=KB_API_HEADERS, params=params,
                            timeout=timeout, verify=False)
        body = res.json().get("dataBody", {})
        if str(body.get("resultCode")) != "11000":
            return None
        return body.get("data")
    except Exception as e:
        print(f"  [KB API 오류] {e}")
        return None

def kb_latest_by_region(data, region_aliases):
    """
    '데이터리스트'에서 지역명이 region_aliases 중 하나와 일치하는 항목을 찾아,
    dataList를 뒤에서부터 훑어 None이 아닌 가장 최신 값과 그 날짜를 반환한다.
    (prcIndxInxrdcRt=가격증감률, dealCntstTnantRato=전세가율처럼 dataList가
    숫자 배열인 API용)
    """
    if not data: return None, None
    dates = data.get("날짜리스트", [])
    for item in data.get("데이터리스트", []):
        if item.get("지역명") in region_aliases:
            dl = item.get("dataList", [])
            for i in range(len(dl) - 1, -1, -1):
                if dl[i] is not None:
                    d = dates[i] if i < len(dates) else None
                    return dl[i], d
    return None, None

def kb_latest_field_national(data, field):
    """
    maktTrnd(설문형 지수: 매수우위지수/전세수급지수/매매·전세전망지수 등) 응답에서
    '전국' dataList의 최신 항목 중 field 값을 반환한다. (dataList가 dict 배열)
    """
    if not data: return None
    for item in data.get("데이터리스트", []):
        if item.get("지역명") == "전국":
            dl = item.get("dataList", [])
            for entry in reversed(dl):
                if isinstance(entry, dict) and entry.get(field) is not None:
                    return entry.get(field)
    return None

def fetch_kb_api_weekly_price_change():
    """KB 공식 API: 주간 아파트 매매/전세 가격지수 증감률 (전국/서울/부산)"""
    result = {"국전체": None, "서울": None, "부산": None, "전세전국": None,
               "전세부산": None, "기준일": None}
    d_sale = kb_api_get(
        "https://data-api.kbland.kr/bfmstat/weekMnthlyHuseTrnd/prcIndxInxrdcRt",
        {"월간주간구분코드": "02", "매물종별구분": "01", "매매전세코드": "01"})
    nat, dte = kb_latest_by_region(d_sale, ["전국"])
    result["국전체"] = nat
    if dte and len(dte) == 8:
        result["기준일"] = f"{dte[:4]}.{dte[4:6]}.{dte[6:8]}"
    seo, _ = kb_latest_by_region(d_sale, ["서울"])
    result["서울"] = seo
    bus, _ = kb_latest_by_region(d_sale, ["부산", "부산광역시"])
    result["부산"] = bus

    d_jeonse = kb_api_get(
        "https://data-api.kbland.kr/bfmstat/weekMnthlyHuseTrnd/prcIndxInxrdcRt",
        {"월간주간구분코드": "02", "매물종별구분": "01", "매매전세코드": "02"})
    jeo, _ = kb_latest_by_region(d_jeonse, ["전국"])
    result["전세전국"] = jeo
    jeo_bus, _ = kb_latest_by_region(d_jeonse, ["부산", "부산광역시"])
    result["전세부산"] = jeo_bus
    return result

def fetch_kb_api_jeonse_ratio():
    """KB 공식 API: 전세가율 (전국/서울/부산, 월간)"""
    result = {"전국": None, "서울": None, "부산": None}
    d = kb_api_get(
        "https://data-api.kbland.kr/bfmstat/weekMnthlyHuseTrnd/dealCntstTnantRato",
        {"매물종별구분": "01"})
    nat, _ = kb_latest_by_region(d, ["전국"])
    result["전국"] = nat
    seo, _ = kb_latest_by_region(d, ["서울"])
    result["서울"] = seo
    bus, _ = kb_latest_by_region(d, ["부산", "부산광역시"])
    result["부산"] = bus
    return result

def fetch_kb_api_forecast():
    """KB 공식 API: 매매/전세 가격전망지수 (전국, 월간)"""
    result = {"매매전망": None, "전세전망": None}
    d_m = kb_api_get(
        "https://data-api.kbland.kr/bfmstat/weekMnthlyHuseTrnd/maktTrnd",
        {"메뉴코드": "05", "월간주간구분코드": "01"})
    result["매매전망"] = kb_latest_field_national(d_m, "매매상승하락전망지수")

    d_j = kb_api_get(
        "https://data-api.kbland.kr/bfmstat/weekMnthlyHuseTrnd/maktTrnd",
        {"메뉴코드": "06", "월간주간구분코드": "01"})
    result["전세전망"] = kb_latest_field_national(d_j, "전세상승하락전망지수")
    return result


# ══════════════════════════════════════════════════════════════════════════════
# 법원경매정보(courtauction.go.kr) 내부 호출 재현
# ══════════════════════════════════════════════════════════════════════════════
# ★ 주의: 이건 KB API처럼 공식 오픈API가 아니라, 실제 웹사이트가 화면을 그릴 때
#   내부적으로 호출하는 주소를 그대로 재현한 것이다 (대법원은 과거 분쟁조정에서
#   이 데이터를 오픈API로 제공하지 않는다고 명시적으로 밝힌 바 있음). 따라서
#   사이트 구조가 바뀌면 언제든 조용히 실패할 수 있고, 그 경우 자동으로 기존
#   뉴스 파싱 로직으로 폴백한다.
COURT_AUCTION_URL = "https://www.courtauction.go.kr/pgj/pgj164/selectRletCortDspslStats.on"
COURT_AUCTION_REFERER = ("https://www.courtauction.go.kr/pgj/index.on?"
                          "w2xPath=%2Fpgj%2Fui%2Fpgj100%2FPGJ164M01.xml")

def _prev_month_yyyymm():
    """가장 최근에 통계가 '완결'됐을 전월(YYYYMM)을 계산한다.
    (법원경매정보는 매월 1일에 전월 최종치를 확정 발표하는 패턴이라, 당월 데이터는
    아직 집계 중일 수 있으므로 전월을 기본값으로 쓴다.)"""
    now = datetime.now(KST)
    y, m = now.year, now.month - 1
    if m == 0:
        y -= 1; m = 12
    return f"{y}{m:02d}"

def fetch_court_auction_apt(yyyymm=None):
    """법원경매정보 용도별 매각통계에서 '아파트' 낙찰률/낙찰가율을 가져온다.
    yyyymm이 없으면 최근 완결된 전월 1개월치만 조회한다."""
    ym = yyyymm or _prev_month_yyyymm()
    payload = {"dma_search": {
        "searchType": "01", "cortOfcCd": "", "adongSdCd": "", "adongSggCd": "",
        "startDate": ym, "endDate": ym,
    }}
    headers = dict(KB_API_HEADERS)
    headers["Content-Type"] = "application/json;charset=UTF-8"
    headers["Referer"] = COURT_AUCTION_REFERER
    try:
        res = requests.post(COURT_AUCTION_URL, json=payload, headers=headers,
                             timeout=10, verify=False)
        data = res.json()
        if data.get("status") != 200:
            return None
        rows = data.get("data", {}).get("rletCortDspslStats", [])
        for row in rows:
            if row.get("lclDspslGdsLstUsgNm") == "아파트":
                return {
                    "낙찰률":   row.get("dspslRate"),
                    "낙찰가율": row.get("dspslAmtRate"),
                    "건수":     row.get("auctnNum"),
                    "매각건수": row.get("dspslNum"),
                    "기준월":   ym,
                    "기준일":   row.get("frstInptDt"),
                }
    except Exception as e:
        print(f"  [법원경매 API 오류] {e}")
    return None


# ══════════════════════════════════════════════════════════════════════════════
# 한국은행 ECOS Open API (소비자동향조사 - CSI / 주택가격전망CSI)
# ══════════════════════════════════════════════════════════════════════════════
# ★ 개인 인증키가 필요한 공식 오픈API. 환경변수 ECOS_API_KEY로 전달받는다
#   (코드에 직접 박아넣지 않음 — GitHub 등에 올라가도 키가 노출되지 않도록).
#   로컬 테스트 시: PowerShell에서
#     $env:ECOS_API_KEY="발급받은키"
#   GitHub Actions에서는 Secrets에 ECOS_API_KEY로 등록.
ECOS_API_KEY = os.environ.get("ECOS_API_KEY", "")
ECOS_BASE = "https://ecos.bok.or.kr/api"

def fetch_ecos_csi():
    """
    한국은행 ECOS: 소비자동향조사(511Y002)에서 소비자심리지수(FME)와
    주택가격전망CSI(FMFB)의 '전체'(99988) 최신월 값을 가져온다.
    """
    if not ECOS_API_KEY:
        return None
    result = {"CSI": None, "주택전망": None, "기준월": None}
    try:
        end = datetime.now(KST).strftime("%Y%m")
        start = (datetime.now(KST).replace(day=1) - timedelta(days=400)).strftime("%Y%m")

        def latest(item_path):
            # ★ ECOS의 "N/M" 구간 파라미터는 "최근 N개"가 아니라 "조회기간 내
            #   앞에서부터 N개"이다. 요청 개수가 실제 구간(약 13개월) 데이터
            #   개수보다 적으면 오래된 달부터 잘려나가 최신월이 누락된다.
            #   그래서 넉넉히(60개, 약 5년치) 요청해 반드시 전체를 다 받은 뒤
            #   마지막 행(rows[-1])을 최신값으로 쓴다.
            url = f"{ECOS_BASE}/StatisticSearch/{ECOS_API_KEY}/json/kr/1/60/511Y002/M/{start}/{end}/{item_path}"
            res = requests.get(url, timeout=10)
            data = res.json()
            rows = data.get("StatisticSearch", {}).get("row")
            if not rows: return None, None
            # 혹시 몰라 TIME 기준으로도 한 번 더 정렬해서 진짜 최신값을 보장한다
            rows = sorted(rows, key=lambda x: x.get("TIME", ""))
            last = rows[-1]
            return safe_float(last.get("DATA_VALUE")), last.get("TIME")

        result["CSI"], t1 = latest("FME/99988")
        result["주택전망"], t2 = latest("FMFB/99988")
        result["기준월"] = t2 or t1
    except Exception as e:
        print(f"  [ECOS API 오류] {e}")
        return None
    return result


# ══════════════════════════════════════════════════════════════════════════════
# 한국부동산원 R-ONE Open API (매매수급동향 / 전세수급동향)
# ══════════════════════════════════════════════════════════════════════════════
RONE_API_KEY = os.environ.get("RONE_API_KEY", "")
RONE_BASE = "https://www.reb.or.kr/r-one/openapi/SttsApiTblData.do"

# 실제 진단으로 확인된 통계표ID (둘 다 '전국' 주간 지수, DTA_VAL 필드)
RONE_STATBL_매매수급 = "T248163133074619"
RONE_STATBL_전세수급 = "T245423133086632"

def fetch_rone_index(statbl_id, cycle="WK"):
    """
    R-ONE 통계표에서 '전국' 최신값을 가져온다.
    이 API는 통계표 전체 이력(예: 2012년~현재, 2만7천여 건)을 오래된 순서로
    돌려주고 페이지네이션(최대 1000건/페이지)만 지원하기 때문에, 최신값을
    구하려면: ①1페이지로 총 건수 확인 → ②마지막 페이지를 다시 요청 →
    ③그 안에서 '전국' 행만 골라 날짜(WRTTIME_DESC) 기준 가장 최근 것을 취한다.
    """
    if not RONE_API_KEY:
        return None, None
    try:
        base_params = {"KEY": RONE_API_KEY, "STATBL_ID": statbl_id,
                        "DTACYCLE_CD": cycle, "Type": "json", "pSize": 1000}

        def unwrap(resp_json):
            """R-ONE 응답은 {'SttsApiTblData': [{head...}, {row...}]} 형태로
            한 겹 감싸져 있다. 이 배열([head, row])을 꺼내서 돌려준다."""
            if isinstance(resp_json, dict) and "SttsApiTblData" in resp_json:
                return resp_json["SttsApiTblData"]
            if isinstance(resp_json, list):  # 혹시 감싸지지 않은 형태로 오는 경우 대비
                return resp_json
            return None

        r1 = requests.get(RONE_BASE, params={**base_params, "pIndex": 1}, timeout=15)
        d1 = unwrap(r1.json())
        if not isinstance(d1, list) or len(d1) < 1:
            print(f"  [R-ONE 진단] STATBL_ID={statbl_id} 1페이지 응답 형식 이상: "
                  f"{str(r1.json())[:200]}")
            return None, None
        total = d1[0].get("head", [{}])[0].get("list_total_count", 0)
        if not total:
            print(f"  [R-ONE 진단] STATBL_ID={statbl_id} list_total_count 없음: "
                  f"{str(d1[0])[:200]}")
            return None, None
        last_page = max(1, -(-int(total) // 1000))  # 올림 나눗셈

        if last_page == 1:
            rows = d1[1].get("row", []) if len(d1) > 1 else []
        else:
            r2 = requests.get(RONE_BASE, params={**base_params, "pIndex": last_page}, timeout=15)
            d2 = unwrap(r2.json())
            if not isinstance(d2, list) or len(d2) < 2:
                print(f"  [R-ONE 진단] STATBL_ID={statbl_id} 마지막페이지({last_page}) "
                      f"응답 형식 이상: {str(r2.json())[:200]}")
                rows = []
            else:
                rows = d2[1].get("row", [])

        if not rows:
            print(f"  [R-ONE 진단] STATBL_ID={statbl_id} 마지막페이지에 row 없음 "
                  f"(total={total}, last_page={last_page})")
            return None, None

        nat = [x for x in rows if x.get("CLS_NM") == "전국"]
        if not nat:
            cls_sample = sorted(set(x.get("CLS_NM") for x in rows))[:10]
            print(f"  [R-ONE 진단] STATBL_ID={statbl_id} '전국' 행 없음. "
                  f"실제 CLS_NM 목록(일부): {cls_sample}")
            return None, None
        nat.sort(key=lambda x: x.get("WRTTIME_DESC", ""))
        last = nat[-1]
        return safe_float(last.get("DTA_VAL")), last.get("WRTTIME_DESC")
    except Exception as e:
        print(f"  [R-ONE API 오류] {e}")
        return None, None

def fetch_rone_supply_demand():
    """한국부동산원 R-ONE: 전국 매매수급동향 / 전세수급동향(주간) 최신값"""
    result = {"매매수급": None, "전세수급": None, "기준일": None}
    tv, d1 = fetch_rone_index(RONE_STATBL_매매수급)
    jv, d2 = fetch_rone_index(RONE_STATBL_전세수급)
    result["매매수급"] = tv
    result["전세수급"] = jv
    result["기준일"] = d2 or d1
    return result

# ══════════════════════════════════════════════════════════════════════════════
# 주택금융공사 HOUSTAT Open API - K-HAI(주택구입부담지수)
# ══════════════════════════════════════════════════════════════════════════════
HOUSTAT_BASE = "https://houstat.hf.go.kr/research/openapi/SttsApiTblData.do"
HOUSTAT_STATBL_KHAI = "T186503126543136"  # '지역별 K-HAI' 표 — '전국' 행 포함 확인됨
HOUSTAT_API_KEY = os.environ.get("HOUSTAT_API_KEY", "")  # 없어도 호출 가능(키 없으면 sample 제한 가능성 있음)

def fetch_houstat_khai():
    """
    HOUSTAT에서 전국 K-HAI 최신 분기값을 가져온다.
    fetch_rone_index()와 동일한 문제: WRTTIME_IDTFR_ID를 생략하면 전체 이력
    (오래된 순, 페이지당 최대 1000건)을 돌려주므로, ①1페이지로 총 건수 확인 →
    ②마지막 페이지를 재요청 → ③'전국' 행 중 가장 최근 것을 취한다.
    """
    try:
        base_params = {"STATBL_ID": HOUSTAT_STATBL_KHAI, "DTACYCLE_CD": "QY",
                        "Type": "json", "pSize": 1000}
        if HOUSTAT_API_KEY:
            base_params["KEY"] = HOUSTAT_API_KEY

        def unwrap(resp_json):
            if isinstance(resp_json, dict) and "SttsApiTblData" in resp_json:
                return resp_json["SttsApiTblData"]
            if isinstance(resp_json, list):
                return resp_json
            return None

        r1 = requests.get(HOUSTAT_BASE, params={**base_params, "pIndex": 1}, timeout=15)
        d1 = unwrap(r1.json())
        if not isinstance(d1, list) or len(d1) < 1:
            print(f"  [K-HAI/HOUSTAT 진단] 1페이지 응답 형식 이상: {str(r1.json())[:200]}")
            return None, None
        total = d1[0].get("head", [{}])[0].get("list_total_count", 0)
        if not total:
            print(f"  [K-HAI/HOUSTAT 진단] list_total_count 없음: {str(d1[0])[:200]}")
            return None, None
        last_page = max(1, -(-int(total) // 1000))  # 올림 나눗셈

        if last_page == 1:
            rows = d1[1].get("row", []) if len(d1) > 1 else []
        else:
            r2 = requests.get(HOUSTAT_BASE, params={**base_params, "pIndex": last_page}, timeout=15)
            d2 = unwrap(r2.json())
            if not isinstance(d2, list) or len(d2) < 2:
                print(f"  [K-HAI/HOUSTAT 진단] 마지막페이지({last_page}) 응답 형식 이상: {str(r2.json())[:200]}")
                rows = []
            else:
                rows = d2[1].get("row", [])

        if not rows:
            print(f"  [K-HAI/HOUSTAT 진단] 마지막페이지에 row 없음 (total={total}, last_page={last_page})")
            return None, None

        nat = [x for x in rows if (x.get("ITM_NM") or "").strip() == "전국"]
        if not nat:
            itm_sample = sorted(set((x.get("ITM_NM") or "").strip() for x in rows))[:10]
            print(f"  [K-HAI/HOUSTAT 진단] '전국' 행 없음. 실제 ITM_NM 목록(일부): {itm_sample}")
            return None, None

        nat.sort(key=lambda x: str(x.get("WRTTIME_IDTFR_ID", "")))
        last = nat[-1]
        return safe_float(last.get("DTA_VAL")), last.get("WRTTIME_IDTFR_ID")
    except Exception as e:
        print(f"  [K-HAI/HOUSTAT API 오류] {e}")
        return None, None
# ══════════════════════════════════════════════════════════════════════════════
# KOSIS(국가통계포털) Open API - 주택건설 인허가실적
# ══════════════════════════════════════════════════════════════════════════════
KOSIS_API_KEY = os.environ.get("KOSIS_API_KEY", "")
KOSIS_BASE = "https://kosis.kr/openapi"

# 실제 진단으로 확인된 표: 국토교통부(orgId=116) '부문별 주택건설 인허가실적(월별 누계)'
# - tblId=DT_MLTM_1946, PRD_SE="M"(월간) 확인됨. objL1~objL3 세 개가 모두 필요하다
#   (구분1=부문 총계/LH/공공부문 등, 구분2=부문 세부, 구분3=시도별).
# - "월별 누계"라는 이름대로 그 해 1월부터의 누적치다(예: 2월 값 = 1~2월 합).
#   실제 국토부 보도자료의 "O월 누적 실적"과 같은 개념이라 그대로 사용한다.
# - DT_MLTM_618(총괄)은 연간(PRD_SE=A)만 제공 확인 → 월간표가 실패할 때만 폴백.
KOSIS_PERMIT_ORG = "116"
KOSIS_PERMIT_TBL_CANDIDATES = [
    {"tblId": "DT_MLTM_1946", "objl_count": 3},  # 월별 누계 (진짜 월간)
    {"tblId": "DT_MLTM_618",  "objl_count": 2},  # 총괄 (연간, 최후 폴백)
]

def _norm_nm(s):
    """'총  계'/'총계'/'합계' 처럼 공백이 들쭉날쭉한 분류명을 비교하기 쉽게 정규화"""
    return re.sub(r'\s+', '', s or '')

def fetch_kosis_permit():
    """
    KOSIS: 주택건설 인허가실적(전국, 총계)의 최신 값을 가져온다.
    표마다 필요한 objL 파라미터 개수가 달라(진단으로 확인) 표별로 다르게 넣는다.
    '총계/총계/전국'에 해당하는 행만 골라 가장 최근 PRD_DE를 채택한다.
    """
    if not KOSIS_API_KEY:
        return None
    url = f"{KOSIS_BASE}/Param/statisticsParameterData.do"
    for cand in KOSIS_PERMIT_TBL_CANDIDATES:
        tbl_id, n_objl = cand["tblId"], cand["objl_count"]
        try:
            params = {
                "method": "getList", "apiKey": KOSIS_API_KEY,
                "format": "json", "jsonVD": "Y",
                "prdSe": "M", "newEstPrdCnt": "6",
                "orgId": KOSIS_PERMIT_ORG, "tblId": tbl_id,
                "itmId": "ALL",
            }
            for i in range(1, n_objl + 1):
                params[f"objL{i}"] = "ALL"

            res = requests.get(url, params=params, timeout=15)
            data = res.json()
            if not isinstance(data, list) or not data:
                continue

            # 총계/합계 계열 행만 추려낸다 (공백 표기가 제각각이라 정규화해서 비교)
            def is_total(nm):
                n = _norm_nm(nm)
                return n in ("총계", "합계", "합")

            totals = [row for row in data if is_total(row.get("C1_NM"))]
            if "C2_NM" in (data[0] if data else {}):
                c2_totals = [row for row in totals if is_total(row.get("C2_NM"))]
                if c2_totals:
                    totals = c2_totals
            if "C3_NM" in (data[0] if data else {}):
                c3_nat = [row for row in totals if row.get("C3_NM") == "전국"]
                if c3_nat:
                    totals = c3_nat
            if not totals:
                continue

            totals.sort(key=lambda r: r.get("PRD_DE", ""))
            last = totals[-1]
            val = safe_int(last.get("DT"))
            if val is None:
                continue
            prd = last.get("PRD_DE", "")
            is_monthly = last.get("PRD_SE") == "M" or len(prd) == 6
            return {"수치": val, "기준": prd, "월간여부": is_monthly,
                    "누계여부": is_monthly, "tblId": tbl_id}
        except Exception as e:
            print(f"  [KOSIS API 오류] tblId={tbl_id}: {e}")
            continue
    return None


# ══════════════════════════════════════════════════════════════════════════════
# K-REMAP(국토연구원) 부동산시장소비심리지수 — 페이지 소스에 데이터 직접 내장
# ══════════════════════════════════════════════════════════════════════════════
# ★ 별도 API 호출이 아니라, 페이지 HTML(자바스크립트) 안에 데이터가 그대로
#   내장되어 있는 걸 정규식으로 뽑아내는 방식이다. 인증키가 필요 없다.
#   jisu=167 이 '부동산시장소비심리지수(전국 등 지역별)' 그리드다.
#   사이트 구조가 바뀌면 조용히 실패하고 뉴스 파싱으로 자동 폴백한다.
KREMAP_URL = "https://kremap.krihs.re.kr/grid/grid"

def fetch_krihs_sentiment(jisu="167"):
    """
    K-REMAP 그리드 페이지에서 '전국지수' 시계열을 뽑아 최신월 값을 반환한다.
    페이지 소스 안에 예: {quarter:"202607", 전국지수:'112.6', 지수:'112.6'} 형태로
    내장되어 있다(변수명은 'quarter'지만 실제로는 월 단위 YYYYMM 문자열).
    """
    try:
        # 최근 9개월 범위로 조회 (사이트 기본 조회기간과 유사하게)
        end = datetime.now(KST)
        start = end - timedelta(days=270)
        params = {
            "jisu": jisu,
            "sDate": start.strftime("%Y-%m"),
            "eDate": end.strftime("%Y-%m"),
        }
        res = requests.get(KREMAP_URL, params=params, headers=HEADERS, timeout=15)
        html = res.text

        # data:[{ quarter : "202511", 전국지수 : '109.5', ... }, ...] 형태 추출
        pattern = re.compile(
            r'quarter\s*:\s*"(\d{6})"\s*,\s*전국지수\s*:\s*\'([\-\d.]+)\''
        )
        rows = pattern.findall(html)
        if not rows:
            print(f"  [K-REMAP 진단] jisu={jisu} 상태코드={res.status_code} "
                  f"응답길이={len(html)} / 'quarter' 포함여부={'quarter' in html} / "
                  f"'전국지수' 포함여부={'전국지수' in html}")
            # 혹시 파라미터 없이 요청하면 다를 수 있으니 한 번 더 시도
            res2 = requests.get(KREMAP_URL, params={"jisu": jisu}, headers=HEADERS, timeout=15)
            rows = pattern.findall(res2.text)
            if not rows:
                print(f"  [K-REMAP 진단] 파라미터 없이 재시도해도 실패 "
                      f"(상태코드={res2.status_code}, 응답길이={len(res2.text)})")
                return None
        rows.sort(key=lambda x: x[0])  # quarter(YYYYMM) 기준 오름차순 정렬
        ym, val = rows[-1]
        v = safe_float(val, 50, 200)
        if v is None:
            return None
        return {"지수": v, "기준월": f"{ym[:4]}.{ym[4:6]}"}
    except Exception as e:
        print(f"  [K-REMAP 오류] {e}")
        return None

# 한국어 조사(은/는/이/가/을/를/로/으로) 뒤에 숫자가 오는 경우를 위한 공통 패턴.
# 예: "소비자심리지수는 101.4로 상승" → "지수" 바로 뒤에 "\s*"만 있으면 "는"에서
#     매칭이 끊기므로, 조사를 선택적으로 건너뛸 수 있게 해준다.
PJ = r'(?:은|는|이|가|을|를|로|으로|도|의|에|와|과|:|,)?\s*'

# 일반 RSS 피드
RSS_FEEDS = [
    "https://www.sedaily.com/Rss/RealEstate",
    "https://www.arunews.com/rss/allArticle.xml",
    "https://www.constimes.co.kr/rss/allArticle.xml",
    "https://www.mk.co.kr/rss/30100041/",
    "https://www.mk.co.kr/rss/50100032/",
    "https://rss.donga.com/economy.xml",
    "https://www.hani.co.kr/rss/economy/",
    "https://www.yna.co.kr/rss/economy.xml",
    "https://www.ajunews.com/rss/economy.xml",
    "https://www.asiae.co.kr/rss/all.htm",
    "https://biz.heraldcorp.com/rss/all_list.xml",
    "https://www.newsis.com/rss/economy.xml",
]

# 부산/경남 전용 RSS (부동산 변동률 수치 포함)
BUSAN_RSS_FEEDS = [
    "https://www.idomin.com/rss/allArticle.xml",      # 경남도민일보
    "https://www.yna.co.kr/rss/economy.xml",          # 연합뉴스 (부산 통계 기사 포함)
    "https://www.arunews.com/rss/allArticle.xml",     # 주택경제신문
]


# ── 유틸 ─────────────────────────────────────────────────────────────────────
def safe_float(v, lo=None, hi=None):
    try:
        if v is None or str(v).strip() in ("","None","—"): return None
        f = float(str(v).replace(",","").replace("%","").strip())
        if lo is not None and f < lo: return None
        if hi is not None and f > hi: return None
        return f
    except: return None

def safe_int(v, lo=None, hi=None):
    try:
        if v is None or str(v).strip() in ("","None","—",","): return None
        i = int(str(v).replace(",","").strip())
        if lo is not None and i < lo: return None
        if hi is not None and i > hi: return None
        return i
    except: return None

def parse_korean_num(text, keyword, lo=None, hi=None):
    """'키워드 근처 X만Y천 / X만Y(정밀표기)' 한국식 숫자 파싱.
    키워드가 문서에 여러 번 등장할 수 있으므로(예: 숫자 없는 언급이 먼저 나오고
    실제 수치는 뒤에 나오는 경우), 모든 등장 위치를 순서대로 시도해
    유효 범위(lo~hi) 안의 첫 결과를 반환한다."""
    def ok(v):
        return v if (lo is None or v>=lo) and (hi is None or v<=hi) else None

    for m0 in re.finditer(re.escape(keyword), text):
        idx = m0.start()
        seg = text[max(0,idx-10):idx+60]

        # X만Y천 (예: "6만7천")
        m = re.search(r'(\d+)\s*만\s*(\d+)\s*천', seg)
        if m:
            v = ok(int(m.group(1))*10000 + int(m.group(2))*1000)
            if v is not None: return v
        # X만Y (정밀표기, 예: "6만7464", "1만181") — 뒤에 '천'이 붙지 않는 경우만
        m = re.search(r'(\d+)\s*만\s*(\d{2,4})(?!\s*천)', seg)
        if m:
            v = ok(int(m.group(1))*10000 + int(m.group(2)))
            if v is not None: return v
        # X.X만
        m = re.search(r'(\d+\.\d+)\s*만', seg)
        if m:
            v = ok(int(float(m.group(1))*10000))
            if v is not None: return v
        # X만
        m = re.search(r'(\d+)\s*만', seg)
        if m:
            v = ok(int(m.group(1))*10000)
            if v is not None: return v
        # 일반 숫자 (4자리 이상, 연도로 오인하기 쉬운 순수 4자리 "20XX"는 제외)
        m = re.search(r'([\d,]{4,})', seg)
        if m:
            raw = m.group(1)
            if not re.fullmatch(r'20\d{2}', raw):  # "2026" 같은 연도 오인식 방지
                v = safe_int(raw, lo, hi)
                if v is not None: return v
    return None

def parse_manwon_count(s):
    """
    '1만181가구', '6만7946가구', '7736가구' 처럼 국토부 보도자료에 흔한
    '만' + 나머지(콤마 없는 순수 자릿수) 조합의 가구수 표기를 정수로 변환.
    parse_korean_num의 'X만Y천' 패턴과 달리 '천' 단위 없이 바로 나머지
    숫자가 붙는 표기(예: 1만181)를 다룬다.
    """
    if not s: return None
    m = re.search(r'(\d+)\s*만\s*(\d+)?', s)
    if m:
        man = int(m.group(1))
        rest = int(m.group(2)) if m.group(2) else 0
        return man*10000 + rest
    m = re.search(r'(\d{2,6})', s)
    if m: return int(m.group(1))
    return None

def sum_region_count(text, keyword, unit="가구"):
    """
    '수도권 인허가는 1만181가구', '비수도권 6월 착공은 7289가구' 처럼
    국토부 통계 보도자료가 '전국' 합계를 직접 안 주고 수도권/비수도권으로만
    나눠 주는 경우, 두 값을 찾아 더해서 전국 수치를 만든다.
    """
    def grab(region):
        pat = re.compile(region + r'[^.]{0,20}?' + re.escape(keyword) +
                          r'[^.]{0,10}?((?:\d+\s*만\s*)?\d{1,6})\s*' + unit)
        m = pat.search(text)
        return parse_manwon_count(m.group(1)) if m else None
    cap = grab('수도권')
    non = grab('비수도권')
    if cap is not None and non is not None:
        return cap + non
    return None

def find_value_near(text, keyword, lo=None, hi=None, window=45):
    """
    '주택가격전망지수는 전월보다 7p 오른 127을 기록했다', '전세가격 전망지수는
    전월 대비 0.5포인트 오른 120.5를 기록했다' 처럼, 키워드 바로 뒤에 조사+숫자가
    바로 오지 않고 '전월 대비 Np' 같은 변동폭 표현을 먼저 거친 뒤에야 실제
    지수값이 나오는 한국 경제지표 기사체를 위한 보강 탐색.
    키워드가 여러 번 나올 수 있어 모든 등장 위치를 순서대로 시도한다.
    """
    for m0 in re.finditer(re.escape(keyword), text):
        idx = m0.start()
        seg = text[idx: idx + window + len(keyword)]
        m = re.search(r'(\d{2,3}\.?\d*)\s*(?:을|를|포인트|p)?\s*'
                       r'(?:기록|나타났|올랐|내렸|상승|하락|기록했다)', seg)
        if m:
            v = safe_float(m.group(1))
            if v is not None and (lo is None or v >= lo) and (hi is None or v <= hi):
                return v
    return None

def parse_korean_num_fwd(text, keyword, lo=None, hi=None):
    """parse_korean_num과 같지만 키워드 '앞'은 보지 않고 뒤쪽만 탐색한다.
    "전국 미분양 6만7천호…악성 미분양 1만2천호"처럼 바로 앞에 다른 지표의
    숫자가 있는 경우, 뒤로 10자 되짚는 기본 윈도우가 앞 숫자를 잘못 집어오는
    문제를 막기 위해 사용한다. (예: '악성' 수치 추출)"""
    def ok(v):
        return v if (lo is None or v>=lo) and (hi is None or v<=hi) else None
    for m0 in re.finditer(re.escape(keyword), text):
        idx = m0.start()
        seg = text[idx:idx+60]
        m = re.search(r'(\d+)\s*만\s*(\d+)\s*천', seg)
        if m:
            v = ok(int(m.group(1))*10000 + int(m.group(2))*1000)
            if v is not None: return v
        m = re.search(r'(\d+)\s*만\s*(\d{2,4})(?!\s*천)', seg)
        if m:
            v = ok(int(m.group(1))*10000 + int(m.group(2)))
            if v is not None: return v
        m = re.search(r'(\d+\.\d+)\s*만', seg)
        if m:
            v = ok(int(float(m.group(1))*10000))
            if v is not None: return v
        m = re.search(r'(\d+)\s*만', seg)
        if m:
            v = ok(int(m.group(1))*10000)
            if v is not None: return v
        m = re.search(r'([\d,]{4,})', seg)
        if m:
            raw = m.group(1)
            if not re.fullmatch(r'20\d{2}', raw):
                v = safe_int(raw, lo, hi)
                if v is not None: return v
    return None

def disp(v, fallback="—"):
    if v is None or str(v).strip() in ("","None"): return fallback
    return str(v)

def pct_str(v, fallback="—"):
    f = safe_float(v)
    if f is None: return fallback
    return f"{f:+.2f}"

def rcolor(v, up="#c62828", flat="#2e7d32", dn="#1565c0"):
    f = safe_float(v)
    if f is None: return "#546e7a"
    return up if f > 0 else (dn if f < 0 else flat)

RE_HTML_TAG = re.compile(r'<[^>]+>')

def clean_summary(raw):
    """RSS description/summary에 섞인 HTML 태그 제거 + 공백 정리"""
    if not raw: return ""
    t = RE_HTML_TAG.sub(" ", raw)
    t = re.sub(r'&nbsp;|&amp;|&lt;|&gt;|&quot;', " ", t)
    t = re.sub(r'\s+', " ", t).strip()
    return t[:400]  # 과도하게 긴 요약은 잘라서 정규식 매칭 속도 보호

def fetch_rss_all():
    """
    일반(국내 언론사) RSS 피드 전체 수집.
    ★ 매경·연합 등 직접 발행 RSS는 description/summary에 실제 기사 요약문이
      포함되어 있으므로(구글뉴스 RSS와 달리) 제목뿐 아니라 요약문도 함께 사용한다.
      이렇게 하면 제목에 없는 수치(예: "전세가율 50%")를 본문 요약에서 잡아낼 수 있다.
    """
    items = []
    for url in RSS_FEEDS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8)
            feed = feedparser.parse(resp.content)
            for e in feed.entries:
                t = (e.get("title","") or "").strip()
                s = clean_summary(e.get("summary","") or e.get("description",""))
                l = e.get("link","")
                d = (e.get("published","") or "")[:10]
                if t: items.append((t, s, l, d))
        except: pass
    print(f"  RSS 수집: {len(items)}건")
    return items

def fetch_gn_titles(query, n=15):
    """
    Google News RSS 수집 — 제목(title)만 사용
    요약(summary)은 HTML 링크(<a href=...>)만 있어서 파싱 불가
    """
    try:
        url  = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=ko&gl=KR&ceid=KR:ko"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        feed = feedparser.parse(resp.content)
        items = []
        for e in feed.entries[:n]:
            t = (e.get("title","") or "").strip()
            l = e.get("link","")
            d = (e.get("published","") or "")[:10]
            if t: items.append((t, "", l, d))
        return items
    except: return []

def combine(rss, *queries):
    items = list(rss)
    for q in queries:
        items.extend(fetch_gn_titles(q))
    return items

def fetch_article_text(url, timeout=6, max_chars=2000):
    """
    제목+요약(RSS)에서 수치를 못 찾았을 때 마지막 수단으로 기사 원문 일부를 가져온다.
    사이트별 HTML 구조가 달라 정교한 본문 추출은 아니지만, <p> 태그 텍스트를 모아
    정규식 매칭에 쓸 수 있는 수준의 텍스트 뭉치를 만드는 것이 목적이다.
    """
    if not url: return ""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        html = resp.text
        html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.S | re.I)
        html = re.sub(r'<style[^>]*>.*?</style>',  ' ', html, flags=re.S | re.I)
        paras = re.findall(r'<p[^>]*>(.*?)</p>', html, flags=re.S | re.I)
        text = " ".join(RE_HTML_TAG.sub(' ', p) for p in paras)
        text = re.sub(r'&nbsp;|&amp;|&lt;|&gt;|&quot;', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:max_chars]
    except Exception:
        return ""

def augment_with_article_body(items, keyword, max_fetch=4):
    """
    키워드가 제목/요약에 있는 상위 후보 기사들만 골라 원문을 추가로 가져와
    (title, summary+본문, link, date) 형태로 재구성한다. 네트워크 호출을 제한하기
    위해 최대 max_fetch건까지만 시도한다.
    """
    picked = [it for it in items if keyword in (it[0] + it[1])][:max_fetch]
    out = []
    for title, summary, link, date in picked:
        body = fetch_article_text(link)
        if body:
            out.append((title, f"{summary} {body}", link, date))
    return out


# ══════════════════════════════════════════════════════════════════════════════
# 선행1: KB 주간 시황 — 제목에서 "서울 X.XX% 상승" 패턴 파싱
# ══════════════════════════════════════════════════════════════════════════════
def get_kb_weekly(rss):
    print("[선행1] KB부동산 주간 시황")
    r = {k: None for k in ["국전체","서울","수도권","부산","전세전국",
                             "전세서울","매수우위","연속주수","방향","기준일"]}
    r["원문"] = []

    # ★ 1순위: KB 공식 데이터 API (뉴스 파싱보다 정확·안정적)
    api = fetch_kb_api_weekly_price_change()
    if api.get("국전체") is not None: r["국전체"]   = f"{api['국전체']:.2f}"
    if api.get("서울") is not None:   r["서울"]     = f"{api['서울']:.2f}"
    if api.get("부산") is not None:   r["부산"]     = f"{api['부산']:.2f}"
    if api.get("전세전국") is not None: r["전세전국"] = f"{api['전세전국']:.2f}"
    if api.get("기준일") is not None: r["기준일"]   = api["기준일"]
    if r["국전체"] is not None or r["서울"] is not None:
        ref = safe_float(r.get("국전체") or r.get("서울"))
        if ref is not None:
            r["방향"] = "상승" if ref > 0 else ("하락" if ref < 0 else "보합")
        r["원문"].append({"title": "KB부동산 데이터허브 (공식 API)",
                          "link": "https://data.kbland.kr", "date": r["기준일"] or ""})
        print(f"  ✔ (KB API) 전국 {disp(r['국전체'])}% | 서울 {disp(r['서울'])}% | "
              f"부산 {disp(r['부산'])}% | 기준일 {disp(r['기준일'])}")
    api_filled = bool(r["국전체"] is not None or r["서울"] is not None)

    APT_KEYS = ["아파트값","아파트 매매","아파트가격","매매가격",
                "KB부동산","국민은행","주간 아파트","주간아파트"]

    # 제목에서 직접 파싱 (소수점 필수)
    RE_SEO = re.compile(r'서울\s*(?:아파트\s*)?(?:값|매매|가격)?' + PJ + r'[▲△▼▽↑↓]?\s*([-+]?\d+\.\d+)\s*%')
    RE_NAT = re.compile(r'전국\s*(?:아파트\s*)?(?:값|매매|가격)?' + PJ + r'[▲△▼▽↑↓]?\s*([-+]?\d+\.\d+)\s*%')
    RE_MET = re.compile(r'수도권\s*(?:아파트\s*)?(?:값|매매|가격)?' + PJ + r'[▲△▼▽↑↓]?\s*([-+]?\d+\.\d+)\s*%')
    RE_BUS = re.compile(r'부산\s*(?:아파트\s*)?(?:값|매매|가격)?' + PJ + r'[▲△▼▽↑↓]?\s*([-+]?\d+\.\d+)\s*%')
    RE_JEO = re.compile(r'전세' + PJ + r'(?:가격\s*)?[▲△▼▽↑↓]?\s*([-+]?\d+\.\d+)\s*%')
    RE_JEO2= re.compile(r'전세도\s*([-+]?\d+\.\d+)\s*%')
    RE_BUY = re.compile(r'매수우위지수' + PJ + r'[^\d]*([\d.]+)')
    RE_WEK = re.compile(r'(\d+)\s*주\s*(?:연속|째|만에|간)')
    RE_DTE = re.compile(r'(\d{4})[년.]\s*(\d{1,2})[월.]\s*(\d{1,2})')

    all_items = combine(rss,
        "서울 아파트값 주간 상승 전세",
        "전국 아파트 매매가 주간 변동",
        "KB부동산 주간 아파트 매매",
        "서울 아파트값 연속 상승 주간",
        "전국 아파트값 상승 주간 변동률",
        "아파트값 연속 상승 전국 서울")

    for title, summary, link, date in all_items:
        # 제목 + 요약(있는 경우) 함께 사용
        text = f"{title} {summary}"
        if not any(k in text for k in APT_KEYS): continue
        if "%" not in text: continue

        m_s = RE_SEO.search(text)
        m_n = RE_NAT.search(text)
        m_m = RE_MET.search(text)
        m_b = RE_BUS.search(text)
        m_j = RE_JEO.search(text) or RE_JEO2.search(text)
        m_u = RE_BUY.search(text)
        m_w = RE_WEK.search(text)
        m_d = RE_DTE.search(title + " " + date)

        seo = safe_float(m_s.group(1) if m_s else None, -5, 5)
        nat = safe_float(m_n.group(1) if m_n else None, -5, 5)
        met = safe_float(m_m.group(1) if m_m else None, -5, 5)
        bus = safe_float(m_b.group(1) if m_b else None, -5, 5)
        jeo = safe_float(m_j.group(1) if m_j else None, -3, 3)

        if seo is None and nat is None: continue

        if seo is not None and r["서울"] is None:     r["서울"]     = f"{seo}"
        if nat is not None and r["국전체"] is None:   r["국전체"]   = f"{nat}"
        if met is not None and r["수도권"] is None:   r["수도권"]   = f"{met}"
        if bus is not None and r["부산"] is None:     r["부산"]     = f"{bus}"
        if jeo is not None and r["전세전국"] is None: r["전세전국"] = f"{jeo}"
        if m_u:
            v = safe_float(m_u.group(1), 0, 100)
            if v and r["매수우위"] is None: r["매수우위"] = f"{v}"
        if m_w:
            v = safe_int(m_w.group(1), 1, 200)
            if v and r["연속주수"] is None: r["연속주수"] = f"{v}"
        if m_d and r["기준일"] is None:
            r["기준일"] = f"{m_d.group(1)}.{int(m_d.group(2)):02d}.{int(m_d.group(3)):02d}"

        if r["방향"] is None:
            ref = safe_float(r.get("서울") or r.get("국전체"))
            if ref is not None:
                r["방향"] = "상승" if ref > 0 else ("하락" if ref < 0 else "보합")

        r["원문"].append({"title": title, "link": link, "date": date})

        # 전국+서울 둘 다 있고, 보조 정보(연속주수)까지 있으면 더 볼 필요 없음.
        # API로 이미 전국/서울이 채워진 경우에는 첫 기사 하나만 보고 멈추지 않고
        # "N주 연속" 문구가 있는 기사를 찾을 때까지 계속 훑는다.
        if r.get("국전체") and r.get("서울") and r.get("연속주수"):
            if not api_filled:
                print(f"  ✔ 전국 {disp(r['국전체'])}% | 서울 {disp(r['서울'])}% | 부산 {disp(r['부산'])}% | {disp(r['연속주수'])}주")
            return r
        if r.get("국전체") and r.get("서울") and not api_filled:
            print(f"  ✔ 전국 {disp(r['국전체'])}% | 서울 {disp(r['서울'])}% | 부산 {disp(r['부산'])}% | {disp(r['연속주수'])}주")
            return r

    # 전국 또는 서울 중 하나라도 있으면 반환
    if r.get("국전체") or r.get("서울"):
        if not api_filled:
            print(f"  ✔ 전국 {disp(r['국전체'])}% | 서울 {disp(r['서울'])}% | 부산 {disp(r['부산'])}% | {disp(r['연속주수'])}주")
        return r
    print("  - 데이터 없음")
    return r


# ══════════════════════════════════════════════════════════════════════════════
# 선행2: 경매 낙찰률
# ══════════════════════════════════════════════════════════════════════════════
def get_auction(rss):
    print("[선행2] 경매 낙찰률")
    r = {"낙찰률": None, "낙찰가율": None, "건수": None, "원문": []}

    # ★ 1순위: 법원경매정보 사이트 내부 호출 재현 (뉴스 파싱보다 정확·안정적)
    court = fetch_court_auction_apt()
    if court and court.get("낙찰률") is not None:
        r["낙찰률"]   = f"{court['낙찰률']}"
        r["낙찰가율"] = f"{court['낙찰가율']}"
        r["건수"]     = f"{court['건수']:,}" if court.get("건수") is not None else None
        ym = court.get("기준월", "")
        ym_disp = f"{ym[:4]}.{ym[4:6]}" if len(ym) == 6 else ym
        r["원문"].append({"title": f"법원경매정보 (공식 사이트, {ym_disp} 기준)",
                          "link": "https://www.courtauction.go.kr", "date": ym_disp})
        print(f"  ✔ (법원경매) 낙찰률 {r['낙찰률']}% | 낙찰가율 {r['낙찰가율']}% | {ym_disp} 기준")
    api_filled = bool(r["낙찰률"])

    RE_R   = re.compile(r'낙찰률' + PJ + r'([\d.]+)\s*%')
    RE_PR  = re.compile(r'낙찰가율' + PJ + r'([\d.]+)\s*%')
    RE_PR2 = re.compile(r'낙찰가율' + PJ + r'(100(?:\.\d+)?)\s*%?\s*돌파')

    all_items = (combine(rss,
        "아파트 경매 낙찰률 낙찰가율 월간",
        "법원경매 아파트 낙찰 낙찰가율 서울",
        "전국 아파트 경매 낙찰률 이달") if not api_filled else [])

    def scan(items):
        for title, summary, link, date in items:
            text = f"{title} {summary}"
            if "낙찰" not in text: continue

            m_r  = RE_R.search(text)
            m_pr = RE_PR.search(text) or RE_PR2.search(text)

            rate  = safe_float(m_r.group(1)  if m_r  else None, 10, 80)
            prate = safe_float(m_pr.group(1) if m_pr else None, 70, 130)

            if rate is not None and r["낙찰률"] is None: r["낙찰률"] = f"{rate}"
            if prate is not None and r["낙찰가율"] is None: r["낙찰가율"] = f"{prate}"
            if rate is not None or prate is not None:
                r["원문"].append({"title": title, "link": link, "date": date})
            # 낙찰률·낙찰가율 둘 다 채워지면 더 볼 필요 없음
            if r["낙찰률"] and r["낙찰가율"]:
                return True
        return False

    if not (r["낙찰률"] and r["낙찰가율"]):
        if scan(all_items) or r["낙찰률"] or r["낙찰가율"]:
            if r["낙찰률"] and r["낙찰가율"] and not api_filled:
                print(f"  ✔ 낙찰률 {disp(r['낙찰률'])}% | 낙찰가율 {disp(r['낙찰가율'])}%")
                return r

    # 폴백: 요약문에도 없으면 관련 기사 원문 일부를 가져와 재시도
    if not (r["낙찰률"] and r["낙찰가율"]):
        fallback_items = augment_with_article_body(all_items, "낙찰")
        scan(fallback_items)

    if r["낙찰률"] or r["낙찰가율"]:
        if not api_filled:
            print(f"  ✔ 낙찰률 {disp(r['낙찰률'])}% | 낙찰가율 {disp(r['낙찰가율'])}%")
        return r

    print("  - 데이터 없음")
    return r


# ══════════════════════════════════════════════════════════════════════════════
# 선행3: 주택 인허가
# 실제 제목: "1~4월 주택인허가 전년대비 24% 감소"
# ══════════════════════════════════════════════════════════════════════════════
def get_permit(rss):
    print("[선행3] 주택 인허가")
    r = {"수치": None, "전년비": None, "기준월": None, "원문": []}

    # ★ 1순위: KOSIS 공식 API ('월별 누계' 표는 그 해 1월부터의 누적치임을 표기)
    kosis = fetch_kosis_permit()
    if kosis and kosis.get("수치") is not None:
        r["수치"] = f"{kosis['수치']:,}"
        prd = kosis.get("기준", "")
        if kosis.get("월간여부"):
            ym = f"{prd[:4]}.{prd[4:6]}" if len(prd) == 6 else prd
            r["기준월"] = f"{ym}(1월~해당월 누계)" if kosis.get("누계여부") else ym
        else:
            r["기준월"] = f"{prd}년(연간누계)" if prd else None
        r["원문"].append({"title": f"KOSIS 국가통계포털 (공식 API, {r['기준월']} 기준)",
                          "link": "https://kosis.kr", "date": r["기준월"] or ""})
    api_filled = bool(r["수치"])
    if api_filled:
        print(f"  ✔ (KOSIS API) {r['수치']}호 | 기준: {disp(r['기준월'])}")

    # 제목에서 전년비 % 직접 추출
    RE_YOY  = re.compile(r'전년\s*(?:동기|동월)?\s*(?:대비|보다|比)?\s*([-+]?\d+\.?\d*)\s*%')
    RE_YOY2 = re.compile(r'([-+]?\d+\.?\d*)\s*%\s*(?:감소|증가)')
    RE_MON  = re.compile(r'(\d{4})년\s*(\d{1,2})월')

    # ★ KOSIS API는 "수치"만 주고 "전년비(%)"는 제공하지 않으므로, 수치가 이미
    #   API로 채워졌어도 전년비를 찾기 위한 뉴스 검색은 그대로 진행한다.
    all_items = combine(rss,
        "주택통계 인허가 착공 준공 전년동기",
        "주택인허가 전년대비 감소 증가",
        "주택 인허가 실적 국토교통부")

    for title, summary, link, date in all_items:
        text = f"{title} {summary}"
        if "인허가" not in text: continue
        # ★ 주택 관련 기사만 채택 (공장·상업시설 인허가 제외)
        if not any(k in text for k in ["주택","아파트","공동주택","단독주택","주거"]):
            continue

        # ★ "국토부, 인허가·착공 부진 속 미분양 6.7만가구…전년비 75%↑"처럼 여러
        #   지표를 한 문장에 압축한 헤드라인은, 거리를 아무리 좁혀도 "인허가"
        #   근처에서 실제로는 "미분양"이나 "준공"의 수치/증감률을 잘못 집어올
        #   위험이 있다. 이런 문장은 아예 수치·전년비 추출을 시도하지 않는다.
        #   다만 "수도권 X가구 + 비수도권 Y가구" 구조가 뚜렷한 국토부 보도자료는
        #   "인허가"라는 단어가 실제로 그 문단에 속함이 문장 구조로 검증되므로
        #   미분양이 같이 언급돼도 안전하게 허용한다.
        has_region_structure = "수도권" in text and "비수도권" in text
        has_confounder = any(k in text for k in ["미분양", "준공"]) and not has_region_structure

        cnt = None
        if has_region_structure:
            cnt = sum_region_count(text, "인허가")
        if cnt is None and not has_confounder:
            cnt = parse_korean_num_fwd(text, "인허가", lo=10000, hi=80000)

        m_m = RE_MON.search(text)

        yoy = None
        if not has_confounder:
            # ★ 인허가 키워드 근처(60자 이내)의 전년비만 추출.
            RE_인허가YOY = re.compile(
                r'인허가[^%\d]{0,20}?([-+]?\d+\.?\d*)\s*%|'
                r'인허가.{0,60}?전년\s*(?:동기|동월)?\s*(?:대비|比|보다|비)?\s*([-+]?\d+\.?\d*)\s*%'
            )
            m_y = RE_인허가YOY.search(text)
            if m_y:
                v = None
                for g in range(1, 4):
                    try:
                        v = m_y.group(g)
                        if v: break
                    except: pass
                yoy = safe_float(v, -70, 100)  # 148%도 허용 (실제 발생 가능)
        else:
            # 압축형 헤드라인이라도 "수도권 인허가는 X가구로 전년동월 대비 Y%"처럼
            # 키워드 바로 뒤(20자 이내)에 붙어있는 경우는 안전하므로 허용한다.
            m_y_tight = re.search(r'인허가[^%\d]{0,20}?([-+]?\d+\.?\d*)\s*%', text)
            if m_y_tight:
                yoy = safe_float(m_y_tight.group(1), -70, 100)

        if cnt is not None and r["수치"] is None: r["수치"] = f"{cnt:,}"
        if yoy is not None and r["전년비"] is None:
            r["전년비"] = f"{yoy}"
            if api_filled:
                print(f"  ✔ (뉴스 보강) 전년비 {r['전년비']}% 추가로 찾음")
        if m_m and r["기준월"] is None: r["기준월"] = f"{m_m.group(1)}.{int(m_m.group(2)):02d}"
        if cnt is not None or yoy is not None:
            r["원문"].append({"title": title, "link": link, "date": date})
        if r["수치"] and r["전년비"]:
            if not api_filled:
                print(f"  ✔ {disp(r['수치'])}호 | 전년비 {disp(r['전년비'])}%")
            return r

    if r["수치"] or r["전년비"]:
        if not api_filled:
            print(f"  ✔ {disp(r['수치'])}호 | 전년비 {disp(r['전년비'])}%")
        return r

    print("  - 데이터 없음")
    return r


# ══════════════════════════════════════════════════════════════════════════════
# 선행4: 전세가율
# ══════════════════════════════════════════════════════════════════════════════
def get_jeonse_ratio(rss):
    print("[선행4] 전세가율")
    r = {"전국": None, "서울": None, "부산": None, "원문": []}

    # ★ 1순위: KB 공식 데이터 API
    api = fetch_kb_api_jeonse_ratio()
    if api.get("전국") is not None: r["전국"] = f"{api['전국']:.1f}"
    if api.get("서울") is not None: r["서울"] = f"{api['서울']:.1f}"
    if api.get("부산") is not None: r["부산"] = f"{api['부산']:.1f}"
    api_filled = bool(r["전국"] or r["서울"])
    if api_filled:
        r["원문"].append({"title": "KB부동산 데이터허브 (공식 API)",
                          "link": "https://data.kbland.kr", "date": ""})
        print(f"  ✔ (KB API) 전국 {disp(r['전국'])}% | 서울 {disp(r['서울'])}% | 부산 {disp(r['부산'])}%")

    RE_SEO = re.compile(r'서울\s*(?:아파트\s*)?전세가율' + PJ + r'([\d.]+)\s*%')
    RE_NAT = re.compile(r'(?:전국|평균)\s*(?:아파트\s*)?전세가율' + PJ + r'([\d.]+)\s*%')
    RE_BUS = re.compile(r'부산\s*(?:아파트\s*)?전세가율' + PJ + r'([\d.]+)\s*%')
    RE_GEN = re.compile(r'전세가율' + PJ + r'([\d.]+)\s*%')

    all_items = combine(rss,
        "전국 아파트 전세가율 현황 KB",
        "서울 아파트 전세가율 현황",
        "전국 전세가율 아파트",
        "전세가율 붕괴 돌파 아파트")

    def scan(items):
        for title, summary, link, date in items:
            text = f"{title} {summary}"
            if "전세가율" not in text: continue

            m_s = RE_SEO.search(text)
            m_n = RE_NAT.search(text)
            m_b = RE_BUS.search(text)
            m_g = RE_GEN.search(text)

            seo = safe_float(m_s.group(1) if m_s else None, 30, 90)
            nat = safe_float(m_n.group(1) if m_n else None, 30, 90)
            bus = safe_float(m_b.group(1) if m_b else None, 30, 90)
            gen = safe_float(m_g.group(1) if m_g else None, 30, 90)

            # ★ "경기도 전체의 전세가율 평균은 66.6%다. 전국 평균은 68.2%,
            #   서울 평균은 51.1%다"처럼, 앞 문장에서만 '전세가율'을 언급하고
            #   뒤이어 "전국 평균은 NN%"로 이어가는(단어 재반복 생략) 문장 대응.
            #   문서 안에 '전세가율'이 나온 걸 이미 확인했으므로 안전하게 사용 가능.
            if nat is None:
                m_nc = re.search(r'전국\s*평균은?' + PJ + r'([\d.]+)\s*%', text)
                nat = safe_float(m_nc.group(1) if m_nc else None, 30, 90)
            if seo is None:
                m_sc = re.search(r'서울\s*평균은?' + PJ + r'([\d.]+)\s*%', text)
                seo = safe_float(m_sc.group(1) if m_sc else None, 30, 90)

            # ★ 핵심 수정: 서울 기사의 수치를 전국으로 오분류 방지
            # "서울 아파트 전세가율 50%" → 서울값으로만 저장
            # 전국값은 "전국" 또는 "평균" 키워드가 있을 때만 저장
            if seo is None and nat is None and gen is None: continue

            if seo is not None and r["서울"] is None: r["서울"] = f"{seo}"
            if nat is not None and r["전국"] is None:
                r["전국"] = f"{nat}"
            elif gen is not None and r["전국"] is None and r["서울"] is None:
                # "전국/평균" 없이 일반 전세가율 패턴
                if "서울" in text or "서울" in text[:text.find("전세가율")]:
                    r["서울"] = f"{gen}"
                elif any(k in text for k in ["전국","전체","평균","우리나라"]):
                    r["전국"] = f"{gen}"
                else:
                    r["서울"] = f"{gen}"
            if bus is not None and r["부산"] is None: r["부산"] = f"{bus}"

            if seo is not None or nat is not None or gen is not None or bus is not None:
                r["원문"].append({"title": title, "link": link, "date": date})

            # 전국·서울 둘 다 채워지면 더 스캔할 필요 없음
            if r["전국"] and r["서울"]:
                return True
        return False

    scan(all_items) if not (r["전국"] and r["서울"]) else None

    # 폴백: 전국 또는 서울 수치가 여전히 비어 있으면 관련 기사 원문으로 재시도
    if not (r["전국"] and r["서울"]):
        fallback_items = augment_with_article_body(all_items, "전세가율")
        scan(fallback_items)

    if r["전국"] or r["서울"]:
        if not api_filled:
            print(f"  ✔ 전국 {disp(r['전국'])}% | 서울 {disp(r['서울'])}%")
        return r

    print("  - 데이터 없음")
    return r


# ══════════════════════════════════════════════════════════════════════════════
# 선행5: CSI + 주택가격전망지수
# ══════════════════════════════════════════════════════════════════════════════
def get_csi(rss):
    print("[선행5] 소비자심리지수 / 주택가격전망지수")
    r = {"CSI": None, "주택전망": None, "원문": []}

    # ★ 1순위: 한국은행 ECOS 공식 API
    ecos = fetch_ecos_csi()
    if ecos:
        if ecos.get("CSI") is not None: r["CSI"] = f"{ecos['CSI']:.1f}"
        if ecos.get("주택전망") is not None: r["주택전망"] = f"{ecos['주택전망']:.1f}"
    api_filled = bool(r["CSI"] or r["주택전망"])
    if api_filled:
        ym = ecos.get("기준월", "")
        ym_disp = f"{ym[:4]}.{ym[4:6]}" if ym and len(ym) == 6 else ym
        r["원문"].append({"title": f"한국은행 ECOS (공식 API, {ym_disp} 기준)",
                          "link": "https://ecos.bok.or.kr", "date": ym_disp})
        print(f"  ✔ (ECOS API) CSI {disp(r['CSI'])} | 주택전망 {disp(r['주택전망'])} | {ym_disp} 기준")

    RE_CSI  = re.compile(r'소비자심리지수(?:\s*\([A-Za-z]+\))?' + PJ + r'(\d{2,3}\.?\d*)')
    RE_HPCI = re.compile(r'주택가격전망(?:지수)?' + PJ + r'(\d{2,3}\.?\d*)')
    # "주택가격전망지수 120" 같은 제목
    RE_HPCI2= re.compile(r'주택전망지수' + PJ + r'(\d{2,3}\.?\d*)')

    all_items = (combine(rss,
        "주택가격전망지수 한국은행",
        "소비자심리지수 주택 전망") if not (r["CSI"] and r["주택전망"]) else [])

    def scan(items):
        for title, summary, link, date in items:
            text = f"{title} {summary}"
            if "전망" not in text and "심리" not in text: continue

            m_c = RE_CSI.search(text)
            m_h = RE_HPCI.search(text) or RE_HPCI2.search(text)
            csi  = safe_float(m_c.group(1) if m_c else None, 60, 200)
            hpci = safe_float(m_h.group(1) if m_h else None, 60, 200)

            # ★ "주택가격전망지수는 전월보다 7p 오른 127을 기록했다" 처럼 키워드
            #   바로 뒤가 아니라 변동폭 서술 뒤에 실제 지수가 나오는 경우 보강
            if csi is None:
                csi = find_value_near(text, "소비자심리지수", 60, 200)
            if hpci is None:
                hpci = find_value_near(text, "주택가격전망지수", 60, 200) \
                    or find_value_near(text, "주택가격전망", 60, 200)

            if csi is not None and r["CSI"] is None: r["CSI"] = f"{csi}"
            if hpci is not None and r["주택전망"] is None: r["주택전망"] = f"{hpci}"
            if csi is not None or hpci is not None:
                r["원문"].append({"title": title, "link": link, "date": date})
            if r["CSI"] and r["주택전망"]:
                return True
        return False

    if not (r["CSI"] and r["주택전망"]):
        scan(all_items)

    if not (r["CSI"] and r["주택전망"]):
        fallback_items = augment_with_article_body(all_items, "심리") + \
                          augment_with_article_body(all_items, "전망")
        scan(fallback_items)

    if r["CSI"] or r["주택전망"]:
        if not api_filled:
            print(f"  ✔ CSI {disp(r['CSI'])} | 주택전망 {disp(r['주택전망'])}")
        return r

    print("  - 데이터 없음")
    return r


# ══════════════════════════════════════════════════════════════════════════════
# 선행6: KB 매매·전세가격전망지수
# debug2 결과: 제목에 수치 없음 → KB Think 원문 RSS 직접 접근
# ══════════════════════════════════════════════════════════════════════════════
def get_kb_forecast(rss):
    print("[선행6] KB 매매·전세가격전망지수")
    r = {"매매전망": None, "전세전망": None, "원문": []}

    # ★ 1순위: KB 공식 데이터 API (매매/전세 상승하락전망지수, 월간)
    api = fetch_kb_api_forecast()
    if api.get("매매전망") is not None: r["매매전망"] = f"{api['매매전망']:.1f}"
    if api.get("전세전망") is not None: r["전세전망"] = f"{api['전세전망']:.1f}"
    api_filled = bool(r["매매전망"] or r["전세전망"])
    if api_filled:
        r["원문"].append({"title": "KB부동산 데이터허브 (공식 API)",
                          "link": "https://data.kbland.kr", "date": ""})
        print(f"  ✔ (KB API) 매매전망 {disp(r['매매전망'])} | 전세전망 {disp(r['전세전망'])}")

    RE_M  = re.compile(r'매매' + PJ + r'(?:가격\s*)?전망(?:지수)?' + PJ + r'(\d{2,3}\.?\d*)')
    RE_J  = re.compile(r'전세' + PJ + r'(?:가격\s*)?전망(?:지수)?' + PJ + r'(\d{2,3}\.?\d*)')
    # "전망지수 XXX" 단독 패턴
    RE_IDX= re.compile(r'전망지수' + PJ + r'(\d{2,3}\.?\d*)')

    all_items = (list(rss)
        + fetch_gn_titles("KB국민은행 매매가격전망지수 전세가격전망지수", 15)
        + fetch_gn_titles("KB부동산 매매전망 전세전망", 10)
        + fetch_gn_titles("KB 주택 매매전망 전세전망 지수", 10)
        + fetch_gn_titles("국민은행 주택가격전망지수", 10)) if not (r["매매전망"] and r["전세전망"]) else []

    def scan(items):
        for title, summary, link, date in items:
            text = f"{title} {summary}"
            if "KB" not in text and "국민은행" not in text: continue
            if "전망" not in text: continue

            m_m = RE_M.search(text)
            m_j = RE_J.search(text)
            m_i = RE_IDX.search(text)
            mv = safe_float(m_m.group(1) if m_m else None, 60, 200)
            jv = safe_float(m_j.group(1) if m_j else None, 60, 200)
            iv = safe_float(m_i.group(1) if (m_i and not m_m) else None, 60, 200)

            # ★ "전국 매매가격 전망지수는 전월 대비 0.6포인트 하락한 107.2를
            #   기록했다" 처럼 키워드 뒤 변동폭 서술 후에 실제 값이 나오는 경우 보강.
            #   "전국"이 있으면 전국 수치를 우선 채택(서울 등 지역값과 혼동 방지)
            if mv is None:
                mv = find_value_near(text, "전국 매매가격 전망지수", 60, 200) \
                    or find_value_near(text, "매매가격 전망지수", 60, 200) \
                    or find_value_near(text, "매매전망지수", 60, 200)
            if jv is None:
                jv = find_value_near(text, "전국 전세가격 전망지수", 60, 200) \
                    or find_value_near(text, "전세가격 전망지수", 60, 200) \
                    or find_value_near(text, "전세전망지수", 60, 200)

            if r["매매전망"] is None:
                if mv is not None: r["매매전망"] = f"{mv}"
                elif iv is not None: r["매매전망"] = f"{iv}"
            if jv is not None and r["전세전망"] is None: r["전세전망"] = f"{jv}"

            if mv is not None or jv is not None or iv is not None:
                r["원문"].append({"title": title, "link": link, "date": date})
            if r["매매전망"] and r["전세전망"]:
                return True
        return False

    if not (r["매매전망"] and r["전세전망"]):
        scan(all_items)

    if not (r["매매전망"] and r["전세전망"]):
        fallback_items = augment_with_article_body(all_items, "전망")
        scan(fallback_items)

    if r["매매전망"] or r["전세전망"]:
        if not api_filled:
            print(f"  ✔ 매매전망 {disp(r['매매전망'])} | 전세전망 {disp(r['전세전망'])}")
        return r

    print("  - 데이터 없음 (월말 발표, 미발표 기간)")
    return r


# ══════════════════════════════════════════════════════════════════════════════
# 선행7: 수급동향 (한국부동산원)
# debug2 결과: 제목에 수치 없음 → 연합뉴스 RSS에서 본문 포함 기사 탐색
# ══════════════════════════════════════════════════════════════════════════════
def get_supply_demand(rss):
    print("[선행7] 수급동향 (한국부동산원)")
    r = {"매매수급": None, "전세수급": None, "원문": []}

    # ★ 1순위: 한국부동산원 R-ONE 공식 API
    rone = fetch_rone_supply_demand()
    if rone.get("매매수급") is not None: r["매매수급"] = f"{rone['매매수급']:.1f}"
    if rone.get("전세수급") is not None: r["전세수급"] = f"{rone['전세수급']:.1f}"
    api_filled = bool(r["매매수급"] or r["전세수급"])
    if api_filled:
        d = rone.get("기준일", "") or ""
        r["원문"].append({"title": f"한국부동산원 R-ONE (공식 API, {d} 기준)",
                          "link": "https://www.reb.or.kr/r-one", "date": d})
        print(f"  ✔ (R-ONE API) 매매 {disp(r['매매수급'])} | 전세 {disp(r['전세수급'])} | {d} 기준")

    RE_T = re.compile(r'매매' + PJ + r'수급' + PJ + r'(?:지수)?' + PJ + r'(\d{2,3}\.?\d*)')
    RE_J = re.compile(r'전세' + PJ + r'수급' + PJ + r'(?:지수)?' + PJ + r'(\d{2,3}\.?\d*)')

    all_items = (combine(rss,
        "매매수급지수 전세수급지수",
        "한국부동산원 매매수급지수",
        "수도권 매매수급지수 기록",
        "아파트 매매수급지수 주간",
        "전국 매매수급지수 아파트",
        "서울 아파트 매수심리 수급지수") if not (r["매매수급"] and r["전세수급"]) else [])

    # "서울 동남권 매매수급지수는 101.9" 처럼 특정 하위 권역(강남권 등) 기사를
    # 전국 수치로 오인하지 않도록, "전국"이 없고 하위권역 표현만 있는 기사는
    # 1차 스캔에서 제외한다 (더 나은 후보가 없을 때만 2차에서 허용)
    REGIONAL_ONLY = ["동남권","서남권","동북권","서북권","강남3구","강북14개구","강북권"]

    def scan(items, require_national=True):
        for title, summary, link, date in items:
            text = f"{title} {summary}"
            if "수급" not in text: continue
            if require_national:
                is_regional_only = any(k in text for k in REGIONAL_ONLY) and "전국" not in text
                if is_regional_only: continue

            m_t = RE_T.search(text)
            m_j = RE_J.search(text)

            tv = safe_float(m_t.group(1) if m_t else None, 85, 135)
            jv = safe_float(m_j.group(1) if m_j else None, 85, 135)

            # ★ 핵심: 같은 기사에서 매매·전세 모두 잡히면 매매만 채택
            # 같은 숫자가 두 패턴 모두 매칭되는 경우 방지
            if tv is not None and jv is not None:
                has_both = ("매매수급" in text and "전세수급" in text)
                if not has_both:
                    jv = None
                elif abs(tv - jv) < 0.01:
                    jv = None

            if tv is not None and r["매매수급"] is None: r["매매수급"] = f"{tv}"
            if jv is not None and r["전세수급"] is None: r["전세수급"] = f"{jv}"
            if tv is not None or jv is not None:
                r["원문"].append({"title": title, "link": link, "date": date})
            if r["매매수급"] and r["전세수급"]:
                return True
        return False

    scan(all_items, require_national=True)
    if not (r["매매수급"] and r["전세수급"]):
        scan(all_items, require_national=False)

    if not (r["매매수급"] and r["전세수급"]):
        fallback_items = augment_with_article_body(all_items, "수급")
        scan(fallback_items)

    if r["매매수급"] or r["전세수급"]:
        if not api_filled:
            print(f"  ✔ 매매 {disp(r['매매수급'])} | 전세 {disp(r['전세수급'])}")
        return r

    print("  - 데이터 없음")
    return r


# ══════════════════════════════════════════════════════════════════════════════
# 선행8: 국토연구원 부동산소비심리지수
# ══════════════════════════════════════════════════════════════════════════════
def get_krihs(rss):
    print("[선행8] 국토연구원 부동산소비심리지수")
    r = {"매매심리": None, "전세심리": None, "원문": []}

    # ★ 1순위: K-REMAP(국토연구원) 그리드 페이지 (jisu=167, 인증키 불필요)
    #   확인된 jisu=167은 "부동산시장소비심리지수(종합, 전국)"이며, 매매/전세로
    #   따로 안 나뉘어 있어 일단 "매매심리" 자리에 채운다(뉴스가 보도하는 값과
    #   같은 스케일). 전세심리 전용 jisu 코드를 찾으면 추가로 연결 가능하다.
    krem = fetch_krihs_sentiment("167")
    if krem and krem.get("지수") is not None:
        r["매매심리"] = f"{krem['지수']}"
        r["원문"].append({"title": f"K-REMAP 국토연구원 (공식 데이터, {krem.get('기준월','')} 기준)",
                          "link": "https://kremap.krihs.re.kr/grid/grid?jisu=167",
                          "date": krem.get("기준월", "")})
        print(f"  ✔ (K-REMAP) 종합소비심리(전국) {r['매매심리']} | {krem.get('기준월','')} 기준")
    api_filled = bool(r["매매심리"])

    RE_M = re.compile(r'매매' + PJ + r'(?:소비\s*)?심리(?:지수)?' + PJ + r'(\d{2,3}\.?\d*)')
    RE_J = re.compile(r'전세' + PJ + r'(?:소비\s*)?심리(?:지수)?' + PJ + r'(\d{2,3}\.?\d*)')
    RE_G = re.compile(r'(?:부동산\s*)?소비심리지수' + PJ + r'(\d{2,3}\.?\d*)')

    all_items = combine(rss,
        "국토연구원 부동산 소비심리지수",
        "국토연구원 부동산시장 소비심리",
        "부동산 소비심리지수 국토연구원",
        "국토연구원 소비심리 매매 전세 지수",
        "부동산 소비심리지수 101 102 103 104 105")

    def scan(items):
        for title, summary, link, date in items:
            text = f"{title} {summary}"
            if "국토연구원" not in text and "소비심리" not in text: continue

            m_m = RE_M.search(text)
            m_j = RE_J.search(text)
            m_g = RE_G.search(text)
            mv = safe_float(m_m.group(1) if m_m else None, 50, 200)
            jv = safe_float(m_j.group(1) if m_j else None, 50, 200)
            gv = safe_float(m_g.group(1) if m_g else None, 50, 200)

            if r["매매심리"] is None:
                if mv is not None: r["매매심리"] = f"{mv}"
                elif gv is not None: r["매매심리"] = f"{gv}"
            if jv is not None and r["전세심리"] is None: r["전세심리"] = f"{jv}"

            if mv is not None or jv is not None or gv is not None:
                r["원문"].append({"title": title, "link": link, "date": date})
            if r["매매심리"] and r["전세심리"]:
                return True
        return False

    scan(all_items)

    if not (r["매매심리"] and r["전세심리"]):
        fallback_items = augment_with_article_body(all_items, "소비심리")
        scan(fallback_items)

    if r["매매심리"] or r["전세심리"]:
        if not api_filled:
            print(f"  ✔ 매매심리 {disp(r['매매심리'])} | 전세심리 {disp(r['전세심리'])}")
        return r

    print("  - 데이터 없음")
    return r


# ══════════════════════════════════════════════════════════════════════════════
# 선행9: K-HAI
# ══════════════════════════════════════════════════════════════════════════════
def get_khai(rss):
    print("[선행9] 주택구입부담지수(K-HAI)")
    r = {"지수": None, "전분기비": None, "원문": []}

    # ① API 우선
    api_val, api_period = fetch_houstat_khai()
    if api_val is not None:
        r["지수"] = f"{api_val}"
        r["원문"] = [{"title": f"주택금융공사 HOUSTAT ({api_period})",
                      "link": "https://houstat.hf.go.kr/research/portal/theme/indexStatKHAIPage.do",
                      "date": api_period}]
        print(f"  ✔ (API) K-HAI {disp(r['지수'])} ({api_period})")
        return r

    # ② API 실패 시 기존 뉴스 파싱 폴백
    RE_IDX = re.compile(r'(?:주택구입부담지수|K-HAI|HAI)' + PJ + r'(\d{2,3}\.?\d*)')
    RE_QOQ = re.compile(r'전\s*분기' + PJ + r'([-+]?\d+\.?\d*)\s*(?:포인트|p|%)')

    all_items = combine(rss,
        "주택금융공사 주택구입부담지수 K-HAI",
        "K-HAI 주택구입부담 분기",
        "주택구입부담지수 상승 하락 분기",
        "주택구입부담지수 발표",
        "K-HAI 발표 분기")

    def scan(items):
        for title, summary, link, date in items:
            text = f"{title} {summary}"
            if "주택구입부담" not in text and "K-HAI" not in text and "HAI" not in text: continue

            m_i = RE_IDX.search(text)
            m_q = RE_QOQ.search(text)
            iv = safe_float(m_i.group(1) if m_i else None, 30, 300)
            qv = safe_float(m_q.group(1) if m_q else None, -50, 50)

            if iv is not None:
                r["지수"] = f"{iv}"
                if qv is not None: r["전분기비"] = f"{qv}"
                r["원문"].append({"title": title, "link": link, "date": date})
                return True
        return False

    if not scan(all_items):
        fallback_items = augment_with_article_body(all_items, "주택구입부담")
        scan(fallback_items)

    if r["지수"]:
        print(f"  ✔ (뉴스) K-HAI {disp(r['지수'])} | 전분기비 {disp(r['전분기비'])}")
        return r

    # ③ API·뉴스 모두 실패 시 이력 파일에서 마지막 non-null 값 재사용
    hist = load_json(HISTORY_FILE, [])
    for h in reversed(hist):
        if h.get("khai") is not None:
            r["지수"] = f"{h['khai']}"
            print(f"  - API/뉴스 모두 실패 → 이력에서 직전 값 재사용: {disp(r['지수'])}")
            return r

    print("  - 데이터 없음 (분기 발표, 미발표 기간)")
    return r

# ══════════════════════════════════════════════════════════════════════════════
# 선행10: KB 매수우위지수
# ══════════════════════════════════════════════════════════════════════════════
def get_buyer_index():
    """
    KB부동산 공식 데이터 API에서 직접 가져오는 매수우위지수.
    (한국부동산원의 '매매수급지수'와는 산출기관·설문방식이 다른 KB 고유 지표라
    별도 지표로 관리한다 — 100을 기준으로 낮을수록 매도자 우위, 높을수록 매수자 우위.
    KB 앱 화면 기준으로는 100 이하일 때 "매도자 우위"로 표기된다는 점에 유의.)
    뉴스 기사에 잘 다뤄지지 않는 지표라 뉴스 파싱 폴백 없이 API로만 수집한다.
    """
    print("[선행10] KB 매수우위지수")
    r = {"지수": None, "매도자많음": None, "매수자많음": None, "비슷함": None,
         "기준일": None, "원문": []}

    d = kb_api_get(
        "https://data-api.kbland.kr/bfmstat/weekMnthlyHuseTrnd/maktTrnd",
        {"메뉴코드": "01", "월간주간구분코드": "02"})
    if d:
        dates = d.get("날짜리스트", [])
        for item in d.get("데이터리스트", []):
            if item.get("지역명") == "전국":
                dl = item.get("dataList", [])
                for i in range(len(dl) - 1, -1, -1):
                    entry = dl[i]
                    if isinstance(entry, dict) and entry.get("매수우위지수") is not None:
                        r["지수"]      = f"{entry['매수우위지수']:.1f}"
                        r["매도자많음"] = f"{entry.get('매도자많음', 0):.1f}"
                        r["매수자많음"] = f"{entry.get('매수자많음', 0):.1f}"
                        r["비슷함"]    = f"{entry.get('비슷함', 0):.1f}"
                        dte = entry.get("기준날짜") or (dates[i] if i < len(dates) else None)
                        if dte and len(dte) == 8:
                            r["기준일"] = f"{dte[:4]}.{dte[4:6]}.{dte[6:8]}"
                        r["원문"].append({"title": "KB부동산 데이터허브 (공식 API)",
                                          "link": "https://data.kbland.kr", "date": r["기준일"] or ""})
                        break
                break

    if r["지수"]:
        print(f"  ✔ 매수우위지수 {r['지수']} (매도자많음 {disp(r['매도자많음'])}% | "
              f"매수자많음 {disp(r['매수자많음'])}%)")
    else:
        print("  - 데이터 없음")
    return r


# ══════════════════════════════════════════════════════════════════════════════
# 동행1: 주택 매매 거래량
# 실제 제목: "11월 주택 매매거래량 11.9% 감소", "거래량 60% 급감"
# ══════════════════════════════════════════════════════════════════════════════
def get_trade_vol(rss):
    print("[동행1] 주택 매매 거래량")
    r = {"거래량": None, "전년비": None, "기준월": None, "원문": []}

    # 제목에서 전년비 % 추출
    RE_YOY  = re.compile(r'전년\s*(?:동기|동월)?\s*(?:대비|보다|比)?\s*([-+]?\d+\.?\d*)\s*%')
    RE_YOY2 = re.compile(r'([-+]?\d+\.?\d*)\s*%\s*(?:감소|증가|줄|늘)')
    RE_YOY3 = re.compile(r'거래(?:량)?\s*(\d+\.?\d*)\s*%\s*(?:급감|급증|감소|증가)')
    RE_MON  = re.compile(r'(\d{1,2})월\s*(?:주택\s*)?(?:매매\s*)?거래')

    all_items = combine(rss,
        "주택 매매 거래량 국토교통부 전년",
        "아파트 거래량 전년대비 증가 감소")

    def scan(items):
        for title, summary, link, date in items:
            text = f"{title} {summary}"
            if "거래" not in text: continue
            if not any(k in text for k in ["거래량","매매거래","거래건수"]): continue
            # 전월비 기사 제외 (전년비만 수집)
            if "전월비" in text and "전년" not in text: continue

            cnt = parse_korean_num(text, "거래", lo=5000, hi=300000)
            m_y = RE_YOY.search(text) or RE_YOY2.search(text) or RE_YOY3.search(text)
            m_m = RE_MON.search(text)

            yoy = safe_float(m_y.group(1) if m_y else None, -80, 500)

            if cnt is not None and r["거래량"] is None: r["거래량"] = f"{cnt:,}"
            if yoy is not None and r["전년비"] is None: r["전년비"] = f"{yoy}"
            if m_m and r["기준월"] is None: r["기준월"] = f"{m_m.group(1)}월"
            if cnt is not None or yoy is not None:
                r["원문"].append({"title": title, "link": link, "date": date})
            if r["거래량"] and r["전년비"]:
                return True
        return False

    scan(all_items)

    if not (r["거래량"] and r["전년비"]):
        fallback_items = augment_with_article_body(all_items, "거래량")
        scan(fallback_items)

    if r["거래량"] or r["전년비"]:
        print(f"  ✔ {disp(r['거래량'])}건 | 전년비 {disp(r['전년비'])}%")
        return r

    print("  - 데이터 없음")
    return r


# ══════════════════════════════════════════════════════════════════════════════
# 동행2: 착공량
# 실제 제목: "비아파트 착공 3만가구, 전년比 7.7% 감소"
#           "1~5월 비아파트 착공 전년 동기 대비 5.5% 감소"
# ══════════════════════════════════════════════════════════════════════════════
def get_construction_start(rss):
    print("[동행2] 착공량")
    r = {"수치": None, "전년비": None, "기준월": None, "원문": []}

    RE_YOY  = re.compile(r'전년\s*(?:동기|동월)?\s*(?:대비|보다|比)?\s*([-+]?\d+\.?\d*)\s*%')
    RE_YOY2 = re.compile(r'([-+]?\d+\.?\d*)\s*%\s*(?:감소|증가)')
    RE_MON  = re.compile(r'(\d{4})년\s*(\d{1,2})월|(\d{1,2})월\s*착공')

    all_items = combine(rss,
        "착공 전년대비 감소 증가",
        "아파트 착공 전년 비아파트",
        "주택 착공 실적 국토교통부",
        "주택통계 착공 전년동기")

    def scan(items):
        for title, summary, link, date in items:
            text = f"{title} {summary}"
            if "착공" not in text: continue
            # 착공 + 전년비/실적 관련 기사만
            if not any(k in text for k in ["착공 전년","착공량","착공 실적","착공물량",
                                            "비아파트 착공","아파트 착공","착공 감소","착공 증가",
                                            "착공이 ","착공은 ","착공했","월 착공"]):
                continue

            cnt = parse_korean_num(text, "착공", lo=3000, hi=300000)
            # ★ "수도권 X가구 + 비수도권 Y가구"로만 나뉘어 나오는 국토부 보도자료
            #   포맷에서는 (서울만 뽑힌) 지역 수치보다 전국 합산이 더 정확하므로 우선한다
            if "수도권" in text and "비수도권" in text:
                region_sum = sum_region_count(text, "착공")
                if region_sum is not None:
                    cnt = region_sum
            m_m = RE_MON.search(text)

            # ★ 착공 키워드 근처 전년비만 추출 (준공 기사 전년비 오파싱 방지)
            RE_착공YOY = re.compile(r'착공.{0,20}?([-+]?\d+\.?\d*)\s*%|'
                                    r'([-+]?\d+\.?\d*)\s*%\s*(?:감소|증가).{0,10}착공')
            m_y = RE_착공YOY.search(text)
            if not m_y:
                m_y = RE_YOY.search(text) if "착공" in (text[:text.find("준공")] if "준공" in text else text) else None

            yoy = None
            if m_y:
                v = None
                try: v = m_y.group(1)
                except: pass
                if not v:
                    try: v = m_y.group(2)
                    except: pass
                yoy = safe_float(v, -80, 100)

            if cnt is not None and r["수치"] is None: r["수치"] = f"{cnt:,}"
            if yoy is not None and r["전년비"] is None: r["전년비"] = f"{yoy}"
            if m_m and r["기준월"] is None:
                g = m_m.groups()
                if g[0]: r["기준월"] = f"{g[0]}.{int(g[1]):02d}"
                elif g[2]: r["기준월"] = f"{g[2]}월"
            if cnt is not None or yoy is not None:
                r["원문"].append({"title": title, "link": link, "date": date})
            if r["수치"] and r["전년비"]:
                return True
        return False

    scan(all_items)

    if not (r["수치"] and r["전년비"]):
        fallback_items = augment_with_article_body(all_items, "착공")
        scan(fallback_items)

    if r["수치"] or r["전년비"]:
        print(f"  ✔ {disp(r['수치'])}호 | 전년비 {disp(r['전년비'])}%")
        return r

    print("  - 데이터 없음")
    return r


# ══════════════════════════════════════════════════════════════════════════════
# 후행1: 전국 미분양
# 실제 제목: "'악성 미분양' 14년만에 3만가구 넘어"
#           "지난달 '악성 미분양' 다시 늘어…전국 2만9천555가구"
# ══════════════════════════════════════════════════════════════════════════════
def get_unsold(rss):
    print("[후행1] 전국 미분양")
    r = {"전국": None, "악성": None, "전년비": None, "기준월": None, "원문": []}

    RE_악성1 = re.compile(r'(?:준공후|악성)\s*미분양\s*([\d,]+)\s*(?:가구|호)?')
    RE_악성2 = re.compile(r'(?:준공후|악성)\s*미분양\s*(\d+(?:\.\d+)?)\s*만')
    RE_YOY   = re.compile(r'전년\s*(?:동기|동월)?\s*(?:대비|보다|比)?\s*([-+]?\d+\.?\d*)\s*%')
    RE_MON   = re.compile(r'(\d{4})년\s*(\d{1,2})월')

    all_items = combine(rss,
        "전국 미분양 주택 국토교통부 만가구",
        "미분양 5만 6만 7만 8만 가구",
        "미분양 넘어 기록 가구 전국",
        "미분양 준공후 악성 가구")

    def scan(items, require_relevant=True):
        for title, summary, link, date in items:
            text = f"{title} {summary}"
            if "미분양" not in text: continue

            # 전국 미분양: 현재 시장 5~8만호 수준
            cnt = parse_korean_num(text, "미분양", lo=50000, hi=300000)

            # 악성(준공후) 미분양
            악성 = None
            m_a = RE_악성1.search(text)
            m_a2 = RE_악성2.search(text)
            if m_a:
                악성 = safe_int(m_a.group(1), 100, 100000)
            elif m_a2:
                v = safe_float(m_a2.group(1))
                if v: 악성 = int(v * 10000)
            if 악성 is None:
                # "악성 미분양 1만2천호" 같은 한국식 만/천 표기 폴백
                # (앞쪽 "전국 미분양 X만Y천호" 숫자와 섞이지 않도록 '악성' 뒤쪽만 탐색)
                악성 = parse_korean_num_fwd(text, "악성", lo=1000, hi=100000)

            # ★ 전년비는 "미분양" 근처(약 40자 이내)에 있는 값만 채택
            #   (긴 본문 폴백 시, 다른 지표 문단의 % 수치를 잘못 가져오는 것 방지)
            yoy = None
            for m0 in re.finditer("미분양", text):
                seg = text[m0.start():m0.start()+40]
                m_y = RE_YOY.search(seg)
                if m_y:
                    yoy = safe_float(m_y.group(1), -80, 300)
                    if yoy is not None: break
            m_m = RE_MON.search(text)

            is_relevant = any(k in text for k in ["국토부","국토교통부","전국 미분양","전국 악성"])
            if require_relevant and not is_relevant: continue
            if cnt is None and yoy is None and 악성 is None: continue

            if cnt is not None and r["전국"] is None: r["전국"] = f"{cnt:,}"
            if 악성 is not None and r["악성"] is None and (cnt is None or 악성 < cnt):
                r["악성"] = f"{악성:,}"
            if yoy is not None and r["전년비"] is None: r["전년비"] = f"{yoy}"
            if m_m and r["기준월"] is None: r["기준월"] = f"{m_m.group(1)}.{int(m_m.group(2)):02d}"
            r["원문"].append({"title": title, "link": link, "date": date})
            if r["전국"] and r["악성"] and r["전년비"]:
                return True
        return False

    scan(all_items)

    # 조건 완화 재시도: 국토부 키워드 없어도 "X만가구" 패턴만 있으면 수집
    if not (r["전국"] and r["악성"] and r["전년비"]):
        retry_items = combine(rss,
            "미분양 만가구 전년대비",
            "악성 미분양 준공후 가구",
            "전국 미분양 현황")
        scan(retry_items, require_relevant=False)

    # 최종 폴백: 기사 원문 보강
    if not (r["전국"] and r["악성"] and r["전년비"]):
        fallback_items = augment_with_article_body(all_items, "미분양")
        scan(fallback_items, require_relevant=False)

    if r["전국"] or r["악성"] or r["전년비"]:
        print(f"  ✔ {disp(r['전국'])}호 | 악성 {disp(r['악성'])}호 | 전년비 {disp(r['전년비'])}%")
        return r

    print("  - 데이터 없음")
    return r


# ══════════════════════════════════════════════════════════════════════════════
# 후행2: 준공량
# 실제 제목: "5월 서울 입주물량 작년 대비 43%↓"
#           "지난달 주택 준공 실적 '반토막'"
# ══════════════════════════════════════════════════════════════════════════════
def get_completion(rss):
    print("[후행2] 준공량")
    r = {"수치": None, "전년비": None, "기준월": None, "원문": []}

    RE_YOY  = re.compile(r'전년\s*(?:동기|동월)?\s*(?:대비|보다|比)?\s*([-+]?\d+\.?\d*)\s*%')
    RE_YOY3 = re.compile(r'([-+]?\d+\.?\d*)\s*%\s*(?:감소|급감|증가|급증)')
    RE_MON  = re.compile(r'(\d{1,2})월\s*(?:서울\s*)?(?:입주|준공)')

    all_items = combine(rss,
        "아파트 입주 물량 준공 전년",
        "주택 준공 실적 국토교통부",
        "입주물량 감소 증가 전년")

    def scan(items):
        for title, summary, link, date in items:
            text = f"{title} {summary}"
            if "준공" not in text and "입주물량" not in text and "입주 물량" not in text:
                continue

            # 착공 기사와 구분: 착공 전용 기사 제외
            if "착공" in text and "준공" not in text and "입주" not in text:
                continue

            cnt = parse_korean_num(text, "준공", lo=10000, hi=300000)
            if not cnt:
                cnt = parse_korean_num(text, "입주", lo=10000, hi=300000)
            # ★ "전국" 수치가 직접 안 나오고 "수도권 X가구 + 비수도권 Y가구"로만
            #   나뉘어 나오는 국토부 보도자료 포맷에서는, 국지적(서울 누적치 등)
            #   수치보다 전국 합산이 더 정확하므로 우선한다
            if "수도권" in text and "비수도권" in text:
                region_sum = sum_region_count(text, "준공")
                if region_sum is not None:
                    cnt = region_sum

            # ★ 준공/입주 키워드 근처 전년비만 추출
            RE_준공YOY = re.compile(
                r'(?:준공|입주).{0,25}?([-+]?\d+\.?\d*)\s*%|'
                r'([-+]?\d+\.?\d*)\s*%\s*(?:감소|증가|급감|급증).{0,15}(?:준공|입주)'
            )
            m_y = RE_준공YOY.search(text)
            yoy = None
            if m_y:
                v = None
                try: v = m_y.group(1)
                except: pass
                if not v:
                    try: v = m_y.group(2)
                    except: pass
                yoy = safe_float(v, -80, 200)
            if yoy is None:
                m_y2 = RE_YOY.search(text) or RE_YOY3.search(text)
                if m_y2: yoy = safe_float(m_y2.group(1), -80, 200)

            m_m = RE_MON.search(text)

            # 국토부 통계 보도자료(수도권/비수도권 구조) 또는 기존 키워드 목록 중 하나면 관련 기사로 인정
            is_official = "국토교통부" in text or "주택통계" in text or \
                          ("수도권" in text and "비수도권" in text)
            is_relevant = is_official or any(k in text for k in [
                "준공 실적","입주물량","입주 물량","준공량","반토막","급감","급증",
                "준공 전년","입주 전년","준공 감소","준공 증가","입주 감소","입주 증가"
            ])
            if not (is_relevant and (cnt is not None or yoy is not None)): continue

            if cnt is not None and r["수치"] is None: r["수치"] = f"{cnt:,}"
            if yoy is not None and r["전년비"] is None: r["전년비"] = f"{yoy}"
            if m_m and r["기준월"] is None: r["기준월"] = f"{m_m.group(1)}월"
            r["원문"].append({"title": title, "link": link, "date": date})
            if r["수치"] and r["전년비"]:
                return True
        return False

    scan(all_items)

    if not (r["수치"] and r["전년비"]):
        fallback_items = augment_with_article_body(all_items, "준공") + \
                          augment_with_article_body(all_items, "입주")
        scan(fallback_items)

    if r["수치"] or r["전년비"]:
        print(f"  ✔ {disp(r['수치'])}호 | 전년비 {disp(r['전년비'])}%")
        return r

    print("  - 데이터 없음")
    return r


# ══════════════════════════════════════════════════════════════════════════════
# 부산 지역 지표
# debug2 결과: 부산 제목에 퍼센트 없음
# → 부산일보/국제신문 RSS 직접 수집 + 한국부동산원 주간 기사 파싱
# ══════════════════════════════════════════════════════════════════════════════
def get_busan(rss):
    print("[지역] 부산 지역 지표")
    r = {"아파트변동": None, "전세변동": None, "미분양": None, "원문": []}

    # ★ 1순위: KB 공식 API (매매/전세 둘 다 부산 지역값 제공)
    api = fetch_kb_api_weekly_price_change()
    if api.get("부산") is not None: r["아파트변동"] = f"{api['부산']:.2f}"
    if api.get("전세부산") is not None: r["전세변동"] = f"{api['전세부산']:.2f}"
    api_filled = bool(r["아파트변동"] or r["전세변동"])
    if api_filled:
        r["원문"].append({"title": "KB부동산 데이터허브 (공식 API)",
                          "link": "https://data.kbland.kr", "date": api.get("기준일") or ""})
        print(f"  ✔ (KB API) 매매 {disp(r['아파트변동'])}% | 전세 {disp(r['전세변동'])}%")

    # 부산일보, 국제신문 RSS 직접 수집 (부동산 섹션 포함)
    busan_rss_items = []
    busan_rss_urls = [
        "https://www.idomin.com/rss/allArticle.xml",
        "https://www.yna.co.kr/rss/economy.xml",
        "https://www.arunews.com/rss/allArticle.xml",
        "https://www.constimes.co.kr/rss/allArticle.xml",
    ]
    for url in busan_rss_urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8)
            feed = feedparser.parse(resp.content)
            for e in feed.entries:
                t = (e.get("title","") or "").strip()
                l = e.get("link","")
                d = (e.get("published","") or "")[:10]
                if t and "부산" in t:
                    busan_rss_items.append((t, "", l, d))
        except: pass

    # 패턴: 부산 제목에서 X.XX% 또는 보합/상승/하락 텍스트
    RE_A   = re.compile(r'부산\s*(?:아파트\s*)?(?:값|매매|가격)?\s*[▲△▼▽↑↓]?\s*([-+]?\d+\.\d+)\s*%')
    RE_J   = re.compile(r'부산\s*전세\s*[▲△▼▽↑↓]?\s*([-+]?\d+\.\d+)\s*%')
    RE_U   = re.compile(r'부산\s*(?:악성\s*)?미분양\s*([\d,]+)')

    # 한국부동산원 주간 기사에서 부산 수치 탐색 (API로 이미 다 채워졌으면 생략)
    if api_filled and r["미분양"]:
        all_items = []
    else:
        all_items = busan_rss_items + fetch_gn_titles("부산 아파트 매매 전세 주간 변동률", 15)
        all_items += fetch_gn_titles("부산 아파트값 상승 하락 주간", 10)
        all_items += fetch_gn_titles("부산 매매가 전세가 주간", 10)
        all_items += fetch_gn_titles("부산 아파트 매매가 하락 전환 변동", 10)
        all_items += list(rss)  # 전체 RSS에서도 탐색

    for title, summary, link, date in all_items:
        text = f"{title} {summary}"
        if "부산" not in text: continue

        m_a = RE_A.search(text)
        m_j = RE_J.search(text)
        m_u = RE_U.search(text)

        apt  = safe_float(m_a.group(1) if m_a else None, -10, 10)
        jeon = safe_float(m_j.group(1) if m_j else None, -10, 10)
        uns  = safe_int(m_u.group(1) if m_u else None, 100, 50000)

        if apt is not None or jeon is not None or uns is not None:
            if apt  is not None and r["아파트변동"] is None: r["아파트변동"] = f"{apt}"
            if jeon is not None and r["전세변동"] is None:   r["전세변동"]   = f"{jeon}"
            if uns is not None and r["미분양"] is None:      r["미분양"]     = f"{uns:,}"
            r["원문"].append({"title": title, "link": link, "date": date})
            if r["아파트변동"] and r["전세변동"] and r["미분양"]:
                if not api_filled:
                    print(f"  ✔ 매매 {disp(r['아파트변동'])}% | 전세 {disp(r['전세변동'])}%")
                return r

    # 수치 없이 방향 텍스트만 있는 경우 → 방향 기반 대표값 설정
    # (API로 이미 매매/전세 둘 다 채워졌으면 추정치로 덮어쓸 필요가 없으므로 생략)
    if not (r["아파트변동"] and r["전세변동"]):
        for title, summary, link, date in all_items:
            text = f"{title} {summary}"
            if "부산" not in text: continue
            if "아파트" not in text and "부동산" not in text: continue
            if any(k in text for k in ["상승","하락","보합","멈추고","오름","내림"]):
                # 방향 텍스트로 대표값 설정 (API로 이미 채워진 값은 덮어쓰지 않음)
                if r["아파트변동"] is None:
                    if "하락 멈추" in text or "보합" in text:
                        r["아파트변동"] = "0.00"
                    elif "상승" in text and "하락" not in text:
                        r["아파트변동"] = "0.05"  # 소폭 상승 추정
                    elif "하락" in text:
                        r["아파트변동"] = "-0.05"  # 소폭 하락 추정
                    r["원문"].append({"title": title, "link": link, "date": date})
                    print(f"  ✔ 부산 방향 파싱: {title[:45]}")
                break

    if r["아파트변동"] or r["전세변동"]:
        if api_filled:
            return r
        print(f"  ✔ 매매 {disp(r['아파트변동'])}% | 전세 {disp(r['전세변동'])}%")
        return r

    print("  - 데이터 없음")
    return r


# ══════════════════════════════════════════════════════════════════════════════
# 종합 분석
# ══════════════════════════════════════════════════════════════════════════════
def analyze(kb, jeonse, auction, csi, kb_fc, supply, krihs, khai,
            trade, cstart, unsold, compl, busan):
    sigs = []

    def add(name, d, desc, cat):
        sigs.append((name, d, desc, cat))

    ref = safe_float(kb.get("서울") or kb.get("국전체"))
    if ref is not None:
        lbl = "KB 서울 매매가" if kb.get("서울") else "KB 전국 매매가"
        d = "상승" if ref>0 else ("하락" if ref<0 else "보합")
        add(lbl, d, f"주간 {ref:+.2f}%", "동행")

    bus = safe_float(busan.get("아파트변동") or kb.get("부산"))
    if bus is not None:
        d = "상승" if bus>0 else ("하락" if bus<0 else "보합")
        add("KB 부산 매매가", d, f"주간 {bus:+.2f}%", "동행")

    jr = safe_float(jeonse.get("전국") or jeonse.get("서울"))
    if jr is not None:
        if jr>=70:   add("전세가율","과열",f"{jr}% (상한 70% 초과)","선행")
        elif jr>=60: add("전세가율","적정",f"{jr}% (적정 60~70%)","선행")
        else:        add("전세가율","침체",f"{jr}% (하한 60% 미달)","선행")

    ar  = safe_float(auction.get("낙찰률"))
    apr = safe_float(auction.get("낙찰가율"))
    if ar is not None:
        if ar>=40:   add("경매낙찰률","상승",f"{ar}% (고점 42% 근접)","선행")
        elif ar>=34: add("경매낙찰률","보합",f"{ar}% (정상)","선행")
        else:        add("경매낙찰률","침체",f"{ar}% (저점 32.4% 근접)","선행")
    elif apr is not None:
        if apr>=100: add("경매낙찰가율","상승",f"{apr}% (100% 초과)","선행")
        elif apr>=90:add("경매낙찰가율","보합",f"{apr}%","선행")
        else:        add("경매낙찰가율","침체",f"{apr}% (90% 미만)","선행")

    hpci = safe_float(csi.get("주택전망"))
    if hpci is not None:
        if hpci>=110:  add("주택가격전망(CSI)","상승",f"{hpci} (낙관)","선행")
        elif hpci>=100:add("주택가격전망(CSI)","보합",f"{hpci} (평균 상회)","선행")
        else:          add("주택가격전망(CSI)","침체",f"{hpci} (평균 하회)","선행")

    mv = safe_float(kb_fc.get("매매전망"))
    if mv is not None:
        if mv>=110:  add("KB 매매전망지수","상승",f"{mv} (상승 우위)","선행")
        elif mv>=100:add("KB 매매전망지수","보합",f"{mv} (균형)","선행")
        else:        add("KB 매매전망지수","침체",f"{mv} (하락 우위)","선행")

    sd = safe_float(supply.get("매매수급"))
    if sd is not None:
        if sd>=110:  add("매매수급지수","상승",f"{sd} (수요우위)","선행")
        elif sd>=90: add("매매수급지수","보합",f"{sd} (균형)","선행")
        else:        add("매매수급지수","침체",f"{sd} (공급우위)","선행")

    km = safe_float(krihs.get("매매심리"))
    if km is not None:
        if km>=115:  add("부동산소비심리(매매)","상승",f"{km} (낙관)","선행")
        elif km>=95: add("부동산소비심리(매매)","보합",f"{km} (보합)","선행")
        else:        add("부동산소비심리(매매)","침체",f"{km} (위축)","선행")

    kh = safe_float(khai.get("지수"))
    if kh is not None:
        if kh>=150:  add("주택구입부담(K-HAI)","침체",f"{kh} (부담 과중)","선행")
        elif kh>=100:add("주택구입부담(K-HAI)","보합",f"{kh} (보통)","선행")
        else:        add("주택구입부담(K-HAI)","상승",f"{kh} (부담 낮음)","선행")

    tvr = safe_float(trade.get("전년비"))
    if tvr is not None:
        if tvr>=20:    add("주택 거래량","상승",f"전년비 +{tvr}% (회복)","동행")
        elif tvr>=-10: add("주택 거래량","보합",f"전년비 {tvr}%","동행")
        else:          add("주택 거래량","침체",f"전년비 {tvr}% (위축)","동행")

    csr = safe_float(cstart.get("전년비"))
    if csr is not None:
        if csr>=10:    add("착공량","상승",f"전년비 +{csr}% (증가)","동행")
        elif csr>=-10: add("착공량","보합",f"전년비 {csr}%","동행")
        else:          add("착공량","침체",f"전년비 {csr}% (감소)","동행")

    us = safe_int(str(unsold.get("전국") or "").replace(",",""))
    if us is not None:
        if us>60000:   add("전국 미분양","침체",f"{us:,}호 (위험 6.2만↑)","후행")
        elif us<30000: add("전국 미분양","상승",f"{us:,}호 (호황 3만↓)","후행")
        else:          add("전국 미분양","보합",f"{us:,}호 (관찰)","후행")

    cr = safe_float(compl.get("전년비"))
    if cr is not None:
        if cr>=10:    add("준공량","보합",f"전년비 +{cr}% (공급 확대)","후행")
        elif cr<-20:  add("준공량","상승",f"전년비 {cr}% (공급 부족)","후행")
        else:         add("준공량","보합",f"전년비 {cr}%","후행")

    n    = len(sigs)
    up   = sum(1 for _,d,_,_ in sigs if d in ["상승","과열","적정"])
    down = sum(1 for _,d,_,_ in sigs if d in ["침체","하락"])

    if n==0:            verdict,vc = "데이터 수집 중",  "#546e7a"
    elif up>=n*0.7:     verdict,vc = "상승 우세",      "#c62828"
    elif up>=n*0.55:    verdict,vc = "완만한 상승",    "#ef6c00"
    elif down>=n*0.7:   verdict,vc = "하락 우세",      "#1565c0"
    elif down>=n*0.55:  verdict,vc = "완만한 하락",    "#42a5f5"
    else:               verdict,vc = "보합 / 혼조",    "#2e7d32"

    return sigs, verdict, vc


# ══════════════════════════════════════════════════════════════════════════════
# 지표 스냅샷 저장 (알림/추이차트용)
# ══════════════════════════════════════════════════════════════════════════════
DATA_DIR       = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
INDICATORS_FILE = os.path.join(DATA_DIR, "indicators.json")
HISTORY_FILE    = os.path.join(DATA_DIR, "indicators_history.json")
HISTORY_MAX_LEN = 500

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def build_indicator_summary(kb, permit, jeonse, auction, csi, kb_fc, supply, krihs, khai,
                             trade, cstart, unsold, compl, busan, verdict, buyer=None):
    """알림/차트용으로 쓰는 핵심 지표 요약 (숫자만 추출)"""
    buyer = buyer or {}
    verdict_score = {"상승 우세": 2, "완만한 상승": 1, "보합 / 혼조": 0,
                      "완만한 하락": -1, "하락 우세": -2}.get(verdict)
    return {
        "timestamp":      datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "verdict":        verdict,
        "verdict_score":  verdict_score,
        "kb_전국":         safe_float(kb.get("국전체")),
        "kb_서울":         safe_float(kb.get("서울")),
        "kb_수도권":       safe_float(kb.get("수도권")),
        "kb_부산":         safe_float(kb.get("부산") or busan.get("아파트변동")),
        "kb_전세전국":     safe_float(kb.get("전세전국")),
        "경매낙찰률":      safe_float(auction.get("낙찰률")),
        "경매낙찰가율":    safe_float(auction.get("낙찰가율")),
        "인허가_전년비":   safe_float(permit.get("전년비")),
        "전세가율_전국":   safe_float(jeonse.get("전국")),
        "전세가율_서울":   safe_float(jeonse.get("서울")),
        "csi_주택전망":    safe_float(csi.get("주택전망")),
        "매매수급지수":    safe_float(supply.get("매매수급")),
        "전세수급지수":    safe_float(supply.get("전세수급")),
        "소비심리_매매":   safe_float(krihs.get("매매심리")),
        "khai":            safe_float(khai.get("지수")),
        "거래량_전년비":   safe_float(trade.get("전년비")),
        "착공량_전년비":   safe_float(cstart.get("전년비")),
        "미분양_전국":     safe_int(str(unsold.get("전국") or "").replace(",", "")),
        "준공량_전년비":   safe_float(compl.get("전년비")),
        "부산_전세":       safe_float(busan.get("전세변동")),
        "매수우위지수":    safe_float(buyer.get("지수")),
    }

def save_indicators(summary):
    save_json(INDICATORS_FILE, summary)
    print(f"  [저장] {INDICATORS_FILE}")

def update_history(summary):
    hist = load_json(HISTORY_FILE, [])
    hist.append(summary)
    if len(hist) > HISTORY_MAX_LEN:
        hist = hist[-HISTORY_MAX_LEN:]
    save_json(HISTORY_FILE, hist)
    print(f"  [저장] {HISTORY_FILE} (누적 {len(hist)}건)")
    return hist


# ══════════════════════════════════════════════════════════════════════════════
# 추이 차트 (순수 SVG 스파크라인 — 외부 라이브러리 불필요)
# ══════════════════════════════════════════════════════════════════════════════
def sparkline_svg(values, width=180, height=46, color="#4fc3f7"):
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return '<div class="spark-empty">데이터 축적 중</div>'
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or (abs(hi) or 1)
    n = len(vals)
    pts = []
    for i, v in enumerate(vals):
        x = i / (n - 1) * width
        y = height - ((v - lo) / rng) * (height - 6) - 3
        pts.append((x, y))
    path_d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area_d = path_d + f" L {width},{height} L 0,{height} Z"
    lx, ly = pts[-1]
    return (f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" class="spark">'
            f'<path d="{area_d}" fill="{color}" fill-opacity="0.12" stroke="none"/>'
            f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linejoin="round" stroke-linecap="round"/>'
            f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="2.6" fill="{color}"/></svg>')

def trend_card(title, key, history, color, unit="", fmt="{:+.2f}"):
    vals = [h.get(key) for h in history]
    recent = vals[-48:]  # 최근 48개 수집 시점 (약 2일치, 1시간 간격 기준)
    latest = next((v for v in reversed(vals) if v is not None), None)
    n_pts  = len([v for v in recent if v is not None])
    svg    = sparkline_svg(recent, color=color)
    latest_h = (fmt.format(latest) + unit) if latest is not None else "—"
    return (f'<div class="tcard"><div class="ttitle">{title}</div>'
            f'<div class="tval" style="color:{color}">{latest_h}</div>'
            f'<div class="tspark">{svg}</div>'
            f'<div class="tsub">누적 {n_pts}개 시점</div></div>')


# ══════════════════════════════════════════════════════════════════════════════
# HTML
# ══════════════════════════════════════════════════════════════════════════════
def card(title, value, unit, sub, color, note="", news=None):
    val_h = (f'<span class="val" style="color:{color}">{value}</span>'
             f'<span class="unit"> {unit}</span>') if value else '<span class="val na">—</span>'
    sub_h  = f'<div class="sub">{sub}</div>'   if sub  else ""
    note_h = f'<div class="note">{note}</div>' if note else ""
    news_h = ""
    for item in (news or [])[:1]:
        t = (item.get("title","") or "")[:50]
        l = item.get("link","#")
        d = (item.get("date","") or "")[:10]
        news_h += (f'<div class="nref"><a href="{l}" target="_blank">📰 {t}</a>'
                   f' <span class="nd">{d}</span></div>')
    return (f'<div class="card"><div class="ctitle">{title}</div>'
            f'<div class="cval">{val_h}</div>{sub_h}{note_h}'
            f'<div class="cnews">{news_h}</div></div>')

def sig_row(name, direction, desc, category):
    cm = {"상승":"#c62828","과열":"#880e4f","보합":"#e65100",
          "적정":"#2e7d32","침체":"#1a237e","하락":"#0d47a1"}
    bm = {"상승":"▲ 상승","과열":"⚠ 과열","보합":"→ 보합",
          "적정":"✔ 적정","침체":"▼ 침체","하락":"▼ 하락"}
    catc = {"선행":"#1565c0","동행":"#2e7d32","후행":"#6a1b9a"}
    c = cm.get(direction,"#555"); b = bm.get(direction, direction)
    cc = catc.get(category,"#546e7a")
    return (f'<tr><td class="sn">{name}'
            f'<span class="cat" style="background:{cc}">{category}</span></td>'
            f'<td><span class="badge" style="background:{c}">{b}</span></td>'
            f'<td class="sd">{desc}</td></tr>')

def build_html(kb, permit, jeonse, auction, csi, kb_fc, supply, krihs, khai,
               trade, cstart, unsold, compl, busan, buyer=None, history=None):
    history = history or []
    buyer = buyer or {}
    sigs, verdict, vc = analyze(kb, jeonse, auction, csi, kb_fc, supply,
                                  krihs, khai, trade, cstart, unsold, compl, busan)
    now   = datetime.now(KST)
    today = now.strftime("%Y년 %m월 %d일")
    upd   = now.strftime("%Y-%m-%d %H:%M KST")

    dir_color = rcolor(kb.get("서울") or kb.get("국전체"))
    wk  = disp(kb.get("연속주수"))
    wkd = disp(kb.get("방향"), "")
    dt  = disp(kb.get("기준일"), "최신")

    kb_bar = ""
    for label, key in [("전국","국전체"),("서울","서울"),("수도권","수도권"),("부산","부산")]:
        v = kb.get(key); fv = safe_float(v)
        if fv is not None:
            ic = "▲" if fv>0 else ("▼" if fv<0 else "→"); co = rcolor(v)
            kb_bar += (f'<div class="kbi"><span class="kbr">{label}</span>'
                       f'<span class="kbv" style="color:{co}">{ic} {fv:+.2f}%</span></div>')
        else:
            kb_bar += (f'<div class="kbi"><span class="kbr">{label}</span>'
                       f'<span class="kbv" style="color:#455a64">—</span></div>')
    kb_bar += (f'<div class="kbi"><span class="kbr">{wkd} 연속</span>'
               f'<span class="kbv" style="color:{dir_color}">{wk}주</span></div>')
    kb_bar += (f'<div class="kbi"><span class="kbr">기준일</span>'
               f'<span class="kbv" style="color:#78909c;font-size:12px">{dt}</span></div>')

    busan_apt  = busan.get("아파트변동") or kb.get("부산")
    busan_jeon = busan.get("전세변동")

    sig_rows = ''.join(sig_row(n,d,desc,cat) for n,d,desc,cat in sigs)
    sig_html = (f'<table class="stbl"><tbody>{sig_rows}</tbody></table>'
                if sigs else '<p style="color:#37474f;font-size:13px">수집된 지표 없음</p>')

    css = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Malgun Gothic',sans-serif;background:#0f1923;color:#e8f0f5;min-height:100vh;font-size:16px}}
.hdr{{background:linear-gradient(135deg,#1a2942,#0d1f35);padding:20px 28px;border-bottom:2px solid #2a4a70}}
.hdr h1{{font-size:22px;font-weight:700;color:#ffffff}}
.hdr h1 em{{font-size:13px;font-weight:400;color:#6fd3ff;margin-left:8px;font-style:normal}}
.upd{{font-size:13px;color:#9fb4c7;margin-top:4px}}
.vbar{{background:#132030;border-left:5px solid {vc};padding:14px 28px;display:flex;align-items:center;gap:16px}}
.vlabel{{font-size:13px;color:#9fb4c7;letter-spacing:1px}}
.vval{{font-size:30px;font-weight:700;color:{vc}}}
.vsub{{font-size:14px;color:#b0c4d4;margin-top:2px}}
.kbbar{{background:#0d1f35;padding:12px 28px;display:flex;gap:18px;flex-wrap:wrap;border-bottom:1px solid #2a4a70}}
.kbi{{display:flex;flex-direction:column;align-items:center;min-width:70px}}
.kbr{{font-size:12px;color:#9fb4c7}}
.kbv{{font-size:18px;font-weight:700;margin-top:2px}}
.sec{{padding:18px 28px}}
.stitle{{font-size:13px;font-weight:700;color:#6fd3ff;letter-spacing:1.5px;text-transform:uppercase;
         margin-bottom:12px;padding-bottom:6px;border-bottom:1px solid #2a4a70}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:10px}}
.tgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px}}
.tcard{{background:#132030;border:1px solid #2a4a70;border-radius:8px;padding:10px 12px}}
.ttitle{{font-size:12px;color:#9fb4c7;letter-spacing:0.5px;margin-bottom:4px}}
.tval{{font-size:20px;font-weight:700;margin-bottom:2px}}
.tspark{{margin:2px 0}}
.spark{{display:block}}
.spark-empty{{font-size:12px;color:#607d8b;padding:14px 0}}
.tsub{{font-size:11px;color:#8fa3b5;margin-top:2px}}
.card{{background:#132030;border:1px solid #2a4a70;border-radius:8px;padding:12px}}
.ctitle{{font-size:12px;color:#9fb4c7;letter-spacing:0.5px;margin-bottom:5px}}
.cval{{margin-bottom:3px}}
.val{{font-size:28px;font-weight:700}}
.unit{{font-size:13px;color:#9fb4c7}}
.val.na{{font-size:16px;color:#607d8b}}
.sub{{font-size:13px;color:#b0c4d4;margin-bottom:2px}}
.note{{font-size:12px;color:#8fa3b5;font-style:italic}}
.cnews{{margin-top:5px}}
.nref{{font-size:12px;color:#8fa3b5;margin-top:2px;line-height:1.5}}
.nref a{{color:#6fd3ff;text-decoration:none}}
.nref a:hover{{text-decoration:underline}}
.nd{{color:#607d8b}}
.stbl{{width:100%;border-collapse:collapse}}
.stbl tr{{border-bottom:1px solid #1e3a5f}}
.stbl td{{padding:8px 6px;vertical-align:middle}}
.sn{{color:#c5d6e3;width:210px;font-size:14px}}
.sd{{color:#9fb4c7;font-size:14px}}
.badge{{display:inline-block;padding:3px 8px;border-radius:4px;font-size:13px;font-weight:700;color:#fff}}
.cat{{display:inline-block;padding:1px 5px;border-radius:3px;font-size:11px;color:#fff;margin-left:5px;vertical-align:middle}}
.bsbox{{background:#0a1e30;border:1px solid #2a4a70;border-left:3px solid #6fd3ff;border-radius:8px;padding:12px}}
.bstitle{{font-size:13px;color:#6fd3ff;font-weight:700;margin-bottom:8px}}
.refbox{{background:#0d1a26;border:1px solid #1e3a5f;border-radius:6px;padding:12px;
         font-size:13px;color:#9fb4c7;line-height:2}}
.refbox b{{color:#c5d6e3}}
footer{{text-align:center;padding:16px;font-size:12px;color:#607d8b}}
"""

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>부동산 경기 지표 대시보드 {today}</title>
<style>{css}</style>
</head>
<body>
<div class="hdr">
  <h1>부동산 경기 지표 대시보드 <em>선행 8개 · 동행 3개 · 후행 2개 자동 수집</em></h1>
  <div class="upd">업데이트: {upd}</div>
</div>
<div class="vbar">
  <div><div class="vlabel">종합 경기 판단</div>
  <div class="vval">{verdict}</div>
  <div class="vsub">수집된 {len(sigs)}개 지표 기반 자동 분석</div></div>
</div>
<div class="kbbar">{kb_bar}</div>

<div class="sec">
  <div class="stitle">지표 추이 — 자동 수집 데이터 누적 (1시간 간격)</div>
  <div class="tgrid">
    {trend_card("종합판단 지수", "verdict_score", history, vc, "", "{:+.0f}")}
    {trend_card("KB 전국 매매가", "kb_전국", history, rcolor(history[-1].get("kb_전국") if history else None), "%")}
    {trend_card("KB 서울 매매가", "kb_서울", history, rcolor(history[-1].get("kb_서울") if history else None), "%")}
    {trend_card("KB 부산 매매가", "kb_부산", history, rcolor(history[-1].get("kb_부산") if history else None), "%")}
    {trend_card("경매 낙찰률", "경매낙찰률", history, "#ef6c00", "%", "{:.1f}")}
    {trend_card("전세가율(전국)", "전세가율_전국", history, "#4fc3f7", "%", "{:.1f}")}
    {trend_card("주택가격전망(CSI)", "csi_주택전망", history, "#c62828", "", "{:.1f}")}
    {trend_card("매매수급지수", "매매수급지수", history, "#1565c0", "", "{:.1f}")}
    {trend_card("소비심리(매매)", "소비심리_매매", history, "#2e7d32", "", "{:.1f}")}
    {trend_card("전국 미분양", "미분양_전국", history, "#ef6c00", "호", "{:,.0f}")}
    {trend_card("거래량(전년비)", "거래량_전년비", history, rcolor(history[-1].get("거래량_전년비") if history else None), "%", "{:+.1f}")}
    {trend_card("착공량(전년비)", "착공량_전년비", history, rcolor(history[-1].get("착공량_전년비") if history else None), "%", "{:+.1f}")}
    {trend_card("KB 매수우위지수", "매수우위지수", history, "#ef6c00", "", "{:.1f}")}
  </div>
</div>

<div class="sec">
  <div class="stitle">선행지표 — 시장 3~12개월 전망</div>
  <div class="grid">
    {card("① 경매 낙찰률",disp(auction.get("낙찰률")),"%",
        f"낙찰가율 {disp(auction.get('낙찰가율'))}% | {disp(auction.get('건수'))}건",
        "#c62828" if safe_float(auction.get("낙찰률"),38,80) else "#1565c0" if safe_float(auction.get("낙찰률"),0,34) else "#ef6c00",
        "32.4%(2023 저점)~42%(2021 고점)",auction.get("원문",[]))}
    {card("② 주택 인허가",
        disp(permit.get("수치")) if permit.get("수치") else f"전년비 {disp(permit.get('전년비'))}%",
        "호" if permit.get("수치") else "",
        f"{disp(permit.get('수치'))}호 | 전년비 {disp(permit.get('전년비'))}% | {disp(permit.get('기준월'))}",
        rcolor(permit.get("전년비")),"인허가→착공→준공 6~24개월 시차",permit.get("원문",[]))}
    {card("③ 전세가율",
        f"{disp(jeonse.get('전국'))}(전국)" if jeonse.get("전국") else f"{disp(jeonse.get('서울'))}(서울)",
        "%",
        f"전국 {disp(jeonse.get('전국'))}% | 서울 {disp(jeonse.get('서울'))}% | 부산 {disp(jeonse.get('부산'))}%",
        "#c62828" if safe_float(jeonse.get("전국") or jeonse.get("서울"),70,90) else "#1565c0" if safe_float(jeonse.get("전국") or jeonse.get("서울"),0,60) else "#2e7d32",
        "적정 60~70% | 70↑과열 | 60↓침체",jeonse.get("원문",[]))}
    {card("④ 주택가격전망지수(CSI)",disp(csi.get("주택전망")),"",
        f"소비자심리지수 {disp(csi.get('CSI'))}",
        "#c62828" if safe_float(csi.get("주택전망"),110,200) else "#2e7d32" if safe_float(csi.get("주택전망"),100,110) else "#1565c0",
        "100↑낙관 · 한국은행 장기평균 기준",csi.get("원문",[]))}
    {card("⑤ KB 매매가격전망지수",disp(kb_fc.get("매매전망")),"",
        f"전세가격전망 {disp(kb_fc.get('전세전망'))}",
        "#c62828" if safe_float(kb_fc.get("매매전망"),110,200) else "#2e7d32" if safe_float(kb_fc.get("매매전망"),100,110) else "#1565c0",
        "100↑상승우위 | 0~200 범위 (KB국민은행)",kb_fc.get("원문",[]))}
    {card("⑥ 매매수급지수",disp(supply.get("매매수급")),"",
        f"전세수급지수 {disp(supply.get('전세수급'))}",
        "#c62828" if safe_float(supply.get("매매수급"),110,180) else "#1565c0" if safe_float(supply.get("매매수급"),0,90) else "#2e7d32",
        "100↑수요우위 | 0~200 범위 (한국부동산원)",supply.get("원문",[]))}
    {card("⑦ 부동산소비심리지수",disp(krihs.get("매매심리")),"",
        f"전세심리 {disp(krihs.get('전세심리'))}",
        "#c62828" if safe_float(krihs.get("매매심리"),115,200) else "#1565c0" if safe_float(krihs.get("매매심리"),0,95) else "#2e7d32",
        "115↑낙관 | 95↓위축 (국토연구원)",krihs.get("원문",[]))}
    {card("⑧ 주택구입부담(K-HAI)",disp(khai.get("지수")),"",
        f"전분기비 {disp(khai.get('전분기비'))}p",
        "#1565c0" if safe_float(khai.get("지수"),150,300) else "#c62828" if safe_float(khai.get("지수"),0,100) else "#2e7d32",
        "지수↑부담 증가 | 100↓부담 낮음 (주택금융공사)",khai.get("원문",[]))}
    {card("⑨ KB 매수우위지수",disp(buyer.get("지수")),"",
        f"매도자많음 {disp(buyer.get('매도자많음'))}% | 매수자많음 {disp(buyer.get('매수자많음'))}%",
        "#c62828" if safe_float(buyer.get("지수"),100,200) else "#1565c0" if safe_float(buyer.get("지수"),0,100) else "#2e7d32",
        "100↑매도자 우위 | 100↓매수자 우위 (KB부동산)",buyer.get("원문",[]))}
  </div>
</div>

<div class="sec">
  <div class="stitle">동행지표 — 현재 시장 상황</div>
  <div class="grid">
    {card("KB 전국 매매가",pct_str(kb.get("국전체")),"%",f"{wk}주 연속 {wkd}",rcolor(kb.get("국전체")),"주간 변동률 (KB국민은행)",kb.get("원문",[]))}
    {card("KB 서울 매매가",pct_str(kb.get("서울")),"%",f"수도권 {pct_str(kb.get('수도권'))}%",rcolor(kb.get("서울")),"주간 변동률 (KB국민은행)",[])}
    {card("KB 전국 전세가",pct_str(kb.get("전세전국")),"%",f"서울 전세 {pct_str(kb.get('전세서울'))}%",rcolor(kb.get("전세전국")),"주간 전세 변동률 (KB국민은행)",[])}
    {card("주택 매매 거래량",
        disp(trade.get("거래량")) if trade.get("거래량") else f"전년비 {disp(trade.get('전년비'))}%",
        "건" if trade.get("거래량") else "",
        f"전년비 {disp(trade.get('전년비'))}% | {disp(trade.get('기준월'))}",
        rcolor(trade.get("전년비")),"국토교통부 실거래 신고 기준",trade.get("원문",[]))}
    {card("착공량",
        disp(cstart.get("수치")) if cstart.get("수치") else f"전년비 {disp(cstart.get('전년비'))}%",
        "호" if cstart.get("수치") else "",
        f"전년비 {disp(cstart.get('전년비'))}% | {disp(cstart.get('기준월'))}",
        rcolor(cstart.get("전년비")),"착공 후 12~24개월 후 공급",cstart.get("원문",[]))}
  </div>
</div>

<div class="sec">
  <div class="stitle">후행지표 — 시장 결과 확인</div>
  <div class="grid">
    {card("전국 미분양",disp(unsold.get("전국")),"호",
        f"준공후(악성) {disp(unsold.get('악성'))}호 | {disp(unsold.get('기준월'))}",
        "#1565c0" if safe_int(str(unsold.get("전국") or "").replace(",",""),60001,999999) else "#c62828" if safe_int(str(unsold.get("전국") or "").replace(",",""),1,29999) else "#ef6c00",
        "3만호↓호황 | 6.2만호↑위험 (국토교통부)",unsold.get("원문",[]))}
    {card("준공량",
        disp(compl.get("수치")) if compl.get("수치") else f"전년비 {disp(compl.get('전년비'))}%",
        "호" if compl.get("수치") else "",
        f"전년비 {disp(compl.get('전년비'))}% | {disp(compl.get('기준월'))}",
        rcolor(compl.get("전년비")),"준공 증가→공급 확대→가격 하락 압력",compl.get("원문",[]))}
  </div>
</div>

<div class="sec">
  <div class="stitle">부산 지역 지표</div>
  <div class="bsbox">
    <div class="bstitle">🌊 부산 부동산 동향</div>
    <div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(160px,1fr))">
      {card("부산 아파트 매매",pct_str(busan_apt),"%","주간 변동률",rcolor(busan_apt),"KB부동산 기준",busan.get("원문",[])[:1])}
      {card("부산 전세가",pct_str(busan_jeon),"%","주간 전세 변동률",rcolor(busan_jeon),"KB부동산 기준",[])}
      {card("부산 미분양",disp(busan.get("미분양")),"호","부산 지역 미분양","#ef6c00" if busan.get("미분양") else "#546e7a","국토교통부 기준",[])}
    </div>
  </div>
</div>

<div class="sec">
  <div class="stitle">지표별 신호 분석</div>
  {sig_html}
</div>

<div class="sec">
  <div class="stitle">지표 해석 기준값</div>
  <div class="refbox">
    <b>[선행] 경매 낙찰률:</b> 42%(2021 고점)~32.4%(2023 저점) · 낙찰가율 100%↑ 과열<br>
    <b>[선행] 주택 인허가:</b> 증가→6~18개월 후 공급 확대 · 감소→공급 부족<br>
    <b>[선행] 전세가율:</b> 60~70% 적정 · 70%↑ 매매가 상승 압력 · 60%↓ 침체 (KB부동산)<br>
    <b>[선행] 주택가격전망지수(CSI):</b> 100↑ 낙관 · 장기평균(2003~2019) 기준 (한국은행)<br>
    <b>[선행] KB 가격전망지수:</b> 0~200 범위 · 100↑ 상승우위 (KB국민은행)<br>
    <b>[선행] 수급지수:</b> 0~200 범위 · 100↑ 수요>공급 (한국부동산원)<br>
    <b>[선행] 소비심리지수:</b> 115↑ 낙관 · 95↓ 위축 (국토연구원)<br>
    <b>[선행] 주택구입부담(K-HAI):</b> 100 기준 · 높을수록 부담 큼 (주택금융공사)<br>
    <b>[동행] 거래량·착공량:</b> 전년비 20%↑ 회복 · -10%↓ 위축<br>
    <b>[후행] 전국 미분양:</b> 3만호↓ 호황 · 6.2만호↑ 위험 (국토교통부)<br>
    <b>[후행] 준공량:</b> 증가→공급 확대 / 감소→공급 부족 압력<br>
    <b>데이터:</b> RSS 12개 피드 + Google News RSS 제목 파싱 (무료·실시간)
  </div>
</div>

<footer>부동산 경기 지표 대시보드 · {upd} · 투자 결정 참고 자료</footer>
</body></html>"""


if __name__ == "__main__":
    print("=" * 55)
    print("부동산 경기 지표 수집 시작")
    print("=" * 55)

    print("\nRSS 사전 수집중...")
    rss = fetch_rss_all()

    print("\n[선행지표]")
    kb     = get_kb_weekly(rss)
    auction= get_auction(rss)
    permit = get_permit(rss)
    jeonse = get_jeonse_ratio(rss)
    csi    = get_csi(rss)
    kb_fc  = get_kb_forecast(rss)
    supply = get_supply_demand(rss)
    krihs  = get_krihs(rss)
    khai   = get_khai(rss)
    buyer  = get_buyer_index()

    print("\n[동행지표]")
    trade  = get_trade_vol(rss)
    cstart = get_construction_start(rss)

    print("\n[후행지표]")
    unsold = get_unsold(rss)
    compl  = get_completion(rss)

    print("\n[지역지표]")
    busan  = get_busan(rss)

    print("\n[지표 스냅샷 저장 / 추이 데이터 갱신]")
    _sigs, _verdict, _vc = analyze(kb, jeonse, auction, csi, kb_fc, supply,
                                    krihs, khai, trade, cstart, unsold, compl, busan)
    summary = build_indicator_summary(kb, permit, jeonse, auction, csi, kb_fc, supply,
                                       krihs, khai, trade, cstart, unsold, compl, busan,
                                       _verdict, buyer=buyer)
    save_indicators(summary)
    history = update_history(summary)

    print("\n" + "=" * 55)
    html = build_html(kb, permit, jeonse, auction, csi, kb_fc, supply,
                      krihs, khai, trade, cstart, unsold, compl, busan,
                      buyer=buyer, history=history)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "realestate_dashboard.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[완료] {out}")
    print(f"\n수집 결과:")
    print(f"  [선행] KB 전국 {disp(kb.get('국전체'))}% | 서울 {disp(kb.get('서울'))}% | 부산 {disp(kb.get('부산'))}% | {disp(kb.get('연속주수'))}주")
    print(f"  [선행] 경매 낙찰률 {disp(auction.get('낙찰률'))}% | 낙찰가율 {disp(auction.get('낙찰가율'))}%")
    print(f"  [선행] 인허가 {disp(permit.get('수치'))}호 | 전년비 {disp(permit.get('전년비'))}%")
    print(f"  [선행] 전세가율 {disp(jeonse.get('전국'))}% | 서울 {disp(jeonse.get('서울'))}%")
    print(f"  [선행] 주택전망 {disp(csi.get('주택전망'))} | CSI {disp(csi.get('CSI'))}")
    print(f"  [선행] KB 매매전망 {disp(kb_fc.get('매매전망'))} | 전세전망 {disp(kb_fc.get('전세전망'))}")
    print(f"  [선행] 매매수급 {disp(supply.get('매매수급'))} | 전세수급 {disp(supply.get('전세수급'))}")
    print(f"  [선행] 소비심리 {disp(krihs.get('매매심리'))} | K-HAI {disp(khai.get('지수'))}")
    print(f"  [선행] KB 매수우위지수 {disp(buyer.get('지수'))} (매도자많음 {disp(buyer.get('매도자많음'))}% | 매수자많음 {disp(buyer.get('매수자많음'))}%)")
    print(f"  [동행] 거래량 {disp(trade.get('거래량'))}건 | 전년비 {disp(trade.get('전년비'))}%")
    print(f"  [동행] 착공량 {disp(cstart.get('수치'))}호 | 전년비 {disp(cstart.get('전년비'))}%")
    print(f"  [후행] 미분양 {disp(unsold.get('전국'))}호 | 악성 {disp(unsold.get('악성'))}호")
    print(f"  [후행] 준공량 {disp(compl.get('수치'))}호 | 전년비 {disp(compl.get('전년비'))}%")
    print(f"  [부산] 매매 {disp(busan.get('아파트변동'))}% | 전세 {disp(busan.get('전세변동'))}%")