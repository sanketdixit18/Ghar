(function () {
  "use strict";

  const root = document.getElementById("dashboard");
  if (!root) return;

  const CITY = root.dataset.city;
  const INITIAL_TAB = root.dataset.initialTab || "prediction";
  const FEATURES = {
    analytics: root.dataset.hasAnalytics === "true",
    recommendation: root.dataset.hasRecommendation === "true",
    market: root.dataset.hasMarket === "true",
  };

  window.RE = window.RE || {};
  window.RE.city = CITY;
  window.RE.currency = root.dataset.currency || "\u20b9";
  window.RE.unit = root.dataset.unit || "Cr";
  window.RE.mapCenter = { lat: parseFloat(root.dataset.mapLat) || null, lon: parseFloat(root.dataset.mapLon) || null };

  const loadedTabs = new Set();
  const tabButtons = Array.from(document.querySelectorAll(".tab-btn"));
  const panels = {
    prediction: document.getElementById("panel-prediction"),
    analytics: document.getElementById("panel-analytics"),
    recommendation: document.getElementById("panel-recommendation"),
    market: document.getElementById("panel-market"),
    locality: document.getElementById("panel-locality"),
  };

  // Hide tabs for features this city doesn't support (still routable directly).
  tabButtons.forEach((btn) => {
    const tab = btn.dataset.tab;
    if (tab === "analytics" && !FEATURES.analytics) btn.style.display = "none";
    if (tab === "recommendation" && !FEATURES.recommendation) btn.style.display = "none";
    if (tab === "market" && !FEATURES.market) btn.style.display = "none";
  });

  function activateTab(tab) {
    if (!panels[tab]) tab = "prediction";
    tabButtons.forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
    Object.entries(panels).forEach(([name, el]) => el && el.classList.toggle("active", name === tab));

    if (!loadedTabs.has(tab)) {
      loadedTabs.add(tab);
      document.dispatchEvent(new CustomEvent("re:tab-loaded:" + tab, { detail: { city: CITY } }));
    }
    const url = new URL(window.location.href);
    url.searchParams.set("city", CITY);
    window.history.replaceState({}, "", url.pathname.split("/")[1] ? url : url);
  }

  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => activateTab(btn.dataset.tab));
  });

  activateTab(INITIAL_TAB);

  // --------------------------------------------------------------------
  // City switcher — populated from /cities, preserves current tab.
  // --------------------------------------------------------------------
  const citySelect = document.getElementById("citySwitchSelect");
  if (citySelect) {
    fetch("/cities")
      .then((r) => r.json())
      .then((cities) => {
        citySelect.innerHTML = "";
        cities.forEach((c) => {
          const opt = document.createElement("option");
          opt.value = c.slug;
          opt.textContent = `${c.emoji || ""} ${c.city}`.trim();
          if (c.slug === CITY) opt.selected = true;
          citySelect.appendChild(opt);
        });
      })
      .catch(() => {
        const opt = document.createElement("option");
        opt.textContent = CITY;
        citySelect.appendChild(opt);
      });

    citySelect.addEventListener("change", () => {
      const activeTab = tabButtons.find((b) => b.classList.contains("active"));
      const tab = activeTab ? activeTab.dataset.tab : "prediction";
      const path = tab === "prediction" ? "/prediction" : `/${tab}`;
      window.location.href = `${path}?city=${encodeURIComponent(citySelect.value)}`;
    });
  }
})();
