import "clsx";
import { d as escape_html, e as ensure_array_like, k as attr_class, b as stringify } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
function WorkOrders($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let total = 0;
    let filterStatus = "";
    let customers = [];
    let customerSearch = "";
    const STATUS_LABELS = {
      requested: "Solicitada",
      approved: "Aprobada",
      in_progress: "En Progreso",
      completed: "Completada",
      rejected: "Rechazada",
      cancelled: "Cancelada"
    };
    customers.filter((c) => {
      const q = customerSearch.toLowerCase();
      return !q || c.name.toLowerCase().includes(q) || (c.email || "").toLowerCase().includes(q);
    });
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="flex h-full gap-4"><div class="flex-1 flex flex-col gap-4 min-w-0"><div class="flex items-center justify-between"><div><h1 class="text-2xl font-bold text-white">Órdenes de Trabajo</h1> <p class="text-sm text-gray-400 mt-0.5">${escape_html(total)} órdenes en total</p></div> <button class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors">+ Nueva Orden</button></div> <div class="flex gap-2"><!--[-->`);
    const each_array = ensure_array_like([
      "",
      "requested",
      "approved",
      "in_progress",
      "completed",
      "rejected"
    ]);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let s = each_array[$$index];
      $$renderer2.push(`<button${attr_class(`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${stringify(filterStatus === s ? "bg-red-600 text-white border-red-600" : "border-gray-700 text-gray-400 hover:text-white hover:border-gray-500")}`)}>${escape_html(s === "" ? "Todas" : STATUS_LABELS[s] ?? s)}</button>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-center py-16 text-gray-400">Cargando...</div>`);
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  WorkOrders($$renderer);
}
export {
  _page as default
};
