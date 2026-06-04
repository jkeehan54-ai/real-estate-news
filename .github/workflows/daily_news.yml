name: Daily News Update

on:
  schedule:
    - cron: '0 0 * * *'   # 09:00 KST
    - cron: '0 2 * * *'   # 11:00 KST
    - cron: '0 5 * * *'   # 14:00 KST
    - cron: '0 23 * * *'  # 08:00 KST
  workflow_dispatch:       # 수동 실행

jobs:
  update-news:
    runs-on: ubuntu-latest
    env:
      TZ: Asia/Seoul       # ★ Actions 실행 환경 시간대를 KST로 고정

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install feedparser requests

      - name: Generate news HTML
        run: python generate_news.py

      - name: Show generated date (디버그용)
        run: |
          echo "=== 현재 서버 시간 ==="
          date
          echo "=== index.html 날짜 확인 ==="
          grep -o '브리핑 ([^)]*' index.html | head -1

      - name: Commit and push index.html
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add index.html
          git diff --cached --quiet || git commit -m "news: $(date '+%Y-%m-%d %H:%M KST')"
          git push
