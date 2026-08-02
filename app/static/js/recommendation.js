(function () {
  "use strict";

  function loadProperties() {
    const select = document.getElementById("recPropertySelect");
    const btn = document.getElementById("recommendBtn");
    if (!select || select.dataset.loaded) return;

    select.innerHTML = '<option>Loading properties…</option>';

    fetch(`/api/recommendation/properties?city=${encodeURIComponent(RE.city)}`)
      .then((r) => r.json())
      .then((data) => {
        select.innerHTML = "";
        if (!data.available || !data.properties.length) {
          select.innerHTML = '<option>No properties available</option>';
          if (btn) btn.disabled = true;
          return;
        }
        data.properties.forEach((p) => {
          const opt = document.createElement("option");
          opt.value = p;
          opt.textContent = p;
          select.appendChild(opt);
        });
        select.dataset.loaded = "true";
      })
      .catch(() => {
        select.innerHTML = '<option>Failed to load properties</option>';
      });
  }

  function renderCards(data) {
    const box = document.getElementById("recResult");
    box.innerHTML = "";

    if (!data.recommendations || !data.recommendations.length) {
      box.innerHTML = '<div class="notice warn">No similar properties were found.</div>';
      return;
    }

    data.recommendations.forEach((rec) => {
      const card = RE.el("div", { class: "glass-card rec-card hoverable" });
      card.innerHTML = `
        <div class="match-score"><span class="pulse-dot"></span>&nbsp; ${rec.match_score}% Match</div>
        <h4>${rec.property_name}</h4>
        <div class="rec-meta">${rec.avg_price !== null ? "Avg. Price: " + RE.fmtMoney(rec.avg_price, RE.currency, RE.unit) : ""}</div>
        ${rec.configurations && rec.configurations.length ? `<div class="chip-row">${rec.configurations.map((c) => `<span class="chip">${c}</span>`).join("")}</div>` : ""}
        ${rec.amenities && rec.amenities.length ? `<div class="chip-row">${rec.amenities.map((a) => `<span class="chip">✨ ${a}</span>`).join("")}</div>` : ""}
        ${rec.nearby && rec.nearby.length ? `<div class="chip-row">${rec.nearby.map((n) => `<span class="chip">📍 ${n}</span>`).join("")}</div>` : ""}
        ${rec.link ? `<a href="${rec.link}" target="_blank" class="btn btn-ghost btn-sm" style="margin-top:0.4rem;"><i class="bi bi-box-arrow-up-right"></i>&nbsp; View Listing</a>` : ""}
      `;
      box.appendChild(card);
    });
  }

  function bindSubmit() {
    const btn = document.getElementById("recommendBtn");
    if (!btn || btn.dataset.bound) return;
    btn.dataset.bound = "true";

    btn.addEventListener("click", function () {
      const select = document.getElementById("recPropertySelect");
      const propertyName = select.value;
      if (!propertyName) return;

      const box = document.getElementById("recResult");
      box.innerHTML = '<div class="loading-block"><span class="spinner"></span>&nbsp; Finding similar properties…</div>';
      btn.disabled = true;

      fetch("/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ city: RE.city, property_name: propertyName, top_n: 5 }),
      })
        .then(async (r) => {
          const body = await r.json();
          if (!r.ok) throw new Error(body.detail || "Could not fetch recommendations");
          return body;
        })
        .then(renderCards)
        .catch((err) => {
          box.innerHTML = `<div class="notice error">⚠️ ${err.message}</div>`;
        })
        .finally(() => {
          btn.disabled = false;
        });
    });
  }

  document.addEventListener("re:tab-loaded:recommendation", loadProperties);
  document.addEventListener("DOMContentLoaded", () => {
    bindSubmit();
    const dash = document.getElementById("dashboard");
    if (dash && dash.dataset.initialTab === "recommendation") loadProperties();
  });
})();
