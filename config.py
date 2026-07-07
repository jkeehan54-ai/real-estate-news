"""
config.py
--------------------------------------------------
BRN Configuration
설정값과 상수만 관리
"""

from datetime import timezone, timedelta

# --------------------------------------------------
# Time Zone
# --------------------------------------------------

KST = timezone(timedelta(hours=9))

# --------------------------------------------------
# HTTP Header
# --------------------------------------------------

HEADERS = {
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",

    "Accept":
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8",

    "Accept-Language":
        "ko-KR,ko;q=0.9",

    "Referer":
        "https://www.google.com/",

    "Cache-Control":
        "no-cache",
}

# --------------------------------------------------
# News Sources
# --------------------------------------------------

SOURCES = {

    "조선일보":
        "https://www.chosun.com/economy/real_estate/",

    "중앙일보":
        "https://www.joongang.co.kr/realestate",

    "동아일보":
        "https://www.donga.com/news/Economy/Realestate",

    "한겨레":
        "https://www.hani.co.kr/arti/economy/property/",

    "매일경제":
        "https://www.mk.co.kr/news/realestate/",

    "한국경제":
        "https://www.hankyung.com/realestate",

    "서울경제":
        "https://www.sedaily.com/News/RealeState",

    "연합뉴스":
        "https://www.yna.co.kr/economy/real-estate/",

    "부산일보":
        "https://www.busan.com/economy/",

    "국제신문":
        "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0220",

    "주택경제신문":
        "https://www.arunews.com/",

    "건설타임즈":
        "https://www.constimes.co.kr/",

    "네이버부동산":
        "https://land.naver.com/news/",
}

# --------------------------------------------------
# RSS
# --------------------------------------------------

RSS_FEEDS = [

    ("한국경제",
     "https://www.hankyung.com/feed/realestate",
     True),

    ("서울경제",
     "https://www.sedaily.com/Rss/RealEstate",
     True),

    ("주택경제신문",
     "https://www.arunews.com/rss/allArticle.xml",
     True),

    ("건설타임즈",
     "https://www.constimes.co.kr/rss/allArticle.xml",
     True),

    ("매일경제",
     "https://www.mk.co.kr/rss/30100041/",
     False),

    ("매일경제2",
     "https://www.mk.co.kr/rss/50100032/",
     False),

    ("동아일보",
     "https://rss.donga.com/economy.xml",
     False),

    ("한겨레",
     "https://www.hani.co.kr/rss/economy/",
     False),

    ("연합뉴스",
     "https://www.yna.co.kr/rss/economy.xml",
     False),

    ("아주경제",
     "https://www.ajunews.com/rss/economy.xml",
     False),

    ("아시아경제",
     "https://www.asiae.co.kr/rss/all.htm",
     False),

    ("조선일보",
     "https://www.chosun.com/arc/outboundfeeds/rss/?outputType=xml",
     False),

    ("경남도민일보",
     "https://www.idomin.com/rss/allArticle.xml",
     False),
]

# --------------------------------------------------
# Google Query
# --------------------------------------------------

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

# --------------------------------------------------
# Category Limit
# --------------------------------------------------

CAT_LIMITS = {

    "청약": 12,

    "재건축": 12,

    "공급개발": 10,

    "세제": 10,

    "정책": 10,

    "부산경남": 15,

    "시장동향": 15,
}

# --------------------------------------------------
# Source Limit
# --------------------------------------------------

SOURCE_LIMITS = {

    "건설타임즈": 6,

    "주택경제신문": 6,

    "경남도민일보": 4,
}
