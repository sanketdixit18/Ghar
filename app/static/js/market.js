(function () {
  "use strict";

  let filterOptions = {};
  const filters = { locality: "All", builder: "All", property_type: "All", price_segment: "All" };

  function renderPlot(id, figJson) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!figJson) {
      el.innerHTML = '<div class="notice warn">No data.</div>';
      return;
    }
    const theme = RE.plotlyTheme();
    const layout = Object.assign({}, figJson.layout, { font: theme.font, paper_bgcolor: "rgba(0,0,0,0)" });
    Plotly.newPlot(el, figJson.data, layout, { responsive: true, displaylogo: false });
  }

  function kpiRow(kpis) {
    if (!kpis) return "";
    return `
      <div class="kpi-row">
        <div class="glass-card kpi-card"><div class="val">${RE.fmtMoney(kpis.avg_price, RE.currency, RE.unit)}</div><div class="lbl">💰 Avg Price</div></div>
        <div class="glass-card kpi-card"><div class="val">₹${RE.fmtNum(kpis.avg_rate)}</div><div class="lbl">📐 Avg Rate / sqft</div></div>
        <div class="glass-card kpi-card"><div class="val">${RE.fmtNum(kpis.localities)}</div><div class="lbl">📍 Localities</div></div>
        <div class="glass-card kpi-card"><div class="val">${RE.fmtNum(kpis.listings)}</div><div class="lbl">🏘️ Listings</div></div>
        <div class="glass-card kpi-card"><div class="val">${kpis.median_bhk}</div><div class="lbl">🛏️ Median BHK</div></div>
      </div>`;
  }

  function highlightsGrid(h) {
    if (!h) return "";
    const items = [
      ["🏆", "Most Expensive Locality", h.most_expensive_locality, RE.fmtMoney(h.most_expensive_price, RE.currency, RE.unit)],
      ["💸", "Most Affordable Locality", h.most_affordable_locality, RE.fmtMoney(h.most_affordable_price, RE.currency, RE.unit)],
      ["🏗️", "Top Builder", h.top_builder, `${h.top_builder_listings} listings`],
      ["📍", "Most Active Locality", h.most_active_locality, `${h.most_active_count} listings`],
      ["🏢", "Most Popular Type", h.popular_type, `${h.common_bhk} BHK common`],
      ["✅", "RERA Approved", `${h.rera_share_pct}%`, "of all listings"],
      ["🔑", "Ready to Move", `${h.ready_share_pct}%`, "of all listings"],
    ];
    return `<div class="highlight-grid">${items.map(([icon, label, value, sub]) => `
      <div class="glass-card highlight-card">
        <div class="h-label">${icon} ${label}</div>
        <div class="h-value">${value}</div>
        <div class="h-sub">${sub}</div>
      </div>`).join("")}</div>`;
  }

  function chartCard(id, title) {
    return `<div class="glass-card chart-card"><h4>${title}</h4><div id="${id}" class="chart-container"></div></div>`;
  }

  function buildShell() {
    const root = document.getElementById("marketRoot");
    root.innerHTML = `
      <div class="glass-card glass-card-pad" style="margin-bottom:1.4rem;">
        <h2 style="margin-top:0;">📈 Market Trends</h2>
        <p style="color:var(--text-2);margin-top:-0.4rem;">Builder performance, locality pricing, and listing composition.</p>
      </div>
      <div class="filter-bar glass-card glass-card-pad" id="marketFilterBar"></div>
      <div id="marketContent"><div class="skeleton"></div></div>
    `;

    RE.fetchJSON(`/api/market/filters?city=${encodeURIComponent(RE.city)}`)
      .then((data) => {
        if (!data.available) {
          root.innerHTML += '<div class="notice warn">Market trends are not available for this city yet.</div>';
          return;
        }
        filterOptions = data;
        renderFilterBar();
        refresh();
      })
      .catch((err) => {
        root.innerHTML += `<div class="notice error">⚠️ ${err.message}</div>`;
      });
  }

  function renderFilterBar() {
    const bar = document.getElementById("marketFilterBar");
    const opt = (list) => (list || []).map((v) => `<option value="${v}">${v}</option>`).join("");
    bar.innerHTML = `
      <div class="field"><label>Locality</label>
        <select id="mfLocality"><option value="All">All</option>${opt(filterOptions.localities)}</select></div>
      <div class="field"><label>Builder</label>
        <select id="mfBuilder"><option value="All">All</option>${opt(filterOptions.builders)}</select></div>
      <div class="field"><label>Property Type</label>
        <select id="mfType"><option value="All">All</option>${opt(filterOptions.property_types)}</select></div>
      <div class="field"><label>Price Segment</label>
        <select id="mfSegment"><option value="All">All</option>${opt(filterOptions.price_segments)}</select></div>
    `;
    ["mfLocality", "mfBuilder", "mfType", "mfSegment"].forEach((id) => {
      document.getElementById(id).addEventListener("change", () => {
        filters.locality = document.getElementById("mfLocality").value;
        filters.builder = document.getElementById("mfBuilder").value;
        filters.property_type = document.getElementById("mfType").value;
        filters.price_segment = document.getElementById("mfSegment").value;
        refresh();
      });
    });
  }

  function refresh() {
    const content = document.getElementById("marketContent");
    content.innerHTML = '<div class="skeleton"></div>';

    const qs = new URLSearchParams({ city: RE.city, ...filters }).toString();
    RE.fetchJSON(`/api/market/overview?${qs}`)
      .then((data) => {
        if (!data.available || data.empty) {
          content.innerHTML = '<div class="notice warn">No listings match the selected filters.</div>';
          return;
        }
        content.innerHTML = `
          ${kpiRow(data.kpis)}
          ${highlightsGrid(data.highlights)}
          <div class="section-head"><h2 style="font-size:1.2rem;">Overview</h2></div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem;">
            ${chartCard("mOverview1", "Price Segment Mix")}
            ${chartCard("mOverview2", "Property Type Mix")}
            ${chartCard("mOverview3", "Construction Status")}
            ${chartCard("mOverview4", "RERA Approval")}
          </div>
          <div class="section-head"><h2 style="font-size:1.2rem;">Location Insights</h2></div>
          ${chartCard("mLoc1", "Top 10 Most Expensive Localities")}
          ${chartCard("mLoc2", "Top 10 Highest Rate Localities")}
          ${chartCard("mLoc3", "Most Active Localities by Listings")}
          <div class="section-head"><h2 style="font-size:1.2rem;">Builder Insights</h2></div>
          ${chartCard("mBuild1", "Top Builders by Listings")}
          ${data.builders.top_premium ? chartCard("mBuild2", "Top Premium Builders") : ""}
          ${chartCard("mBuild3", "Most Listed Projects")}
          <div class="section-head"><h2 style="font-size:1.2rem;">Price &amp; Area</h2></div>
          ${chartCard("mPrice1", "Price Distribution")}
          ${chartCard("mPrice2", "Area vs Price")}
          ${chartCard("mPrice3", "Price by Property Type")}
          ${chartCard("mPrice4", "Avg Rate: RERA vs Non-RERA")}
        `;

        renderPlot("mOverview1", data.overview.price_segment_mix);
        renderPlot("mOverview2", data.overview.property_type_mix);
        renderPlot("mOverview3", data.overview.construction_status);
        renderPlot("mOverview4", data.overview.rera_approval);

        renderPlot("mLoc1", data.location.top_expensive_localities);
        renderPlot("mLoc2", data.location.top_rate_localities);
        renderPlot("mLoc3", data.location.most_active_localities);

        renderPlot("mBuild1", data.builders.top_by_listings);
        if (data.builders.top_premium) renderPlot("mBuild2", data.builders.top_premium);
        renderPlot("mBuild3", data.builders.top_projects);

        renderPlot("mPrice1", data.price_area.price_distribution);
        renderPlot("mPrice2", data.price_area.area_vs_price);
        renderPlot("mPrice3", data.price_area.price_by_type);
        renderPlot("mPrice4", data.price_area.rera_vs_rate);
      })
      .catch((err) => {
        content.innerHTML = `<div class="notice error">⚠️ ${err.message}</div>`;
      });
  }

  function init() {
    const root = document.getElementById("marketRoot");
    if (!root || root.dataset.loaded) return;
    root.dataset.loaded = "true";
    buildShell();
  }

  document.addEventListener("re:tab-loaded:market", init);
  document.addEventListener("DOMContentLoaded", () => {
    const dash = document.getElementById("dashboard");
    if (dash && dash.dataset.initialTab === "market") init();
  });
})();
