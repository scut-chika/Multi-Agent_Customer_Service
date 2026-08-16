# -*- coding: utf-8 -*-
"""将 docs 下的三篇参赛文档渲染为排版好的 HTML（供 Chrome headless 打印为 PDF）。"""
import markdown
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = ROOT / "pdf" / "_html"

FILES = ["作品简介.md", "Agent-Identity清单.md", "Skill清单.md"]

CSS = """
@page { size: A4; margin: 16mm 14mm 16mm 14mm; }
* { box-sizing: border-box; }
body { font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif;
       font-size: 10.5pt; line-height: 1.7; color: #1f2937; margin: 0; }
h1 { font-size: 20pt; color: #0e2a47; border-bottom: 2.5pt solid #0ea5a4;
     padding-bottom: 6pt; margin: 0 0 14pt; }
h2 { font-size: 14pt; color: #0e2a47; margin: 18pt 0 8pt;
     border-left: 4pt solid #0ea5a4; padding-left: 8pt; }
h3 { font-size: 12pt; color: #0e2a47; margin: 14pt 0 6pt; }
p { margin: 6pt 0; }
strong { color: #0e2a47; }
blockquote { margin: 8pt 0; padding: 6pt 10pt; background: #f0f9f8;
             border-left: 3pt solid #0ea5a4; color: #475569; border-radius: 2pt; }
table { width: 100%; border-collapse: collapse; margin: 10pt 0;
        table-layout: fixed; font-size: 8pt; }
th, td { border: 0.6pt solid #cbd5e1; padding: 5pt 6pt; vertical-align: top;
         word-break: break-word; }
th { background: #0e2a47; color: #ffffff; font-weight: bold; }
tr:nth-child(even) td { background: #f8fafc; }
code { font-family: Consolas, "Courier New", monospace; background: #f1f5f9;
       padding: 1pt 3pt; border-radius: 2pt; font-size: 90%; color: #0f766e; }
pre { background: #f1f5f9; border: 0.6pt solid #e2e8f0; border-radius: 4pt;
      padding: 8pt 10pt; white-space: pre; overflow-wrap: normal;
      font-family: Consolas, "Courier New", monospace; font-size: 8pt; line-height: 1.4; }
ul, ol { margin: 6pt 0 6pt 18pt; padding: 0; }
li { margin: 3pt 0; }
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        src = (DOCS / name).read_text(encoding="utf-8")
        body = markdown.markdown(src, extensions=["tables", "fenced_code", "sane_lists"])
        html = (
            "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"utf-8\">\n"
            f"<title>{Path(name).stem}</title>\n<style>{CSS}</style>\n</head>\n<body>\n"
            f"{body}\n</body>\n</html>\n"
        )
        out = OUT / (Path(name).stem + ".html")
        out.write_text(html, encoding="utf-8")
        print("HTML generated:", out)
    print("done")


if __name__ == "__main__":
    main()
