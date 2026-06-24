from playwright.sync_api import sync_playwright
import re
import sys, io
from difflib import SequenceMatcher
import html
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import feedparser, requests, re, os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.parse import urlparse
from urllib.parse import quote_plus

from datetime import datetime, timezone, timedelta

# --- 여기에 함수를 정의합니다 ---
def is_real_estate_news(title):
    title = title.strip()

    if not RE_ESTATE.search(title):
        return False

    if RE_EXCLUDE.search(title):
        return False

    if is_bad_news(title):
        return False

    return True
    
    # 제외할 키워드
    exclude_keywords = ["날씨", "운세", "강풍", "폭우", "사고", "침수", "호우", "태극기", "유튜버", "가격 폭탄"]
    if any(k in title for k in exclude_keywords):
        return False
        
    # 부동산 관련 키워드 (이 중 하나라도 있어야 함)
    include_keywords = ["아파트", "부동산", "재건축", "재개발", "청약", "분양", "주택", "용적률", "공급", "신도시", "종부세", "양도세", "전세"]
    return any(k in title for k in include_keywords)

KST = timezone(timedelta(hours=9))

SOURCES = {
    "조선일보":"https://www.chosun.com/economy/real_estate/",
    "중앙일보":"https://www.joongang.co.kr/realestate",
    "동아일보":"https://www.donga.com/news/Economy/Realestate",
    "한겨레":"https://www.hani.co.kr/arti/economy/property/",
    "매일경제":"https://www.mk.co.kr/news/realestate/",
    "한국경제":"https://www.hankyung.com/realestate",
    "서울경제":"https://www.sedaily.com/News/RealeState",
    "연합뉴스":"https://www.yna.co.kr/economy/real-estate/",
    "부산일보":"https://www.busan.com/economy/",
    "국제신문":"http://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200",
    "주택경제신문":"https://www.arunews.com/",
    "건설타임즈":"https://www.constimes.co.kr/",
    "네이버부동산":"https://land.naver.com/",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language":"ko-KR,ko;q=0.9",
    "Referer":"https://www.google.com/",
}

RSS_FEEDS = [
    ("한국경제", "https://www.hankyung.com/feed/realestate", True),
    ("서울경제", "https://www.sedaily.com/Feed/v1/20", True),
    ("주택경제신문", "https://www.arunews.com/rss/allRSS.xml", True),
    ("건설타임즈", "https://www.constimes.co.kr/rss/allRSS.xml", True),
    ("동아일보", "https://rss.donga.com/economy.xml", False),
    ("한겨레", "https://www.hani.co.kr/rss/economy/property/", False),
    ("연합뉴스", "https://feeds.yonhapnews.co.kr/national/RSS/economy.xml", False),
    ("연합뉴스2", "https://feeds.yonhapnews.co.kr/national/RSS/news.xml", False),
    ("아주경제", "https://www.ajunews.com/rss/economy.xml", False),
    ("아시아경제", "https://view.asiae.co.kr/rss/realestate.xml", False),
    ("조선일보", "https://www.chosun.com/arc/outboundfeeds/rss/?outputType=xml", False),
    ("경남도민일보", "https://www.idomin.com/rss/allArticle.xml", False),
    ("매일경제", "https://www.mk.co.kr/rss/realestate.xml", False) # 404가 나는 메인 rss/ 대신 부동산전용으로 변경
 ]


GOOGLE_QUERIES = [   
    "부동산 청약 분양",
    "아파트 재건축 재개발",
    "부동산 세금 종부세",
    "부동산 정책 대출 금리",
    "부동산 시장 매매 전세",

    "부산 부동산 site:busan.com",
    "부산 아파트 site:busan.com",
    "부산 재개발 site:busan.com",
    "부산 분양 site:busan.com",

    "부산 부동산 site:kookje.co.kr",
    "부산 아파트 site:kookje.co.kr",
    "부산 재개발 site:kookje.co.kr",
    "부산 분양 site:kookje.co.kr",

    "해운대 아파트",
    "부산 재건축",
    "부산 분양",

    "해운대 아파트 site:kookje.co.kr",
    "수영구 아파트 site:kookje.co.kr",
    "에코델타시티 site:kookje.co.kr",
    "오시리아 site:kookje.co.kr",

    "부산 재건축 site:kookje.co.kr",
    "부산 정비사업 site:kookje.co.kr",
    "부산 주택 site:kookje.co.kr",

    "해운대 아파트 site:busan.com",
    "수영구 아파트 site:busan.com",
    "에코델타시티 site:busan.com",
    "오시리아 site:busan.com",

    "부산 재건축 site:busan.com",
    "부산 정비사업 site:busan.com",
    "부산 주택 site:busan.com",
    "Google/매일경제 부동산", "부동산 site:mk.co.kr",
    "Google/부산일보 부동산", "부산 부동산 site:busan.com",
    "Google/국제신문 부동산", "부산 부동산 site:kookje.co.kr",
    "부동산",
    "아파트",
    "청약",
    "분양",
    "재건축",
    "재개발",
    
    "부산 부동산",
    "부산 아파트",

    "site:busan.com 부동산",
    "site:kookje.co.kr 부동산",

    "에코델타시티",
    "오시리아"
]
 
