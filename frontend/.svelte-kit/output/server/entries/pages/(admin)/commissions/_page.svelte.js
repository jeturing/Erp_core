import "clsx";
import { d as escape_html, c as attr, e as ensure_array_like } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { P as Percent } from "../../../../chunks/percent.js";
import { P as Plus } from "../../../../chunks/plus.js";
import { S as Search } from "../../../../chunks/search.js";
function Commissions($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let commissions = [];
    let partners = [];
    let search = "";
    let partnerFilter = 0;
    let statusFilter = "";
    let summary = {
      total_partner_amount: 0,
      total_jeturing_amount: 0,
      total_pending_payout: 0,
      total_gross: 0
    };
    (commissions || []).filter((c) => (c.partner_name || "").toLowerCase().includes(search.toLowerCase()));
    $$renderer2.push(`<div class="p-6 space-y-6"><div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"><div><h1 class="page-title flex items-center gap-2">`);
    Percent($$renderer2, { size: 24 });
    $$renderer2.push(`<!----> Comisiones</h1> <p class="page-subtitle">Split 50/50 sobre Ingresos Netos — Cláusula 8</p></div> <button class="btn-accent flex items-center gap-2">`);
    Plus($$renderer2, { size: 16 });
    $$renderer2.push(`<!----> Nueva Comisión</button></div> <div class="grid grid-cols-1 sm:grid-cols-4 gap-4"><div class="stat-card"><div class="text-xs font-semibold uppercase text-gray-500 mb-1">Ingresos Brutos</div> <div class="text-2xl font-bold text-text-light">$${escape_html(summary.total_gross.toLocaleString("en-US", { minimumFractionDigits: 2 }))}</div></div> <div class="stat-card"><div class="text-xs font-semibold uppercase text-gray-500 mb-1">Partners (50%)</div> <div class="text-2xl font-bold text-purple-400">$${escape_html(summary.total_partner_amount.toLocaleString("en-US", { minimumFractionDigits: 2 }))}</div></div> <div class="stat-card"><div class="text-xs font-semibold uppercase text-gray-500 mb-1">Jeturing (50%)</div> <div class="text-2xl font-bold text-blue-400">$${escape_html(summary.total_jeturing_amount.toLocaleString("en-US", { minimumFractionDigits: 2 }))}</div></div> <div class="stat-card"><div class="text-xs font-semibold uppercase text-gray-500 mb-1">Pendiente pago</div> <div class="text-2xl font-bold text-amber-400">$${escape_html(summary.total_pending_payout.toLocaleString("en-US", { minimumFractionDigits: 2 }))}</div></div></div> <div class="flex flex-col sm:flex-row gap-3"><div class="relative flex-1">`);
    Search($$renderer2, {
      size: 16,
      class: "absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"
    });
    $$renderer2.push(`<!----> <input type="text"${attr("value", search)} placeholder="Buscar por partner..." class="input pl-10 w-full"/></div> `);
    $$renderer2.select({ value: partnerFilter, class: "input w-auto" }, ($$renderer3) => {
      $$renderer3.option({ value: 0 }, ($$renderer4) => {
        $$renderer4.push(`Todos los partners`);
      });
      $$renderer3.push(`<!--[-->`);
      const each_array = ensure_array_like(partners);
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let p = each_array[$$index];
        $$renderer3.option({ value: p.id }, ($$renderer4) => {
          $$renderer4.push(`${escape_html(p.company_name)}`);
        });
      }
      $$renderer3.push(`<!--]-->`);
    });
    $$renderer2.push(` `);
    $$renderer2.select({ value: statusFilter, class: "input w-auto" }, ($$renderer3) => {
      $$renderer3.option({ value: "" }, ($$renderer4) => {
        $$renderer4.push(`Todos los estados`);
      });
      $$renderer3.option({ value: "pending" }, ($$renderer4) => {
        $$renderer4.push(`Pendiente`);
      });
      $$renderer3.option({ value: "approved" }, ($$renderer4) => {
        $$renderer4.push(`Aprobada`);
      });
      $$renderer3.option({ value: "paid" }, ($$renderer4) => {
        $$renderer4.push(`Pagada`);
      });
      $$renderer3.option({ value: "disputed" }, ($$renderer4) => {
        $$renderer4.push(`Disputada`);
      });
    });
    $$renderer2.push(`</div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-center py-12 text-gray-500">Cargando comisiones...</div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Commissions($$renderer);
}
export {
  _page as default
};
