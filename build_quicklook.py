"""
iOSクイックルック（JavaScript無効環境）向け 純粋HTML+CSSフラッシュカード生成モジュール
全677問（美術・家庭科・体育・音楽・保健・社会）と全画像・SVGマーク・図解を
JSなしで開閉・暗記できる <details>/<summary> 構成として出力する。
"""
import html as html_lib
import re


def esc(s):
    return html_lib.escape(str(s or ""), quote=True)


def fmt_q(q):
    return esc(q).replace("［ ？ ］", '<span class="blank">？</span>')


def fmt_solved(q, a):
    return esc(q).replace("［ ？ ］", f'<span class="hl">{esc(a)}</span>')


def parse_marks_from_js(marks_js):
    """MARKSオブジェクト定義から {key: svg文字列} を抽出する"""
    out = {}
    for m in re.finditer(r'^\s{2}([a-z0-9]+):\s*`(<svg[\s\S]*?</svg>)`', marks_js, re.M):
        out[m.group(1)] = m.group(2)
    return out


def credit_diagram_svg(slot, reveal):
    """クレジットカード三者間契約SVGをPython側でも静的生成（JS不要表示用）"""
    labels = {
        "s2": "カードでの支払い",
        "s3": "商品の引き渡し",
        "s4": "代金の支払い",
        "s5": "カード発行",
        "s6": "代金の請求",
        "s7": "立て替え払い",
        "s8": "売上票",
    }
    blanks = {
        "s2": "［ ？ ］での支払い",
        "s3": "［ ？ ］の引き渡し",
        "s4": "［ ？ ］の支払い",
        "s5": "カード［ ？ ］",
        "s6": "［ ？ ］の請求",
        "s7": "［ ？ ］",
        "s8": "［ ？ ］",
    }
    txt = lambda k: (labels[k] if reveal else blanks[k]) if k == slot else labels[k]
    col = lambda k: "#7b4fb0" if k == slot else "#333"
    fw = lambda k: "900" if k == slot else "600"
    box = lambda k, x, y, w: (
        f'<rect x="{x - w/2}" y="{y - 13}" width="{w}" height="18" rx="4" fill="#f3ebfc" stroke="#7b4fb0" stroke-width="1.5"/>'
        if k == slot else ""
    )
    sc = lambda k: ("#7b4fb0", "2.5", "ahp") if k == slot else ("#666", "1.6", "ah")
    c2, w2, m2 = sc("s2")
    c3, w3, m3 = sc("s3")
    c4, w4, m4 = sc("s4")
    c56, w56, m56 = ("#7b4fb0", "2.5", "ahp") if slot in ("s5", "s6") else ("#666", "1.6", "ah")
    c7, w7, m7 = sc("s7")
    c8, w8, m8 = sc("s8")
    return (
        f'<svg viewBox="0 0 420 215" xmlns="http://www.w3.org/2000/svg">'
        f'<defs>'
        f'<marker id="qah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 1 L10 5 L0 9 Z" fill="#555"/></marker>'
        f'<marker id="qahp" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 1 L10 5 L0 9 Z" fill="#7b4fb0"/></marker>'
        f'</defs>'
        f'<rect x="160" y="10" width="100" height="32" rx="8" fill="#fff" stroke="#222" stroke-width="2"/>'
        f'<text x="210" y="31" text-anchor="middle" font-size="15" font-weight="800" fill="#222">消費者</text>'
        f'<rect x="14" y="156" width="94" height="32" rx="8" fill="#fff" stroke="#222" stroke-width="2"/>'
        f'<text x="61" y="177" text-anchor="middle" font-size="15" font-weight="800" fill="#222">販売者</text>'
        f'<rect x="278" y="156" width="130" height="32" rx="8" fill="#fff" stroke="#222" stroke-width="2"/>'
        f'<text x="343" y="177" text-anchor="middle" font-size="13" font-weight="800" fill="#222">クレジットカード会社</text>'
        f'<line x1="168" y1="46" x2="72" y2="148" stroke="{c2}" stroke-width="{w2}" marker-end="url(#q{m2})"/>'
        f'<line x1="90" y1="152" x2="184" y2="48" stroke="{c3}" stroke-width="{w3}" marker-end="url(#q{m3})"/>'
        f'{box("s2", 64, 86, 112)}<text x="64" y="86" text-anchor="middle" font-size="11.5" font-weight="{fw("s2")}" fill="{col("s2")}">{txt("s2")}</text>'
        f'{box("s3", 152, 118, 102)}<text x="152" y="118" text-anchor="middle" font-size="11.5" font-weight="{fw("s3")}" fill="{col("s3")}">{txt("s3")}</text>'
        f'<line x1="236" y1="48" x2="322" y2="148" stroke="{c4}" stroke-width="{w4}" marker-end="url(#q{m4})"/>'
        f'<line x1="340" y1="148" x2="254" y2="46" stroke="{c56}" stroke-width="{w56}" marker-end="url(#q{m56})"/>'
        f'{box("s4", 250, 118, 92)}<text x="250" y="118" text-anchor="middle" font-size="11.5" font-weight="{fw("s4")}" fill="{col("s4")}">{txt("s4")}</text>'
        f'{box("s5", 348, 72, 92)}<text x="348" y="72" text-anchor="middle" font-size="11.5" font-weight="{fw("s5")}" fill="{col("s5")}">{txt("s5")}</text>'
        f'{box("s6", 356, 94, 92)}<text x="356" y="94" text-anchor="middle" font-size="11.5" font-weight="{fw("s6")}" fill="{col("s6")}">{txt("s6")}</text>'
        f'<line x1="274" y1="164" x2="114" y2="164" stroke="{c7}" stroke-width="{w7}" marker-end="url(#q{m7})"/>'
        f'<line x1="114" y1="180" x2="274" y2="180" stroke="{c8}" stroke-width="{w8}" marker-end="url(#q{m8})"/>'
        f'{box("s7", 194, 155, 96)}<text x="194" y="155" text-anchor="middle" font-size="11.5" font-weight="{fw("s7")}" fill="{col("s7")}">{txt("s7")}</text>'
        f'{box("s8", 194, 200, 76)}<text x="194" y="200" text-anchor="middle" font-size="11.5" font-weight="{fw("s8")}" fill="{col("s8")}">{txt("s8")}</text>'
        f'</svg>'
    )


