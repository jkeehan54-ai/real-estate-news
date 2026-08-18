# modules/html_builder.py
# ============================================================
# BRN 2.0 HTML Builder
# Sprint 1-2
# Part 1 / 3
#
# 기존 BRN 구조 보존
# + src/source 호환
# + 언론사 바로가기 복구
# ============================================================

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from html import escape

from .news_config import SOURCES

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
# 기사 제목 표시용 정리
###############################################################################

def display_title(value):

    """
    기사 제목을 화면 표시용으로 정리한다.

    주의:
    - 중복 제거용 normalize()와 분리한다.
    - 원문의 일반적인 공백은 최대한 유지한다.
    - 숫자/기호가 분리되어 들어온 일부 RSS 제목을 보정한다.
    """

    if value is None:
        return ""

    title = str(value)

    # --------------------------------------------------------
    # HTML escape 전 제목 문자열에서 보정
    # --------------------------------------------------------

    replacements = {

        # 퍼센트
        "3 18%": "3.18%",
        "3 27%": "3.27%",
        "0 13%": "0.13%",
        "4 4%": "4.4%",
        "1 5%": "1.5%",

        # 자주 발생하는 %p
        "0 13 p": "0.13%p",
        "0 13% p": "0.13%p",

        # 만명 / 만 가구
        "1 5만명": "1.5만명",
        "2 3만명": "2.3만명",
        "1 5만 명": "1.5만 명",

        # 억 / 조 단위
        "5조원": "5조원",

        # 날짜
        "8 13 대책": "8·13 대책",
        "8 13": "8·13",

        # 배수
        "1 36배": "1.36배",

    }

    for old, new in replacements.items():

        title = title.replace(
            old,
            new,
        )

    return title


###############################################################################
# 언론사 이름 가져오기
###############################################################################

def get_source(item):

    """
    기존 데이터의 source/src 양쪽을 모두 지원한다.

    기존 html_builder.py:
        item["source"]

    현재 news_pipeline.py:
        item["src"]
    """

    if not isinstance(item, dict):
        return ""

    return (
        item.get("source")
        or item.get("src")
        or ""
    )


###############################################################################
# 언론사 바로가기 URL
###############################################################################

def get_source_url(source):

    """
    news_config.py의 SOURCES에서
    언론사 바로가기 URL을 가져온다.

    SOURCES 값이 Markdown 링크 형태인 경우
    실제 URL만 추출한다.
    """

    if not source:
        return ""

    value = SOURCES.get(
        source,
        "",
    )

    if not value:
        return ""

    value = str(value).strip()

    # --------------------------------------------------------
    # Markdown 링크
    #
    # [표시명](https://example.com)
    # --------------------------------------------------------

    if value.startswith("[") and "](" in value:

        start = value.find("](") + 2

        end = value.find(
            ")",
            start,
        )

        if end > start:

            return value[
                start:end
            ].strip()

    # --------------------------------------------------------
    # 일반 URL
    # --------------------------------------------------------

    if value.startswith(
        (
            "http://",
            "https://",
        )
    ):

        return value

    return ""


###############################################################################
# 언론사 바로가기
###############################################################################

