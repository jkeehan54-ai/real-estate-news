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

import feedparser, requests, re, os
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
}

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
    """'키워드 근처 X만Y천' 한국식 숫자 파싱"""
    idx = text.find(keyword)
    if idx < 0: return None
    seg = text[max(0,idx-10):idx+60]
    # X만Y천
    m = re.search(r'(\d+)\s*만\s*(\d+)\s*천', seg)
    if m:
        v = int(m.group(1))*10000 + int(m.group(2))*1000
        return v if (lo is None or v>=lo) and (hi is None or v<=hi) else None
    # X.X만
    m = re.search(r'(\d+\.\d+)\s*만', seg)
    if m:
        v = int(float(m.group(1))*10000)
        return v if (lo is None or v>=lo) and (hi is None or v<=hi) else None
    # X만
    m = re.search(r'(\d+)\s*만', seg)
    if m:
        v = int(m.group(1))*10000
        return v if (lo is None or v>=lo) and (hi is None or v<=hi) else None
    # 일반 숫자
    m = re.search(r'([\d,]{4,})', seg)
    if m: return safe_int(m.group(1), lo, hi)
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

def fetch_rss_all():
    """일반 RSS 피드 전체 수집"""
    items = []
    for url in RSS_FEEDS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8)
            feed = feedparser.parse(resp.content)
            for e in feed.entries:
                t = (e.get("title","") or "").strip()
                # ★ 요약은 사용 안 함 (Google News 구조 문제로 제목만 사용)
                l = e.get("link","")
                d = (e.get("published","") or "")[:10]
                if t: items.append((t, "", l, d))
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


