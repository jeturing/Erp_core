import "clsx";
import { h as sanitize_props, i as spread_props, j as slot, c as attr, d as escape_html } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/tenants.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { f as formatCurrency } from "../../../../chunks/formatters.js";
import { F as File_text } from "../../../../chunks/file-text.js";
import { Z as Zap } from "../../../../chunks/zap.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
import { P as Plus } from "../../../../chunks/plus.js";
import { I as Icon } from "../../../../chunks/Icon.js";
import { S as Search } from "../../../../chunks/search.js";
function Link_2($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["path", { "d": "M9 17H7A5 5 0 0 1 7 7h2" }],
    ["path", { "d": "M15 7h2a5 5 0 1 1 0 10h-2" }],
    ["line", { "x1": "8", "x2": "16", "y1": "12", "y2": "12" }]
  ];
  Icon($$renderer, spread_props([
    { name: "link-2" },
    $$sanitized_props,
    {
      /**
       * @component @name Link2
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNOSAxN0g3QTUgNSAwIDAgMSA3IDdoMiIgLz4KICA8cGF0aCBkPSJNMTUgN2gyYTUgNSAwIDEgMSAwIDEwaC0yIiAvPgogIDxsaW5lIHgxPSI4IiB4Mj0iMTYiIHkxPSIxMiIgeTI9IjEyIiAvPgo8L3N2Zz4K) - https://lucide.dev/icons/link-2
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
function Invoices($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let totalAmount, paidCount, pendingCount, stripeLinked;
    let invoices = [];
    let total = 0;
    let loading = true;
    let search = "";
    let statusFilter = "";
    (invoices || []).filter((i) => (i.invoice_number || "").toLowerCase().includes(search.toLowerCase()));
    totalAmount = (invoices || []).reduce((s, i) => s + i.total, 0);
    paidCount = (invoices || []).filter((i) => i.status === "paid").length;
    pendingCount = (invoices || []).filter((i) => ["issued", "draft", "open", "past_due", "overdue"].includes(i.status)).length;
    stripeLinked = (invoices || []).filter((i) => i.stripe_invoice_id).length;
    $$renderer2.push(`<div class="p-6 space-y-6"><div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"><div><h1 class="page-title flex items-center gap-2">`);
    File_text($$renderer2, { size: 24 });
    $$renderer2.push(`<!----> Facturas</h1> <p class="page-subtitle">Facturación SaaS — Fuente de verdad: Stripe</p></div> <div class="flex gap-2"><button class="btn-secondary flex items-center gap-2">`);
    Zap($$renderer2, { size: 14 });
    $$renderer2.push(`<!----> Stripe Sync</button> <button class="btn-secondary flex items-center gap-2"${attr("disabled", loading, true)}>`);
    Refresh_cw($$renderer2, { size: 14, class: "animate-spin" });
    $$renderer2.push(`<!----> Actualizar</button> <button class="btn-accent flex items-center gap-2">`);
    Plus($$renderer2, { size: 16 });
    $$renderer2.push(`<!----> Generar Factura</button></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="grid grid-cols-2 lg:grid-cols-5 gap-4"><div class="stat-card"><span class="stat-label">Total Facturas</span> <span class="stat-value">${escape_html(total)}</span></div> <div class="stat-card"><span class="stat-label">Monto Total</span> <span class="stat-value text-success">${escape_html(formatCurrency(totalAmount))}</span></div> <div class="stat-card"><span class="stat-label">Pagadas</span> <span class="stat-value text-success">${escape_html(paidCount)}</span></div> <div class="stat-card"><span class="stat-label">Pendientes</span> <span class="stat-value text-warning">${escape_html(pendingCount)}</span></div> <div class="stat-card"><span class="stat-label flex items-center gap-1">`);
    Link_2($$renderer2, { size: 12 });
    $$renderer2.push(`<!----> Stripe</span> <span class="stat-value text-indigo-400">${escape_html(stripeLinked)}</span></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="flex flex-col sm:flex-row gap-3"><div class="relative flex-1">`);
    Search($$renderer2, {
      size: 16,
      class: "absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"
    });
    $$renderer2.push(`<!----> <input type="text"${attr("value", search)} placeholder="Buscar por número..." class="input pl-10 w-full"/></div> `);
    $$renderer2.select({ value: statusFilter, class: "input w-auto" }, ($$renderer3) => {
      $$renderer3.option({ value: "" }, ($$renderer4) => {
        $$renderer4.push(`Todos los estados`);
      });
      $$renderer3.option({ value: "draft" }, ($$renderer4) => {
        $$renderer4.push(`Draft`);
      });
      $$renderer3.option({ value: "issued" }, ($$renderer4) => {
        $$renderer4.push(`Issued`);
      });
      $$renderer3.option({ value: "paid" }, ($$renderer4) => {
        $$renderer4.push(`Paid`);
      });
      $$renderer3.option({ value: "overdue" }, ($$renderer4) => {
        $$renderer4.push(`Overdue`);
      });
      $$renderer3.option({ value: "void" }, ($$renderer4) => {
        $$renderer4.push(`Void`);
      });
    });
    $$renderer2.push(`</div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-center py-16 text-gray-500"><div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin mx-auto"></div></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Invoices($$renderer);
}
export {
  _page as default
};