RE_ESTATE = re.compile(
      r'아파트|부동산|청약|분양|'
      r'재건축|재개발|정비사업|'
      r'주택|오피스텔|빌라|'
      r'전세|월세|임대|'
      r'입주|미분양|'
      r'집값|매물|전셋값|'
      r'주담대|전세대출|담보대출|'
      r'종부세|재산세|취득세|양도세|'
      r'용적률|역세권|'
      r'신도시|택지지구|'
      r'에코델타|오시리아|북항|'
      r'LH|SH|HUG|'
      r'견본주택|모델하우스'
      r'아파트|부동산|주택|청약|분양|'
      r'재건축|재개발|정비사업|리모델링|'
      r'전세|월세|임대|임차|'
      r'입주|미분양|악성미분양|'
      r'집값|매매가|전셋값|'
      r'주담대|DSR|LTV|DTI|'
      r'종부세|양도세|취득세|재산세|'
      r'용적률|건폐율|'
      r'택지|신도시|도시개발|'
      r'LH|SH|HUG|'
      r'모델하우스|견본주택|'
      r'에코델타|오시리아|북항'
)



RE_EXCLUDE = re.compile(
    r'숨진|사망|시신|변사|화상|부상|충돌|입건|구속|체포|검거|'
    r'화재|폭발|투표소|선거|후보|당선|낙선|'
    r'코스닥|코스피|주식|증권|'
    r'공개매수|지분매도|대량매도|주식매수|'
    r'만취|음주운전|교통사고|폭행|'
    r'전동킥보드|전동휠체어|오토바이|승용차 몰다'
    r'업무협약|MOU|상생대상|본사 이전|발전 5개사|기탁|봉사' # [추가]
)



STOPWORDS = {"은","는","이","가","을","를","의","에","도","와","과","하고","으로","로","에서","까지","부터","이다","합니다","입니다","했다","한다","됩니다","됐다","및","등","것","안","돼","안돼","반드시","이제","않다","이라고","라며","라고","하며","대해","위해","있다","없다","하다","된다","한","더","또"}
LOC_ENTITIES = {"수도권","서울","강남","강북","부산","경기","인천","대구","광주","대전","울산","세종","경남","해운대","수영","사하","동래","기장","연제","금정"}
ORG_ENTITIES = {"국세청","한국부동산원","국토부","금융위","금감원","LH","SH","HUG"}

def extract_date_from_url(url):
    m = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
    if m:
        try: return datetime(int(m.group(1)),int(m.group(2)),int(m.group(3)),6,0,tzinfo=KST)
        except: return None
    return None

def get_best_pub_dt(entry):
    d = extract_date_from_url(getattr(entry,'link',''))
    if d: return d
    pub = entry.get("published_parsed")
    if pub: return datetime(*pub[:6],tzinfo=timezone.utc).astimezone(KST)
    return None

def is_within_24h(entry, now_kst):
    d = get_best_pub_dt(entry)
    return True if d is None else (now_kst-d).total_seconds()<=86400


def normalize_title(title):

    title = title.lower()

    # 따옴표 제거
    title = re.sub(r"[\"'‘’“”]", "", title)

    # 괄호 제거
    title = re.sub(r"\[.*?\]", "", title)
    title = re.sub(r"\(.*?\)", "", title)

    # 언론사 꼬리 제거
    title = re.sub(r"\s*-\s*.*$", "", title)

    # 공백 정리
    title = re.sub(r"\s+", " ", title)

    return title.strip()

