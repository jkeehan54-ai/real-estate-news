import os
import threading
import time

from flask import Flask
from flask import render_template
from flask import request

from news_fetcher import (
    fetch_news,
    make_briefing
)

app = Flask(__name__)

cached_articles = []
cached_briefing = ""


def update_news():

    global cached_articles
    global cached_briefing

    while True:

        try:

            articles = fetch_news()

            cached_articles = articles

            cached_briefing = make_briefing(
                articles
            )

            print(
                "뉴스 업데이트 완료"
            )

        except Exception as e:

            print(
                "뉴스 업데이트 오류:",
                e
            )

        time.sleep(300)


thread = threading.Thread(
    target=update_news,
    daemon=True
)

thread.start()


@app.route("/")
def home():

    query = request.args.get(
        "q",
        ""
    )

    category = request.args.get(
        "category",
        "전체"
    )

    articles = cached_articles

    if query:

        articles = [

            article

            for article in articles

            if query.lower() in (

                article["title"]
                + article["summary"]

            ).lower()
        ]

    if category != "전체":

        articles = [

            article

            for article in articles

            if article["category"]
            == category
        ]

    top_articles = articles[:5]

    return render_template(

        "index.html",

        articles=articles,

        top_articles=top_articles,

        briefing=cached_briefing,

        query=query,

        category=category
    )


if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )