# generate_news_modular.py
"""
부동산 뉴스 브리핑 - 비용 없는 자동 필터링
============================================
비부동산 제거: RE_ESTATE(포함) + RE_EXCLUDE(제외) 2중 규칙
중복 제거: 문자열유사도 + 키워드자카드 + 엔티티겹침 3단계
날짜: datetime.now(KST) 명시 → GitHub Actions UTC 환경에서도 정확
"""

import sys
import io
import os

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from modules.html_builder import build_html
from modules.news_pipeline import get_clean_news


def main():
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "index.html"
    )

    data = get_clean_news()

    

    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(build_html(data))

    print(f"\n[완료] {output_path}")

    for cat, lst in data.items():
        print(f"  [{cat}] {len(lst)}건")


if __name__ == "__main__":
    print("=== generate_news_modular.py 실행 ===")
    main()
           

