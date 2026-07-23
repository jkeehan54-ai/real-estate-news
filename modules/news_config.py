# news_config.py
import re

from datetime import timezone, timedelta

KST = timezone(timedelta(hours=9))

SOURCES = {
    "조선일보":    "https://www.chosun.com/economy/real_estate/",
    "중앙일보":    "https://www.joongang.co.kr/realestate",
    "동아일보":    "https://www.donga.com/news/Economy/Realestate",
    "한겨레":      "https://www.hani.co.kr/arti/economy/property/",
    "매일경제":    "https://www.mk.co.kr/news/realestate/",
    "한국경제":    "https://www.hankyung.com/realestate",
    "서울경제":    "https://www.sedaily.com/News/RealeState",
    "연합뉴스":    "https://www.yna.co.kr/economy/real-estate/",
    "부산일보":    "https://www.busan.com/economy/",
    "국제신문":    "http://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0220",
    "주택경제신문": "https://www.arunews.com/",
    "건설타임즈":  "https://www.constimes.co.kr/",
    "네이버부동산": "https://land.naver.com/news/",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://www.google.com/",
    "Cache-Control": "no-cache",
}

RSS_FEEDS = [
    ("한국경제",    "https://www.hankyung.com/feed/realestate",                    True),
    ("서울경제",    "https://www.sedaily.com/Rss/RealEstate",                      True),
    ("주택경제신문", "https://www.arunews.com/rss/allArticle.xml",                 True),
    ("건설타임즈",  "https://www.constimes.co.kr/rss/allArticle.xml",              True),
    ("매일경제",    "https://www.mk.co.kr/rss/30100041/",                          False),
    ("매일경제2",   "https://www.mk.co.kr/rss/50100032/",                          False),
    ("동아일보",    "https://rss.donga.com/economy.xml",                           False),
    ("한겨레",      "https://www.hani.co.kr/rss/economy/",                         False),
    ("연합뉴스",    "https://www.yna.co.kr/rss/economy.xml",                       False),
    ("아주경제",    "https://www.ajunews.com/rss/economy.xml",                     False),
    ("아시아경제",  "https://www.asiae.co.kr/rss/all.htm",                         False),
    ("조선일보",    "https://www.chosun.com/arc/outboundfeeds/rss/?outputType=xml", False),
    ("경남도민일보", "https://www.idomin.com/rss/allArticle.xml",                  False),
]

GOOGLE_QUERIES = [
    "부동산 청약 분양",
    "아파트 재건축 재개발",
    "부동산 세금 종부세 취득세",
    "부동산 정책 대출 금리",
    "아파트 매매 전세 집값",
    "부산 부동산 아파트",
    "해운대 아파트 분양",
    "부산 재건축 재개발",
    "경남 아파트 분양",
    "분양가 상한제 아파트",
    "임대차 전세 월세",
    "신도시 공공주택 공급",
]

# ══════════════════════════════════════════════════════════════════════════════
# 핵심 필터 3개 — 이 3개만 제대로 작동하면 비부동산·중복 99% 해결
# ══════════════════════════════════════════════════════════════════════════════

# [필터1] 부동산 핵심어 — 하나라도 없으면 수집 자체를 안 함
RE_ESTATE = re.compile(
    r'아파트|부동산|청약|재건축|재개발|전세|월세|임대|분양|주택|매매|'
    r'오피스텔|빌라|다세대|공동주택|정비사업|가로주택|'
    r'LH|SH|HUG|담보대출|주담대|전셋값|갭투자|분양가|'
    r'집값|매물|공시가|실거래|종부세|취득세|양도세|재산세|'
    r'신도시|택지|용적률|역세권|준공|착공|견본주택|모델하우스|'
    r'에코델타|오시리아|북항|재산세|입주물량|미분양'
)

# [필터2] 비부동산 제외어 — 하나라도 있으면 무조건 제거
# ★ 수정 포인트: 매수·매도·공급은 부동산 용어이므로 제외 목록에서 삭제
# ★ 수정 포인트: | 연결 정확히 작성 (줄 끝 |, 다음 줄 시작으로 연결)
RE_EXCLUDE = re.compile(
    r'숨진|사망|시신|변사|화상|부상|입건|구속|체포|검거|'
    r'화재|폭발|음주운전|교통사고|폭행|'
    r'전동킥보드|전동휠체어|오토바이|승용차 몰다|'
    r'코스피|코스닥|나스닥|환율|달러|증시|주가|주식|펀드|ETF|채권|'
    r'반도체|배터리|전기차|수출입|무역|관세|원자재|'
    r'열차|철도|항공|공항|항공편|비행기|선박|'
    r'태양광|풍력|수소|원전|발전소|배출권|탄소|'
    r'LNG|액화천연가스|플랜트|해양|제련소|항만|댐|터널|교량|도로공사|'
    r'폐작업복|필통|군 복무|병역|어린이집|미술관|도서관|공연|전시|'
    r'창업|귀농|스페이스X|공모주|상장|IPO|주식청약|'
    r'입찰공고|용역공고|협력업체 선정|현장설명회|현설|'
    r'선거|투표|정당|여당|야당|국회의원 선거|대통령 선거'
)

# [필터3] 시장동향 전용 2차 필터 — 시장동향으로 분류된 기사에만 적용
# 이 키워드가 없으면 시장동향에서도 제거 (비부동산 기사 차단)
RE_MARKET_REQUIRED = re.compile(
    r'아파트|부동산|주택|전세|월세|매매|집값|전셋값|매물|거래|'
    r'오피스텔|빌라|다세대|상가|토지|공시가|실거래|'
    r'임대|분양|입주|미분양|역세권|복합단지|용적률|'
    r'건설사|시행사|공사비|분양가|HUG|LH|SH|'
    r'관리처분|이주비|수주|인허가|사업승인|정비구역'
)

# ── 중복 제거용 상수 ──────────────────────────────────────────────────────────
STOPWORDS = {
    "은","는","이","가","을","를","의","에","도","와","과","하고","으로","로",
    "에서","까지","부터","이다","합니다","입니다","했다","한다","됩니다","됐다",
    "및","등","것","안","돼","않다","이라고","라며","라고","하며","있다","없다",
    "하다","된다","한","더","또","위해","대해",
}
LOC_ENTITIES = {
    "수도권","서울","강남","강북","부산","경기","인천","대구","광주","대전",
    "울산","세종","경남","해운대","수영","사하","동래","기장","연제","금정",
}
ORG_ENTITIES = {"국세청","한국부동산원","국토부","금융위","금감원","LH","SH","HUG"}

CAT_LIMITS = {
    "청약":    12,
    "재건축":  12,
    "공급개발": 10,
    "세제":    10,
    "정책":    10,
    "부산경남": 15,
    "시장동향": 15,
}

SOURCE_LIMITS = {
    "건설타임즈":  6,
    "주택경제신문": 6,
    "경남도민일보": 4,
}
