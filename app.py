import os

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for

from news_fetcher import (
    fetch_news,
    make_briefing
)

app = Flask(__name__)

app.config[
    "TEMPLATES_AUTO_RELOAD"
] = True

app.config[
    "SEND_FILE_MAX_AGE_DEFAULT"
] = 0


@app.after_request
def add_header(response):

    response.headers[
        "Cache-Control"
    ] = (
        "no-store, no-cache, "
        "must-revalidate, max-age=0"
    )

    response.headers[
        "Pragma"
    ] = "no-cache"

    response.headers[
        "Expires"
    ] = "0"

    return response


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

    top_articles = articles[:5]

    briefing = make_briefing(
        articles
    )

    return render_template(

        "index.html",

        articles=articles,

        top_articles=top_articles,

        briefing=briefing,

        query=query,

        category=category
    )


@app.route("/refresh")
def refresh_news():

    return redirect(
        url_for("home")
    )


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )
    )

    app.run(

        host="0.0.0.0",

        port=port,

        debug=False
    )