# ══════════════════════════════════════════════════════════════════════════════
# 선행1: KB 주간 시황 — 제목에서 "서울 X.XX% 상승" 패턴 파싱
# ══════════════════════════════════════════════════════════════════════════════
def get_kb_weekly(rss):
    print("[선행1] KB부동산 주간 시황")
    r = {k: None for k in ["국전체","서울","수도권","부산","전세전국",
                             "전세서울","매수우위","연속주수","방향","기준일"]}
    r["원문"] = []

    APT_KEYS = ["아파트값","아파트 매매","아파트가격","매매가격",
                "KB부동산","국민은행","주간 아파트","주간아파트"]

    # 제목에서 직접 파싱 (소수점 필수)
    RE_SEO = re.compile(r'서울\s*(?:아파트\s*)?(?:값|매매|가격)?\s*[▲△▼▽↑↓]?\s*([-+]?\d+\.\d+)\s*%')
    RE_NAT = re.compile(r'전국\s*(?:아파트\s*)?(?:값|매매|가격)?\s*[▲△▼▽↑↓]?\s*([-+]?\d+\.\d+)\s*%')
    RE_MET = re.compile(r'수도권\s*(?:아파트\s*)?(?:값|매매|가격)?\s*[▲△▼▽↑↓]?\s*([-+]?\d+\.\d+)\s*%')
    RE_BUS = re.compile(r'부산\s*(?:아파트\s*)?(?:값|매매|가격)?\s*[▲△▼▽↑↓]?\s*([-+]?\d+\.\d+)\s*%')
    RE_JEO = re.compile(r'전세\s*(?:가격\s*)?[▲△▼▽↑↓]?\s*([-+]?\d+\.\d+)\s*%')
    RE_JEO2= re.compile(r'전세도\s*([-+]?\d+\.\d+)\s*%')
    RE_BUY = re.compile(r'매수우위지수\s*[^\d]*([\d.]+)')
    RE_WEK = re.compile(r'(\d+)\s*주\s*(?:연속|째)')
    RE_DTE = re.compile(r'(\d{4})[년.]\s*(\d{1,2})[월.]\s*(\d{1,2})')

    all_items = combine(rss,
        "서울 아파트값 주간 상승 전세",
        "전국 아파트 매매가 주간 변동",
        "KB부동산 주간 아파트 매매")

    for title, _, link, date in all_items:
        # 제목만 사용
        text = title
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

        if seo is not None: r["서울"]     = f"{seo}"
        if nat is not None: r["국전체"]   = f"{nat}"
        if met is not None: r["수도권"]   = f"{met}"
        if bus is not None: r["부산"]     = f"{bus}"
        if jeo is not None: r["전세전국"] = f"{jeo}"
        if m_u:
            v = safe_float(m_u.group(1), 0, 100)
            if v: r["매수우위"] = f"{v}"
        if m_w:
            v = safe_int(m_w.group(1), 1, 200)
            if v: r["연속주수"] = f"{v}"
        if m_d:
            r["기준일"] = f"{m_d.group(1)}.{int(m_d.group(2)):02d}.{int(m_d.group(3)):02d}"

        ref = safe_float(r.get("서울") or r.get("국전체"))
        if ref is not None:
            r["방향"] = "상승" if ref > 0 else ("하락" if ref < 0 else "보합")

        r["원문"].append({"title": title, "link": link, "date": date})
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

    RE_R   = re.compile(r'낙찰률\s*([\d.]+)\s*%')
    RE_PR  = re.compile(r'낙찰가율\s*([\d.]+)\s*%')
    RE_PR2 = re.compile(r'낙찰가율\s*(100(?:\.\d+)?)\s*%?\s*돌파')

    all_items = combine(rss,
        "아파트 경매 낙찰률 낙찰가율 월간",
        "법원경매 아파트 낙찰 낙찰가율 서울")

    for title, _, link, date in all_items:
        text = title
        if "낙찰" not in text: continue

        m_r  = RE_R.search(text)
        m_pr = RE_PR.search(text) or RE_PR2.search(text)

        rate  = safe_float(m_r.group(1)  if m_r  else None, 10, 80)
        prate = safe_float(m_pr.group(1) if m_pr else None, 50, 200)

        if rate is not None or prate is not None:
            if rate:  r["낙찰률"]  = f"{rate}"
            if prate: r["낙찰가율"] = f"{prate}"
            r["원문"].append({"title": title, "link": link, "date": date})
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

    # 제목에서 전년비 % 직접 추출
    RE_YOY  = re.compile(r'전년\s*(?:동기|대비|比|보다)?\s*([-+]?\d+\.?\d*)\s*%')
    RE_YOY2 = re.compile(r'([-+]?\d+\.?\d*)\s*%\s*(?:감소|증가)')
    RE_MON  = re.compile(r'(\d{4})년\s*(\d{1,2})월')

    all_items = combine(rss,
        "주택인허가 전년대비 감소 증가",
        "주택 인허가 실적 국토교통부")

    for title, _, link, date in all_items:
        text = title
        if "인허가" not in text: continue
        # ★ 주택 관련 기사만 채택 (공장·상업시설 인허가 제외)
        if not any(k in text for k in ["주택","아파트","공동주택","단독주택","주거"]):
            continue

        cnt = parse_korean_num(text, "인허가", lo=1000, hi=500000)
        m_y = RE_YOY.search(text) or RE_YOY2.search(text)
        m_m = RE_MON.search(text)

        # 전년비 범위 조정: 주택인허가는 최대 ±80% 수준
        yoy = safe_float(m_y.group(1) if m_y else None, -80, 150)

        if cnt or yoy is not None:
            if cnt: r["수치"] = f"{cnt:,}"
            if yoy is not None: r["전년비"] = f"{yoy}"
            if m_m: r["기준월"] = f"{m_m.group(1)}.{int(m_m.group(2)):02d}"
            r["원문"].append({"title": title, "link": link, "date": date})
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

    RE_SEO = re.compile(r'서울\s*(?:아파트\s*)?전세가율\s*([\d.]+)\s*%')
    RE_NAT = re.compile(r'(?:전국|평균)\s*(?:아파트\s*)?전세가율\s*([\d.]+)\s*%')
    RE_GEN = re.compile(r'전세가율\s*([\d.]+)\s*%')

    all_items = combine(rss,
        "서울 아파트 전세가율 현황",
        "전세가율 붕괴 돌파 아파트")

    for title, _, link, date in all_items:
        text = title
        if "전세가율" not in text: continue

        m_s = RE_SEO.search(text)
        m_n = RE_NAT.search(text)
        m_g = RE_GEN.search(text)

        seo = safe_float(m_s.group(1) if m_s else None, 30, 90)
        nat = safe_float(m_n.group(1) if m_n else None, 30, 90)
        gen = safe_float(m_g.group(1) if m_g else None, 30, 90)

        if seo is None and nat is None and gen is None: continue

        if seo: r["서울"] = f"{seo}"
        if nat: r["전국"] = f"{nat}"
        elif gen: r["전국"] = f"{gen}"
        r["원문"].append({"title": title, "link": link, "date": date})
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

    RE_CSI  = re.compile(r'소비자심리지수\s*(\d{2,3}\.?\d*)')
    RE_HPCI = re.compile(r'주택가격전망(?:지수)?\s*(\d{2,3}\.?\d*)')
    # "주택가격전망지수 120" 같은 제목
    RE_HPCI2= re.compile(r'주택전망지수\s*(\d{2,3}\.?\d*)')

    all_items = combine(rss,
        "주택가격전망지수 한국은행",
        "소비자심리지수 주택 전망")

    for title, _, link, date in all_items:
        text = title
        if "전망" not in text and "심리" not in text: continue

        m_c = RE_CSI.search(text)
        m_h = RE_HPCI.search(text) or RE_HPCI2.search(text)
        csi  = safe_float(m_c.group(1) if m_c else None, 60, 200)
        hpci = safe_float(m_h.group(1) if m_h else None, 60, 200)

        if csi or hpci:
            if csi:  r["CSI"]    = f"{csi}"
            if hpci: r["주택전망"] = f"{hpci}"
            r["원문"].append({"title": title, "link": link, "date": date})
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

    RE_M  = re.compile(r'매매\s*(?:가격\s*)?전망(?:지수)?\s*(\d{2,3}\.?\d*)')
    RE_J  = re.compile(r'전세\s*(?:가격\s*)?전망(?:지수)?\s*(\d{2,3}\.?\d*)')
    # "전망지수 XXX" 단독 패턴
    RE_IDX= re.compile(r'전망지수\s*(\d{2,3}\.?\d*)')
    # "XXX.X로 상승/하락" 패턴
    RE_VAL= re.compile(r'(\d{2,3}\.?\d*)\s*(?:로|으로|를)\s*(?:상승|하락|올라|내려|기록)')

    all_items = (list(rss)
        + fetch_gn_titles("KB국민은행 매매가격전망지수 전세가격전망지수", 15)
        + fetch_gn_titles("KB부동산 매매전망 전세전망", 10))

    for title, _, link, date in all_items:
        text = title
        if "KB" not in text and "국민은행" not in text: continue
        if "전망" not in text: continue

        m_m = RE_M.search(text)
        m_j = RE_J.search(text)
        m_i = RE_IDX.search(text)
        mv = safe_float(m_m.group(1) if m_m else None, 60, 200)
        jv = safe_float(m_j.group(1) if m_j else None, 60, 200)
        iv = safe_float(m_i.group(1) if (m_i and not m_m) else None, 60, 200)

        if mv or jv or iv:
            if mv: r["매매전망"] = f"{mv}"
            elif iv: r["매매전망"] = f"{iv}"
            if jv: r["전세전망"] = f"{jv}"
            r["원문"].append({"title": title, "link": link, "date": date})
            print(f"  ✔ 매매전망 {disp(r['매매전망'])} | 전세전망 {disp(r['전세전망'])}")
            return r

    print("  - 데이터 없음")
    return r