def build_source_links(data):

    """
    전체 뉴스 데이터에서 실제 사용된 언론사를 추출하여
    클릭 가능한 언론사 바로가기를 생성한다.

    news_pipeline.py의 현재 구조:

        {
            "title": ...,
            "link": ...,
            "src": ...,
            "pub_str": ...
        }

    기존 구조의 source도 동시에 지원한다.
    """

    sources = set()

    for category, items in data.items():

        if category == "BRN":
            continue

        if not isinstance(
            items,
            list,
        ):
            continue

        for item in items:

            source = get_source(
                item
            )

            if source:
                sources.add(
                    source
                )

    if not sources:
        return ""

    html = []

    html.append(
        "<div class='summary'>"
    )

    html.append(
        "<h2>언론사 바로가기</h2>"
    )

    html.append(
        "<div class='source-links'>"
    )

    # --------------------------------------------------------
    # 화면에 표시할 순서
    #
    # SOURCES의 설정 순서를 우선한다.
    # --------------------------------------------------------

    ordered_sources = []

    for source in SOURCES:

        if source in sources:

            ordered_sources.append(
                source
            )

    # --------------------------------------------------------
    # SOURCES에 없는 매체도 마지막에 표시
    # --------------------------------------------------------

    for source in sorted(sources):

        if source not in ordered_sources:

            ordered_sources.append(
                source
            )

    # --------------------------------------------------------
    # 링크 생성
    # --------------------------------------------------------

    for source in ordered_sources:

        url = get_source_url(
            source
        )

        source_html = safe(
            source
        )

        if url:

            url_html = escape(
                url,
                quote=True,
            )

            html.append(
                f"<a "
                f"class='source-link' "
                f"href='{url_html}' "
                f"target='_blank' "
                f"rel='noopener noreferrer'>"
                f"{source_html}"
                f"</a>"
            )

        else:

            html.append(
                f"<span "
                f"class='source-link source-disabled'>"
                f"{source_html}"
                f"</span>"
            )

    html.append(
        "</div>"
    )

    html.append(
        "</div>"
    )

    return "\n".join(
        html
    )


###############################################################################
# 기사 한 줄
###############################################################################

def build_news_item(
    item,
    no,
):

    title = safe(
        item.get("title")
    )

    link = item.get(
        "link",
        "",
    )

    source = safe(
        get_source(item)
    )

    summary = safe(
        item.get("summary")
    )

    html = []

    html.append(
        "<div class='news-item'>"
    )

    html.append(
        "<div class='news-title'>"
    )

    # --------------------------------------------------------
    # 기사 URL 안전 처리
    # --------------------------------------------------------

    link_html = escape(
        str(link),
        quote=True,
    )

    html.append(
        f"<span class='news-no'>{no}.</span> "
        f"<a href='{link_html}' "
        f"target='_blank' "
        f"rel='noopener noreferrer'>"
        f"{title}</a>"
    )

    html.append(
        "</div>"
    )

    # --------------------------------------------------------
    # 매체명
    # --------------------------------------------------------

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

    html.append(
        "</div>"
    )

    return "\n".join(
        html
    )


###############################################################################
# BRN 카드
###############################################################################

def build_brn(brn):

    if not brn:
        return ""

    summary = safe(
        brn.get(
            "summary",
            "",
        )
    )

    dashboard = brn.get(
        "dashboard",
        {},
    )

    signals = brn.get(
        "signals",
        {},
    )

    forecast = brn.get(
        "forecast",
        {},
    )

    html = []

    html.append(
        "<div class='summary'>"
    )

    html.append(
        "<h2>📊 BRN 시장 브리핑</h2>"
    )

    if summary:

        html.append(
            f"<p>{summary}</p>"
        )

    ###################################################################
    # Dashboard
    ###################################################################

    if (
        isinstance(
            dashboard,
            dict,
        )
        and dashboard
    ):

        labels = {

            "nation": "전국",

            "seoul": "서울",

            "busan": "부산",

            "buyer": "매수우위",

            "seller": "매도우위",

            "weeks": "연속주수",

            "trend": "추세",

        }

        html.append(
            "<table>"
        )

        html.append(
            "<tr>"
            "<th>항목</th>"
            "<th>값</th>"
            "</tr>"
        )

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

        html.append(
            "</table>"
        )

    ###################################################################
    # Signals
    ###################################################################

    if (
        isinstance(
            signals,
            dict,
        )
        and signals
    ):

        html.append(
            "<h3>시장 신호</h3>"
        )

        html.append(
            "<ul>"
        )

        for key, value in signals.items():

            html.append(
                f"<li>"
                f"<b>{safe(key)}</b> : "
                f"{safe(value)}"
                f"</li>"
            )

        html.append(
            "</ul>"
        )

    ###################################################################
    # Forecast
    ###################################################################

    if isinstance(
        forecast,
        dict,
    ):

        comment = forecast.get(
            "comment"
        )

        if comment:

            html.append(
                "<h3>전망</h3>"
            )

            html.append(
                f"<p>{safe(comment)}</p>"
            )

    html.append(
        "</div>"
    )

    return "\n".join(
        html
    )


