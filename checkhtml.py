"""
부산일보 / 국제신문 / 네이버부동산 HTML 구조 확인 스크립트
실행: python check_html.py
결과와 생성된 *_html.txt 파일을 Claude에 공유해주세요.
"""
import requests
from bs4 import BeautifulSoup
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}

TARGETS = [
    # 부산일보
    ("부산일보_경제",    "https://www.busan.com/",          "https://www.busan.com/economy/"),
    ("부산일보_부동산",  "https://www.busan.com/",          "https://www.busan.com/land/"),
    # 국제신문
    ("국제신문_부동산",  "https://www.kookje.co.kr/",       "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0220"),
    ("국제신문_경제",    "https://www.kookje.co.kr/",       "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200"),
    # 네이버 부동산 뉴스
    ("네이버부동산_뉴스", "https://land.naver.com/",        "https://land.naver.com/news/"),
    ("네이버부동산_뉴스2","https://land.naver.com/",        "https://fin.land.naver.com/news"),
    ("네이버뉴스_부동산", "https://news.naver.com/",        "https://news.naver.com/section/101"),  # 경제 섹션
]

def analyze(name, home_url, target_url):
    print(f"\n{'='*60}")
    print(f"[{name}]")
    print(f"URL: {target_url}")
    try:
        s = requests.Session()
        s.headers.update(HEADERS)
        # 홈 먼저 방문해서 쿠키 획득
        s.get(home_url, timeout=6)
        s.headers["Referer"] = home_url
        resp = s.get(target_url, timeout=10)
        print(f"HTTP {resp.status_code} | 길이 {len(resp.text):,}자")

        if resp.status_code != 200:
            print(f"  → 접근 실패 (HTTP {resp.status_code})")
            return

        if len(resp.text) < 500:
            print(f"  → 응답이 너무 짧음 (JS 렌더링 필요 가능성)")
            print(f"  → 내용: {resp.text[:200]}")
            return

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 1. 기사 후보 링크 (15~100자 텍스트)
        print(f"\n[기사 후보 링크 상위 15개]")
        candidates = []
        for a in soup.find_all('a', href=True):
            txt = a.get_text(strip=True)
            href = a['href']
            if 15 <= len(txt) <= 100:
                parent = a.find_parent()
                p_tag = parent.name if parent else '-'
                p_cls = ' '.join(parent.get('class', []))[:40] if parent else '-'
                gp = parent.find_parent() if parent else None
                gp_tag = gp.name if gp else '-'
                gp_cls = ' '.join(gp.get('class', []))[:40] if gp else '-'
                candidates.append((txt, href, p_tag, p_cls, gp_tag, gp_cls))

        for txt, href, p_tag, p_cls, gp_tag, gp_cls in candidates[:15]:
            print(f"  부모: {p_tag}.{p_cls}")
            print(f"  조부: {gp_tag}.{gp_cls}")
            print(f"  제목: {txt}")
            print(f"  링크: {href[:80]}")
            print()

        # 2. 뉴스 관련 class/id 목록
        print(f"[뉴스 관련 class/id]")
        news_classes = set()
        news_ids = set()
        keywords_for_class = ['news', 'article', 'list', 'item', 'tit', 'title', 'board', 'cont', 'wrap']
        for el in soup.find_all(True):
            for c in el.get('class', []):
                if any(k in c.lower() for k in keywords_for_class):
                    news_classes.add(f"{el.name}.{c}")
            el_id = el.get('id', '')
            if el_id and any(k in el_id.lower() for k in keywords_for_class):
                news_ids.add(f"{el.name}#{el_id}")
        if news_classes:
            print(f"  class: {', '.join(sorted(news_classes)[:15])}")
        if news_ids:
            print(f"  id:    {', '.join(sorted(news_ids)[:10])}")

        # 3. HTML 저장 (앞 8000자)
        save_dir = os.path.dirname(os.path.abspath(__file__))
        fname = os.path.join(save_dir, f"{name}_html.txt")
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(f"URL: {target_url}\n")
            f.write(f"HTTP: {resp.status_code}\n")
            f.write("="*60 + "\n")
            f.write(soup.prettify()[:8000])
        print(f"\n→ HTML을 [{fname}] 에 저장했습니다.")

    except Exception as e:
        print(f"  오류: {type(e).__name__} - {e}")


for name, home, target in TARGETS:
    analyze(name, home, target)

print("\n" + "="*60)
print("완료!")
print("위 콘솔 출력 내용과 생성된 *_html.txt 파일을 Claude에 공유해주세요.")
print("특히 HTTP 200이 뜬 사이트의 html.txt 파일이 중요합니다.")