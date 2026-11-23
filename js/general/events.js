/* ========================================
   BLINK CONTROL: WebSocket + Scanning
   NEXT / PREVIOUS = move highlight
   CONFIRM = click highlighted element
======================================== */

(function () {
  const WS_URL = "ws://127.0.0.1:8000/ws/events";

  let socket = null;
  let retryMs = 500;
  let current = null;
  let serverUp = false;
  let cvUp = false;
  let face = null;

  /* ---------- styles + UI ---------- */

  const style = document.createElement("style");
  style.textContent = `
    .blink-focus {
      outline: 5px solid #facc15 !important;
      outline-offset: 3px !important;
      box-shadow: 0 0 18px rgba(250, 204, 21, 0.9) !important;
    }
    #blinkProgress {
      position: fixed; top: 0; left: 0; height: 6px; width: 0;
      background: #22c55e; z-index: 99999; transition: width 0.08s linear;
    }
    #blinkBadge {
      position: fixed; bottom: 10px; left: 10px; z-index: 99999;
      padding: 6px 12px; border-radius: 999px; font: 13px sans-serif;
      color: #fff; background: #475569; opacity: 0.9;
    }
  `;
  document.head.appendChild(style);

  const progressBar = document.createElement("div");
  progressBar.id = "blinkProgress";
  document.body.appendChild(progressBar);

  const badge = document.createElement("div");
  badge.id = "blinkBadge";
  document.body.appendChild(badge);

  function renderBadge() {
    if (!serverUp) {
      badge.textContent = "Server offline";
      badge.style.background = "#dc2626";
    } else if (!cvUp) {
      badge.textContent = "Server OK | CV offline";
      badge.style.background = "#d97706";
    } else {
      badge.textContent = face === false ? "CV OK | no face" : "CV OK | face detected";
      badge.style.background = face === false ? "#d97706" : "#16a34a";
    }
  }

  /* ---------- scanning navigation ---------- */

  function getItems() {
    const root = document.querySelector("dialog[open]") || document.body;
    return Array.from(root.querySelectorAll("button, a[href]")).filter(
      (el) => !el.disabled && el.getClientRects().length > 0
    );
  }

  function clearFocus() {
    if (current) current.classList.remove("blink-focus");
    current = null;
  }

  function setFocus(el) {
    if (current) current.classList.remove("blink-focus");
    current = el;
    if (current) {
      current.classList.add("blink-focus");
      current.scrollIntoView({ block: "nearest", inline: "nearest" });
    }
  }

  function move(step) {
    const items = getItems();
    if (!items.length) return;

    let index = items.indexOf(current);
    if (index < 0) {
      index = step > 0 ? 0 : items.length - 1;
    } else {
      index = (index + step + items.length) % items.length;
    }
    setFocus(items[index]);
  }

  function confirm() {
    if (!current || !getItems().includes(current)) return;

    const target = current;
    clearFocus();
    target.click();

    // after click (dialog may open/close) start from first item of new context
    setTimeout(() => move(1), 80);
  }

  function handleGesture(msg) {
    if (msg.event === "NEXT") move(1);
    else if (msg.event === "PREVIOUS") move(-1);
    else if (msg.event === "CONFIRM") confirm();
  }

  /* ---------- WebSocket ---------- */

  function handleMessage(msg) {
    if (msg.type === "gesture") {
      handleGesture(msg);
      window.dispatchEvent(new CustomEvent("blink:gesture", { detail: msg }));
    } else if (msg.type === "progress") {
      progressBar.style.width = Math.round(msg.value * 100) + "%";
      window.dispatchEvent(new CustomEvent("blink:progress", { detail: msg }));
    } else if (msg.type === "status") {
      cvUp = true;
      face = msg.face;
      renderBadge();
    } else if (msg.type === "cv_connection") {
      cvUp = msg.connected;
      if (!cvUp) face = null;
      renderBadge();
    }
  }

  function connect() {
    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      serverUp = true;
      retryMs = 500;
      renderBadge();
    };

    socket.onmessage = (e) => {
      try {
        handleMessage(JSON.parse(e.data));
      } catch (err) {
        console.warn("Bad message", err);
      }
    };

    socket.onclose = () => {
      serverUp = false;
      cvUp = false;
      face = null;
      renderBadge();
      setTimeout(connect, retryMs);
      retryMs = Math.min(retryMs * 2, 5000);
    };

    socket.onerror = () => socket.close();
  }

  /* ---------- keyboard fallback for testing (no camera) ---------- */

  document.addEventListener("keydown", (e) => {
    const tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea") return;

    if (e.key === "ArrowRight") { e.preventDefault(); move(1); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); move(-1); }
    else if (e.key === "Enter" && current) { e.preventDefault(); confirm(); }
  });

  renderBadge();
  connect();
})();