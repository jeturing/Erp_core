import "clsx";
import { h as sanitize_props, i as spread_props, j as slot, d as escape_html, c as attr, e as ensure_array_like, f as derived } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/tenants.js";
import "../../../../chunks/toast.js";
import "../../../../chunks/darkMode.js";
import { I as Icon } from "../../../../chunks/Icon.js";
import { P as Plus } from "../../../../chunks/plus.js";
import { S as Search } from "../../../../chunks/search.js";
function Ghost($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["path", { "d": "M9 10h.01" }],
    ["path", { "d": "M15 10h.01" }],
    [
      "path",
      {
        "d": "M12 2a8 8 0 0 0-8 8v12l3-3 2.5 2.5L12 19l2.5 2.5L17 19l3 3V10a8 8 0 0 0-8-8z"
      }
    ]
  ];
  Icon($$renderer, spread_props([
    { name: "ghost" },
    $$sanitized_props,
    {
      /**
       * @component @name Ghost
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNOSAxMGguMDEiIC8+CiAgPHBhdGggZD0iTTE1IDEwaC4wMSIgLz4KICA8cGF0aCBkPSJNMTIgMmE4IDggMCAwIDAtOCA4djEybDMtMyAyLjUgMi41TDEyIDE5bDIuNSAyLjVMMTcgMTlsMyAzVjEwYTggOCAwIDAgMC04LTh6IiAvPgo8L3N2Zz4K) - https://lucide.dev/icons/ghost
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
    $$renderer2.push(`<div class="space-y-6"><div class="flex items-center justify-between"><div><h1 class="page-title">TENANTS</h1> <p class="page-subtitle">Gestión de clientes y sus instancias</p></div> <div class="flex items-center gap-3"><button class="btn-secondary px-4 py-2 flex items-center gap-2 text-amber-400 border-amber-500/30 hover:bg-amber-900/20">`);
    Ghost($$renderer2, { size: 14 });
    $$renderer2.push(`<!----> FANTASMAS</button> <button class="btn-accent px-4 py-2 flex items-center gap-2">`);
    Plus($$renderer2, { size: 14 });
    $$renderer2.push(`<!----> NUEVO TENANT</button></div></div> `);
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
