# -*- coding: utf-8 -*-
"""
把 Facebook 匯出檔裡的新貼文加進網站（content/articles/）。
已經存在的文章不會被覆蓋，所以在後台改過的標題、分類不會不見。

用法：
    python tools/import_facebook.py 你的FB匯出檔.json
    python tools/import_facebook.py 匯出檔.json --min 300

匯出檔是 Facebook「下載你的資訊」選 JSON 格式後，
在 your_facebook_activity/posts/ 裡的 your_posts__check_ins__photos_and_videos_1.json。
（有多個檔就一起放上來：python tools/import_facebook.py 檔1.json 檔2.json）

規則：
- 只收字數 >= --min（預設 300）的貼文。
- 和方格子同一篇（標題相同）的會自動略過。
- 新加入的文章預設「不公開」，請到後台檢查分類後再打開「公開」。
"""
import argparse, glob, json, os, re, sys
import yaml
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TW = timezone(timedelta(hours=8))
PROFILE = "https://www.facebook.com/chenrayfong"

RULES = [
    ("證照考試", r"EP\s*\d|領隊|導遊|國考|考試"),
    ("遊戲學習", r"遊戲|MEG|桌遊|解謎"),
    ("旅行郵輪", r"郵輪|公主號|遊輪"),
    ("理財情報", r"保險|保單|理財|投資|財務"),
    ("老後提案", r"長照|照護|看護|醫生|復健|退休"),
    ("每日晨讀", r"晨讀|論文|期刊|讀書|書中|這本書|博士"),
    ("技職教育", r"實習|學生|課程|導師|教學|旅運系|醒吾"),
    ("旅行郵輪", r"旅行|旅遊|溫哥華|加拿大|日本|泰國|機場|航空|出國|旅展|飯店"),
]


def fix(s):
    """Facebook 匯出的中文是亂碼（latin-1 包 UTF-8），轉回正常文字。"""
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def category(text):
    head = text[:400]
    for cat, pat in RULES:
        if re.search(pat, head):
            return cat
    return "生活記憶"


def make_title(text):
    lines = [x.strip() for x in text.split("\n") if x.strip()]
    for line in lines:
        t = re.sub(r"^(\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}\s*(\([^)]*\))?|\d+/\d+)\s*", "", line).strip(" #")
        if len(t) >= 4:
            return t[:28] + "…" if len(t) > 28 else t
    return lines[0][:28]


def norm(s):
    return re.sub(r"[\s\W_]+", "", s)


def existing():
    ids, titles = set(), []
    for path in glob.glob(os.path.join(ROOT, "content", "articles", "*.md")):
        stem = os.path.splitext(os.path.basename(path))[0]
        ids.add(re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem))
        with open(path, encoding="utf-8") as f:
            m = re.match(r"^---\s*\n(.*?)\n---", f.read(), re.S)
        if m:
            fm = yaml.safe_load(m.group(1)) or {}
            if fm.get("source") == "方格子":
                titles.append(norm(str(fm.get("title", "")))[:10])
    return ids, titles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="Facebook 匯出的 JSON 檔")
    ap.add_argument("--min", type=int, default=300, help="最少字數（預設 300）")
    args = ap.parse_args()

    posts = []
    for fn in args.files:
        with open(fn, encoding="utf-8") as f:
            posts += json.load(f)

    have, vocus_titles = existing()
    added = 0
    for p in posts:
        text = "\n".join(fix(d["post"]) for d in p.get("data", []) if d.get("post")).strip()
        if len(text) < args.min:
            continue
        ts = p.get("timestamp", 0)
        aid = f"f{ts}"
        if aid in have:
            continue
        have.add(aid)
        if any(v and v in norm(text[:600]) for v in vocus_titles):
            continue
        date = datetime.fromtimestamp(ts, TW).strftime("%Y-%m-%d")
        fm = {"title": make_title(text), "date": date, "category": category(text),
              "source": "Facebook", "source_url": PROFILE, "published": False,
              "note": "新匯入，請檢查後再公開"}
        body = "\n\n".join(x.strip() for x in text.split("\n") if x.strip())
        with open(os.path.join(ROOT, "content", "articles", f"{date}-{aid}.md"), "w", encoding="utf-8") as f:
            f.write("---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, width=1000) + "---\n\n" + body + "\n")
        added += 1
    print(f"完成：新增 {added} 篇到 content/articles/（預設不公開）")


if __name__ == "__main__":
    main()
