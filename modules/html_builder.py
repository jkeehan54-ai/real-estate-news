# html_builder.py

from datetime import datetime

from modules.news_config import (
    KST,
    SOURCES,
)

from modules.news_utils import (
    interleave_by_source,
)

from modules.kb_market import (
    get_market_brief,
)



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
           
