"""키이스케이프 빈자리 알림. 실행 한 번에 한 번 확인하고, 자리가 있으면 ntfy로 푸시한다."""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://www.keyescape.com/controller/run_proc.php"
BOOK_URL = "https://www.keyescape.com/reservation1.php?zizum_num=16&theme_num=56&theme_info_num=33"
ZIZUM, THEME = "16", "56"  # 우주라이크점 WANNA GO HOME
DATE = "2026-11-08"
WANT = "16:00"
KST = timezone(timedelta(hours=9))
STOP = datetime(2026, 11, 8, 16, 0, tzinfo=KST)


def open_slots(res):
    """API 응답에서 원하는 타임이 예약 가능하면 돌려준다. 조회 실패나 마감이면 빈 목록."""
    if not res.get("status"):
        return []
    times = (f"{s['hh']}:{s['mm']}" for s in res["data"] if s["enable"] != "N")
    return [t for t in times if t == WANT]


def fetch():
    body = urllib.parse.urlencode(
        {"t": "get_theme_time", "date": DATE, "zizumNum": ZIZUM, "themeNum": THEME}
    ).encode()
    with urllib.request.urlopen(API, body, timeout=20) as r:
        return json.load(r)


def push(topic, slots):
    req = urllib.request.Request(
        f"https://ntfy.sh/{topic}",
        data=f"{DATE} {', '.join(slots)} 예약 가능".encode(),
        headers={"Click": BOOK_URL, "Priority": "urgent", "Title": "WANNA GO HOME slot open"},
    )
    urllib.request.urlopen(req, timeout=20).close()


def main():
    now = datetime.now(KST)
    if now > STOP:
        print("watch ended")
        return
    slots = open_slots(fetch())
    print(now.isoformat(), slots)
    if slots:
        push(os.environ["NTFY_TOPIC"], slots)


def test():
    slot = lambda h, m, e: {"hh": h, "mm": m, "enable": e}
    assert open_slots({"status": False, "msg": "x"}) == []
    assert open_slots({"status": True, "data": [slot("16", "00", "N")]}) == []
    assert open_slots({"status": True, "data": [slot("10", "00", "Y"), slot("22", "00", "Y")]}) == []
    assert open_slots({"status": True, "data": [slot("10", "00", "Y"), slot("16", "00", "Y")]}) == ["16:00"]


if __name__ == "__main__":
    test() if "--test" in sys.argv else main()
