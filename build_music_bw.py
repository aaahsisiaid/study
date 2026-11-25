"""
音楽65問のみ・完全白黒（モノクロ）版ビルドスクリプト
1. music_bw.html : 音楽65問専用の完全白黒フラッシュカード（単一HTML・オフライン動作・QR/JSON入出力付き）
2. music_bw.pdf  : A4白黒印刷＆iOSクイックルック対応の音楽テスト問題＋解答プリントPDF
"""
import base64
import html as html_lib
import json
import os
import subprocess

WORK_DIR = r"C:\Users\ytouw\.gemini\antigravity\scratch\kateika-flashcards"
CROP_DIR = r"C:\Users\ytouw\.gemini\antigravity\brain\0a7e6c3c-42b7-4101-a5c9-b19506fdd07e\scratch\extracted_hoken\crops"
PHOTO_DIR = os.path.join(WORK_DIR, "music_photos")
SCRATCH_DIR = r"C:\Users\ytouw\.gemini\antigravity\brain\0a7e6c3c-42b7-4101-a5c9-b19506fdd07e\scratch"

esc = lambda s: html_lib.escape(str(s or ""), quote=True)

with open(os.path.join(WORK_DIR, "data_music.json"), encoding="utf-8") as f:
    music_cards = json.load(f)

music_imgs = {}
for fn in sorted(os.listdir(CROP_DIR)):
    if fn.endswith(".jpg") and not fn.startswith("_"):
        key = os.path.splitext(fn)[0]
        sp = os.path.join(PHOTO_DIR, fn) if os.path.exists(os.path.join(PHOTO_DIR, fn)) else os.path.join(CROP_DIR, fn)
        with open(sp, "rb") as f:
            music_imgs[key] = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("ascii")


