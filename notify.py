# -*- coding: utf-8 -*-
"""
부동산 경기 지표 알림 발송 (이메일 + 슬랙)
==========================================
동작 방식:
  1) 매일 08:00 KST 실행 시 → 무조건 "일일 요약"을 보냄 (전체 핵심 지표)
  2) 그 외 시간(09~22시, 1시간 간격) 실행 시 → 직전 실행 대비 "의미 있는 변화"가
     있는 지표만 있으면 "변동 알림"을 보내고, 변화가 없으면 아무 것도 보내지 않음
     (매시간 동일 내용 스팸 방지)

필요한 GitHub Secrets:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_TO   (이메일 발송용)
  SLACK_WEBHOOK_URL                                          (슬랙 발송용)
  둘 중 한쪽 Secrets이 비어 있으면 해당 채널은 자동으로 건너뜁니다.
"""
import os, sys, io, json, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests

KST = timezone(timedelta(hours=9))

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "data")
CURR_FILE  = os.path.join(DATA_DIR, "indicators.json")
PREV_FILE  = os.path.join(DATA_DIR, "indicators_prev.json")

DASHBOARD_URL = "https://jkeehan54-ai.github.io/real-estate-news/realestate_dashboard.html"
NEWS_URL      = "https://jkeehan54-ai.github.io/real-estate-news/index.html"

# 지표별 "이 정도 바뀌면 알림 보낼 만하다" 기준값 + 표시 라벨/단위/포맷
# 임계값은 필요에 맞게 자유롭게 조정하세요.
FIELDS = {
    "verdict_score":  {"label": "종합판단",        "unit": "",  "fmt": "{:+.0f}", "th": 1},
    "kb_전국":         {"label": "KB 전국 매매가",   "unit": "%", "fmt": "{:+.2f}", "th": 0.05},
    "kb_서울":         {"label": "KB 서울 매매가",   "unit": "%", "fmt": "{:+.2f}", "th": 0.05},
    "kb_부산":         {"label": "KB 부산 매매가",   "unit": "%", "fmt": "{:+.2f}", "th": 0.05},
    "경매낙찰률":      {"label": "경매 낙찰률",      "unit": "%", "fmt": "{:.1f}",  "th": 1.0},
    "전세가율_전국":   {"label": "전세가율(전국)",   "unit": "%", "fmt": "{:.1f}",  "th": 1.0},
    "csi_주택전망":    {"label": "주택가격전망(CSI)", "unit": "", "fmt": "{:.1f}",  "th": 2.0},
    "매매수급지수":    {"label": "매매수급지수",     "unit": "",  "fmt": "{:.1f}",  "th": 2.0},
    "소비심리_매매":   {"label": "부동산소비심리",   "unit": "",  "fmt": "{:.1f}",  "th": 2.0},
    "미분양_전국":     {"label": "전국 미분양",      "unit": "호", "fmt": "{:,.0f}", "th": 2000},
    "거래량_전년비":   {"label": "거래량(전년비)",   "unit": "%", "fmt": "{:+.1f}", "th": 5.0},
    "착공량_전년비":   {"label": "착공량(전년비)",   "unit": "%", "fmt": "{:+.1f}", "th": 5.0},
    "준공량_전년비":   {"label": "준공량(전년비)",   "unit": "%", "fmt": "{:+.1f}", "th": 5.0},
}


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def diff_fields(prev, curr):
    """직전 대비 임계값 이상 바뀐 지표 목록 반환"""
    changes = []
    if not prev:
        return changes
    for key, meta in FIELDS.items():
        pv, cv = prev.get(key), curr.get(key)
        if pv is None or cv is None:
            continue
        if abs(cv - pv) >= meta["th"]:
            changes.append((meta["label"], pv, cv, meta["unit"], meta["fmt"]))
    return changes


def fmt_val(v, unit, fmt):
    try:
        return fmt.format(v) + unit
    except Exception:
        return str(v)


def build_daily_summary_text(curr):
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    lines = [f"🏠 부동산 경기 지표 일일 요약 ({now})", f"종합판단: {curr.get('verdict','—')}", ""]
    for key, meta in FIELDS.items():
        v = curr.get(key)
        lines.append(f"- {meta['label']}: {fmt_val(v, meta['unit'], meta['fmt']) if v is not None else '—'}")
    lines.append("")
    lines.append(f"대시보드: {DASHBOARD_URL}")
    lines.append(f"뉴스브리핑: {NEWS_URL}")
    return "\n".join(lines)


def build_change_alert_text(curr, changes):
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    lines = [f"⚡ 부동산 지표 변동 알림 ({now})", f"종합판단: {curr.get('verdict','—')}", ""]
    for label, pv, cv, unit, fmt in changes:
        lines.append(f"- {label}: {fmt_val(pv, unit, fmt)} → {fmt_val(cv, unit, fmt)}")
    lines.append("")
    lines.append(f"대시보드: {DASHBOARD_URL}")
    return "\n".join(lines)


def send_email(subject, body_text):
    host = os.environ.get("SMTP_HOST")
    port = os.environ.get("SMTP_PORT")
    user = os.environ.get("SMTP_USER")
    pw   = os.environ.get("SMTP_PASSWORD")
    to   = os.environ.get("EMAIL_TO")

    if not all([host, port, user, pw, to]):
        print("  [이메일] SMTP 관련 Secrets가 설정되지 않아 건너뜁니다.")
        return

    recipients = [x.strip() for x in to.split(",") if x.strip()]
    msg = MIMEMultipart()
    msg["From"] = user
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    try:
        with smtplib.SMTP(host, int(port), timeout=20) as server:
            server.starttls()
            server.login(user, pw)
            server.sendmail(user, recipients, msg.as_string())
        print(f"  [이메일] 발송 완료 → {recipients}")
    except Exception as e:
        print(f"  [이메일] 발송 실패: {e}")


def send_slack(text):
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        print("  [슬랙] SLACK_WEBHOOK_URL Secret이 설정되지 않아 건너뜁니다.")
        return
    try:
        resp = requests.post(url, json={"text": text}, timeout=10)
        if resp.status_code == 200:
            print("  [슬랙] 발송 완료")
        else:
            print(f"  [슬랙] 발송 실패: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        print(f"  [슬랙] 발송 실패: {e}")


def main():
    print("=" * 50)
    print("알림 발송 판단 시작")
    print("=" * 50)

    curr = load_json(CURR_FILE)
    if curr is None:
        print("현재 지표 파일이 없습니다. (realestate_dashboard.py가 먼저 실행되어야 함)")
        return

    prev = load_json(PREV_FILE)
    hour = datetime.now(KST).hour

    if hour == 8:
        print("08시 정기 실행 → 일일 요약 발송")
        text = build_daily_summary_text(curr)
        send_email("🏠 [부동산 대시보드] 오늘의 지표 요약", text)
        send_slack(text)
        return

    changes = diff_fields(prev, curr)
    if not changes:
        print(f"{hour}시 실행 → 직전 대비 유의미한 변화 없음. 알림 생략.")
        return

    print(f"{hour}시 실행 → {len(changes)}개 지표 변동 감지. 알림 발송.")
    text = build_change_alert_text(curr, changes)
    send_email("⚡ [부동산 대시보드] 지표 변동 알림", text)
    send_slack(text)


if __name__ == "__main__":
    main()
