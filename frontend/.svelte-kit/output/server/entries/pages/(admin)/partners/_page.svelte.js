import "clsx";
import { d as escape_html, c as attr } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { H as Handshake } from "../../../../chunks/handshake.js";
import { P as Plus } from "../../../../chunks/plus.js";
import { S as Search } from "../../../../chunks/search.js";
function Partners($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let partners = [];
    let search = "";
    let statusFilter = "";
    let summary = { active: 0, pending: 0, total_leads: 0 };
    partners.filter((p) => p.company_name.toLowerCase().includes(search.toLowerCase()) || p.contact_email.toLowerCase().includes(search.toLowerCase()) || (p.contact_name || "").toLowerCase().includes(search.toLowerCase()));
    $$renderer2.push(`<div class="p-6 space-y-6"><div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"><div><h1 class="page-title flex items-center gap-2">`);
    Handshake($$renderer2, { size: 24 });
    $$renderer2.push(`<!----> Partners</h1> <p class="page-subtitle">Gestión de socios comerciales</p></div> <button class="btn-accent flex items-center gap-2">`);
    Plus($$renderer2, { size: 16 });
    $$renderer2.push(`<!----> Nuevo Partner</button></div> <div class="grid grid-cols-1 sm:grid-cols-3 gap-4"><div class="stat-card"><div class="text-xs font-semibold uppercase text-gray-500 mb-1">Activos</div> <div class="text-2xl font-bold text-emerald-400">${escape_html(summary.active)}</div></div> <div class="stat-card"><div class="text-xs font-semibold uppercase text-gray-500 mb-1">Pendientes</div> <div class="text-2xl font-bold text-amber-400">${escape_html(summary.pending)}</div></div> <div class="stat-card"><div class="text-xs font-semibold uppercase text-gray-500 mb-1">Total Leads</div> <div class="text-2xl font-bold text-blue-400">${escape_html(summary.total_leads)}</div></div></div> <div class="flex flex-col sm:flex-row gap-3"><div class="relative flex-1">`);
    Search($$renderer2, {
      size: 16,
      class: "absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"
    });
    $$renderer2.push(`<!----> <input type="text"${attr("value", search)} placeholder="Buscar partner..." class="input pl-10 w-full"/></div> `);
    $$renderer2.select({ value: statusFilter, class: "input w-auto" }, ($$renderer3) => {
      $$renderer3.option({ value: "" }, ($$renderer4) => {
        $$renderer4.push(`Todos los estados`);
      });
      $$renderer3.option({ value: "active" }, ($$renderer4) => {
        $$renderer4.push(`Activos`);
      });
      $$renderer3.option({ value: "pending" }, ($$renderer4) => {
        $$renderer4.push(`Pendientes`);
      });
      $$renderer3.option({ value: "suspended" }, ($$renderer4) => {
        $$renderer4.push(`Suspendidos`);
      });
      $$renderer3.option({ value: "terminated" }, ($$renderer4) => {
        $$renderer4.push(`Terminados`);
      });
    });
    $$renderer2.push(`</div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-center py-12 text-gray-500">Cargando partners...</div>`);
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Partners($$renderer);
}
export {
  _page as default
};
