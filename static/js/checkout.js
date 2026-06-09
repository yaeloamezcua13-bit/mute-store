/* MUTE — checkout: recalcula envío y total en vivo según el país / CP */
(function () {
  "use strict";
  const $ = (s) => document.querySelector(s);

  const countrySel = $("#id_country");
  const postal = $("#id_postal_code");
  const banner = $("#ship-banner");
  const payBtn = $("#pay-btn");
  if (!countrySel) return;

  const money2 = (n) =>
    "$" + Number(n).toLocaleString("es-MX", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  function flash(el) {
    if (!el) return;
    el.style.color = "var(--accent)";
    setTimeout(() => (el.style.color = ""), 600);
  }

  function update() {
    const country = countrySel.value;
    const url = window.MUTE.urls.shipping + "?country=" + encodeURIComponent(country);
    fetch(url)
      .then((r) => r.json())
      .then((d) => {
        $("#bd-subtotal").textContent = money2(d.subtotal);
        $("#bd-base").textContent = money2(d.base);
        $("#bd-iva").textContent = money2(d.iva);
        $("#bd-total").textContent = money2(d.total);

        const shipEl = $("#bd-shipping");
        const i18n = window.MUTE.i18n;
        if (d.free_shipping) {
          shipEl.innerHTML = '<span class="free">' + i18n.free + "</span>";
          banner.className = "ship-banner free";
          banner.innerHTML = i18n.freeBanner;
        } else {
          shipEl.textContent = money2(d.shipping);
          banner.className = "ship-banner intl";
          banner.innerHTML = i18n.intlBanner.replace("{x}", money2(d.shipping));
        }
        flash($("#bd-total"));
        flash(shipEl);
      });
  }

  // Detección automática: al cambiar país o código postal se recalcula el total
  countrySel.addEventListener("change", update);
  postal && postal.addEventListener("blur", update);

  // Etiqueta del botón con el total
  const form = $("#checkout-form");
  form &&
    form.addEventListener("submit", () => {
      payBtn.textContent = window.MUTE.i18n.redirecting;
      payBtn.disabled = true;
    });
})();
