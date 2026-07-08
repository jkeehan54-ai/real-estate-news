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




    
# ── HTML 생성 ─────────────────────────────────────────────────────────────────





if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    data = get_clean_news()
    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(build_html(data))
    print(f"\n[완료] {output_path}")
    for cat, lst in data.items():
        print(f"  [{cat}] {len(lst)}건")
           

