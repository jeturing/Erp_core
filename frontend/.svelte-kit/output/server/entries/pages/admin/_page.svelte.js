import { d as escape_html, p as bind_props, k as attr_class, b as stringify } from "../../../chunks/index2.js";
import { a8 as fallback } from "../../../chunks/utils2.js";
import "clsx";
function AdminHeader($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let apiKey = fallback($$props["apiKey"], "prov-key-2026-secure");
    $$renderer2.push(`<div class="header svelte-zh9tnt"><div class="header-content svelte-zh9tnt"><div class="logo-section svelte-zh9tnt"><h1 class="svelte-zh9tnt">⚙️ Admin Panel</h1> <p class="svelte-zh9tnt">Gestión centralizada de SMTP, Templates y Alertas de Almacenamiento</p></div> <div class="api-key-section svelte-zh9tnt">`);
    {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<button class="btn btn-small btn-secondary svelte-zh9tnt">🔑 Cambiar API Key</button> <span class="api-key-display svelte-zh9tnt">API Key: ${escape_html(apiKey.substring(0, 8))}...${escape_html(apiKey.substring(apiKey.length - 4))}</span>`);
    }
    $$renderer2.push(`<!--]--></div></div> <div class="status-bar svelte-zh9tnt"><div class="status-item svelte-zh9tnt"><span class="status-badge status-ok svelte-zh9tnt">✓ Sistema Operacional</span></div> <div class="status-item svelte-zh9tnt"><span class="status-time svelte-zh9tnt">${escape_html((/* @__PURE__ */ new Date()).toLocaleString("es-ES"))}</span></div></div></div>`);
    bind_props($$props, { apiKey });
  });
}
function SmtpManager($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    $$renderer2.push(`<div class="smtp-container svelte-e57fri">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="loading svelte-e57fri"><div class="spinner svelte-e57fri"></div> <p>Cargando configuración SMTP...</p></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  let apiKey = "prov-key-2026-secure";
  $$renderer.push(`<div class="admin-container svelte-1jef3w8">`);
  AdminHeader($$renderer, { apiKey });
  $$renderer.push(`<!----> <div class="tabs-container svelte-1jef3w8"><div class="tabs svelte-1jef3w8"><button${attr_class(`tab-button ${stringify("active")}`, "svelte-1jef3w8")}>📧 SMTP</button> <button${attr_class(`tab-button ${stringify("")}`, "svelte-1jef3w8")}>📝 Email Templates</button> <button${attr_class(`tab-button ${stringify("")}`, "svelte-1jef3w8")}>💾 Storage Alerts</button></div></div> <div class="content-area svelte-1jef3w8">`);
  {
    $$renderer.push("<!--[-->");
    SmtpManager($$renderer);
  }
  $$renderer.push(`<!--]--></div></div>`);
}
export {
  _page as default
};
