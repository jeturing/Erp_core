import "clsx";
import { c as attr, d as escape_html } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/tenants.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { S as Shield } from "../../../../chunks/shield.js";
import { C as Circle_check_big } from "../../../../chunks/circle-check-big.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
import { S as Search } from "../../../../chunks/search.js";
import { F as Funnel } from "../../../../chunks/funnel.js";
function Audit($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let eventTypes;
    let events = [];
    let total = 0;
    let loading = true;
    let search = "";
    let typeFilter = "";
    let resourceFilter = "";
    let tenantFilter = "";
    (events || []).filter((e) => (e.event_type || "").toLowerCase().includes(search.toLowerCase()) || (e.actor_username || "").toLowerCase().includes(search.toLowerCase()) || (e.resource || "").toLowerCase().includes(search.toLowerCase()) || (e.action || "").toLowerCase().includes(search.toLowerCase()));
    eventTypes = [
      ...new Set((events || []).map((e) => e.event_type).filter(Boolean))
    ];
    $$renderer2.push(`<div class="p-6 space-y-6"><div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"><div><h1 class="page-title flex items-center gap-2">`);
    Shield($$renderer2, { size: 24 });
    $$renderer2.push(`<!----> Auditoría</h1> <p class="page-subtitle">Trail de eventos del sistema — persistente e inmutable</p></div> <div class="flex items-center gap-3">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 border border-green-500/30 rounded-lg text-green-400 text-xs">`);
      Circle_check_big($$renderer2, { size: 14 });
      $$renderer2.push(`<!----> <span>Acceso Autorizado</span></div>`);
    }
    $$renderer2.push(`<!--]--> <button class="btn-secondary flex items-center gap-2"${attr("disabled", loading, true)}>`);
    Refresh_cw($$renderer2, { size: 14, class: "animate-spin" });
    $$renderer2.push(`<!----> Actualizar</button></div></div> <div class="grid grid-cols-2 lg:grid-cols-4 gap-4"><div class="stat-card"><span class="stat-label">Total Eventos</span> <span class="stat-value">${escape_html(total)}</span></div> <div class="stat-card"><span class="stat-label">Tipos únicos</span> <span class="stat-value text-info">${escape_html(eventTypes.length)}</span></div> <div class="stat-card"><span class="stat-label">Éxitos</span> <span class="stat-value text-success">${escape_html((events || []).filter((e) => e.status === "success" || e.status === "ok").length)}</span></div> <div class="stat-card"><span class="stat-label">Errores</span> <span class="stat-value text-error">${escape_html((events || []).filter((e) => e.status === "error" || e.status === "failed").length)}</span></div></div> <div class="flex flex-col sm:flex-row gap-3"><div class="relative flex-1">`);
    Search($$renderer2, {
      size: 16,
      class: "absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"
    });
    $$renderer2.push(`<!----> <input type="text"${attr("value", search)} placeholder="Buscar evento, actor, recurso..." class="input pl-10 w-full"/></div> <input type="text"${attr("value", typeFilter)} placeholder="Tipo de evento..." class="input w-auto"/> <input type="text"${attr("value", resourceFilter)} placeholder="Recurso..." class="input w-auto"/> <input type="text"${attr("value", tenantFilter)} placeholder="Tenant (ej: demo_cliente)..." class="input w-auto"/> <button class="btn-secondary btn-sm flex items-center gap-1">`);
    Funnel($$renderer2, { size: 14 });
    $$renderer2.push(`<!----> Filtrar</button></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-center py-16 text-gray-500"><div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin mx-auto"></div></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Audit($$renderer);
}
export {
  _page as default
};
