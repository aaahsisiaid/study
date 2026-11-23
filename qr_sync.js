// =========================================================================
// 外部ライブラリ不要のピュアJS QRエンコーダ（ISO/IEC 18004, Version 1〜12, Level L）
// および 学習記録（覚えた）の同期コード・QR・JSONエクスポート／インポート機能
// =========================================================================
const QR = (() => {
  const ALIGN = [
    null, [], [6,18], [6,22], [6,26], [6,30], [6,34],
    [6,22,38], [6,24,42], [6,26,46], [6,28,50], [6,30,54], [6,32,58]
  ];
  // [ecPerBlock, g1Blocks, g1Data, g2Blocks, g2Data] (Level L)
  const EC_L = [
    null,
    [7,  1, 19, 0, 0],
    [10, 1, 34, 0, 0],
    [15, 1, 55, 0, 0],
    [20, 1, 80, 0, 0],
    [26, 1, 108, 0, 0],
    [18, 2, 68, 0, 0],
    [20, 2, 78, 0, 0],
    [24, 2, 97, 0, 0],
    [30, 2, 116, 0, 0],
    [18, 2, 68, 2, 69],
    [20, 4, 81, 0, 0],
    [24, 2, 92, 2, 93]
  ];

  // GF(256) 演算テーブル（原始多項式 0x11d）
  const EXP = new Uint8Array(512);
  const LOG = new Uint8Array(256);
  let x = 1;
  for (let i = 0; i < 255; i++) {
    EXP[i] = x;
    LOG[x] = i;
    x <<= 1;
    if (x & 256) x ^= 0x11d;
  }
  for (let i = 255; i < 512; i++) EXP[i] = EXP[i - 255];
  const gfMul = (a, b) => (a && b) ? EXP[LOG[a] + LOG[b]] : 0;

  function rsGenPoly(deg) {
    let p = [1];
    for (let i = 0; i < deg; i++) {
      const next = new Array(p.length + 1).fill(0);
      for (let j = 0; j < p.length; j++) {
        next[j] ^= p[j];
        next[j + 1] ^= gfMul(p[j], EXP[i]);
      }
      p = next;
    }
    return p;
  }

  function rsRemainder(data, ecLen) {
    const gen = rsGenPoly(ecLen);
    const res = new Uint8Array(ecLen);
    for (let i = 0; i < data.length; i++) {
      const factor = data[i] ^ res[0];
      for (let j = 0; j < ecLen - 1; j++) res[j] = res[j + 1] ^ gfMul(gen[j + 1], factor);
      res[ecLen - 1] = gfMul(gen[ecLen], factor);
    }
    return res;
  }

  function bchFormat(mask) {
    // Level L = 01 (bits 4..3), mask = 0..7 (bits 2..0)
    const data = (1 << 3) | mask;
    let rem = data << 10;
    for (let i = 4; i >= 0; i--) {
      if ((rem >>> (i + 10)) & 1) rem ^= 0x537 << i;
    }
    return ((data << 10) | rem) ^ 0x5412;
  }

  function bchVersion(ver) {
    let rem = ver << 12;
    for (let i = 5; i >= 0; i--) {
      if ((rem >>> (i + 12)) & 1) rem ^= 0x1f25 << i;
    }
    return (ver << 12) | rem;
  }

  function encode(text) {
    const bytes = new TextEncoder().encode(text);
    // 最小バージョンを選択
    let ver = 0;
    for (let v = 1; v <= 12; v++) {
      const [, b1, d1, b2, d2] = EC_L[v];
      const capBytes = b1 * d1 + b2 * d2;
      const ccBits = v >= 10 ? 16 : 8;
      const neededBits = 4 + ccBits + bytes.length * 8;
      if (Math.ceil(neededBits / 8) <= capBytes) { ver = v; break; }
    }
    if (!ver) throw new Error("QRコードの最大容量を超えています");

    const [ecLen, b1, d1, b2, d2] = EC_L[ver];
    const totalData = b1 * d1 + b2 * d2;
    const ccBits = ver >= 10 ? 16 : 8;

    // ビット列構築（バイトモード 0100）
    const bits = [];
    const pushBits = (val, n) => { for (let i = n - 1; i >= 0; i--) bits.push((val >>> i) & 1); };
    pushBits(0b0100, 4);
    pushBits(bytes.length, ccBits);
    for (const b of bytes) pushBits(b, 8);
    // 終端パターン（最大4bit）
    const maxBits = totalData * 8;
    for (let i = 0; i < 4 && bits.length < maxBits; i++) bits.push(0);
    while (bits.length % 8) bits.push(0);

    const dataCw = [];
    for (let i = 0; i < bits.length; i += 8) {
      let b = 0;
      for (let j = 0; j < 8; j++) b = (b << 1) | bits[i + j];
      dataCw.push(b);
    }
    for (let p = 0; dataCw.length < totalData; p++) dataCw.push(p & 1 ? 0x11 : 0xec);

    // ブロック分割とRS符号生成・インターリーブ
    const blocks = [];
    let off = 0;
    for (let i = 0; i < b1; i++) { blocks.push(dataCw.slice(off, off + d1)); off += d1; }
    for (let i = 0; i < b2; i++) { blocks.push(dataCw.slice(off, off + d2)); off += d2; }
    const ecs = blocks.map(bl => rsRemainder(bl, ecLen));

    const codewords = [];
    const maxDataLen = Math.max(d1, d2);
    for (let i = 0; i < maxDataLen; i++) {
      for (const bl of blocks) if (i < bl.length) codewords.push(bl[i]);
    }
    for (let i = 0; i < ecLen; i++) {
      for (const ec of ecs) codewords.push(ec[i]);
    }

    // マトリクス初期化
    const sz = 17 + 4 * ver;
    const mat = Array.from({ length: sz }, () => new Uint8Array(sz));
    const func = Array.from({ length: sz }, () => new Uint8Array(sz));
    const setFunc = (r, c, v) => {
      if (r >= 0 && r < sz && c >= 0 && c < sz) { mat[r][c] = v ? 1 : 0; func[r][c] = 1; }
    };

    // ファインダパターン＋セパレータ
    for (const [fr, fc] of [[0, 0], [0, sz - 7], [sz - 7, 0]]) {
      for (let dr = -1; dr <= 7; dr++) {
        for (let dc = -1; dc <= 7; dc++) {
          const d = Math.max(Math.abs(dr - 3), Math.abs(dc - 3));
          setFunc(fr + dr, fc + dc, d !== 2 && d !== 4);
        }
      }
    }
    // タイミングパターン
    for (let i = 8; i < sz - 8; i++) {
      setFunc(6, i, (i & 1) === 0);
      setFunc(i, 6, (i & 1) === 0);
    }
    // アライメントパターン
    const pts = ALIGN[ver];
    for (const r of pts) {
      for (const c of pts) {
        if ((r === 6 && c === 6) || (r === 6 && c === pts[pts.length - 1]) || (r === pts[pts.length - 1] && c === 6)) continue;
        for (let dr = -2; dr <= 2; dr++) {
          for (let dc = -2; dc <= 2; dc++) {
            const d = Math.max(Math.abs(dr), Math.abs(dc));
            setFunc(r + dr, c + dc, d !== 1);
          }
        }
      }
    }
    // 形式情報領域の予約＋ダークモジュール
    for (let i = 0; i < 9; i++) {
      if (!func[8][i]) setFunc(8, i, 0);
      if (!func[i][8]) setFunc(i, 8, 0);
    }
    for (let i = 0; i < 8; i++) {
      setFunc(8, sz - 1 - i, 0);
      setFunc(sz - 1 - i, 8, 0);
    }
    setFunc(4 * ver + 9, 8, 1);

    // 型番情報（Version 7以上）
    if (ver >= 7) {
      const vb = bchVersion(ver);
      for (let i = 0; i < 18; i++) {
        const bit = (vb >>> i) & 1;
        const r = (i / 3) | 0, c = sz - 11 + (i % 3);
        setFunc(r, c, bit);
        setFunc(c, r, bit);
      }
    }

    // データビット配置（ジグザグ上り下り）
    const totalBits = codewords.length * 8;
    let bitIdx = 0;
    for (let right = sz - 1; right >= 1; right -= 2) {
      if (right === 6) right = 5;
      const upward = (((right + 1) & 2) === 0);
      for (let step = 0; step < sz; step++) {
        const r = upward ? (sz - 1 - step) : step;
        for (let k = 0; k < 2; k++) {
          const c = right - k;
          if (!func[r][c]) {
            let bit = 0;
            if (bitIdx < totalBits) bit = (codewords[bitIdx >>> 3] >>> (7 - (bitIdx & 7))) & 1;
            mat[r][c] = bit;
            bitIdx++;
          }
        }
      }
    }

    // マスク関数（0〜7）と簡易ペナルティ評価で最適マスクを選択
    const maskFn = [
      (r, c) => ((r + c) & 1) === 0,
      (r, c) => (r & 1) === 0,
      (r, c) => c % 3 === 0,
      (r, c) => (r + c) % 3 === 0,
      (r, c) => (((r >> 1) + ((c / 3) | 0)) & 1) === 0,
      (r, c) => ((r * c) & 1) + ((r * c) % 3) === 0,
      (r, c) => ((((r * c) & 1) + ((r * c) % 3)) & 1) === 0,
      (r, c) => ((((r + c) & 1) + ((r * c) % 3)) & 1) === 0
    ];

    function applyFormat(grid, m) {
      const fb = bchFormat(m);
      for (let i = 0; i <= 5; i++) grid[8][i] = (fb >>> (14 - i)) & 1;
      grid[8][7] = (fb >>> 8) & 1;
      grid[8][8] = (fb >>> 7) & 1;
      grid[7][8] = (fb >>> 6) & 1;
      for (let i = 9; i < 15; i++) grid[14 - i][8] = (fb >>> (14 - i)) & 1;
      for (let i = 0; i < 8; i++) grid[8][sz - 1 - i] = (fb >>> i) & 1;
      for (let i = 0; i < 7; i++) grid[sz - 1 - i][8] = (fb >>> (14 - i)) & 1;
    }

    function penalty(grid) {
      let p = 0;
      for (let r = 0; r < sz; r++) {
        let run = 1, runC = 1;
        for (let c = 1; c < sz; c++) {
          if (grid[r][c] === grid[r][c - 1]) run++; else { if (run >= 5) p += run - 2; run = 1; }
          if (grid[c][r] === grid[c - 1][r]) runC++; else { if (runC >= 5) p += runC - 2; runC = 1; }
        }
        if (run >= 5) p += run - 2;
        if (runC >= 5) p += runC - 2;
      }
      for (let r = 0; r < sz - 1; r++) {
        for (let c = 0; c < sz - 1; c++) {
          const v = grid[r][c];
          if (v === grid[r][c + 1] && v === grid[r + 1][c] && v === grid[r + 1][c + 1]) p += 3;
        }
      }
      let dark = 0;
      for (let r = 0; r < sz; r++) for (let c = 0; c < sz; c++) dark += grid[r][c];
      p += Math.abs(((dark * 100 / (sz * sz)) - 50) / 5 | 0) * 10;
      return p;
    }

    let bestGrid = null, bestPen = 1e9;
    for (let m = 0; m < 8; m++) {
      const g = mat.map(row => row.slice());
      const fn = maskFn[m];
      for (let r = 0; r < sz; r++) {
        for (let c = 0; c < sz; c++) {
          if (!func[r][c] && fn(r, c)) g[r][c] ^= 1;
        }
      }
      applyFormat(g, m);
      const pen = penalty(g);
      if (pen < bestPen) { bestPen = pen; bestGrid = g; }
    }
    return { size: sz, grid: bestGrid, version: ver };
  }

  function toSvg(text, quiet = 4) {
    const { size, grid } = encode(text);
    const full = size + quiet * 2;
    let d = "";
    for (let r = 0; r < size; r++) {
      for (let c = 0; c < size; c++) {
        if (grid[r][c]) d += `M${c + quiet},${r + quiet}h1v1h-1z`;
      }
    }
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${full} ${full}" shape-rendering="crispEdges"><rect width="${full}" height="${full}" fill="#fff"/><path d="${d}" fill="#000"/></svg>`;
  }

  function toCanvas(text, scale = 6, quiet = 4) {
    const { size, grid } = encode(text);
    const full = size + quiet * 2;
    const cv = document.createElement("canvas");
    cv.width = cv.height = full * scale;
    const ctx = cv.getContext("2d");
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, cv.width, cv.height);
    ctx.fillStyle = "#000";
    for (let r = 0; r < size; r++) {
      for (let c = 0; c < size; c++) {
        if (grid[r][c]) ctx.fillRect((c + quiet) * scale, (r + quiet) * scale, scale, scale);
      }
    }
    return cv;
  }

  return { encode, toSvg, toCanvas };
})();

