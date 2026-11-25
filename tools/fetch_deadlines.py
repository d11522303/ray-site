"""抓取醒吾旅運系實習公告的截止日，寫成 date-calculator/deadlines.json。

要追蹤的公告寫在 date-calculator/sources.json。
抓不到或解析不到任何截止日時，保留原本的 deadlines.json，不會清空。
"""
import datetime as dt
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "date-calculator"
SOURCES = DIR / "sources.json"
OUT = DIR / "deadlines.json"
TW = dt.timezone(dt.timedelta(hours=8))

# 例：(已截止) 11/02星期一前 EVA AIR 長榮航空 實習招募
LINE = re.compile(
    r"(?P<closed>[（(]\s*已截止\s*[)）])?\s*"
    r"(?P<m>\d{1,2})\s*/\s*(?P<d>\d{1,2})\s*(?:\(|（)?\s*(?:星期|週|周)[一二三四五六日天](?:\)|）)?\s*前?\s*"
    r"(?P<name>[^\n]{1,40}?)\s*實習(?:生)?招募"
)


def page_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|nav|header|footer)\b.*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</(p|div|li|h\d|tr|td)>", "\n", raw)
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw)).replace("\xa0", " ")
    return "\n".join(re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines())


def page_title(raw: str) -> str:
    m = re.search(r'(?i)<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', raw)
    return html.unescape(m.group(1)).strip() if m else ""


def parse(raw: str, today: dt.date):
    text = page_text(raw)
    roc = re.search(r"(1\d\d)\s*年", text)
    base_year = int(roc.group(1)) + 1911 if roc else today.year
    items, seen = [], set()
    for m in LINE.finditer(text):
        month, day = int(m["m"]), int(m["d"])
        name = m["name"].strip(" ：:-")
        year = base_year
        # 學年跨年：公告寫 12 月前後的 1～7 月截止日，多半是下一年
        if roc is None and month < today.month - 6:
            year += 1
        try:
            date = dt.date(year, month, day)
        except ValueError:
            continue
        key = (name, date)
        if not name or key in seen:
            continue
        seen.add(key)
        items.append({"name": name, "date": date.isoformat(), "closed": bool(m["closed"])})
    return page_title(raw), items


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (deadline tracker)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode(r.headers.get_content_charset() or "utf-8", "replace")


def main() -> int:
    today = dt.datetime.now(TW).date()
    sources = json.loads(SOURCES.read_text("utf-8"))
    old = json.loads(OUT.read_text("utf-8")) if OUT.exists() else {"groups": []}
    old_by_url = {g["url"]: g for g in old.get("groups", [])}
    groups, ok = [], 0
    for src in sources:
        url = src["url"]
        try:
            title, items = parse(fetch(url), today)
        except Exception as e:  # 網站暫時連不上就沿用上次的資料
            print(f"抓取失敗 {url}: {e}", file=sys.stderr)
            title, items = "", []
        if items:
            ok += 1
            groups.append({"title": src.get("title") or title, "url": url, "items": items})
            print(f"{title or url}: {len(items)} 筆")
        elif url in old_by_url:
            groups.append(old_by_url[url])
            print(f"沿用舊資料 {url}", file=sys.stderr)
    if not ok:
        print("沒有抓到任何截止日，保留原本的 deadlines.json", file=sys.stderr)
        return 0
    data = {"updated": dt.datetime.now(TW).isoformat(timespec="minutes"), "groups": groups}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
