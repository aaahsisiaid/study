// =========================================================================
// データ同期・バックアップモーダルUI（QR・同期コード・JSONファイル）
// =========================================================================
(function initSyncUI() {
  const modal = $("#sync-modal");
  if (!modal) return;

  let qrMode = IS_OFFLINE_BUILD ? "code" : "url"; // url | code
  let scanStream = null;
  let scanRaf = 0;
  let jsqrPromise = null;

  const setMsg = (txt, isErr = false) => {
    const el = $("#sync-msg");
    el.textContent = txt || "";
    el.style.color = isErr ? "var(--ng)" : "var(--ok)";
  };

  function getCurrentPayload() {
    const code = encodeSyncCode();
    return qrMode === "url" ? `${SYNC_URL_BASE}#sync=${code}` : code;
  }

  function renderExport() {
    const code = encodeSyncCode();
    const payload = getCurrentPayload();
    const knownCount = ALL.filter(c => known[c.id]).length;
    $("#sync-summary").textContent = `現在の「覚えた」記録：${knownCount} / ${ALL.length} 問`;
    $("#sync-code-out").value = code;
    $("#qr-mode-url").classList.toggle("on", qrMode === "url");
    $("#qr-mode-code").classList.toggle("on", qrMode === "code");
    $("#qr-hint").textContent = qrMode === "url"
      ? "スマホの標準カメラで読み取ってリンクを開くだけで自動取り込みできます（完全オフライン生成）"
      : "ネットなしの端末同士で読み取る用（S1_... の同期コードのみをQR化）";
    try {
      $("#qr-wrap").innerHTML = QR.toSvg(payload, 4);
    } catch (e) {
      $("#qr-wrap").innerHTML = `<p style="color:var(--ng);font-size:.85rem">${esc(e.message)}</p>`;
    }
  }

  function openModal(tab = "export") {
    setMsg("");
    renderExport();
    switchTab(tab);
    modal.classList.add("open");
  }

  function closeModal() {
    stopCamera();
    modal.classList.remove("open");
  }

  function switchTab(tab) {
    document.querySelectorAll(".sync-tabs button").forEach(b => b.classList.toggle("on", b.dataset.tab === tab));
    $("#pane-export").style.display = tab === "export" ? "" : "none";
    $("#pane-import").style.display = tab === "import" ? "" : "none";
    if (tab !== "import") stopCamera();
    if (tab === "export") renderExport();
  }

  function getImportMode() {
    const el = document.querySelector('input[name="imp-mode"]:checked');
    return el ? el.value : "merge";
  }

  function doImportText(raw, labelPrefix = "") {
    try {
      const { ids, source } = decodeSyncInput(raw);
      const mode = getImportMode();
      const modeLabel = mode === "replace" ? "上書き" : "追加（マージ）";
      applyImportedIds(ids, mode);
      renderExport();
      setMsg(`${labelPrefix}${source}から ${ids.length} 問の「覚えた」を${modeLabel}しました！`);
      return true;
    } catch (e) {
      setMsg(`読み込みエラー：${e.message}`, true);
      return false;
    }
  }

  // 通常版のみ：BarcodeDetector非対応ブラウザでQRスキャンを押した時だけjsQRを動的ロード
  function loadJsQR() {
    if (IS_OFFLINE_BUILD) return Promise.resolve(null);
    if (window.jsQR) return Promise.resolve(window.jsQR);
    if (!jsqrPromise) {
      jsqrPromise = new Promise(resolve => {
        const sc = document.createElement("script");
        sc.src = "https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js";
        sc.onload = () => resolve(window.jsQR || null);
        sc.onerror = () => resolve(null);
        document.head.appendChild(sc);
      });
    }
    return jsqrPromise;
  }

  async function detectQrFromSource(source, w, h) {
    // 1. ブラウザ標準 BarcodeDetector（外部ライブラリゼロ・オフライン対応）
    if ("BarcodeDetector" in window) {
      try {
        const det = new window.BarcodeDetector({ formats: ["qr_code"] });
        const codes = await det.detect(source);
        if (codes && codes.length && codes[0].rawValue) return codes[0].rawValue;
      } catch (e) {}
    }
    // 2. 通常版フォールバック（jsQR）
    if (!IS_OFFLINE_BUILD) {
      const jsqr = await loadJsQR();
      if (jsqr) {
        const cv = document.createElement("canvas");
        cv.width = w; cv.height = h;
        const ctx = cv.getContext("2d", { willReadFrequently: true });
        ctx.drawImage(source, 0, 0, w, h);
        const imgData = ctx.getImageData(0, 0, w, h);
        const res = jsqr(imgData.data, w, h);
        if (res && res.data) return res.data;
      }
    }
    return null;
  }

  function stopCamera() {
    if (scanRaf) { cancelAnimationFrame(scanRaf); scanRaf = 0; }
    if (scanStream) {
      scanStream.getTracks().forEach(t => t.stop());
      scanStream = null;
    }
    const camBox = $("#cam-box");
    if (camBox) camBox.style.display = "none";
  }

  async function startCamera() {
    setMsg("");
    if (IS_OFFLINE_BUILD && !("BarcodeDetector" in window)) {
      setMsg("このブラウザはオフラインQRカメラ読取（BarcodeDetector）に未対応です。下の「同期コード貼付」または「JSONファイル」をご利用ください。", true);
      return;
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setMsg("カメラにアクセスできません（HTTPS環境または対応ブラウザが必要です）。QR画像読取・同期コード貼付をご利用ください。", true);
      return;
    }
    try {
      if (!("BarcodeDetector" in window) && !IS_OFFLINE_BUILD) {
        setMsg("QRスキャナを準備中...");
        const jsqr = await loadJsQR();
        if (!jsqr) {
          setMsg("オフラインのためQRカメラ読取ライブラリを取得できませんでした。同期コード貼付またはJSONをご利用ください。", true);
          return;
        }
      }
      scanStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
      const video = $("#cam-video");
      video.srcObject = scanStream;
      await video.play();
      $("#cam-box").style.display = "";
      setMsg("QRコードをカメラにかざしてください...");

      const tick = async () => {
        if (!scanStream) return;
        if (video.readyState >= 2 && video.videoWidth > 0) {
          const val = await detectQrFromSource(video, video.videoWidth, video.videoHeight);
          if (val) {
            stopCamera();
            $("#sync-code-in").value = val;
            doImportText(val, "QRスキャン成功！");
            return;
          }
        }
        scanRaf = requestAnimationFrame(tick);
      };
      scanRaf = requestAnimationFrame(tick);
    } catch (e) {
      stopCamera();
      setMsg(`カメラ起動に失敗しました：${e.message || e}`, true);
    }
  }

  // イベント登録
  $("#sync-open").onclick = () => openModal("export");
  $("#sync-close").onclick = closeModal;
  modal.onclick = e => { if (e.target === modal) closeModal(); };
  document.querySelectorAll(".sync-tabs button").forEach(b => {
    b.onclick = () => switchTab(b.dataset.tab);
  });
  $("#qr-mode-url").onclick = () => { qrMode = "url"; renderExport(); };
  $("#qr-mode-code").onclick = () => { qrMode = "code"; renderExport(); };

  $("#btn-save-qr").onclick = () => {
    try {
      const cv = QR.toCanvas(getCurrentPayload(), 8, 4);
      const a = document.createElement("a");
      a.href = cv.toDataURL("image/png");
      a.download = `study-sync-qr-${new Date().toISOString().slice(0,10)}.png`;
      a.click();
      setMsg("QRコード画像（PNG）を保存しました！");
    } catch (e) {
      setMsg(`QR保存エラー：${e.message}`, true);
    }
  };

  $("#btn-copy-code").onclick = async () => {
    const code = encodeSyncCode();
    try {
      await navigator.clipboard.writeText(code);
      setMsg("同期コードをコピーしました！");
    } catch (e) {
      $("#sync-code-out").select();
      document.execCommand("copy");
      setMsg("同期コードをコピーしました！");
    }
  };

  $("#btn-copy-url").onclick = async () => {
    const url = `${SYNC_URL_BASE}#sync=${encodeSyncCode()}`;
    try {
      await navigator.clipboard.writeText(url);
      setMsg("同期用URLをコピーしました！（LINEやメモに貼って別端末で開けます）");
    } catch (e) {
      setMsg("コピーに失敗しました。コードを手動コピーしてください。", true);
    }
  };

  $("#btn-dl-json").onclick = () => {
    const knownIds = ALL.filter(c => known[c.id]).map(c => c.id);
    const data = {
      format: "study-fc-v1",
      exportedAt: new Date().toISOString(),
      totalCards: ALL.length,
      knownCount: knownIds.length,
      code: encodeSyncCode(),
      knownIds
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `study-flashcards-backup-${new Date().toISOString().slice(0,10)}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setMsg(`JSONバックアップ（覚えた ${knownIds.length} 問）をダウンロードしました！`);
  };

  $("#btn-imp-code").onclick = () => doImportText($("#sync-code-in").value);

  $("#file-imp-json").onchange = e => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => doImportText(reader.result, "JSON読み込み成功！");
    reader.readAsText(file);
    e.target.value = "";
  };

  $("#btn-cam-scan").onclick = startCamera;
  $("#btn-cam-stop").onclick = () => { stopCamera(); setMsg("カメラを停止しました"); };

  $("#file-imp-qr").onchange = async e => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    e.target.value = "";
    if (IS_OFFLINE_BUILD && !("BarcodeDetector" in window)) {
      setMsg("このブラウザはオフラインQR画像読取（BarcodeDetector）に未対応です。同期コード貼付またはJSONファイルをご利用ください。", true);
      return;
    }
    setMsg("QR画像を解析中...");
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = async () => {
      try {
        const val = await detectQrFromSource(img, img.naturalWidth, img.naturalHeight);
        if (val) {
          $("#sync-code-in").value = val;
          doImportText(val, "QR画像読取成功！");
        } else {
          setMsg("画像からQRコードを読み取れませんでした。明るくピントの合った画像でお試しください。", true);
        }
      } finally {
        URL.revokeObjectURL(url);
      }
    };
    img.onerror = () => { URL.revokeObjectURL(url); setMsg("画像の読み込みに失敗しました。", true); };
    img.src = url;
  };

  // URLハッシュ（#sync=S1_...）からの自動インポート確認
  function checkHashSync() {
    const hash = location.hash || location.search || "";
    const m = hash.match(/(?:[#?&]sync=)(S1_[A-Za-z0-9_-]+)/);
    if (!m) return;
    try {
      const { ids } = decodeSyncInput(m[1]);
      const banner = $("#hash-banner");
      $("#hash-banner-txt").textContent = `QR / 同期リンクから「覚えた」記録（${ids.length} 問）を受け取りました！`;
      banner.style.display = "";
      const clearHash = () => {
        banner.style.display = "none";
        try { history.replaceState(null, "", location.pathname); } catch (e) { location.hash = ""; }
      };
      $("#hash-merge").onclick = () => { applyImportedIds(ids, "merge"); clearHash(); };
      $("#hash-replace").onclick = () => { applyImportedIds(ids, "replace"); clearHash(); };
      $("#hash-cancel").onclick = clearHash;
    } catch (e) {}
  }

  checkHashSync();
  window.addEventListener("hashchange", checkHashSync);
})();
