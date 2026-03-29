import "clsx";
import { d as escape_html, c as attr, e as ensure_array_like, f as derived } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/toast.js";
import "../../../../chunks/darkMode.js";
import { P as Plus } from "../../../../chunks/plus.js";
import { S as Search } from "../../../../chunks/search.js";
function Tenants($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let tenants = [];
    let searchQuery = "";
    let filterStatus = "all";
    let filterPlan = "all";
    let filterPartner = "all";
    let filteredTenants = derived(() => tenants.filter((t) => {
      return true;
    }));
    let totalTenants = derived(() => tenants.length);
    let activeTenants = derived(() => tenants.filter((t) => t.status === "active").length);
    let suspendedTenants = derived(() => tenants.filter((t) => t.status === "suspended").length);
    let uniquePartnerNames = derived(() => [
      ...new Set(tenants.map((t) => t.partner_name).filter(Boolean))
    ]);
    $$renderer2.push(`<div class="space-y-6"><div class="flex items-center justify-between"><div><h1 class="page-title">TENANTS</h1> <p class="page-subtitle">Gestión de clientes y sus instancias</p></div> <button class="btn-accent px-4 py-2 flex items-center gap-2">`);
    Plus($$renderer2, { size: 14 });
    $$renderer2.push(`<!----> NUEVO TENANT</button></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="grid grid-cols-2 md:grid-cols-4 gap-4"><div class="stat-card card"><div class="stat-value">${escape_html(totalTenants())}</div> <div class="stat-label">Total Tenants</div></div> <div class="stat-card card"><div class="stat-value">${escape_html(activeTenants())}</div> <div class="stat-label">Activos</div></div> <div class="stat-card card"><div class="stat-value">${escape_html(suspendedTenants())}</div> <div class="stat-label">Suspendidos</div></div> <div class="stat-card card"><div class="stat-value">${escape_html(filteredTenants().length)}</div> <div class="stat-label">Mostrando</div></div></div> <div class="space-y-3"><div class="relative">`);
    Search($$renderer2, {
      size: 14,
      class: "absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
    });
    $$renderer2.push(`<!----> <input class="input w-full pl-9 pr-3 py-2" type="text" placeholder="Buscar por subdominio, email o empresa..."${attr("value", searchQuery)}/></div> <div class="flex flex-wrap gap-3">`);
    $$renderer2.select({ class: "input px-3 py-2 text-sm", value: filterStatus }, ($$renderer3) => {
      $$renderer3.option({ value: "all" }, ($$renderer4) => {
        $$renderer4.push(`Estado: Todos`);
      });
      $$renderer3.option({ value: "active" }, ($$renderer4) => {
        $$renderer4.push(`✅ Activos`);
      });
      $$renderer3.option({ value: "suspended" }, ($$renderer4) => {
        $$renderer4.push(`⚠️ Suspendidos`);
      });
      $$renderer3.option({ value: "pending" }, ($$renderer4) => {
        $$renderer4.push(`⏳ Pendientes`);
      });
    });
    $$renderer2.push(` `);
    $$renderer2.select({ class: "input px-3 py-2 text-sm", value: filterPlan }, ($$renderer3) => {
      $$renderer3.option({ value: "all" }, ($$renderer4) => {
        $$renderer4.push(`Plan: Todos`);
      });
      $$renderer3.option({ value: "basic" }, ($$renderer4) => {
        $$renderer4.push(`Basic`);
      });
      $$renderer3.option({ value: "pro" }, ($$renderer4) => {
        $$renderer4.push(`Pro`);
      });
      $$renderer3.option({ value: "enterprise" }, ($$renderer4) => {
        $$renderer4.push(`Enterprise`);
      });
    });
    $$renderer2.push(` `);
    $$renderer2.select({ class: "input px-3 py-2 text-sm", value: filterPartner }, ($$renderer3) => {
      $$renderer3.option({ value: "all" }, ($$renderer4) => {
        $$renderer4.push(`Partner: Todos`);
      });
      $$renderer3.option({ value: "none" }, ($$renderer4) => {
        $$renderer4.push(`🔹 Sin Partner (Directo)`);
      });
      $$renderer3.push(`<!--[-->`);
      const each_array_2 = ensure_array_like(uniquePartnerNames());
      for (let $$index_2 = 0, $$length = each_array_2.length; $$index_2 < $$length; $$index_2++) {
        let pn = each_array_2[$$index_2];
        $$renderer3.option({ value: pn }, ($$renderer4) => {
          $$renderer4.push(`${escape_html(pn)}`);
        });
      }
      $$renderer3.push(`<!--]-->`);
    });
    $$renderer2.push(` `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div></div> <div class="card p-0 overflow-hidden">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="p-8 text-center text-gray-500 text-sm">Cargando tenants...</div>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Tenants($$renderer);
}
export {
  _page as default
};