def keywords(title):
    return {w for w in normalize(title).split() if w not in STOPWORDS and len(w)>=2}

def extract_entities(title):
    t = re.sub(r'[^\w\s]',' ',title)
    ents = set()
    for m in re.finditer(r'\d+\.?\d*\s*(?:억|만|건|%|개월|층|평|채|명|가구)',t): ents.add(m.group().strip())
    for loc in LOC_ENTITIES:
        if loc in t: ents.add(loc)
    for org in ORG_ENTITIES:
        if org in t: ents.add(org)
    return ents



from urllib.parse import urlparse

def normalize_url(url):
    p = urlparse(url)
    return f"{p.netloc}{p.path}"

def normalize_title(t):
    

    t = t.lower()

    # 괄호 제거
    t = re.sub(r'\([^)]*\)', '', t)
    t = re.sub(r'\[[^\]]*\]', '', t)

    # 특수문자 제거
    t = re.sub(r'[^\w\s]', ' ', t)

    # 회사명 제거
    t = re.sub(r'현대건설', '', t)
    t = re.sub(r'삼성물산', '', t)
    t = re.sub(r'포스코이앤씨', '', t)
    t = re.sub(r'dl이앤씨', '', t)

    # 동일 기사 표현 통일
    t = re.sub(r'고양대전환준비위원회', '고양시', t)
    t = re.sub(r'민선\s*\d+기', '', t)

    t = re.sub(r'적극 검토', '검토', t)
 
    t = re.sub(r'착수', '', t)
    t = re.sub(r'고양대전환준비위', '고양시', t)
    t = re.sub(r'민선\s*\d+기', '', t)

    t = re.sub(r'일산신도시', '일산', t)


    t = re.sub(r'상향안', '', t)
   
    t = re.sub(r'검토 착수', '검토', t)

    t = re.sub(r'용적률\s*350%', '용적률', t)
    t = re.sub(r'300%\s*→\s*350%', '용적률', t)

    # 범천4구역 기사 통합
    t = re.sub(r'현대건설.*범천4구역', '범천4구역 재개발', t)
    t = re.sub(r'주택재개발정비사업', '재개발', t)
    t = re.sub(r'계약 체결', '', t)
    t = re.sub(r'규모', '', t)
    
    t = re.sub(r'범천4구역 주택재개발정비사업', '범천4구역 재개발', t)

    t = re.sub(r'8531억.*', '', t)
    # 숫자 제거
    t = re.sub(r'\d+억원?', '', t)
    t = re.sub(r'\d+주 연속', '', t)
    t = re.sub(r'\d+%', '', t)
    t = re.sub(r'\d+억', '', t)
    t = re.sub(r'\d+가구', '', t)

    t = re.sub(r'3\.3㎡당', '', t)
    t = re.sub(r'평당', '', t)

    # 언론사 꼬리 제거
    t = re.sub(
        r'\s*-\s*(뉴스1|네이트|daum|v\.daum\.net|chosunbiz|조선비즈).*',
        '',
        t,
        flags=re.I
    )

    # 공백 정리
    t = re.sub(r'\s+', ' ', t)

    return t.strip()

    
def is_duplicate(title, seen_titles):
    title_n = normalize_title(title)
    for old in seen_titles:
        old_n = normalize_title(old)
        # 임계치를 0.92로 상향하여 조금이라도 다른 내용은 별도 기사로 인정
        ratio = SequenceMatcher(None, title_n, old_n).ratio()
        if ratio >= 0.92:
            return True
    return False

LOCAL_EXCLUDE = [
    "체험",
    "축제",
    "공연",
    "행사",
    "발대식",
    "복지관",
    "어린이",
    "봉사",
    "기탁",
    "시민기자",
    "전시",
    "체육회",
    "핸드볼",
    "야구장",
    "도서관",
    "문화센터",
    "환승센터",
    "경로당",
    "개소",
    "개소식",
    "주민 화합",
    "의원",
    "조례",
    "본회의",
    "문화",
    "체육",
    "봉사",
    "복지",
]

