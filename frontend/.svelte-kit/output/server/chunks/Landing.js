import { h as sanitize_props, i as spread_props, j as slot, s as store_get, d as escape_html, e as ensure_array_like, u as unsubscribe_stores, o as bind_props, k as attr_class, b as stringify, c as attr, w as head } from "./index2.js";
import { a8 as fallback } from "./utils2.js";
import { $ as $format, g as $locale } from "./darkMode.js";
import { N as NavBar, F as Footer } from "./Footer.js";
import { A as Arrow_right } from "./arrow-right.js";
import { C as Calculator } from "./calculator.js";
import { B as Building_2 } from "./building-2.js";
import { H as Handshake } from "./handshake.js";
import { I as Icon } from "./Icon.js";
import { R as Receipt } from "./receipt.js";
import { C as Chart_column, E as Eye } from "./eye.js";
import { P as Package } from "./package.js";
import { U as Users } from "./users.js";
import { Z as Zap } from "./zap.js";
import { U as User_plus } from "./user-plus.js";
import { S as Server } from "./server.js";
import { M as Mail } from "./mail.js";
import { D as Dollar_sign } from "./dollar-sign.js";
import { P as Palette } from "./palette.js";
import { R as Refresh_cw } from "./refresh-cw.js";
import { S as Star } from "./star.js";
import { C as Chevron_down } from "./chevron-down.js";
import "@sveltejs/kit/internal";
import "./exports.js";
import "./utils.js";
import "@sveltejs/kit/internal/server";
import "./root.js";
import "./state.svelte.js";
import { C as Check } from "./check.js";
function html(value) {
  var html2 = String(value ?? "");
  var open = "<!---->";
  return open + html2 + "<!---->";
}
function Cloud($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    [
      "path",
      { "d": "M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z" }
    ]
  ];
  Icon($$renderer, spread_props([
    { name: "cloud" },
    $$sanitized_props,
    {
      /**
       * @component @name Cloud
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMTcuNSAxOUg5YTcgNyAwIDEgMSA2LjcxLTloMS43OWE0LjUgNC41IDAgMSAxIDAgOVoiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/cloud
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
function Git_merge($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["circle", { "cx": "18", "cy": "18", "r": "3" }],
    ["circle", { "cx": "6", "cy": "6", "r": "3" }],
    ["path", { "d": "M6 21V9a9 9 0 0 0 9 9" }]
  ];
  Icon($$renderer, spread_props([
    { name: "git-merge" },
    $$sanitized_props,
    {
      /**
       * @component @name GitMerge
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8Y2lyY2xlIGN4PSIxOCIgY3k9IjE4IiByPSIzIiAvPgogIDxjaXJjbGUgY3g9IjYiIGN5PSI2IiByPSIzIiAvPgogIDxwYXRoIGQ9Ik02IDIxVjlhOSA5IDAgMCAwIDkgOSIgLz4KPC9zdmc+Cg==) - https://lucide.dev/icons/git-merge
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
function Headphones($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    [
      "path",
      {
        "d": "M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a9 9 0 0 1 18 0v7a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3"
      }
    ]
  ];
  Icon($$renderer, spread_props([
    { name: "headphones" },
    $$sanitized_props,
    {
      /**
       * @component @name Headphones
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMyAxNGgzYTIgMiAwIDAgMSAyIDJ2M2EyIDIgMCAwIDEtMiAySDVhMiAyIDAgMCAxLTItMnYtN2E5IDkgMCAwIDEgMTggMHY3YTIgMiAwIDAgMS0yIDJoLTFhMiAyIDAgMCAxLTItMnYtM2EyIDIgMCAwIDEgMi0yaDMiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/headphones
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
function Rocket($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    [
      "path",
      {
        "d": "M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"
      }
    ],
    [
      "path",
      {
        "d": "m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"
      }
    ],
    ["path", { "d": "M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0" }],
    ["path", { "d": "M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5" }]
  ];
  Icon($$renderer, spread_props([
    { name: "rocket" },
    $$sanitized_props,
    {
      /**
       * @component @name Rocket
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNNC41IDE2LjVjLTEuNSAxLjI2LTIgNS0yIDVzMy43NC0uNSA1LTJjLjcxLS44NC43LTIuMTMtLjA5LTIuOTFhMi4xOCAyLjE4IDAgMCAwLTIuOTEtLjA5eiIgLz4KICA8cGF0aCBkPSJtMTIgMTUtMy0zYTIyIDIyIDAgMCAxIDItMy45NUExMi44OCAxMi44OCAwIDAgMSAyMiAyYzAgMi43Mi0uNzggNy41LTYgMTFhMjIuMzUgMjIuMzUgMCAwIDEtNCAyeiIgLz4KICA8cGF0aCBkPSJNOSAxMkg0cy41NS0zLjAzIDItNGMxLjYyLTEuMDggNSAwIDUgMCIgLz4KICA8cGF0aCBkPSJNMTIgMTV2NXMzLjAzLS41NSA0LTJjMS4wOC0xLjYyIDAtNSAwLTUiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/rocket
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
function Sparkles($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    [
      "path",
      {
        "d": "M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"
      }
    ],
    ["path", { "d": "M20 2v4" }],
    ["path", { "d": "M22 4h-4" }],
    ["circle", { "cx": "4", "cy": "20", "r": "2" }]
  ];
  Icon($$renderer, spread_props([
    { name: "sparkles" },
    $$sanitized_props,
    {
      /**
       * @component @name Sparkles
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMTEuMDE3IDIuODE0YTEgMSAwIDAgMSAxLjk2NiAwbDEuMDUxIDUuNTU4YTIgMiAwIDAgMCAxLjU5NCAxLjU5NGw1LjU1OCAxLjA1MWExIDEgMCAwIDEgMCAxLjk2NmwtNS41NTggMS4wNTFhMiAyIDAgMCAwLTEuNTk0IDEuNTk0bC0xLjA1MSA1LjU1OGExIDEgMCAwIDEtMS45NjYgMGwtMS4wNTEtNS41NThhMiAyIDAgMCAwLTEuNTk0LTEuNTk0bC01LjU1OC0xLjA1MWExIDEgMCAwIDEgMC0xLjk2Nmw1LjU1OC0xLjA1MWEyIDIgMCAwIDAgMS41OTQtMS41OTR6IiAvPgogIDxwYXRoIGQ9Ik0yMCAydjQiIC8+CiAgPHBhdGggZD0iTTIyIDRoLTQiIC8+CiAgPGNpcmNsZSBjeD0iNCIgY3k9IjIwIiByPSIyIiAvPgo8L3N2Zz4K) - https://lucide.dev/icons/sparkles
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
function Hero($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let displayStats;
    let stats = fallback($$props["stats"], () => [], true);
    let partnerBranding = fallback($$props["partnerBranding"], null);
    displayStats = stats.length > 0 ? stats : [
      {
        value: "500+",
        label: store_get($$store_subs ??= {}, "$t", $format)("hero.stat_companies")
      },
      {
        value: "99.9%",
        label: store_get($$store_subs ??= {}, "$t", $format)("hero.stat_uptime")
      },
      {
        value: "24/7",
        label: store_get($$store_subs ??= {}, "$t", $format)("hero.stat_support")
      },
      {
        value: "50+",
        label: store_get($$store_subs ??= {}, "$t", $format)("hero.stat_partners")
      }
    ];
    partnerBranding?.primary_color || "#1B4FD8";
    $$renderer2.push(`<section class="relative min-h-screen flex items-center justify-center overflow-hidden pt-20"><div class="absolute inset-0 bg-gradient-hero pointer-events-none"></div> <div class="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full bg-secondary/10 blur-3xl pointer-events-none"></div> <div class="relative z-10 max-w-4xl mx-auto px-6 text-center"><div class="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-5 py-2 mb-8 backdrop-blur-sm"><span class="text-xs font-inter font-medium text-white/90 tracking-[0.08em] uppercase">✦ ${escape_html(store_get($$store_subs ??= {}, "$t", $format)("hero.badge"))}</span></div> <h1 class="text-5xl sm:text-6xl lg:text-7xl font-jakarta font-extrabold text-white leading-[1.1] mb-6">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("hero.headline"))}<br/> <span class="bg-clip-text text-transparent bg-gradient-to-r from-white via-blue-200 to-secondary">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("hero.headline_highlight"))}</span></h1> <p class="text-lg font-inter text-blue-100/80 max-w-2xl mx-auto mb-10 leading-relaxed">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("hero.subheading"))}</p> <div class="flex flex-col sm:flex-row items-center justify-center gap-4 mb-5"><a href="/signup" class="flex items-center gap-2 text-navy font-inter font-semibold text-[15px] px-8 py-4 rounded-btn transition-all hover:-translate-y-px hover:shadow-elevated w-full sm:w-auto" style="background: white">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("common.get_started"))} `);
    Arrow_right($$renderer2, { class: "w-4 h-4" });
    $$renderer2.push(`<!----></a> <a href="/accountants" class="flex items-center gap-2 border border-white/30 text-white hover:bg-white/10 font-inter font-medium text-[15px] px-8 py-4 rounded-btn transition-all w-full sm:w-auto">`);
    Calculator($$renderer2, { class: "w-4 h-4" });
    $$renderer2.push(`<!----> ${escape_html(store_get($$store_subs ??= {}, "$t", $format)("common.join_accountant"))}</a></div> <div class="flex flex-wrap items-center justify-center gap-3 mb-10"><a href="/signup?mode=tenant" class="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-inter text-white/85 transition-all hover:bg-white/15">`);
    Building_2($$renderer2, { class: "w-4 h-4" });
    $$renderer2.push(`<!----> Crear mi empresa</a> <a href="/signup?mode=accountant" class="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-inter text-white/85 transition-all hover:bg-white/15">`);
    Calculator($$renderer2, { class: "w-4 h-4" });
    $$renderer2.push(`<!----> Soy contador</a> <a href="/partner-signup" class="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-inter text-white/85 transition-all hover:bg-white/15">`);
    Handshake($$renderer2, { class: "w-4 h-4" });
    $$renderer2.push(`<!----> Quiero ser socio</a></div> <p class="text-sm font-inter text-blue-200/60 mb-12">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("hero.trust_line"))} · Cliente, contador o socio: cada ruta tiene su propio onboarding.</p> <div class="flex flex-wrap justify-center gap-4 mb-14"><!--[-->`);
    const each_array = ensure_array_like(displayStats);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let stat = each_array[$$index];
      $$renderer2.push(`<div class="flex items-center gap-2 rounded-full border border-white/15 bg-white/5 backdrop-blur-sm px-5 py-2.5"><span class="text-base font-jakarta font-bold text-white">${escape_html(stat.value)}</span> <span class="text-xs font-inter text-blue-200/70">${escape_html(stat.label)}</span></div>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="max-w-3xl mx-auto"><div class="rounded-xl border border-white/15 bg-white/5 backdrop-blur-md shadow-elevated overflow-hidden"><div class="flex items-center gap-2 px-4 py-2.5 bg-white/10 border-b border-white/10"><span class="w-3 h-3 rounded-full bg-red-400/80"></span> <span class="w-3 h-3 rounded-full bg-yellow-400/80"></span> <span class="w-3 h-3 rounded-full bg-green-400/80"></span> <span class="flex-1 mx-4 rounded-md bg-white/10 h-5 flex items-center px-3"><span class="text-[10px] text-blue-200/50 font-mono">app.sajet.us/dashboard</span></span></div> <div class="p-6 space-y-4"><div class="flex items-center justify-between"><div class="h-4 w-32 rounded bg-white/10"></div> <div class="flex gap-2"><div class="h-4 w-16 rounded bg-white/10"></div> <div class="h-4 w-16 rounded bg-secondary/30"></div></div></div> <div class="grid grid-cols-4 gap-3"><div class="rounded-lg bg-white/10 p-4 space-y-2"><div class="h-3 w-14 rounded bg-white/15"></div> <div class="h-6 w-20 rounded bg-secondary/25"></div></div> <div class="rounded-lg bg-white/10 p-4 space-y-2"><div class="h-3 w-14 rounded bg-white/15"></div> <div class="h-6 w-16 rounded bg-emerald-400/25"></div></div> <div class="rounded-lg bg-white/10 p-4 space-y-2"><div class="h-3 w-14 rounded bg-white/15"></div> <div class="h-6 w-18 rounded bg-amber-400/25"></div></div> <div class="rounded-lg bg-white/10 p-4 space-y-2"><div class="h-3 w-14 rounded bg-white/15"></div> <div class="h-6 w-14 rounded bg-violet-400/25"></div></div></div> <div class="rounded-lg bg-white/10 h-32 flex items-end px-4 pb-3 gap-2"><div class="w-8 bg-secondary/30 rounded-t" style="height: 40%"></div> <div class="w-8 bg-secondary/30 rounded-t" style="height: 65%"></div> <div class="w-8 bg-secondary/30 rounded-t" style="height: 50%"></div> <div class="w-8 bg-secondary/30 rounded-t" style="height: 80%"></div> <div class="w-8 bg-secondary/30 rounded-t" style="height: 55%"></div> <div class="w-8 bg-secondary/30 rounded-t" style="height: 90%"></div> <div class="w-8 bg-secondary/30 rounded-t" style="height: 70%"></div> <div class="w-8 bg-secondary/40 rounded-t" style="height: 95%"></div></div> <div class="space-y-2"><div class="flex gap-3 items-center"><div class="h-3 w-24 rounded bg-white/10"></div> <div class="h-3 flex-1 rounded bg-white/5"></div> <div class="h-3 w-16 rounded bg-emerald-400/20"></div></div> <div class="flex gap-3 items-center"><div class="h-3 w-20 rounded bg-white/10"></div> <div class="h-3 flex-1 rounded bg-white/5"></div> <div class="h-3 w-16 rounded bg-amber-400/20"></div></div></div></div></div></div></div></section>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
    bind_props($$props, { stats, partnerBranding });
  });
}
function SocialProof($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    const industryKeys = [
      "industry_retail",
      "industry_manufacturing",
      "industry_services",
      "industry_healthcare",
      "industry_distribution",
      "industry_consulting"
    ];
    const industryIcons = ["🛒", "🏭", "💼", "🏥", "🚚", "📋"];
    $$renderer2.push(`<section class="bg-cloud py-16 border-y border-border"><div class="max-w-6xl mx-auto px-6"><p class="text-center text-sm font-inter text-slate tracking-wide mb-8">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("social_proof.trusted_by"))}</p> <div class="flex flex-wrap justify-center items-center gap-8"><!--[-->`);
    const each_array = ensure_array_like(industryKeys);
    for (let i = 0, $$length = each_array.length; i < $$length; i++) {
      let key = each_array[i];
      $$renderer2.push(`<div class="flex items-center gap-2 text-slate/60"><div class="w-8 h-8 rounded-card-sm bg-primary-light flex items-center justify-center"><span class="text-xs">${escape_html(industryIcons[i])}</span></div> <span class="text-sm font-inter font-medium text-slate">${escape_html(store_get($$store_subs ??= {}, "$t", $format)(`social_proof.${key}`))}</span></div>`);
    }
    $$renderer2.push(`<!--]--></div></div></section>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function ValueProp($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    const pillars = [
      {
        icon: Git_merge,
        title: store_get($$store_subs ??= {}, "$t", $format)("value_prop.one_source"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("value_prop.one_source_desc")
      },
      {
        icon: Cloud,
        title: store_get($$store_subs ??= {}, "$t", $format)("value_prop.managed_cloud"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("value_prop.managed_cloud_desc")
      },
      {
        icon: Building_2,
        title: store_get($$store_subs ??= {}, "$t", $format)("value_prop.multi_company"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("value_prop.multi_company_desc")
      }
    ];
    $$renderer2.push(`<section class="bg-white py-24"><div class="max-w-6xl mx-auto px-6"><div class="text-center mb-16"><span class="inline-flex items-center gap-2 rounded-full bg-primary-light text-primary text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("value_prop.badge"))}</span> <h2 class="text-4xl font-jakarta font-bold text-slate-dark mb-4 whitespace-pre-line">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("value_prop.headline"))}</h2> <p class="text-lg font-inter text-slate max-w-xl mx-auto leading-relaxed">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("value_prop.subheading"))}</p></div> <div class="grid grid-cols-1 md:grid-cols-3 gap-8"><!--[-->`);
    const each_array = ensure_array_like(pillars);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let pillar = each_array[$$index];
      $$renderer2.push(`<div class="rounded-card-lg border border-border bg-white p-8 hover:shadow-medium transition-all group"><div class="w-12 h-12 rounded-card-sm bg-primary-light flex items-center justify-center mb-5 group-hover:bg-primary/10 transition-colors">`);
      if (pillar.icon) {
        $$renderer2.push("<!--[-->");
        pillar.icon($$renderer2, { class: "w-6 h-6 text-primary", strokeWidth: 1.5 });
        $$renderer2.push("<!--]-->");
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push("<!--]-->");
      }
      $$renderer2.push(`</div> <h3 class="text-xl font-jakarta font-semibold text-slate-dark mb-3">${escape_html(pillar.title)}</h3> <p class="text-base font-inter text-slate leading-relaxed">${escape_html(pillar.desc)}</p></div>`);
    }
    $$renderer2.push(`<!--]--></div></div></section>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function FeaturesGrid($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let displayFeatures;
    const defaultFeatures = [
      {
        icon: Receipt,
        title: store_get($$store_subs ??= {}, "$t", $format)("features.finance"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("features.finance_desc")
      },
      {
        icon: Chart_column,
        title: store_get($$store_subs ??= {}, "$t", $format)("features.sales"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("features.sales_desc")
      },
      {
        icon: Package,
        title: store_get($$store_subs ??= {}, "$t", $format)("features.inventory"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("features.inventory_desc")
      },
      {
        icon: Users,
        title: store_get($$store_subs ??= {}, "$t", $format)("features.hr"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("features.hr_desc")
      },
      {
        icon: Zap,
        title: store_get($$store_subs ??= {}, "$t", $format)("features.payments"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("features.payments_desc")
      },
      {
        icon: Chart_column,
        title: store_get($$store_subs ??= {}, "$t", $format)("features.reports"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("features.reports_desc")
      }
    ];
    let features = fallback($$props["features"], () => [], true);
    displayFeatures = features.length > 0 ? features : defaultFeatures;
    $$renderer2.push(`<section id="features" class="bg-gradient-subtle py-24"><div class="max-w-6xl mx-auto px-6"><div class="text-center mb-16"><span class="inline-flex items-center gap-2 rounded-full bg-primary-light text-primary text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("features.title"))}</span> <h2 class="text-4xl font-jakarta font-bold text-slate-dark mb-4">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("features.subtitle"))}</h2></div> <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"><!--[-->`);
    const each_array = ensure_array_like(displayFeatures);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let feature = each_array[$$index];
      $$renderer2.push(`<div class="rounded-card-sm border border-border bg-white p-6 hover:shadow-medium hover:border-primary/20 transition-all group"><div class="w-10 h-10 rounded-lg bg-primary-light flex items-center justify-center mb-4 group-hover:bg-primary/10 transition-colors">`);
      if (feature.icon) {
        $$renderer2.push("<!--[-->");
        if (feature.icon) {
          $$renderer2.push("<!--[-->");
          feature.icon($$renderer2, { class: "w-5 h-5 text-primary", strokeWidth: 1.5 });
          $$renderer2.push("<!--]-->");
        } else {
          $$renderer2.push("<!--[!-->");
          $$renderer2.push("<!--]-->");
        }
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></div> <h3 class="text-base font-jakarta font-semibold text-slate-dark mb-2">${escape_html(feature.title)}</h3> <p class="text-sm font-inter text-slate leading-relaxed">${escape_html(feature.desc)}</p></div>`);
    }
    $$renderer2.push(`<!--]--></div></div></section>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
    bind_props($$props, { features });
  });
}
function HowItWorks($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    const steps = [
      {
        num: 1,
        icon: User_plus,
        title: store_get($$store_subs ??= {}, "$t", $format)("how_it_works.step1_title"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("how_it_works.step1_desc")
      },
      {
        num: 2,
        icon: Server,
        title: store_get($$store_subs ??= {}, "$t", $format)("how_it_works.step2_title"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("how_it_works.step2_desc")
      },
      {
        num: 3,
        icon: Mail,
        title: store_get($$store_subs ??= {}, "$t", $format)("how_it_works.step3_title"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("how_it_works.step3_desc")
      },
      {
        num: 4,
        icon: Rocket,
        title: store_get($$store_subs ??= {}, "$t", $format)("how_it_works.step4_title"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("how_it_works.step4_desc")
      }
    ];
    $$renderer2.push(`<section id="how-it-works" class="bg-white py-24"><div class="max-w-5xl mx-auto px-6"><div class="text-center mb-16"><span class="inline-flex items-center gap-2 rounded-full bg-primary-light text-primary text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("how_it_works.title"))}</span> <h2 class="text-4xl font-jakarta font-bold text-slate-dark mb-4">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("how_it_works.subtitle"))}</h2></div> <div class="relative"><div class="hidden md:block absolute left-1/2 top-8 bottom-8 w-px bg-gradient-to-b from-primary/30 via-primary/10 to-transparent -translate-x-1/2" aria-hidden="true"></div> <div class="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-y-16"><!--[-->`);
    const each_array = ensure_array_like(steps);
    for (let i = 0, $$length = each_array.length; i < $$length; i++) {
      let step = each_array[i];
      $$renderer2.push(`<div${attr_class(`relative flex items-start gap-5 ${stringify(i % 2 === 1 ? "md:col-start-2" : "md:col-start-1")}`)}><div class="flex-shrink-0 relative"><div class="w-14 h-14 rounded-2xl bg-primary-light flex items-center justify-center shadow-soft">`);
      if (step.icon) {
        $$renderer2.push("<!--[-->");
        step.icon($$renderer2, { class: "w-6 h-6 text-primary", strokeWidth: 1.5 });
        $$renderer2.push("<!--]-->");
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push("<!--]-->");
      }
      $$renderer2.push(`</div> <span class="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-primary text-white text-xs font-jakarta font-bold flex items-center justify-center shadow-md">${escape_html(step.num)}</span></div> <div><h3 class="text-lg font-jakarta font-semibold text-slate-dark mb-1">${escape_html(step.title)}</h3> <p class="text-sm font-inter text-slate leading-relaxed">${escape_html(step.desc)}</p></div></div>`);
    }
    $$renderer2.push(`<!--]--></div></div> <div class="text-center mt-16"><a href="/signup" class="inline-flex items-center gap-2 bg-primary hover:bg-navy text-white font-jakarta font-semibold text-sm px-6 py-3 rounded-btn shadow-soft hover:shadow-medium transition-all">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("how_it_works.cta"))}</a></div></div></section>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function ForPartners($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    const benefits = [
      {
        icon: Dollar_sign,
        title: store_get($$store_subs ??= {}, "$t", $format)("partners.recurring"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("partners.recurring_desc")
      },
      {
        icon: Palette,
        title: store_get($$store_subs ??= {}, "$t", $format)("partners.white_label"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("partners.white_label_desc")
      },
      {
        icon: Headphones,
        title: store_get($$store_subs ??= {}, "$t", $format)("partners.support"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("partners.support_desc")
      }
    ];
    $$renderer2.push(`<section id="partners" class="bg-[#0F172A] py-24"><div class="max-w-5xl mx-auto px-6"><div class="text-center mb-14"><span class="inline-flex items-center gap-2 rounded-full bg-emerald-500/15 text-emerald-400 text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("partners.title"))}</span> <h2 class="text-4xl font-jakarta font-bold text-white mb-4">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("partners.subtitle"))}</h2> <p class="text-base font-inter text-slate-400 max-w-xl mx-auto">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("partners.description"))}</p></div> <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12"><!--[-->`);
    const each_array = ensure_array_like(benefits);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let benefit = each_array[$$index];
      $$renderer2.push(`<div class="rounded-card-sm border border-white/10 bg-white/5 backdrop-blur-sm p-6 hover:border-emerald-400/30 hover:bg-white/[0.07] transition-all group"><div class="w-10 h-10 rounded-lg bg-emerald-500/15 flex items-center justify-center mb-4">`);
      if (benefit.icon) {
        $$renderer2.push("<!--[-->");
        benefit.icon($$renderer2, { class: "w-5 h-5 text-emerald-400", strokeWidth: 1.5 });
        $$renderer2.push("<!--]-->");
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push("<!--]-->");
      }
      $$renderer2.push(`</div> <h3 class="text-base font-jakarta font-semibold text-white mb-2">${escape_html(benefit.title)}</h3> <p class="text-sm font-inter text-slate-400 leading-relaxed">${escape_html(benefit.desc)}</p></div>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="text-center"><a href="/partner-signup" class="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-white font-jakarta font-semibold text-sm px-6 py-3 rounded-btn shadow-soft hover:shadow-medium transition-all">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("partners.cta"))}</a></div></div></section>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function AccountantsSummary($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    const benefits = [
      {
        icon: Eye,
        title: store_get($$store_subs ??= {}, "$t", $format)("accountants.benefit1_title"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("accountants.benefit1_desc")
      },
      {
        icon: Building_2,
        title: store_get($$store_subs ??= {}, "$t", $format)("accountants.benefit2_title"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("accountants.benefit2_desc")
      },
      {
        icon: Refresh_cw,
        title: store_get($$store_subs ??= {}, "$t", $format)("accountants.benefit3_title"),
        desc: store_get($$store_subs ??= {}, "$t", $format)("accountants.benefit3_desc")
      }
    ];
    $$renderer2.push(`<section class="bg-white py-24 border-t border-border"><div class="max-w-5xl mx-auto px-6"><div class="text-center mb-14"><span class="inline-flex items-center gap-2 rounded-full bg-blue-50 text-primary text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">`);
    Calculator($$renderer2, { class: "w-3.5 h-3.5" });
    $$renderer2.push(`<!----> ${escape_html(store_get($$store_subs ??= {}, "$t", $format)("accountants.badge"))}</span> <h2 class="text-4xl font-jakarta font-bold text-slate-dark mb-4 whitespace-pre-line">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("accountants.headline"))}<br/> ${escape_html(store_get($$store_subs ??= {}, "$t", $format)("accountants.headline_highlight"))}</h2> <p class="text-base font-inter text-slate max-w-xl mx-auto leading-relaxed">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("accountants.subheading"))}</p></div> <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10"><!--[-->`);
    const each_array = ensure_array_like(benefits);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let benefit = each_array[$$index];
      $$renderer2.push(`<div class="rounded-card-sm border border-border bg-cloud/50 p-6 hover:shadow-soft transition-all group"><div class="w-10 h-10 rounded-lg bg-primary-light flex items-center justify-center mb-4">`);
      if (benefit.icon) {
        $$renderer2.push("<!--[-->");
        benefit.icon($$renderer2, { class: "w-5 h-5 text-primary", strokeWidth: 1.5 });
        $$renderer2.push("<!--]-->");
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push("<!--]-->");
      }
      $$renderer2.push(`</div> <h3 class="text-base font-jakarta font-semibold text-slate-dark mb-2">${escape_html(benefit.title)}</h3> <p class="text-sm font-inter text-slate leading-relaxed">${escape_html(benefit.desc)}</p></div>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="text-center"><a href="/accountants" class="inline-flex items-center gap-2 bg-primary hover:bg-navy text-white font-jakarta font-semibold text-sm px-6 py-3 rounded-btn shadow-soft hover:shadow-medium transition-all">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("accountants.cta"))} `);
    Arrow_right($$renderer2, { class: "w-4 h-4" });
    $$renderer2.push(`<!----></a></div></div></section>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function Testimonials($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let displayTestimonials;
    let testimonials = fallback($$props["testimonials"], () => [], true);
    const fallback$1 = [
      {
        name: store_get($$store_subs ??= {}, "$t", $format)("testimonials.t1_author"),
        role: "",
        company: store_get($$store_subs ??= {}, "$t", $format)("testimonials.t1_company"),
        text: store_get($$store_subs ??= {}, "$t", $format)("testimonials.t1_quote"),
        stars: 5,
        avatar_url: ""
      },
      {
        name: store_get($$store_subs ??= {}, "$t", $format)("testimonials.t2_author"),
        role: "",
        company: store_get($$store_subs ??= {}, "$t", $format)("testimonials.t2_company"),
        text: store_get($$store_subs ??= {}, "$t", $format)("testimonials.t2_quote"),
        stars: 5,
        avatar_url: ""
      },
      {
        name: store_get($$store_subs ??= {}, "$t", $format)("testimonials.t3_author"),
        role: "",
        company: store_get($$store_subs ??= {}, "$t", $format)("testimonials.t3_company"),
        text: store_get($$store_subs ??= {}, "$t", $format)("testimonials.t3_quote"),
        stars: 5,
        avatar_url: ""
      }
    ];
    displayTestimonials = testimonials.length > 0 ? testimonials : fallback$1;
    $$renderer2.push(`<section id="testimonials" class="bg-white py-24"><div class="max-w-6xl mx-auto px-6"><div class="text-center mb-14"><span class="inline-flex items-center gap-2 rounded-full bg-primary-light text-primary text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("testimonials.title"))}</span> <h2 class="text-4xl font-jakarta font-bold text-slate-dark mb-4">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("testimonials.subtitle"))}</h2></div> <div class="grid grid-cols-1 md:grid-cols-3 gap-6"><!--[-->`);
    const each_array = ensure_array_like(displayTestimonials);
    for (let $$index_1 = 0, $$length = each_array.length; $$index_1 < $$length; $$index_1++) {
      let t = each_array[$$index_1];
      $$renderer2.push(`<div class="rounded-card-lg border border-border bg-cloud p-6 flex flex-col"><div class="flex items-center gap-0.5 mb-4"><!--[-->`);
      const each_array_1 = ensure_array_like(Array(t.stars || 5));
      for (let $$index = 0, $$length2 = each_array_1.length; $$index < $$length2; $$index++) {
        each_array_1[$$index];
        Star($$renderer2, { class: "w-4 h-4 text-amber-400 fill-amber-400" });
      }
      $$renderer2.push(`<!--]--></div> <p class="text-sm font-inter text-slate-dark leading-relaxed flex-1 mb-6">"${escape_html(t.text)}"</p> <div class="flex items-center gap-3">`);
      if (t.avatar_url) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<img${attr("src", t.avatar_url)}${attr("alt", t.name)} class="w-10 h-10 rounded-full object-cover"/>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div class="w-10 h-10 rounded-full bg-primary-light text-primary font-jakarta font-bold text-sm flex items-center justify-center">${escape_html(t.name?.charAt(0) || "?")}</div>`);
      }
      $$renderer2.push(`<!--]--> <div><p class="text-sm font-jakarta font-semibold text-slate-dark">${escape_html(t.name)}</p> <p class="text-xs font-inter text-slate">${escape_html(t.role)}, ${escape_html(t.company)}</p></div></div></div>`);
    }
    $$renderer2.push(`<!--]--></div></div></section>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
    bind_props($$props, { testimonials });
  });
}
function FAQ($$renderer) {
  const faqs = [
    {
      q: "¿Necesito una tarjeta de crédito para el período de prueba?",
      a: "No. Los 14 días de prueba son completamente gratis, sin necesidad de tarjeta de crédito ni compromiso. Solo te pedimos tu correo electrónico."
    },
    {
      q: "¿Puedo cambiar de plan en cualquier momento?",
      a: "Sí, puedes subir o bajar de plan en cualquier momento. Los ajustes se prorratean automáticamente en tu próxima factura."
    },
    {
      q: "¿Sajet funciona para empresas en República Dominicana?",
      a: "Absolutamente. Sajet fue diseñado desde cero para el mercado dominicano: soporte para NCF, e-CF / facturación electrónica ante la DGII (vía República FEL), DOP y USD, e integraciones locales."
    },
    {
      q: "¿Qué incluye la integración de facturación electrónica (e-CF)?",
      a: "Sajet se integra nativamente con República FEL, proveedor certificado por la DGII. La generación, firma y envío de comprobantes fiscales electrónicos se gestiona directamente desde Sajet. El servicio FEL se contrata por separado (desde $50/mes según volumen)."
    },
    {
      q: "¿Cuántos usuarios puedo agregar a mi plan?",
      a: "Depende del plan: Básico admite hasta 10 usuarios, Profesional hasta 50, y Empresarial es ilimitado. Puedes usar la calculadora de precios para ver el costo exacto según la cantidad de usuarios que necesitas."
    },
    {
      q: "¿Cómo funciona el soporte?",
      a: "Todos los planes incluyen soporte por correo y chat. El plan Profesional incluye soporte prioritario con respuesta en 4 horas. El plan Empresarial incluye un gerente de cuenta dedicado y soporte 24/7."
    }
  ];
  let openIndex = null;
  $$renderer.push(`<section id="faq" class="bg-white py-24"><div class="max-w-2xl mx-auto px-6"><div class="text-center mb-12"><span class="inline-flex items-center gap-2 rounded-full bg-primary-light text-primary text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">FAQ</span> <h2 class="text-4xl font-jakarta font-bold text-slate-dark">Preguntas frecuentes</h2> <p class="text-base font-inter text-slate mt-3 max-w-md mx-auto">¿Algo que no encontraste aquí? Escríbenos por WhatsApp o correo y te respondemos en minutos.</p></div> <div class="divide-y divide-border"><!--[-->`);
  const each_array = ensure_array_like(faqs);
  for (let i = 0, $$length = each_array.length; i < $$length; i++) {
    let faq = each_array[i];
    $$renderer.push(`<div><button type="button" class="w-full flex items-center justify-between gap-4 py-5 text-left focus:outline-none group"${attr("aria-expanded", openIndex === i)}><span class="text-base font-jakarta font-semibold text-slate-dark group-hover:text-primary transition-colors">${escape_html(faq.q)}</span> `);
    Chevron_down($$renderer, {
      class: `w-5 h-5 text-slate flex-shrink-0 transition-transform duration-200 ${stringify(openIndex === i ? "rotate-180 text-primary" : "")}`
    });
    $$renderer.push(`<!----></button> `);
    if (openIndex === i) {
      $$renderer.push("<!--[-->");
      $$renderer.push(`<div class="pb-5"><p class="text-sm font-inter text-slate leading-relaxed">${escape_html(faq.a)}</p></div>`);
    } else {
      $$renderer.push("<!--[!-->");
    }
    $$renderer.push(`<!--]--></div>`);
  }
  $$renderer.push(`<!--]--></div> <div class="mt-10 text-center"><p class="text-sm font-inter text-slate mb-3">¿Más preguntas?</p> <a href="https://wa.me/4012001999" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-jakarta font-semibold px-5 py-2.5 rounded-btn transition-colors shadow-soft"><svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"></path><path d="M12 0C5.373 0 0 5.373 0 12c0 2.123.558 4.115 1.535 5.836L.057 23.944l6.264-1.449A11.94 11.94 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.818a9.818 9.818 0 01-5.013-1.373l-.359-.214-3.724.861.882-3.624-.234-.373A9.818 9.818 0 012.182 12C2.182 6.567 6.567 2.182 12 2.182S21.818 6.567 21.818 12 17.433 21.818 12 21.818z"></path></svg> Chatear en WhatsApp</a></div></div></section>`);
}
function PricingPreview($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let displayPlans, priceKey;
    let plans = fallback($$props["plans"], () => [], true);
    let partnerCode = fallback($$props["partnerCode"], "");
    let annual = false;
    let userCount = 1;
    let pricingByPlan = {};
    let pricingLoading = false;
    let pricingError = "";
    let lastPriceKey = "";
    function normalizePlan(p) {
      return {
        ...p,
        name: p.name,
        display_name: p.display_name || p.name,
        base_price: p.base_price ?? p.monthly_price ?? 0,
        price_per_user: p.price_per_user ?? 0,
        included_users: p.included_users ?? 1,
        max_users: p.max_users ?? 0,
        trial_days: p.trial_days ?? 14,
        annual_discount_percent: p.annual_discount_percent ?? 20
      };
    }
    async function updatePrices() {
      if (displayPlans.length === 0) {
        pricingByPlan = {};
        return;
      }
      pricingLoading = true;
      pricingError = "";
      try {
        const results = await Promise.all(displayPlans.map(async (plan) => {
          const res = await fetch("/api/public/calculate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              plan_name: plan.name,
              user_count: userCount,
              billing_period: annual ? "annual" : "monthly"
            })
          });
          if (!res.ok) {
            throw new Error(`Pricing error for ${plan.name}`);
          }
          return res.json();
        }));
        const next = {};
        results.forEach((result) => {
          next[result.plan_name] = result;
        });
        pricingByPlan = next;
      } catch (err) {
        console.error("[Pricing] Failed to calculate pricing", err);
        pricingError = store_get($$store_subs ??= {}, "$t", $format)("pricing.error");
        pricingByPlan = {};
      } finally {
        pricingLoading = false;
      }
    }
    function displayTotal(plan) {
      const data = pricingByPlan[plan.name];
      if (!data) return "—";
      const total = data.monthly.total;
      return `$${Math.round(total)}`;
    }
    function extraUsersLine(plan) {
      const data = pricingByPlan[plan.name];
      if (!data || !data.extra_users || data.extra_users === 0) return "";
      return `${plan.included_users} incluido${plan.included_users > 1 ? "s" : ""} + ${data.extra_users} × $${plan.price_per_user} extra`;
    }
    function maxUsersLabel(plan) {
      if (!plan.max_users || plan.max_users === 0) return "∞";
      return `máx ${plan.max_users}`;
    }
    function storageLabel(mb) {
      if (!mb || mb === 0) return "∞";
      if (mb >= 1024) return `${mb / 1024} GB`;
      return `${mb} MB`;
    }
    function apiLabel(plan) {
      if (plan.name === "pro") return "API lectura";
      return "API completa";
    }
    function supportLabel(plan) {
      if (plan.name === "basic") return "Email";
      if (plan.name === "pro") return "Prioritario";
      return "24/7";
    }
    displayPlans = plans.length > 0 ? plans.map(normalizePlan) : [];
    priceKey = `${userCount}|${annual}|${displayPlans.map((p) => p.name).join(",")}`;
    if (displayPlans.length > 0 && priceKey !== lastPriceKey) {
      lastPriceKey = priceKey;
      updatePrices();
    }
    $$renderer2.push(`<section id="pricing" class="bg-gradient-subtle py-24"><div class="max-w-6xl mx-auto px-6"><div class="text-center mb-12"><span class="inline-flex items-center gap-2 rounded-full bg-primary-light text-primary text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.title"))}</span> <h2 class="text-4xl font-jakarta font-bold text-slate-dark mb-4 whitespace-pre-line">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.headline"))}</h2> <p class="text-base font-inter text-slate max-w-lg mx-auto">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.subtitle"))}</p></div> <div class="flex flex-col sm:flex-row items-center justify-center gap-6 mb-12"><div class="flex items-center gap-3 bg-white rounded-full border border-border px-1.5 py-1 shadow-soft"><button${attr_class(`text-sm font-inter font-medium px-4 py-1.5 rounded-full transition-all ${stringify(
      "bg-primary text-white shadow-sm"
    )}`)}>${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.monthly"))}</button> <button${attr_class(`text-sm font-inter font-medium px-4 py-1.5 rounded-full transition-all ${stringify("text-slate hover:text-slate-dark")}`)}>${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.annual"))} <span class="text-xs text-emerald-600 font-semibold ml-1">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.save"))}</span></button></div> <div class="flex items-center gap-3 bg-white rounded-full border border-border px-4 py-2 shadow-soft"><label class="text-sm font-inter text-slate">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.users"))}:</label> <button class="w-7 h-7 rounded-full bg-cloud text-slate-dark font-bold text-lg flex items-center justify-center hover:bg-primary-light transition-colors disabled:opacity-40"${attr("disabled", userCount <= 1, true)}>−</button> <span class="w-8 text-center text-sm font-jakarta font-bold text-slate-dark">${escape_html(userCount)}</span> <button class="w-7 h-7 rounded-full bg-cloud text-slate-dark font-bold text-lg flex items-center justify-center hover:bg-primary-light transition-colors">+</button></div></div> <div class="grid grid-cols-1 md:grid-cols-3 gap-6 items-start"><!--[-->`);
    const each_array = ensure_array_like(displayPlans);
    for (let $$index_1 = 0, $$length = each_array.length; $$index_1 < $$length; $$index_1++) {
      let plan = each_array[$$index_1];
      $$renderer2.push(`<div${attr_class(`relative rounded-card-lg border bg-white p-6 flex flex-col ${stringify(plan.is_highlighted ? "border-primary shadow-elevated ring-2 ring-primary/20" : "border-border shadow-soft")}`)}>`);
      if (plan.is_highlighted) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="absolute -top-3 left-1/2 -translate-x-1/2"><span class="inline-flex items-center gap-1 bg-primary text-white text-xs font-inter font-semibold px-3 py-1 rounded-full shadow-md">`);
        Sparkles($$renderer2, { class: "w-3 h-3" });
        $$renderer2.push(`<!----> ${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.most_popular"))}</span></div>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> <h3 class="text-lg font-jakarta font-bold text-slate-dark mb-1">${escape_html(plan.display_name || plan.name)}</h3> <div class="flex items-baseline gap-1 mb-2">`);
      if (pricingLoading) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<span class="text-3xl font-jakarta font-bold text-slate animate-pulse">…</span>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<span class="text-4xl font-jakarta font-extrabold text-slate-dark">${escape_html(displayTotal(plan))}</span> <span class="text-sm font-inter text-slate">/mes</span>`);
      }
      $$renderer2.push(`<!--]--></div> <div class="text-xs font-inter text-slate mb-3 bg-cloud rounded-lg px-3 py-2 space-y-0.5"><p class="font-semibold text-slate-dark">Base: $${escape_html(plan.base_price)}/mes</p> <p>+$${escape_html(plan.price_per_user)}/usuario adicional</p> <p class="text-slate-400">${escape_html(plan.included_users)} usuario${escape_html(plan.included_users > 1 ? "s" : "")} incluido${escape_html(plan.included_users > 1 ? "s" : "")} · Hasta ${escape_html(maxUsersLabel(plan))}</p> `);
      if (!pricingLoading && extraUsersLine(plan)) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<p class="text-primary font-medium pt-1 border-t border-border">${escape_html(extraUsersLine(plan))}</p>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></div> <div class="flex flex-wrap gap-1.5 mb-4"><span class="inline-flex items-center gap-1 text-[11px] font-inter font-medium bg-cloud text-slate-dark rounded-full px-2.5 py-1">💾 ${escape_html(storageLabel(plan.max_storage_mb))}</span> <span class="inline-flex items-center gap-1 text-[11px] font-inter font-medium bg-cloud text-slate-dark rounded-full px-2.5 py-1">🔒 Backups ∞</span> <span class="inline-flex items-center gap-1 text-[11px] font-inter font-medium bg-cloud text-slate-dark rounded-full px-2.5 py-1">⚡ ${escape_html(apiLabel(plan))}</span> <span class="inline-flex items-center gap-1 text-[11px] font-inter font-medium bg-cloud text-slate-dark rounded-full px-2.5 py-1">💬 ${escape_html(supportLabel(plan))}</span></div> <p class="text-xs font-inter text-primary font-semibold mb-4">✓ ${escape_html(plan.trial_days)} días de prueba gratis · Sin tarjeta</p> <ul class="space-y-2.5 mb-6 flex-1"><!--[-->`);
      const each_array_1 = ensure_array_like(plan.features || []);
      for (let $$index = 0, $$length2 = each_array_1.length; $$index < $$length2; $$index++) {
        let feat = each_array_1[$$index];
        $$renderer2.push(`<li class="flex items-start gap-2 text-sm font-inter text-slate-dark">`);
        Check($$renderer2, {
          class: "w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5",
          strokeWidth: 2.5
        });
        $$renderer2.push(`<!----> <span>${escape_html(feat)}</span></li>`);
      }
      $$renderer2.push(`<!--]--></ul> <button${attr_class(`w-full text-center text-sm font-jakarta font-semibold py-2.5 rounded-btn transition-all ${stringify(plan.is_highlighted ? "bg-primary hover:bg-navy text-white shadow-soft hover:shadow-medium" : "border border-primary text-primary hover:bg-primary hover:text-white")}`)}>${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.start_trial"))}</button></div>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    if (pricingError) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<p class="text-center text-xs font-inter text-rose-600 mt-8">${escape_html(pricingError)}</p>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <p class="text-center text-xs font-inter text-slate mt-8">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.all_prices_usd"))}</p> <p class="text-center text-xs font-inter text-slate-400 mt-2">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.billing_note"))}</p> <div class="mt-10 rounded-card-lg border border-amber-200 bg-amber-50 p-5 flex gap-4 items-start"><div class="flex-shrink-0 w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center">`);
    Zap($$renderer2, { class: "w-5 h-5 text-amber-600" });
    $$renderer2.push(`<!----></div> <div class="flex-1"><p class="text-sm font-jakarta font-bold text-amber-900 mb-1">⚡ ¿Necesitas facturación electrónica DGII (e-CF)?</p> <p class="text-sm font-inter text-amber-800 leading-relaxed mb-2">Todos los planes incluyen integración nativa con <strong>República FEL</strong>, proveedor certificado ante la DGII.
          El módulo e-CF se activa sobre cualquier plan — el costo del timbre fiscal depende de tu volumen de documentos
          y se factura directamente por el PAC. <strong>Nos encargamos de toda la implementación técnica sin costo adicional.</strong></p> <div class="flex flex-wrap gap-3"><a href="mailto:ventas@sajet.us?subject=Consulta%20integracion%20FEL%20-%20SAJET" class="inline-flex items-center gap-1 text-xs font-inter font-semibold text-amber-700 hover:text-amber-900 transition-colors">Consultar integración FEL →</a> <span class="text-xs font-inter text-amber-600">·</span> <a href="https://republicafel.com" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 text-xs font-inter font-semibold text-amber-700 hover:text-amber-900 transition-colors">Ver tarifas República FEL ↗</a></div></div></div></div></section>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
    bind_props($$props, { plans, partnerCode });
  });
}
function FinalCTA($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    $$renderer2.push(`<section id="cta-final" class="bg-gradient-hero py-24"><div class="max-w-3xl mx-auto px-6 text-center"><h2 class="text-4xl md:text-5xl font-jakarta font-extrabold text-white mb-6 leading-tight">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("final_cta.headline"))}<br/> ${escape_html(store_get($$store_subs ??= {}, "$t", $format)("final_cta.headline_highlight"))}</h2> <p class="text-lg font-inter text-white/80 mb-10 max-w-xl mx-auto">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("final_cta.subheading"))}</p> <div class="flex flex-col sm:flex-row items-center justify-center gap-4"><a href="/signup" class="inline-flex items-center gap-2 bg-white text-primary font-jakarta font-semibold text-sm px-8 py-3.5 rounded-btn shadow-medium hover:shadow-elevated hover:bg-cloud transition-all">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("final_cta.cta_primary"))} `);
    Arrow_right($$renderer2, { class: "w-4 h-4" });
    $$renderer2.push(`<!----></a> <a href="mailto:ventas@sajet.us?subject=Quiero%20hablar%20con%20SAJET" class="inline-flex items-center gap-2 border border-white/40 text-white font-jakarta font-semibold text-sm px-8 py-3.5 rounded-btn hover:bg-white/10 transition-all">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("final_cta.cta_secondary"))}</a></div></div></section>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function Landing($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let partnerBranding = fallback($$props["partnerBranding"], null);
    let partnerCode = fallback($$props["partnerCode"], "");
    let stats = {};
    let plans = [];
    let features = [];
    let testimonials = [];
    head("1egott1", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>${escape_html(store_get($$store_subs ??= {}, "$t", $format)("seo.title"))}</title>`);
      });
      $$renderer3.push(`<meta name="description"${attr("content", store_get($$store_subs ??= {}, "$t", $format)("seo.description"))}/> <meta name="keywords"${attr("content", store_get($$store_subs ??= {}, "$t", $format)("seo.keywords"))}/> <meta property="og:type" content="website"/> <meta property="og:url" content="https://sajet.us"/> <meta property="og:title"${attr("content", store_get($$store_subs ??= {}, "$t", $format)("seo.og_title"))}/> <meta property="og:description"${attr("content", store_get($$store_subs ??= {}, "$t", $format)("seo.og_description"))}/> <meta property="og:image" content="https://sajet.us/static/images/og-sajet-erp.png"/> <meta property="og:image:alt"${attr("content", store_get($$store_subs ??= {}, "$t", $format)("seo.og_image_alt"))}/> <meta property="og:locale"${attr("content", store_get($$store_subs ??= {}, "$locale", $locale) === "es" ? "es_LA" : "en_US")}/> <meta property="og:site_name" content="SAJET ERP"/> <meta name="twitter:card" content="summary_large_image"/> <meta name="twitter:title"${attr("content", store_get($$store_subs ??= {}, "$t", $format)("seo.og_title"))}/> <meta name="twitter:description"${attr("content", store_get($$store_subs ??= {}, "$t", $format)("seo.og_description"))}/> <meta name="twitter:image" content="https://sajet.us/static/images/og-sajet-erp.png"/> <link rel="alternate" hreflang="en" href="https://sajet.us/"/> <link rel="alternate" hreflang="es" href="https://sajet.us/?lang=es"/> <link rel="alternate" hreflang="x-default" href="https://sajet.us/"/> <link rel="canonical" href="https://sajet.us/"/> ${html(`<script type="application/ld+json">${JSON.stringify({
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "SAJET ERP",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "url": "https://sajet.us",
        "description": store_get($$store_subs ??= {}, "$t", $format)("seo.description"),
        "offers": {
          "@type": "Offer",
          "price": "0",
          "priceCurrency": "USD",
          "description": "14-day free trial"
        },
        "publisher": {
          "@type": "Organization",
          "name": "Jeturing SRL",
          "url": "https://sajet.us"
        }
      })}<\/script>`)}`);
    });
    $$renderer2.push(`<div class="min-h-screen bg-white font-inter">`);
    NavBar($$renderer2, { partnerBranding });
    $$renderer2.push(`<!----> `);
    Hero($$renderer2, { stats, partnerBranding });
    $$renderer2.push(`<!----> `);
    SocialProof($$renderer2);
    $$renderer2.push(`<!----> `);
    ValueProp($$renderer2);
    $$renderer2.push(`<!----> `);
    FeaturesGrid($$renderer2, { features });
    $$renderer2.push(`<!----> `);
    HowItWorks($$renderer2);
    $$renderer2.push(`<!----> `);
    PricingPreview($$renderer2, { plans, partnerCode });
    $$renderer2.push(`<!----> `);
    ForPartners($$renderer2);
    $$renderer2.push(`<!----> `);
    AccountantsSummary($$renderer2);
    $$renderer2.push(`<!----> `);
    Testimonials($$renderer2, { testimonials });
    $$renderer2.push(`<!----> `);
    FAQ($$renderer2);
    $$renderer2.push(`<!----> `);
    FinalCTA($$renderer2);
    $$renderer2.push(`<!----> `);
    Footer($$renderer2);
    $$renderer2.push(`<!----></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
    bind_props($$props, { partnerBranding, partnerCode });
  });
}
export {
  Landing as L
};