def build_music_bw_html():
    """音楽65問のみ・完全白黒フラッシュカードHTML（オフライン完結・外部ライブラリなし）"""
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>音楽フラッシュカード（白黒版・全65問）</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#fff;color:#111;font-family:"Hiragino Sans","Yu Gothic UI","Meiryo",sans-serif;line-height:1.6}}
.wrap{{max-width:620px;margin:auto;padding:16px 16px 40px}}
h1{{font-size:1.25rem;margin:0 0 10px;border-bottom:2px solid #111;padding-bottom:6px}}
.ctl{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;align-items:center}}
.ctl button,.ctl select{{font:inherit;font-size:.84rem;border:1.5px solid #111;background:#fff;color:#111;border-radius:999px;padding:4px 12px;cursor:pointer}}
.ctl button.on{{background:#111;color:#fff}}
.stat{{color:#444;font-size:.84rem;margin:8px 0;display:flex;justify-content:space-between}}
.scene{{perspective:1200px;cursor:pointer;user-select:none}}
.card{{position:relative;height:min(66vh,520px);transition:transform .45s;transform-style:preserve-3d}}
.card.flip{{transform:rotateY(180deg)}}
.face{{position:absolute;inset:0;backface-visibility:hidden;background:#fff;border:2px solid #111;border-radius:14px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:34px 20px 30px;text-align:center;overflow-y:auto}}
.back{{transform:rotateY(180deg);background:#f7f7f7}}
.face img{{max-width:100%;max-height:68%;object-fit:contain;border:1px solid #bbb;border-radius:6px;padding:4px;background:#fff;filter:grayscale(100%) contrast(1.08)}}
.face img.fig-img{{max-height:44%;margin-bottom:10px}}
.face img.mini{{max-height:30%!important;margin-bottom:10px}}
.topic{{position:absolute;top:10px;left:14px;right:14px;display:flex;justify-content:space-between;font-size:.75rem;color:#555;pointer-events:none}}
.hint{{position:absolute;bottom:8px;left:0;right:0;text-align:center;font-size:.75rem;color:#555;pointer-events:none}}
.q{{font-size:1.1rem;font-weight:700;max-width:100%;word-break:break-word}}
.q-sub{{font-weight:400;font-size:.96rem;margin:10px 0 6px;line-height:1.65}}
.blank{{display:inline-block;padding:0 6px;margin:0 2px;border:1.5px solid #111;border-radius:4px;font-weight:800;background:#fff}}
.hl{{font-weight:900;text-decoration:underline;text-underline-offset:3px}}
.t{{font-size:1.4rem;font-weight:800;margin:0 0 6px}}
.ans{{font-size:1.55rem;font-weight:900;color:#111;border-bottom:2px solid #111;padding-bottom:2px}}
.y{{font-size:.9rem;color:#555;margin:4px 0 8px}}
.tag{{display:inline-block;background:#111;color:#fff;border-radius:4px;padding:1px 10px;font-size:.82rem;margin:2px}}
.tag.r{{background:#fff;color:#111;border:1px solid #111}}
.region-hint{{margin-top:8px;font-size:.9rem;color:#333;font-weight:700}}
.nav{{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;margin-top:12px}}
.nav button{{font:inherit;font-weight:700;border-radius:10px;padding:12px 0;border:1.5px solid #111;background:#fff;color:#111;cursor:pointer}}
.nav .ok{{background:#111;color:#fff}}
.nav .ng{{border-style:dashed}}
label.chk{{display:inline-flex;align-items:center;gap:4px;font-size:.82rem;margin-right:4px;cursor:pointer}}
.empty{{padding:40px 20px;text-align:center;color:#555}}
.links{{margin-top:12px;font-size:.8rem;color:#555;display:flex;gap:12px;flex-wrap:wrap}}
.links a{{color:#111;font-weight:700}}
</style>
</head>
<body>
<div class="wrap">
<h1>音楽フラッシュカード（白黒・全65問）</h1>
<div class="ctl" id="filt">
 <button data-f="all" class="on">ぜんぶ (65)</button>
 <button data-f="inst">世界の楽器・写真 (24)</button>
 <button data-f="world">タンソ・ウード・タブラー (16)</button>
 <button data-f="sorrento">帰れソレントへ (25)</button>
 <button data-f="todo">まだだけ</button>
</div>
<div class="ctl">
 <select id="side">
  <option value="img">表：写真 → 裏：楽器名・地域</option>
  <option value="name">表：楽器名 → 裏：写真・地域</option>
 </select>
 <button id="shuf">シャッフル</button>
 <button id="reset">覚えた印を消す</button>
</div>
<div class="ctl" id="show">
 <span style="font-size:.82rem;color:#555">裏に出す：</span>
 <label class="chk"><input type="checkbox" value="img" checked>写真/図</label>
 <label class="chk"><input type="checkbox" value="t" checked>解答</label>
 <label class="chk"><input type="checkbox" value="a" checked>全文</label>
 <label class="chk"><input type="checkbox" value="r" checked>地域・単元</label>
 <label class="chk"><input type="checkbox" value="y" checked>番号</label>
</div>
<div class="stat"><span id="pos"></span><span id="known"></span></div>
<div id="area"></div>
<div class="nav"><button id="prev">← 前</button><button class="ng" id="no">まだ</button><button class="ok" id="yes">覚えた</button><button id="nxt">次 →</button></div>
<p style="color:#555;font-size:.8rem;margin-top:10px">タップでめくる。キーボード：←→ 移動 / Space めくる / ↑ 覚えた / ↓ まだ</p>
<div class="links">
 <a href="./music_bw.pdf" download="music_bw.pdf">白黒印刷用PDF（問題＋解答）をダウンロード</a>
 <a href="./index.html">6教科統合版に戻る</a>
</div>
</div>
<script>
const MUSIC_IMGS = {json.dumps(music_imgs, ensure_ascii=False)};
const ALL = {json.dumps(music_cards, ensure_ascii=False)};
const KEY = "music-bw-known-v1";
let known = {{}};
try {{ known = JSON.parse(localStorage.getItem(KEY) || "{{}}"); }} catch (e) {{}}
const save = () => {{ try {{ localStorage.setItem(KEY, JSON.stringify(known)); }} catch (e) {{}} }};
let filt = "all", list = [], i = 0, flipped = false;
const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, m => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[m]));
const fmtQ = q => esc(q).replace(/［ ？ ］/g, '<span class="blank">？</span>');
const fmtSolved = (q, a) => esc(q).replace(/［ ？ ］/g, `<span class="hl">${{esc(a)}}</span>`);
const showCfg = () => {{ const o = {{}}; document.querySelectorAll("#show input").forEach(x => o[x.value] = x.checked); return o; }};

function apply(sh = false) {{
  let arr = ALL.filter(c => filt === "all" ? true : filt === "todo" ? !known[c.id] : c.cat === filt);
  if (sh) {{
    arr = arr.slice();
    for (let k = arr.length - 1; k > 0; k--) {{ const j = Math.random() * (k + 1) | 0; [arr[k], arr[j]] = [arr[j], arr[k]]; }}
  }}
  list = arr; i = 0; render();
}}

function render() {{
  const kc = ALL.filter(c => known[c.id]).length;
  $("#known").textContent = `覚えた ${{kc}} / ${{ALL.length}}`;
  if (!list.length) {{
    $("#pos").textContent = "0 / 0";
    $("#area").innerHTML = `<div class="face" style="position:static;min-height:220px"><div class="empty">該当するカードはありません</div></div>`;
    return;
  }}
  const c = list[i]; flipped = false;
  $("#pos").textContent = `${{i + 1}} / ${{list.length}}${{known[c.id] ? "　✓覚えた" : ""}}`;
  const sh = showCfg(), side = $("#side").value;
  let f = `<div class="topic"><span>${{esc(c.unit)}}</span><span>${{esc(c.note)}}</span></div>`, b = "";
  if (c.type === "photo") {{
    const src = MUSIC_IMGS[c.imgKey];
    if (side === "img") {{
      f += `<img src="${{src}}" alt=""><div class="region-hint">地域：${{esc(c.r)}}</div>`;
      if (sh.t) b += `<p class="t">${{esc(c.a)}}</p>`;
      if (sh.r) b += `<div><span class="tag r">${{esc(c.r)}}</span><span class="tag">${{esc(c.unit)}}</span></div>`;
      if (sh.y) b += `<p class="y">${{esc(c.note)}}</p>`;
    }} else {{
      f += `<p class="t">${{esc(c.a)}}</p>`;
      if (sh.img) b += `<img class="mini" src="${{src}}" alt="">`;
      if (sh.t) b += `<p class="t" style="font-size:1.12rem">${{esc(c.a)}}</p>`;
      if (sh.r) b += `<div><span class="tag r">${{esc(c.r)}}</span><span class="tag">${{esc(c.unit)}}</span></div>`;
      if (sh.y) b += `<p class="y">${{esc(c.note)}}</p>`;
    }}
  }} else {{
    if (c.imgKey && MUSIC_IMGS[c.imgKey]) f += `<img class="fig-img" src="${{MUSIC_IMGS[c.imgKey]}}" alt="">`;
    f += `<div class="q">${{fmtQ(c.q)}}</div>`;
    if (c.imgKey && MUSIC_IMGS[c.imgKey] && sh.img) b += `<img class="mini" src="${{MUSIC_IMGS[c.imgKey]}}" alt="">`;
    if (sh.t) b += `<div class="ans">${{esc(c.a)}}</div>`;
    if (sh.a) b += `<p class="q-sub">${{fmtSolved(c.q, c.a)}}</p>`;
    if (sh.r) b += `<div><span class="tag">${{esc(c.unit)}}</span></div>`;
    if (sh.y) b += `<p class="y">${{esc(c.note)}}</p>`;
  }}
  $("#area").innerHTML = `<div class="scene"><div class="card" id="card"><div class="face">${{f}}<span class="hint">タップでめくる</span></div><div class="face back">${{b || '<p class="y">（表示項目オフ）</p>'}}</div></div></div>`;
  $(".scene").onclick = flip;
}}
function flip() {{ const el = $("#card"); if (!el) return; flipped = !flipped; el.classList.toggle("flip", flipped); }}
function go(d) {{ if (!list.length) return; i = (i + d + list.length) % list.length; render(); }}
function mark(v) {{
  if (!list.length) return;
  const c = list[i]; if (v) known[c.id] = 1; else delete known[c.id]; save();
  if (filt === "todo" && v) {{ list.splice(i, 1); if (i >= list.length) i = 0; render(); }} else go(1);
}}
$("#filt").onclick = e => {{
  const b = e.target.closest("button[data-f]"); if (!b) return;
  document.querySelectorAll("#filt button").forEach(x => x.classList.remove("on"));
  b.classList.add("on"); filt = b.dataset.f; apply(false);
}};
$("#side").onchange = render; $("#show").onchange = render;
$("#shuf").onclick = () => apply(true);
$("#reset").onclick = () => {{ if (confirm("音楽の覚えた印をぜんぶ消す？")) {{ known = {{}}; save(); apply(false); }} }};
$("#prev").onclick = () => go(-1); $("#nxt").onclick = () => go(1);
$("#yes").onclick = () => mark(1); $("#no").onclick = () => mark(0);
document.addEventListener("keydown", e => {{
  if (e.target.tagName === "SELECT" || e.target.tagName === "INPUT") return;
  if (e.key === "ArrowRight") {{ e.preventDefault(); go(1); }}
  else if (e.key === "ArrowLeft") {{ e.preventDefault(); go(-1); }}
  else if (e.key === " ") {{ e.preventDefault(); flip(); }}
  else if (e.key === "ArrowUp") {{ e.preventDefault(); mark(1); }}
  else if (e.key === "ArrowDown") {{ e.preventDefault(); mark(0); }}
}});
apply(false);
</script>
</body>
</html>"""


def build_music_bw_print_html():
    """A4白黒印刷用・音楽テスト対策プリント（問題ページ＋別ページ解答一覧）"""
    inst_cards = [c for c in music_cards if c["cat"] == "inst"]
    world_cards = [c for c in music_cards if c["cat"] == "world"]
    sorrento_cards = [c for c in music_cards if c["cat"] == "sorrento"]

    # (1) 楽器24問グリッド（白黒写真＋地域＋解答欄）
    inst_grid = "".join(
        f'<div class="icard">'
        f'<div class="ihd">({idx}) {esc(c["r"])}</div>'
        f'<div class="iimg"><img src="{music_imgs[c["imgKey"]]}" alt=""></div>'
        f'<div class="iline"></div>'
        f'</div>'
        for idx, c in enumerate(inst_cards, 1)
    )

    # (2) タンソ・ウード・タブラー（図1〜3付き穴埋め16問）
    world_groups = [
        ("タンソ（図1）", "fig_1", world_cards[0:6]),
        ("ウード（図2）", "fig_2", world_cards[6:12]),
        ("タブラー（図3）", "fig_3", world_cards[12:16]),
    ]
    world_html = ""
    for gtitle, fkey, gcards in world_groups:
        items = "".join(
            f'<li><span class="qtxt">{esc(c["q"]).replace("［ ？ ］", "<span class=blank>（　　　　　）</span>")}</span></li>'
            for c in gcards
        )
        world_html += (
            f'<div class="wblock">'
            f'<div class="wleft"><h3>{esc(gtitle)}</h3><ol>{items}</ol></div>'
            f'<div class="wright"><img src="{music_imgs[fkey]}" alt=""></div>'
            f'</div>'
        )

    # (3) 帰れソレントへ（25問＋楽譜画像）
    sorrento_items = "".join(
        f'<li>{esc(c["q"]).replace("［ ？ ］", "<span class=blank>（　　　　　）</span>")}</li>'
        for c in sorrento_cards
    )

    # 解答ページ
    ans_inst = "".join(f'<span><b>({i})</b> {esc(c["a"])}</span>' for i, c in enumerate(inst_cards, 1))
    ans_w1 = "".join(f'<span><b>①</b>' if i == 1 else f'<span><b>({i})</b>' for i in [])
    ans_w = []
    for gtitle, _, gcards in world_groups:
        s = " / ".join(f'<b>({i})</b> {esc(c["a"])}' for i, c in enumerate(gcards, 1))
        ans_w.append(f'<p><b>【{esc(gtitle)}】</b> {s}</p>')
    ans_sor = "".join(f'<span><b>({i})</b> {esc(c["a"])}</span>' for i, c in enumerate(sorrento_cards, 1))

    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>音楽テスト対策問題（白黒印刷用・全65問）</title>
<style>
@page {{ size: A4 portrait; margin: 12mm; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: #fff; color: #000; font-family: "Yu Gothic UI", "Meiryo", "Hiragino Sans", sans-serif; font-size: 9.5pt; line-height: 1.5; }}
h1 {{ font-size: 14pt; margin: 0 0 8pt; border-bottom: 2px solid #000; padding-bottom: 3pt; display: flex; justify-content: space-between; align-items: baseline; }}
h1 small {{ font-size: 9pt; font-weight: 400; }}
h2 {{ font-size: 11pt; margin: 10pt 0 6pt; padding: 2pt 6pt; border-left: 4px solid #000; background: #efefef; }}
h3 {{ font-size: 10pt; margin: 0 0 4pt; }}
img {{ filter: grayscale(100%) contrast(1.1); }}
.igrid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 5pt; }}
.icard {{ border: 1px solid #000; padding: 3.5pt; display: flex; flex-direction: column; break-inside: avoid; }}
.ihd {{ font-size: 7.8pt; font-weight: 700; margin-bottom: 2pt; }}
.iimg {{ height: 56pt; display: flex; align-items: center; justify-content: center; overflow: hidden; }}
.iimg img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
.iline {{ border-bottom: 1px solid #000; height: 13pt; margin-top: 2pt; }}
.pb {{ page-break-before: always; break-before: page; }}
.wblock {{ display: flex; gap: 10pt; border: 1px solid #000; padding: 7pt; margin-bottom: 8pt; align-items: center; break-inside: avoid; }}
.wleft {{ flex: 1; }}
.wleft ol {{ margin: 0; padding-left: 16pt; }}
.wleft li {{ margin: 2pt 0; }}
.wright {{ width: 105pt; text-align: center; }}
.wright img {{ max-width: 100%; max-height: 115pt; border: 1px solid #666; }}
.score-box {{ text-align: center; margin: 6pt 0 8pt; padding: 5pt; border: 1px solid #000; }}
.score-box img {{ max-width: 75%; max-height: 85pt; }}
.sor-list {{ margin: 0; padding-left: 18pt; columns: 1; }}
.sor-list li {{ margin: 2.5pt 0; }}
.blank {{ font-weight: 700; }}
.ans-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 4pt 10pt; border: 1px solid #000; padding: 8pt; margin-bottom: 10pt; }}
.ans-box {{ border: 1px solid #000; padding: 8pt; margin-bottom: 10pt; }}
.ans-box p {{ margin: 4pt 0; }}
</style>
</head>
<body>
<h1><span>音楽 テスト対策問題（白黒・全65問）</span><small>名前：＿＿＿＿＿＿＿＿＿＿</small></h1>
<h2>1. 世界の諸民族の音楽：次の写真を見て楽器名を答えなさい（24問）</h2>
<div class="igrid">{inst_grid}</div>

<div class="pb"></div>
<h2>2. タンソ・ウード・タブラーに関する穴埋め問題（16問）</h2>
{world_html}

<div class="pb"></div>
<h2>3. 『帰れソレントへ』に関する穴埋め問題（25問）</h2>
<div class="score-box">
  <div style="font-size:8pt;margin-bottom:2pt">【問21・問22 楽譜】</div>
  <img src="{music_imgs["sorrento_score"]}" alt="">
</div>
<ol class="sor-list">{sorrento_items}</ol>

<div class="pb"></div>
<h1><span>音楽 テスト対策 解答（全65問）</span><small>答え合わせ用</small></h1>
<h2>1. 世界の民族楽器（24問）</h2>
<div class="ans-grid">{ans_inst}</div>
<h2>2. タンソ・ウード・タブラー（16問）</h2>
<div class="ans-box">{"".join(ans_w)}</div>
<h2>3. 『帰れソレントへ』（25問）</h2>
<div class="ans-grid">{ans_sor}</div>
</body>
</html>"""


def main():
    # 1. 白黒フラッシュカード HTML
    html_out = os.path.join(WORK_DIR, "music_bw.html")
    h = build_music_bw_html()
    with open(html_out, "w", encoding="utf-8") as f:
        f.write(h)
    print(f"HTML_OK: {html_out} ({len(h):,} bytes)", flush=True)

    # 2. A4白黒印刷用 PDF（問題＋解答）
    tmp_print = os.path.join(SCRATCH_DIR, "music_bw_print.html")
    phtml = build_music_bw_print_html()
    with open(tmp_print, "w", encoding="utf-8") as f:
        f.write(phtml)

    chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome):
        chrome = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    pdf_out = os.path.join(WORK_DIR, "music_bw.pdf")
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_out}",
        "file:///" + tmp_print.replace("\\", "/"),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0 and os.path.exists(pdf_out), f"PDF failed: {r.stderr}"
    print(f"PDF_OK : {pdf_out} ({os.path.getsize(pdf_out):,} bytes)", flush=True)


if __name__ == "__main__":
    main()
