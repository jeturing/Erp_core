import { h as sanitize_props, i as spread_props, j as slot, s as store_get, a as attr_style, d as escape_html, e as ensure_array_like, c as attr, b as stringify, u as unsubscribe_stores, o as bind_props, w as head } from "./index2.js";
import { a8 as fallback } from "./utils2.js";
import { $ as $format, j as $locale } from "./darkMode.js";
import { N as NavBar, F as Footer } from "./Footer.js";
import { A as Arrow_right } from "./arrow-right.js";
import { C as Calculator } from "./calculator.js";
import { B as Building_2 } from "./building-2.js";
import { H as Handshake } from "./handshake.js";
import { R as Receipt } from "./receipt.js";
import { C as Chart_column, E as Eye } from "./eye.js";
import { P as Package } from "./package.js";
import { U as Users } from "./users.js";
import { Z as Zap } from "./zap.js";
import { D as Dollar_sign } from "./dollar-sign.js";
import { P as Palette } from "./palette.js";
import { I as Icon } from "./Icon.js";
import { R as Refresh_cw } from "./refresh-cw.js";
import "@sveltejs/kit/internal";
import "./exports.js";
import "./utils.js";
import "@sveltejs/kit/internal/server";
import "./root.js";
import "./state.svelte.js";
import { C as Check } from "./check.js";
import { h as html } from "./html.js";
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
    const partnerBranding = null;
    const metrics = [
      {
        label: "Ingresos",
        value: "$84,290",
        delta: "+12.4%",
        color: "#00FF9F"
      },
      {
        label: "Clientes",
        value: "1,847",
        delta: "+8.1%",
        color: "#0EA5E9"
      },
      {
        label: "Facturas",
        value: "342",
        delta: "+5.3%",
        color: "#a78bfa"
      },
      {
        label: "Pendiente",
        value: "$9,140",
        delta: "-2.1%",
        color: "#f59e0b"
      }
    ];
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
    $$renderer2.push(`<section class="relative min-h-screen flex items-center justify-center overflow-hidden pt-20" style="background: #020e1f;"><div class="absolute inset-0 pointer-events-none" style="background: radial-gradient(ellipse 80% 55% at 50% 0%, rgba(0,59,115,0.65) 0%, transparent 70%);"></div> <div class="absolute pointer-events-none" style="top:-80px;left:50%;transform:translateX(-50%);width:640px;height:420px; background:radial-gradient(ellipse at 50% 0%, rgba(0,255,159,0.11) 0%, transparent 65%); filter:blur(48px);"></div> <div class="absolute pointer-events-none" style="top:20%;left:-5%;width:500px;height:500px; background:radial-gradient(circle, rgba(0,59,115,0.28) 0%, transparent 70%); filter:blur(90px);"></div> <div class="absolute pointer-events-none" style="top:30%;right:-5%;width:400px;height:400px; background:radial-gradient(circle, rgba(6,182,212,0.10) 0%, transparent 70%); filter:blur(70px);"></div> <div class="absolute bottom-0 left-0 right-0 h-48 pointer-events-none" style="background:linear-gradient(to bottom, transparent, #020e1f);"></div> <div class="absolute inset-0 pointer-events-none" style="opacity:0.022; background-image:linear-gradient(rgba(255,255,255,0.6) 1px, transparent 1px), linear-gradient(90deg,rgba(255,255,255,0.6) 1px, transparent 1px); background-size:60px 60px;"></div> <div class="relative z-10 max-w-4xl mx-auto px-6 text-center"${attr_style(`opacity:${stringify(0)}; transform:translateY(${stringify(18)}px); transition:opacity 0.65s ease, transform 0.65s ease;`)}><div class="inline-flex items-center gap-2 rounded-full px-4 py-1.5 mb-8 text-[11px] font-inter font-semibold tracking-[0.10em] uppercase" style="background:rgba(0,255,159,0.09); border:1px solid rgba(0,255,159,0.28); color:#00FF9F;"><span class="w-1.5 h-1.5 rounded-full" style="background:#00FF9F; box-shadow:0 0 6px #00FF9F;"></span> ${escape_html(store_get($$store_subs ??= {}, "$t", $format)("hero.badge"))}</div> <h1 class="font-jakarta font-extrabold text-[#f0f4ff] mb-6 leading-[1.06]" style="font-size: clamp(2.4rem, 6vw, 3.9rem); letter-spacing: -1.8px;">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("hero.headline"))}<br/> <span style="color:#00FF9F; text-shadow:0 0 36px rgba(0,255,159,0.35);">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("hero.headline_highlight"))}</span></h1> <p class="font-inter text-[#c8d3e8] max-w-2xl mx-auto mb-10 leading-relaxed" style="font-size:1.1rem; letter-spacing:-0.2px;">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("hero.subheading"))}</p> <div class="flex flex-col sm:flex-row items-center justify-center gap-3 mb-5"><a href="/signup" class="flex items-center gap-2 font-inter font-semibold text-[14px] px-7 py-3.5 rounded-lg w-full sm:w-auto justify-center transition-all duration-150 hover:-translate-y-px" style="background:#00FF9F; color:#020e1f; box-shadow:0 4px 18px rgba(0,255,159,0.30);">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("common.get_started"))} `);
    Arrow_right($$renderer2, { class: "w-4 h-4" });
    $$renderer2.push(`<!----></a> <a href="/accountants" class="flex items-center gap-2 font-inter font-medium text-[14px] text-[#c8d3e8] px-7 py-3.5 rounded-lg w-full sm:w-auto justify-center transition-all hover:-translate-y-px" style="border:1px solid rgba(255,255,255,0.12); background:rgba(255,255,255,0.04);">`);
    Calculator($$renderer2, { class: "w-4 h-4 text-[#7a8fa6]" });
    $$renderer2.push(`<!----> ${escape_html(store_get($$store_subs ??= {}, "$t", $format)("common.join_accountant"))}</a></div> <div class="flex flex-wrap items-center justify-center gap-2.5 mb-8"><!--[-->`);
    const each_array = ensure_array_like([
      {
        icon: Building_2,
        label: "Crear mi empresa",
        href: "/signup?mode=tenant"
      },
      {
        icon: Calculator,
        label: "Soy contador",
        href: "/signup?mode=accountant"
      },
      {
        icon: Handshake,
        label: "Quiero ser socio",
        href: "/partner-signup"
      }
    ]);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let item = each_array[$$index];
      $$renderer2.push(`<a${attr("href", item.href)} class="inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 text-[12px] font-inter text-[#7a8fa6] transition-all hover:text-[#f0f4ff]" style="border:1px solid rgba(255,255,255,0.08); background:rgba(255,255,255,0.03);">`);
      {
        $$renderer2.push("<!--[-->");
        const C = item.icon;
        C($$renderer2, { class: "w-3.5 h-3.5" });
      }
      $$renderer2.push(`<!--]--> ${escape_html(item.label)}</a>`);
    }
    $$renderer2.push(`<!--]--></div> <p class="text-[12px] font-inter text-[#4a6080] mb-10">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("hero.trust_line"))} · Sin tarjeta de crédito · Cancela cuando quieras</p> <div class="flex flex-wrap justify-center gap-3 mb-14"><!--[-->`);
    const each_array_1 = ensure_array_like(displayStats);
    for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
      let stat = each_array_1[$$index_1];
      $$renderer2.push(`<div class="flex items-center gap-2 rounded-full px-5 py-2" style="border:1px solid rgba(255,255,255,0.08); background:rgba(255,255,255,0.04); backdrop-filter:blur(8px);"><span class="text-[15px] font-jakarta font-bold text-[#f0f4ff]">${escape_html(stat.value)}</span> <span class="text-[11px] font-inter text-[#7a8fa6]">${escape_html(stat.label)}</span></div>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="max-w-3xl mx-auto rounded-xl overflow-hidden" style="border:1px solid rgba(255,255,255,0.10); background:rgba(255,255,255,0.025); backdrop-filter:blur(20px); box-shadow:0 24px 80px rgba(0,0,0,0.60), 0 0 0 1px rgba(0,255,159,0.04);"><div class="flex items-center gap-2 px-4 py-3" style="background:rgba(255,255,255,0.04); border-bottom:1px solid rgba(255,255,255,0.08);"><span class="w-2.5 h-2.5 rounded-full" style="background:#ff5f56;"></span> <span class="w-2.5 h-2.5 rounded-full" style="background:#ffbd2e;"></span> <span class="w-2.5 h-2.5 rounded-full" style="background:#27c93f;"></span> <div class="flex-1 mx-4 rounded-md h-5 flex items-center px-3 gap-1.5" style="background:rgba(255,255,255,0.06);"><span class="w-2 h-2 rounded-full" style="background:rgba(0,255,159,0.5);"></span> <span class="text-[10px] font-mono" style="color:#4a6080;">app.sajet.us/dashboard</span></div> <div class="flex gap-1.5"><div class="h-4 w-14 rounded text-[8px] flex items-center justify-center font-mono" style="background:rgba(0,255,159,0.14); color:#00FF9F;">● Live</div></div></div> <div class="p-5 space-y-4"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><div class="h-3 w-28 rounded" style="background:rgba(255,255,255,0.12);"></div> <div class="h-3 w-14 rounded" style="background:rgba(255,255,255,0.06);"></div></div> <div class="h-6 w-20 rounded-lg text-[9px] font-inter flex items-center justify-center" style="background:rgba(0,255,159,0.14); color:#00FF9F; border:1px solid rgba(0,255,159,0.20);">+ Nueva factura</div></div> <div class="grid grid-cols-4 gap-3"><!--[-->`);
    const each_array_2 = ensure_array_like(metrics);
    for (let $$index_2 = 0, $$length = each_array_2.length; $$index_2 < $$length; $$index_2++) {
      let m = each_array_2[$$index_2];
      $$renderer2.push(`<div class="rounded-xl p-3.5 space-y-1.5" style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.07);"><div class="text-[8px] font-inter uppercase tracking-widest" style="color:#4a6080;">${escape_html(m.label)}</div> <div class="text-[13px] font-mono font-semibold"${attr_style(`color:${stringify(m.color)};`)}>${escape_html(m.value)}</div> <div class="text-[8px] font-inter px-1.5 py-0.5 rounded-full w-fit"${attr_style(`background:rgba(0,255,159,0.08); color:${stringify(m.color)};`)}>${escape_html(m.delta)}</div></div>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="rounded-xl flex items-end px-3 pb-3 gap-1 pt-4" style="background:rgba(255,255,255,0.025); border:1px solid rgba(255,255,255,0.06); height:90px;"><!--[-->`);
    const each_array_3 = ensure_array_like([38, 55, 42, 70, 52, 88, 65, 95, 72, 85, 60, 78]);
    for (let i = 0, $$length = each_array_3.length; i < $$length; i++) {
      let h = each_array_3[i];
      $$renderer2.push(`<div class="flex-1 rounded-t"${attr_style(`height:${stringify(h)}%; background:${stringify(i === 7 || i === 11 ? "linear-gradient(to top,rgba(0,255,159,0.65),rgba(0,255,159,0.22))" : "linear-gradient(to top,rgba(14,165,233,0.30),rgba(14,165,233,0.08))")};`)}></div>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="space-y-1.5 pb-1"><!--[-->`);
    const each_array_4 = ensure_array_like([
      {
        name: "Distribuidora Nova",
        amount: "$3,200",
        status: "Pagado",
        color: "#00FF9F"
      },
      {
        name: "Constructora Sur",
        amount: "$1,850",
        status: "Pendiente",
        color: "#f59e0b"
      },
      {
        name: "Grupo Meridian LLC",
        amount: "$5,400",
        status: "Pagado",
        color: "#00FF9F"
      }
    ]);
    for (let $$index_4 = 0, $$length = each_array_4.length; $$index_4 < $$length; $$index_4++) {
      let row = each_array_4[$$index_4];
      $$renderer2.push(`<div class="flex gap-3 items-center px-3 py-2 rounded-lg" style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05);"><div class="h-1.5 w-1.5 rounded-full"${attr_style(`background:${stringify(row.color)};`)}></div> <div class="text-[10px] font-inter flex-1" style="color:#c8d3e8;">${escape_html(row.name)}</div> <div class="text-[10px] font-mono" style="color:#f0f4ff;">${escape_html(row.amount)}</div> <div class="text-[8px] font-inter px-2 py-0.5 rounded-full"${attr_style(`color:${stringify(row.color)}; border:1px solid rgba(0,255,159,0.18); background:rgba(0,255,159,0.07);`)}>${escape_html(row.status)}</div></div>`);
    }
    $$renderer2.push(`<!--]--></div></div></div></div></section>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
    bind_props($$props, { stats, partnerBranding });
  });
}
function SocialProof($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    const logos = ["TecHeels", "AgroLife", "Esecure", "Partner+", "Socios +"];
    $$renderer2.push(`<section id="socialproof-section" style="background:#ffffff; border-top:1px solid #e5edf5; border-bottom:1px solid #e5edf5; padding:56px 24px;"><div style="max-width:960px; margin:0 auto; text-align:center;"><p${attr_style(` font-size:12px; font-weight:600; letter-spacing:0.12em; text-transform:uppercase; color:#64748d; margin-bottom:40px; opacity:${stringify(0)}; transform:translateY(${stringify("10px")}); transition:opacity 0.5s cubic-bezier(.16,1,.3,1), transform 0.5s cubic-bezier(.16,1,.3,1); `)}>Empresas que confían en SAJET</p> <div style="display:flex; gap:48px; justify-content:center; flex-wrap:wrap; align-items:center;"><!--[-->`);
    const each_array = ensure_array_like(logos);
    for (let i = 0, $$length = each_array.length; i < $$length; i++) {
      let logo = each_array[i];
      $$renderer2.push(`<div${attr_style(` font-family:'Plus Jakarta Sans',system-ui,sans-serif; font-size:15px; font-weight:700; letter-spacing:-0.02em; color:#273951; opacity:${stringify(0)}; transform:translateY(${stringify("8px")}); transition:opacity 0.5s ${stringify(0.1 + i * 0.06)}s cubic-bezier(.16,1,.3,1), transform 0.5s ${stringify(0.1 + i * 0.06)}s cubic-bezier(.16,1,.3,1); `)}>${escape_html(logo)}</div>`);
    }
    $$renderer2.push(`<!--]--></div> <div style="display:flex; gap:48px; justify-content:center; flex-wrap:wrap; margin-top:56px; padding-top:40px; border-top:1px solid #e5edf5;"><!--[-->`);
    const each_array_1 = ensure_array_like([
      { num: "150+", label: "Tenants activos" },
      { num: "99.8%", label: "Uptime 2025" },
      { num: "4.9★", label: "Satisfacción media" }
    ]);
    for (let i = 0, $$length = each_array_1.length; i < $$length; i++) {
      let stat = each_array_1[i];
      $$renderer2.push(`<div${attr_style(` text-align:center; opacity:${stringify(0)}; transform:translateY(${stringify("12px")}); transition:opacity 0.6s ${stringify(0.3 + i * 0.08)}s cubic-bezier(.16,1,.3,1), transform 0.6s ${stringify(0.3 + i * 0.08)}s cubic-bezier(.16,1,.3,1); `)}><div style="font-size:2.2rem; font-weight:700; color:#003B73; letter-spacing:-0.04em; font-variant-numeric:tabular-nums;">${escape_html(stat.num)}</div> <div style="font-size:13px; color:#64748d; margin-top:4px;">${escape_html(stat.label)}</div></div>`);
    }
    $$renderer2.push(`<!--]--></div></div></section>`);
  });
}
function ValueProp($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    $$renderer2.push(`<section id="valueprop-section" style="background: #f5f5f7; padding: clamp(80px, 10vw, 140px) 24px;"><div style="max-width:960px; margin:0 auto; text-align:center;"><p${attr_style(` font-size:13px; font-weight:600; letter-spacing:0.12em; text-transform:uppercase; color:#003B73; margin-bottom:20px; opacity:${stringify(0)}; transform:translateY(${stringify("12px")}); transition:opacity 0.55s cubic-bezier(.16,1,.3,1), transform 0.55s cubic-bezier(.16,1,.3,1); `)}>Por qué SAJET</p> <h2${attr_style(` font-family:'Plus Jakarta Sans','Inter',system-ui,sans-serif; font-size:clamp(2rem,5vw,3rem); font-weight:700; letter-spacing:-0.03em; line-height:1.08; color:#061b31; margin:0 0 24px; opacity:${stringify(0)}; transform:translateY(${stringify("20px")}); transition:opacity 0.65s 0.1s cubic-bezier(.16,1,.3,1), transform 0.65s 0.1s cubic-bezier(.16,1,.3,1); `)}>Un ERP diseñado para<br/>la forma en que trabajas hoy.</h2> <p${attr_style(` font-size:18px; line-height:1.6; color:#64748d; max-width:560px; margin:0 auto 64px; font-weight:300; opacity:${stringify(0)}; transform:translateY(${stringify("16px")}); transition:opacity 0.65s 0.18s cubic-bezier(.16,1,.3,1), transform 0.65s 0.18s cubic-bezier(.16,1,.3,1); `)}>Sin instalaciones complicadas, sin curvas de aprendizaje interminables.
    Operativo desde el primer día.</p> <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:24px;"><!--[-->`);
    const each_array = ensure_array_like([
      { num: "98%", label: "Uptime garantizado", icon: "⚡" },
      { num: "<2h", label: "Tiempo de onboarding", icon: "🚀" },
      { num: "40+", label: "Módulos activos", icon: "🧩" },
      { num: "100%", label: "Datos en tu control", icon: "🔒" }
    ]);
    for (let i = 0, $$length = each_array.length; i < $$length; i++) {
      let item = each_array[i];
      $$renderer2.push(`<div${attr_style(` background:#ffffff; border:1px solid #e5edf5; border-radius:8px; padding:32px 24px; box-shadow:rgba(50,50,93,0.25) 0px 30px 45px -30px, rgba(0,0,0,0.1) 0px 18px 36px -18px; opacity:${stringify(0)}; transform:translateY(${stringify("24px")}); transition:opacity 0.65s ${stringify(0.22 + i * 0.07)}s cubic-bezier(.16,1,.3,1), transform 0.65s ${stringify(0.22 + i * 0.07)}s cubic-bezier(.16,1,.3,1), box-shadow 0.25s, translate 0.25s; `)} role="article"><div style="font-size:28px; margin-bottom:12px;">${escape_html(item.icon)}</div> <div style="font-size:clamp(2rem,4vw,2.8rem); font-weight:700; color:#003B73; letter-spacing:-0.04em; font-variant-numeric:tabular-nums;">${escape_html(item.num)}</div> <div style="font-size:13px; color:#64748d; margin-top:6px; font-weight:400;">${escape_html(item.label)}</div></div>`);
    }
    $$renderer2.push(`<!--]--></div></div></section>`);
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
    $$renderer2.push(`<section id="features" class="py-28" style="background:#020e1f; border-top:1px solid rgba(255,255,255,0.05);"><div class="relative max-w-6xl mx-auto px-6"><div class="absolute -top-16 left-1/2 -translate-x-1/2 w-[500px] h-[200px] pointer-events-none" style="background:radial-gradient(ellipse, rgba(0,59,115,0.30) 0%, transparent 70%); filter:blur(60px);"></div> <div class="text-center mb-16"><span class="inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 mb-5 text-[11px] font-inter font-semibold tracking-[0.10em] uppercase" style="background:rgba(0,255,159,0.09); border:1px solid rgba(0,255,159,0.25); color:#00FF9F;"><span class="w-1 h-1 rounded-full" style="background:#00FF9F;"></span> ${escape_html(store_get($$store_subs ??= {}, "$t", $format)("features.title"))}</span> <h2 class="font-jakarta font-bold text-[#f0f4ff] mb-4" style="font-size:clamp(1.75rem, 4vw, 2.4rem); letter-spacing:-0.8px;">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("features.subtitle"))}</h2> <p class="font-inter text-[#7a8fa6] max-w-xl mx-auto leading-relaxed text-[15px]">Todo lo que tu empresa necesita, en una sola plataforma.</p></div> <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"><!--[-->`);
    const each_array = ensure_array_like(displayFeatures);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let feature = each_array[$$index];
      $$renderer2.push(`<div role="article" class="rounded-xl p-6 transition-all duration-200 cursor-default" style="background:rgba(255,255,255,0.025); border:1px solid rgba(255,255,255,0.07);"><div class="w-9 h-9 rounded-lg flex items-center justify-center mb-4" style="background:rgba(0,255,159,0.10); border:1px solid rgba(0,255,159,0.18);">`);
      if (feature.icon) {
        $$renderer2.push("<!--[-->");
        {
          $$renderer2.push("<!--[-->");
          const C = feature.icon;
          C($$renderer2, { class: "w-4 h-4", strokeWidth: 1.5, style: "color:#00FF9F;" });
        }
        $$renderer2.push(`<!--]-->`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></div> <h3 class="font-jakarta font-semibold text-[#f0f4ff] mb-2 text-[15px]" style="letter-spacing:-0.2px;">${escape_html(feature.title)}</h3> <p class="font-inter text-[#7a8fa6] text-[13px] leading-relaxed">${escape_html(feature.desc)}</p></div>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="absolute -bottom-16 left-1/2 -translate-x-1/2 w-[600px] h-[180px] pointer-events-none" style="background:radial-gradient(ellipse, rgba(0,59,115,0.18) 0%, transparent 70%); filter:blur(60px);"></div></div></section>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
    bind_props($$props, { features });
  });
}
function HowItWorks($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    const steps = [
      {
        num: "01",
        title: "Crea tu cuenta",
        desc: "Regístrate en minutos. Sin tarjeta, sin contratos. Solo tus datos.",
        color: "rgba(0,59,115,0.08)"
      },
      {
        num: "02",
        title: "Configura tu espacio",
        desc: "Personaliza módulos, usuarios y permisos según tu estructura.",
        color: "rgba(0,255,159,0.06)"
      },
      {
        num: "03",
        title: "Conecta tus sistemas",
        desc: "APIs abiertas para integrarse con lo que ya usas: bancos, facturación, CRM.",
        color: "rgba(0,59,115,0.08)"
      },
      {
        num: "04",
        title: "Opera y crece",
        desc: "Dashboards en tiempo real, reportes automáticos, alertas inteligentes.",
        color: "rgba(0,255,159,0.06)"
      }
    ];
    $$renderer2.push(`<section id="howitworks-section" style="background: #000000; padding: clamp(80px, 10vw, 140px) 24px; position:relative; overflow:hidden;"><div style="position:absolute;top:-120px;left:-80px;width:500px;height:500px;border-radius:50%;background:radial-gradient(circle,rgba(0,59,115,0.3) 0%,transparent 70%);pointer-events:none;"></div> <div style="position:absolute;bottom:-80px;right:-60px;width:400px;height:400px;border-radius:50%;background:radial-gradient(circle,rgba(0,255,159,0.08) 0%,transparent 70%);pointer-events:none;"></div> <div style="max-width:960px; margin:0 auto; position:relative; z-index:1;"><div style="text-align:center; margin-bottom:72px;"><p${attr_style(` font-size:13px; font-weight:600; letter-spacing:0.12em; text-transform:uppercase; color:#00FF9F; margin-bottom:16px; opacity:${stringify(0)}; transform:translateY(${stringify("12px")}); transition:opacity 0.5s cubic-bezier(.16,1,.3,1), transform 0.5s cubic-bezier(.16,1,.3,1); `)}>Cómo funciona</p> <h2${attr_style(` font-family:'Plus Jakarta Sans','Inter',system-ui,sans-serif; font-size:clamp(2rem,5vw,3rem); font-weight:700; letter-spacing:-0.035em; line-height:1.07; color:#f5f5f7; margin:0; opacity:${stringify(0)}; transform:translateY(${stringify("20px")}); transition:opacity 0.6s 0.08s cubic-bezier(.16,1,.3,1), transform 0.6s 0.08s cubic-bezier(.16,1,.3,1); `)}>De cero a operando<br/>en cuatro pasos.</h2></div> <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:2px; background:rgba(255,255,255,0.04); border-radius:12px; overflow:hidden;"><!--[-->`);
    const each_array = ensure_array_like(steps);
    for (let i = 0, $$length = each_array.length; i < $$length; i++) {
      let step = each_array[i];
      $$renderer2.push(`<div${attr_style(` background:#111111; padding:40px 28px; border-right: ${stringify(i < steps.length - 1 ? "1px solid rgba(255,255,255,0.06)" : "none")}; opacity:${stringify(0)}; transform:translateY(${stringify("28px")}); transition:opacity 0.65s ${stringify(0.15 + i * 0.09)}s cubic-bezier(.16,1,.3,1), transform 0.65s ${stringify(0.15 + i * 0.09)}s cubic-bezier(.16,1,.3,1), background 0.2s; `)} role="article"><div style="font-size:11px; font-weight:700; letter-spacing:0.15em; color:#00FF9F; margin-bottom:20px; font-variant-numeric:tabular-nums;">${escape_html(step.num)}</div> <h3 style="font-size:18px; font-weight:600; color:#f5f5f7; margin:0 0 12px; letter-spacing:-0.02em;">${escape_html(step.title)}</h3> <p style="font-size:14px; line-height:1.65; color:rgba(245,245,247,0.55); margin:0; font-weight:300;">${escape_html(step.desc)}</p></div>`);
    }
    $$renderer2.push(`<!--]--></div></div></section>`);
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
      {
        $$renderer2.push("<!--[-->");
        const C = benefit.icon;
        C($$renderer2, { class: "w-5 h-5 text-emerald-400", strokeWidth: 1.5 });
      }
      $$renderer2.push(`<!--]--></div> <h3 class="text-base font-jakarta font-semibold text-white mb-2">${escape_html(benefit.title)}</h3> <p class="text-sm font-inter text-slate-400 leading-relaxed">${escape_html(benefit.desc)}</p></div>`);
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
      {
        $$renderer2.push("<!--[-->");
        const C = benefit.icon;
        C($$renderer2, { class: "w-5 h-5 text-primary", strokeWidth: 1.5 });
      }
      $$renderer2.push(`<!--]--></div> <h3 class="text-base font-jakarta font-semibold text-slate-dark mb-2">${escape_html(benefit.title)}</h3> <p class="text-sm font-inter text-slate leading-relaxed">${escape_html(benefit.desc)}</p></div>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="text-center"><a href="/accountants" class="inline-flex items-center gap-2 bg-primary hover:bg-navy text-white font-jakarta font-semibold text-sm px-6 py-3 rounded-btn shadow-soft hover:shadow-medium transition-all">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("accountants.cta"))} `);
    Arrow_right($$renderer2, { class: "w-4 h-4" });
    $$renderer2.push(`<!----></a></div></div></section>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function Testimonials($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    const testimonials = [
      {
        quote: "SAJET redujo nuestro tiempo de cierre mensual de 3 días a menos de 4 horas. La integración con facturación electrónica fue transparente.",
        name: "María González",
        role: "CFO, TecHeels",
        initials: "MG"
      },
      {
        quote: "El soporte de Jeturing es excepcionalmente rápido. Tuvimos una integración bancaria corriendo en menos de una semana.",
        name: "Carlos Reyes",
        role: "Director TI, AgroLife",
        initials: "CR"
      },
      {
        quote: "Multi-tenancy real, no simulado. Cada cliente tiene su espacio aislado y eso nos dio la confianza para escalar.",
        name: "Laura Méndez",
        role: "CTO, Esecure",
        initials: "LM"
      }
    ];
    $$renderer2.push(`<section id="testimonials-section" style="background:#f5f5f7; padding: clamp(80px,10vw,140px) 24px;"><div style="max-width:1080px; margin:0 auto;"><div style="text-align:center; margin-bottom:72px;"><p${attr_style(` font-size:13px; font-weight:600; letter-spacing:0.12em; text-transform:uppercase; color:#003B73; margin-bottom:16px; opacity:${stringify(0)}; transform:translateY(${stringify("10px")}); transition:opacity 0.5s cubic-bezier(.16,1,.3,1), transform 0.5s cubic-bezier(.16,1,.3,1); `)}>Testimonios</p> <h2${attr_style(` font-family:'Plus Jakarta Sans','Inter',system-ui,sans-serif; font-size:clamp(1.8rem,4.5vw,2.8rem); font-weight:700; letter-spacing:-0.035em; line-height:1.08; color:#061b31; margin:0; opacity:${stringify(0)}; transform:translateY(${stringify("18px")}); transition:opacity 0.6s 0.08s cubic-bezier(.16,1,.3,1), transform 0.6s 0.08s cubic-bezier(.16,1,.3,1); `)}>Lo que dicen nuestros clientes.</h2></div> <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:24px;"><!--[-->`);
    const each_array = ensure_array_like(testimonials);
    for (let i = 0, $$length = each_array.length; i < $$length; i++) {
      let t = each_array[i];
      $$renderer2.push(`<div${attr_style(` background:#ffffff; border:1px solid #e5edf5; border-radius:8px; padding:36px 32px; box-shadow:rgba(50,50,93,0.25) 0px 30px 45px -30px, rgba(0,0,0,0.1) 0px 18px 36px -18px; display:flex; flex-direction:column; justify-content:space-between; opacity:${stringify(0)}; transform:translateY(${stringify("24px")}); transition:opacity 0.65s ${stringify(0.12 + i * 0.1)}s cubic-bezier(.16,1,.3,1), transform 0.65s ${stringify(0.12 + i * 0.1)}s cubic-bezier(.16,1,.3,1), box-shadow 0.25s; `)} role="article"><div style="font-size:48px; color:#003B73; opacity:0.15; line-height:1; margin-bottom:16px; font-family:Georgia,serif;">"</div> <p style="font-size:16px; line-height:1.65; color:#273951; font-weight:300; margin:0 0 32px; flex:1;">${escape_html(t.quote)}</p> <div style="display:flex; align-items:center; gap:12px;"><div style="width:40px; height:40px; border-radius:50%; background:linear-gradient(135deg,#003B73,#00569e); display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:700; color:#00FF9F; flex-shrink:0;">${escape_html(t.initials)}</div> <div><div style="font-size:14px; font-weight:600; color:#061b31;">${escape_html(t.name)}</div> <div style="font-size:12px; color:#64748d; margin-top:1px;">${escape_html(t.role)}</div></div></div></div>`);
    }
    $$renderer2.push(`<!--]--></div></div></section>`);
  });
}
function FAQ($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let open = null;
    const faqs = [
      {
        q: "¿Cuánto tiempo toma implementar SAJET?",
        a: "La mayoría de tenants están operativos en menos de 2 horas. Incluye onboarding asistido, migración de datos básica y configuración inicial de módulos."
      },
      {
        q: "¿Puedo migrar mis datos desde otro ERP?",
        a: "Sí. Ofrecemos conectores para los principales ERPs del mercado y servicio de migración asistida para datos históricos."
      },
      {
        q: "¿Cómo funciona la facturación electrónica?",
        a: "SAJET integra nativamente con los servicios de la DGII (República Dominicana) y otros sistemas fiscales latinoamericanos. El módulo e-CF está incluido en todos los planes."
      },
      {
        q: "¿Mis datos están seguros?",
        a: "Infraestructura propia en servidores dedicados, cifrado AES-256 en reposo y TLS 1.3 en tránsito, backups diarios con retención de 30 días, y aislamiento total por tenant."
      },
      {
        q: "¿Tienen soporte en español?",
        a: "Todo nuestro equipo de soporte opera en español, con horario extendido y SLA de respuesta < 4 horas en planes Professional y Enterprise."
      }
    ];
    $$renderer2.push(`<section id="faq-section" style="background:#000000; padding: clamp(80px,10vw,140px) 24px;"><div style="max-width:720px; margin:0 auto;"><div style="text-align:center; margin-bottom:64px;"><p${attr_style(` font-size:13px; font-weight:600; letter-spacing:0.12em; text-transform:uppercase; color:#00FF9F; margin-bottom:16px; opacity:${stringify(0)}; transform:translateY(${stringify("10px")}); transition:opacity 0.5s cubic-bezier(.16,1,.3,1), transform 0.5s cubic-bezier(.16,1,.3,1); `)}>Preguntas frecuentes</p> <h2${attr_style(` font-family:'Plus Jakarta Sans','Inter',system-ui,sans-serif; font-size:clamp(1.8rem,4.5vw,2.8rem); font-weight:700; letter-spacing:-0.035em; line-height:1.08; color:#f5f5f7; margin:0; opacity:${stringify(0)}; transform:translateY(${stringify("18px")}); transition:opacity 0.6s 0.08s cubic-bezier(.16,1,.3,1), transform 0.6s 0.08s cubic-bezier(.16,1,.3,1); `)}>Todo lo que necesitas saber.</h2></div> <div style="display:flex; flex-direction:column; gap:2px;"><!--[-->`);
    const each_array = ensure_array_like(faqs);
    for (let i = 0, $$length = each_array.length; i < $$length; i++) {
      let faq = each_array[i];
      $$renderer2.push(`<div${attr_style(` border-bottom:1px solid rgba(255,255,255,0.08); opacity:${stringify(0)}; transform:translateY(${stringify("16px")}); transition:opacity 0.6s ${stringify(0.1 + i * 0.07)}s cubic-bezier(.16,1,.3,1), transform 0.6s ${stringify(0.1 + i * 0.07)}s cubic-bezier(.16,1,.3,1); `)}><button style="width:100%; text-align:left; padding:24px 0; background:none; border:none; cursor:pointer; display:flex; justify-content:space-between; align-items:center; gap:16px;"><span${attr_style(`font-size:17px; font-weight:500; color:${stringify(open === i ? "#00FF9F" : "#f5f5f7")}; line-height:1.4; letter-spacing:-0.01em; transition:color 0.2s;`)}>${escape_html(faq.q)}</span> <span${attr_style(` color:${stringify(open === i ? "#00FF9F" : "rgba(245,245,247,0.4)")}; font-size:20px; flex-shrink:0; transform:rotate(${stringify(open === i ? 45 : 0)}deg); transition:transform 0.25s cubic-bezier(.16,1,.3,1), color 0.2s; `)}>+</span></button> `);
      if (open === i) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div style="padding:0 0 24px; font-size:15px; line-height:1.7; color:rgba(245,245,247,0.6); font-weight:300;">${escape_html(faq.a)}</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></div>`);
    }
    $$renderer2.push(`<!--]--></div></div></section>`);
  });
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
    $$renderer2.push(`<section id="pricing" style="background:#f5f5f7; padding:clamp(80px,10vw,140px) 24px;"><div class="max-w-6xl mx-auto px-6"><div class="text-center mb-12"><span style="display:inline-flex;align-items:center;gap:6px;border-radius:4px;background:rgba(0,59,115,0.08);color:#003B73;font-size:12px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;padding:5px 14px;margin-bottom:16px;">${escape_html(
      // Track InitiateCheckout event
      store_get($$store_subs ??= {}, "$t", $format)("pricing.title")
    )}</span> <h2 style="font-family:'Plus Jakarta Sans','Inter',system-ui;font-size:clamp(1.8rem,4.5vw,2.8rem);font-weight:700;letter-spacing:-0.035em;line-height:1.08;color:#061b31;margin:0 0 16px;">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.headline"))}</h2> <p style="font-size:17px;font-weight:300;color:#64748d;max-width:480px;margin:0 auto;">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.subtitle"))}</p></div> <div class="flex flex-col sm:flex-row items-center justify-center gap-6 mb-12"><div style="display:flex;align-items:center;gap:4px;background:#ffffff;border:1px solid #e5edf5;border-radius:8px;padding:4px;box-shadow:rgba(50,50,93,0.12) 0px 4px 12px -4px,rgba(0,0,0,0.06) 0px 2px 6px -2px;"><button${attr_style(`font-size:13px;font-weight:500;padding:6px 16px;border-radius:6px;border:none;cursor:pointer;transition:all 0.2s;background:${stringify("#003B73")};color:${stringify("#ffffff")};`)}>${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.monthly"))}</button> <button${attr_style(`font-size:13px;font-weight:500;padding:6px 16px;border-radius:6px;border:none;cursor:pointer;transition:all 0.2s;background:${stringify("transparent")};color:${stringify("#64748d")};`)}>${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.annual"))} <span style="font-size:11px;color:#00a36e;font-weight:600;margin-left:4px;">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.save"))}</span></button></div> <div style="display:flex;align-items:center;gap:10px;background:#ffffff;border:1px solid #e5edf5;border-radius:8px;padding:8px 16px;box-shadow:rgba(50,50,93,0.12) 0px 4px 12px -4px,rgba(0,0,0,0.06) 0px 2px 6px -2px;"><span style="font-size:13px;color:#64748d;">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.users"))}:</span> <button style="width:28px;height:28px;border-radius:50%;background:#f0f7ff;color:#003B73;font-weight:700;font-size:18px;display:flex;align-items:center;justify-content:center;border:none;cursor:pointer;transition:background 0.2s;"${attr("disabled", userCount <= 1, true)} aria-label="Reducir usuarios">−</button> <span style="width:32px;text-align:center;font-size:14px;font-weight:700;color:#061b31;font-variant-numeric:tabular-nums;">${escape_html(userCount)}</span> <button style="width:28px;height:28px;border-radius:50%;background:#f0f7ff;color:#003B73;font-weight:700;font-size:18px;display:flex;align-items:center;justify-content:center;border:none;cursor:pointer;transition:background 0.2s;" aria-label="Aumentar usuarios">+</button></div></div> <div class="grid grid-cols-1 md:grid-cols-3 gap-6 items-start"><!--[-->`);
    const each_array = ensure_array_like(displayPlans);
    for (let $$index_2 = 0, $$length = each_array.length; $$index_2 < $$length; $$index_2++) {
      let plan = each_array[$$index_2];
      $$renderer2.push(`<div${attr_style(` position:relative; border-radius:8px; background:#ffffff; border:${stringify(plan.is_highlighted ? "2px solid #003B73" : "1px solid #e5edf5")}; padding:${stringify(plan.is_highlighted ? "28px 28px" : "24px 24px")}; display:flex; flex-direction:column; box-shadow:${stringify(plan.is_highlighted ? "rgba(50,50,93,0.35) 0px 30px 60px -12px, rgba(0,0,0,0.2) 0px 18px 36px -18px" : "rgba(50,50,93,0.18) 0px 20px 40px -20px, rgba(0,0,0,0.08) 0px 10px 24px -12px")}; transform:${stringify(plan.is_highlighted ? "translateY(-4px)" : "none")}; `)}>`);
      if (plan.is_highlighted) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%);"><span style="display:inline-flex;align-items:center;gap:4px;background:#003B73;color:#00FF9F;font-size:11px;font-weight:600;padding:4px 12px;border-radius:4px;letter-spacing:0.04em;text-transform:uppercase;">`);
        Sparkles($$renderer2, { class: "w-3 h-3" });
        $$renderer2.push(`<!----> ${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.most_popular"))}</span></div>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> <h3 style="font-size:16px;font-weight:700;color:#061b31;margin:0 0 4px;letter-spacing:-0.02em;">${escape_html(plan.display_name || plan.name)}</h3> <div style="display:flex;align-items:baseline;gap:4px;margin-bottom:8px;">`);
      if (pricingLoading) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<span style="font-size:2rem;font-weight:700;color:#64748d;">…</span>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<span style="font-size:2.5rem;font-weight:800;color:#061b31;letter-spacing:-0.04em;font-variant-numeric:tabular-nums;">${escape_html(displayTotal(plan))}</span> <span style="font-size:13px;color:#64748d;">/mes</span>`);
      }
      $$renderer2.push(`<!--]--></div> <div style="font-size:11px;color:#64748d;margin-bottom:12px;background:#f8fafc;border-radius:6px;padding:10px 12px;line-height:1.8;border:1px solid #e5edf5;"><p style="font-weight:600;color:#273951;margin:0;">Base: $${escape_html(plan.base_price)}/mes</p> <p style="margin:0;">+$${escape_html(plan.price_per_user)}/usuario adicional</p> <p style="margin:0;color:#94a3b8;">${escape_html(plan.included_users)} usuario${escape_html(plan.included_users > 1 ? "s" : "")} incluido${escape_html(plan.included_users > 1 ? "s" : "")} · Hasta ${escape_html(maxUsersLabel(plan))}</p> `);
      if (!pricingLoading && extraUsersLine(plan)) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<p style="color:#003B73;font-weight:500;margin:4px 0 0;padding-top:4px;border-top:1px solid #e5edf5;">${escape_html(extraUsersLine(plan))}</p>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></div> <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px;"><!--[-->`);
      const each_array_1 = ensure_array_like([
        `💾 ${storageLabel(plan.max_storage_mb)}`,
        "🔒 Backups ∞",
        `⚡ ${apiLabel(plan)}`,
        `💬 ${supportLabel(plan)}`
      ]);
      for (let $$index = 0, $$length2 = each_array_1.length; $$index < $$length2; $$index++) {
        let chip = each_array_1[$$index];
        $$renderer2.push(`<span style="font-size:11px;font-weight:500;background:#f0f7ff;color:#273951;border-radius:4px;padding:3px 8px;border:1px solid #e5edf5;">${escape_html(chip)}</span>`);
      }
      $$renderer2.push(`<!--]--></div> <p class="text-xs font-inter text-primary font-semibold mb-4">✓ ${escape_html(plan.trial_days)} días de prueba gratis · Sin tarjeta</p> <ul class="space-y-2.5 mb-6 flex-1"><!--[-->`);
      const each_array_2 = ensure_array_like(plan.features || []);
      for (let $$index_1 = 0, $$length2 = each_array_2.length; $$index_1 < $$length2; $$index_1++) {
        let feat = each_array_2[$$index_1];
        $$renderer2.push(`<li class="flex items-start gap-2 text-sm font-inter text-slate-dark">`);
        Check($$renderer2, {
          class: "w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5",
          strokeWidth: 2.5
        });
        $$renderer2.push(`<!----> <span>${escape_html(feat)}</span></li>`);
      }
      $$renderer2.push(`<!--]--></ul> <button${attr_style(` width:100%; text-align:center; font-size:14px; font-weight:600; padding:12px 24px; border-radius:6px; cursor:pointer; transition:all 0.2s; margin-top:auto; background:${stringify(plan.is_highlighted ? "#003B73" : "transparent")}; color:${stringify(plan.is_highlighted ? "#00FF9F" : "#003B73")}; border:${stringify(plan.is_highlighted ? "none" : "2px solid #003B73")}; box-shadow:${stringify(plan.is_highlighted ? "rgba(50,50,93,0.25) 0px 6px 16px -4px" : "none")}; `)}>${escape_html(store_get($$store_subs ??= {}, "$t", $format)("pricing.start_trial"))}</button></div>`);
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
    $$renderer2.push(`<section id="cta-final" class="py-28 relative overflow-hidden" style="background:#020e1f; border-top:1px solid rgba(255,255,255,0.05);"><div class="absolute top-0 left-1/2 -translate-x-1/2 pointer-events-none" style="width:700px; height:300px; background:radial-gradient(ellipse at 50% 0%, rgba(0,255,159,0.12) 0%, transparent 65%); filter:blur(50px);"></div> <div class="absolute bottom-0 left-1/2 -translate-x-1/2 pointer-events-none" style="width:500px; height:200px; background:radial-gradient(ellipse, rgba(0,59,115,0.35) 0%, transparent 70%); filter:blur(60px);"></div> <div class="relative max-w-2xl mx-auto px-6 text-center"><div class="inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 mb-8 text-[11px] font-inter font-semibold tracking-[0.10em] uppercase" style="background:rgba(0,255,159,0.09); border:1px solid rgba(0,255,159,0.28); color:#00FF9F;"><span class="w-1.5 h-1.5 rounded-full" style="background:#00FF9F; box-shadow:0 0 6px #00FF9F;"></span> Empieza hoy</div> <h2 class="font-jakarta font-extrabold text-[#f0f4ff] mb-5 leading-[1.08]" style="font-size:clamp(2rem, 5vw, 3.2rem); letter-spacing:-1.4px;">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("final_cta.headline"))}<br/> <span style="color:#00FF9F; text-shadow:0 0 32px rgba(0,255,159,0.30);">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("final_cta.headline_highlight"))}</span></h2> <p class="font-inter text-[#7a8fa6] mb-10 max-w-lg mx-auto leading-relaxed text-[16px]">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("final_cta.subheading"))}</p> <div class="flex flex-col sm:flex-row items-center justify-center gap-3"><a href="/signup" class="inline-flex items-center gap-2 font-inter font-semibold text-[14px] px-8 py-3.5 rounded-lg transition-all duration-150 hover:-translate-y-px w-full sm:w-auto justify-center" style="background:#00FF9F; color:#020e1f; box-shadow:0 4px 20px rgba(0,255,159,0.30);">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("final_cta.cta_primary"))} `);
    Arrow_right($$renderer2, { class: "w-4 h-4" });
    $$renderer2.push(`<!----></a> <a href="mailto:ventas@sajet.us?subject=Quiero%20hablar%20con%20SAJET" class="inline-flex items-center gap-2 font-inter font-medium text-[14px] text-[#c8d3e8] px-8 py-3.5 rounded-lg transition-all hover:-translate-y-px w-full sm:w-auto justify-center" style="border:1px solid rgba(255,255,255,0.12); background:rgba(255,255,255,0.04);">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("final_cta.cta_secondary"))}</a></div> <p class="text-[11px] font-inter text-[#4a6080] mt-8">Sin tarjeta de crédito · 14 días gratis · Cancela cuando quieras</p></div></section>`);
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
    Testimonials($$renderer2);
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