BAD_KEYWORDS = [
    "입찰공고",
    "협력업체",
    "감정평가법인",
    "법무법인",
    "해체계획서",
    "현금청산",
    "물김치",
    "폐건전지",
    "이동상담실",
    "자율방재단",
    "어린이집",
    "복지안전망",
    "투표용지",
    "도박단",
    "환송식",
    "낙하산",
    "뭐라노",
    "칼럼",
    "사설",
    # 정치
    "대통령",
    "국회",
    "선거",
    "투표",
    "정청래",

    # 사건사고
    "화재",
    "도박",
    "검거",
    "사기",
    "사망",
    "추락",

    # 경제 일반
    "수출",
    "주식",
    "코스피",
    "공개매수",

    # 금융
    "코스닥",
    "코스피",
    "사이드카",
    "주가",
    "증시",
    "주식",
    "AI 자금조달",
    "카카오뱅크",
    "케이뱅크",
    "농협은행",
    "기준금리",
    "통화정책",

    # 문화
    "미술관",
    "도서관",
    "전시",
    "공연",

    # 지역행정
    "어린이집",
    "복지",
    "보건",
    "자원순환",

    # 출판
    "신간",
    "출간",
    "도서",

    # 기타
    "타운홀",
    "워크숍",
    "철도문화전",
    "시간여행"
    "국제",
    "사칭",
    "복지",
    "발달장애인",
    "시장",
    "어울림",
    "투표상자",
    "증거보전",
    "조명공장",
    "나눔",
    "센터 개소",
    "국제",
    "시간여행",
    "승차권",
    "북극항로",
    "유조선",
    "중학교",
    "배정",
    "교량",
    "병원 이송",
    "기계설비",
    "가스시공",
    "공시 현장",
    "CEO",
    "캠페인",
    "상생협력",
    "대표 선임",
    "협력사",
    "공장",
    "붕괴",
    "창업",
    "귀농",
    "철도",
    "풍력",
    "설계공모",
    "응모 공고",
    "현상설계",
    "시공자 현설",
    "증거인멸",
    "국고채",
    "금융범죄",
    "과학수사",
    "예방",
    "빚투",
    "주가",
    "증시",
    "금융권",
    "환경정화",
    "대청소",
    "틈새건강",
    "캐시백",
    "도로학회",
    "건설기술인",
    "핵융합",
    "케어닥",
    "모빌리티",
    "스페이스X",
    "공모주",
    "상장",
    "주식청약",
    "인사",
    "법원 판결",
    "정보공개 의무",
    "기술평가위",
    "건설기술인",
    "협회",
    # 사건사고
    "화재",
    "산불",
    "사망",
    "부상",
    "범죄",
    "검거",
    "음주운전",
    "불",
    "사망",
    "사고",
    "폭발",
    "실종",
    "살인",
    "구속",
    "검찰",
    "경찰",
    "해수면",
    "기후변화",
    "로봇청소기",
    "가전",
    "CBRE",
    "물류자산",
    "[표]",
    "난민",
    "UNHCR",
    "투자자별 매매동향",
    "코스닥",
    "코스피",
    "사이드카",
    "매각 공고",
    "입찰 공고",
    "용역 공고",
    "유치원시설",
    "이재명",
    "오세훈",
    "대통령",
    "정권",
    "민주당",
    "국민의힘",
    "수주",
    "수주공시",
    "방음벽",
    "소음",
    "난민",
    "사이드카",
    "코스닥",
    "코스피",
    "ETF",
    "인사",
    "공고",
    "매각"
    "갤러리 오픈",
    "오픈하우스",
    "고분양태",
    "무형유산",
    "종합병원",
    "병원",
    "의료",
    "환자",
    "외상환자",
    "BTS",
    "역조공",
    "인도女",
    "건설사업본부장",
    "감사원",
    "인천공항공사",
    "외상 환자",
    "본부장",
    "선출",
    "자동차담보대출",
    "캐피탈",
    "실버타운",
    "재건 특수",
    "이란",
    "예비위원장",
    "위원장 선출",
    "본부장 선임",
    "역조공",
    "BTS",
    "극적 구조",
    "게시판",
    "피살",
    "살인",
    "시신",
    "용의자",
    "추적 중",
    "당선인",
    "구청장",
    "시장 당선",
    "군수",
    "모델하우스 탐방",
    "견본주택에",
    "방문객 몰려",
    "분양홍보관",
    "오픈하우스",
    "업무협약", "상생대상", "유치 본격화", "발전 5개사",
    "연극",
    "영화",
    "드라마",
    "비트코인",
    "가상자산",
    "희토류",
    "방산",
    "주식",
    "코인",
    "하노이",
    "베트남",
    "중국",
    "일본",
    "미국",
    "싱가포르",
    "드라마",
    "영화",
    "배우",
    "가수",
    "포스터",
    "예능",
    "방송",
    "행복home",
    "사회공헌",
    "봉사활동",
    "취약계층",
    "후원",
    "기부",
    "캠페인"
]

