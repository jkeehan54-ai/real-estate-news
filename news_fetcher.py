import feedparser

from bs4 import BeautifulSoup


RSS_FEEDS = [

    (
        "매일경제",
        "https://www.mk.co.kr/rss/50300009/"
    ),

    (
        "한국경제",
        "https://www.hankyung.com/feed/realestate"
    ),

    (
        "서울경제",
        "https://www.sedaily.com/rss/NewsReal.xml"
    ),

    (
        "이데일리",
        "https://www.edaily.co.kr/rss/rss_realestate.xml"
    ),

    (
        "연합뉴스",
        "https://www.yna.co.kr/rss/economy.xml"
    ),
]


REAL_ESTATE_KEYWORDS = [

    "부동산",
    "아파트",
    "재건축",
    "재개발",
    "청약",
    "분양",
    "전세",
    "월세",
    "주택",
    "오피스텔",
    "입주",
    "매매",
    "집값",
    "공급",
]


EXCLUDE_KEYWORDS = [

    "연예",
    "축구",
    "야구",
    "농구",
    "비트코인",
    "코인",
]


def clean_html(text):

    if not text:
        return ""

    soup = BeautifulSoup(
        text,
        "html.parser"
    )

    return soup.get_text().strip()


def is_real_estate_news(
    title,
    summary
):

    text = (
        title
        + " "
        + summary
    )

    include = any(

        keyword in text

        for keyword
        in REAL_ESTATE_KEYWORDS
    )

    exclude = any(

        keyword in text

        for keyword
        in EXCLUDE_KEYWORDS
    )

    return include and not exclude


def categorize_news(title):

    if (
        "청약" in title
        or "분양" in title
    ):
        return "청약"

    if (
        "재건축" in title
        or "재개발" in title
    ):
        return "재건축"

    if (
        "세금" in title
        or "양도세" in title
        or "종부세" in title
    ):
        return "세제"

    if (
        "정책" in title
        or "정부" in title
    ):
        return "정책"

    return "부동산"


def remove_duplicates(news_list):

    seen = set()

    unique_news = []

    for news in news_list:

        title = (
            news["title"]
            .replace(" ", "")
            .strip()
        )

        if title not in seen:

            seen.add(title)

            unique_news.append(news)

    return unique_news


def fetch_news():

    articles = []

    for source_name, rss_url in RSS_FEEDS:

        try:

            feed = feedparser.parse(
                rss_url
            )

            entries = feed.entries[:20]

            for entry in entries:

                title = clean_html(
                    entry.get(
                        "title",
                        ""
                    )
                )

                summary = clean_html(
                    entry.get(
                        "summary",
                        ""
                    )
                )

                link = entry.get(
                    "link",
                    ""
                )

                if not is_real_estate_news(
                    title,
                    summary
                ):
                    continue

                articles.append({

                    "title": title,

                    "summary": summary[:180],

                    "link": link,

                    "source": source_name,

                    "category": categorize_news(
                        title
                    )
                })

        except Exception as e:

            print(
                source_name,
                "오류:",
                e
            )

    articles = remove_duplicates(
        articles
    )

    return articles[:50]


def make_briefing(articles):

    if not articles:

        return (
            "오늘의 주요 "
            "부동산 뉴스가 없습니다."
        )

    top_titles = [

        f"• {article['title']}"

        for article
        in articles[:5]
    ]

    return "\n".join(top_titles)