# modules/html_builder.py
# ============================================================
# BRN 2.0 HTML Builder
# Sprint 1-2
# Part 2 / 3
# ============================================================

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

        if not isinstance(
            items,
            list,
        ):
            continue

        category_count[category] += len(items)

        total += len(items)

        for item in items:

            source = get_source(
                item
            )

            source_count[source] += 1

    html = []

    html.append(
        "<div class='summary'>"
    )

    html.append(
        "<h2>오늘의 뉴스 통계</h2>"
    )

    html.append(
        "<ul>"
    )

    html.append(
        f"<li>전체 기사 : {total}건</li>"
    )

    html.append(
        f"<li>카테고리 : "
        f"{len(category_count)}개</li>"
    )

    html.append(
        f"<li>언론사 : "
        f"{len(source_count)}개</li>"
    )

    html.append(
        "</ul>"
    )

    html.append(
        "</div>"
    )

    return "\n".join(
        html
    )


###############################################################################
# 카테고리
###############################################################################

def build_category(
    name,
    items,
):

    if not items:
        return ""

    html = []

    html.append(
        section_header(
            f"{name} ({len(items)})"
        )
    )

    for idx, item in enumerate(
        items,
        1,
    ):

        html.append(
            build_news_item(
                item,
                idx,
            )
        )

    html.append(
        section_footer()
    )

    return "\n".join(
        html
    )


###############################################################################
# 헤더
###############################################################################

def build_page_header():

    today = datetime.now().strftime(
        "%Y년 %m월 %d일"
    )

    html = []

    html.append(
        "<div class='summary'>"
    )

    html.append(
        "<h2>부동산 뉴스 브리핑</h2>"
    )

    html.append(
        f"<p>{today}</p>"
    )

    html.append(
        "</div>"
    )

    return "\n".join(
        html
    )


###############################################################################
# 언론사 통계
###############################################################################

def build_source_table(data):

    source_count = defaultdict(int)

    total = 0

    for category, items in data.items():

        if category == "BRN":
            continue

        if not isinstance(
            items,
            list,
        ):
            continue

        for item in items:

            total += 1

            source = get_source(
                item
            )

            if source:
                source_count[source] += 1

    if total == 0:
        return ""

    html = []

    html.append(
        "<div class='summary'>"
    )

    html.append(
        "<h2>언론사별 기사수</h2>"
    )

    html.append(
        "<table style='width:100%'>"
    )

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

        ratio = (
            cnt / total * 100
        )

        source_url = get_source_url(
            source
        )

        source_name = safe(
            source
        )

        if source_url:

            source_html = (
                f"<a "
                f"href='{escape(source_url, quote=True)}' "
                f"target='_blank' "
                f"rel='noopener noreferrer'>"
                f"{source_name}"
                f"</a>"
            )

        else:

            source_html = source_name

        html.append(
            "<tr>"
            f"<td>{source_html}</td>"
            f"<td align='right'>{cnt}</td>"
            f"<td align='right'>{ratio:.1f}%</td>"
            "</tr>"
        )

    html.append(
        "</table>"
    )

    html.append(
        "</div>"
    )

    return "\n".join(
        html
    )


###############################################################################
# 카테고리 출력
###############################################################################

def build_categories(data):

    html = []

    for category in CATEGORY_ORDER:

        items = data.get(
            category
        )

        if not items:
            continue

        html.append(
            build_category(
                category,
                items,
            )
        )

    return "\n".join(
        html
    )


###############################################################################
# 기타 카테고리
###############################################################################

def build_other_categories(data):

    html = []

    for category, items in sorted(
        data.items()
    ):

        if category == "BRN":
            continue

        if category in CATEGORY_ORDER:
            continue

        if not isinstance(
            items,
            list,
        ):
            continue

        if not items:
            continue

        html.append(
            build_category(
                category,
                items,
            )
        )

    return "\n".join(
        html
    )


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

    html.append(
        "</div>"
    )

    return "\n".join(
        html
    )


###############################################################################
# 기사 개수
###############################################################################

def count_news(data):

    total = 0

    for category, items in data.items():

        if category == "BRN":
            continue

        if isinstance(
            items,
            list,
        ):

            total += len(items)

    return total


