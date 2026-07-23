import sys,io
if sys.stdout.encoding and sys.stdout.encoding.lower()!="utf-8":
    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8",errors="replace")
import feedparser,requests,re

H={"User-Agent":"Mozilla/5.0 Chrome/124.0.0.0 Safari/537.36","Accept-Language":"ko-KR,ko;q=0.9"}

def gn(q,n=5):
    url=f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=ko&gl=KR&ceid=KR:ko"
    feed=feedparser.parse(requests.get(url,headers=H,timeout=10).content)
    return [(e.get("title",""), (e.get("summary","") or "")[:200]) for e in feed.entries[:n]]

print("===거래량===")
for q in ["주택 매매 거래량 국토교통부","아파트 거래량 만건 전년"]:
    print(f"[{q}]")
    for t,s in gn(q):
        nums=re.findall(r'[\d,]+\s*(?:만\s*)?건',t+" "+s)
        print(f"  제목:{t}\n  수치:{nums[:4]}")

print("\n===미분양===")
for q in ["전국 미분양 주택 국토교통부","미분양 준공후 악성 가구"]:
    print(f"[{q}]")
    for t,s in gn(q):
        nums=re.findall(r'[\d,]+\s*(?:가구|호|만)',t+" "+s)
        print(f"  제목:{t}\n  수치:{nums[:4]}")

print("\n===부산===")
for q in ["부산 아파트 매매 전세 주간","부산 부동산 동향 상승"]:
    print(f"[{q}]")
    for t,s in gn(q):
        pcts=re.findall(r'[-+]?\d+\.?\d*\s*%',t+" "+s)
        print(f"  제목:{t}\n  수치:{pcts[:4]}")

print("\n===인허가===")
for q in ["주택 인허가 실적 국토교통부","주택인허가 전년대비 감소"]:
    print(f"[{q}]")
    for t,s in gn(q):
        nums=re.findall(r'[\d,]+\s*(?:호|가구|만)',t+" "+s)
        print(f"  제목:{t}\n  수치:{nums[:4]}")

print("\n===KB수급전망===")
for q in ["KB국민은행 매매가격전망지수","한국부동산원 매매수급지수 주간"]:
    print(f"[{q}]")
    for t,s in gn(q):
        nums=re.findall(r'\d{2,3}\.?\d*',t+" "+s)
        print(f"  제목:{t}\n  수치:{nums[:5]}")

print("\n===착공준공===")
for q in ["주택 착공량 준공량 국토교통부","아파트 착공 준공 전년대비"]:
    print(f"[{q}]")
    for t,s in gn(q):
        nums=re.findall(r'[\d,]+\s*(?:호|가구|만)',t+" "+s)
        pcts=re.findall(r'[-+]?\d+\.?\d*\s*%',t+" "+s)
        print(f"  제목:{t}\n  수치:{nums[:4]} 비율:{pcts[:3]}")

print("\n===KHAI===")
for q in ["주택금융공사 주택구입부담지수","K-HAI 주택구입부담"]:
    print(f"[{q}]")
    for t,s in gn(q):
        nums=re.findall(r'\d{2,3}\.?\d*',t+" "+s)
        print(f"  제목:{t}\n  수치:{nums[:5]}")

print("완료")
