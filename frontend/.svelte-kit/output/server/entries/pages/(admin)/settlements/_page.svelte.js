import "clsx";
import { c as attr, d as escape_html } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/tenants.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { f as formatCurrency } from "../../../../chunks/formatters.js";
import { S as Scale } from "../../../../chunks/scale.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
import { P as Plus } from "../../../../chunks/plus.js";
function Settlements($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let totalGross, totalJeturing, totalPartner;
    let settlements = [];
    let loading = true;
    totalGross = (settlements || []).reduce((s, i) => s + i.gross_revenue, 0);
    totalJeturing = (settlements || []).reduce((s, i) => s + i.jeturing_share, 0);
    totalPartner = (settlements || []).reduce((s, i) => s + i.final_partner_payout, 0);
    $$renderer2.push(`<div class="p-6 space-y-6"><div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"><div><h1 class="page-title flex items-center gap-2">`);
    Scale($$renderer2, { size: 24 });
    $$renderer2.push(`<!----> Liquidaciones</h1> <p class="page-subtitle">Settlement 50/50 — Partner ↔ Jeturing</p></div> <div class="flex gap-2"><button class="btn-secondary flex items-center gap-2"${attr("disabled", loading, true)}>`);
    Refresh_cw($$renderer2, { size: 14, class: "animate-spin" });
    $$renderer2.push(`<!----> Actualizar</button> <button class="btn-accent flex items-center gap-2">`);
    Plus($$renderer2, { size: 16 });
    $$renderer2.push(`<!----> Nueva Liquidación</button></div></div> <div class="grid grid-cols-1 sm:grid-cols-3 gap-4"><div class="stat-card"><span class="stat-label">Revenue Bruto Total</span> <span class="stat-value">${escape_html(formatCurrency(totalGross))}</span></div> <div class="stat-card"><span class="stat-label">Share Jeturing</span> <span class="stat-value text-info">${escape_html(formatCurrency(totalJeturing))}</span></div> <div class="stat-card"><span class="stat-label">Payout Partners</span> <span class="stat-value text-terracotta">${escape_html(formatCurrency(totalPartner))}</span></div></div> `);
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
  Settlements($$renderer);
}
export {
  _page as default
};
