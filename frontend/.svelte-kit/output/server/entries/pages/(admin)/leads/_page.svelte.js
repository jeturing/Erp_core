import "clsx";
import { e as ensure_array_like, k as attr_class, d as escape_html, a as attr_style, c as attr, b as stringify } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { T as Target } from "../../../../chunks/target.js";
import { P as Plus } from "../../../../chunks/plus.js";
import { S as Search } from "../../../../chunks/search.js";
function Leads($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let leads = [];
    let partners = [];
    let search = "";
    let partnerFilter = 0;
    let statusFilter = "";
    let pipeline = {};
    let totalEstimated = 0;
    const statusLabels = {
      new: "Nuevo",
      contacted: "Contactado",
      qualified: "Calificado",
      proposal: "Propuesta",
      won: "Ganado",
      lost: "Perdido",
      invalid: "Inválido"
    };
    const statusColors = {
      new: "bg-blue-500",
      contacted: "bg-cyan-500",
      qualified: "bg-amber-500",
      proposal: "bg-purple-500",
      won: "bg-emerald-500",
      lost: "bg-red-500",
      invalid: "bg-gray-500"
    };
    (leads || []).filter((l) => l.company_name.toLowerCase().includes(search.toLowerCase()) || (l.contact_name || "").toLowerCase().includes(search.toLowerCase()) || (l.contact_email || "").toLowerCase().includes(search.toLowerCase()));
    $$renderer2.push(`<div class="p-6 space-y-6"><div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"><div><h1 class="page-title flex items-center gap-2">`);
    Target($$renderer2, { size: 24 });
    $$renderer2.push(`<!----> Pipeline de Leads</h1> <p class="page-subtitle">Prospectos registrados por partners — Cláusula 7</p></div> <button class="btn-accent flex items-center gap-2">`);
    Plus($$renderer2, { size: 16 });
    $$renderer2.push(`<!----> Nuevo Lead</button></div> <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2"><!--[-->`);
    const each_array = ensure_array_like(Object.entries(statusLabels));
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let [key, label] = each_array[$$index];
      $$renderer2.push(`<button${attr_class(`card p-3 text-center hover:ring-1 hover:ring-terracotta transition-all cursor-pointer ${stringify(statusFilter === key ? "ring-2 ring-terracotta" : "")}`)}><div class="text-xs text-gray-500 mb-1">${escape_html(label)}</div> <div class="text-lg font-bold text-text-light">${escape_html(pipeline[key] || 0)}</div> <div${attr_class(`h-1 rounded-full mt-1 ${stringify(statusColors[key])}`)}${attr_style(`width: ${stringify(Math.min(100, (pipeline[key] || 0) / Math.max(1, leads.length) * 100))}%`)}></div></button>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="stat-card"><div class="text-xs font-semibold uppercase text-gray-500 mb-1">Valor mensual estimado total</div> <div class="text-2xl font-bold text-emerald-400">$${escape_html(totalEstimated.toLocaleString("en-US", { minimumFractionDigits: 2 }))}</div></div> <div class="flex flex-col sm:flex-row gap-3"><div class="relative flex-1">`);
    Search($$renderer2, {
      size: 16,
      class: "absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"
    });
    $$renderer2.push(`<!----> <input type="text"${attr("value", search)} placeholder="Buscar lead..." class="input pl-10 w-full"/></div> `);
    $$renderer2.select({ value: partnerFilter, class: "input w-auto" }, ($$renderer3) => {
      $$renderer3.option({ value: 0 }, ($$renderer4) => {
        $$renderer4.push(`Todos los partners`);
      });
      $$renderer3.push(`<!--[-->`);
      const each_array_1 = ensure_array_like(partners);
      for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
        let p = each_array_1[$$index_1];
        $$renderer3.option({ value: p.id }, ($$renderer4) => {
          $$renderer4.push(`${escape_html(p.company_name)}`);
        });
      }
      $$renderer3.push(`<!--]-->`);
    });
    $$renderer2.push(`</div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-center py-12 text-gray-500">Cargando leads...</div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Leads($$renderer);
}
export {
  _page as default
};
