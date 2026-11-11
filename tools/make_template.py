"""出張旅費伝票のテンプレートPDFを 素材/出張旅費伝票.svg から作り直すスクリプト。

使い方（支払伝票PJ フォルダで）:
    python travel-slip-app/tools/make_template.py
出力:
    travel-slip-app/tools/out/ryohi_tpl.pdf … テンプレートPDF（A5横 595.32×419.52pt）
    travel-slip-app/tools/out/ryohi_tpl.b64 … 出張旅費伝票.html の TEMPLATE_B64 に貼る文字列
必要: Python + playwright（Chrome） + pymupdf

SVG（Inkscape製）は最初からA5（210×148mm、viewBox は y を0.5mmずらした範囲）なので、
フォーム座標 793.76×559.36px で描画して Chrome で印刷し PDF にする（入金伝票と違い「経理部」も入っている）。
Chrome の PDF は 594.96×420pt になるため、MediaBox を上端基準で 595.32×419.52pt に合わせる。
HTML内の座標（フォーム座標）は、このページを 793.76×559.36 とした値（1単位=0.75pt）。
印字範囲（HTMLの SLIP_CONTENT）は 25.2–582.0 × 10.8–407.5pt（288dpiで画像化して実測）。
"""
import os, re, base64
from playwright.sync_api import sync_playwright
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
PJ = os.path.abspath(os.path.join(HERE, "..", ".."))
SVG = os.path.join(PJ, "素材", "出張旅費伝票.svg")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
W_PX, H_PX = 793.76, 559.36

t = open(SVG, encoding="utf-8").read()
t, n = re.subn(r'width="210mm"(\s+)height="148mm"', f'width="{W_PX}px"\\1height="{H_PX}px" preserveAspectRatio="none"', t, count=1)
assert n == 1, "SVGの先頭(width/height)が想定と違います"
html_path = os.path.join(OUT, "tpl.html")
open(html_path, "w", encoding="utf-8").write(
    '<!doctype html><html><head><meta charset="utf-8"><style>@page{size:595.32pt 419.52pt;margin:0}'
    'html,body{margin:0;padding:0}svg{display:block}</style></head><body>' + t[t.index('<svg'):] + '</body></html>')
raw_pdf = os.path.join(OUT, "raw.pdf")
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    pg = b.new_page()
    pg.goto("file:///" + html_path.replace("\\", "/"))
    pg.pdf(path=raw_pdf, prefer_css_page_size=True, print_background=True,
           margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
    b.close()
d = pymupdf.open(raw_pdf)
page = d[0]
x0, y0, x1, y1 = page.mediabox
d.xref_set_key(page.xref, "MediaBox", f"[0 {y1 - 419.52:.2f} 595.32 {y1:.2f}]")
out_pdf = os.path.join(OUT, "ryohi_tpl.pdf")
d.save(out_pdf, garbage=4, deflate=True)
open(os.path.join(OUT, "ryohi_tpl.b64"), "w").write(base64.b64encode(open(out_pdf, "rb").read()).decode())
print("ok", pymupdf.open(out_pdf)[0].rect)
