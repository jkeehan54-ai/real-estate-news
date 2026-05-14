import feedparser
from urllib.parse import quote
import re

SEARCH_KEYWORDS=[
"아파트",
"주택",
"청약",
"분양",
"재건축",
"재개발",
"전세",
"월세",
"집값",
"양도세",
"종부세"
]


def fetch_news():

    articles=[]
    seen=set()

    for keyword in SEARCH_KEYWORDS:

        url=(
        f"https://news.google.com/rss/search?q={quote(keyword)}&hl=ko&gl=KR&ceid=KR:ko"
        )

        feed=feedparser.parse(url)

        for item in feed.entries:

            title=getattr(item,"title","")
            summary=getattr(item,"summary","")
            link=getattr(item,"link","")

            if title in seen:
                continue

            seen.add(title)

            summary=re.sub(
                '<.*?>',
                '',
                summary
            )

            source="뉴스"

            if hasattr(item,"source"):
                source=item.source.title

            articles.append({
                "title":title,
                "summary":summary[:200],
                "source":source,
                "link":link
            })

    return articles[:50]


def make_briefing(articles):

    return [
        x["title"]
        for x in articles[:5]
    ]