BAD_SOURCES = [
    "nate.com",
    "youtube.com",
]

BUSAN_KEYWORDS = [
    "부산",
    "해운대",
    "수영구",
    "부남구",
    "동래",
    "사상",
    "사하",
    "강서구",
    "에코델타",
    "오시리아",
    "센텀",
    "북항",
    "범천",
    "좌천",
    "재송",
    "기장",
    "정관",
    "명지",
]

REAL_ESTATE_KEYWORDS = {
    "부동산": 3,
    "아파트": 2,
    "청약": 4,
    "분양": 4,
    "재건축": 5,
    "재개발": 5,
    "정비사업": 5,
    "주택": 3,
    "오피스텔": 3,
    "전세": 3,
    "월세": 3,
    "매매": 3,
    "입주": 3,
    "공급": 2,
    "신도시": 3,
    "용적률": 3,
    "역세권": 2,
    "주담대": 4,
    "DSR": 4,
    "LTV": 4,
    "종부세": 5,
    "양도세": 5,
    "취득세": 5,
}

NEGATIVE_KEYWORDS = [
    "배우",
    "드라마",
    "영화",
    "가수",
    "포스터",
    "연극",
    "축제",
    "공연",
    "경로당",
    "복지관",
    "봉사",
    "기부",
    "캠페인",
    "이혼",
    "외도",
    "재산분할",
    "학교",
]

def real_estate_score(title):

    score = 0

    for kw, weight in REAL_ESTATE_KEYWORDS.items():
        if kw in title:
            score += weight

    for kw in NEGATIVE_KEYWORDS:
        if kw in title:
            score -= 5

    return score

    score = real_estate_score(title)

    if score < 3:
        dropped += 1
        print(f"[DROP {score}] {title}")
        continue

def classify(title, src):
    t = title
    
    EXCLUDE_KEYWORDS = [
    "경로당",
    "개소식",
    "복지관",
    "노인회",
    "축제",
    "문화행사",
    "공연",
    "전시",
    "드라마",
    "영화",
    "배우",
    "가수",
    "포스터"
    "외도",
    "재산분할",
    "이혼",
    "맞춤복",
    "기성복",
    "갑질",
    "동대표",
    "관리실",
    "전원 사표",
    "법률상담",
    "로톡",    
    ]

    if any(k in title for k in EXCLUDE_KEYWORDS):
        return "기타"

    if any(k in title for k in BUSAN_KEYWORDS):

        if real_estate_score(title) >= 3:
            return "부산경남"

    if "공모청약" in title:
        return "기타"

    if "상장" in title:
        return "기타"
    
    # [정책] 카테고리 확장
    if any(keyword in title for keyword in ["정책", "규제", "국토부", "기획재정부", "금리", "대출", "DSR", "LTV", "DTI", "규제"]):
        return "정책"
        
    # [세제] 카테고리 확장
    if any(keyword in title for keyword in ["세금", "종부세", "양도세", "취득세", "세제", "공시가격"]):
        return "세제"
    
    # [추가] 국제신문 기사 강제 분류
    if "국제신문" in src or "kookje.co.kr" in title:
        return "부산경남"

    # 1. 지역 언론사 우선 분류
    # [강화] 매일경제, 부산일보, 국제신문은 최우선순위로 처리
    if src in ["부산일보", "국제신문"]:
        return "부산경남"
    if src in ["매일경제", "매일경제2"]:
        # 매경 기사는 경제/시장동향으로 우선 분류
        return "시장동향"
    
    # 2. [추가] 제목에 부산 관련 키워드가 있으면 지역 뉴스로 분류
    # 전국 매체라도 부산 관련 내용이면 부산 카테고리로 모아줍니다.
    if "에코델타" in title and "부산" in title:
        return "부산경남"
    if any(k in t for k in ["부산", "해운대", "에코델타", "오시리아", "수영구", "명지", "북항", "센텀"]):
        return "부산경남"

    # 3. 주제별 분류
    if any(k in t for k in ["청약", "무순위", "특별공급"]):
        return "청약"
    elif any(k in t for k in ["재건축", "재개발", "정비사업", "가로주택", "리모델링"]):
        return "재건축"
    elif any(k in t for k in ["신도시", "3기 신도시", "착공", "분양", "입주", "공급", "택지", "역세권"]):
        return "공급개발"
    
    elif any(k in t for k in [
        "종부세",
        "재산세",
        "양도세",
        "취득세",
        "세금"
    ]):
        return "세제"

    elif any(k in t for k in [
        "주담대",
        "주택담보대출",
        "전세대출",
        "주거자금",
        "모기지",
        "DSR",
        "LTV",
        "DTI",
        "대출규제",
        "규제완화"
    ]):
        return "정책"

    elif src in ["부산일보","국제신문","경남도민일보"]:

        if any(k in t for k in [
             "아파트",
             "부동산",
             "분양",
             "청약",
             "재건축",
             "재개발",
             "정비사업",
             "주택",
             "오피스텔",
             "전세",
             "월세",
             "미분양",
             "용적률",
             "신도시",
             "에코델타",
             "오시리아"
        ]):
             return "부산경남"

    
    return "시장동향"


