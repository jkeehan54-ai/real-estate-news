# generate_news_modular.py
"""
부동산 뉴스 브리핑 - 비용 없는 자동 필터링
============================================
비부동산 제거: RE_ESTATE(포함) + RE_EXCLUDE(제외) 2중 규칙
중복 제거: 문자열유사도 + 키워드자카드 + 엔티티겹침 3단계
날짜: datetime.now(KST) 명시 → GitHub Actions UTC 환경에서도 정확
"""
print("=== generate_news_modular.py 실행 ===")

import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import feedparser, requests, re, os
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
from difflib import SequenceMatcher
from datetime import datetime, timezone, timedelta
from modules.news_config import *
from modules.news_utils import *
from modules.news_filter import *
from modules.rss_engine import *
from modules.crawler_engine import *
from modules.google_engine import *
from modules.kb_market import *
from modules.html_builder import *
from modules.news_pipeline import get_clean_news




# ── 날짜 유틸 ─────────────────────────────────────────────────────────────────





# ══════════════════════════════════════════════════════════════════════════════
# 비부동산 제거 함수
# ══════════════════════════════════════════════════════════════════════════════




# ══════════════════════════════════════════════════════════════════════════════
# 중복 제거 함수 (3단계, 비용 없음)
# ══════════════════════════════════════════════════════════════════════════════





# ── 카테고리 분류 ─────────────────────────────────────────────────────────────



# ── A. RSS 수집 ───────────────────────────────────────────────────────────────



# ── B-1. 부산일보 스크래핑 ───────────────────────────────────────────────────


# ── B-2. 국제신문 스크래핑 ───────────────────────────────────────────────────


# ── B-3. 네이버 부동산 스크래핑 ──────────────────────────────────────────────


# ── C. Google News RSS ───────────────────────────────────────────────────────

# ── 메인 수집 ─────────────────────────────────────────────────────────────────



def get_latest_kb_date():

    url = (
        "https://api.kbland.kr/land-extra/market-conditions/ref-date"
        "?거래유형=1&주기=1"
    )

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://kbland.kr",
        "Referer": "https://kbland.kr/",
        "webservice": "1",
    }

    r = requests.get(
        url,
        headers=headers,
        timeout=20
    )

    r.raise_for_status()

    data = r.json()

    latest = data["dataBody"]["data"][0]

    print("[KB 최신 기준일]", latest)

    return latest
    
# ── HTML 생성 ─────────────────────────────────────────────────────────────────
def get_market_brief():

    try:

        latest = get_latest_kb_date()

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://kbland.kr",
            "Referer": "https://kbland.kr/",
            "webservice": "1",
        }

        url = (
            "https://api.kbland.kr/land-extra/market-conditions/sales"
            f"?기준년월일={latest}"
            "&법정동코드=0000000000"
        )

        r = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        print("[KB STATUS]", r.status_code)

        data = r.json()

        print(
            "[KB DATA DATE]",
            data["dataBody"]["data"]["기준년월일"]
        )

        summary = data["dataBody"]["data"]["시장요약"]
        print("[KB SUMMARY]")
        print(summary)
        change = summary["대표지역변동률"]
        weeks = summary["대표지역변동률연속주수"]
        trend = summary["대표지역변동률연속상태"]

        seller = summary["매도자많음응답"]
        buyer = summary["매수자많음응답"]

        all_market = data["dataBody"]["data"]["전체시황"]

        seoul = next(
            x["변동률"]
            for x in all_market
            if x["지역명"] == "서울"
        )

        busan = next(
            x["변동률"]
            for x in all_market
            if x["지역명"] == "부산"
        )

        return (
            f"전국 아파트 매매가격은 {change}% {trend}했습니다. "
            f"{weeks}주 연속 {trend}세를 유지했습니다. "
            f"서울은 {market_text(seoul)}, "
            f"부산은 {market_text(busan)}입니다. "
            f"매도자많음 {seller}%, "
            f"매수자많음 {buyer}%입니다."
        )

    except Exception as e:

        print("[KB ERROR]", repr(e))

        return "KB 시황 정보를 불러오지 못했습니다."




def build_html(data):
    today       = datetime.now(KST).strftime("%Y년 %m월 %d일")
    update_time = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    total_news  = sum(len(v) for v in data.values())

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>부동산 뉴스 브리핑 {today}</title>
<style>
body{{font-family:'Malgun Gothic',sans-serif;max-width:1100px;margin:auto;padding:20px;line-height:1.7;background:#f8f9fa}}
h1{{color:#1f4fa3;border-bottom:3px solid #1f4fa3;padding-bottom:8px}}
h2{{background:#f2f6ff;padding:8px 12px;border-left:5px solid #1f4fa3;margin-top:24px}}
.sources{{background:#fff;padding:10px;border-radius:6px;margin-bottom:12px;font-size:13px}}
.sources a{{color:#1f4fa3;text-decoration:none;margin:0 4px}}
.sources a:hover{{text-decoration:underline}}
.briefing{{background:#fff3cd;padding:12px;border-radius:6px;border-left:4px solid #ffc107;margin:12px 0;font-weight:bold}}
.news-item{{background:#fff;padding:9px 14px;margin:5px 0;border-radius:4px;border-left:3px solid #dee2e6}}
.news-item a{{text-decoration:none;color:#222;font-size:14px;line-height:1.5}}
.news-item a:hover{{color:#1f4fa3;text-decoration:underline}}
.news-meta{{font-size:12px;color:#888;margin-top:2px}}
.empty{{color:#999;font-style:italic;padding:6px}}
.cnt{{font-size:12px;color:#666;font-weight:normal;margin-left:6px}}
</style>
</head>
<body>
<h1>부동산 뉴스 브리핑 ({today})</h1>
<p style="color:#666;font-size:13px">업데이트: {update_time} | 총 {total_news}건</p>
<div class="sources"><b>뉴스매체:</b> """
    html += " | ".join(f'<a href="{u}" target="_blank">{n}</a>' for n, u in SOURCES.items())
    html += f'</div>\n<div class="briefing">{get_market_brief()}</div>\n'

    labels = {
        "청약":    "[청약]",
        "재건축":  "[재건축·재개발]",
        "공급개발": "[공급·개발]",
        "세제":    "[세제]",
        "정책":    "[정책·규제]",
        "부산경남": "[부산·경남]",
        "시장동향": "[시장동향]",
    }
    for cat, lst in data.items():
        html += f'<h2>{labels.get(cat,cat)}<span class="cnt">({len(lst)}건)</span></h2>\n'
        if not lst:
            html += '<p class="empty">최근 24시간 내 수집된 기사가 없습니다.</p>\n'
            continue
        display = interleave_by_source(lst) if cat == "시장동향" else lst
        for n in display:
            print(n)
            html += '<div class="news-item">'
            html += f'<a href="{n["link"]}" target="_blank">{n["title"]}</a>'
            html += f'<div class="news-meta"><b>{n["src"]}</b>'
            if n["pub_str"]:
                html += f' · {n["pub_str"]}'
            html += '</div></div>\n'

    html += f"<p style='text-align:right;color:#bbb;font-size:11px'>총 {total_news}건 · {today}</p>\n"
    html += "</body>\n</html>"
    return html


if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    data = get_clean_news()
    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(build_html(data))
    print(f"\n[완료] {output_path}")
    for cat, lst in data.items():
        print(f"  [{cat}] {len(lst)}건")
           

