import sys,io
if sys.stdout.encoding and sys.stdout.encoding.lower()!="utf-8":
    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8",errors="replace")
import feedparser,requests,re

H={"User-Agent":"Mozilla/5.0 Chrome/124.0.0.0 Safari/537.36","Accept-Language":"ko-KR,ko;q=0.9"}

def gn(q,n=5):
    url=f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=ko&gl=KR&ceid=KR:ko"
    feed=feedparser.parse(requests.get(url,headers=H,timeout=10).content)
    return [(e.get("title",""), (e.get("summary","") or "")[:300]) for e in feed.entries[:n]]

print("===거래량===")
for q in ["주택 매매 거래량 국토교통부","아파트 거래량 만건 전년"]:
    print(f"[{q}]")
    for t,s in gn(q):
        text=t+" "+s
        all_cnt=re.findall(r"[\d,]+\s*(?:만\s*)?건",text)
        man=re.findall(r"\d+(?:\.\d+)?\s*만\s*건",text)
        print(f"  제목:{t}")
        print(f"  요약:{s[:120]}")
        print(f"  건수치:{all_cnt[:5]} 만단위:{man[:3]}")

print("\n===미분양===")
for q in ["전국 미분양 주택 국토교통부","미분양 만가구 전년대비"]:
    print(f"[{q}]")
    for t,s in gn(q):
        text=t+" "+s
        nums=re.findall(r"[\d,]+\s*(?:만\s*)?(?:가구|호|세대)",text)
        man=re.findall(r"\d+(?:\.\d+)?\s*만\s*(?:가구|호)?",text)
        pcts=re.findall(r"[-+]?\d+\.?\d*\s*%",text)
        print(f"  제목:{t}")
        print(f"  요약:{s[:120]}")
        print(f"  수치:{nums[:4]} 만단위:{man[:3]} 퍼센트:{pcts[:3]}")

print("\n===착공량===")
for q in ["주택 착공량 실적 국토교통부","아파트 착공 전년대비"]:
    print(f"[{q}]")
    for t,s in gn(q):
        text=t+" "+s
        pcts=re.findall(r"[-+]?\d+\.?\d*\s*%",text)
        nums=re.findall(r"[\d,]+\s*(?:만\s*)?(?:가구|호)",text)
        print(f"  제목:{t}")
        print(f"  요약:{s[:120]}")
        print(f"  퍼센트:{pcts[:5]} 수치:{nums[:3]}")

print("\n===부산===")
for q in ["부산 아파트 매매 전세 주간","부산 부동산 동향 상승","부산 아파트 변동률"]:
    print(f"[{q}]")
    for t,s in gn(q):
        text=t+" "+s
        pcts=re.findall(r"[-+]?\d+\.?\d*\s*%",text)
        busan=re.findall(r"부산.{0,15}?([-+]?\d+\.?\d*)\s*%",text)
        print(f"  제목:{t}")
        print(f"  요약:{s[:120]}")
        print(f"  전체%:{pcts[:5]} 부산%:{busan[:3]}")

print("\n===KB수급전망===")
for q in ["KB국민은행 매매가격전망지수","한국부동산원 매매수급지수 주간"]:
    print(f"[{q}]")
    for t,s in gn(q):
        text=t+" "+s
        nums=re.findall(r"\d{2,3}\.?\d*",text)
        print(f"  제목:{t}")
        print(f"  요약:{s[:120]}")
        print(f"  수치:{nums[:8]}")

print("\n===준공량===")
for q in ["주택 준공량 입주 국토교통부","아파트 입주 물량 준공 전년"]:
    print(f"[{q}]")
    for t,s in gn(q):
        text=t+" "+s
        nums=re.findall(r"[\d,]+\s*(?:만\s*)?(?:가구|호|세대)",text)
        pcts=re.findall(r"[-+]?\d+\.?\d*\s*%",text)
        print(f"  제목:{t}")
        print(f"  요약:{s[:120]}")
        print(f"  수치:{nums[:4]} 퍼센트:{pcts[:4]}")

print("완료")
