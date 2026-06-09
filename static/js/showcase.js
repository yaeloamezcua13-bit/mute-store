/* MUTE — showcase deslizable de características (scroll horizontal con pin) */
(function () {
  "use strict";
  const section = document.querySelector("[data-showcase]");
  if (!section || !window.gsap) return;

  const track = section.querySelector(".showcase-track");
  const panels = [...track.querySelectorAll(".feature-panel")];
  const progress = section.querySelector("[data-progress]");
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Crea los puntos de progreso (uno por panel)
  if (progress) {
    panels.forEach((_, i) => {
      const dot = document.createElement("span");
      if (i === 0) dot.classList.add("on");
      progress.appendChild(dot);
    });
  }
  const dots = progress ? [...progress.children] : [];

  function setActive(idx) {
    dots.forEach((d, i) => d.classList.toggle("on", i === idx));
  }

  if (reduce) {
    // Sin animación: apila los paneles verticalmente
    track.style.flexDirection = "column";
    panels.forEach((p) => (p.style.width = "100%"));
    return;
  }

  gsap.registerPlugin(ScrollTrigger);

  const getDistance = () => track.scrollWidth - window.innerWidth;

  const horizontal = gsap.to(track, {
    x: () => -getDistance(),
    ease: "none",
    scrollTrigger: {
      trigger: section,
      pin: true,
      scrub: 1,
      start: "top top",
      end: () => "+=" + getDistance(),
      invalidateOnRefresh: true,
      onUpdate: (self) => {
        const idx = Math.round(self.progress * (panels.length - 1));
        setActive(idx);
      },
    },
  });

  // Reveal del contenido de cada panel (ligado al desplazamiento horizontal)
  panels.forEach((panel) => {
    const text = panel.querySelector(".feature-text");
    if (!text) return;
    gsap.from(text.children, {
      opacity: 0,
      y: 30,
      stagger: 0.08,
      duration: 0.6,
      scrollTrigger: {
        trigger: panel,
        containerAnimation: horizontal,
        start: "left 70%",
      },
    });
  });
})();
