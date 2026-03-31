import "clsx";
import { h as sanitize_props, i as spread_props, j as slot, c as attr, d as escape_html, e as ensure_array_like, k as attr_class, b as stringify } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/toast.js";
import { a as formatDate } from "../../../../chunks/formatters.js";
import { Z as Zap } from "../../../../chunks/zap.js";
import { S as Search } from "../../../../chunks/search.js";
import { I as Icon } from "../../../../chunks/Icon.js";
import { U as Users } from "../../../../chunks/users.js";
import { S as Shield } from "../../../../chunks/shield.js";
import { S as Shield_check } from "../../../../chunks/shield-check.js";
import { K as Key } from "../../../../chunks/key.js";
import { E as External_link } from "../../../../chunks/external-link.js";
function At_sign($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["circle", { "cx": "12", "cy": "12", "r": "4" }],
    ["path", { "d": "M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-4 8" }]
  ];
  Icon($$renderer, spread_props([
    { name: "at-sign" },
    $$sanitized_props,
    {
      /**
       * @component @name AtSign
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSI0IiAvPgogIDxwYXRoIGQ9Ik0xNiA4djVhMyAzIDAgMCAwIDYgMHYtMWExMCAxMCAwIDEgMC00IDgiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/at-sign
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
function Briefcase($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    [
      "path",
      { "d": "M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" }
    ],
    [
      "rect",
      { "width": "20", "height": "14", "x": "2", "y": "6", "rx": "2" }
    ]
  ];
  Icon($$renderer, spread_props([
    { name: "briefcase" },
    $$sanitized_props,
    {
      /**
       * @component @name Briefcase
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMTYgMjBWNGEyIDIgMCAwIDAtMi0yaC00YTIgMiAwIDAgMC0yIDJ2MTYiIC8+CiAgPHJlY3Qgd2lkdGg9IjIwIiBoZWlnaHQ9IjE0IiB4PSIyIiB5PSI2IiByeD0iMiIgLz4KPC9zdmc+Cg==) - https://lucide.dev/icons/briefcase
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
function Calendar($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["path", { "d": "M8 2v4" }],
    ["path", { "d": "M16 2v4" }],
    [
      "rect",
      { "width": "18", "height": "18", "x": "3", "y": "4", "rx": "2" }
    ],
    ["path", { "d": "M3 10h18" }]
  ];
  Icon($$renderer, spread_props([
    { name: "calendar" },
    $$sanitized_props,
    {
      /**
       * @component @name Calendar
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNOCAydjQiIC8+CiAgPHBhdGggZD0iTTE2IDJ2NCIgLz4KICA8cmVjdCB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHg9IjMiIHk9IjQiIHJ4PSIyIiAvPgogIDxwYXRoIGQ9Ik0zIDEwaDE4IiAvPgo8L3N2Zz4K) - https://lucide.dev/icons/calendar
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
function Log_in($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["path", { "d": "m10 17 5-5-5-5" }],
    ["path", { "d": "M15 12H3" }],
    ["path", { "d": "M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" }]
  ];
  Icon($$renderer, spread_props([
    { name: "log-in" },
    $$sanitized_props,
    {
      /**
       * @component @name LogIn
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJtMTAgMTcgNS01LTUtNSIgLz4KICA8cGF0aCBkPSJNMTUgMTJIMyIgLz4KICA8cGF0aCBkPSJNMTUgM2g0YTIgMiAwIDAgMSAyIDJ2MTRhMiAyIDAgMCAxLTIgMmgtNCIgLz4KPC9zdmc+Cg==) - https://lucide.dev/icons/log-in
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
function Shield_alert($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    [
      "path",
      {
        "d": "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"
      }
    ],
    ["path", { "d": "M12 8v4" }],
    ["path", { "d": "M12 16h.01" }]
  ];
  Icon($$renderer, spread_props([
    { name: "shield-alert" },
    $$sanitized_props,
    {
      /**
       * @component @name ShieldAlert
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMjAgMTNjMCA1LTMuNSA3LjUtNy42NiA4Ljk1YTEgMSAwIDAgMS0uNjctLjAxQzcuNSAyMC41IDQgMTggNCAxM1Y2YTEgMSAwIDAgMSAxLTFjMiAwIDQuNS0xLjIgNi4yNC0yLjcyYTEuMTcgMS4xNyAwIDAgMSAxLjUyIDBDMTQuNTEgMy44MSAxNyA1IDE5IDVhMSAxIDAgMCAxIDEgMXoiIC8+CiAgPHBhdGggZD0iTTEyIDh2NCIgLz4KICA8cGF0aCBkPSJNMTIgMTZoLjAxIiAvPgo8L3N2Zz4K) - https://lucide.dev/icons/shield-alert
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
function NeuralUsers($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let searchQuery = "";
    let users = [];
    let loadingSearch = false;
    const typeLabels = {
      admin: {
        label: "ADMIN",
        color: "bg-terracotta/20 text-terracotta",
        icon: Shield
      },
      customer: {
        label: "TENANT",
        color: "bg-emerald-500/20 text-emerald-400",
        icon: Users
      },
      partner: {
        label: "PARTNER",
        color: "bg-blue-500/20 text-blue-400",
        icon: Briefcase
      }
    };
    $$renderer2.push(`<div class="space-y-6"><div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-charcoal to-charcoal-light border border-border-dark p-8"><div class="absolute top-0 right-0 p-4 opacity-10">`);
    Zap($$renderer2, { size: 120, strokeWidth: 0.5 });
    $$renderer2.push(`<!----></div> <div class="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6"><div><h1 class="text-3xl font-bold text-text-light tracking-tight flex items-center gap-3">`);
    Zap($$renderer2, { class: "text-accent", size: 28 });
    $$renderer2.push(`<!----> NEURAL CENTER</h1> <p class="text-gray-400 mt-2 max-w-xl">Gestión centralizada de identidades administrativas, tenants y partners. 
          Control maestro de credenciales, bypass de seguridad y auditoría de sesiones.</p></div> <div class="flex items-center gap-2"><div class="relative group">`);
    Search($$renderer2, {
      class: "absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-accent transition-colors",
      size: 18
    });
    $$renderer2.push(`<!----> <input type="text" placeholder="Email, nombre o ID..." class="input pl-10 pr-32 py-3 w-full md:w-80 shadow-2xl border-border-dark focus:border-accent"${attr("value", searchQuery)}/> <button class="absolute right-2 top-1/2 -translate-y-1/2 btn-accent px-4 py-1.5 text-xs font-bold uppercase"${attr("disabled", loadingSearch, true)}>${escape_html("BUSCAR")}</button></div></div></div></div> <div class="grid grid-cols-1 gap-4">`);
    if (users.length > 0) {
      $$renderer2.push("<!--[1-->");
      $$renderer2.push(`<!--[-->`);
      const each_array = ensure_array_like(users);
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let user = each_array[$$index];
        $$renderer2.push(`<div${attr_class(`card p-6 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 border-l-4 ${stringify(user.is_active ? "border-l-accent" : "border-l-gray-600")} hover:border-l-terracotta transition-all`, "svelte-jo84z5")}><div class="flex items-center gap-4"><div${attr_class(`w-12 h-12 rounded-xl flex items-center justify-center ${stringify(typeLabels[user.type].color)}`, "svelte-jo84z5")}>`);
        if (typeLabels[user.type].icon) {
          $$renderer2.push("<!--[-->");
          typeLabels[user.type].icon($$renderer2, { size: 24 });
          $$renderer2.push("<!--]-->");
        } else {
          $$renderer2.push("<!--[!-->");
          $$renderer2.push("<!--]-->");
        }
        $$renderer2.push(`</div> <div><div class="flex items-center gap-2"><span class="text-lg font-bold text-text-light">${escape_html(user.display_name)}</span> <span${attr_class(`text-[10px] font-black px-2 py-0.5 rounded-full ${stringify(typeLabels[user.type].color)}`, "svelte-jo84z5")}>${escape_html(typeLabels[user.type].label)}</span> `);
        if (user.onboarding_bypass) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<span class="bg-terracotta/20 text-terracotta text-[10px] font-black px-2 py-0.5 rounded-full flex items-center gap-1">`);
          Zap($$renderer2, { size: 10 });
          $$renderer2.push(`<!----> BYPASS ACTIVO</span>`);
        } else {
          $$renderer2.push("<!--[!-->");
        }
        $$renderer2.push(`<!--]--></div> <div class="flex items-center gap-4 mt-1 text-sm text-gray-400"><span class="flex items-center gap-1">`);
        At_sign($$renderer2, { size: 14 });
        $$renderer2.push(`<!----> ${escape_html(user.email)}</span> <span class="flex items-center gap-1">`);
        Calendar($$renderer2, { size: 14 });
        $$renderer2.push(`<!----> ID: ${escape_html(user.id)}</span> `);
        if (user.last_login_at) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<span class="flex items-center gap-1">`);
          Log_in($$renderer2, { size: 14 });
          $$renderer2.push(`<!----> login: ${escape_html(formatDate(user.last_login_at))}</span>`);
        } else {
          $$renderer2.push("<!--[!-->");
        }
        $$renderer2.push(`<!--]--></div></div></div> <div class="flex items-center gap-3 w-full lg:w-auto"><button class="btn-secondary flex-1 lg:flex-none flex items-center justify-center gap-2 py-2 px-4 text-xs font-bold" title="Alternar bypass de onboarding y MFA">`);
        if (user.onboarding_bypass) {
          $$renderer2.push("<!--[-->");
          Shield_alert($$renderer2, { size: 16, class: "text-terracotta" });
          $$renderer2.push(`<!----> QUITAR BYPASS`);
        } else {
          $$renderer2.push("<!--[!-->");
          Shield_check($$renderer2, { size: 16, class: "text-accent" });
          $$renderer2.push(`<!----> ACTIVAR BYPASS`);
        }
        $$renderer2.push(`<!--]--></button> <button class="btn-accent flex-1 lg:flex-none flex items-center justify-center gap-2 py-2 px-4 text-xs font-bold">`);
        Key($$renderer2, { size: 16 });
        $$renderer2.push(`<!----> GESTIONAR TOKENS</button> <button class="bg-gray-700 hover:bg-gray-600 text-text-light lg:p-2.5 rounded-lg transition-colors flex items-center justify-center" title="Ver Detalles Completos">`);
        External_link($$renderer2, { size: 18 });
        $$renderer2.push(`<!----></button></div></div>`);
      }
      $$renderer2.push(`<!--]-->`);
    } else {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<div class="card p-12 text-center bg-transparent border-dashed border-2 border-border-dark svelte-jo84z5"><div class="flex flex-col items-center gap-4 text-gray-600">`);
      Users($$renderer2, { size: 48, strokeWidth: 1 });
      $$renderer2.push(`<!----> <p class="font-medium">Ingresa un término de búsqueda para localizar usuarios en el ecosistema Sajet</p></div></div>`);
    }
    $$renderer2.push(`<!--]--></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
function _page($$renderer) {
  NeuralUsers($$renderer);
}
export {
  _page as default
};
