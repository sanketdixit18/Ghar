(function () {
  "use strict";

  function renderField(field) {
    const wrap = RE.el("div", { class: "field" });
    const label = RE.el("label", { for: "f_" + field.name }, [field.label]);
    wrap.appendChild(label);

    if (field.type === "select") {
      const select = RE.el("select", { id: "f_" + field.name, name: field.name, required: "required" });
      (field.options || []).forEach((opt) => {
        const o = document.createElement("option");
        o.value = opt;
        o.textContent = opt;
        select.appendChild(o);
      });
      wrap.appendChild(select);
    } else {
      const input = RE.el("input", {
        id: "f_" + field.name, name: field.name, type: "number",
        min: field.min ?? 0, step: field.step ?? 1, required: "required",
        placeholder: `Min ${field.min ?? 0}`,
      });
      wrap.appendChild(input);
    }
    return wrap;
  }

  function loadForm() {
    const form = document.getElementById("predictForm");
    if (!form || form.dataset.loaded) return;

    form.innerHTML = '<div class="loading-block"><span class="spinner"></span>&nbsp; Loading form…</div>';

    fetch(`/api/prediction/schema?city=${encodeURIComponent(RE.city)}`)
      .then((r) => {
        if (!r.ok) throw new Error("Failed to load form");
        return r.json();
      })
      .then((data) => {
        form.innerHTML = "";
        data.fields.forEach((f) => form.appendChild(renderField(f)));
        form.dataset.loaded = "true";
      })
      .catch(() => {
        form.innerHTML = '<div class="notice error">Could not load the prediction form for this city.</div>';
      });
  }

  function renderResult(data) {
    const box = document.getElementById("predictResult");
    box.innerHTML = "";

    const hero = RE.el("div", { class: "glass-card result-hero" }, [
      RE.el("div", { class: "notice success", style: "display:inline-flex;margin-bottom:1rem;" }, ["✅ Prediction generated successfully"]),
      RE.el("div", {}, [RE.el("div", { class: "price" }, [RE.fmtMoney(data.predicted_price, data.currency, data.unit)])]),
      RE.el("div", { class: "range" }, [
        `${RE.fmtMoney(data.lower_estimate, data.currency, data.unit)} — ${RE.fmtMoney(data.upper_estimate, data.currency, data.unit)}`,
      ]),
    ]);

    const grid = RE.el("div", { class: "result-grid" }, [
      RE.el("div", { class: "glass-card result-stat" }, [
        RE.el("div", { class: "val" }, [RE.fmtMoney(data.lower_estimate, data.currency, data.unit)]),
        RE.el("div", { class: "lbl" }, ["📉 Lower Estimate"]),
      ]),
      RE.el("div", { class: "glass-card result-stat" }, [
        RE.el("div", { class: "val" }, [RE.fmtMoney(data.predicted_price, data.currency, data.unit)]),
        RE.el("div", { class: "lbl" }, ["🏠 Predicted Price"]),
      ]),
      RE.el("div", { class: "glass-card result-stat" }, [
        RE.el("div", { class: "val" }, [RE.fmtMoney(data.upper_estimate, data.currency, data.unit)]),
        RE.el("div", { class: "lbl" }, ["📈 Upper Estimate"]),
      ]),
    ]);

    const detailsRows = Object.entries(data.input_summary || {})
      .map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`).join("");
    const details = RE.el("div", { class: "glass-card glass-card-pad", style: "margin-top:1.4rem;" }, []);
    details.innerHTML = `
      <details>
        <summary style="cursor:pointer;font-weight:600;">📋 View Property Details</summary>
        <table class="data-table" style="margin-top:1rem;"><tbody>${detailsRows}</tbody></table>
      </details>`;

    box.appendChild(hero);
    box.appendChild(grid);
    box.appendChild(details);
  }

  function bindSubmit() {
    const form = document.getElementById("predictForm");
    const btn = document.getElementById("predictBtn");
    const label = document.getElementById("predictBtnLabel");
    if (!form || form.dataset.bound) return;
    form.dataset.bound = "true";

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      const features = {};
      new FormData(form).forEach((v, k) => (features[k] = v));

      btn.disabled = true;
      label.innerHTML = '<span class="spinner"></span>&nbsp; Predicting…';

      fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ city: RE.city, features }),
      })
        .then(async (r) => {
          const body = await r.json();
          if (!r.ok) throw new Error(body.detail || "Prediction failed");
          return body;
        })
        .then((data) => {
          renderResult(data);
          document.getElementById("predictResult").scrollIntoView({ behavior: "smooth", block: "nearest" });
        })
        .catch((err) => {
          document.getElementById("predictResult").innerHTML =
            `<div class="notice error">⚠️ ${err.message}</div>`;
        })
        .finally(() => {
          btn.disabled = false;
          label.innerHTML = '<i class="bi bi-magic"></i>&nbsp; Predict Price';
        });
    });
  }

  document.addEventListener("re:tab-loaded:prediction", loadForm);
  document.addEventListener("DOMContentLoaded", () => {
    bindSubmit();
    // If prediction is the initial tab it fires before this listener is attached — check directly.
    const dash = document.getElementById("dashboard");
    if (dash && dash.dataset.initialTab === "prediction") loadForm();
  });
})();
