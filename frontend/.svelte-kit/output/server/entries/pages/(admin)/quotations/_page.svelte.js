import "clsx";
import { d as escape_html, c as attr, e as ensure_array_like } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { F as File_spreadsheet } from "../../../../chunks/file-spreadsheet.js";
import { S as Shopping_bag } from "../../../../chunks/shopping-bag.js";
import { P as Plus } from "../../../../chunks/plus.js";
import { S as Search } from "../../../../chunks/search.js";
function Quotations($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let quotations = [];
    let search = "";
    let statusFilter = "";
    let summary = { total_value: 0, draft: 0, sent: 0, accepted: 0 };
    const statusLabels = {
      draft: "Borrador",
      sent: "Enviada",
      accepted: "Aceptada",
      rejected: "Rechazada",
      expired: "Expirada",
      invoiced: "Facturada"
    };
    let form = {
      lines: []
    };
    form.lines.reduce((sum, l) => sum + l.quantity * l.unit_price, 0);
    quotations.filter((q) => (q.quote_number || "").toLowerCase().includes(search.toLowerCase()) || (q.prospect_name || "").toLowerCase().includes(search.toLowerCase()) || (q.prospect_company || "").toLowerCase().includes(search.toLowerCase()));
    $$renderer2.push(`<div class="p-6 space-y-6"><div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"><div><h1 class="page-title flex items-center gap-2">`);
    File_spreadsheet($$renderer2, { size: 24 });
    $$renderer2.push(`<!----> Cotizaciones</h1> <p class="page-subtitle">Cotizaciones y catálogo de servicios SAJET</p></div> <div class="flex gap-2"><button class="btn-secondary flex items-center gap-2">`);
    Shopping_bag($$renderer2, { size: 16 });
    $$renderer2.push(`<!----> Catálogo</button> <button class="btn-accent flex items-center gap-2">`);
    Plus($$renderer2, { size: 16 });
    $$renderer2.push(`<!----> Nueva Cotización</button></div></div> <div class="grid grid-cols-1 sm:grid-cols-4 gap-4"><div class="stat-card"><div class="text-xs font-semibold uppercase text-gray-500 mb-1">Valor total</div> <div class="text-2xl font-bold text-text-light">$${escape_html(summary.total_value.toLocaleString("en-US", { minimumFractionDigits: 2 }))}</div></div> <div class="stat-card"><div class="text-xs font-semibold uppercase text-gray-500 mb-1">Borradores</div> <div class="text-2xl font-bold text-gray-400">${escape_html(summary.draft)}</div></div> <div class="stat-card"><div class="text-xs font-semibold uppercase text-gray-500 mb-1">Enviadas</div> <div class="text-2xl font-bold text-blue-400">${escape_html(summary.sent)}</div></div> <div class="stat-card"><div class="text-xs font-semibold uppercase text-gray-500 mb-1">Aceptadas</div> <div class="text-2xl font-bold text-emerald-400">${escape_html(summary.accepted)}</div></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="flex flex-col sm:flex-row gap-3"><div class="relative flex-1">`);
    Search($$renderer2, {
      size: 16,
      class: "absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"
    });
    $$renderer2.push(`<!----> <input type="text"${attr("value", search)} placeholder="Buscar cotización..." class="input pl-10 w-full"/></div> `);
    $$renderer2.select({ value: statusFilter, class: "input w-auto" }, ($$renderer3) => {
      $$renderer3.option({ value: "" }, ($$renderer4) => {
        $$renderer4.push(`Todos`);
      });
      $$renderer3.push(`<!--[-->`);
      const each_array_2 = ensure_array_like(Object.entries(statusLabels));
      for (let $$index_2 = 0, $$length = each_array_2.length; $$index_2 < $$length; $$index_2++) {
        let [key, label] = each_array_2[$$index_2];
        $$renderer3.option({ value: key }, ($$renderer4) => {
          $$renderer4.push(`${escape_html(label)}`);
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
      $$renderer2.push(`<div class="text-center py-12 text-gray-500">Cargando cotizaciones...</div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Quotations($$renderer);
}
export {
  _page as default
};
