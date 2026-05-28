import feedparser
import re
import time
from datetime import datetime

# 1. 설정
KEYWORDS = ["청약", "분양", "집값", "전세", "금리", "재개발", "재건축", "대출", "부동산규제", "오피스텔", "공급"]
# ... (SOURCES 생략 - 이전과 동일) ...

# 오늘 날짜 확인 (YYYY-MM-DD 형식)
today_str = datetime.now().strftime('%Y-%m-%d')

RSS_URL = "https://news.google.com/rss/search?q=%EB%B6%90%EB%8F%99%EC%82%B0+OR+%EC%95%84%ED%8C%8C%ED%8A%B8&hl=ko&gl=KR&ceid=KR:ko&sort=date"
feed = feedparser.parse(RSS_URL)

# ... (HTML 상단 및 .source-bar 코드 생략 - 이전과 동일) ...

# 3. 뉴스 데이터 처리 (오늘 날짜 & 10개 제한 & 중복 제거)
for keyword in KEYWORDS:
    html += f"<h2>#{keyword}</h2><ul>"
    found_count = 0
    seen_keys = set()
    
    for entry in feed.entries:
        if found_count >= 10: break  # 키워드별 10개 제한
        
        # 날짜 확인 (RSS의 published 속성을 오늘 날짜와 비교)
        pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed)).strftime('%Y-%m-%d')
        if pub_date != today_str: continue # 오늘 날짜 아니면 건너뜀
        
        if keyword in entry.title:
            words = re.findall(r'[가-힣]{2,}', entry.title)
            topic_key = "_".join(words[:2])
            
            if topic_key in seen_keys: continue
            
            html += f"<li><a href='{entry.link}' target='_blank'>{entry.title}</a></li>"
            seen_keys.add(topic_key)
            found_count += 1
            
    if found_count == 0:
        html += "<li>오늘 등록된 최신 뉴스가 없습니다.</li>"
    html += "</ul>"