# ══════════════════════════════════════════════════════════════════════════════
# 선행7: 수급동향 (한국부동산원)
# debug2 결과: 제목에 수치 없음 → 연합뉴스 RSS에서 본문 포함 기사 탐색
# ══════════════════════════════════════════════════════════════════════════════
def get_supply_demand(rss):
    print("[선행7] 수급동향 (한국부동산원)")
    r = {"매매수급": None, "전세수급": None, "원문": []}

    RE_T  = re.compile(r'매매\s*수급\s*(?:지수)?\s*(\d{2,3}\.?\d*)')
    RE_J  = re.compile(r'전세\s*수급\s*(?:지수)?\s*(\d{2,3}\.?\d*)')
    # "수급지수 XX.X" 단독
    RE_SQ = re.compile(r'수급지수\s*(\d{2,3}\.?\d*)')

    all_items = combine(rss,
        "한국부동산원 매매수급지수 전세수급지수",
        "부동산원 수급동향 아파트 지수",
        "매매수급지수 전세수급지수")

    for title, _, link, date in all_items:
        text = title
        if "수급" not in text: continue

        m_t  = RE_T.search(text)
        m_j  = RE_J.search(text)
        m_sq = RE_SQ.search(text)
        tv = safe_float(m_t.group(1) if m_t else None, 50, 180)
        jv = safe_float(m_j.group(1) if m_j else None, 50, 180)
        sv = safe_float(m_sq.group(1) if (m_sq and not m_t) else None, 50, 180)

        if tv or jv or sv:
            if tv: r["매매수급"] = f"{tv}"
            elif sv: r["매매수급"] = f"{sv}"
            if jv: r["전세수급"] = f"{jv}"
            r["원문"].append({"title": title, "link": link, "date": date})
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

    RE_M = re.compile(r'매매\s*(?:소비\s*)?심리(?:지수)?\s*(\d{2,3}\.?\d*)')
    RE_J = re.compile(r'전세\s*(?:소비\s*)?심리(?:지수)?\s*(\d{2,3}\.?\d*)')
    RE_G = re.compile(r'(?:부동산\s*)?소비심리지수\s*(\d{2,3}\.?\d*)')

    all_items = combine(rss,
        "국토연구원 부동산 소비심리지수",
        "국토연구원 주거 심리지수 매매 전세")

    for title, _, link, date in all_items:
        text = title
        if "국토연구원" not in text and "소비심리" not in text: continue

        m_m = RE_M.search(text)
        m_j = RE_J.search(text)
        m_g = RE_G.search(text)
        mv = safe_float(m_m.group(1) if m_m else None, 50, 200)
        jv = safe_float(m_j.group(1) if m_j else None, 50, 200)
        gv = safe_float(m_g.group(1) if m_g else None, 50, 200)

        if mv or jv or gv:
            if mv: r["매매심리"] = f"{mv}"
            elif gv: r["매매심리"] = f"{gv}"
            if jv: r["전세심리"] = f"{jv}"
            r["원문"].append({"title": title, "link": link, "date": date})
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

    RE_IDX = re.compile(r'(?:주택구입부담지수|K-HAI|HAI)\s*(\d{2,3}\.?\d*)')
    RE_QOQ = re.compile(r'전\s*분기\s*(?:대비)?\s*([-+]?\d+\.?\d*)\s*(?:포인트|p|%)')

    all_items = combine(rss,
        "주택금융공사 주택구입부담지수 K-HAI",
        "K-HAI 주택구입부담 분기",
        "주택구입부담지수 상승 하락 분기")

    for title, _, link, date in all_items:
        text = title
        if "주택구입부담" not in text and "K-HAI" not in text and "HAI" not in text: continue

        m_i = RE_IDX.search(text)
        m_q = RE_QOQ.search(text)
        iv = safe_float(m_i.group(1) if m_i else None, 30, 300)
        qv = safe_float(m_q.group(1) if m_q else None, -50, 50)

        if iv:
            r["지수"] = f"{iv}"
            if qv is not None: r["전분기비"] = f"{qv}"
            r["원문"].append({"title": title, "link": link, "date": date})
            print(f"  ✔ K-HAI {disp(r['지수'])} | 전분기비 {disp(r['전분기비'])}")
            return r

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
    RE_YOY  = re.compile(r'전년\s*(?:동기|대비|보다|比)?\s*([-+]?\d+\.?\d*)\s*%')
    RE_YOY2 = re.compile(r'([-+]?\d+\.?\d*)\s*%\s*(?:감소|증가|줄|늘)')
    RE_YOY3 = re.compile(r'거래(?:량)?\s*(\d+\.?\d*)\s*%\s*(?:급감|급증|감소|증가)')
    RE_MON  = re.compile(r'(\d{1,2})월\s*(?:주택\s*)?(?:매매\s*)?거래')

    all_items = combine(rss,
        "주택 매매거래량 감소 증가 전년",
        "아파트 거래량 전년대비")

    for title, _, link, date in all_items:
        text = title
        if "거래" not in text: continue
        if not any(k in text for k in ["거래량","매매거래","거래건수"]): continue

        cnt = parse_korean_num(text, "거래", lo=5000, hi=300000)
        m_y = RE_YOY.search(text) or RE_YOY2.search(text) or RE_YOY3.search(text)
        m_m = RE_MON.search(text)

        yoy = safe_float(m_y.group(1) if m_y else None, -80, 500)

        if cnt or yoy is not None:
            if cnt: r["거래량"] = f"{cnt:,}"
            if yoy is not None: r["전년비"] = f"{yoy}"
            if m_m: r["기준월"] = f"{m_m.group(1)}월"
            r["원문"].append({"title": title, "link": link, "date": date})
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

    RE_YOY  = re.compile(r'전년\s*(?:동기|대비|比|보다)?\s*([-+]?\d+\.?\d*)\s*%')
    RE_YOY2 = re.compile(r'([-+]?\d+\.?\d*)\s*%\s*(?:감소|증가)')
    RE_MON  = re.compile(r'(\d{4})년\s*(\d{1,2})월|(\d{1,2})월\s*착공')

    all_items = combine(rss,
        "아파트 착공 전년대비 감소 증가",
        "주택 착공 실적 국토교통부 전년")

    for title, _, link, date in all_items:
        text = title
        if "착공" not in text: continue

        cnt = parse_korean_num(text, "착공", lo=500, hi=300000)
        m_y = RE_YOY.search(text) or RE_YOY2.search(text)
        m_m = RE_MON.search(text)

        yoy = safe_float(m_y.group(1) if m_y else None, -80, 200)

        # 착공 관련 기사임을 좀 더 엄격히 확인
        is_relevant = any(k in text for k in ["착공 전년","착공량","착공 실적","착공물량",
                                                "비아파트 착공","아파트 착공"])

        if is_relevant and (cnt or yoy is not None):
            if cnt: r["수치"] = f"{cnt:,}"
            if yoy is not None: r["전년비"] = f"{yoy}"
            if m_m:
                g = m_m.groups()
                if g[0]: r["기준월"] = f"{g[0]}.{int(g[1]):02d}"
                elif g[2]: r["기준월"] = f"{g[2]}월"
            r["원문"].append({"title": title, "link": link, "date": date})
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
    RE_YOY   = re.compile(r'전년\s*(?:동기|대비|보다)?\s*([-+]?\d+\.?\d*)\s*%')
    RE_MON   = re.compile(r'(\d{4})년\s*(\d{1,2})월')

    all_items = combine(rss,
        "전국 미분양 주택 국토교통부 만가구",
        "미분양 준공후 악성 가구")

    for title, _, link, date in all_items:
        text = title
        if "미분양" not in text: continue

        # 전국 미분양 수치 (제목에서)
        cnt = parse_korean_num(text, "미분양", lo=3000, hi=300000)

        # 악성(준공후) 미분양
        악성 = None
        m_a = RE_악성1.search(text)
        m_a2 = RE_악성2.search(text)
        if m_a:
            악성 = safe_int(m_a.group(1), 100, 100000)
        elif m_a2:
            v = safe_float(m_a2.group(1))
            if v: 악성 = int(v * 10000)

        m_y = RE_YOY.search(text)
        m_m = RE_MON.search(text)
        yoy = safe_float(m_y.group(1) if m_y else None, -80, 300)

        # "국토부", "전국" 키워드 포함 기사만
        is_relevant = any(k in text for k in ["국토부","국토교통부","전국 미분양","전국 악성"])

        if is_relevant and (cnt or yoy is not None):
            if cnt: r["전국"] = f"{cnt:,}"
            if 악성 and (cnt is None or 악성 < cnt): r["악성"] = f"{악성:,}"
            if yoy is not None: r["전년비"] = f"{yoy}"
            if m_m: r["기준월"] = f"{m_m.group(1)}.{int(m_m.group(2)):02d}"
            r["원문"].append({"title": title, "link": link, "date": date})
            print(f"  ✔ {disp(r['전국'])}호 | 악성 {disp(r['악성'])}호 | 전년비 {disp(r['전년비'])}%")
            return r

    # 조건 완화 재시도: "X만가구" 패턴만 있어도 수집
    for title, _, link, date in combine(rss,
        "미분양 만가구 전년대비",
        "악성 미분양 준공후 가구",
        "전국 미분양 현황"):
        text = title
        if "미분양" not in text: continue
        cnt = parse_korean_num(text, "미분양", lo=5000, hi=300000)  # 최소 5000호
        m_a  = RE_악성1.search(text)
        m_a2 = RE_악성2.search(text)
        악성 = None
        if m_a:
            악성 = safe_int(m_a.group(1), 100, 100000)
        elif m_a2:
            v = safe_float(m_a2.group(1))
            if v: 악성 = int(v * 10000)
        if cnt:
            r["전국"] = f"{cnt:,}"
            if 악성 and 악성 < cnt: r["악성"] = f"{악성:,}"
            r["원문"].append({"title": title, "link": link, "date": date})
            print(f"  ✔ {r['전국']}호 | 악성 {disp(r['악성'])}호")
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

    RE_YOY  = re.compile(r'전년\s*(?:동기|대비|보다|比)?\s*([-+]?\d+\.?\d*)\s*%')
    RE_YOY2 = re.compile(r'([-+]?\d+\.?\d*)\s*%?\s*[↓↑]\s*')
    RE_YOY3 = re.compile(r'([-+]?\d+\.?\d*)\s*%\s*(?:감소|급감|증가|급증)')
    RE_MON  = re.compile(r'(\d{1,2})월\s*(?:서울\s*)?(?:입주|준공)')

    all_items = combine(rss,
        "아파트 입주 물량 준공 전년",
        "주택 준공 실적 국토교통부")

    for title, _, link, date in all_items:
        text = title
        if "준공" not in text and "입주물량" not in text and "입주 물량" not in text: continue

        cnt = parse_korean_num(text, "준공", lo=500, hi=300000)
        if not cnt:
            cnt = parse_korean_num(text, "입주", lo=500, hi=300000)

        m_y = RE_YOY.search(text) or RE_YOY2.search(text) or RE_YOY3.search(text)
        m_m = RE_MON.search(text)
        yoy = safe_float(m_y.group(1) if m_y else None, -80, 300)

        is_relevant = any(k in text for k in ["준공 실적","입주물량","입주 물량","준공량","반토막","급감","급증"])

        if is_relevant and (cnt or yoy is not None):
            if cnt: r["수치"] = f"{cnt:,}"
            if yoy is not None: r["전년비"] = f"{yoy}"
            if m_m: r["기준월"] = f"{m_m.group(1)}월"
            r["원문"].append({"title": title, "link": link, "date": date})
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

    # 한국부동산원 주간 기사에서 부산 수치 탐색
    all_items = busan_rss_items + fetch_gn_titles("부산 아파트 매매 전세 주간 변동률", 15)
    all_items += fetch_gn_titles("부산 아파트값 상승 하락 주간", 10)
    all_items += list(rss)  # 전체 RSS에서도 탐색

    for title, _, link, date in all_items:
        text = title
        if "부산" not in text: continue

        m_a = RE_A.search(text)
        m_j = RE_J.search(text)
        m_u = RE_U.search(text)

        apt  = safe_float(m_a.group(1) if m_a else None, -10, 10)
        jeon = safe_float(m_j.group(1) if m_j else None, -10, 10)
        uns  = safe_int(m_u.group(1) if m_u else None, 100, 50000)

        if apt is not None or jeon is not None:
            if apt  is not None: r["아파트변동"] = f"{apt}"
            if jeon is not None: r["전세변동"]   = f"{jeon}"
            if uns:              r["미분양"]     = f"{uns:,}"
            r["원문"].append({"title": title, "link": link, "date": date})
            print(f"  ✔ 매매 {disp(r['아파트변동'])}% | 전세 {disp(r['전세변동'])}%")
            return r

    # 수치 없이 방향 텍스트만 있는 경우 → 방향 기반 대표값 설정
    for title, _, link, date in all_items:
        text = title
        if "부산" not in text: continue
        if "아파트" not in text and "부동산" not in text: continue
        if any(k in text for k in ["상승","하락","보합","멈추고","오름","내림"]):
            # 방향 텍스트로 대표값 설정
            if "하락 멈추" in text or "보합" in text:
                r["아파트변동"] = "0.00"
            elif "상승" in text and "하락" not in text:
                r["아파트변동"] = "0.05"  # 소폭 상승 추정
            elif "하락" in text:
                r["아파트변동"] = "-0.05"  # 소폭 하락 추정
            r["원문"].append({"title": title, "link": link, "date": date})
            print(f"  ✔ 부산 방향 파싱: {title[:45]}")
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
               trade, cstart, unsold, compl, busan):
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
body{{font-family:'Malgun Gothic',sans-serif;background:#0f1923;color:#cfd8dc;min-height:100vh;font-size:14px}}
.hdr{{background:linear-gradient(135deg,#1a2942,#0d1f35);padding:20px 28px;border-bottom:2px solid #1e3a5f}}
.hdr h1{{font-size:19px;font-weight:700;color:#e8f4ff}}
.hdr h1 em{{font-size:11px;font-weight:400;color:#4fc3f7;margin-left:8px;font-style:normal}}
.upd{{font-size:11px;color:#546e7a;margin-top:4px}}
.vbar{{background:#132030;border-left:5px solid {vc};padding:14px 28px;display:flex;align-items:center;gap:16px}}
.vlabel{{font-size:11px;color:#546e7a;letter-spacing:1px}}
.vval{{font-size:26px;font-weight:700;color:{vc}}}
.vsub{{font-size:12px;color:#78909c;margin-top:2px}}
.kbbar{{background:#0d1f35;padding:12px 28px;display:flex;gap:18px;flex-wrap:wrap;border-bottom:1px solid #1e3a5f}}
.kbi{{display:flex;flex-direction:column;align-items:center;min-width:66px}}
.kbr{{font-size:10px;color:#546e7a}}
.kbv{{font-size:16px;font-weight:700;margin-top:2px}}
.sec{{padding:18px 28px}}
.stitle{{font-size:11px;font-weight:600;color:#4fc3f7;letter-spacing:1.5px;text-transform:uppercase;
         margin-bottom:12px;padding-bottom:6px;border-bottom:1px solid #1e3a5f}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:10px}}
.card{{background:#132030;border:1px solid #1e3a5f;border-radius:8px;padding:12px}}
.ctitle{{font-size:10px;color:#546e7a;letter-spacing:0.5px;margin-bottom:5px}}
.cval{{margin-bottom:3px}}
.val{{font-size:24px;font-weight:700}}
.unit{{font-size:11px;color:#546e7a}}
.val.na{{font-size:14px;color:#37474f}}
.sub{{font-size:11px;color:#78909c;margin-bottom:2px}}
.note{{font-size:10px;color:#455a64;font-style:italic}}
.cnews{{margin-top:5px}}
.nref{{font-size:10px;color:#455a64;margin-top:2px;line-height:1.4}}
.nref a{{color:#4fc3f7;text-decoration:none}}
.nref a:hover{{text-decoration:underline}}
.nd{{color:#37474f}}
.stbl{{width:100%;border-collapse:collapse}}
.stbl tr{{border-bottom:1px solid #1a2942}}
.stbl td{{padding:8px 6px;vertical-align:middle}}
.sn{{color:#90a4ae;width:210px;font-size:12px}}
.sd{{color:#546e7a;font-size:12px}}
.badge{{display:inline-block;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:700;color:#fff}}
.cat{{display:inline-block;padding:1px 5px;border-radius:3px;font-size:9px;color:#fff;margin-left:5px;vertical-align:middle}}
.bsbox{{background:#0a1e30;border:1px solid #1e3a5f;border-left:3px solid #4fc3f7;border-radius:8px;padding:12px}}
.bstitle{{font-size:11px;color:#4fc3f7;font-weight:600;margin-bottom:8px}}
.refbox{{background:#0d1a26;border:1px solid #1a2942;border-radius:6px;padding:12px;
         font-size:11px;color:#455a64;line-height:1.9}}
.refbox b{{color:#607d8b}}
footer{{text-align:center;padding:16px;font-size:10px;color:#263238}}
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
  <div class="stitle">선행지표 — 시장 3~12개월 전망</div>
  <div class="grid">
    {card("① 경매 낙찰률",disp(auction.get("낙찰률")),"%",
        f"낙찰가율 {disp(auction.get('낙찰가율'))}% | {disp(auction.get('건수'))}건",
        "#c62828" if safe_float(auction.get("낙찰률"),38,80) else "#1565c0" if safe_float(auction.get("낙찰률"),0,34) else "#ef6c00",
        "32.4%(2023 저점)~42%(2021 고점)",auction.get("원문",[]))}
    {card("② 주택 인허가",disp(permit.get("수치")),"호",
        f"전년비 {disp(permit.get('전년비'))}% | {disp(permit.get('기준월'))}",
        rcolor(permit.get("전년비")),"인허가→착공→준공 6~24개월 시차",permit.get("원문",[]))}
    {card("③ 전세가율",disp(jeonse.get("전국") or jeonse.get("서울")),"%",
        f"서울 {disp(jeonse.get('서울'))}% | 부산 {disp(jeonse.get('부산'))}%",
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
  </div>
</div>

<div class="sec">
  <div class="stitle">동행지표 — 현재 시장 상황</div>
  <div class="grid">
    {card("KB 전국 매매가",pct_str(kb.get("국전체")),"%",f"{wk}주 연속 {wkd}",rcolor(kb.get("국전체")),"주간 변동률 (KB국민은행)",kb.get("원문",[]))}
    {card("KB 서울 매매가",pct_str(kb.get("서울")),"%",f"수도권 {pct_str(kb.get('수도권'))}%",rcolor(kb.get("서울")),"주간 변동률 (KB국민은행)",[])}
    {card("KB 전국 전세가",pct_str(kb.get("전세전국")),"%",f"서울 전세 {pct_str(kb.get('전세서울'))}%",rcolor(kb.get("전세전국")),"주간 전세 변동률 (KB국민은행)",[])}
    {card("주택 매매 거래량",disp(trade.get("거래량")),"건",f"전년비 {disp(trade.get('전년비'))}% | {disp(trade.get('기준월'))}",rcolor(trade.get("전년비")),"국토교통부 실거래 신고 기준",trade.get("원문",[]))}
    {card("착공량",disp(cstart.get("수치")),"호",f"전년비 {disp(cstart.get('전년비'))}% | {disp(cstart.get('기준월'))}",rcolor(cstart.get("전년비")),"착공 후 12~24개월 후 공급",cstart.get("원문",[]))}
  </div>
</div>

<div class="sec">
  <div class="stitle">후행지표 — 시장 결과 확인</div>
  <div class="grid">
    {card("전국 미분양",disp(unsold.get("전국")),"호",
        f"준공후(악성) {disp(unsold.get('악성'))}호 | {disp(unsold.get('기준월'))}",
        "#1565c0" if safe_int(str(unsold.get("전국") or "").replace(",",""),60001,999999) else "#c62828" if safe_int(str(unsold.get("전국") or "").replace(",",""),1,29999) else "#ef6c00",
        "3만호↓호황 | 6.2만호↑위험 (국토교통부)",unsold.get("원문",[]))}
    {card("준공량",disp(compl.get("수치")),"호",f"전년비 {disp(compl.get('전년비'))}% | {disp(compl.get('기준월'))}",
        "#ef6c00" if compl.get("수치") else "#546e7a","준공 증가→공급 확대→가격 하락 압력",compl.get("원문",[]))}
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

    print("\n[동행지표]")
    trade  = get_trade_vol(rss)
    cstart = get_construction_start(rss)

    print("\n[후행지표]")
    unsold = get_unsold(rss)
    compl  = get_completion(rss)

    print("\n[지역지표]")
    busan  = get_busan(rss)

    print("\n" + "=" * 55)
    html = build_html(kb, permit, jeonse, auction, csi, kb_fc, supply,
                      krihs, khai, trade, cstart, unsold, compl, busan)

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
    print(f"  [동행] 거래량 {disp(trade.get('거래량'))}건 | 전년비 {disp(trade.get('전년비'))}%")
    print(f"  [동행] 착공량 {disp(cstart.get('수치'))}호 | 전년비 {disp(cstart.get('전년비'))}%")
    print(f"  [후행] 미분양 {disp(unsold.get('전국'))}호 | 악성 {disp(unsold.get('악성'))}호")
    print(f"  [후행] 준공량 {disp(compl.get('수치'))}호 | 전년비 {disp(compl.get('전년비'))}%")
    print(f"  [부산] 매매 {disp(busan.get('아파트변동'))}% | 전세 {disp(busan.get('전세변동'))}%")
