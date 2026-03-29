import "clsx";
import { h as sanitize_props, i as spread_props, j as slot, c as attr } from "../../../../chunks/index2.js";
import { o as onDestroy } from "../../../../chunks/index-server.js";
import "../../../../chunks/client.js";
import "../../../../chunks/toast.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/root.js";
import "../../../../chunks/state.svelte.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
import { I as Icon } from "../../../../chunks/Icon.js";
function Loader($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["path", { "d": "M12 2v4" }],
    ["path", { "d": "m16.2 7.8 2.9-2.9" }],
    ["path", { "d": "M18 12h4" }],
    ["path", { "d": "m16.2 16.2 2.9 2.9" }],
    ["path", { "d": "M12 18v4" }],
    ["path", { "d": "m4.9 19.1 2.9-2.9" }],
    ["path", { "d": "M2 12h4" }],
    ["path", { "d": "m4.9 4.9 2.9 2.9" }]
  ];
  Icon($$renderer, spread_props([
    { name: "loader" },
    $$sanitized_props,
    {
      /**
       * @component @name Loader
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMTIgMnY0IiAvPgogIDxwYXRoIGQ9Im0xNi4yIDcuOCAyLjktMi45IiAvPgogIDxwYXRoIGQ9Ik0xOCAxMmg0IiAvPgogIDxwYXRoIGQ9Im0xNi4yIDE2LjIgMi45IDIuOSIgLz4KICA8cGF0aCBkPSJNMTIgMTh2NCIgLz4KICA8cGF0aCBkPSJtNC45IDE5LjEgMi45LTIuOSIgLz4KICA8cGF0aCBkPSJNMiAxMmg0IiAvPgogIDxwYXRoIGQ9Im00LjkgNC45IDIuOSAyLjkiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/loader
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
function Migrations($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let loading = true;
    function stopPolling() {
    }
    onDestroy(stopPolling);
    $$renderer2.push(`<div class="space-y-6"><div class="flex items-center justify-between"><div><h1 class="page-title">MIGRACIONES</h1> <p class="page-subtitle">Migración de tenants entre nodos del clúster</p></div> <button class="btn-secondary px-4 py-2 flex items-center gap-2"${attr("disabled", loading, true)}>`);
    Refresh_cw($$renderer2, { size: 14, class: "animate-spin" });
    $$renderer2.push(`<!----> Recargar</button></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="flex items-center justify-center py-16">`);
      Loader($$renderer2, { size: 32, class: "animate-spin text-slate-400" });
      $$renderer2.push(`<!----></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Migrations($$renderer);
}
export {
  _page as default
};