def is_bad_news(title):
    return any(k in title for k in BAD_KEYWORDS)       


def fetch_rss(name, url, estate_only, now_kst):
    items = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        for entry in feed.entries:
            if not is_within_24h(entry, now_kst): continue
            title = (entry.title or "").strip()
            if not title: continue
            if any(x in title for x in LOCAL_EXCLUDE):
                continue

            if not RE_ESTATE.search(title):
                continue

            if RE_EXCLUDE.search(title):
                continue

            if is_bad_news(title):
                continue

            
            src = entry.source.title if hasattr(entry,'source') and hasattr(entry.source,'title') else name
            items.append((get_best_pub_dt(entry), title, entry.link, src))
        print(f"  OK [{name}] {len(items)}geon")
    except Exception as e:
        print(f"  ER [{name}] {type(e).__name__}: {str(e)[:50]}")
    return items

def fetch_google(now_kst):
    items = []
    for q in GOOGLE_QUERIES:
        try:
            url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=ko&gl=KR&ceid=KR:ko"
            resp = requests.get(url, headers=HEADERS, timeout=8)
            feed = feedparser.parse(resp.content)
            cnt = 0
            for entry in feed.entries:
                if not is_within_24h(entry, now_kst): continue
                title = (entry.title or "").strip()
                if not title: continue
                if any(x in title for x in LOCAL_EXCLUDE):
                     continue
                if not RE_ESTATE.search(title):
                    continue

                if RE_EXCLUDE.search(title):
                    continue

                if is_bad_news(title):
                    continue

                
                src = entry.source.title if hasattr(entry,'source') and hasattr(entry.source,'title') else "news"
                
                if ( "land.naver.com" in entry.link or "fin.land.naver.com" in entry.link
                ):
                   src = "네이버부동산"

                elif src in ["Naver Blog", "네이버"]:
                    src = "네이버부동산"

                if "busan.com" in entry.link:
                    src = "부산일보"

                if "kookje.co.kr" in entry.link:
                    src = "국제신문"
                
                items.append((get_best_pub_dt(entry), title, entry.link, src))
                cnt += 1
            print(f"  OK [Google/{q}] {cnt}geon")
        except Exception as e:
            print(f"  ER [Google/{q}] {type(e).__name__}: {str(e)[:50]}")
    return items
def fetch_naver_news(now_kst):
    items = []

    try:
        url = "https://land.naver.com/news/headline.naver"
        resp = requests.get(url, headers=HEADERS, timeout=10)

        soup = BeautifulSoup(resp.text, "html.parser")

        for a in soup.select("a"):
            href = a.get("href", "")

            if not href.startswith("https://n.news.naver.com"):
                continue

            title = a.get("title", "").strip()

            if not title:
                 title = a.get_text(strip=True)

            if len(title) < 15:
                continue
            if any(x in title for x in LOCAL_EXCLUDE):
                 continue

            if not RE_ESTATE.search(title):
                continue

            if RE_EXCLUDE.search(title):
                continue

            if is_bad_news(title):
                continue
        
            try:
                article_html = requests.get(
                    href,
                    headers=HEADERS,
                    timeout=5
                ).text

                m = re.search(
                    r'<meta property="og:title" content="([^"]+)"',
                    article_html
                )

                if m:
                    title = m.group(1)

            except Exception:
                pass

            
            items.append(
                  (
                       now_kst,
                       title,
                       href,
                       "네이버부동산"
                  )
         )

        print(f"  OK [NAVER_NEWS] {len(items)}geon")

    except Exception as e:
        print(f"  ER [NAVER_NEWS] {type(e).__name__}: {str(e)[:50]}")

    return items

