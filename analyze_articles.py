import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import requests, feedparser, re

HEADERS = {"User-Agent": "Mozilla/5.0 Chrome/124.0.0.0 Safari/537.36", "Accept-Language": "ko-KR,ko;q=0.9"}

def gn(q, n=5):
    url = f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=ko&gl=KR&ceid=KR:ko"
    return feedparser.parse(requests.get(url, headers=HEADERS, timeout=10).content).entries[:n]

def rss(url, n=50):
    try: return feedparser.parse(requests.get(url, headers=HEADERS, timeout=8).content).entries[:n]
    except: return []

print("===== KB 주간시황 =====")
rss_urls = ["https://www.sedaily.com/Rss/RealEstate","https://www.mk.co.kr/rss/30100041/","https://www.arunews.com/rss/allArticle.xml","https://www.yna.co.kr/rss/economy.xml"]
for url in rss_urls:
    for e in rss(url):
        t = e.get("title",""); s = (e.get("summary","") or "")[:200]
        if any(k in t+s for k in ["KB","국민은행","주간","아파트값","아파트 매매"]) and "%" in t+s:
            pcts = re.findall(r'[-+]?\d+\.\d+\s*%', t+" "+s)
            weeks= re.findall(r'\d+\s*주\s*(?:연속|째)', t+" "+s)
            if pcts: print(f"\n[{url.split('/')[2]}]\n제목: {t}\n요약: {s[:120]}\n수치: {pcts[:5]} | 주수: {weeks}")

print("\n===== KB Google News =====")
for e in gn("KB부동산 주간 아파트 매매가격"):
    t=e.get("title",""); s=(e.get("summary","") or "")[:200]
    pcts=re.findall(r'[-+]?\d+\.\d+\s*%',t+" "+s); weeks=re.findall(r'\d+\s*주\s*(?:연속|째)',t+" "+s)
    print(f"\n제목: {t}\n요약: {s[:120]}\n수치: {pcts[:5]} | 주수: {weeks}")

print("\n===== 전세가율 =====")
for e in gn("서울 아파트 전세가율"):
    t=e.get("title",""); s=(e.get("summary","") or "")[:200]
    pcts=re.findall(r'[\d.]+\s*%',t+" "+s)
    print(f"\n제목: {t}\n수치: {pcts[:5]}")

print("\n===== 경매 낙찰률 =====")
for e in gn("아파트 경매 낙찰률 낙찰가율"):
    t=e.get("title",""); s=(e.get("summary","") or "")[:200]
    pcts=re.findall(r'[\d.]+\s*%',t+" "+s)
    print(f"\n제목: {t}\n수치: {pcts[:5]}")

print("\n===== 미분양 =====")
for e in gn("미분양 주택 국토교통부"):
    t=e.get("title",""); s=(e.get("summary","") or "")[:200]
    nums=re.findall(r'[\d,]+\s*(?:가구|호|만)',t+" "+s)
    print(f"\n제목: {t}\n수치: {nums[:5]}")

print("\n===== 수급지수 =====")
for e in gn("한국부동산원 매매수급지수"):
    t=e.get("title",""); s=(e.get("summary","") or "")[:200]
    nums=re.findall(r'\d{2,3}\.\d+',t+" "+s)
    print(f"\n제목: {t}\n수치: {nums[:5]}")

print("\n===== 주택가격전망지수 =====")
for e in gn("주택가격전망지수 한국은행"):
    t=e.get("title",""); s=(e.get("summary","") or "")[:200]
    nums=re.findall(r'\d{2,3}\.\d+',t+" "+s)
    print(f"\n제목: {t}\n수치: {nums[:5]}")

print("\n완료")
