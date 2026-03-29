import "clsx";
import { d as escape_html, c as attr, e as ensure_array_like, f as derived } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { S as Shopping_bag } from "../../../../chunks/shopping-bag.js";
import { P as Plus } from "../../../../chunks/plus.js";
import { S as Search } from "../../../../chunks/search.js";
function ServiceCatalog($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let catalog = [];
    let categories = [];
    let search = "";
    let categoryFilter = "";
    let showInactive = false;
    let filtered = derived(() => catalog.filter((item) => {
      const matchesCategory = !categoryFilter;
      return matchesCategory;
    }));
    let groupedByCategory = derived(() => (() => {
      const groups = {};
      for (const item of filtered()) {
        const cat = item.category || "other";
        if (!groups[cat]) groups[cat] = [];
        groups[cat].push(item);
      }
      return groups;
    })());
    let activeCount = derived(() => catalog.filter((i) => i.is_active).length);
    let addonCount = derived(() => catalog.filter((i) => i.is_addon && i.is_active).length);
    let linkedCount = derived(() => catalog.filter((i) => (i.linked_plans?.length || 0) > 0).length);
    $$renderer2.push(`<div class="p-6 space-y-6"><div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"><div><h1 class="page-title flex items-center gap-2">`);
    Shopping_bag($$renderer2, { size: 24 });
    $$renderer2.push(`<!----> Catálogo de Servicios SAJET</h1> <p class="page-subtitle">Administra servicios, precios y vinculación con planes</p></div> <button class="btn-accent flex items-center gap-2">`);
    Plus($$renderer2, { size: 16 });
    $$renderer2.push(`<!----> Nuevo Servicio</button></div> <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"><div class="stat-card"><div class="text-xs font-semibold uppercase text-gray-500 mb-1">Servicios Activos</div> <div class="text-2xl font-bold text-text-light">${escape_html(activeCount())}</div></div> <div class="stat-card"><div class="text-xs font-semibold uppercase text-gray-500 mb-1">Categorías</div> <div class="text-2xl font-bold text-blue-400">${escape_html(Object.keys(groupedByCategory()).length)}</div></div> <div class="stat-card"><div class="text-xs font-semibold uppercase text-gray-500 mb-1">Add-ons</div> <div class="text-2xl font-bold text-amber-400">${escape_html(addonCount())}</div></div> <div class="stat-card"><div class="text-xs font-semibold uppercase text-gray-500 mb-1">Vinculados a Planes</div> <div class="text-2xl font-bold text-emerald-400">${escape_html(linkedCount())}</div></div></div> <div class="flex flex-col sm:flex-row gap-3"><div class="relative flex-1">`);
    Search($$renderer2, {
      size: 16,
      class: "absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"
    });
    $$renderer2.push(`<!----> <input type="text"${attr("value", search)} placeholder="Buscar servicio..." class="input pl-10 w-full"/></div> `);
    $$renderer2.select({ value: categoryFilter, class: "input w-auto" }, ($$renderer3) => {
      $$renderer3.option({ value: "" }, ($$renderer4) => {
        $$renderer4.push(`Todas las categorías`);
      });
      $$renderer3.push(`<!--[-->`);
      const each_array = ensure_array_like(categories);
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let cat = each_array[$$index];
        $$renderer3.option({ value: cat.value }, ($$renderer4) => {
          $$renderer4.push(`${escape_html(cat.label)}`);
        });
      }
      $$renderer3.push(`<!--]-->`);
    });
    $$renderer2.push(` <label class="flex items-center gap-2 text-sm text-gray-400 cursor-pointer select-none"><input type="checkbox"${attr("checked", showInactive, true)} class="accent-terracotta"/> Mostrar inactivos</label></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="flex justify-center py-12"><div class="animate-spin rounded-full h-8 w-8 border-2 border-terracotta border-t-transparent"></div></div>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
function _page($$renderer) {
  ServiceCatalog($$renderer);
}
export {
  _page as default
};