// =========================================================================
// 学習データ（覚えた）の圧縮同期コード＆JSONエクスポート・インポート
// =========================================================================
const SYNC_URL_BASE = "https://aaahsisiaid.github.io/study/";

function encodeSyncCode() {
  const n = ALL.length;
  const byteLen = Math.ceil(n / 8);
  const buf = new Uint8Array(3 + byteLen);
  buf[0] = 1; // バージョン1
  buf[1] = (n >> 8) & 0xff;
  buf[2] = n & 0xff;
  for (let idx = 0; idx < n; idx++) {
    if (known[ALL[idx].id]) buf[3 + (idx >> 3)] |= (1 << (idx & 7));
  }
  let bin = "";
  for (let k = 0; k < buf.length; k++) bin += String.fromCharCode(buf[k]);
  return "S1_" + btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function decodeSyncInput(rawText) {
  const s = String(rawText || "").trim();
  if (!s) throw new Error("データが空です");

  // 1. JSONバックアップ形式の場合
  if (s.startsWith("{")) {
    const obj = JSON.parse(s);
    if (Array.isArray(obj.knownIds)) {
      const validSet = new Set(ALL.map(c => c.id));
      const ids = obj.knownIds.filter(id => validSet.has(id));
      return { ids, source: "JSON" };
    }
    if (typeof obj.code === "string") return decodeSyncInput(obj.code);
    throw new Error("対応していないJSON形式です");
  }

  // 2. URL（#sync=... または ?sync=...）から同期コードを抽出
  let code = s;
  const m = s.match(/(?:[#?&]sync=)(S1_[A-Za-z0-9_-]+)/);
  if (m) code = m[1];
  else {
    const m2 = s.match(/(S1_[A-Za-z0-9_-]+)/);
    if (m2) code = m2[1];
  }
  if (!code.startsWith("S1_")) throw new Error("同期コード（S1_...）またはJSONファイルが見つかりませんでした");

  let b64 = code.slice(3).replace(/-/g, "+").replace(/_/g, "/");
  while (b64.length % 4) b64 += "=";
  const bin = atob(b64);
  const buf = new Uint8Array(bin.length);
  for (let k = 0; k < bin.length; k++) buf[k] = bin.charCodeAt(k);
  if (buf.length < 4 || buf[0] !== 1) throw new Error("同期コードのバージョンが不正です");
  const count = (buf[1] << 8) | buf[2];
  const ids = [];
  const limit = Math.min(count, ALL.length);
  for (let idx = 0; idx < limit; idx++) {
    if ((buf[3 + (idx >> 3)] >> (idx & 7)) & 1) ids.push(ALL[idx].id);
  }
  return { ids, source: "同期コード" };
}

function applyImportedIds(ids, mode) {
  if (mode === "replace") known = {};
  ids.forEach(id => { known[id] = 1; });
  saveKnown();
  apply(false);
}
