# html_builder.py

"""
modules/html_builder.py

BRN HTML 생성기
"""

from collections import defaultdict
from datetime import datetime
from html import escape

from .templates import (
    html_header,
    html_footer,
    section_header,
    section_footer,
)

###############################################################################
# 출력 순서
###############################################################################

CATEGORY_ORDER = [
    "정책",
    "시장동향",
    "청약",
    "공급개발",
    "재건축",
    "세제",
    "부산경남",
]

###############################################################################
# 안전하게 문자열 가져오기
###############################################################################

def safe(value):

    if value is None:
        return ""

    return escape(str(value))


###############################################################################
# 기사 한 줄
###############################################################################

def build_news_item(item, no):

    title = safe(item.get("title"))
    link = item.get("link", "")
    source = safe(item.get("source"))

    summary = safe(item.get("summary"))

    html = []

    html.append("<div class='news-item'>")

    html.append("<div class='news-title'>")

    html.append(
        f"<span class='news-no'>{no}.</span> "
        f"<a href='{link}' "
        f"target='_blank' "
        f"rel='noopener noreferrer'>"
        f"{title}</a>"
    )

    html.append("</div>")

    html.append(
        f"<div class='news-meta'>"
        f"<span class='source'>{source}</span>"
        f"</div>"
    )

    if summary:

        html.append(
            f"<div class='news-summary'>"
            f"{summary}"
            f"</div>"
        )

    html.append("</div>")

    return "\n".join(html)


###############################################################################
# BRN 카드
###############################################################################

def build_brn(brn):

    if not brn:
        return ""

    summary = safe(brn.get("summary", ""))

    dashboard = brn.get("dashboard", {})
    signals = brn.get("signals", {})
    forecast = brn.get("forecast", {})

    html = []

    html.append("<div class='summary'>")
    html.append("<h2>📊 BRN 시장 브리핑</h2>")

    if summary:
        html.append(f"<p>{summary}</p>")

    ###################################################################
    # Dashboard
    ###################################################################

    if isinstance(dashboard, dict) and dashboard:

        labels = {
            "nation": "전국",
            "seoul": "서울",
            "busan": "부산",
            "buyer": "매수우위",
            "seller": "매도우위",
            "weeks": "연속주수",
            "trend": "추세",
        }

        html.append("<table>")
        html.append("<tr><th>항목</th><th>값</th></tr>")

        for key in (
            "nation",
            "seoul",
            "busan",
            "buyer",
            "seller",
            "weeks",
            "trend",
        ):

            if key in dashboard:

                html.append(
                    f"<tr>"
                    f"<td>{labels[key]}</td>"
                    f"<td>{safe(dashboard[key])}</td>"
                    f"</tr>"
                )

        html.append("</table>")

    ###################################################################
    # Signals
    ###################################################################

    if isinstance(signals, dict) and signals:

        html.append("<h3>시장 신호</h3>")
        html.append("<ul>")

        for key, value in signals.items():

            html.append(
                f"<li><b>{safe(key)}</b> : {safe(value)}</li>"
            )

        html.append("</ul>")

    ###################################################################
    # Forecast
    ###################################################################

    if isinstance(forecast, dict):

        comment = forecast.get("comment")

        if comment:

            html.append("<h3>전망</h3>")
            html.append(f"<p>{safe(comment)}</p>")

    html.append("</div>")

    return "\n".join(html)

###############################################################################
# 통계
###############################################################################

def build_summary(data):

    total = 0

    source_count = defaultdict(int)

    category_count = defaultdict(int)

    for category, items in data.items():

        if category == "BRN":
            continue

        if not isinstance(items, list):
            continue

        category_count[category] += len(items)

        total += len(items)

        for item in items:

            source = item.get("source", "")

            source_count[source] += 1

    html = []

    html.append("<div class='summary'>")

    html.append("<h2>오늘의 뉴스 통계</h2>")

    html.append("<ul>")

    html.append(
        f"<li>전체 기사 : {total}건</li>"
    )

    html.append(
        f"<li>카테고리 : {len(category_count)}개</li>"
    )

    html.append(
        f"<li>언론사 : {len(source_count)}개</li>"
    )

    html.append("</ul>")

    html.append("</div>")

    return "\n".join(html)


###############################################################################
# 카테고리
###############################################################################

def build_category(name, items):

    if not items:

        return ""

    html = []

    html.append(

        section_header(
            f"{name} ({len(items)})"
        )

    )

    for idx, item in enumerate(items, 1):

        html.append(
            build_news_item(
                item,
                idx,
            )
        )

    html.append(section_footer())

    return "\n".join(html)


###############################################################################
# 헤더
###############################################################################

def build_page_header():

    today = datetime.now().strftime("%Y년 %m월 %d일")

    html = []

    html.append("<div class='summary'>")

    html.append(
        "<h2>부동산 뉴스 브리핑</h2>"
    )

    html.append(
        f"<p>{today}</p>"
    )

    html.append("</div>")

    return "\n".join(html)


###############################################################################
# 언론사 통계
###############################################################################

