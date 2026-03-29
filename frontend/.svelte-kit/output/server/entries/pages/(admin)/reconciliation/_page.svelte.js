import "clsx";
import { h as sanitize_props, i as spread_props, j as slot, c as attr, d as escape_html, k as attr_class, b as stringify } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { f as formatCurrency } from "../../../../chunks/formatters.js";
import { I as Icon } from "../../../../chunks/Icon.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
import { P as Play } from "../../../../chunks/play.js";
function Git_compare($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["circle", { "cx": "18", "cy": "18", "r": "3" }],
    ["circle", { "cx": "6", "cy": "6", "r": "3" }],
    ["path", { "d": "M13 6h3a2 2 0 0 1 2 2v7" }],
    ["path", { "d": "M11 18H8a2 2 0 0 1-2-2V9" }]
  ];
  Icon($$renderer, spread_props([
    { name: "git-compare" },
    $$sanitized_props,
    {
      /**
       * @component @name GitCompare
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8Y2lyY2xlIGN4PSIxOCIgY3k9IjE4IiByPSIzIiAvPgogIDxjaXJjbGUgY3g9IjYiIGN5PSI2IiByPSIzIiAvPgogIDxwYXRoIGQ9Ik0xMyA2aDNhMiAyIDAgMCAxIDIgMnY3IiAvPgogIDxwYXRoIGQ9Ik0xMSAxOEg4YTIgMiAwIDAgMS0yLTJWOSIgLz4KPC9zdmc+Cg==) - https://lucide.dev/icons/git-compare
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
function Reconciliation($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let totalDiscrepancy, cleanRuns, issueRuns;
    let runs = [];
    let loading = true;
    totalDiscrepancy = (runs || []).reduce((s, r) => s + Math.abs(r.discrepancy), 0);
    cleanRuns = (runs || []).filter((r) => Math.abs(r.discrepancy) < 0.01).length;
    issueRuns = (runs || []).length - cleanRuns;
    $$renderer2.push(`<div class="p-6 space-y-6"><div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"><div><h1 class="page-title flex items-center gap-2">`);
    Git_compare($$renderer2, { size: 24 });
    $$renderer2.push(`<!----> Reconciliación</h1> <p class="page-subtitle">Stripe vs Base de Datos local — auditoría de ingresos</p></div> <div class="flex gap-2"><button class="btn-secondary flex items-center gap-2"${attr("disabled", loading, true)}>`);
    Refresh_cw($$renderer2, { size: 14, class: "animate-spin" });
    $$renderer2.push(`<!----> Actualizar</button> <button class="btn-accent flex items-center gap-2">`);
    Play($$renderer2, { size: 16 });
    $$renderer2.push(`<!----> Ejecutar Reconciliación</button></div></div> <div class="grid grid-cols-2 lg:grid-cols-4 gap-4"><div class="stat-card"><span class="stat-label">Total Ejecuciones</span> <span class="stat-value">${escape_html(runs.length)}</span></div> <div class="stat-card"><span class="stat-label">Sin diferencias</span> <span class="stat-value text-success">${escape_html(cleanRuns)}</span></div> <div class="stat-card"><span class="stat-label">Con Issues</span> <span class="stat-value text-error">${escape_html(issueRuns)}</span></div> <div class="stat-card"><span class="stat-label">Discrepancia Total</span> <span${attr_class(`stat-value ${stringify(totalDiscrepancy > 0 ? "text-warning" : "text-success")}`)}>${escape_html(formatCurrency(totalDiscrepancy))}</span></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-center py-16 text-gray-500"><div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin mx-auto"></div></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Reconciliation($$renderer);
}
export {
  _page as default
};
