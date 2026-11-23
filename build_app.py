"""
5教科統合フラッシュカード（美術・家庭科・体育・音楽・保健）ビルドスクリプト
単一のスタンドアロン index.html を生成する。
"""
import base64
import json
import os
import re

WORK_DIR = r"C:\Users\ytouw\.gemini\antigravity\scratch\kateika-flashcards"
CROP_DIR = r"C:\Users\ytouw\.gemini\antigravity\brain\0a7e6c3c-42b7-4101-a5c9-b19506fdd07e\scratch\extracted_hoken\crops"

# 1. 美術（art_source.html）から148問を抽出
with open(os.path.join(WORK_DIR, "art_source.html"), encoding="utf-8") as f:
    art_html = f.read()
m_art = re.search(r"const ALL=(\[.*?\]);", art_html)
assert m_art, "art_source.html から ALL 配列を取得できませんでした"
raw_art = json.loads(m_art.group(1))

art_cards = []
for c in raw_art:
    if c.get("k") == "w":
        r = c.get("r", "")
        cat = "jp" if r == "日本" else ("west" if r == "西洋" else "asia")
        art_cards.append({
            "id": "art:" + c["id"],
            "legacyId": c["id"],
            "subj": "art",
            "cat": cat,
            "unit": c.get("m") or f"{r}の作品",
            "note": f"美術・{r}",
            "type": "art-work",
            "img": c["img"],
            "t": c.get("t", ""),
            "a": c.get("a", ""),
            "y": c.get("y", ""),
            "m": c.get("m", ""),
            "r": r,
        })
    else:
        art_cards.append({
            "id": "art:" + c["id"],
            "legacyId": c["id"],
            "subj": "art",
            "cat": "cloze",
            "unit": "美術 穴埋め",
            "note": f"教科書 {c.get('src', '')}".strip(),
            "type": "art-cloze",
            "q": c["q"].replace("［　］", "［ ？ ］"),
            "a": c["ans"],
        })

# 2. 家庭科（既存 index.html または kateika_only.html）から SVG と 149問を抽出
kateika_src = os.path.join(WORK_DIR, "kateika_only.html")
if not os.path.exists(kateika_src):
    with open(os.path.join(WORK_DIR, "index.html"), encoding="utf-8") as f:
        k_html = f.read()
    with open(kateika_src, "w", encoding="utf-8") as f:
        f.write(k_html)
else:
    with open(kateika_src, encoding="utf-8") as f:
        k_html = f.read()

# MARKS と creditDiagram 関数を抽出
m_marks = re.search(r"(// 商品選択に役立つ表示マーク[\s\S]*?^// 全149問のフラッシュカードデータ)", k_html, re.M)
assert m_marks, "MARKS / creditDiagram が見つかりません"
marks_and_diagram_js = m_marks.group(1).rsplit("// 全149問", 1)[0].strip()

# CARDS 配列（JSオブジェクトリテラル）を抽出して各要素に subj:"home" を付与
m_kcards = re.search(r"const CARDS = \[\s*([\s\S]*?)\n\];", k_html)
assert m_kcards, "家庭科 CARDS 配列が見つかりません"
kcards_js = m_kcards.group(1)
# 各エントリ先頭の {id: に subj:"home", を挿入
kcards_js_with_subj = re.sub(r'(\{id:"[^"]+",)', r'\1subj:"home",', kcards_js)
k_count = len(re.findall(r'\{id:"p\d+-\d+"', kcards_js_with_subj))
assert k_count == 149, f"家庭科カード数が149ではありません: {k_count}"

# 3. 体育・音楽・保健のJSONを読み込み
with open(os.path.join(WORK_DIR, "data_pe.json"), encoding="utf-8") as f:
    pe_cards = json.load(f)
with open(os.path.join(WORK_DIR, "data_music.json"), encoding="utf-8") as f:
    music_cards = json.load(f)
with open(os.path.join(WORK_DIR, "data_health.json"), encoding="utf-8") as f:
    health_cards = json.load(f)