def build_source_table(data):

    source_count = defaultdict(int)

    total = 0

    for category, items in data.items():

        if category == "BRN":
            continue

        if not isinstance(items, list):
            continue

        for item in items:

            total += 1

            source = item.get("source", "")

            source_count[source] += 1

    if total == 0:

        return ""

    html = []

    html.append("<div class='summary'>")

    html.append("<h2>언론사별 기사수</h2>")

    html.append("<table style='width:100%'>")

    html.append(
        "<tr>"
        "<th align='left'>언론사</th>"
        "<th align='right'>기사수</th>"
        "<th align='right'>비율</th>"
        "</tr>"
    )

    for source, cnt in sorted(
        source_count.items(),
        key=lambda x: x[1],
        reverse=True,
    ):

        ratio = cnt / total * 100

        html.append(

            "<tr>"

            f"<td>{safe(source)}</td>"

            f"<td align='right'>{cnt}</td>"

            f"<td align='right'>{ratio:.1f}%</td>"

            "</tr>"

        )

    html.append("</table>")

    html.append("</div>")

    return "\n".join(html)


###############################################################################
# 카테고리 출력
###############################################################################

def build_categories(data):

    html = []

    for category in CATEGORY_ORDER:

        items = data.get(category)

        if not items:

            continue

        html.append(
            build_category(
                category,
                items,
            )
        )

    return "\n".join(html)


###############################################################################
# 기타 카테고리
###############################################################################

def build_other_categories(data):

    html = []

    for category, items in sorted(data.items()):

        if category == "BRN":

            continue

        if category in CATEGORY_ORDER:

            continue

        if not isinstance(items, list):

            continue

        if not items:

            continue

        html.append(

            build_category(
                category,
                items,
            )

        )

    return "\n".join(html)


###############################################################################
# 빈 뉴스
###############################################################################

def build_empty():

    html = []

    html.append(
        "<div class='summary'>"
    )

    html.append(
        "<h2>오늘 수집된 뉴스가 없습니다.</h2>"
    )

    html.append(
        "<p>RSS 및 검색 결과가 비어 있습니다.</p>"
    )

    html.append("</div>")

    return "\n".join(html)


###############################################################################
# 기사 개수
###############################################################################

def count_news(data):

    total = 0

    for category, items in data.items():

        if category == "BRN":

            continue

        if isinstance(items, list):

            total += len(items)

    return total


###############################################################################
# 메인 HTML
###############################################################################

def build_html(data):
    """
    data 예시

    {
        "정책": [...],
        "시장동향": [...],
        "청약": [...],
        "공급개발": [...],
        "재건축": [...],
        "세제": [...],
        "부산경남": [...],
        "BRN": {...}
    }
    """

    html = []

    html.append(html_header())

    html.append(build_page_header())

    total = count_news(data)

    if total == 0:

        html.append(build_empty())

        html.append(html_footer())

        return "\n".join(html)

    ###########################################################################
    # BRN
    ###########################################################################

    brn = data.get("BRN")

    if isinstance(brn, dict):

        html.append(
            build_brn(brn)
        )

    ###########################################################################
    # 뉴스 통계
    ###########################################################################

    html.append(
        build_summary(data)
    )

    ###########################################################################
    # 언론사 통계
    ###########################################################################

    html.append(
        build_source_table(data)
    )

    ###########################################################################
    # 기본 카테고리
    ###########################################################################

    html.append(
        build_categories(data)
    )

    ###########################################################################
    # 기타 카테고리
    ###########################################################################

    other = build_other_categories(data)

    if other:

        html.append(other)

    ###########################################################################

    html.append(
        html_footer()
    )

    return "\n".join(html)


###############################################################################
# 저장
###############################################################################

def save_html(data, output="index.html"):

    html = build_html(data)

    with open(
        output,
        "w",
        encoding="utf-8-sig",
    ) as f:

        f.write(html)

    print(
        f"[SAVE HTML] {output}"
    )


###############################################################################
# 테스트
###############################################################################

if __name__ == "__main__":

    sample = {

        "시장동향": [

            {
                "title": "서울 아파트값 상승",
                "link": "https://example.com/1",
                "source": "한국경제",
                "summary": "서울 아파트 가격이 상승세를 이어가고 있다."
            },

            {
                "title": "전국 아파트 거래 증가",
                "link": "https://example.com/2",
                "source": "매일경제",
            },

        ],

        "재건축": [

            {
                "title": "재건축 규제 완화",
                "link": "https://example.com/3",
                "source": "서울경제",
            }

        ],

        "부산경남": [

            {
                "title": "부산 분양시장 회복",
                "link": "https://example.com/4",
                "source": "부산일보",
            }

        ],

        "BRN": {

            "summary": "서울은 강보합, 지방은 보합세를 유지했습니다.",

            "매매": "▲0.08%",

            "전세": "▲0.03%",

            "매수우위": "61.2",

            "매도우위": "38.8",

        }

    }

    html = build_html(sample)

    with open(
        "index.html",
        "w",
        encoding="utf-8-sig",
    ) as f:

        f.write(html)

    print("[완료] index.html 생성")
