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
            "cats": list(dict.fromkeys([fm.get("category", "生活記憶")] + [c for c in (fm.get("also") or []) if c in CATS])),
            "sub": str(fm.get("subcategory") or ""),
            "det": str(fm.get("detail") or ""),
            "src": fm.get("source", ""),
            "url": fm.get("source_url", ""),
            "ex": str(fm.get("excerpt") or text[:90]),
            "len": len(re.sub(r"\s", "", text)),
            "body": body,
            "cover": str(fm.get("cover") or ""),
            "photos": [{"src": str(x.get("image")), "cap": str(x.get("caption") or "")}
                       for x in (fm.get("photos") or []) if isinstance(x, dict) and x.get("image")],
        })
    arts.sort(key=lambda a: a["date"], reverse=True)
    return arts


def read_yml(*parts):
    p = os.path.join(ROOT, *parts)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def prep_about(about):
    about = dict(about)
    md = lambda t: markdown.markdown(str(t or ""), extensions=["nl2br", "sane_lists"])
    about["body"] = md(about.get("body"))
    about["boxes"] = [{"title": str(b.get("title") or ""), "text": md(b.get("text"))}
                      for b in (about.get("boxes") or []) if isinstance(b, dict)]
    return about


def js(o):
    return json.dumps(o, ensure_ascii=False).replace("</", "<\\/")


def render(tpl, arts, home, about, out):
    tpl = tpl.replace("__HOME__", js(home)).replace("__ABOUT__", js(prep_about(about)))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(tpl.replace("__DATA__", js(arts)))


def english(arts, tpl):
    """英文版：content/en/ 裡有翻譯的文章才會出現；介面文字照 tools/ui_en.yml 替換。"""
    tax = read_yml("content", "en", "taxonomy.yml")
    t = lambda v: tax.get(v, v) if v else v
    out = []
    for a in arts:
        p = os.path.join(ROOT, "content", "en", "articles", a["file"] + ".md")
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            raw = f.read()
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", raw, re.S)
        if not m:
            print("略過英文（格式不對）：", p)
            continue
        fm = yaml.safe_load(m.group(1)) or {}
        if not fm.get("published", True):
            continue
        body = to_html(m.group(2).strip())
        text = text_of(body)
        out.append(dict(a, title=str(fm.get("title") or a["title"]), ex=str(fm.get("excerpt") or text[:160]),
                        body=body, len=len(text.split()), cat=t(a["cat"]), cats=[t(c) for c in a["cats"]], sub=t(a["sub"]), det=t(a["det"]),
                        zt=a["title"]))
    pairs = yaml.safe_load(open(os.path.join(ROOT, "tools", "ui_en.yml"), encoding="utf-8")) or []
    pairs += [[f'"{k}"', f'"{v}"'] for k, v in tax.items() if k in CATS] + [[f"'{k}'", f"'{v}'"] for k, v in tax.items() if k in CATS]
    for zh, en in sorted(pairs, key=lambda x: -len(x[0])):
        if zh not in tpl and not zh.strip("'\"") in CATS:
            print("英文介面：模板裡找不到", zh[:40])
        tpl = tpl.replace(zh, en)
    tpl = tpl.replace("a.title.includes(H.series_keyword)", "(a.zt||a.title).includes(H.series_keyword)")
    home = read_yml("content", "en", "home.yml")
    about = read_yml("content", "en", "about.yml")
    if home.get("series_category"):
        home["series_category"] = t(home["series_category"])
    render(tpl, out, home, about, os.path.join(ROOT, "en", "index.html"))
    return out


CATS = ["證照考試", "技職教育", "旅行郵輪", "每日晨讀", "遊戲學習", "生活記憶", "理財情報", "老後提案"]


def main():
    arts = load()
    with open(os.path.join(ROOT, "src", "template.html"), encoding="utf-8") as f:
        tpl = f.read()
    render(tpl, arts, read_yml("content", "home.yml"), read_yml("content", "about.yml"), os.path.join(ROOT, "index.html"))
    en = english(arts, tpl)
    cats = {}
    for a in arts:
        cats[a["cat"]] = cats.get(a["cat"], 0) + 1
    print(f"完成：index.html 公開 {len(arts)} 篇 {cats}；英文版 en/index.html {len(en)} 篇")


if __name__ == "__main__":
    main()