# modules/html_builder.py
# ============================================================
# BRN 2.0 HTML Builder
# Sprint 1-2
# Part 3 / 3
# ============================================================


###############################################################################
# HTML 전체 생성
###############################################################################

def build_html(
    data,
    brn=None,
    title="BRN 부동산 뉴스 브리핑",
):
    """
    BRN 전체 HTML 생성

    data 구조:

        {
            "정책": [...],
            "시장동향": [...],
            "청약": [...],
            ...
        }

    brn은 선택 사항이다.
    """

    total = count_news(data)

    html = []

    # --------------------------------------------------------
    # HTML HEADER
    # --------------------------------------------------------

    html.append(
        html_header(title)
    )

    # --------------------------------------------------------
    # PAGE HEADER
    # --------------------------------------------------------

    html.append(
        build_page_header()
    )

    # --------------------------------------------------------
    # BRN MARKET BRIEF
    # --------------------------------------------------------

    if brn:

        html.append(
            build_brn(brn)
        )

    # --------------------------------------------------------
    # NEWS SUMMARY
    # --------------------------------------------------------

    html.append(
        build_summary(data)
    )

    # --------------------------------------------------------
    # SOURCE QUICK LINKS
    # --------------------------------------------------------

    html.append(
        build_source_links(data)
    )

    # --------------------------------------------------------
    # SOURCE STATISTICS
    # --------------------------------------------------------

    html.append(
        build_source_table(data)
    )

    # --------------------------------------------------------
    # NEWS
    # --------------------------------------------------------

    if total > 0:

        html.append(
            build_categories(data)
        )

        html.append(
            build_other_categories(data)
        )

    else:

        html.append(
            build_empty()
        )

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    html.append(
        html_footer()
    )

    return "\n".join(
        html
    )


###############################################################################
# 파일 저장
###############################################################################

def save_html(
    html,
    filename="index.html",
):
    """
    HTML 파일 저장
    """

    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as fp:

        fp.write(
            html
        )

    return filename


###############################################################################
# build + save
###############################################################################

def build_and_save(
    data,
    filename="index.html",
    brn=None,
    title="BRN 부동산 뉴스 브리핑",
):
    """
    HTML 생성 후 파일 저장
    """

    html = build_html(
        data=data,
        brn=brn,
        title=title,
    )

    save_html(
        html,
        filename,
    )

    return html


###############################################################################
# 기존 BRN 호환 함수
###############################################################################

def generate_html(
    data,
    filename="index.html",
    brn=None,
):
    """
    기존 코드와의 호환을 위한 함수

    반환값:
        생성된 HTML 문자열
    """

    return build_and_save(
        data=data,
        filename=filename,
        brn=brn,
    )


###############################################################################
# 기존 build_html 호출 호환
###############################################################################

def build(
    data,
    brn=None,
):
    """
    간단한 HTML 생성 API
    """

    return build_html(
        data=data,
        brn=brn,
    )


###############################################################################
# 테스트용 최소 데이터
###############################################################################

def _test_data():

    return {

        "정책": [
            {
                "title": "테스트 정책 기사",
                "link": "https://example.com",
                "src": "한국경제",
                "pub_str": "08/10 10:00",
            }
        ],

        "시장동향": [],

        "청약": [],

        "공급개발": [],

        "재건축": [],

        "세제": [],

        "부산경남": [],

    }


###############################################################################
# MODULE EXPORT
###############################################################################

__all__ = [

    "CATEGORY_ORDER",

    "safe",

    "get_source",

    "get_source_url",

    "build_source_links",

    "build_news_item",

    "build_brn",

    "build_summary",

    "build_category",

    "build_page_header",

    "build_source_table",

    "build_categories",

    "build_other_categories",

    "build_empty",

    "count_news",

    "build_html",

    "save_html",

    "build_and_save",

    "generate_html",

    "build",

]


###############################################################################
# DIRECT TEST
###############################################################################

if __name__ == "__main__":

    test_data = _test_data()

    test_html = build_html(
        test_data
    )

    print(
        test_html
    )




