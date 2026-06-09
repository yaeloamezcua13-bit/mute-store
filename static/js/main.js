/* MUTE — interacciones globales */
(function () {
  "use strict";

  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];
  const money = (n) =>
    "$" + Number(n).toLocaleString("es-MX", { minimumFractionDigits: 0, maximumFractionDigits: 0 });

  // --- Nav: clase al hacer scroll ---
  const nav = $("#nav");
  const onScroll = () => nav && nav.classList.toggle("scrolled", window.scrollY > 40);
  window.addEventListener("scroll", onScroll);
  onScroll();

  // --- Selector de idioma (toggle al hacer clic, útil en móvil) ---
  const langSwitch = $("#lang-switch");
  const langToggle = $("#lang-toggle");
  if (langSwitch && langToggle) {
    langToggle.addEventListener("click", (e) => {
      e.stopPropagation();
      langSwitch.classList.toggle("open");
    });
    document.addEventListener("click", () => langSwitch.classList.remove("open"));
  }

  // --- Carrito lateral ---
  const drawer = $("#cart-drawer");
  const overlay = $("#cart-overlay");
  const body = $("#cart-body");
  const foot = $("#cart-foot");
  const empty = $("#cart-empty");

  function openCart() {
    drawer.classList.add("open");
    overlay.classList.add("open");
    document.body.style.overflow = "hidden";
    refreshCart();
  }
  function closeCart() {
    drawer.classList.remove("open");
    overlay.classList.remove("open");
    document.body.style.overflow = "";
  }
  $("#cart-toggle") && $("#cart-toggle").addEventListener("click", openCart);
  $("#cart-close") && $("#cart-close").addEventListener("click", closeCart);
  overlay && overlay.addEventListener("click", closeCart);
  document.addEventListener("keydown", (e) => e.key === "Escape" && closeCart());

  function setCount(n) {
    const el = $("#cart-count");
    if (!el) return;
    el.textContent = n;
    el.hidden = n === 0;
  }

  function renderCart(data) {
    setCount(data.cart_count);
    if (!data.items.length) {
      body.innerHTML = "";
      body.hidden = true;
      foot.hidden = true;
      empty.style.display = "flex";
      return;
    }
    empty.style.display = "none";
    body.hidden = false;
    foot.hidden = false;
    body.innerHTML = data.items
      .map(
        (it) => `
      <div class="cart-item" data-id="${it.variant_id}">
        <div class="cart-item-img">
          ${
            it.image
              ? `<img src="${it.image}" alt="${it.name}">`
              : `<div class="ph" style="--ph-color:${it.color_hex}; height:100%;"><span class="ph-logo" style="font-size:11px;">MUTE</span></div>`
          }
        </div>
        <div class="cart-item-info">
          <span class="name">${it.name}</span>
          <span class="opts">${it.color} · ${window.MUTE.i18n.size} ${it.size}</span>
          <div class="cart-item-bottom">
            <div class="cart-qty">
              <button data-act="dec" data-id="${it.variant_id}">−</button>
              <span>${it.quantity}</span>
              <button data-act="inc" data-id="${it.variant_id}">+</button>
            </div>
            <span class="price">${money(it.line_total)}</span>
          </div>
          <button class="remove" data-act="rm" data-id="${it.variant_id}">${window.MUTE.i18n.remove}</button>
        </div>
      </div>`
      )
      .join("");
    $("#cart-subtotal").textContent = money(data.subtotal);
  }

  function post(url, params) {
    return fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": window.MUTE.csrf,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams(params),
    }).then((r) => r.json());
  }

  function refreshCart() {
    fetch(window.MUTE.urls.cartJson)
      .then((r) => r.json())
      .then(renderCart);
  }

  // Delegación: +/-/quitar dentro del carrito
  body &&
    body.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-act]");
      if (!btn) return;
      const id = btn.dataset.id;
      const act = btn.dataset.act;
      const item = btn.closest(".cart-item");
      const qty = parseInt(item.querySelector(".cart-qty span").textContent, 10);
      if (act === "rm") {
        post(window.MUTE.urls.cartRemove, { variant_id: id }).then(renderCart);
      } else {
        const newQty = act === "inc" ? qty + 1 : qty - 1;
        post(window.MUTE.urls.cartUpdate, { variant_id: id, quantity: newQty }).then(renderCart);
      }
    });

  // API global para añadir al carrito (usada por product.js)
  window.MUTE.addToCart = function (variantId, quantity, onDone) {
    post(window.MUTE.urls.cartAdd, { variant_id: variantId, quantity })
      .then((res) => {
        if (res.ok) {
          setCount(res.cart_count);
          openCart();
        }
        onDone && onDone(res);
      })
      .catch(() => onDone && onDone({ ok: false }));
  };
  window.MUTE.openCart = openCart;

  // --- Animaciones de aparición (GSAP) ---
  if (window.gsap) {
    gsap.registerPlugin(ScrollTrigger);
    $$(".reveal").forEach((el) => {
      gsap.to(el, {
        opacity: 1,
        y: 0,
        duration: 0.9,
        ease: "power3.out",
        scrollTrigger: { trigger: el, start: "top 88%" },
      });
    });
    // Estado inicial de los reveals
    gsap.set(".reveal", { opacity: 0, y: 30 });

    // Hero: el logo (eclipse) gira y se desvanece al bajar -> transición a productos
    const hero = document.getElementById("hero");
    if (hero && document.getElementById("hero-logo")) {
      gsap
        .timeline({
          scrollTrigger: { trigger: hero, start: "top top", end: "+=64%", scrub: true, pin: true },
        })
        .to("#hero-logo", { scale: 1.35, opacity: 0, ease: "none" }, 0)
        .to("#hero-ring-img", { rotation: 170, ease: "none" }, 0)
        .to("#hero-scroll", { opacity: 0, ease: "none" }, 0);
    }
  } else {
    $$(".reveal").forEach((el) => (el.style.opacity = 1));
  }
})();