def render_ql_card(c, idx, total, marks_map, music_imgs, art_img_key_map):
    """1枚のカードを純粋HTML <details class="ql-card"> として描画する"""
    ctype = c["type"]
    meta = f'<div class="ql-meta"><span>{idx} / {total}・{esc(c.get("unit", ""))}</span><span>{esc(c.get("note", ""))}</span></div>'
    front = ""
    back = ""

    if ctype == "art-work":
        ik = art_img_key_map[c["id"]]
        front = f'<div class="ql-imgwrap"><img data-imgkey="{ik}" src="{c["img"]}" alt=""></div>'
        tags = f'<span class="tag r">{esc(c.get("r", ""))}</span>'
        if c.get("m"):
            tags += f'<span class="tag">{esc(c["m"])}</span>'
        back = (
            f'<p class="t">{esc(c.get("t", ""))}</p>'
            f'<p class="a">{esc(c.get("a", ""))}</p>'
            f'<p class="y">{esc(c.get("y", ""))}</p>'
            f'<div>{tags}</div>'
        )
    elif ctype == "photo":
        ik = c["imgKey"]
        src = music_imgs[ik]
        front = (
            f'<div class="ql-imgwrap"><img data-imgkey="{ik}" src="{src}" alt=""></div>'
            f'<div class="region-hint">地域：{esc(c.get("r", ""))}</div>'
        )
        back = (
            f'<p class="t">{esc(c["a"])}</p>'
            f'<div><span class="tag r">{esc(c.get("r", ""))}</span><span class="tag">{esc(c.get("unit", ""))}</span></div>'
        )
    elif ctype == "mark":
        svg = marks_map.get(c["mark"], "")
        front = f'<div class="mark-box ql-center">{svg}</div>'
        back = (
            f'<p class="t">{esc(c["a"])}</p>'
            f'<p class="a">{esc(c.get("desc", ""))}</p>'
            f'<div><span class="tag">{esc(c.get("unit", ""))}</span></div>'
        )
    elif ctype == "diagram":
        front = (
            f'<div class="diag-box ql-center">{credit_diagram_svg(c["slot"], False)}</div>'
            f'<div class="q">{fmt_q(c["q"])}</div>'
        )
        back = (
            f'<div class="ans">{esc(c["a"])}</div>'
            f'<p class="q-sub">{fmt_solved(c["q"], c["a"])}</p>'
            f'<div class="diag-box mini ql-center">{credit_diagram_svg(c["slot"], True)}</div>'
        )
    elif ctype == "list":
        front = f'<div class="q">{esc(c["q"])}</div>'
        lis = "".join(f"<li>{esc(it)}</li>" for it in c["items"])
        back = f'<div class="ans" style="font-size:1.2rem">{esc(c["a"])}</div><ol class="ans-list">{lis}</ol>'
    else:
        # cloze / art-cloze
        img_html = ""
        if c.get("imgKey") and c["imgKey"] in music_imgs:
            ik = c["imgKey"]
            img_html = f'<div class="ql-imgwrap ql-fig"><img data-imgkey="{ik}" src="{music_imgs[ik]}" alt=""></div>'
        front = f'{img_html}<div class="q">{fmt_q(c["q"])}</div>'
        back = (
            f'<div class="ans">{esc(c["a"])}</div>'
            f'<p class="q-sub">{fmt_solved(c["q"], c["a"])}</p>'
        )

    return (
        f'<details class="ql-card">'
        f'<summary>{meta}{front}<div class="ql-tap">タップで答えを表示 ▼</div></summary>'
        f'<div class="ql-ans">{back}</div>'
        f'</details>'
    )


