import feedparser
import requests
from urllib.parse import quote_plus
from difflib import SequenceMatcher
from datetime import datetime, timezone, timedelta
import re

# ── 설정 및 기본값 ─────────────────────────────────────────────────────────────
KST = timezone(timedelta(hours=9))
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

DIRECT_RSS = [
    ("연합뉴스", "https://www.yna.co.kr/economy/real-estate/rss.xml", True),
    ("매일경제", "https://www.mk.co.kr/rss/50200030/", True),
    ("한국경제", "https://www.hankyung.com/feed/realestate", True),
    ("머니투데이", "https://news.mt.co.kr/mtview/rss/estate.xml", True),
    ("이데일리", "https://www.edaily.co.kr/rss/realestate.xml", True),
    ("서울경제", "https://www.sedaily.com/Rss/RealEstate", True),
    ("헤럴드경제", "https://biz.heraldcorp.com/rss/realestate.xml", True),
    ("뉴시스", "https://www.newsis.com/rss/realestate.xml", True),
    ("아주경제", "https://www.ajunews.com/rss/realestate.xml", True),
    ("파이낸셜뉴스", "https://www.fnnews.com/rss/fn_realestate_news.xml", True),
    ("조선일보", "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/real_estate/", True),
    ("동아일보", "https://rss.donga.com/economy.xml", False),
    ("부산일보", "https://www.busan.com/rss/rss_article.jsp?sec_cd=1010", False),
    ("국제신문", "https://www.kookje.co.kr/news2011/rss/rss_0200.xml", False),
    ("네이버뉴스", "https://rss.news.naver.com/cs/rss/estate.xml", True),
]

GOOGLE_QUERIES = ["부동산 청약", "아파트 재건축 재개발", "부동산 세금 종부세", "부동산 정책", "부동산 시장", "부산 부동산"]

# (중복제거/분류 로직은 이전 코드와 동일하게 유지됨)
def normalize(title: str) -> str:
    title = re.split(r'\s[-|]\s', title)[0].strip()
    title = re.sub(r'^\[.*?\]\s*', '', title)
    title = re.sub(r'\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}', '', title)
    title = re.sub(r'[^\w\s]', ' ', title)
    return re.sub(r'\s+', ' ', title).strip()

def classify(title: str) -> str:
    t = normalize(title).lower()
    if any(k in t for k in ["분양","청약"]): return "청약"
    elif any(k in t for k in ["재건축","재개발"]): return "재건축"
    elif any(k in t for k in ["세금","종부세","취득세","양도세"]): return "세제"
    elif any(k in t for k in ["정부","대출","금리","정책","규제"]): return "정책"
    elif any(k in t for k in ["부산","해운대","사하","동래","강서","기장"]): return "부산"
    return "시장동향"

# ... (기타 함수 생략: 위에서 제공해주신 로직 그대로 사용) ...

# ── 메인 실행 루틴 ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # get_clean_news() 호출 후 데이터 로드
    data = get_clean_news()
    
    # HTML 생성
    html_content = build_html(data)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print("\n[완료] index.html이 생성되었습니다. 오늘 날짜 브리핑을 확인하세요.")
