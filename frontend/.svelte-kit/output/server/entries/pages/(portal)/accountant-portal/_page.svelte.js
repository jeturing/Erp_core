import "clsx";
import { L as Layout } from "../../../../chunks/Layout.js";
import { S as Spinner } from "../../../../chunks/Spinner.js";
import "../../../../chunks/toast.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/root.js";
import "../../../../chunks/state.svelte.js";
import { h as sanitize_props, i as spread_props, j as slot } from "../../../../chunks/index2.js";
import { I as Icon } from "../../../../chunks/Icon.js";
function User_plus($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["path", { "d": "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" }],
    ["circle", { "cx": "9", "cy": "7", "r": "4" }],
    ["line", { "x1": "19", "x2": "19", "y1": "8", "y2": "14" }],
    ["line", { "x1": "22", "x2": "16", "y1": "11", "y2": "11" }]
  ];
  Icon($$renderer, spread_props([
    { name: "user-plus" },
    $$sanitized_props,
    {
      /**
       * @component @name UserPlus
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMTYgMjF2LTJhNCA0IDAgMCAwLTQtNEg2YTQgNCAwIDAgMC00IDR2MiIgLz4KICA8Y2lyY2xlIGN4PSI5IiBjeT0iNyIgcj0iNCIgLz4KICA8bGluZSB4MT0iMTkiIHgyPSIxOSIgeTE9IjgiIHkyPSIxNCIgLz4KICA8bGluZSB4MT0iMjIiIHgyPSIxNiIgeTE9IjExIiB5Mj0iMTEiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/user-plus
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
function AccountantPortal($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    Layout($$renderer2, {
      currentRoute: "accountant-portal",
      children: ($$renderer3) => {
        $$renderer3.push(`<div class="p-6 max-w-6xl mx-auto"><div class="flex items-center justify-between mb-8"><div><h1 class="text-2xl font-jakarta font-bold text-slate-dark">Accountant Dashboard</h1> <p class="text-sm font-inter text-slate mt-1">Manage all your client companies from one place.</p></div> <button class="inline-flex items-center gap-2 bg-primary hover:bg-navy text-white font-jakarta font-semibold text-sm px-4 py-2 rounded-btn shadow-soft transition-all">`);
        User_plus($$renderer3, { class: "w-4 h-4" });
        $$renderer3.push(`<!----> Invite Client</button></div> `);
        {
          $$renderer3.push("<!--[-->");
          $$renderer3.push(`<div class="flex items-center justify-center py-20">`);
          Spinner($$renderer3, { size: "lg" });
          $$renderer3.push(`<!----></div>`);
        }
        $$renderer3.push(`<!--]--></div>`);
      },
      $$slots: { default: true }
    });
  });
}
function _page($$renderer) {
  AccountantPortal($$renderer);
}
export {
  _page as default
};