def build_quicklook_html(subjects_data, marks_map, music_imgs):
    """
    subjects_data: list of (key, label, cards_list)
    returns: (ql_html_str, art_img_key_map)
    """
    art_img_key_map = {}
    art_idx = 0
    for key, _, cards in subjects_data:
        if key == "art":
            for c in cards:
                if c["type"] == "art-work":
                    art_img_key_map[c["id"]] = f"art_{art_idx}"
                    art_idx += 1

    total_all = sum(len(cards) for _, _, cards in subjects_data)
    parts = [
        '<div id="ql-app">',
        '<div class="wrap">',
        '<h1>テスト対策フラッシュカード<span class="ver-badge">完全オフライン / クイックルック対応</span></h1>',
        f'<p class="ql-note">全6教科・全{total_all}問を収録（JavaScriptなし／iOSクイックルック対応）。下の教科をタップして開き、各カードをタップすると答えが表示されます。</p>',
    ]

    for key, label, cards in subjects_data:
        cards_html = "".join(
            render_ql_card(c, i + 1, len(cards), marks_map, music_imgs, art_img_key_map)
            for i, c in enumerate(cards)
        )
        parts.append(
            f'<details class="ql-subj s-bd-{key}">'
            f'<summary class="ql-subj-hd"><span class="sbadge s-{key}">{esc(label)}</span>'
            f'<span>{esc(label)}（全{len(cards)}問）</span><span class="ql-arr">▼</span></summary>'
            f'<div class="ql-list">{cards_html}</div>'
            f'</details>'
        )

    parts.append("</div></div>")
    return "\n".join(parts), art_img_key_map
