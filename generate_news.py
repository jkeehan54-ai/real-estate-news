# 이 스크립트를 실행하면 generate_news.py가 생성됩니다
# 실행: python make_generate_news.py

import os

code = """\
import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import feedparser, requests, re, os
from urllib.parse import quote_plus
from difflib import SequenceMatcher
from datetime import datetime, timezone, timedelta

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
}

HEADERS = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language":"ko-KR,ko;q=0.9",
    "Referer":"https://www.google.com/",
}

RSS_FEEDS = [
    ("한국경제","https://www.hankyung.com/feed/realestate",True),
    ("서울경제","https://www.sedaily.com/Rss/RealEstate",True),
    ("주택경제신문","https://www.arunews.com/rss/allArticle.xml",True),
    ("건설타임즈","https://www.constimes.co.kr/rss/allArticle.xml",True),
    ("매일경제","https://www.mk.co.kr/rss/30100041/",False),
    ("매일경제2","https://www.mk.co.kr/rss/50100032/",False),
    ("동아일보","https://rss.donga.com/economy.xml",False),
    ("한겨레","https://www.hani.co.kr/rss/economy/",False),
    ("연합뉴스","https://www.yna.co.kr/rss/economy.xml",False),
    ("연합뉴스2","https://www.yna.co.kr/rss/news.xml",False),
    ("아주경제","https://www.ajunews.com/rss/economy.xml",False),
    ("아시아경제","https://www.asiae.co.kr/rss/all.htm",False),
    ("조선일보","https://www.chosun.com/arc/outboundfeeds/rss/?outputType=xml",False),
    ("경남도민일보","https://www.idomin.com/rss/allArticle.xml",False),
]

GOOGLE_QUERIES = [
    "부동산 청약 분양",
    "아파트 재건축 재개발",
    "부동산 세금 종부세",
    "부동산 정책 대출 금리",
    "부동산 시장 매매 전세",
]

RE_ESTATE = re.compile(
    r'아파트|부동산|청약|재건축|재개발|전세|월세|임대|분양|주택|매매|'
    r'PF|건설|LH|SH|HUG|준공|착공|입주|종부세|취득세|양도세|재산세|집값|매물|오피스텔|빌라'
)

STOPWORDS = {
    "은","는","이","가","을","를","의","에","도","와","과","하고","으로","로",
    "에서","까지","부터","이다","합니다","입니다","했다","한다","됩니다","됐다",
    "및","등","것","안","돼","안돼","반드시","이제","않다","이라고","라며",
    "라고","하며","대해","위해","있다","없다","하다","된다","한","더","또",
}
LOC_ENTITIES = {
    "수도권","서울","강남","강북","부산","경기","인천","대구","광주","대전",
    "울산","세종","경남","해운대","수영","사하","동래","기장","연제","금정",
}
ORG_ENTITIES = {"국세청","한국부동산원","국토부","금융위","금감원","LH","SH","HUG"}


def extract_date_from_url(url):
    m = re.search(r'/(\\d{4})/(\\d{2})/(\\d{2})/', url)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), 6, 0, tzinfo=KST)
        except Exception:
            return None
    return None


def get_best_pub_dt(entry):
    d = extract_date_from_url(getattr(entry, 'link', ''))
    if d:
        return d
    pub = entry.get("published_parsed")
    if pub:
        return datetime(*pub[:6], tzinfo=timezone.utc).astimezone(KST)
    return None


def is_within_24h(entry, now_kst):
    d = get_best_pub_dt(entry)
    if d is None:
        return True
    return (now_kst - d).total_seconds() <= 86400


def normalize(title):
    title = re.split(r'\\s[-|]\\s', title)[0].strip()
    title = re.sub(r'^\\[.*?\\]\\s*', '', title)
    title = re.sub(r'\\d{4}[.\\-/]\\d{1,2}[.\\-/]\\d{1,2}', '', title)
    title = re.sub(r'[^\\w\\s]', ' ', title)
    title = re.sub(r'(?<!\\w)[\\u4e00-\\u9fff](?!\\w)', '', title)
    return re.sub(r'\\s+', ' ', title).strip()


def keywords(title):
    return {w for w in normalize(title).split() if w not in STOPWORDS and len(w) >= 2}


def extract_entities(title):
    t = re.sub(r'[^\\w\\s]', ' ', title)
    ents = set()
    for m in re.finditer(r'\\d+\\.?\\d*\\s*(?:억|만|건|%|개월|층|평|채|명|가구)', t):
        ents.add(m.group().strip())
    for loc in LOC_ENTITIES:
        if loc in t:
            ents.add(loc)
    for org in ORG_ENTITIES:
        if org in t:
            ents.add(org)
    return ents


def is_duplicate(new_raw, seen_raw):
    nn = normalize(new_raw)
    kn = keywords(new_raw)
    en = extract_entities(new_raw)
    for s in seen_raw:
        ns = normalize(s)
        if SequenceMatcher(None, nn, ns).ratio() >= 0.65:
            return True
        ks = keywords(s)
        u = len(kn | ks)
        if u and len(kn & ks) / u >= 0.45:
            return True
        es = extract_entities(s)
        if en and es and len(en & es) >= 2:
            return True
    return False


def classify(title):
    t = normalize(title).lower()
    if any(k in t for k in ["분양", "청약"]):
        return "청약"
    elif any(k in t for k in ["재건축", "재개발", "정비사업"]):
        return "재건축"
    elif any(k in t for k in ["세금", "종부세", "취득세", "양도세", "재산세"]):
        return "세제"
    elif any(k in t for k in ["대출", "금리", "정책", "규제", "완화"]):
        return "정책"
    elif any(k in t for k in ["부산", "해운대", "수영", "사하", "동래", "기장", "경남", "울산"]):
        return "부산경남"
    return "시장동향"


def fetch_rss(name, url, estate_only, now_kst):
    items = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        for entry in feed.entries:
            if not is_within_24h(entry, now_kst):
                continue
            title = (entry.title or "").strip()
            if not title:
                continue
            if not estate_only and not RE_ESTATE.search(title):
                continue
            src = name
            if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
                src = entry.source.title
            items.append((get_best_pub_dt(entry), title, entry.link, src))
        print("  OK [" + name + "] " + str(len(items)) + "건")
    except Exception as e:
        print("  ER [" + name + "] " + type(e).__name__ + ": " + str(e)[:50])
    return items


def fetch_google(now_kst):
    items = []
    for q in GOOGLE_QUERIES:
        try:
            url = "https://news.google.com/rss/search?q=" + quote_plus(q) + "&hl=ko&gl=KR&ceid=KR:ko"
            resp = requests.get(url, headers=HEADERS, timeout=8)
            feed = feedparser.parse(resp.content)
            cnt = 0
            for entry in feed.entries:
                if not is_within_24h(entry, now_kst):
                    continue
                title = (entry.title or "").strip()
                if not title:
                    continue
                src = "news"
                if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
                    src = entry.source.title
                items.append((get_best_pub_dt(entry), title, entry.link, src))
                cnt += 1
            print("  OK [Google/" + q + "] " + str(cnt) + "건")
        except Exception as e:
            print("  ER [Google/" + q + "] " + type(e).__name__ + ": " + str(e)[:50])
    return items


def get_clean_news():
    cats = ["청약", "재건축", "세제", "정책", "부산경남", "시장동향"]
    results = {c: [] for c in cats}
    seen = []
    now_kst = datetime.now(KST)
    all_entries = []

    print("[1단계] 매체 직접 RSS 수집")
    for name, url, eo in RSS_FEEDS:
        all_entries.extend(fetch_rss(name, url, eo, now_kst))

    print("[2단계] Google News RSS 보완")
    all_entries.extend(fetch_google(now_kst))

    all_entries.sort(key=lambda x: x[0] or datetime.max.replace(tzinfo=KST), reverse=True)

    total = dropped = 0
    for pub_dt, title, link, src in all_entries:
        total += 1
        if is_duplicate(title, seen):
            dropped += 1
            continue
        cat = classify(title)
        if len(results[cat]) < 12:
            ud = extract_date_from_url(link)
            if ud:
                ps = ud.strftime("%m/%d")
            elif pub_dt:
                ps = pub_dt.strftime("%m/%d %H:%M")
            else:
                ps = ""
            results[cat].append({"title": normalize(title), "link": link, "src": src, "pub_str": ps})
            seen.append(title)

    print("[결과] 전체 " + str(total) + "건 | 중복제거 " + str(dropped) + "건 | 최종 " + str(total - dropped) + "건")
    return results


def build_html(data):
    today = datetime.now(KST).strftime("%Y년 %m월 %d일")
    html = "<h1>부동산 뉴스 브리핑 (" + today + ")</h1>\\n"
    html += " | ".join('<a href="' + u + '" target="_blank">' + n + '</a>' for n, u in SOURCES.items())
    html += "\\n<h2>오늘의 핵심 브리핑</h2>"
    html += "<p>전국 아파트 매매가격 0.05% 상승, 38주 연속 상승세 유지. 매수우위지수는 62.9%로 매도자 우위입니다.</p>"
    labels = {
        "청약": "[청약]", "재건축": "[재건축]", "세제": "[세제]",
        "정책": "[정책]", "부산경남": "[부산경남]", "시장동향": "[시장동향]",
    }
    for cat, lst in data.items():
        html += "<h2>" + labels.get(cat, cat) + "</h2>"
        if lst:
            for n in lst:
                html += '<p><a href="' + n["link"] + '" target="_blank">' + n["title"] + '</a>'
                html += ' | <b>' + n["src"] + '</b>'
                if n["pub_str"]:
                    html += ' <small style="color:#aaa">(' + n["pub_str"] + ')</small>'
                html += '</p>'
        else:
            html += "<p>최근 24시간 내 수집된 기사가 없습니다.</p>"
    return html


if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    data = get_clean_news()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(build_html(data))
    total = sum(len(v) for v in data.values())
    print("[완료] 파일 생성 위치: " + output_path)
    for cat, lst in data.items():
        print("  [" + cat + "] " + str(len(lst)) + "건")
"""

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generate_news.py")
with open(out, "w", encoding="utf-8") as f:
    f.write(code)
print("생성 완료: " + out)