# 4. 音楽の画像28枚（楽器24種は鮮明な実物カラー写真、図1〜3と楽譜は切り抜き）をBase64データURI化
PHOTO_DIR = os.path.join(WORK_DIR, "music_photos")
music_imgs = {}
for fn in sorted(os.listdir(CROP_DIR)):
    if fn.endswith(".jpg") and not fn.startswith("_"):
        key = os.path.splitext(fn)[0]
        src_path = os.path.join(PHOTO_DIR, fn) if os.path.exists(os.path.join(PHOTO_DIR, fn)) else os.path.join(CROP_DIR, fn)
        with open(src_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        music_imgs[key] = "data:image/jpeg;base64," + b64

# 参照切れチェック
for c in music_cards:
    if "imgKey" in c:
        assert c["imgKey"] in music_imgs, f"画像が見つかりません: {c['imgKey']}"

print(f"Art: {len(art_cards)}, Home: {k_count}, PE: {len(pe_cards)}, Music: {len(music_cards)} (imgs={len(music_imgs)}), Health: {len(health_cards)}")
print(f"GRAND TOTAL: {len(art_cards) + k_count + len(pe_cards) + len(music_cards) + len(health_cards)}")

# 5. 単一HTMLテンプレートに結合
html_template = r"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>5教科テスト対策フラッシュカード｜美術・家庭科・体育・音楽・保健（全553問）</title>
<meta name="description" content="中学・高校の期末テスト対策に使える無料の暗記フラッシュカード。美術（名画・作品148問）・家庭科（消費者・クレジットカード・表示マーク・8つの権利と5つの責任など151問）・体育（水泳・器械運動・陸上・ハンドボール・卓球80問）・音楽（世界の民族楽器写真24種・帰れソレントへ65問）・保健（感染症・エイズ・医薬品109問）の全553問を収録。">
<meta name="keywords" content="テスト対策,期末テスト,フラッシュカード,暗記カード,実技教科,美術,家庭科,体育,音楽,保健,消費者の8つの権利,消費者の5つの責任,クーリングオフ,世界の民族楽器,帰れソレントへ,感染症,エイズ,無料">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://aaahsisiaid.github.io/study/">
<meta property="og:type" content="website">
<meta property="og:locale" content="ja_JP">
<meta property="og:site_name" content="5教科テスト対策フラッシュカード">
<meta property="og:title" content="5教科テスト対策フラッシュカード｜美術・家庭科・体育・音楽・保健（全553問）">
<meta property="og:description" content="美術・家庭科（8つの権利と5つの責任・マーク15種）・体育・音楽（民族楽器24種写真）・保健の全553問をスマホやPCで暗記できる無料フラッシュカード。">
<meta property="og:url" content="https://aaahsisiaid.github.io/study/">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="5教科テスト対策フラッシュカード（美術・家庭科・体育・音楽・保健）">
<meta name="twitter:description" content="実技5教科の全553問を教科別・単元別に暗記できる無料フラッシュカード。">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "5教科テスト対策フラッシュカード（美術・家庭科・体育・音楽・保健）",
  "url": "https://aaahsisiaid.github.io/study/",
  "inLanguage": "ja",
  "applicationCategory": "EducationalApplication",
  "operatingSystem": "All",
  "isAccessibleForFree": true,
  "description": "美術148問・家庭科151問（消費者の8つの権利・5つの責任・商品選択マーク15種含む）・体育80問・音楽65問（世界の民族楽器24種写真・帰れソレントへ）・保健109問の全553問を収録した期末テスト対策フラッシュカード。",
  "about": ["美術", "家庭科", "消費者の8つの権利", "消費者の5つの責任", "体育", "音楽", "世界の民族楽器", "帰れソレントへ", "保健体育", "感染症"]
}
</script>
<style>
:root{--bg:#f6f3ee;--fg:#222;--sub:#666;--card:#fff;--line:#ddd6cb;--acc:#7b4fb0;--ok:#2e8b57;--ng:#c0392b;--mark-bg:#ffffff;--s-art:#7b4fb0;--s-home:#c06c2b;--s-pe:#2574a9;--s-music:#b83b6e;--s-health:#2e8b57}
@media (prefers-color-scheme:dark){:root{--bg:#1b1a18;--fg:#eee;--sub:#aaa;--card:#262522;--line:#3a3833;--acc:#a988d6;--ok:#4cbb7f;--ng:#e5675a;--mark-bg:#f4f2ee;--s-art:#a988d6;--s-home:#e69b5c;--s-pe:#5faee3;--s-music:#e57ca8;--s-health:#5ac48a}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font-family:"Hiragino Sans","Yu Gothic UI","Meiryo",sans-serif;line-height:1.6}
.wrap{max-width:640px;margin:auto;padding:16px 16px 40px}
h1{font-size:1.25rem;margin:0 0 10px}
.ctl{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;align-items:center}
.ctl button,.ctl select{font:inherit;font-size:.84rem;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;padding:4px 12px;cursor:pointer}
.ctl button.on{background:var(--fg);color:var(--bg);border-color:var(--fg)}
.subj-bar button{font-weight:700;padding:5px 13px}
.subj-bar button[data-s="art"].on{background:var(--s-art);border-color:var(--s-art);color:#fff}
.subj-bar button[data-s="home"].on{background:var(--s-home);border-color:var(--s-home);color:#fff}
.subj-bar button[data-s="pe"].on{background:var(--s-pe);border-color:var(--s-pe);color:#fff}
.subj-bar button[data-s="music"].on{background:var(--s-music);border-color:var(--s-music);color:#fff}
.subj-bar button[data-s="health"].on{background:var(--s-health);border-color:var(--s-health);color:#fff}
.cnt{font-size:.75rem;opacity:.75;margin-left:3px;font-weight:500}
.stat{color:var(--sub);font-size:.84rem;margin:8px 0;display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px}
.scene{perspective:1200px;cursor:pointer;user-select:none}
.card{position:relative;height:min(66vh,520px);transition:transform .45s;transform-style:preserve-3d}
.card.flip{transform:rotateY(180deg)}
.face{position:absolute;inset:0;backface-visibility:hidden;background:var(--card);border:1px solid var(--line);border-radius:14px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:34px 20px 30px;text-align:center;overflow-y:auto}
.back{transform:rotateY(180deg)}
.face img{max-width:100%;max-height:76%;object-fit:contain;border-radius:8px}
.face img.art-full{max-height:88%}
.face img.fig-img{max-height:46%;margin-bottom:10px;border:1px solid var(--line);background:#fff;padding:3px}
.face img.mini{max-height:30%!important;margin-bottom:10px;border-radius:6px}
.hint{position:absolute;bottom:8px;left:0;right:0;text-align:center;font-size:.75rem;color:var(--sub);pointer-events:none}
.topic{position:absolute;top:10px;left:14px;right:14px;display:flex;justify-content:space-between;align-items:center;font-size:.75rem;color:var(--sub);pointer-events:none;gap:8px}
.sbadge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.72rem;font-weight:700;color:#fff;margin-right:5px}
.s-art{background:var(--s-art)}.s-home{background:var(--s-home)}.s-pe{background:var(--s-pe)}.s-music{background:var(--s-music)}.s-health{background:var(--s-health)}
.q{font-size:1.1rem;font-weight:700;max-width:100%;word-break:break-word}
.q-sub{font-weight:400;font-size:.96rem;margin:10px 0 6px;line-height:1.65}
.blank{display:inline-block;padding:0 6px;margin:0 2px;border-radius:5px;border:1.5px solid var(--acc);color:var(--acc);font-weight:800}
.hl{color:var(--acc);font-weight:800;text-decoration:underline;text-underline-offset:3px}
.t{font-size:1.38rem;font-weight:800;margin:0 0 6px}
.a{font-size:1.05rem;margin:2px 0 6px}
.y{font-size:.92rem;color:var(--sub);margin:2px 0 8px}
.tag{display:inline-block;background:var(--acc);color:#fff;border-radius:4px;padding:1px 10px;font-size:.84rem;margin:2px}
.tag.r{background:transparent;color:var(--sub);border:1px solid var(--line)}
.ans{font-size:1.55rem;font-weight:800;color:var(--acc);line-height:1.35}
.region-hint{margin-top:8px;font-size:.88rem;color:var(--sub);font-weight:700}
.mark-box{background:var(--mark-bg);border:1px solid var(--line);border-radius:12px;padding:16px;display:flex;align-items:center;justify-content:center;max-width:250px;width:64%;aspect-ratio:4/3}
.mark-box svg{width:100%;height:100%;display:block}
.mark-box.mini{max-width:128px;width:38%;padding:8px;margin-bottom:8px}
.diag-box{background:var(--mark-bg);border:1px solid var(--line);border-radius:12px;padding:8px;width:100%;max-width:450px;margin-bottom:8px}
.diag-box svg{width:100%;height:auto;display:block}
.diag-box.mini{max-width:320px;padding:5px;margin-bottom:6px}
.nav{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;margin-top:12px}
.nav button{font:inherit;font-weight:700;border-radius:10px;padding:12px 0;border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}
.nav .ng{border-color:var(--ng);color:var(--ng)}.nav .ok{border-color:var(--ok);color:var(--ok)}
label.chk{display:inline-flex;align-items:center;gap:4px;font-size:.82rem;margin-right:4px;cursor:pointer}
.empty{padding:40px 20px;text-align:center;color:var(--sub)}
.ans-list{text-align:left;margin:6px 0 8px;padding-left:1.3em;font-size:.93rem;line-height:1.55;max-width:95%}
.ans-list li{margin:2px 0}
.seo-info{margin-top:24px;border-top:1px solid var(--line);padding-top:12px;color:var(--sub);font-size:.8rem}
.seo-info summary{cursor:pointer;font-weight:700}
.seo-info h2{font-size:.88rem;margin:10px 0 4px;color:var(--fg)}
.seo-info p{margin:4px 0}
</style>
</head>
<body>
<div class="wrap">
<h1>テスト対策フラッシュカード</h1>
<div class="ctl subj-bar" id="subj"></div>
<div class="ctl" id="filt"></div>
<div class="ctl">
 <select id="sort">
  <option value="default">並び：教科・単元順</option>
  <option value="subj-order">並び：教科ソート（五十音順）</option>
  <option value="todo-first">並び：まだのカードを先に</option>
  <option value="unit">並び：単元名順</option>
 </select>
 <select id="side">
  <option value="img">表：絵・マーク・楽器 → 裏：名称・説明</option>
  <option value="name">表：名称 → 裏：絵・マーク・楽器</option>
 </select>
 <button id="shuf">シャッフル</button>
 <button id="reset">覚えた印を消す</button>
</div>
<div class="ctl" id="show">
 <span style="font-size:.82rem;color:var(--sub)">裏に出す：</span>
 <label class="chk"><input type="checkbox" value="img" checked>絵/図</label>
 <label class="chk"><input type="checkbox" value="t" checked>題名・解答</label>
 <label class="chk"><input type="checkbox" value="a" checked>作者・全文</label>
 <label class="chk"><input type="checkbox" value="y" checked>年・ノート</label>
 <label class="chk"><input type="checkbox" value="m" checked>主義・単元</label>
 <label class="chk"><input type="checkbox" value="r" checked>地域・教科</label>
</div>
<div class="stat"><span id="pos"></span><span id="known"></span></div>
<div id="area"></div>
<div class="nav"><button id="prev">← 前</button><button class="ng" id="no">まだ</button><button class="ok" id="yes">覚えた</button><button id="nxt">次 →</button></div>
<p style="color:var(--sub);font-size:.8rem;margin-top:10px">カードをタップでめくる。キーボードは ←→ で移動、スペースでめくる、↑で覚えた、↓でまだ。</p>
<details class="seo-info">
  <summary>収録教科・テスト対策範囲一覧（全553問）</summary>
  <h2>美術（148問）</h2>
  <p>日本の作品・西洋の作品・アジアの作品の絵画フラッシュカード（題名・作者・制作年・主義・地域）および教科書穴埋め問題。</p>
  <h2>家庭科（151問）</h2>
  <p>消費者としての自覚、購入方法と支払い方法、クレジットカード（三者間契約の図解付き）、消費生活センター・国民生活センター・消費者庁、悪質商法とクーリング・オフ制度、適切な選択と商品選択に役立つ表示マーク15種（PSE・PSC・SG・JIS・G・ウール・エコ・グリーン・再生紙・間伐材・PETボトル等）、消費者基本法、国際消費者機構による「消費者の8つの権利」と「消費者の5つの責任」。</p>
  <h2>体育（80問）</h2>
  <p>水泳（背泳ぎのポイント・泳法用語）、器械運動、陸上競技（リレー・クラウチングスタート等）、ハンドボール（反則・シュート・パス）、卓球（打法・サービスのポイント）。</p>
  <h2>音楽（65問）</h2>
  <p>世界の諸民族の音楽（バグパイプ・バンジョー・グーチン・スティールパン・チャランゴ・カヤグム・ディジェリドゥ・シタール・トーキングドラム・バラフォン・ウード・バラライカ・チャンゴ・ケーナ・サンポーニャ・コラ・ドゥドゥク・ズルナ・ツィター・ウクレレ・ピーパー・タンソ・サウンガウ・タブラーの24種写真付き）、タンソ・ウード・タブラーの解説問題、カンツォーネ『帰れソレントへ』（楽譜・同主調・速度記号）。</p>
  <h2>保健（109問）</h2>
  <p>感染症とその予防（潜伏期間・症状・新興感染症）、感染症対策と食中毒予防の三原則、性感染症・エイズ（HIV）と予防、ヘルスプロモーション・保健所と保健センター・ノーマライゼーション・国民総幸福量（GNH）・医療機関の利用と医薬品の正しい使用。</p>
</details>
</div>
<script>
// 教科メタ情報（表示名・五十音ソート順・単元フィルター定義）
const SUBJ_META = {
  all:    { label: "全教科", order: 0, filters: [["all","ぜんぶ"],["visual","絵・写真・マーク"],["cloze","穴埋め"],["todo","まだのカードだけ"]] },
  art:    { label: "美術",   order: 5, filters: [["all","ぜんぶ"],["jp","日本の作品"],["west","西洋の作品"],["asia","アジアの作品"],["cloze","穴埋め"],["todo","まだのカードだけ"]] },
  home:   { label: "家庭科", order: 2, filters: [["all","ぜんぶ"],["consumer","消費者・支払い"],["credit","クレカ・相談機関"],["trouble","トラブル・法律"],["select","選択・マーク"],["mark","マークだけ"],["rights","消費者基本法・権利と責任"],["rights85","8つの権利・5つの責任"],["todo","まだのカードだけ"]] },
  pe:     { label: "体育",   order: 3, filters: [["all","ぜんぶ"],["swim","水泳"],["gym","器械運動"],["track","陸上競技"],["handball","ハンドボール"],["pingpong","卓球"],["todo","まだのカードだけ"]] },
  music:  { label: "音楽",   order: 1, filters: [["all","ぜんぶ"],["inst","世界の楽器（写真）"],["world","タンソ・ウード・タブラー"],["sorrento","帰れソレントへ"],["todo","まだのカードだけ"]] },
  health: { label: "保健",   order: 4, filters: [["all","ぜんぶ"],["inf1","感染症と予防"],["inf2","対策・食中毒・性感染症"],["aids","エイズ・予防"],["soc","社会の取組・医薬品"],["todo","まだのカードだけ"]] }
};

__MARKS_AND_DIAGRAM__

const MUSIC_IMGS = __MUSIC_IMGS__;

const ART_CARDS = __ART_CARDS__;

const HOME_CARDS = [
__HOME_CARDS__,
  {id:"p7-all-rights",subj:"home",cat:"rights",unit:"8つの権利",note:"ノート7 まとめ",type:"list",
   a:"消費者の8つの権利",
   q:"国際消費者機構が挙げた【消費者の8つの権利】をすべて答えなさい。",
   items:["安全を求める権利","意見が反映される権利","選択する権利","知らされる権利","補償を受ける権利","消費者教育を受ける権利","生活の基本的ニーズが保障される権利","健全な環境を享受する権利"]},
  {id:"p7-all-resp",subj:"home",cat:"rights",unit:"5つの責任",note:"ノート7 まとめ",type:"list",
   a:"消費者の5つの責任",
   q:"国際消費者機構が挙げた【消費者の5つの責任】をすべて答えなさい。",
   items:["批判的意識を持つ責任","主張し、行動する責任","連帯する責任","環境への配慮をする責任","社会的弱者に配慮する責任"]}
];

const PE_CARDS = __PE_CARDS__;
const MUSIC_CARDS = __MUSIC_CARDS__;
const HEALTH_CARDS = __HEALTH_CARDS__;

// 全教科のカードを結合（初期順：美術 → 家庭科 → 体育 → 音楽 → 保健）
const ALL = [...ART_CARDS, ...HOME_CARDS, ...PE_CARDS, ...MUSIC_CARDS, ...HEALTH_CARDS];
ALL.forEach((c, idx) => { c._ord = idx; });

// 既存の学習記録（美術・家庭科）を引き継いで統合保存
const KNOWN_KEY = "study-fc-known-v1";
const SHOW_KEY = "study-fc-show-v1";
let known = {};
try {
  known = JSON.parse(localStorage.getItem(KNOWN_KEY) || "{}");
  const oldArt = JSON.parse(localStorage.getItem("art-known") || "{}");
  Object.keys(oldArt).forEach(k => { if (oldArt[k]) known["art:" + k] = 1; });
  const oldHome = JSON.parse(localStorage.getItem("kateika_fc_known_v1") || "[]");
  if (Array.isArray(oldHome)) oldHome.forEach(k => { known[k] = 1; });
} catch (e) {}
const saveKnown = () => { try { localStorage.setItem(KNOWN_KEY, JSON.stringify(known)); } catch (e) {} };

let show = { img: 1, t: 1, a: 1, y: 1, m: 1, r: 1 };
try { Object.assign(show, JSON.parse(localStorage.getItem(SHOW_KEY) || "{}")); } catch (e) {}

const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, m => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
const fmtQ = q => esc(q).replace(/［ ？ ］/g, '<span class="blank">？</span>');
const fmtSolved = (q, a) => esc(q).replace(/［ ？ ］/g, `<span class="hl">${esc(a)}</span>`);
const isVisual = c => c.type === "art-work" || c.type === "mark" || c.type === "photo" || c.type === "diagram";

let subj = "all";
let filt = "all";
let sortMode = "default";
let list = [];
let i = 0;
let flipped = false;

const shuffle = a => {
  a = a.slice();
  for (let k = a.length - 1; k > 0; k--) {
    const j = Math.random() * (k + 1) | 0;
    [a[k], a[j]] = [a[j], a[k]];
  }
  return a;
};

// 教科ボタン行の生成
function buildSubjBar() {
  const keys = ["all", "art", "home", "pe", "music", "health"];
  $("#subj").innerHTML = keys.map(k => {
    const cnt = k === "all" ? ALL.length : ALL.filter(c => c.subj === k).length;
    return `<button data-s="${k}" class="${k === subj ? "on" : ""}">${SUBJ_META[k].label}<span class="cnt">${cnt}</span></button>`;
  }).join("");
}

// 選択中教科に応じた単元フィルター行の生成
function buildFiltBar() {
  const defs = SUBJ_META[subj].filters;
  if (!defs.some(d => d[0] === filt)) filt = "all";
  $("#filt").innerHTML = defs.map(([k, label]) =>
    `<button data-f="${k}" class="${k === filt ? "on" : ""}">${label}</button>`
  ).join("");
}

function apply(doShuffle = false) {
  let arr = ALL.filter(c => {
    if (subj !== "all" && c.subj !== subj) return false;
    if (filt === "all") return true;
    if (filt === "todo") return !known[c.id];
    if (filt === "visual") return isVisual(c);
    if (filt === "cloze") return c.type === "art-cloze" || c.type === "cloze" || c.type === "list";
    if (filt === "mark") return c.type === "mark";
    if (filt === "rights85") return c.unit === "8つの権利" || c.unit === "5つの責任";
    return c.cat === filt;
  });

  if (doShuffle) {
    arr = shuffle(arr);
  } else if (sortMode === "subj-order") {
    arr.sort((a, b) => (SUBJ_META[a.subj].order - SUBJ_META[b.subj].order) || (a._ord - b._ord));
  } else if (sortMode === "todo-first") {
    arr.sort((a, b) => ((known[a.id] ? 1 : 0) - (known[b.id] ? 1 : 0)) || (a._ord - b._ord));
  } else if (sortMode === "unit") {
    arr.sort((a, b) => a.unit.localeCompare(b.unit, "ja") || (a._ord - b._ord));
  } else {
    arr.sort((a, b) => a._ord - b._ord);
  }

  list = arr;
  i = 0;
  render();
}

function render() {
  const totalKnown = ALL.filter(c => known[c.id]).length;
  if (subj === "all") {
    $("#known").textContent = `覚えた ${totalKnown} / ${ALL.length}`;
  } else {
    const subAll = ALL.filter(c => c.subj === subj);
    const subKnown = subAll.filter(c => known[c.id]).length;
    $("#known").textContent = `${SUBJ_META[subj].label} 覚えた ${subKnown} / ${subAll.length}（全体 ${totalKnown} / ${ALL.length}）`;
  }

  const n = list.length;
  if (!n) {
    $("#pos").textContent = "0 / 0";
    $("#area").innerHTML = `<div class="face" style="position:static;min-height:240px"><div class="empty">${
      filt === "todo" ? "まだのカードはありません！すべて覚えました。" : "このしぼりこみのカードはありません。"
    }</div></div>`;
    return;
  }

  const c = list[i];
  flipped = false;
  $("#pos").textContent = `${i + 1} / ${n}${known[c.id] ? "　✓覚えた" : ""}`;

  const side = $("#side").value;
  const subjLabel = SUBJ_META[c.subj].label;
  const topBar = `<div class="topic"><span><span class="sbadge s-${c.subj}">${subjLabel}</span>${c.type === "art-work" && side === "img" ? "" : esc(c.unit)}</span><span>${c.type === "art-work" && side === "img" ? "" : esc(c.note)}</span></div>`;

  let f = topBar, b = "";

  if (c.type === "art-work") {
    const infoTags = (show.r ? `<span class="tag r">${esc(c.r)}</span>` : "") + (show.m && c.m ? `<span class="tag">${esc(c.m)}</span>` : "");
    const infoBody = (show.a ? `<p class="a">${esc(c.a)}</p>` : "") + (show.y ? `<p class="y">${esc(c.y)}</p>` : "") + (infoTags ? `<div>${infoTags}</div>` : "");
    if (side === "img") {
      f += `<img class="art-full" src="${c.img}" alt="">`;
      b = (show.t ? `<p class="t">${esc(c.t)}</p>` : "") + infoBody;
    } else {
      f += `<p class="t">${esc(c.t)}</p>`;
      b = (show.img ? `<img class="mini" src="${c.img}" alt="">` : "") + (show.t ? `<p class="t" style="font-size:1.1rem">${esc(c.t)}</p>` : "") + infoBody;
    }
  } else if (c.type === "photo") {
    const src = MUSIC_IMGS[c.imgKey];
    if (side === "img") {
      f += `<img src="${src}" alt="" style="max-height:68%;border:1px solid var(--line);background:#fff;padding:4px">` +
           `<div class="region-hint">地域：${esc(c.r)}</div>`;
      if (show.t) b += `<p class="t">${esc(c.a)}</p>`;
      if (show.r || show.m) b += `<div>${show.r ? `<span class="tag r">${esc(c.r)}</span>` : ""}${show.m ? `<span class="tag">${esc(c.unit)}</span>` : ""}</div>`;
      if (show.y) b += `<p class="y">${esc(c.note)}</p>`;
    } else {
      f += `<p class="t">${esc(c.a)}</p>`;
      if (show.img) b += `<img class="mini" src="${src}" alt="" style="border:1px solid var(--line);background:#fff;padding:3px">`;
      if (show.t) b += `<p class="t" style="font-size:1.12rem">${esc(c.a)}</p>`;
      if (show.r || show.m) b += `<div>${show.r ? `<span class="tag r">${esc(c.r)}</span>` : ""}${show.m ? `<span class="tag">${esc(c.unit)}</span>` : ""}</div>`;
      if (show.y) b += `<p class="y">${esc(c.note)}</p>`;
    }
  } else if (c.type === "mark") {
    if (side === "img") {
      f += `<div class="mark-box">${MARKS[c.mark]}</div>`;
      if (show.t) b += `<p class="t">${esc(c.a)}</p>`;
      if (show.a) b += `<p class="a">${esc(c.desc)}</p>`;
    } else {
      f += `<p class="t">${esc(c.a)}</p>`;
      if (show.img) b += `<div class="mark-box mini">${MARKS[c.mark]}</div>`;
      if (show.t) b += `<p class="t" style="font-size:1.1rem">${esc(c.a)}</p>`;
      if (show.a) b += `<p class="a">${esc(c.desc)}</p>`;
    }
    if (show.r || show.m) b += `<div>${show.r ? `<span class="tag r">${subjLabel}</span>` : ""}${show.m ? `<span class="tag">${esc(c.unit)}</span>` : ""}</div>`;
    if (show.y) b += `<p class="y">${esc(c.note)}</p>`;
  } else if (c.type === "diagram") {
    f += `<div class="diag-box">${creditDiagram(c.slot, false)}</div><div class="q" style="font-size:1rem">${fmtQ(c.q)}</div>`;
    if (show.img) b += `<div class="diag-box mini">${creditDiagram(c.slot, true)}</div>`;
    if (show.t) b += `<div class="ans">${esc(c.a)}</div>`;
    if (show.a) b += `<p class="q-sub">${fmtSolved(c.q, c.a)}</p>`;
    if (show.r || show.m) b += `<div>${show.r ? `<span class="tag r">${subjLabel}</span>` : ""}${show.m ? `<span class="tag">${esc(c.unit)}</span>` : ""}</div>`;
    if (show.y) b += `<p class="y">${esc(c.note)}</p>`;
  } else if (c.type === "list") {
    f += `<div class="q">${esc(c.q)}</div>`;
    if (show.t) b += `<div class="ans" style="font-size:1.25rem">${esc(c.a)}</div>`;
    if (show.a) b += `<ol class="ans-list">${c.items.map(it => `<li>${esc(it)}</li>`).join("")}</ol>`;
    if (show.r || show.m) b += `<div>${show.r ? `<span class="tag r">${subjLabel}</span>` : ""}${show.m ? `<span class="tag">${esc(c.unit)}</span>` : ""}</div>`;
    if (show.y) b += `<p class="y">${esc(c.note)}</p>`;
  } else {
    // art-cloze および 各教科 cloze（図・楽譜付きにも対応）
    if (c.imgKey && MUSIC_IMGS[c.imgKey]) {
      f += `<img class="fig-img" src="${MUSIC_IMGS[c.imgKey]}" alt="">`;
    }
    f += `<div class="q">${fmtQ(c.q)}</div>`;
    if (c.imgKey && MUSIC_IMGS[c.imgKey] && show.img) {
      b += `<img class="mini" src="${MUSIC_IMGS[c.imgKey]}" alt="" style="border:1px solid var(--line);background:#fff;padding:2px">`;
    }
    if (show.t) b += `<div class="ans">${esc(c.a)}</div>`;
    if (show.a) b += `<p class="q-sub">${fmtSolved(c.q, c.a)}</p>`;
    if (show.r || show.m) b += `<div>${show.r ? `<span class="tag r">${subjLabel}</span>` : ""}${show.m ? `<span class="tag">${esc(c.unit)}</span>` : ""}</div>`;
    if (show.y) b += `<p class="y">${esc(c.note)}</p>`;
  }

  if (!b) b = `<p class="y">（裏に出す項目がえらばれてない）</p>`;
  $("#area").innerHTML = `<div class="scene"><div class="card" id="card"><div class="face">${f}<span class="hint">タップでめくる</span></div><div class="face back">${b}</div></div></div>`;
  $(".scene").onclick = flip;
}

function flip() {
  const el = $("#card");
  if (!el) return;
  flipped = !flipped;
  el.classList.toggle("flip", flipped);
}

function go(d) {
  if (!list.length) return;
  i = (i + d + list.length) % list.length;
  render();
}

function mark(v) {
  if (!list.length) return;
  const c = list[i];
  if (v) known[c.id] = 1; else delete known[c.id];
  saveKnown();
  if (filt === "todo" && v) {
    list.splice(i, 1);
    if (i >= list.length) i = 0;
    render();
  } else {
    go(1);
  }
}

// イベント登録
$("#subj").onclick = e => {
  const b = e.target.closest("button[data-s]");
  if (!b) return;
  subj = b.dataset.s;
  filt = "all";
  buildSubjBar();
  buildFiltBar();
  apply(false);
};
$("#filt").onclick = e => {
  const b = e.target.closest("button[data-f]");
  if (!b) return;
  document.querySelectorAll("#filt button").forEach(x => x.classList.remove("on"));
  b.classList.add("on");
  filt = b.dataset.f;
  apply(false);
};
$("#sort").onchange = e => { sortMode = e.target.value; apply(false); };
$("#side").onchange = () => render();
$("#shuf").onclick = () => apply(true);
$("#reset").onclick = () => {
  const msg = subj === "all"
    ? "全教科の覚えた印をぜんぶ消す？"
    : `「${SUBJ_META[subj].label}」の覚えた印をぜんぶ消す？`;
  if (!confirm(msg)) return;
  if (subj === "all") {
    known = {};
  } else {
    ALL.forEach(c => { if (c.subj === subj) delete known[c.id]; });
  }
  saveKnown();
  apply(false);
};
document.querySelectorAll("#show input").forEach(x => {
  x.checked = !!show[x.value];
  x.onchange = () => {
    show[x.value] = x.checked ? 1 : 0;
    try { localStorage.setItem(SHOW_KEY, JSON.stringify(show)); } catch (e) {}
    render();
  };
});
$("#prev").onclick = () => go(-1);
$("#nxt").onclick = () => go(1);
$("#yes").onclick = () => mark(1);
$("#no").onclick = () => mark(0);

document.addEventListener("keydown", e => {
  if (e.target.tagName === "SELECT" || e.target.tagName === "INPUT") return;
  if (e.key === "ArrowRight") { e.preventDefault(); go(1); }
  else if (e.key === "ArrowLeft") { e.preventDefault(); go(-1); }
  else if (e.key === " " || e.code === "Space") { e.preventDefault(); flip(); }
  else if (e.key === "ArrowUp") { e.preventDefault(); mark(1); }
  else if (e.key === "ArrowDown") { e.preventDefault(); mark(0); }
});

buildSubjBar();
buildFiltBar();
apply(false);
</script>
</body>
</html>
"""

out_html = (
    html_template
    .replace("__MARKS_AND_DIAGRAM__", marks_and_diagram_js)
    .replace("__MUSIC_IMGS__", json.dumps(music_imgs, ensure_ascii=False))
    .replace("__ART_CARDS__", json.dumps(art_cards, ensure_ascii=False))
    .replace("__HOME_CARDS__", kcards_js_with_subj)
    .replace("__PE_CARDS__", json.dumps(pe_cards, ensure_ascii=False))
    .replace("__MUSIC_CARDS__", json.dumps(music_cards, ensure_ascii=False))
    .replace("__HEALTH_CARDS__", json.dumps(health_cards, ensure_ascii=False))
)

out_path = os.path.join(WORK_DIR, "index.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(out_html)
print(f"BUILT: {out_path} ({len(out_html):,} bytes)")
