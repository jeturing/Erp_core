import "clsx";
import { h as sanitize_props, i as spread_props, j as slot, d as escape_html, s as store_get, e as ensure_array_like, k as attr_class, b as stringify, u as unsubscribe_stores } from "../../../../chunks/index2.js";
import { c as currentUser } from "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { S as Spinner } from "../../../../chunks/Spinner.js";
import "../../../../chunks/client.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/root.js";
import "../../../../chunks/state.svelte.js";
import { B as Building_2 } from "../../../../chunks/building-2.js";
import { L as Log_out } from "../../../../chunks/log-out.js";
import { I as Icon } from "../../../../chunks/Icon.js";
import { G as Globe } from "../../../../chunks/globe.js";
import { U as Users } from "../../../../chunks/users.js";
import { P as Package } from "../../../../chunks/package.js";
import { S as Shield } from "../../../../chunks/shield.js";
function Layout_grid($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    [
      "rect",
      { "width": "7", "height": "7", "x": "3", "y": "3", "rx": "1" }
    ],
    [
      "rect",
      { "width": "7", "height": "7", "x": "14", "y": "3", "rx": "1" }
    ],
    [
      "rect",
      { "width": "7", "height": "7", "x": "14", "y": "14", "rx": "1" }
    ],
    [
      "rect",
      { "width": "7", "height": "7", "x": "3", "y": "14", "rx": "1" }
    ]
  ];
  Icon($$renderer, spread_props([
    { name: "layout-grid" },
    $$sanitized_props,
    {
      /**
       * @component @name LayoutGrid
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cmVjdCB3aWR0aD0iNyIgaGVpZ2h0PSI3IiB4PSIzIiB5PSIzIiByeD0iMSIgLz4KICA8cmVjdCB3aWR0aD0iNyIgaGVpZ2h0PSI3IiB4PSIxNCIgeT0iMyIgcng9IjEiIC8+CiAgPHJlY3Qgd2lkdGg9IjciIGhlaWdodD0iNyIgeD0iMTQiIHk9IjE0IiByeD0iMSIgLz4KICA8cmVjdCB3aWR0aD0iNyIgaGVpZ2h0PSI3IiB4PSIzIiB5PSIxNCIgcng9IjEiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/layout-grid
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
function TenantPortal($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let info = null;
    let activeTab = "dashboard";
    $$renderer2.push(`<div class="min-h-screen bg-[#F5F3EF]"><header class="bg-[#1a1a1a] border-b border-[#2a2a2a] sticky top-0 z-20"><div class="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between"><div class="flex items-center gap-3"><div class="w-8 h-8 rounded bg-[#C05A3C] flex items-center justify-center"><span class="text-white font-bold text-sm">S</span></div> <span class="text-white font-semibold tracking-[0.05em] text-sm">SAJET</span></div> <div class="flex items-center gap-2">`);
    Building_2($$renderer2, { class: "w-4 h-4 text-gray-400" });
    $$renderer2.push(`<!----> <span class="text-gray-300 text-sm font-medium">${escape_html(store_get($$store_subs ??= {}, "$currentUser", currentUser)?.company_name || info?.company_name || "Mi Empresa")}</span> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div> <button class="flex items-center gap-1.5 text-[11px] font-semibold tracking-[0.08em] text-gray-400 hover:text-white uppercase transition-colors">`);
    Log_out($$renderer2, { class: "w-3.5 h-3.5" });
    $$renderer2.push(`<!----> CERRAR SESIÓN</button></div> <div class="max-w-6xl mx-auto px-6 flex gap-1"><!--[-->`);
    const each_array = ensure_array_like([
      { id: "dashboard", label: "MI PORTAL", icon: Layout_grid },
      { id: "domains", label: "DOMINIOS", icon: Globe },
      { id: "users", label: "USUARIOS", icon: Users },
      { id: "services", label: "SERVICIOS", icon: Package },
      { id: "security", label: "SEGURIDAD", icon: Shield }
    ]);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let tab = each_array[$$index];
      $$renderer2.push(`<button${attr_class(`flex items-center gap-1.5 px-4 py-2.5 text-[11px] font-semibold tracking-[0.08em] transition-colors border-b-2 ${stringify(activeTab === tab.id ? "text-white border-[#C05A3C]" : "text-gray-500 border-transparent hover:text-gray-300 hover:border-gray-600")}`)}>`);
      if (tab.icon) {
        $$renderer2.push("<!--[-->");
        tab.icon($$renderer2, { class: "w-3.5 h-3.5" });
        $$renderer2.push("<!--]-->");
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push("<!--]-->");
      }
      $$renderer2.push(` ${escape_html(tab.label)}</button>`);
    }
    $$renderer2.push(`<!--]--></div></header> <main class="max-w-6xl mx-auto px-6 py-8 space-y-6">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="py-24 flex justify-center">`);
      Spinner($$renderer2, { size: "lg" });
      $$renderer2.push(`<!----></div>`);
    }
    $$renderer2.push(`<!--]--></main></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function _page($$renderer) {
  TenantPortal($$renderer);
}
export {
  _page as default
};
