(function () {
  "use strict";

  const SUBTABS = [
    { id: "geo", label: "🗺️ Geo Map" },
    { id: "wordcloud", label: "☁️ Word Cloud" },
    { id: "area-price", label: "📐 Area vs Price" },
    { id: "bhk", label: "🛏️ BHK Analysis" },
    { id: "property-type", label: "🏢 Property Type" },
  ];

  let currentSector = "All";
  let filterOptions = {};

  function skeleton() {
    return '<div class="skeleton"></div>';
  }

  function kpiRow(kpis) {
    if (!kpis) return "";
    const items = [
      ["avg_price", "💰 Avg Price", (v) => RE.fmtMoney(v, RE.currency, RE.unit)],
      ["max_price", "🏆 Max Price", (v) => RE.fmtMoney(v, RE.currency, RE.unit)],
      ["min_price", "🏷️ Min Price", (v) => RE.fmtMoney(v, RE.currency, RE.unit)],
      ["sector_count", "📍 Sectors", (v) => RE.fmtNum(v)],
      ["total_properties", "🏘️ Properties", (v) => RE.fmtNum(v)],
    ];
    const cards = items
      .filter(([key]) => kpis[key] !== undefined && kpis[key] !== null)
      .map(([key, label, fmt]) => `
        <div class="glass-card kpi-card">
          <div class="val">${fmt(kpis[key])}</div>
          <div class="lbl">${label}</div>
        </div>`)
      .join("");
    return `<div class="kpi-row">${cards}</div>`;
  }

  function sectorFilterBar(root, label, onChange) {
    const bar = document.createElement("div");
    bar.className = "filter-bar glass-card glass-card-pad";
    const sectors = filterOptions.sectors || [];
    bar.innerHTML = `
      <div class="field">
        <label>${label}</label>
        <select id="analyticsSectorFilter">
          <option value="All">All</option>
          ${sectors.map((s) => `<option value="${s}" ${s === currentSector ? "selected" : ""}>${s}</option>`).join("")}
        </select>
      </div>`;
    root.appendChild(bar);
    bar.querySelector("select").addEventListener("change", (e) => {
      currentSector = e.target.value;
      onChange(currentSector);
    });
  }

  function renderPlot(containerId, figJson) {
    const el = document.getElementById(containerId);
    if (!el) return;
    if (!figJson || figJson.empty) {
      el.innerHTML = '<div class="notice warn">No data available for this selection.</div>';
      return;
    }
    const theme = RE.plotlyTheme();
    const layout = Object.assign({}, figJson.layout, { font: theme.font, paper_bgcolor: "rgba(0,0,0,0)" });
    Plotly.newPlot(el, figJson.data, layout, { responsive: true, displaylogo: false });
  }

  function renderError(containerId, err) {
    const el = document.getElementById(containerId);
    if (el) el.innerHTML = `<div class="notice error">⚠️ ${err.message || "Something went wrong."}</div>`;
  }

  function summaryTable(rows) {
    if (!rows || !rows.length) return "";
    const cols = Object.keys(rows[0]);
    const thead = cols.map((c) => `<th>${c.replace(/_/g, " ")}</th>`).join("");
    const tbody = rows.map((r) => `<tr>${cols.map((c) => `<td>${r[c]}</td>`).join("")}</tr>`).join("");
    return `<table class="data-table"><thead><tr>${thead}</tr></thead><tbody>${tbody}</tbody></table>`;
  }

  // -----------------------------------------------------------------
  function loadGeo(root) {
    root.innerHTML = skeleton();
    RE.fetchJSON(`/sector?city=${encodeURIComponent(RE.city)}&sector=All`)
      .then((data) => {
        filterOptions = data.filter_options || {};
        root.innerHTML = "";
        root.appendChild(RE.el("div", { html: kpiRow(data.kpis) }));
        sectorFilterBar(root, "Filter by Sector", (sector) => refreshGeo(sector));
        root.appendChild(RE.el("div", { class: "glass-card chart-card" }, [
          RE.el("div", { id: "geoChart", class: "chart-container" }),
        ]));
        renderPlot("geoChart", data.geo_map);
      })
      .catch((err) => (root.innerHTML = `<div class="notice error">⚠️ ${err.message}</div>`));
  }

  function refreshGeo(sector) {
    RE.fetchJSON(`/sector?city=${encodeURIComponent(RE.city)}&sector=${encodeURIComponent(sector)}`)
      .then((data) => renderPlot("geoChart", data.geo_map))
      .catch((err) => renderError("geoChart", err));
  }

  function loadWordcloud(root) {
    root.innerHTML = skeleton();
    filtersReady().then(() => {
      root.innerHTML = "";
      sectorFilterBar(root, "Filter by Sector", (sector) => refreshWordcloud(root, sector));
      root.appendChild(RE.el("div", { class: "glass-card chart-card", id: "wordcloudCard" }, [
        RE.el("div", { class: "loading-block" }, ["Generating word cloud…"]),
      ]));
      refreshWordcloud(root, currentSector);
    });
  }

  function refreshWordcloud(root, sector) {
    const card = document.getElementById("wordcloudCard");
    card.innerHTML = '<div class="loading-block"><span class="spinner"></span>&nbsp; Generating…</div>';
    RE.fetchJSON(`/wordcloud?city=${encodeURIComponent(RE.city)}&sector=${encodeURIComponent(sector)}`)
      .then((data) => {
        if (!data.available || !data.image) {
          card.innerHTML = '<div class="notice warn">No amenity data available for this selection.</div>';
          return;
        }
        card.innerHTML = `<img src="${data.image}" alt="Amenities word cloud" style="width:100%;border-radius:12px;" />`;
      })
      .catch((err) => (card.innerHTML = `<div class="notice error">⚠️ ${err.message}</div>`));
  }

  function filtersReady() {
    if (filterOptions && filterOptions.sectors) return Promise.resolve();
    return RE.fetchJSON(`/sector?city=${encodeURIComponent(RE.city)}`)
      .then((data) => { filterOptions = data.filter_options || {}; });
  }

  function loadAreaPrice(root) {
    root.innerHTML = skeleton();
    filtersReady().then(() => {
      root.innerHTML = "";
      const bar = document.createElement("div");
      bar.className = "filter-bar glass-card glass-card-pad";
      const types = filterOptions.property_types || [];
      const beds = filterOptions.bedrooms || [];
      bar.innerHTML = `
        <div class="field"><label>Property Type</label>
          <select id="apType"><option value="All">All</option>${types.map((t) => `<option value="${t}">${t}</option>`).join("")}</select>
        </div>
        <div class="field"><label>Bedrooms</label>
          <select id="apBed"><option value="All">All</option>${beds.map((b) => `<option value="${b}">${b}</option>`).join("")}</select>
        </div>`;
      root.appendChild(bar);
      root.appendChild(RE.el("div", { class: "glass-card chart-card" }, [
        RE.el("div", { id: "areaPriceChart", class: "chart-container" }),
      ]));

      function refresh() {
        const type = document.getElementById("apType").value;
        const bed = document.getElementById("apBed").value;
        RE.fetchJSON(`/area-price?city=${encodeURIComponent(RE.city)}&property_type=${encodeURIComponent(type)}&bedrooms=${encodeURIComponent(bed)}`)
          .then((data) => renderPlot("areaPriceChart", data.chart))
          .catch((err) => renderError("areaPriceChart", err));
      }
      bar.querySelectorAll("select").forEach((s) => s.addEventListener("change", refresh));
      refresh();
    });
  }

  function loadBhk(root) {
    root.innerHTML = skeleton();
    filtersReady().then(() => {
      root.innerHTML = "";
      sectorFilterBar(root, "Filter by Sector", (sector) => refreshBhk(root, sector));
      root.appendChild(RE.el("div", { class: "glass-card chart-card" }, [
        RE.el("h4", {}, ["Bedroom Distribution"]),
        RE.el("div", { id: "bhkPie", class: "chart-container", style: "min-height:340px;" }),
      ]));
      root.appendChild(RE.el("div", { class: "glass-card chart-card" }, [
        RE.el("h4", {}, ["Price by Bedroom Count"]),
        RE.el("div", { id: "bhkBox", class: "chart-container" }),
      ]));
      root.appendChild(RE.el("div", { class: "glass-card chart-card", id: "bhkSummary" }));
      refreshBhk(root, currentSector);
    });
  }

  function refreshBhk(root, sector) {
    RE.fetchJSON(`/bhk?city=${encodeURIComponent(RE.city)}&sector=${encodeURIComponent(sector)}`)
      .then((data) => {
        renderPlot("bhkPie", data.bhk_distribution && data.bhk_distribution.chart);
        renderPlot("bhkBox", data.bedroom_price_box && data.bedroom_price_box.chart);
        const summaryEl = document.getElementById("bhkSummary");
        if (summaryEl) {
          summaryEl.innerHTML = "<h4>Summary</h4>" + summaryTable(data.bedroom_price_box && data.bedroom_price_box.summary);
        }
      })
      .catch((err) => {
        renderError("bhkPie", err);
        renderError("bhkBox", err);
      });
  }

  function loadPropertyType(root) {
    root.innerHTML = skeleton();
    filtersReady().then(() => {
      root.innerHTML = "";
      sectorFilterBar(root, "Filter by Sector", (sector) => refreshHistogram(root, sector));
      root.appendChild(RE.el("div", { class: "glass-card chart-card" }, [
        RE.el("div", { id: "histChart", class: "chart-container" }),
      ]));
      refreshHistogram(root, currentSector);
    });
  }

  function refreshHistogram(root, sector) {
    RE.fetchJSON(`/property-type?city=${encodeURIComponent(RE.city)}&sector=${encodeURIComponent(sector)}`)
      .then((data) => renderPlot("histChart", data.price_histogram && data.price_histogram.chart))
      .catch((err) => renderError("histChart", err));
  }

  const LOADERS = {
    geo: loadGeo,
    wordcloud: loadWordcloud,
    "area-price": loadAreaPrice,
    bhk: loadBhk,
    "property-type": loadPropertyType,
  };

  function buildShell() {
    const container = document.getElementById("analyticsRoot");
    container.innerHTML = `
      <div class="glass-card glass-card-pad" style="margin-bottom:1.4rem;">
        <h2 style="margin-top:0;">📊 Market Analytics</h2>
        <p style="color:var(--text-2);margin-top:-0.4rem;">Explore pricing patterns, distributions, and geography.</p>
      </div>
      <div class="subtabs" id="analyticsSubtabs">
        ${SUBTABS.map((t, i) => `<button class="subtab-btn ${i === 0 ? "active" : ""}" data-subtab="${t.id}">${t.label}</button>`).join("")}
      </div>
      <div id="analyticsSubtabContent"></div>
    `;

    const content = document.getElementById("analyticsSubtabContent");
    const buttons = Array.from(document.querySelectorAll("#analyticsSubtabs .subtab-btn"));
    const loadedSub = new Set();

    function activate(id) {
      buttons.forEach((b) => b.classList.toggle("active", b.dataset.subtab === id));
      if (!loadedSub.has(id)) {
        loadedSub.add(id);
        LOADERS[id](content);
      } else {
        LOADERS[id](content); // cheap re-fetch keeps filters in sync per sub-tab; data is small
      }
    }

    buttons.forEach((b) => b.addEventListener("click", () => activate(b.dataset.subtab)));
    activate("geo");
  }

  function init() {
    const root = document.getElementById("analyticsRoot");
    if (!root || root.dataset.loaded) return;
    root.dataset.loaded = "true";
    buildShell();
  }

  document.addEventListener("re:tab-loaded:analytics", init);
  document.addEventListener("DOMContentLoaded", () => {
    const dash = document.getElementById("dashboard");
    if (dash && dash.dataset.initialTab === "analytics") init();
  });
})();
