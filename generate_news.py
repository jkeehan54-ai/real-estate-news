import feedparser
import re
from difflib import SequenceMatcher

# ... (기존 SOURCES 정의 동일) ...

def is_similar(title1, title2, threshold=0.7):
    # 특수문자 제거 후 유사도 비교
    t1 = re.sub(r'\[.*?\]', '', title1).strip()
    t2 = re.sub(r'\[.*?\]', '', title2).strip()
    return SequenceMatcher(None, t1, t2).ratio() > threshold

# ... (HTML 상단 코드 동일) ...

for keyword in KEYWORDS:
    html += f"<h2>#{keyword}</h2><ul>"
    found = False
    added_titles = [] # 지금까지 추가된 제목 리스트
    
    for entry in feed.entries:
        if keyword in entry.title:
            # 현재 기사 제목이 이미 추가된 기사들과 유사한지 확인
            if any(is_similar(entry.title, t) for t in added_titles):
                continue
            
            html += f"<li><a href='{entry.link}' target='_blank'>{entry.title}</a></li>"
            added_titles.append(entry.title)
            found = True
                
    if not found:
        html += "<li>해당 키워드 뉴스가 없습니다.</li>"
    html += "</ul>"

# ... (하단 마무리 코드 동일) ...
