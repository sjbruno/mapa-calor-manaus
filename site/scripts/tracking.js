(() => {
  const ENDPOINT = "/api/track";
  const SESSION_KEY = "moa_sid";
  const SECTIONS_SEEN_KEY = "moa_sections_seen";

  function uuid() {
    if (crypto.randomUUID) return crypto.randomUUID();
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  // Vive só no sessionStorage: some quando a aba fecha, não é reidentificável entre sessões.
  function getSessionId() {
    try {
      let id = sessionStorage.getItem(SESSION_KEY);
      if (!id) {
        id = uuid();
        sessionStorage.setItem(SESSION_KEY, id);
      }
      return id;
    } catch {
      return uuid();
    }
  }

  function getSeenSections() {
    try {
      return new Set(JSON.parse(sessionStorage.getItem(SECTIONS_SEEN_KEY) || "[]"));
    } catch {
      return new Set();
    }
  }

  function saveSeenSections(set) {
    try {
      sessionStorage.setItem(SECTIONS_SEEN_KEY, JSON.stringify([...set]));
    } catch {
      // sessionStorage indisponível (modo privado etc.): sem persistência, sem problema.
    }
  }

  const sessionId = getSessionId();
  const deviceType = window.matchMedia("(max-width: 768px)").matches ? "mobile" : "desktop";

  function send(event, extra) {
    const payload = JSON.stringify({
      event,
      session_id: sessionId,
      device_type: deviceType,
      path: location.pathname,
      ...extra,
    });
    if (navigator.sendBeacon) {
      navigator.sendBeacon(ENDPOINT, new Blob([payload], { type: "application/json" }));
    } else {
      fetch(ENDPOINT, { method: "POST", body: payload, keepalive: true }).catch(() => {});
    }
  }

  function utm(name) {
    return new URLSearchParams(location.search).get(name) || undefined;
  }

  function referrerDomain() {
    if (!document.referrer) return undefined;
    try {
      return new URL(document.referrer).hostname;
    } catch {
      return undefined;
    }
  }

  send("pageview", {
    referrer_domain: referrerDomain(),
    utm_source: utm("utm_source"),
    utm_medium: utm("utm_medium"),
    utm_campaign: utm("utm_campaign"),
    utm_content: utm("utm_content"),
    utm_term: utm("utm_term"),
  });

  // Seções: "section" marca 1x por sessão que a pessoa viu; "section_time" mede cada
  // visita (entrou → saiu, aba escondida ou página fechada). Pode disparar section_time
  // várias vezes pra mesma seção na mesma sessão — a soma é feita na hora de analisar,
  // não na captura, pra não perder dado se a aba fechar no meio de uma visita.
  const MIN_SECTION_MS = 1000;
  const sectionEls = document.querySelectorAll("section.block[class*=sec-]");
  if ("IntersectionObserver" in window && sectionEls.length) {
    const seenMilestone = getSeenSections();
    const activeSince = new Map();
    const currentlyIntersecting = new Set();
    let pageVisible = document.visibilityState === "visible";

    function sectionIdOf(el) {
      return [...el.classList].find((c) => /^sec-\d+$/.test(c));
    }

    function startTiming(id, ts) {
      if (!activeSince.has(id)) activeSince.set(id, ts);
    }

    function flushTiming(id, ts) {
      const start = activeSince.get(id);
      if (start == null) return;
      activeSince.delete(id);
      const durationMs = Math.round(ts - start);
      if (durationMs >= MIN_SECTION_MS) {
        send("section_time", { section_id: id, duration_ms: durationMs });
      }
    }

    function flushAllTiming(ts) {
      [...activeSince.keys()].forEach((id) => flushTiming(id, ts));
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const now = performance.now();
        entries.forEach((entry) => {
          const id = sectionIdOf(entry.target);
          if (!id) return;

          if (entry.isIntersecting) {
            currentlyIntersecting.add(id);
            if (!seenMilestone.has(id)) {
              seenMilestone.add(id);
              saveSeenSections(seenMilestone);
              send("section", { section_id: id });
            }
            if (pageVisible) startTiming(id, now);
          } else {
            currentlyIntersecting.delete(id);
            flushTiming(id, now);
          }
        });
      },
      { threshold: 0.5 },
    );

    sectionEls.forEach((el) => observer.observe(el));

    document.addEventListener("visibilitychange", () => {
      const now = performance.now();
      if (document.visibilityState === "hidden") {
        pageVisible = false;
        flushAllTiming(now);
      } else {
        pageVisible = true;
        currentlyIntersecting.forEach((id) => startTiming(id, now));
      }
    });

    window.addEventListener("pagehide", () => flushAllTiming(performance.now()));
  }

  document.getElementById("share-btn")?.addEventListener("click", () => {
    send("share_button_clicked");
  });

  // Clique em link: ignora âncoras internas (#nota-x), registra o resto com destino + se é saída do site.
  document.addEventListener(
    "click",
    (e) => {
      const link = e.target.closest("a[href]");
      if (!link) return;
      const href = link.getAttribute("href");
      if (!href || href.startsWith("#")) return;

      let url;
      try {
        url = new URL(href, location.href);
      } catch {
        return;
      }
      send("link_click", { url: url.href, outbound: url.hostname !== location.hostname });
    },
    true,
  );
})();
