# html_builder.py

"""
html_builder.py

BRN HTML 생성기

입력
-----
news : list(dict)

출력
-----
index.html
"""

from collections import defaultdict
from datetime import datetime

from .templates import (
    html_header,
    html_footer,
    section_header,
    section_footer,
)

###############################################################################
# 카테고리 순서
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
# 기사 한 줄
###############################################################################

def build_news_item(item):

    title = item.get("title","")
    link = item.get("link","")
    source = item.get("source","")

    return f"""
<div class="news-item">
<a href="{link}" target="_blank">
{title}
</a>
<span class="source">{source}</span>
</div>
"""


###############################################################################
# 카테고리 그룹화
###############################################################################

def group_news(news):

    grouped = defaultdict(list)

    for item in news:

        category = item.get("category","기타")

        grouped[category].append(item)

    return grouped


###############################################################################
# 카테고리 HTML
###############################################################################

def build_category(name, items):

    html = []

    html.append(section_header(name))

    for item in items:

        html.append(build_news_item(item))

    html.append(section_footer())

    return "\n".join(html)


###############################################################################
# 통계
###############################################################################

def build_summary(news):

    source_count = defaultdict(int)

    for item in news:

        source = item.get("source","")

        source_count[source] += 1

    html = [
        "<div class='summary'>",
        "<h2>오늘의 뉴스 통계</h2>",
        "<ul>"
    ]

    html.append(f"<li>전체 기사 : {len(news)}</li>")

    for source, cnt in sorted(source_count.items()):

        html.append(f"<li>{source} : {cnt}</li>")

    html.append("</ul>")
    html.append("</div>")

    return "\n".join(html)


###############################################################################
# 메인 HTML
###############################################################################

def build_html(news):

    grouped = group_news(news)

    html = []

    html.append(html_header())

    html.append(build_summary(news))

    for cat in CATEGORY_ORDER:

        if cat not in grouped:

            continue

        html.append(build_category(cat, grouped[cat]))

    html.append(html_footer())

    return "\n".join(html)


###############################################################################
# 저장
###############################################################################

def save_html(news, output="index.html"):

    html = build_html(news)

    with open(output, "w", encoding="utf-8") as f:

        f.write(html)

    print(f"[SAVE HTML] {output}")


###############################################################################
# 테스트
###############################################################################

if __name__ == "__main__":

    sample = [

        {
            "title":"서울 아파트 상승",
            "link":"https://example.com/1",
            "source":"한국경제",
            "category":"시장동향"
        },

        {
            "title":"재건축 규제 완화",
            "link":"https://example.com/2",
            "source":"매일경제",
            "category":"재건축"
        },

        {
            "title":"부산 분양시장 회복",
            "link":"https://example.com/3",
            "source":"부산일보",
            "category":"부산경남"
        }

    ]

    save_html(sample)
