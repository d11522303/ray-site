# -*- coding: utf-8 -*-
"""
把 content/articles/ 裡的文章合併進 src/template.html，產生網站：
  index.html     中文版（網站首頁，打開先看 HELLO 關於頁）
  en/index.html  英文版
中文版看中文文章的「公開」，英文版看英文翻譯的「在英文版公開」，兩邊各自獨立。
還沒有英文翻譯的文章，只有在中文公開時才會在英文版顯示（先顯示中文）。
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
        body = to_html(m.group(2).strip())
        text = text_of(body)
        stem = os.path.splitext(os.path.basename(path))[0]
        arts.append({
            "pub": bool(fm.get("published", True)),
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


LANG_LINK = {
    "zh": '<a href="en/" class="lang hand" data-lang="1" title="English version">EN</a>',
    "en": '<a href="../" class="lang hand" data-lang="1" title="中文版">中文</a>',
}


def render(tpl, arts, home, about, out, base, lang, switch=True):
    # 內文裡從後台插入的圖片是 /images/...，改成相對路徑，網站放在子路徑（例如 /ray-site/en/）也看得到
    fix = lambda h: re.sub(r'(src|href)="/(images/)', r'\1="' + base + r'\2', h)
    arts = [dict(a, body=fix(a["body"])) for a in arts]
    about = prep_about(about)
    about = dict(about, body=fix(about["body"]), boxes=[dict(b, text=fix(b["text"])) for b in about["boxes"]])
    head = ('<!doctype html>\n<html lang="%s">\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            '<link rel="alternate" hreflang="zh-Hant" href="%s">\n<link rel="alternate" hreflang="en" href="%sen/">\n'
            % ("en" if lang == "en" else "zh-Hant", base or "./", base or ""))
    tpl = head + tpl.replace("<!--EN-->", LANG_LINK[lang] if switch else "").replace("__BASE__", base).replace("__START__", "hello" if lang == "zh" else "home")
    tpl = tpl.replace("__HOME__", js(home)).replace("__ABOUT__", js(about))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(tpl.replace("__DATA__", js(arts)))


def english(arts, tpl, zh_home, switch):
    """英文版：用 content/en/ 裡的翻譯；還沒翻譯的文章先用中文顯示並加註。介面文字照 tools/ui_en.yml 替換。"""
    tax = read_yml("content", "en", "taxonomy.yml")
    t = lambda v: tax.get(v, v) if v else v
    out = []
    for a in arts:
        p = os.path.join(ROOT, "content", "en", "articles", a["file"] + ".md")
        if not os.path.exists(p):
            if not a["pub"]:
                continue
            out.append(dict(a, untr=True, len=a["len"] // 2, cat=t(a["cat"]), cats=[t(c) for c in a["cats"]], sub=t(a["sub"]), det=t(a["det"]), zt=a["title"]))
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
    for k in ("hero_image", "hero_alt"):  # 首頁照片兩種語言共用，在中文「首頁文字」上傳
        if not home.get(k):
            home[k] = zh_home.get(k, "")
    if home.get("series_category"):
        home["series_category"] = t(home["series_category"])
    render(tpl, out, home, about, os.path.join(ROOT, "en", "index.html"), "../", "en", switch)
    return out


CATS = ["證照考試", "技職教育", "旅行郵輪", "每日晨讀", "遊戲學習", "生活記憶", "理財情報", "老後提案"]


def main():
    all_arts = load()
    arts = [a for a in all_arts if a["pub"]]
    with open(os.path.join(ROOT, "src", "template.html"), encoding="utf-8") as f:
        tpl = f.read()
    zh_home = read_yml("content", "home.yml")
    render(tpl, arts, zh_home, read_yml("content", "about.yml"), os.path.join(ROOT, "index.html"), "", "zh")
    en = english(all_arts, tpl, zh_home, switch=True)
    cats = {}
    for a in arts:
        cats[a["cat"]] = cats.get(a["cat"], 0) + 1
    untr = sum(1 for a in en if a.get("untr"))
    print(f"完成：中文版 index.html 公開 {len(arts)} 篇 {cats}；英文版 en/index.html {len(en)} 篇（其中 {untr} 篇還沒翻譯，先顯示中文）")


if __name__ == "__main__":
    main()
