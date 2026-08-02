(function () {
  "use strict";

  const root = document.documentElement;
  const toggle = document.getElementById("themeToggle");
  const icon = document.getElementById("themeIcon");

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    if (icon) {
      icon.className = theme === "dark" ? "bi bi-moon-stars-fill" : "bi bi-sun-fill";
    }
  }

  let saved = "dark";
  try {
    saved = (window.__rePrefs && window.__rePrefs.theme) || "dark";
  } catch (e) { /* no-op: in-memory only, no browser storage per platform rules */ }

  applyTheme(saved);
  window.__rePrefs = window.__rePrefs || {};
  window.__rePrefs.theme = saved;

  if (toggle) {
    toggle.addEventListener("click", function () {
      const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      applyTheme(next);
      window.__rePrefs.theme = next;
    });
  }

  // Small helper reused by every page-level script
  window.RE = window.RE || {};
  window.RE.fmtMoney = function (value, currency, unit) {
    if (value === null || value === undefined || isNaN(value)) return "—";
    return `${currency || "\u20b9"} ${Number(value).toFixed(2)} ${unit || "Cr"}`;
  };
  window.RE.fmtNum = function (value, digits) {
    if (value === null || value === undefined || isNaN(value)) return "—";
    return Number(value).toLocaleString(undefined, { maximumFractionDigits: digits === undefined ? 0 : digits });
  };
  window.RE.fetchJSON = function (url) {
    return fetch(url).then(async (r) => {
      const body = await r.json().catch(() => ({}));
      if (!r.ok) {
        throw new Error(body.detail || `Request failed (${r.status})`);
      }
      return body;
    });
  };
  window.RE.el = function (tag, attrs, children) {
    const node = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([k, v]) => {
      if (k === "class") node.className = v;
      else if (k === "html") node.innerHTML = v;
      else node.setAttribute(k, v);
    });
    (children || []).forEach((c) => {
      if (typeof c === "string") node.appendChild(document.createTextNode(c));
      else if (c) node.appendChild(c);
    });
    return node;
  };
  window.RE.plotlyTheme = function () {
    const dark = document.documentElement.getAttribute("data-theme") !== "light";
    return {
      font: { color: dark ? "#c7cede" : "#363f5c", family: "Plus Jakarta Sans, sans-serif" },
      paper_bgcolor: "rgba(0,0,0,0)",
    };
  };
})();
