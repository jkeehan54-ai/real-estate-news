import os

from flask import Flask
from flask import render_template
from flask import request

from news_fetcher import (
    fetch_news,
    make_briefing
)

app = Flask(__name__)


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

    articles = fetch_news()

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

    briefing = make_briefing(
        articles
    )

    top_articles = articles[:5]

    return render_template(

        "index.html",

        articles=articles,

        top_articles=top_articles,

        briefing=briefing,

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