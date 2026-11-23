"""
iOSクイックルック完全対応 インタラクティブPDF（study_quicklook.pdf）生成スクリプト
- スマホ縦画面サイズ（110mm × 175mm）
- 表紙目次（6教科へタップでジャンプ）＋全677問（問題ページ → タップで答えページ → 次の問題へ）
- 美術絵画87枚・音楽カラー楽器写真24種＆楽譜・家庭科SVGマーク15種＆三者間契約図解をすべて鮮明に埋め込み
"""
import base64
import json
import os
import re
import subprocess
import sys

WORK_DIR = r"C:\Users\ytouw\.gemini\antigravity\scratch\kateika-flashcards"
CROP_DIR = r"C:\Users\ytouw\.gemini\antigravity\brain\0a7e6c3c-42b7-4101-a5c9-b19506fdd07e\scratch\extracted_hoken\crops"
SCRATCH_DIR = r"C:\Users\ytouw\.gemini\antigravity\brain\0a7e6c3c-42b7-4101-a5c9-b19506fdd07e\scratch"

if WORK_DIR not in sys.path:
    sys.path.insert(0, WORK_DIR)
from build_quicklook import esc, fmt_q, fmt_solved, parse_marks_from_js, credit_diagram_svg


def load_all_subjects():
    # 1. 美術
    with open(os.path.join(WORK_DIR, "art_source.html"), encoding="utf-8") as f:
        m_art = re.search(r"const ALL=(\[.*?\]);", f.read())
    raw_art = json.loads(m_art.group(1))
    art_cards = []
    for c in raw_art:
        if c.get("k") == "w":
            r = c.get("r", "")
            art_cards.append({
                "id": "art:" + c["id"], "subj": "art", "unit": c.get("m") or f"{r}の作品",
                "note": f"美術・{r}", "type": "art-work", "img": c["img"],
                "t": c.get("t", ""), "a": c.get("a", ""), "y": c.get("y", ""), "m": c.get("m", ""), "r": r,
            })
        else:
            art_cards.append({
                "id": "art:" + c["id"], "subj": "art", "unit": "美術 穴埋め",
                "note": f"教科書 {c.get('src', '')}".strip(), "type": "art-cloze",
                "q": c["q"].replace("［　］", "［ ？ ］"), "a": c["ans"],
            })

    # 2. 家庭科 + SVGマーク
    with open(os.path.join(WORK_DIR, "kateika_only.html"), encoding="utf-8") as f:
        k_html = f.read()
    m_marks = re.search(r"(// 商品選択に役立つ表示マーク[\s\S]*?^// 全149問のフラッシュカードデータ)", k_html, re.M)
    marks_map = parse_marks_from_js(m_marks.group(1))
    m_kcards = re.search(r"const CARDS = \[\s*([\s\S]*?)\n\];", k_html)
    kcards_js = re.sub(r'(\{id:"[^"]+",)', r'\1subj:"home",', m_kcards.group(1))
    clean = re.sub(r'^\s*//.*$', '', kcards_js, flags=re.M)
    clean = re.sub(r'([{,\s])([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', clean)
    home_cards = json.loads("[" + clean + "]")
    home_cards.extend([
        {
            "id": "p7-all-rights", "subj": "home", "unit": "8つの権利", "note": "ノート7 まとめ",
            "type": "list", "a": "消費者の8つの権利",
            "q": "国際消費者機構が挙げた【消費者の8つの権利】をすべて答えなさい。",
            "items": [
                "安全を求める権利", "意見が反映される権利", "選択する権利", "知らされる権利",
                "補償を受ける権利", "消費者教育を受ける権利", "生活の基本的ニーズが保障される権利", "健全な環境を享受する権利",
            ],
        },
        {
            "id": "p7-all-resp", "subj": "home", "unit": "5つの責任", "note": "ノート7 まとめ",
            "type": "list", "a": "消費者の5つの責任",
            "q": "国際消費者機構が挙げた【消費者の5つの責任】をすべて答えなさい。",
            "items": [
                "批判的意識を持つ責任", "主張し、行動する責任", "連帯する責任",
                "環境への配慮をする責任", "社会的弱者に配慮する責任",
            ],
        },
    ])

    # 3. 体育・音楽・保健・社会
    with open(os.path.join(WORK_DIR, "data_pe.json"), encoding="utf-8") as f:
        pe_cards = json.load(f)
    with open(os.path.join(WORK_DIR, "data_music.json"), encoding="utf-8") as f:
        music_cards = json.load(f)
    with open(os.path.join(WORK_DIR, "data_health.json"), encoding="utf-8") as f:
        health_cards = json.load(f)
    with open(os.path.join(WORK_DIR, "data_social.json"), encoding="utf-8") as f:
        social_cards = json.load(f)

    # 4. 音楽画像
    photo_dir = os.path.join(WORK_DIR, "music_photos")
    music_imgs = {}
    for fn in sorted(os.listdir(CROP_DIR)):
        if fn.endswith(".jpg") and not fn.startswith("_"):
            key = os.path.splitext(fn)[0]
            sp = os.path.join(photo_dir, fn) if os.path.exists(os.path.join(photo_dir, fn)) else os.path.join(CROP_DIR, fn)
            with open(sp, "rb") as f:
                music_imgs[key] = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("ascii")

    subjects = [
        ("art", "美術", "#7b4fb0", "日本の作品・西洋の作品・穴埋め", art_cards),
        ("home", "家庭科", "#c06c2b", "消費者・クレカ・マーク15種・8つの権利と5つの責任", home_cards),
        ("pe", "体育", "#2574a9", "水泳・器械運動・陸上・ハンドボール・卓球", pe_cards),
        ("music", "音楽", "#b83b6e", "世界の民族楽器24種・タンソ/ウード/タブラー・帰れソレントへ", music_cards),
        ("health", "保健", "#2e8b57", "感染症・食中毒・性感染症・エイズ・社会の取組と医薬品", health_cards),
        ("social", "社会", "#a67c00", "歴史：明治維新〜第一次世界大戦と民族独立の動き", social_cards),
    ]
    return subjects, marks_map, music_imgs


