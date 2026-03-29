import "clsx";
import { h as sanitize_props, i as spread_props, j as slot, d as escape_html, c as attr } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import { X } from "../../../../chunks/x.js";
import { I as Icon } from "../../../../chunks/Icon.js";
import { P as Plus } from "../../../../chunks/plus.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
import { S as Search } from "../../../../chunks/search.js";
function Copy($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    [
      "rect",
      {
        "width": "14",
        "height": "14",
        "x": "8",
        "y": "8",
        "rx": "2",
        "ry": "2"
      }
    ],
    [
      "path",
      {
        "d": "M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"
      }
    ]
  ];
  Icon($$renderer, spread_props([
    { name: "copy" },
    $$sanitized_props,
    {
      /**
       * @component @name Copy
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cmVjdCB3aWR0aD0iMTQiIGhlaWdodD0iMTQiIHg9IjgiIHk9IjgiIHJ4PSIyIiByeT0iMiIgLz4KICA8cGF0aCBkPSJNNCAxNmMtMS4xIDAtMi0uOS0yLTJWNGMwLTEuMS45LTIgMi0yaDEwYzEuMSAwIDIgLjkgMiAyIiAvPgo8L3N2Zz4K) - https://lucide.dev/icons/copy
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
function CredentialsModal($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let {
      isOpen = false,
      credentials = null
    } = $$props;
    let sending = false;
    const tenantUrl = credentials?.tenant_url || (credentials ? `https://${credentials.subdomain}.sajet.us` : "");
    if (isOpen && credentials) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="fixed inset-0 bg-black/60 z-[9999] flex items-center justify-center p-4" role="dialog"><div class="bg-charcoal rounded-xl border border-border-dark w-full max-w-md shadow-2xl animate-in fade-in scale-95 duration-200"><div class="flex items-center justify-between p-6 border-b border-border-dark"><h2 class="text-lg font-semibold text-text-light flex items-center gap-2">✓ Cliente Creado</h2> <button class="text-gray-400 hover:text-text-light transition-colors p-1" aria-label="Cerrar">`);
      X($$renderer2, { size: 20 });
      $$renderer2.push(`<!----></button></div> <div class="p-6 space-y-5"><div class="bg-gray-700/30 rounded-lg p-4"><div class="text-xs text-gray-400 uppercase tracking-widest mb-2">Información del Tenant</div> <div class="text-text-light font-medium mb-1">${escape_html(credentials.company_name)}</div> <div class="text-sm text-gray-400 font-mono break-all">${escape_html(credentials.subdomain)}.sajet.us</div></div> <div class="space-y-3"><div class="text-xs text-gray-400 uppercase tracking-widest">Credenciales de Acceso</div> <div class="bg-dark-subtle rounded-lg p-4 border border-border-dark"><label class="text-xs text-gray-500 block mb-2">Nombre de Usuario</label> <div class="flex items-center gap-2"><code class="text-text-light font-mono text-sm flex-1 break-all">${escape_html(credentials.admin_login)}</code> <button class="p-2 hover:bg-gray-600 rounded transition-colors text-gray-400 hover:text-text-light" title="Copiar usuario"${attr("disabled", sending, true)}>`);
      {
        $$renderer2.push("<!--[!-->");
        Copy($$renderer2, { size: 16 });
      }
      $$renderer2.push(`<!--]--></button></div></div> <div class="bg-dark-subtle rounded-lg p-4 border border-border-dark"><label class="text-xs text-gray-500 block mb-2">Contraseña Temporal</label> <div class="flex items-center gap-2"><code class="text-text-light font-mono text-sm flex-1 break-all">${escape_html(credentials.admin_password)}</code> <button class="p-2 hover:bg-gray-600 rounded transition-colors text-gray-400 hover:text-text-light" title="Copiar contraseña"${attr("disabled", sending, true)}>`);
      {
        $$renderer2.push("<!--[!-->");
        Copy($$renderer2, { size: 16 });
      }
      $$renderer2.push(`<!--]--></button></div> <div class="text-xs text-yellow-400/70 mt-2">⚠ Cambia esta contraseña después de tu primer acceso</div></div> <div class="bg-dark-subtle rounded-lg p-4 border border-border-dark"><label class="text-xs text-gray-500 block mb-2">URL de Acceso</label> <div class="flex items-center gap-2"><code class="text-blue-400 font-mono text-sm flex-1 break-all">${escape_html(tenantUrl)}</code> <button class="p-2 hover:bg-gray-600 rounded transition-colors text-gray-400 hover:text-text-light" title="Copiar URL"${attr("disabled", sending, true)}>`);
      {
        $$renderer2.push("<!--[!-->");
        Copy($$renderer2, { size: 16 });
      }
      $$renderer2.push(`<!--]--></button></div></div></div> <div class="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 text-sm text-blue-300"><div class="font-medium mb-1">Próximos pasos:</div> <ul class="text-xs space-y-1"><li>✓ Copia las credenciales arriba</li> <li>✓ Accede a la URL con usuario y contraseña</li> <li>✓ Cambia tu contraseña inmediatamente</li></ul></div> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> <div class="text-xs text-gray-500 text-center">`);
      {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<span>Este modal se cerrará automáticamente en 8 segundos</span>`);
      }
      $$renderer2.push(`<!--]--></div></div> <div class="border-t border-border-dark p-4 flex gap-2"><button${attr("disabled", sending, true)} class="flex-1 btn-secondary">Cerrar</button> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></div></div></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
function Clients($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let searchQuery = "";
    let filterStatus = "all";
    let filterPlan = "all";
    let filterType = "all";
    let recalculating = false;
    let summary = {
      total_users: 0,
      total_mrr: 0,
      admin_accounts: 0,
      billable_accounts: 0
    };
    let showCredentialsModal = false;
    let credentials = null;
    function formatCurrency(amount) {
      return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(amount);
    }
    $$renderer2.push(`<div class="p-6 space-y-6"><div class="flex items-center justify-between flex-wrap gap-4"><div><h1 class="page-title">Gestión de Clientes</h1> <p class="page-subtitle">Administra clientes, usuarios y montos de facturación</p></div> <div class="flex items-center gap-2"><button class="btn-accent flex items-center gap-2">`);
    Plus($$renderer2, { size: 16 });
    $$renderer2.push(`<!----> Nuevo Cliente</button> <button class="btn-secondary flex items-center gap-2"${attr("disabled", recalculating, true)}>`);
    Refresh_cw($$renderer2, { size: 16, class: "" });
    $$renderer2.push(`<!----> ${escape_html("Recalcular")}</button></div></div> <div class="grid grid-cols-2 md:grid-cols-4 gap-4"><div class="stat-card"><div class="stat-label">MRR Total</div> <div class="stat-value text-terracotta">${escape_html(formatCurrency(summary.total_mrr))}</div></div> <div class="stat-card"><div class="stat-label">Cuentas Facturables</div> <div class="stat-value">${escape_html(summary.billable_accounts)}</div></div> <div class="stat-card"><div class="stat-label">Total Usuarios</div> <div class="stat-value">${escape_html(summary.total_users)}</div></div> <div class="stat-card"><div class="stat-label">Cuentas Admin</div> <div class="stat-value text-yellow-400">${escape_html(summary.admin_accounts)}</div></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="space-y-3"><div class="relative">`);
    Search($$renderer2, {
      size: 16,
      class: "absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"
    });
    $$renderer2.push(`<!----> <input type="text" class="input pl-10" placeholder="Buscar por empresa, email o subdominio..."${attr("value", searchQuery)}/></div> <div class="flex flex-wrap gap-3">`);
    $$renderer2.select({ class: "input px-3 py-2 text-sm", value: filterStatus }, ($$renderer3) => {
      $$renderer3.option({ value: "all" }, ($$renderer4) => {
        $$renderer4.push(`Estado: Todos`);
      });
      $$renderer3.option({ value: "active" }, ($$renderer4) => {
        $$renderer4.push(`✅ Activo`);
      });
      $$renderer3.option({ value: "pending" }, ($$renderer4) => {
        $$renderer4.push(`⏳ Pendiente`);
      });
      $$renderer3.option({ value: "suspended" }, ($$renderer4) => {
        $$renderer4.push(`⚠️ Suspendido`);
      });
      $$renderer3.option({ value: "none" }, ($$renderer4) => {
        $$renderer4.push(`🔹 Sin suscripción`);
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
    $$renderer2.select({ class: "input px-3 py-2 text-sm", value: filterType }, ($$renderer3) => {
      $$renderer3.option({ value: "all" }, ($$renderer4) => {
        $$renderer4.push(`Tipo: Todos`);
      });
      $$renderer3.option({ value: "billable" }, ($$renderer4) => {
        $$renderer4.push(`💳 Facturables`);
      });
      $$renderer3.option({ value: "admin" }, ($$renderer4) => {
        $$renderer4.push(`🛡️ Admin (Exentos)`);
      });
    });
    $$renderer2.push(` `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="flex justify-center py-12"><div class="animate-spin rounded-full h-8 w-8 border-2 border-terracotta border-t-transparent"></div></div>`);
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
    CredentialsModal($$renderer2, {
      isOpen: showCredentialsModal,
      credentials
    });
    $$renderer2.push(`<!---->`);
  });
}
function _page($$renderer) {
  Clients($$renderer);
}
export {
  _page as default
};