def get_clean_news():
    LIMITS = {
        "청약": 3,
        "재건축": 10,
        "공급개발": 10,
        "세제": 20,
        "정책": 5,
        "부산경남": 8,
        "시장동향": 12,
    }

    SOURCE_LIMITS = {
        "건설타임즈": 5,
        "주택경제신문": 5,
        "연합뉴스": 4,
        "서울경제": 5,
        "경남도민일보": 3,      # 비중 대폭 축소 (기존 12 -> 3)
        "매일경제": 5,        # 매일경제 우선 확보 (강제 수집)
        "매일경제 마켓": 5,
        "부산일보": 10,
        "국제신문": 10,
        "한국경제": 5,
        "네이버부동산": 6,
    }

    cats = ["부산경남", "청약", "재건축", "공급개발", "세제", "정책", "시장동향"]
    results = {c: [] for c in cats}
    
    # [수정] 변수 정의를 명확히 상단에 배치
    seen = set()
    seen_titles = []
    seen_normalized = set()
    source_count = {}

    now_kst = datetime.now(KST)
    all_entries = []

    print("[1단계] RSS")
    for item in RSS_FEEDS:
        # 리스트 항목 개수에 따라 유연하게 처리
        name = item[0]
        url = item[1]
        eo = item[2] if len(item) > 2 else True
        
        try:
            # fetch_rss 함수 호출 및 결과 저장
            entries = fetch_rss(name, url, eo, now_kst)
            if entries:
                all_entries.extend(entries)
        except Exception as e:
            print(f"  [!] 수집 중 오류 [{name}]: {e}")
            continue

    print("[1.5단계] NAVER")
    all_entries.extend(fetch_naver_news(now_kst))

    print("[2단계] Google")
    all_entries.extend(fetch_google(now_kst))
    all_entries.sort(key=lambda x:x[0] or datetime.max.replace(tzinfo=KST),reverse=True)
    total=dropped=0

    for pub_dt, title, link, src in all_entries:
        total += 1

        norm_title = normalize_title(title)

        # 디버그 출력
        print("ORIGINAL:", title)
        print("NORMAL  :", norm_title)

        duplicate = False

        score = real_estate_score(title)

        if score < 2:
            dropped += 1
            print(f"[DROP SCORE={score}] {title}")
            continue
        
        for old in seen_normalized:
            score = SequenceMatcher(None, norm_title, old).ratio()

            if score >= 0.84:
                print(f"[DUP] {score:.2f} | {title}")
                duplicate = True
                break

        if duplicate:
           dropped += 1
           continue

        seen_normalized.add(norm_title)

        if link in seen:
            dropped += 1
            continue

        cat = classify(title, src)
        if cat not in results:
            dropped += 1
            continue
        cnt = source_count.get(src, 0)

        if cnt >= SOURCE_LIMITS.get(src, 999):
           dropped += 1
           continue

        if len(results[cat]) >= LIMITS.get(cat, 999):
           dropped += 1
           continue

        results[cat].append((title, link, src))
        seen.add(link)
        source_count[src] = cnt + 1

        print(f"[SAVE] {cat} {src} {title}")

        norm_title = normalize_title(title)

        if "범천4구역" in title:
            print("[ORIGINAL]", title)
            print("[NORMAL]", norm_title)
    
    # 루프 종료 후 결과 출력
    print(f"\n[result] total={total} dup={dropped} kept={total-dropped}")

    print("\n=== SOURCE COUNT ===")
    for k, v in sorted(source_count.items()):
        print(f" {k} {v}")

    return results

def interleave_by_source(items):
     groups = {}

     for item in items:
          groups.setdefault(item["src"], []).append(item)

     result = []

     while True:
          added = False

          for src in list(groups.keys()):
               if groups[src]:
                   result.append(groups[src].pop(0))
                   added = True

          if not added:
             break

     return result