def render_pdf_html():
    subjects, marks_map, music_imgs = load_all_subjects()
    total_all = sum(len(cards) for _, _, _, _, cards in subjects)

    # 表紙＋目次ページ
    toc_links = "".join(
        f'<a class="toc-btn" href="#q-{sk}-1">'
        f'<span class="sbadge" style="background:{col}">{esc(label)}</span>'
        f'<span class="toc-main"><b>{esc(label)}（{len(cards)}問）</b><small>{esc(desc)}</small></span>'
        f'<span class="toc-go">→</span></a>'
        for sk, label, col, desc, cards in subjects
    )

    pages = [
        f'<section class="page toc-page" id="toc">'
        f'<div class="toc-hd"><h1>6教科テスト対策<br>フラッシュカード</h1>'
        f'<p class="toc-sub">全{total_all}問｜iOSクイックルック対応PDF（タップ移動OK）</p></div>'
        f'<div class="toc-list">{toc_links}</div>'
        f'<p class="toc-tip">教科をタップでジャンプ。問題ページの「答えを見る →」をタップ（または次ページへスワイプ）で解答確認できます。</p>'
        f'</section>'
    ]

    for s_idx, (sk, label, col, _, cards) in enumerate(subjects):
        n = len(cards)
        next_subj_id = f"q-{subjects[s_idx + 1][0]}-1" if s_idx + 1 < len(subjects) else "toc"
        for idx, c in enumerate(cards, 1):
            qid = f"q-{sk}-{idx}"
            aid = f"a-{sk}-{idx}"
            prev_q = f"q-{sk}-{idx - 1}" if idx > 1 else "toc"
            next_q = f"q-{sk}-{idx + 1}" if idx < n else next_subj_id
            next_lbl = "次の問題 →" if idx < n else ("次の教科へ →" if s_idx + 1 < len(subjects) else "目次へ戻る")

            ctype = c["type"]
            q_body = ""
            a_body = ""

            if ctype == "art-work":
                q_body = f'<img class="hero" src="{c["img"]}" alt="">'
                tags = f'<span class="tag r">{esc(c.get("r", ""))}</span>'
                if c.get("m"):
                    tags += f'<span class="tag">{esc(c["m"])}</span>'
                a_body = (
                    f'<p class="t">{esc(c.get("t", ""))}</p>'
                    f'<p class="a">{esc(c.get("a", ""))}</p>'
                    f'<p class="y">{esc(c.get("y", ""))}</p>'
                    f'<div>{tags}</div>'
                )
            elif ctype == "photo":
                src = music_imgs[c["imgKey"]]
                q_body = f'<img class="hero" src="{src}" alt=""><div class="region">地域：{esc(c.get("r", ""))}</div>'
                a_body = (
                    f'<p class="t">{esc(c["a"])}</p>'
                    f'<div><span class="tag r">{esc(c.get("r", ""))}</span><span class="tag">{esc(c.get("unit", ""))}</span></div>'
                    f'<p class="y">{esc(c.get("note", ""))}</p>'
                )
            elif ctype == "mark":
                svg = marks_map.get(c["mark"], "")
                q_body = f'<div class="mark-box">{svg}</div>'
                a_body = (
                    f'<p class="t">{esc(c["a"])}</p>'
                    f'<p class="a">{esc(c.get("desc", ""))}</p>'
                    f'<div><span class="tag">{esc(c.get("unit", ""))}</span></div>'
                    f'<p class="y">{esc(c.get("note", ""))}</p>'
                )
            elif ctype == "diagram":
                q_body = f'<div class="diag-box">{credit_diagram_svg(c["slot"], False)}</div><div class="q">{fmt_q(c["q"])}</div>'
                a_body = (
                    f'<div class="ans">{esc(c["a"])}</div>'
                    f'<p class="q-sub">{fmt_solved(c["q"], c["a"])}</p>'
                    f'<div class="diag-box mini">{credit_diagram_svg(c["slot"], True)}</div>'
                    f'<p class="y">{esc(c.get("note", ""))}</p>'
                )
            elif ctype == "list":
                q_body = f'<div class="q">{esc(c["q"])}</div>'
                lis = "".join(f"<li>{esc(it)}</li>" for it in c["items"])
                a_body = f'<div class="ans" style="font-size:15pt">{esc(c["a"])}</div><ol class="ans-list">{lis}</ol>'
            else:
                img_part = ""
                if c.get("imgKey") and c["imgKey"] in music_imgs:
                    img_part = f'<img class="fig" src="{music_imgs[c["imgKey"]]}" alt="">'
                q_body = f'{img_part}<div class="q">{fmt_q(c["q"])}</div>'
                a_body = (
                    f'<div class="ans">{esc(c["a"])}</div>'
                    f'<p class="q-sub">{fmt_solved(c["q"], c["a"])}</p>'
                    f'<div><span class="tag">{esc(c.get("unit", ""))}</span></div>'
                    f'<p class="y">{esc(c.get("note", ""))}</p>'
                )

            hdr_q = (
                f'<div class="top">'
                f'<span><span class="sbadge" style="background:{col}">{esc(label)}</span>'
                f'<span class="pos">{idx} / {n}</span></span>'
                f'<a class="toc-mini" href="#toc">目次</a></div>'
            )
            hdr_a = (
                f'<div class="top">'
                f'<span><span class="sbadge" style="background:{col}">{esc(label)}・解答</span>'
                f'<span class="pos">{idx} / {n}</span></span>'
                f'<a class="toc-mini" href="#toc">目次</a></div>'
            )

            # 問題ページ
            pages.append(
                f'<section class="page" id="{qid}">{hdr_q}'
                f'<div class="card"><div class="unit-lbl">{esc(c.get("unit", "")) if ctype != "art-work" else "美術作品"}</div>{q_body}</div>'
                f'<div class="bot">'
                f'<a class="btn-sub" href="#{prev_q}">← 前</a>'
                f'<a class="btn-main" href="#{aid}">答えを見る →</a>'
                f'</div></section>'
            )
            # 解答ページ
            pages.append(
                f'<section class="page" id="{aid}">{hdr_a}'
                f'<div class="card ans-card">{a_body}</div>'
                f'<div class="bot">'
                f'<a class="btn-sub" href="#{qid}">← 問題へ</a>'
                f'<a class="btn-ok" href="#{next_q}">{next_lbl}</a>'
                f'</div></section>'
            )

    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>6教科テスト対策フラッシュカード（PDF版）</title>
