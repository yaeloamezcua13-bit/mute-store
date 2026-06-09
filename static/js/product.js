/* MUTE — página de producto: color, talla, cantidad, agregar al carrito */
(function () {
  "use strict";
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];

  const mapEl = $("#variant-map");
  if (!mapEl) return;
  const variantMap = JSON.parse(mapEl.textContent); // {colorId: {size: {id, stock}}}

  let colorId = $(".color-opt.active")?.dataset.colorId || Object.keys(variantMap)[0];
  let size = null;

  const stockHint = $("#stock-hint");
  const addBtn = $("#add-to-cart");
  const qtyInput = $("#qty");
  const visual = $("#pd-visual");
  const imgEl = $("#pd-img");
  const thumbsEl = $("#pd-thumbs");
  let imagesMap = {};
  try {
    imagesMap = JSON.parse($("#images-map").textContent);
  } catch (e) {}

  function setMain(url) {
    if (url && imgEl) {
      imgEl.src = url;
      imgEl.style.display = "";
      if (visual) visual.style.display = "none";
    } else {
      if (imgEl) imgEl.style.display = "none";
      if (visual) visual.style.display = "";
    }
  }

  function renderThumbs(urls) {
    if (!thumbsEl) return;
    thumbsEl.innerHTML = "";
    if (urls.length <= 1) return; // sin tira si solo hay una foto
    urls.forEach((u, i) => {
      const b = document.createElement("button");
      b.className = "pd-thumb" + (i === 0 ? " active" : "");
      b.innerHTML = `<img src="${u}" alt="">`;
      b.addEventListener("click", () => {
        setMain(u);
        [...thumbsEl.children].forEach((c) => c.classList.remove("active"));
        b.classList.add("active");
      });
      thumbsEl.appendChild(b);
    });
  }

  function showColorVisual(opt) {
    const urls = imagesMap[opt.dataset.colorId] || [];
    if (urls.length) {
      setMain(urls[0]);
    } else {
      setMain(opt.dataset.image || null);
      if (visual) visual.style.setProperty("--ph-color", opt.dataset.hex);
    }
    renderThumbs(urls);
  }

  function refreshSizes() {
    const sizes = variantMap[colorId] || {};
    $$(".size-opt").forEach((btn) => {
      const info = sizes[btn.dataset.size];
      const ok = info && info.stock > 0;
      btn.disabled = !ok;
      btn.classList.remove("active");
    });
    size = null;
    addBtn.disabled = true;
    stockHint.textContent = window.MUTE.i18n.selectSize;
    stockHint.classList.remove("low");
  }

  // Colores
  $$(".color-opt").forEach((opt) => {
    opt.addEventListener("click", () => {
      $$(".color-opt").forEach((o) => o.classList.remove("active"));
      opt.classList.add("active");
      colorId = opt.dataset.colorId;
      $("#color-name").textContent = opt.dataset.colorName;
      showColorVisual(opt);
      refreshSizes();
    });
  });

  // Tallas
  $$(".size-opt").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (btn.disabled) return;
      $$(".size-opt").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      size = btn.dataset.size;
      const info = variantMap[colorId][size];
      addBtn.disabled = false;
      if (info.stock <= 5) {
        stockHint.textContent = window.MUTE.i18n.onlyLeft.replace("{n}", info.stock);
        stockHint.classList.add("low");
      } else {
        stockHint.textContent = window.MUTE.i18n.available;
        stockHint.classList.remove("low");
      }
    });
  });

  // Cantidad
  $("#qty-minus").addEventListener("click", () => {
    qtyInput.value = Math.max(1, parseInt(qtyInput.value, 10) - 1);
  });
  $("#qty-plus").addEventListener("click", () => {
    qtyInput.value = parseInt(qtyInput.value, 10) + 1;
  });

  // Agregar al carrito
  addBtn.addEventListener("click", () => {
    if (!size) return;
    const variant = variantMap[colorId][size];
    const qty = parseInt(qtyInput.value, 10);
    const original = addBtn.textContent;
    addBtn.textContent = window.MUTE.i18n.adding;
    addBtn.disabled = true;
    window.MUTE.addToCart(variant.id, qty, (res) => {
      addBtn.textContent = res.ok ? window.MUTE.i18n.added : window.MUTE.i18n.error;
      setTimeout(() => {
        addBtn.textContent = original;
        addBtn.disabled = false;
      }, 1400);
    });
  });

  // Inicializa la galería con el color activo
  const activeColor = $(".color-opt.active");
  if (activeColor) showColorVisual(activeColor);
  refreshSizes();
})();
