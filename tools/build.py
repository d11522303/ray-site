# -*- coding: utf-8 -*-
"""
把 content/articles/ 裡的文章合併進 src/template.html，產生網站首頁 index.html。
後台每次存檔後，GitHub 會自動執行這支程式並更新網站。

本機執行：pip install pyyaml markdown 之後，python tools/build.py
"""
import glob, html, json, os, re
import markdown
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCK = re.compile(r"^\s*<(p|div|h[1-6]|figure|ul|ol|blockquote|table|section)\b", re.I)


def to_html(body):
    if BLOCK.match(body):  # 方格子匯入的文章本來就是 HTML
        return body
    # 把沒加連結的網址變成可點的連結
    body = re.sub(r'(?<![(<"\'=])(https?://[^\s<>()]+)', r"<\1>", body)
    return markdown.markdown(body, extensions=["nl2br", "sane_lists"])


def text_of(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def load():
    arts = []
    for path in sorted(glob.glob(os.path.join(ROOT, "content", "articles", "*.md"))):
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", raw, re.S)
        if not m:
            print("略過（格式不對）：", path)
            continue
        fm = yaml.safe_load(m.group(1)) or {}
        if not fm.get("published", True):
            continue
        body = to_html(m.group(2).strip())
        text = text_of(body)
        stem = os.path.splitext(os.path.basename(path))[0]
        arts.append({
            "id": re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem),
            "file": stem,
            "date": str(fm.get("date", ""))[:10],
            "title": str(fm.get("title", stem)),
            "cat": fm.get("category", "生活記憶"),
            "sub": str(fm.get("subcategory") or ""),
            "det": str(fm.get("detail") or ""),
            "src": fm.get("source", ""),
            "url": fm.get("source_url", ""),
            "ex": str(fm.get("excerpt") or text[:90]),
            "len": len(re.sub(r"\s", "", text)),
            "body": body,
        })
    arts.sort(key=lambda a: a["date"], reverse=True)
    return arts


def main():
    arts = load()
    with open(os.path.join(ROOT, "src", "template.html"), encoding="utf-8") as f:
        tpl = f.read()
    data = json.dumps(arts, ensure_ascii=False).replace("</", "<\\/")
    home = {}
    hp = os.path.join(ROOT, "content", "home.yml")
    if os.path.exists(hp):
        with open(hp, encoding="utf-8") as f:
            home = yaml.safe_load(f) or {}
    tpl = tpl.replace("__HOME__", json.dumps(home, ensure_ascii=False).replace("</", "<\\/"))
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(tpl.replace("__DATA__", data))
    cats = {}
    for a in arts:
        cats[a["cat"]] = cats.get(a["cat"], 0) + 1
    print(f"完成：index.html 公開 {len(arts)} 篇 {cats}")


if __name__ == "__main__":
    main()