<style>
@page {{ size: 110mm 175mm; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #f6f3ee; color: #222; font-family: "Yu Gothic UI", "Meiryo", "Hiragino Sans", sans-serif; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.page {{ width: 110mm; height: 175mm; padding: 7mm 6mm 6mm; display: flex; flex-direction: column; justify-content: space-between; page-break-after: always; break-after: page; overflow: hidden; background: #f6f3ee; }}
.top {{ display: flex; justify-content: space-between; align-items: center; font-size: 8.5pt; color: #666; }}
.sbadge {{ display: inline-block; padding: 1.5pt 7pt; border-radius: 99px; color: #fff; font-weight: 700; font-size: 8pt; margin-right: 4pt; }}
.pos {{ font-weight: 700; color: #555; }}
.toc-mini {{ text-decoration: none; color: #555; border: 1px solid #d5cdc0; background: #fff; border-radius: 99px; padding: 1.5pt 8pt; font-size: 8pt; font-weight: 700; }}
.card {{ flex: 1; margin: 4mm 0; background: #fff; border: 1px solid #ddd6cb; border-radius: 10pt; padding: 6mm 5mm; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; overflow: hidden; position: relative; }}
.unit-lbl {{ position: absolute; top: 3.5mm; left: 4mm; right: 4mm; font-size: 7.5pt; color: #777; text-align: left; }}
.hero {{ max-width: 100%; max-height: 92mm; object-fit: contain; border-radius: 5pt; }}
.fig {{ max-width: 100%; max-height: 46mm; object-fit: contain; border: 1px solid #ddd6cb; border-radius: 5pt; padding: 2pt; margin-bottom: 4mm; }}
.region {{ margin-top: 3mm; font-size: 9.5pt; font-weight: 700; color: #555; }}
.q {{ font-size: 11.5pt; font-weight: 700; line-height: 1.55; word-break: break-word; }}
.q-sub {{ font-size: 9.5pt; line-height: 1.55; margin: 3mm 0 2mm; color: #333; }}
.blank {{ display: inline-block; padding: 0 4pt; margin: 0 1pt; border: 1.2pt solid #7b4fb0; border-radius: 4pt; color: #7b4fb0; font-weight: 800; }}
.hl {{ color: #7b4fb0; font-weight: 800; text-decoration: underline; }}
.ans {{ font-size: 16pt; font-weight: 800; color: #7b4fb0; line-height: 1.3; margin-bottom: 2mm; }}
.t {{ font-size: 14pt; font-weight: 800; margin: 0 0 2mm; }}
.a {{ font-size: 10.5pt; margin: 1mm 0 2mm; }}
.y {{ font-size: 8.5pt; color: #666; margin: 2mm 0 0; }}
.tag {{ display: inline-block; background: #7b4fb0; color: #fff; border-radius: 3pt; padding: 1pt 7pt; font-size: 8pt; margin: 1.5pt; }}
.tag.r {{ background: transparent; color: #666; border: 1px solid #ddd6cb; }}
.mark-box {{ width: 58mm; height: 44mm; border: 1px solid #ddd6cb; border-radius: 8pt; padding: 4mm; display: flex; align-items: center; justify-content: center; background: #fff; }}
.mark-box svg {{ width: 100%; height: 100%; }}
.diag-box {{ width: 100%; margin-bottom: 3mm; border: 1px solid #ddd6cb; border-radius: 6pt; padding: 2mm; background: #fff; }}
.diag-box.mini {{ width: 82%; margin-top: 2mm; }}
.diag-box svg {{ width: 100%; height: auto; display: block; }}
.ans-list {{ text-align: left; font-size: 9.5pt; line-height: 1.5; padding-left: 16pt; margin: 2mm 0; }}
.bot {{ display: grid; grid-template-columns: 1fr 2fr; gap: 3mm; }}
.bot a {{ text-decoration: none; text-align: center; font-weight: 800; font-size: 10pt; padding: 3.5mm 0; border-radius: 8pt; display: block; }}
.btn-sub {{ background: #fff; color: #444; border: 1px solid #d5cdc0; }}
.btn-main {{ background: #7b4fb0; color: #fff; }}
.btn-ok {{ background: #2e8b57; color: #fff; }}
/* 表紙目次 */
.toc-page {{ justify-content: flex-start; gap: 4mm; }}
.toc-hd h1 {{ font-size: 16pt; margin: 2mm 0 1mm; line-height: 1.3; }}
.toc-sub {{ font-size: 8.5pt; color: #666; margin: 0; }}
.toc-list {{ display: flex; flex-direction: column; gap: 3mm; margin-top: 2mm; }}
.toc-btn {{ text-decoration: none; color: #222; background: #fff; border: 1px solid #ddd6cb; border-radius: 10pt; padding: 3.2mm 3.5mm; display: flex; align-items: center; gap: 3mm; }}
.toc-main {{ flex: 1; display: flex; flex-direction: column; text-align: left; }}
.toc-main b {{ font-size: 10.5pt; }}
.toc-main small {{ font-size: 7pt; color: #666; line-height: 1.3; margin-top: 1pt; }}
.toc-go {{ font-weight: 800; color: #7b4fb0; font-size: 11pt; }}
.toc-tip {{ font-size: 7.8pt; color: #666; margin-top: auto; line-height: 1.45; }}
</style>
</head>
<body>
{"".join(pages)}
</body>
</html>"""


def main():
    html_str = render_pdf_html()
    tmp_html = os.path.join(SCRATCH_DIR, "print_quicklook.html")
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(html_str)
    print(f"PRINT_HTML: {tmp_html} ({len(html_str):,} bytes)", flush=True)

    chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome):
        chrome = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    out_pdf = os.path.join(WORK_DIR, "study_quicklook.pdf")
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={out_pdf}",
        "file:///" + tmp_html.replace("\\", "/"),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    print("CHROME_RC:", r.returncode, flush=True)
    if r.stderr.strip():
        print("CHROME_STDERR:", r.stderr.strip()[:400], flush=True)
    assert r.returncode == 0 and os.path.exists(out_pdf), "PDF generation failed"
    print(f"PDF_OK: {out_pdf} ({os.path.getsize(out_pdf):,} bytes)", flush=True)


if __name__ == "__main__":
    main()
