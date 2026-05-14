from flask import Flask, render_template, request
from news_fetcher import fetch_news, make_briefing

app = Flask(__name__)

@app.route('/')
def home():

    query=request.args.get("q","")

    articles=fetch_news()

    if query:
        articles=[
            a for a in articles
            if query.lower() in (
                a["title"]+
                a["summary"]
            ).lower()
        ]

    top_articles=articles[:5]

    briefing=make_briefing(
        articles
    )

    return render_template(
        "index.html",
        articles=articles,
        top_articles=top_articles,
        briefing=briefing,
        query=query
    )

if __name__=="__main__":

    app.run(
        host="0.0.0.0",
        port=8080,
        debug=True
    )