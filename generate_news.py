import feedparser
import re

KEYWORDS = ["청약", "분양", "집값", "전세", "금리", "재개발", "재건축", "대출", "부동산규제", "오피스텔", "공급"]

# ... (SOURCES 정의 및 HTML 상단 생략, 이전과 동일) ...

for keyword in KEYWORDS:
    html += f"<h2>#{keyword}</h2><ul>"
    found = False
    seen_normalized_titles = set()
    
    for entry in feed.entries:
        if keyword in entry.title:
            # 제목에서 [단독], [종합] 등 대괄호 내용과 특수문자를 제거하여 순수 제목만 남김
            normalized_title = re.sub(r'\[.*?\]', '', entry.title).strip()
            
            # 정규화된 제목이 이미 리스트에 있다면 건너뜀
            if normalized_title not in seen_normalized_titles:
                html += f"<li><a href='{entry.link}' target='_blank'>{entry.title}</a></li>"
                seen_normalized_titles.add(normalized_title)
                found = True
                
    if not found:
        html += "<li>해당 키워드 뉴스가 없습니다.</li>"
    html += "</ul>"

# ... (나머지 HTML 마무리 코드 동일) ...
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
