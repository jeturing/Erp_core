import "clsx";
import { h as sanitize_props, i as spread_props, j as slot, s as store_get, d as escape_html, c as attr, e as ensure_array_like, a as attr_style, b as stringify, k as attr_class, l as clsx, u as unsubscribe_stores } from "../../../../chunks/index2.js";
import { o as onDestroy } from "../../../../chunks/index-server.js";
import { d as dashboard, a as auth } from "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { f as formatCurrency, a as formatDate } from "../../../../chunks/formatters.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
import { I as Icon } from "../../../../chunks/Icon.js";
import { D as Dollar_sign } from "../../../../chunks/dollar-sign.js";
import { U as Users } from "../../../../chunks/users.js";
import { Z as Zap } from "../../../../chunks/zap.js";
import { T as Target } from "../../../../chunks/target.js";
import { S as Server } from "../../../../chunks/server.js";
import { C as Clipboard_list, G as Git_compare_arrows } from "../../../../chunks/git-compare-arrows.js";
import { A as Activity } from "../../../../chunks/activity.js";
import { C as Circle_check } from "../../../../chunks/circle-check.js";
import { T as Triangle_alert } from "../../../../chunks/triangle-alert.js";
function Circle_alert($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["circle", { "cx": "12", "cy": "12", "r": "10" }],
    ["line", { "x1": "12", "x2": "12", "y1": "8", "y2": "12" }],
    [
      "line",
      { "x1": "12", "x2": "12.01", "y1": "16", "y2": "16" }
    ]
  ];
  Icon($$renderer, spread_props([
    { name: "circle-alert" },
    $$sanitized_props,
    {
      /**
       * @component @name CircleAlert
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCIgLz4KICA8bGluZSB4MT0iMTIiIHgyPSIxMiIgeTE9IjgiIHkyPSIxMiIgLz4KICA8bGluZSB4MT0iMTIiIHgyPSIxMi4wMSIgeTE9IjE2IiB5Mj0iMTYiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/circle-alert
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
function Circle_x($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["circle", { "cx": "12", "cy": "12", "r": "10" }],
    ["path", { "d": "m15 9-6 6" }],
    ["path", { "d": "m9 9 6 6" }]
  ];
  Icon($$renderer, spread_props([
    { name: "circle-x" },
    $$sanitized_props,
    {
      /**
       * @component @name CircleX
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCIgLz4KICA8cGF0aCBkPSJtMTUgOS02IDYiIC8+CiAgPHBhdGggZD0ibTkgOSA2IDYiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/circle-x
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
function Cpu($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["path", { "d": "M12 20v2" }],
    ["path", { "d": "M12 2v2" }],
    ["path", { "d": "M17 20v2" }],
    ["path", { "d": "M17 2v2" }],
    ["path", { "d": "M2 12h2" }],
    ["path", { "d": "M2 17h2" }],
    ["path", { "d": "M2 7h2" }],
    ["path", { "d": "M20 12h2" }],
    ["path", { "d": "M20 17h2" }],
    ["path", { "d": "M20 7h2" }],
    ["path", { "d": "M7 20v2" }],
    ["path", { "d": "M7 2v2" }],
    [
      "rect",
      { "x": "4", "y": "4", "width": "16", "height": "16", "rx": "2" }
    ],
    [
      "rect",
      { "x": "8", "y": "8", "width": "8", "height": "8", "rx": "1" }
    ]
  ];
  Icon($$renderer, spread_props([
    { name: "cpu" },
    $$sanitized_props,
    {
      /**
       * @component @name Cpu
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMTIgMjB2MiIgLz4KICA8cGF0aCBkPSJNMTIgMnYyIiAvPgogIDxwYXRoIGQ9Ik0xNyAyMHYyIiAvPgogIDxwYXRoIGQ9Ik0xNyAydjIiIC8+CiAgPHBhdGggZD0iTTIgMTJoMiIgLz4KICA8cGF0aCBkPSJNMiAxN2gyIiAvPgogIDxwYXRoIGQ9Ik0yIDdoMiIgLz4KICA8cGF0aCBkPSJNMjAgMTJoMiIgLz4KICA8cGF0aCBkPSJNMjAgMTdoMiIgLz4KICA8cGF0aCBkPSJNMjAgN2gyIiAvPgogIDxwYXRoIGQ9Ik03IDIwdjIiIC8+CiAgPHBhdGggZD0iTTcgMnYyIiAvPgogIDxyZWN0IHg9IjQiIHk9IjQiIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgcng9IjIiIC8+CiAgPHJlY3QgeD0iOCIgeT0iOCIgd2lkdGg9IjgiIGhlaWdodD0iOCIgcng9IjEiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/cpu
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
function Hard_drive($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["line", { "x1": "22", "x2": "2", "y1": "12", "y2": "12" }],
    [
      "path",
      {
        "d": "M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"
      }
    ],
    ["line", { "x1": "6", "x2": "6.01", "y1": "16", "y2": "16" }],
    [
      "line",
      { "x1": "10", "x2": "10.01", "y1": "16", "y2": "16" }
    ]
  ];
  Icon($$renderer, spread_props([
    { name: "hard-drive" },
    $$sanitized_props,
    {
      /**
       * @component @name HardDrive
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8bGluZSB4MT0iMjIiIHgyPSIyIiB5MT0iMTIiIHkyPSIxMiIgLz4KICA8cGF0aCBkPSJNNS40NSA1LjExIDIgMTJ2NmEyIDIgMCAwIDAgMiAyaDE2YTIgMiAwIDAgMCAyLTJ2LTZsLTMuNDUtNi44OUEyIDIgMCAwIDAgMTYuNzYgNEg3LjI0YTIgMiAwIDAgMC0xLjc5IDEuMTF6IiAvPgogIDxsaW5lIHgxPSI2IiB4Mj0iNi4wMSIgeTE9IjE2IiB5Mj0iMTYiIC8+CiAgPGxpbmUgeDE9IjEwIiB4Mj0iMTAuMDEiIHkxPSIxNiIgeTI9IjE2IiAvPgo8L3N2Zz4K) - https://lucide.dev/icons/hard-drive
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
function Memory_stick($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["path", { "d": "M12 12v-2" }],
    ["path", { "d": "M12 18v-2" }],
    ["path", { "d": "M16 12v-2" }],
    ["path", { "d": "M16 18v-2" }],
    ["path", { "d": "M2 11h1.5" }],
    ["path", { "d": "M20 18v-2" }],
    ["path", { "d": "M20.5 11H22" }],
    ["path", { "d": "M4 18v-2" }],
    ["path", { "d": "M8 12v-2" }],
    ["path", { "d": "M8 18v-2" }],
    [
      "rect",
      { "x": "2", "y": "6", "width": "20", "height": "10", "rx": "2" }
    ]
  ];
  Icon($$renderer, spread_props([
    { name: "memory-stick" },
    $$sanitized_props,
    {
      /**
       * @component @name MemoryStick
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMTIgMTJ2LTIiIC8+CiAgPHBhdGggZD0iTTEyIDE4di0yIiAvPgogIDxwYXRoIGQ9Ik0xNiAxMnYtMiIgLz4KICA8cGF0aCBkPSJNMTYgMTh2LTIiIC8+CiAgPHBhdGggZD0iTTIgMTFoMS41IiAvPgogIDxwYXRoIGQ9Ik0yMCAxOHYtMiIgLz4KICA8cGF0aCBkPSJNMjAuNSAxMUgyMiIgLz4KICA8cGF0aCBkPSJNNCAxOHYtMiIgLz4KICA8cGF0aCBkPSJNOCAxMnYtMiIgLz4KICA8cGF0aCBkPSJNOCAxOHYtMiIgLz4KICA8cmVjdCB4PSIyIiB5PSI2IiB3aWR0aD0iMjAiIGhlaWdodD0iMTAiIHJ4PSIyIiAvPgo8L3N2Zz4K) - https://lucide.dev/icons/memory-stick
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
function Trending_up($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["path", { "d": "M16 7h6v6" }],
    ["path", { "d": "m22 7-8.5 8.5-5-5L2 17" }]
  ];
  Icon($$renderer, spread_props([
    { name: "trending-up" },
    $$sanitized_props,
    {
      /**
       * @component @name TrendingUp
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMTYgN2g2djYiIC8+CiAgPHBhdGggZD0ibTIyIDctOC41IDguNS01LTVMMiAxNyIgLz4KPC9zdmc+Cg==) - https://lucide.dev/icons/trending-up
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
function Dashboard($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let rawReport, report;
    onDestroy(() => dashboard.stopAutoRefresh());
    function statusIcon(s) {
      if (s === "ok") return { icon: Circle_check, color: "text-success" };
      if (s === "warning") return { icon: Triangle_alert, color: "text-warning" };
      return { icon: Circle_x, color: "text-error" };
    }
    function statusBadge(status) {
      if (status === "active") return "badge-success";
      if (status === "provisioning" || status === "pending") return "badge-warning";
      if (status === "suspended" || status === "payment_failed") return "badge-error";
      return "badge-neutral";
    }
    const planColors = { basic: "#6B7280", pro: "#C05A3C", enterprise: "#1a1a1a" };
    rawReport = store_get($$store_subs ??= {}, "$dashboard", dashboard).report;
    report = rawReport ? {
      ...rawReport,
      system_health: rawReport.system_health ?? [],
      recent_activity: rawReport.recent_activity ?? [],
      recent_stripe_events: rawReport.recent_stripe_events ?? [],
      revenue: rawReport.revenue ?? {
        mrr: 0,
        arr: 0,
        pending_amount: 0,
        pending_count: 0,
        churn_rate: 0,
        total_users: 0,
        plan_distribution: {},
        new_this_month: 0,
        cancelled_30d: 0
      },
      customers: rawReport.customers ?? { total: 0, active: 0, suspended: 0, active_subscriptions: 0 },
      partners: {
        ...rawReport.partners ?? { total: 0, active: 0, pending: 0, top: [] },
        top: rawReport.partners?.top ?? []
      },
      leads: {
        ...rawReport.leads ?? { total: 0, active: 0, won: 0, pipeline_value: 0, pipeline: {} },
        pipeline: rawReport.leads?.pipeline ?? {}
      },
      commissions: rawReport.commissions ?? { total_partner: 0, pending: 0, paid: 0, jeturing_share: 0 },
      infrastructure: rawReport.infrastructure ?? {
        nodes_total: 0,
        nodes_online: 0,
        containers_total: 0,
        containers_running: 0,
        cpu: { used: 0, total: 0, percent: 0 },
        ram: { used: 0, total: 0, percent: 0 },
        disk: { used: 0, total: 0, percent: 0 }
      },
      settlements: rawReport.settlements ?? { open: 0, closed: 0, total_partner_payout: 0 },
      work_orders: rawReport.work_orders ?? { total: 0, requested: 0, in_progress: 0, completed: 0 },
      reconciliation: rawReport.reconciliation ?? { total_runs: 0, clean: 0, issues: 0 },
      invoices: rawReport.invoices ?? {
        total: 0,
        paid: 0,
        pending: 0,
        total_amount: 0,
        paid_amount: 0
      }
    } : null;
    $$renderer2.push(`<div class="p-6 lg:p-10 space-y-6"><div class="flex items-start justify-between"><div><h1 class="page-title">DASHBOARD</h1> <p class="page-subtitle">Bienvenido, ${escape_html(store_get($$store_subs ??= {}, "$auth", auth).user?.username || "Admin")} · ${escape_html((/* @__PURE__ */ new Date()).toLocaleDateString("es-ES", { day: "2-digit", month: "long", year: "numeric" }))} `);
    if (store_get($$store_subs ??= {}, "$dashboard", dashboard).lastUpdated) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<span class="text-[10px] text-gray-400 ml-2">Actualizado ${escape_html(store_get($$store_subs ??= {}, "$dashboard", dashboard).lastUpdated.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" }))}</span>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></p></div> <button class="btn-accent btn-sm flex items-center gap-2"${attr("disabled", store_get($$store_subs ??= {}, "$dashboard", dashboard).isLoading, true)}>`);
    Refresh_cw($$renderer2, {
      size: 14,
      class: store_get($$store_subs ??= {}, "$dashboard", dashboard).isLoading ? "animate-spin" : ""
    });
    $$renderer2.push(`<!----> Actualizar</button></div> `);
    if (store_get($$store_subs ??= {}, "$dashboard", dashboard).isLoading && !report) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="flex items-center justify-center py-20"><div class="w-8 h-8 border-2 border-terracotta border-t-transparent rounded-full animate-spin"></div></div>`);
    } else if (store_get($$store_subs ??= {}, "$dashboard", dashboard).error) {
      $$renderer2.push("<!--[1-->");
      $$renderer2.push(`<div class="card flex items-center gap-3 text-error">`);
      Circle_alert($$renderer2, { size: 20 });
      $$renderer2.push(`<!----> <span class="font-body text-sm">${escape_html(store_get($$store_subs ??= {}, "$dashboard", dashboard).error)}</span> <button class="btn-secondary btn-sm ml-auto">Reintentar</button></div>`);
    } else if (report) {
      $$renderer2.push("<!--[2-->");
      $$renderer2.push(`<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4"><div class="stat-card"><span class="stat-label flex items-center gap-1">`);
      Dollar_sign($$renderer2, { size: 12 });
      $$renderer2.push(`<!----> MRR</span> <span class="stat-value">${escape_html(formatCurrency(report.revenue.mrr))}</span> <span class="text-[10px] text-gray-400">ARR ${escape_html(formatCurrency(report.revenue.arr))}</span></div> <div class="stat-card"><span class="stat-label flex items-center gap-1">`);
      Users($$renderer2, { size: 12 });
      $$renderer2.push(`<!----> Clientes activos</span> <span class="stat-value">${escape_html(report.customers.active)}</span> <span class="text-[10px] text-gray-400">${escape_html(report.customers.total)} total · ${escape_html(report.revenue.total_users)} users</span></div> <div class="stat-card"><span class="stat-label flex items-center gap-1">`);
      Trending_up($$renderer2, { size: 12 });
      $$renderer2.push(`<!----> Nuevos este mes</span> <span class="stat-value text-success">${escape_html(report.revenue.new_this_month)}</span> <span class="text-[10px] text-gray-400">Churn ${escape_html(report.revenue.churn_rate)}% (${escape_html(report.revenue.cancelled_30d)} cancel)</span></div> <div class="stat-card"><span class="stat-label flex items-center gap-1">`);
      Zap($$renderer2, { size: 12 });
      $$renderer2.push(`<!----> Pendiente cobro</span> <span class="stat-value text-warning">${escape_html(formatCurrency(report.revenue.pending_amount))}</span> <span class="text-[10px] text-gray-400">${escape_html(report.revenue.pending_count)} suscripciones</span></div> <div class="stat-card"><span class="stat-label flex items-center gap-1">`);
      Target($$renderer2, { size: 12 });
      $$renderer2.push(`<!----> Pipeline valor</span> <span class="stat-value">${escape_html(formatCurrency(report.leads.pipeline_value))}</span> <span class="text-[10px] text-gray-400">${escape_html(report.leads.active)} leads activos</span></div></div> <div class="grid grid-cols-1 lg:grid-cols-3 gap-6"><div class="card p-0"><div class="px-6 py-4 border-b border-border-light"><span class="section-heading">Distribución por Plan</span></div> <div class="p-6 space-y-4">`);
      const each_array = ensure_array_like(Object.entries(report.revenue?.plan_distribution || {}));
      if (each_array.length !== 0) {
        $$renderer2.push("<!--[-->");
        for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
          let [plan, data] = each_array[$$index];
          $$renderer2.push(`<div><div class="flex justify-between mb-1.5"><span class="text-sm font-semibold font-sans capitalize">${escape_html(plan)}</span> <span class="text-sm font-body">${escape_html(data.count)} subs · ${escape_html(formatCurrency(data.revenue))}/mo</span></div> <div class="h-2 bg-border-light rounded-full overflow-hidden"><div class="h-full rounded-full transition-all"${attr_style(`width: ${stringify(report.customers.active_subscriptions ? Math.round(data.count / report.customers.active_subscriptions * 100) : 0)}%; background-color: ${stringify(planColors[plan] || "#999")}`)}></div></div> <span class="text-[10px] text-gray-400">${escape_html(data.users)} usuarios</span></div>`);
        }
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<p class="text-sm text-gray-400 text-center py-4">Sin suscripciones</p>`);
      }
      $$renderer2.push(`<!--]--></div></div> <div class="card p-0"><div class="px-6 py-4 border-b border-border-light flex items-center justify-between"><span class="section-heading">Partners &amp; Pipeline</span> <a href="/partners" class="text-[11px] uppercase tracking-widest text-gray-500 hover:text-terracotta font-sans">Ver →</a></div> <div class="divide-y divide-border-light"><div class="grid grid-cols-2 gap-4 px-6 py-4"><div><div class="text-[11px] uppercase tracking-widest text-gray-500 font-sans mb-1">Partners</div> <div class="text-2xl font-bold font-sans">${escape_html(report.partners.active)}</div> <div class="text-[10px] text-gray-400">${escape_html(report.partners.pending)} pendientes</div></div> <div><div class="text-[11px] uppercase tracking-widest text-gray-500 font-sans mb-1">Leads</div> <div class="text-2xl font-bold font-sans">${escape_html(report.leads.total)}</div> <div class="text-[10px] text-gray-400">${escape_html(report.leads.won)} ganados</div></div></div> `);
      if ((report.partners?.top || []).length > 0) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="px-6 py-3"><div class="text-[10px] uppercase tracking-widest text-gray-400 font-sans mb-2">Top Partners</div> <!--[-->`);
        const each_array_1 = ensure_array_like((report.partners?.top || []).slice(0, 3));
        for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
          let p = each_array_1[$$index_1];
          $$renderer2.push(`<div class="flex justify-between items-center py-1.5"><span class="text-sm font-body text-text-primary truncate">${escape_html(p.company_name)}</span> <span class="text-sm font-semibold font-sans">${escape_html(formatCurrency(p.total_revenue))}</span></div>`);
        }
        $$renderer2.push(`<!--]--></div>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> <div class="px-6 py-3"><div class="text-[10px] uppercase tracking-widest text-gray-400 font-sans mb-2">Pipeline</div> <div class="flex gap-1.5 flex-wrap"><!--[-->`);
      const each_array_2 = ensure_array_like(Object.entries(report.leads?.pipeline || {}));
      for (let $$index_2 = 0, $$length = each_array_2.length; $$index_2 < $$length; $$index_2++) {
        let [status, count] = each_array_2[$$index_2];
        $$renderer2.push(`<span class="badge-neutral text-[9px]">${escape_html(status)}: ${escape_html(count)}</span>`);
      }
      $$renderer2.push(`<!--]--></div></div></div></div> <div class="card p-0"><div class="px-6 py-4 border-b border-border-light flex items-center justify-between"><span class="section-heading">Financiero</span> <a href="/commissions" class="text-[11px] uppercase tracking-widest text-gray-500 hover:text-terracotta font-sans">Ver →</a></div> <div class="divide-y divide-border-light"><div class="grid grid-cols-2 gap-4 px-6 py-4"><div><div class="text-[11px] uppercase tracking-widest text-gray-500 font-sans mb-1">Comisiones Partner</div> <div class="text-2xl font-bold font-sans">${escape_html(formatCurrency(report.commissions.total_partner))}</div> <div class="text-[10px] text-gray-400">${escape_html(formatCurrency(report.commissions.pending))} pendiente</div></div> <div><div class="text-[11px] uppercase tracking-widest text-gray-500 font-sans mb-1">Revenue Jeturing</div> <div class="text-2xl font-bold font-sans">${escape_html(formatCurrency(report.commissions.jeturing_share))}</div> <div class="text-[10px] text-gray-400">${escape_html(formatCurrency(report.commissions.paid))} pagado</div></div></div> <div class="grid grid-cols-3 gap-2 px-6 py-3 text-center"><div><div class="text-[10px] uppercase tracking-widest text-gray-400 font-sans">Settlements</div> <div class="font-bold text-lg font-sans">${escape_html(report.settlements.open + report.settlements.closed)}</div> <div class="text-[10px] text-gray-400">${escape_html(report.settlements.open)} abiertos</div></div> <div><div class="text-[10px] uppercase tracking-widest text-gray-400 font-sans">Facturas</div> <div class="font-bold text-lg font-sans">${escape_html(report.invoices.total)}</div> <div class="text-[10px] text-gray-400">${escape_html(report.invoices.pending)} pendientes</div></div> <div><div class="text-[10px] uppercase tracking-widest text-gray-400 font-sans">Payout Total</div> <div class="font-bold text-lg font-sans">${escape_html(formatCurrency(report.settlements.total_partner_payout))}</div></div></div></div></div></div> <div class="grid grid-cols-1 lg:grid-cols-3 gap-6"><div class="card p-0"><div class="px-6 py-4 border-b border-border-light flex items-center justify-between"><span class="section-heading flex items-center gap-2">`);
      Server($$renderer2, { size: 16 });
      $$renderer2.push(`<!----> Infraestructura</span> <a href="/infrastructure" class="text-[11px] uppercase tracking-widest text-gray-500 hover:text-terracotta font-sans">Ver →</a></div> <div class="p-6 space-y-4"><div class="grid grid-cols-2 gap-4 text-center"><div><div class="text-2xl font-bold font-sans">${escape_html(report.infrastructure.nodes_online)}/${escape_html(report.infrastructure.nodes_total)}</div> <div class="text-[10px] uppercase tracking-widest text-gray-500">Nodos online</div></div> <div><div class="text-2xl font-bold font-sans">${escape_html(report.infrastructure.containers_running)}/${escape_html(report.infrastructure.containers_total)}</div> <div class="text-[10px] uppercase tracking-widest text-gray-500">Containers</div></div></div> <div><div class="flex justify-between mb-1"><span class="text-[11px] uppercase tracking-widest text-gray-500 font-sans flex items-center gap-1">`);
      Cpu($$renderer2, { size: 12 });
      $$renderer2.push(`<!----> CPU</span> <span class="text-[11px] font-semibold text-text-primary font-sans">${escape_html(report.infrastructure.cpu.percent)}%</span></div> <div class="h-1.5 bg-border-light rounded-full overflow-hidden"><div class="h-full bg-charcoal rounded-full transition-all"${attr_style(`width:${stringify(Math.min(100, report.infrastructure.cpu.percent))}%`)}></div></div></div> <div><div class="flex justify-between mb-1"><span class="text-[11px] uppercase tracking-widest text-gray-500 font-sans flex items-center gap-1">`);
      Memory_stick($$renderer2, { size: 12 });
      $$renderer2.push(`<!----> RAM</span> <span class="text-[11px] font-semibold text-text-primary font-sans">${escape_html(report.infrastructure.ram.percent)}%</span></div> <div class="h-1.5 bg-border-light rounded-full overflow-hidden"><div class="h-full bg-terracotta rounded-full transition-all"${attr_style(`width:${stringify(Math.min(100, report.infrastructure.ram.percent))}%`)}></div></div></div> <div><div class="flex justify-between mb-1"><span class="text-[11px] uppercase tracking-widest text-gray-500 font-sans flex items-center gap-1">`);
      Hard_drive($$renderer2, { size: 12 });
      $$renderer2.push(`<!----> Disco</span> <span class="text-[11px] font-semibold text-text-primary font-sans">${escape_html(report.infrastructure.disk.percent)}%</span></div> <div class="h-1.5 bg-border-light rounded-full overflow-hidden"><div${attr_class(`h-full rounded-full transition-all ${stringify(report.infrastructure.disk.percent > 85 ? "bg-error" : "bg-charcoal")}`)}${attr_style(`width:${stringify(Math.min(100, report.infrastructure.disk.percent))}%`)}></div></div></div></div></div> <div class="card p-0"><div class="px-6 py-4 border-b border-border-light flex items-center justify-between"><span class="section-heading flex items-center gap-2">`);
      Clipboard_list($$renderer2, { size: 16 });
      $$renderer2.push(`<!----> Operaciones</span> <a href="/workorders" class="text-[11px] uppercase tracking-widest text-gray-500 hover:text-terracotta font-sans">Ver →</a></div> <div class="divide-y divide-border-light"><div class="grid grid-cols-4 gap-2 px-6 py-4 text-center"><div><div class="font-bold text-lg font-sans">${escape_html(report.work_orders.total)}</div> <div class="text-[9px] uppercase tracking-widest text-gray-500">Total</div></div> <div><div class="font-bold text-lg font-sans text-warning">${escape_html(report.work_orders.requested)}</div> <div class="text-[9px] uppercase tracking-widest text-gray-500">Pedidas</div></div> <div><div class="font-bold text-lg font-sans text-info">${escape_html(report.work_orders.in_progress)}</div> <div class="text-[9px] uppercase tracking-widest text-gray-500">En curso</div></div> <div><div class="font-bold text-lg font-sans text-success">${escape_html(report.work_orders.completed)}</div> <div class="text-[9px] uppercase tracking-widest text-gray-500">Listas</div></div></div> <div class="px-6 py-4"><div class="flex items-center gap-2 mb-3">`);
      Git_compare_arrows($$renderer2, { size: 16 });
      $$renderer2.push(`<!----> <span class="text-sm font-semibold font-sans">Conciliación Stripe ↔ DB</span></div> <div class="grid grid-cols-3 gap-2 text-center"><div><div class="font-bold text-lg font-sans">${escape_html(report.reconciliation.total_runs)}</div> <div class="text-[9px] uppercase tracking-widest text-gray-500">Corridas</div></div> <div><div class="font-bold text-lg font-sans text-success">${escape_html(report.reconciliation.clean)}</div> <div class="text-[9px] uppercase tracking-widest text-gray-500">OK</div></div> <div><div class="font-bold text-lg font-sans text-error">${escape_html(report.reconciliation.issues)}</div> <div class="text-[9px] uppercase tracking-widest text-gray-500">Issues</div></div></div></div></div></div> <div class="card p-0"><div class="px-6 py-4 border-b border-border-light flex items-center justify-between"><span class="section-heading flex items-center gap-2">`);
      Activity($$renderer2, { size: 16 });
      $$renderer2.push(`<!----> Estado del Sistema</span> <a href="/logs" class="text-[11px] uppercase tracking-widest text-gray-500 hover:text-terracotta font-sans">Logs →</a></div> <div class="divide-y divide-border-light"><!--[-->`);
      const each_array_3 = ensure_array_like(report.system_health || []);
      for (let $$index_3 = 0, $$length = each_array_3.length; $$index_3 < $$length; $$index_3++) {
        let item = each_array_3[$$index_3];
        const si = statusIcon(item.status);
        $$renderer2.push(`<div class="flex items-center justify-between px-6 py-3"><span class="text-sm font-body text-text-secondary">${escape_html(item.name)}</span> <div class="flex items-center gap-2">`);
        if (si.icon) {
          $$renderer2.push("<!--[-->");
          si.icon($$renderer2, { size: 14, class: si.color });
          $$renderer2.push("<!--]-->");
        } else {
          $$renderer2.push("<!--[!-->");
          $$renderer2.push("<!--]-->");
        }
        $$renderer2.push(` <span${attr_class(`text-[11px] font-semibold uppercase tracking-widest ${stringify(si.color)} font-sans`)}>${escape_html(item.detail)}</span></div></div>`);
      }
      $$renderer2.push(`<!--]--></div> `);
      if ((report.recent_stripe_events || []).length > 0) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="px-6 py-3 border-t border-border-light"><div class="text-[10px] uppercase tracking-widest text-gray-400 font-sans mb-2">Últimos eventos Stripe</div> <!--[-->`);
        const each_array_4 = ensure_array_like((report.recent_stripe_events || []).slice(0, 4));
        for (let $$index_4 = 0, $$length = each_array_4.length; $$index_4 < $$length; $$index_4++) {
          let evt = each_array_4[$$index_4];
          $$renderer2.push(`<div class="flex justify-between py-1"><span class="text-[11px] font-mono text-gray-500 truncate">${escape_html(evt.event_type)}</span> <span class="text-[10px] text-gray-400">${escape_html(evt.processed ? "✓" : "⏳")}</span></div>`);
        }
        $$renderer2.push(`<!--]--></div>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></div></div> <div class="card p-0"><div class="flex items-center justify-between px-6 py-4 border-b border-border-light"><span class="section-heading">Actividad Reciente — Últimos Clientes</span> <a href="/tenants" class="text-[11px] uppercase tracking-widest text-gray-500 hover:text-terracotta font-sans">Ver todos →</a></div> <div class="overflow-x-auto"><table class="table w-full"><thead><tr><th>Empresa</th><th>Subdominio</th><th>Plan</th><th class="text-right">Users</th><th class="text-right">MRR</th><th>Estado</th><th>Fecha</th></tr></thead><tbody>`);
      const each_array_5 = ensure_array_like(report.recent_activity || []);
      if (each_array_5.length !== 0) {
        $$renderer2.push("<!--[-->");
        for (let $$index_5 = 0, $$length = each_array_5.length; $$index_5 < $$length; $$index_5++) {
          let t = each_array_5[$$index_5];
          $$renderer2.push(`<tr><td><div class="flex items-center gap-2"><div class="w-7 h-7 bg-charcoal flex items-center justify-center flex-shrink-0"><span class="text-text-light font-sans font-bold text-[10px]">${escape_html((t.company_name || t.subdomain).charAt(0).toUpperCase())}</span></div> <div><div class="text-sm font-semibold font-sans text-text-primary">${escape_html(t.company_name || "—")}</div> <div class="text-[10px] text-gray-400">${escape_html(t.email)}</div></div></div></td><td class="text-[11px] font-mono text-gray-500">${escape_html(t.subdomain)}</td><td><span${attr_class(`badge-${stringify(t.plan === "enterprise" ? "enterprise" : t.plan === "pro" ? "pro" : "basic")} text-[9px]`)}>${escape_html(t.plan)}</span></td><td class="text-right font-sans font-semibold">${escape_html(t.user_count)}</td><td class="text-right font-sans font-semibold">${escape_html(formatCurrency(t.monthly_amount))}</td><td><span${attr_class(clsx(statusBadge(t.status)))}>${escape_html(t.status)}</span></td><td class="text-xs text-gray-400">${escape_html(formatDate(t.created_at))}</td></tr>`);
        }
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<tr><td colspan="7" class="text-center text-gray-400 py-8">Sin actividad reciente</td></tr>`);
      }
      $$renderer2.push(`<!--]--></tbody></table></div></div> <div class="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-8 gap-2"><!--[-->`);
      const each_array_6 = ensure_array_like([
        { href: "/tenants", label: "Tenants" },
        { href: "/billing", label: "Billing" },
        { href: "/partners", label: "Partners" },
        { href: "/leads", label: "Leads" },
        { href: "/invoices", label: "Facturas" },
        { href: "/settlements", label: "Settlements" },
        { href: "/blueprints", label: "Blueprints" },
        { href: "/audit", label: "Auditoría" }
      ]);
      for (let $$index_6 = 0, $$length = each_array_6.length; $$index_6 < $$length; $$index_6++) {
        let link = each_array_6[$$index_6];
        $$renderer2.push(`<a${attr("href", link.href)} class="card p-3 text-center hover:border-terracotta transition-colors"><span class="text-[10px] font-semibold uppercase tracking-widest text-text-secondary font-sans">${escape_html(link.label)}</span></a>`);
      }
      $$renderer2.push(`<!--]--></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function _page($$renderer) {
  Dashboard($$renderer);
}
export {
  _page as default
};