import requests
from bs4 import BeautifulSoup
import re

def get_market_brief():

    try:

        url = (
            "https://api.kbland.kr/land-extra/market-conditions/sales"
            "?기준년월일=20260615"
            "&법정동코드=0000000000"
        )

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://kbland.kr",
            "Referer": "https://kbland.kr/",
            "webservice": "1"
        }

        r = requests.get(
            url,
            headers=headers,
            timeout=20
        )
        print("[KB STATUS]", r.status_code)
        print("[KB RESPONSE]", r.text[:5000])
        
        data = r.json()

        summary = data["dataBody"]["data"]["시장요약"]

        change = summary["대표지역변동률"]
        weeks = summary["대표지역변동률연속주수"]
        trend = summary["대표지역변동률연속상태"]

        seller = summary["매도자많음응답"]
        buyer = summary["매수자많음응답"]

        all_market = data["dataBody"]["data"]["전체시황"]

        seoul = next(
            x["변동률"]
            for x in all_market
            if x["지역명"] == "서울"
        )

        busan = next(
            x["변동률"]
            for x in all_market
            if x["지역명"] == "부산"
        )

        return (
            f"전국 아파트 매매가격은 {change}% {trend}했습니다. "
            f"{weeks}주 연속 {trend}세를 유지했습니다. "
            f"서울은 {seoul}% 상승, 부산은 {busan}% 보합입니다. "
            f"매도자많음 {seller}%, 매수자많음 {buyer}%입니다."
        )

    except Exception as e:
        print("[KB ERROR]", repr(e))

    return "KB 시황 정보를 불러오지 못했습니다."


def build_html(data):

    html = ""
    now = datetime.now(KST)

    today = now.strftime("%Y년 %m월 %d일")
    update_time = now.strftime("%Y-%m-%d %H:%M:%S KST")

    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>부동산 뉴스 브리핑</title>

<style>
body {{
       font-family: "Malgun Gothic", sans-serif;
       max-width: 1200px;
       margin: auto;
       padding: 20px;
       line-height: 1.7;
}}

h1 {{
    color: #1f4fa3;
}}

h2 {{
     background: #f2f6ff;
     padding: 10px;
     border-left: 5px solid #1f4fa3;
}}

a {{
    text-decoration: none;
    color: #222;
}}

a:hover {{
    text-decoration: underline;
}}

small {{
    color: #666;
}}
</style>

</head>
<body>

<h1>부동산 뉴스 브리핑 ({today})</h1>
<p>업데이트: {update_time}</p>
"""

    html += "<hr><p><b>뉴스매체 바로가기</b> : "

    html += " | ".join(
        f"<a href='{url}' target='_blank'>{name}</a>"
        for name, url in SOURCES.items()
    )

    html += "</p><hr>"

    market_brief = get_market_brief()

    html += f"""
    <div style="
    background:#fff3cd;
    padding:12px;
    border-radius:6px;
    border-left:4px solid #ffc107;
    margin:15px 0;
    font-weight:bold;
    ">
    {market_brief}
    </div>
    """




    labels = {
         "청약": "[청약]",
         "재건축": "[재건축·재개발]",
         "공급개발": "[공급·개발]",
         "세제": "[세제]",
         "정책": "[정책]",
         "부산경남": "[부산·경남]",
         "시장동향": "[시장동향]"
    }

    for cat, lst in data.items():
        # 데이터가 없으면 건너뜀
        if not lst:
            continue

        html += f"<h2>{labels.get(cat, cat)}</h2>"
        html += "<ul>"
        
        for n in lst:
            # n은 (title, link, src) 튜플입니다.
            # 인덱스 0: title, 1: link, 2: src
            title = n[0]
            link = n[1]
            src = n[2]
            
            # 리스트 아이템 생성
            html += f"<li><a href='{link}' target='_blank'>{title}</a> - {src}</li>"
            
        html += "</ul>"

    html += "</body></html>"
    return html


if __name__ == "__main__":
       output_path = os.path.join(
           os.path.dirname(os.path.abspath(__file__)),
           "index.html"
       )

       data = get_clean_news()

       with open(output_path, "w", encoding="utf-8-sig") as f:
           f.write(build_html(data))

       print(f"[done] {output_path}")

       for cat, lst in data.items():
            print(f"  [{cat}] {len(lst)}")


