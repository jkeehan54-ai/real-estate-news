import feedparser
from datetime import datetime
from difflib import SequenceMatcher
import re

# 13개 매체 고정 리스트
SOURCES = {
    "조선일보": "https://www.chosun.com/economy/real_estate/",
    "중앙일보": "https://www.joongang.co.kr/realestate",
    "동아일보": "https://www.donga.com/news/Economy/Realestate",
    "한겨레": "https://www.hani.co.kr/arti/economy/property/",
    "매일경제": "https://www.mk.co.kr/news/realestate/",
    "한국경제": "https://www.hankyung.com/realestate",
    "부산일보": "https://www.busan.com/economy/",
    "국제신문": "http://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200",
    "네이버부동산": "https://land.naver.com/news/",
    "한국부동산원": "https://www.reb.or.kr/reb/main.do",
    "KB부동산": "https://kbland.kr/today",
    "머니투데이": "https://news.mt.co.kr/estate/",
    "연합뉴스": "https://www.yna.co.kr/economy/real-estate/"
}

# 의미 없는 불용어 (중복 판단 시 제외)
STOPWORDS = {
    "은", "는", "이", "가", "을", "를", "의", "에", "도", "와", "과",
    "하고", "으로", "로", "에서", "까지", "부터", "이다", "합니다",
    "입니다", "했다", "한다", "됩니다", "됐다", "및", "등", "것",
    # 너무 범용적인 단어 (단독으로는 동일 기사 판단 불가)
    "안", "돼", "안돼", "반드시", "이제", "탈출", "공화국",
    "이라고", "라며", "했으며", "라고", "하며",
}

def normalize_title(title):
    """제목 정규화: 매체명·태그·날짜·특수문자 제거"""
    # 매체명 구분자 제거 (예: "제목 - 연합뉴스")
    title = re.split(r'\s[-|]\s', title)[0].strip()
    # [속보] [李정부 1년①] 같은 앞부분 태그 제거
    title = re.sub(r'^\[.*?\]\s*', '', title)
    # 날짜 형식 제거
    title = re.sub(r'\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}', '', title)
    # ★ 핵심 수정: 특수문자를 공백으로 치환 (제거하면 단어가 붙어버림)
    title = re.sub(r'[^\w\s]', ' ', title)
    # 단독 한자 1글자 제거 (李, 日 등 약칭)
    title = re.sub(r'(?<!\w)[一-龥](?!\w)', '', title)
    # 연속 공백 정리
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def title_to_keywords(title):
    """불용어 제거 후 2글자 이상 핵심 키워드 집합 반환"""
    words = title.split()
    return {w for w in words if w not in STOPWORDS and len(w) >= 2}

def is_duplicate(new_title, seen_titles, sim_threshold=0.65, keyword_threshold=0.45):
    """
    세 가지 기준으로 중복 판단:
    1. 정규화 후 완전 일치
    2. SequenceMatcher 문자열 유사도 65% 이상
    3. 핵심 키워드 자카드 유사도 45% 이상
    """
    norm_new = normalize_title(new_title)
    kw_new = title_to_keywords(norm_new)

    for seen_title in seen_titles:
        norm_seen = normalize_title(seen_title)

        # 1. 완전 일치
        if norm_new == norm_seen:
            return True

        # 2. 문자열 유사도
        if SequenceMatcher(None, norm_new, norm_seen).ratio() >= sim_threshold:
            return True

        # 3. 키워드 자카드 유사도
        kw_seen = title_to_keywords(norm_seen)
        if kw_new and kw_seen:
            union = len(kw_new | kw_seen)
            if union > 0 and len(kw_new & kw_seen) / union >= keyword_threshold:
                return True

    return False

def get_clean_news():
    results = {"청약": [], "재건축": [], "세제": [], "정책": [], "시장동향": []}
    seen_titles = []  # 실제 제목 목록 (유사도 비교에 원문 필요)

    queries = [
        "부동산 분양 청약",
        "아파트 재건축 재개발",
        "부동산 세금 종부세",
        "부동산 대출 정책",
        "부동산 시장 동향"
    ]

    for q in queries:
        feed = feedparser.parse(
            f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
        )
        for entry in feed.entries:
            raw_title = entry.title
            title = normalize_title(raw_title)

            if not title:
                continue

            if is_duplicate(raw_title, seen_titles):
                continue

            # 카테고리 분류
            t = title.lower()
            cat = "시장동향"
            if any(k in t for k in ["분양", "청약"]):
                cat = "청약"
            elif any(k in t for k in ["재건축", "재개발"]):
                cat = "재건축"
            elif any(k in t for k in ["세금", "종부세", "취득세"]):
                cat = "세제"
            elif any(k in t for k in ["정부", "대출", "금리", "정책"]):
                cat = "정책"

            if len(results[cat]) < 10:
                src = (entry.source.title
                       if hasattr(entry, 'source') and hasattr(entry.source, 'title')
                       else "뉴스")
                results[cat].append({
                    "title": title,
                    "link": entry.link,
                    "src": src
                })
                seen_titles.append(raw_title)  # 원문 기준으로 비교

    return results

data = get_clean_news()

# HTML 출력
html = "<h1>🏠 부동산 뉴스 브리핑</h1>\n"
html += " | ".join([
    f'<a href="{url}" target="_blank">{name}</a>'
    for name, url in SOURCES.items()
])
html += "\n<h2>오늘의 핵심 브리핑</h2>"
html += "<p>전국 아파트 매매가격 0.05% 상승, 38주 연속 상승세 유지. 매수우위지수는 62.9%로 매도자 우위입니다.</p>"

for cat, news_list in data.items():
    html += f"<h2>[{cat}]</h2>"
    if news_list:
        html += "".join([
            f"<p>{n['title']} | {n['src']} - <a href='{n['link']}' target='_blank'>[바로가기]</a></p>"
            for n in news_list
        ])
    else:
        html += "<p>관련 뉴스 없음</p>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("완료: index.html 생성됨")
total = sum(len(v) for v in data.values())
print(f"총 수집 뉴스: {total}건")
for cat, news_list in data.items():
    print(f"  {cat}: {len(news_list)}건")
