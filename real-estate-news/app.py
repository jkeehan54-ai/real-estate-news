import os

from flask import Flask
from flask import render_template

from news_fetcher import (
    fetch_news,
    make_briefing
)

app = Flask(__name__)


@app.route("/")
def home():

    try:

        articles = fetch_news()

        briefing = make_briefing(
            articles
        )

        top_articles = articles[:5]

    except Exception as e:

        print("오류:", e)

        articles = []

        briefing = "뉴스를 불러오는 중입니다."

        top_articles = []

    return render_template(

        "index.html",

        articles=articles,

        top_articles=top_articles,

        briefing=briefing
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