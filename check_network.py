"""
네트워크 및 RSS 수집 진단 스크립트
실행: python check_network.py
결과를 공유해주시면 문제를 정확히 파악할 수 있습니다.
"""
import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import requests, feedparser, re
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

print("=" * 60)
print("부동산 경기 지표 - 네트워크 진단")
print(f"실행시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# 1. 기본 인터넷 연결 확인
print("\n[1단계] 인터넷 연결 확인")
test_urls = [
    ("Google",      "https://www.google.com"),
    ("Naver",       "https://www.naver.com"),
    ("한국경제",    "https://www.hankyung.com"),
    ("연합뉴스",    "https://www.yna.co.kr"),
    ("Google News", "https://news.google.com"),
]
for name, url in test_urls:
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        print(f"  OK  {name}: HTTP {r.status_code} ({len(r.text):,}자)")
    except Exception as e:
        print(f"  ERR {name}: {type(e).__name__} - {str(e)[:60]}")

# 2. RSS 피드 개별 테스트
print("\n[2단계] RSS 피드 수집 테스트")
rss_list = [
    ("한국경제 부동산",  "https://www.hankyung.com/feed/realestate"),
    ("서울경제 부동산",  "https://www.sedaily.com/Rss/RealEstate"),
    ("매일경제 부동산",  "https://www.mk.co.kr/rss/30100041/"),
    ("연합뉴스 경제",   "https://www.yna.co.kr/rss/economy.xml"),
    ("아시아경제",      "https://www.asiae.co.kr/rss/all.htm"),
    ("동아일보 경제",   "https://rss.donga.com/economy.xml"),
    ("한겨레 경제",     "https://www.hani.co.kr/rss/economy/"),
    ("아주경제",        "https://www.ajunews.com/rss/economy.xml"),
    ("조선일보",        "https://www.chosun.com/arc/outboundfeeds/rss/?outputType=xml"),
    ("주택경제신문",    "https://www.arunews.com/rss/allArticle.xml"),
    ("건설타임즈",      "https://www.constimes.co.kr/rss/allArticle.xml"),
]
working = []
for name, url in rss_list:
    try:
        r    = requests.get(url, headers=HEADERS, timeout=8)
        feed = feedparser.parse(r.content)
        n    = len(feed.entries)
        if n > 0:
            sample = feed.entries[0].get("title","")[:50]
            print(f"  OK  [{name}] {n}건 | 샘플: {sample}")
            working.append((name, url, n))
        else:
            print(f"  NO  [{name}] HTTP {r.status_code} | 0건 (응답은 됨)")
    except Exception as e:
        print(f"  ERR [{name}]: {type(e).__name__} - {str(e)[:60]}")

# 3. Google News RSS 테스트
print("\n[3단계] Google News RSS 테스트")
gn_queries = [
    "아파트 매매가격",
    "부동산 시장",
    "KB부동산",
    "미분양",
    "전세가율",
]
gn_working = []
for q in gn_queries:
    try:
        url  = f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=ko&gl=KR&ceid=KR:ko"
        r    = requests.get(url, headers=HEADERS, timeout=10)
        feed = feedparser.parse(r.content)
        n    = len(feed.entries)
        if n > 0:
            sample = feed.entries[0].get("title","")[:50]
            print(f"  OK  [{q}] {n}건 | 샘플: {sample}")
            gn_working.append(q)
        else:
            print(f"  NO  [{q}] HTTP {r.status_code} | 0건")
    except Exception as e:
        print(f"  ERR [{q}]: {type(e).__name__} - {str(e)[:60]}")

# 4. 작동하는 RSS에서 KB 시황 기사 탐색
if working:
    print(f"\n[4단계] 작동하는 RSS {len(working)}개에서 KB시황 기사 탐색")
    KB_KEYS  = ["KB","KB부동산","국민은행","매수우위","주간 아파트"]
    EST_KEYS = ["아파트","매매가격","매매가"]
    found = 0
    for name, url, _ in working:
        try:
            r    = requests.get(url, headers=HEADERS, timeout=8)
            feed = feedparser.parse(r.content)
            for e in feed.entries:
                t = e.get("title","")
                s = (e.get("summary","") or "")[:200]
                text = t + " " + s
                if any(k in text for k in KB_KEYS) and any(k in text for k in EST_KEYS):
                    pcts = re.findall(r'[-+]?\d+\.\d+\s*%', text)
                    weeks= re.findall(r'\d+\s*주', text)
                    print(f"  [KB시황] [{name}] {t[:60]}")
                    print(f"    수치: {pcts[:5]} | 주수: {weeks[:3]}")
                    found += 1
        except Exception:
            pass
    if found == 0:
        print("  KB 시황 기사를 찾지 못했습니다.")
        print("  → KB부동산 주간 시황은 매주 목요일 발표됩니다.")
        print("  → 오늘 기사가 없으면 이전 주 데이터가 수집됩니다.")

# 5. 종합 결과
print("\n" + "=" * 60)
print("진단 결과 요약")
print("=" * 60)
print(f"  작동하는 RSS 피드: {len(working)}개")
print(f"  작동하는 Google News 쿼리: {len(gn_working)}개")
if working:
    print(f"  수집 가능 매체: {', '.join(n for n,_,_ in working[:5])}")
if not working and not gn_working:
    print("\n  [원인 분석]")
    print("  1. 회사/학교 네트워크 방화벽 차단 가능성")
    print("  2. VPN 사용 중인 경우 RSS 접근 제한")
    print("  3. 프록시 설정 문제")
    print("\n  [해결 방법]")
    print("  1. 다른 네트워크(모바일 핫스팟)에서 테스트")
    print("  2. 브라우저에서 https://www.hankyung.com/feed/realestate 직접 접근해보기")
    print("  3. 회사 방화벽 담당자에게 RSS 허용 요청")