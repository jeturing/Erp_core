import "clsx";
import { h as sanitize_props, i as spread_props, j as slot, e as ensure_array_like, k as attr_class, b as stringify, d as escape_html } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/toast.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
import { K as Key } from "../../../../chunks/key.js";
import { C as Credit_card } from "../../../../chunks/credit-card.js";
import { S as Server } from "../../../../chunks/server.js";
import { I as Icon } from "../../../../chunks/Icon.js";
import { G as Globe } from "../../../../chunks/globe.js";
function Database($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["ellipse", { "cx": "12", "cy": "5", "rx": "9", "ry": "3" }],
    ["path", { "d": "M3 5V19A9 3 0 0 0 21 19V5" }],
    ["path", { "d": "M3 12A9 3 0 0 0 21 12" }]
  ];
  Icon($$renderer, spread_props([
    { name: "database" },
    $$sanitized_props,
    {
      /**
       * @component @name Database
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8ZWxsaXBzZSBjeD0iMTIiIGN5PSI1IiByeD0iOSIgcnk9IjMiIC8+CiAgPHBhdGggZD0iTTMgNVYxOUE5IDMgMCAwIDAgMjEgMTlWNSIgLz4KICA8cGF0aCBkPSJNMyAxMkE5IDMgMCAwIDAgMjEgMTIiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/database
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
function Settings($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let activeTab = "credentials";
    $$renderer2.push(`<div class="space-y-6"><div class="flex items-center justify-between flex-wrap gap-4"><div><h1 class="page-title">SETTINGS</h1> <p class="page-subtitle">Configuración del sistema, credenciales y Stripe</p></div> <button class="btn-secondary px-4 py-2 flex items-center gap-2">`);
    Refresh_cw($$renderer2, { size: 14 });
    $$renderer2.push(`<!----> ACTUALIZAR</button></div> <div class="flex border-b border-gray-200 gap-1"><!--[-->`);
    const each_array = ensure_array_like([
      { id: "credentials", label: "Credenciales", icon: Key },
      { id: "stripe", label: "Stripe", icon: Credit_card },
      { id: "system", label: "Sistema", icon: Server },
      { id: "odoo", label: "Sajet", icon: Database },
      { id: "environment", label: "Ambiente", icon: Globe }
    ]);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let tab = each_array[$$index];
      const IconComp = tab.icon;
      $$renderer2.push(`<button${attr_class(`px-4 py-2.5 text-sm font-medium flex items-center gap-2 border-b-2 transition-colors ${stringify(activeTab === tab.id ? "border-indigo-600 text-indigo-700" : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300")}`)}>`);
      if (IconComp) {
        $$renderer2.push("<!--[-->");
        IconComp($$renderer2, { size: 14 });
        $$renderer2.push("<!--]-->");
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push("<!--]-->");
      }
      $$renderer2.push(` ${escape_html(tab.label)}</button>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[-->");
      {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="card p-8 text-center text-gray-500 text-sm">`);
        Refresh_cw($$renderer2, { size: 16, class: "animate-spin mx-auto mb-2" });
        $$renderer2.push(`<!----> Cargando credenciales...</div>`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Settings($$renderer);
}
export {
  _page as default
};
