import time
import feedparser

from bs4 import BeautifulSoup


CACHE_TIME = 600

cached_articles = []

last_update = 0


RSS_FEEDS = [

    (
        "매일경제",
        "https://www.mk.co.kr/rss/50300009/"
    ),

    (
        "연합뉴스",
        "https://www.yna.co.kr/rss/economy.xml"
    ),

    (
        "한겨레",
        "https://www.hani.co.kr/rss/realestate/"
    ),

    (
        "부산일보",
        "https://rss.busan.com/rss/news_realestate.xml"
    ),
]


KEYWORDS = [

    "부동산",
    "아파트",
    "청약",
    "재건축",
    "재개발",
    "분양",
    "전세",
    "월세",
    "주택",
    "오피스텔",
]


def clean_html(text):

    if not text:
        return ""

    soup = BeautifulSoup(
        text,
        "html.parser"
    )

    return soup.get_text().strip()


def is_real_estate(title):

    for keyword in KEYWORDS:

        if keyword in title:
            return True

    return False


def category(title):

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
    ):
        return "세제"

    if (
        "정책" in title
        or "정부" in title
    ):
        return "정책"

    return "부동산"


def remove_duplicates(news):

    seen = set()

    result = []

    for item in news:

        key = item["title"].replace(
            " ",
            ""
        )

        if key not in seen:

            seen.add(key)

            result.append(item)

    return result


def fetch_news():

    global cached_articles
    global last_update

    now = time.time()

    # 캐시 사용
    if (
        cached_articles
        and now - last_update < CACHE_TIME
    ):

        return cached_articles

    articles = []

    for source, url in RSS_FEEDS:

        try:

            print("RSS 수집:", source)

            feed = feedparser.parse(url)

            for entry in feed.entries[:5]:

                title = clean_html(
                    entry.get(
                        "title",
                        ""
                    )
                )

                if not is_real_estate(title):
                    continue

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

                articles.append({

                    "title": title,

                    "summary": summary[:150],

                    "link": link,

                    "source": source,

                    "category": category(title)
                })

        except Exception as e:

            print(
                "RSS 오류:",
                source,
                e
            )

    articles = remove_duplicates(
        articles
    )

    cached_articles = articles[:40]

    last_update = now

    return cached_articles


def make_briefing(articles):

    if not articles:

        return "뉴스를 불러오는 중입니다."

    lines = [

        f"• {article['title']}"

        for article
        in articles[:5]
    ]

    return "\n".join(lines)