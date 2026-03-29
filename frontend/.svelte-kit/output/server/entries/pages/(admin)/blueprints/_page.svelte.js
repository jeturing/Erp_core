import "clsx";
import { h as sanitize_props, i as spread_props, j as slot, c as attr, d as escape_html, k as attr_class, b as stringify } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { B as Boxes } from "../../../../chunks/boxes.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
import { D as Download } from "../../../../chunks/download.js";
import { P as Plus } from "../../../../chunks/plus.js";
import { P as Package } from "../../../../chunks/package.js";
import { I as Icon } from "../../../../chunks/Icon.js";
import { S as Search } from "../../../../chunks/search.js";
function Puzzle($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    [
      "path",
      {
        "d": "M15.39 4.39a1 1 0 0 0 1.68-.474 2.5 2.5 0 1 1 3.014 3.015 1 1 0 0 0-.474 1.68l1.683 1.682a2.414 2.414 0 0 1 0 3.414L19.61 15.39a1 1 0 0 1-1.68-.474 2.5 2.5 0 1 0-3.014 3.015 1 1 0 0 1 .474 1.68l-1.683 1.682a2.414 2.414 0 0 1-3.414 0L8.61 19.61a1 1 0 0 0-1.68.474 2.5 2.5 0 1 1-3.014-3.015 1 1 0 0 0 .474-1.68l-1.683-1.682a2.414 2.414 0 0 1 0-3.414L4.39 8.61a1 1 0 0 1 1.68.474 2.5 2.5 0 1 0 3.014-3.015 1 1 0 0 1-.474-1.68l1.683-1.682a2.414 2.414 0 0 1 3.414 0z"
      }
    ]
  ];
  Icon($$renderer, spread_props([
    { name: "puzzle" },
    $$sanitized_props,
    {
      /**
       * @component @name Puzzle
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMTUuMzkgNC4zOWExIDEgMCAwIDAgMS42OC0uNDc0IDIuNSAyLjUgMCAxIDEgMy4wMTQgMy4wMTUgMSAxIDAgMCAwLS40NzQgMS42OGwxLjY4MyAxLjY4MmEyLjQxNCAyLjQxNCAwIDAgMSAwIDMuNDE0TDE5LjYxIDE1LjM5YTEgMSAwIDAgMS0xLjY4LS40NzQgMi41IDIuNSAwIDEgMC0zLjAxNCAzLjAxNSAxIDEgMCAwIDEgLjQ3NCAxLjY4bC0xLjY4MyAxLjY4MmEyLjQxNCAyLjQxNCAwIDAgMS0zLjQxNCAwTDguNjEgMTkuNjFhMSAxIDAgMCAwLTEuNjguNDc0IDIuNSAyLjUgMCAxIDEtMy4wMTQtMy4wMTUgMSAxIDAgMCAwIC40NzQtMS42OGwtMS42ODMtMS42ODJhMi40MTQgMi40MTQgMCAwIDEgMC0zLjQxNEw0LjM5IDguNjFhMSAxIDAgMCAxIDEuNjguNDc0IDIuNSAyLjUgMCAxIDAgMy4wMTQtMy4wMTUgMSAxIDAgMCAxLS40NzQtMS42OGwxLjY4My0xLjY4MmEyLjQxNCAyLjQxNCAwIDAgMSAzLjQxNCAweiIgLz4KPC9zdmc+Cg==) - https://lucide.dev/icons/puzzle
       * @see https://lucide.dev/guide/packages/lucide-svelte - Documentation
       *
       * @param {Object} props - Lucide icons props and any valid SVG attribute
       * @returns {FunctionalComponent} Svelte component
       *
       */
      iconNode,
      children: ($$renderer2) => {
        $$renderer2.push(`<!--[-->`);
        slot($$renderer2, $$props, "default", {});
        $$renderer2.push(`<!--]-->`);
      },
      $$slots: { default: true }
    }
  ]));
}
function Blueprints($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let pickerModules, coreModules, addonModules;
    let modules = [];
    let packages = [];
    let loading = true;
    let importing = false;
    let search = "";
    let filterType = "all";
    let pkgModuleSearch = "";
    modules.filter((m) => {
      const q = search.toLowerCase();
      const matchSearch = !q || m.technical_name.toLowerCase().includes(q) || (m.display_name || "").toLowerCase().includes(q) || (m.category || "").toLowerCase().includes(q);
      const matchCat = true;
      const matchType = filterType === "all";
      return matchSearch && matchCat && matchType;
    });
    packages.filter((p) => {
      const q = search.toLowerCase();
      return !q || p.name.toLowerCase().includes(q) || (p.display_name || "").toLowerCase().includes(q);
    });
    pickerModules = modules.filter((m) => {
      const q = pkgModuleSearch.toLowerCase();
      const matchSearch = !q || m.technical_name.includes(q) || (m.display_name || "").toLowerCase().includes(q);
      const matchCat = true;
      return matchSearch && matchCat;
    });
    pickerModules.reduce(
      (acc, m) => {
        const cat = m.category || "General";
        if (!acc[cat]) acc[cat] = [];
        acc[cat].push(m);
        return acc;
      },
      {}
    );
    coreModules = modules.filter((m) => m.is_core).length;
    addonModules = modules.filter((m) => !m.is_core).length;
    $$renderer2.push(`<div class="p-6 space-y-5"><div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"><div><h1 class="page-title flex items-center gap-2">`);
    Boxes($$renderer2, {
      size: (
        // ── API ──
        // ── Module form ──
        // ── Package form ──
        22
      )
    });
    $$renderer2.push(`<!----> Blueprints</h1> <p class="page-subtitle">Catálogo de módulos y paquetes para tenants</p></div> <div class="flex gap-2 flex-wrap"><button class="btn-secondary flex items-center gap-2 text-xs"${attr("disabled", loading, true)}>`);
    Refresh_cw($$renderer2, { size: 13, class: "animate-spin" });
    $$renderer2.push(`<!----> Actualizar</button> <button class="btn-secondary flex items-center gap-2 text-xs"${attr("disabled", importing, true)} title="Importar módulos desde /opt/extra-addons/V17">`);
    Download($$renderer2, { size: 13, class: "" });
    $$renderer2.push(`<!----> ${escape_html("Importar V17")}</button> `);
    {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<button class="btn-accent flex items-center gap-2 text-xs">`);
      Plus($$renderer2, { size: 14 });
      $$renderer2.push(`<!----> Nuevo Paquete</button>`);
    }
    $$renderer2.push(`<!--]--></div></div> <div class="grid grid-cols-2 sm:grid-cols-4 gap-3"><div class="stat-card"><span class="stat-label">Total Módulos</span> <span class="stat-value">${escape_html(modules.length)}</span></div> <div class="stat-card"><span class="stat-label">Core</span> <span class="stat-value text-blue-400">${escape_html(coreModules)}</span></div> <div class="stat-card"><span class="stat-label">Add-ons</span> <span class="stat-value text-terracotta">${escape_html(addonModules)}</span></div> <div class="stat-card"><span class="stat-label">Paquetes</span> <span class="stat-value">${escape_html(packages.length)}</span></div></div> <div class="flex flex-col sm:flex-row gap-3 items-start sm:items-center"><div class="flex border border-border-dark overflow-hidden rounded"><button${attr_class(`px-4 py-2 text-xs font-semibold uppercase tracking-wider transition-colors ${stringify(
      "bg-charcoal text-text-light"
    )}`)}>`);
    Package($$renderer2, { size: 13, class: "inline mr-1" });
    $$renderer2.push(`<!----> Paquetes</button> <button${attr_class(`px-4 py-2 text-xs font-semibold uppercase tracking-wider transition-colors ${stringify("bg-bg-card text-text-secondary hover:bg-border-light")}`)}>`);
    Puzzle($$renderer2, { size: 13, class: "inline mr-1" });
    $$renderer2.push(`<!----> Módulos (${escape_html(modules.length)})</button></div> <div class="relative flex-1">`);
    Search($$renderer2, {
      size: 14,
      class: "absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"
    });
    $$renderer2.push(`<!----> <input type="text"${attr("value", search)} placeholder="Buscar..." class="input pl-9 w-full text-sm"/></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-center py-16 text-gray-500"><div class="w-8 h-8 border-2 border-charcoal border-t-transparent rounded-full animate-spin mx-auto"></div> <p class="mt-3 text-sm">Cargando blueprints...</p></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Blueprints($$renderer);
}
export {
  _page as default
};
