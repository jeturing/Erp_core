import "clsx";
import { h as sanitize_props, i as spread_props, j as slot, d as escape_html, s as store_get, e as ensure_array_like, k as attr_class, l as clsx, c as attr, b as stringify, u as unsubscribe_stores } from "../../../../chunks/index2.js";
import { e as domainsStore, f as domainStats } from "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import "../../../../chunks/client.js";
import { a as formatDate } from "../../../../chunks/formatters.js";
import { P as Plus } from "../../../../chunks/plus.js";
import { X } from "../../../../chunks/x.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
import { G as Globe } from "../../../../chunks/globe.js";
import { E as External_link } from "../../../../chunks/external-link.js";
import { S as Shield } from "../../../../chunks/shield.js";
import { S as Server } from "../../../../chunks/server.js";
import { Z as Zap } from "../../../../chunks/zap.js";
import { C as Check } from "../../../../chunks/check.js";
import { T as Trash_2 } from "../../../../chunks/trash-2.js";
import { I as Icon } from "../../../../chunks/Icon.js";
import { T as Triangle_alert } from "../../../../chunks/triangle-alert.js";
import { C as Chevron_down } from "../../../../chunks/chevron-down.js";
function Info($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["circle", { "cx": "12", "cy": "12", "r": "10" }],
    ["path", { "d": "M12 16v-4" }],
    ["path", { "d": "M12 8h.01" }]
  ];
  Icon($$renderer, spread_props([
    { name: "info" },
    $$sanitized_props,
    {
      /**
       * @component @name Info
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCIgLz4KICA8cGF0aCBkPSJNMTIgMTZ2LTQiIC8+CiAgPHBhdGggZD0iTTEyIDhoLjAxIiAvPgo8L3N2Zz4K) - https://lucide.dev/icons/info
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
function Pencil($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    [
      "path",
      {
        "d": "M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"
      }
    ],
    ["path", { "d": "m15 5 4 4" }]
  ];
  Icon($$renderer, spread_props([
    { name: "pencil" },
    $$sanitized_props,
    {
      /**
       * @component @name Pencil
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMjEuMTc0IDYuODEyYTEgMSAwIDAgMC0zLjk4Ni0zLjk4N0wzLjg0MiAxNi4xNzRhMiAyIDAgMCAwLS41LjgzbC0xLjMyMSA0LjM1MmEuNS41IDAgMCAwIC42MjMuNjIybDQuMzUzLTEuMzJhMiAyIDAgMCAwIC44My0uNDk3eiIgLz4KICA8cGF0aCBkPSJtMTUgNSA0IDQiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/pencil
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
function Domains($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let domains = [];
    let loading = true;
    let customers = [];
    let linkedDomainsByCustomer = {};
    let loadingLinkedByCustomer = {};
    let expandedLinkedCustomerId = null;
    let editingQuotaCustomerId = null;
    let editingMaxDomains = 0;
    let savingQuota = false;
    let filterCustomerId = null;
    let filterStatus = "";
    let actionLoading = {};
    domainsStore.subscribe((state) => {
      domains = state.items ?? [];
      loading = state.loading ?? false;
    });
    function sourceLabel(source) {
      if (source === "base") return "Base";
      if (source === "custom") return "Custom";
      if (source === "odoo") return "Sajet";
      return source;
    }
    function sourceClass(source) {
      if (source === "base") return "bg-blue-100 text-blue-800";
      if (source === "custom") return "bg-emerald-100 text-emerald-800";
      if (source === "odoo") return "bg-purple-100 text-purple-800";
      return "bg-gray-100 text-gray-700";
    }
    function linkedDomainsForRow(domain) {
      const linked = linkedDomainsByCustomer[domain.customer_id]?.domains ?? [];
      const currentExternal = (domain.external_domain ?? "").toLowerCase();
      const currentSajet = (domain.sajet_full_domain ?? "").toLowerCase();
      return linked.filter((d) => d.domain !== currentExternal && d.domain !== currentSajet);
    }
    async function handleFilter() {
      const params = {};
      await domainsStore.load(params);
    }
    function getDomainStep(d) {
      if (d.is_active && d.nginx_configured) return 5;
      if (d.is_active) return 4;
      if (d.verification_status === "verified") return 3;
      if (d.cloudflare_configured) return 2;
      return 1;
    }
    function getStepLabel(step) {
      const labels = {
        1: "Registrado",
        2: "CF Configurado",
        3: "DNS Verificado",
        4: "Activo",
        5: "Operativo"
      };
      return labels[step] ?? "Desconocido";
    }
    function getCustomerForDomain(d) {
      return customers.find((c) => c.id === d.customer_id);
    }
    $$renderer2.push(`<div class="space-y-6"><div class="flex items-center justify-between flex-wrap gap-3"><div><h1 class="page-title">DOMINIOS EXTERNOS</h1> <p class="page-subtitle">Vincular dominios personalizados a tenants según plan</p></div> <button class="btn-accent px-4 py-2 flex items-center gap-2">`);
    Plus($$renderer2, { size: 14 });
    $$renderer2.push(`<!----> NUEVO DOMINIO</button></div> <div class="grid grid-cols-2 sm:grid-cols-5 gap-3"><div class="stat-card card"><div class="stat-value">${escape_html(store_get($$store_subs ??= {}, "$domainStats", domainStats).total)}</div> <div class="stat-label">Total</div></div> <div class="stat-card card"><div class="stat-value text-emerald-500">${escape_html(store_get($$store_subs ??= {}, "$domainStats", domainStats).active)}</div> <div class="stat-label">Activos</div></div> <div class="stat-card card"><div class="stat-value text-emerald-600">${escape_html(store_get($$store_subs ??= {}, "$domainStats", domainStats).verified)}</div> <div class="stat-label">Verificados</div></div> <div class="stat-card card"><div class="stat-value text-amber-500">${escape_html(store_get($$store_subs ??= {}, "$domainStats", domainStats).pending)}</div> <div class="stat-label">Pendientes</div></div> <div class="stat-card card"><div class="stat-value text-red-500">${escape_html(store_get($$store_subs ??= {}, "$domainStats", domainStats).failed)}</div> <div class="stat-label">Fallidos</div></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="card"><div class="flex flex-wrap items-end gap-4"><div class="flex-1 min-w-[200px]"><label class="label" for="filter-customer">Filtrar por cliente</label> `);
    $$renderer2.select(
      {
        id: "filter-customer",
        class: "input w-full px-3 py-2",
        value: filterCustomerId,
        onchange: handleFilter
      },
      ($$renderer3) => {
        $$renderer3.option({ value: null }, ($$renderer4) => {
          $$renderer4.push(`Todos los clientes`);
        });
        $$renderer3.push(`<!--[-->`);
        const each_array_1 = ensure_array_like(customers);
        for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
          let c = each_array_1[$$index_1];
          $$renderer3.option({ value: c.id }, ($$renderer4) => {
            $$renderer4.push(`${escape_html(c.company_name)} (${escape_html(c.subdomain)})`);
          });
        }
        $$renderer3.push(`<!--]-->`);
      }
    );
    $$renderer2.push(`</div> <div class="min-w-[160px]"><label class="label" for="filter-status">Estado</label> `);
    $$renderer2.select(
      {
        id: "filter-status",
        class: "input w-full px-3 py-2",
        value: filterStatus,
        onchange: handleFilter
      },
      ($$renderer3) => {
        $$renderer3.option({ value: "" }, ($$renderer4) => {
          $$renderer4.push(`Todos`);
        });
        $$renderer3.option({ value: "pending" }, ($$renderer4) => {
          $$renderer4.push(`Pendiente`);
        });
        $$renderer3.option({ value: "verifying" }, ($$renderer4) => {
          $$renderer4.push(`Verificando`);
        });
        $$renderer3.option({ value: "verified" }, ($$renderer4) => {
          $$renderer4.push(`Verificado`);
        });
        $$renderer3.option({ value: "failed" }, ($$renderer4) => {
          $$renderer4.push(`Fallido`);
        });
      }
    );
    $$renderer2.push(`</div> <button class="btn-secondary px-3 py-2 flex items-center gap-1">`);
    X($$renderer2, { size: 14 });
    $$renderer2.push(`<!----> Limpiar</button></div></div> <div class="card p-0 overflow-hidden">`);
    if (loading) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="p-8 text-center text-gray-500 text-sm flex items-center justify-center gap-2">`);
      Refresh_cw($$renderer2, { size: 16, class: "animate-spin" });
      $$renderer2.push(`<!----> Cargando dominios...</div>`);
    } else if (domains.length === 0) {
      $$renderer2.push("<!--[1-->");
      $$renderer2.push(`<div class="p-12 text-center">`);
      Globe($$renderer2, { size: 48, class: "mx-auto text-gray-300 mb-3" });
      $$renderer2.push(`<!----> <p class="text-gray-500 text-sm">No hay dominios registrados</p> <p class="text-gray-400 text-xs mt-1">Haga clic en "NUEVO DOMINIO" para vincular un dominio externo</p></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<div class="overflow-x-auto"><table class="table w-full"><thead><tr><th>CLIENTE</th><th>DOMINIO EXTERNO</th><th>SUBDOMINIO SAJET</th><th>PROGRESO</th><th>ESTADO</th><th>CREADO</th><th>ACCIONES</th></tr></thead><tbody><!--[-->`);
      const each_array_2 = ensure_array_like(domains);
      for (let $$index_4 = 0, $$length = each_array_2.length; $$index_4 < $$length; $$index_4++) {
        let domain = each_array_2[$$index_4];
        const step = getDomainStep(domain);
        const customer = getCustomerForDomain(domain);
        $$renderer2.push(`<tr${attr_class(clsx(!domain.is_active ? "opacity-60" : ""))}><td><div class="text-sm font-medium">${escape_html(customer?.company_name ?? `#${domain.customer_id}`)}</div> `);
        if (customer) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="text-xs text-gray-400 font-mono">${escape_html(customer.plan_name)} `);
          if (customer.unlimited) {
            $$renderer2.push("<!--[-->");
            $$renderer2.push(`· ∞`);
          } else if (customer.max_domains > 0) {
            $$renderer2.push("<!--[1-->");
            $$renderer2.push(`· ${escape_html(customer.used_domains)}/${escape_html(customer.max_domains)}`);
          } else {
            $$renderer2.push("<!--[!-->");
          }
          $$renderer2.push(`<!--]--></div>`);
        } else {
          $$renderer2.push("<!--[!-->");
        }
        $$renderer2.push(`<!--]--></td><td><div class="flex items-center gap-1.5">`);
        Globe($$renderer2, {
          size: 14,
          class: domain.is_active ? "text-emerald-500" : "text-gray-400"
        });
        $$renderer2.push(`<!----> <span class="font-mono text-sm">${escape_html(domain.external_domain)}</span></div> `);
        if (domain.is_active) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<a${attr("href", `https://${stringify(domain.external_domain)}`)} target="_blank" rel="noopener" class="text-xs text-blue-500 hover:underline flex items-center gap-0.5 mt-0.5">`);
          External_link($$renderer2, { size: 10 });
          $$renderer2.push(`<!----> Abrir</a>`);
        } else {
          $$renderer2.push("<!--[!-->");
        }
        $$renderer2.push(`<!--]--> `);
        if (loadingLinkedByCustomer[domain.customer_id]) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="text-[10px] text-gray-400 mt-1 flex items-center gap-1">`);
          Refresh_cw($$renderer2, { size: 10, class: "animate-spin" });
          $$renderer2.push(`<!----> Cargando vinculados...</div>`);
        } else if (linkedDomainsForRow(domain).length > 0) {
          $$renderer2.push("<!--[1-->");
          $$renderer2.push(`<div class="mt-1.5 space-y-1"><div class="text-[10px] text-gray-500">Vinculados (${escape_html(linkedDomainsForRow(domain).length)})</div> <div class="flex flex-wrap gap-1"><!--[-->`);
          const each_array_3 = ensure_array_like(linkedDomainsForRow(domain).slice(0, 3));
          for (let $$index_2 = 0, $$length2 = each_array_3.length; $$index_2 < $$length2; $$index_2++) {
            let ld = each_array_3[$$index_2];
            $$renderer2.push(`<span class="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-700 font-mono"${attr("title", ld.sources.join(", "))}>${escape_html(ld.domain)}</span>`);
          }
          $$renderer2.push(`<!--]--> `);
          if (linkedDomainsForRow(domain).length > 3) {
            $$renderer2.push("<!--[-->");
            $$renderer2.push(`<span class="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">+${escape_html(linkedDomainsForRow(domain).length - 3)}</span>`);
          } else {
            $$renderer2.push("<!--[!-->");
          }
          $$renderer2.push(`<!--]--></div></div>`);
        } else {
          $$renderer2.push("<!--[!-->");
        }
        $$renderer2.push(`<!--]--></td><td><span class="text-sm text-gray-600 font-mono">${escape_html(domain.sajet_full_domain ?? domain.sajet_subdomain + ".sajet.us")}</span></td><td><div class="flex items-center gap-0.5"><!--[-->`);
        const each_array_4 = ensure_array_like([1, 2, 3, 4, 5]);
        for (let $$index_3 = 0, $$length2 = each_array_4.length; $$index_3 < $$length2; $$index_3++) {
          let s = each_array_4[$$index_3];
          $$renderer2.push(`<div${attr_class(`w-5 h-1.5 rounded-full ${stringify(s <= step ? "bg-emerald-500" : "bg-gray-200")}`)}${attr("title", getStepLabel(s))}></div>`);
        }
        $$renderer2.push(`<!--]--> <span class="text-xs text-gray-500 ml-1.5">${escape_html(getStepLabel(step))}</span></div></td><td><div class="flex flex-col gap-1">`);
        if (domain.verification_status === "verified") {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<span class="badge-success text-[10px]">Verificado</span>`);
        } else if (domain.verification_status === "pending") {
          $$renderer2.push("<!--[1-->");
          $$renderer2.push(`<span class="badge-warning text-[10px]">DNS Pendiente</span>`);
        } else if (domain.verification_status === "verifying") {
          $$renderer2.push("<!--[2-->");
          $$renderer2.push(`<span class="badge-warning text-[10px]">Verificando</span>`);
        } else {
          $$renderer2.push("<!--[!-->");
          $$renderer2.push(`<span class="badge-error text-[10px]">${escape_html(domain.verification_status)}</span>`);
        }
        $$renderer2.push(`<!--]--> <div class="flex items-center gap-2 text-[10px]"><span class="flex items-center gap-0.5" title="Cloudflare">`);
        if (domain.cloudflare_configured) {
          $$renderer2.push("<!--[-->");
          Shield($$renderer2, { size: 10, class: "text-emerald-500" });
          $$renderer2.push(`<!----> CF`);
        } else {
          $$renderer2.push("<!--[!-->");
          Shield($$renderer2, { size: 10, class: "text-gray-300" });
          $$renderer2.push(`<!----> CF`);
        }
        $$renderer2.push(`<!--]--></span> <span class="flex items-center gap-0.5" title="Nginx">`);
        if (domain.nginx_configured) {
          $$renderer2.push("<!--[-->");
          Server($$renderer2, { size: 10, class: "text-emerald-500" });
          $$renderer2.push(`<!----> NGX`);
        } else {
          $$renderer2.push("<!--[!-->");
          Server($$renderer2, { size: 10, class: "text-gray-300" });
          $$renderer2.push(`<!----> NGX`);
        }
        $$renderer2.push(`<!--]--></span> <span class="flex items-center gap-0.5" title="Activo">`);
        if (domain.is_active) {
          $$renderer2.push("<!--[-->");
          Zap($$renderer2, { size: 10, class: "text-emerald-500" });
          $$renderer2.push(`<!----> ON`);
        } else {
          $$renderer2.push("<!--[!-->");
          Zap($$renderer2, { size: 10, class: "text-gray-300" });
          $$renderer2.push(`<!----> OFF`);
        }
        $$renderer2.push(`<!--]--></span></div></div></td><td class="text-xs text-gray-500">${escape_html(formatDate(domain.created_at))}</td><td><div class="flex items-center gap-1 flex-wrap">`);
        if (!domain.cloudflare_configured) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<button class="btn-secondary btn-sm text-[10px] flex items-center gap-1"${attr("disabled", !!actionLoading[domain.id], true)}>`);
          if (actionLoading[domain.id] === "cf") {
            $$renderer2.push("<!--[-->");
            Refresh_cw($$renderer2, { size: 10, class: "animate-spin" });
          } else {
            $$renderer2.push("<!--[!-->");
            Shield($$renderer2, { size: 10 });
          }
          $$renderer2.push(`<!--]--> CF</button>`);
        } else {
          $$renderer2.push("<!--[!-->");
        }
        $$renderer2.push(`<!--]--> `);
        if (domain.cloudflare_configured && domain.verification_status !== "verified") {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<button class="btn-secondary btn-sm text-[10px] flex items-center gap-1"${attr("disabled", !!actionLoading[domain.id], true)}>`);
          if (actionLoading[domain.id] === "verify") {
            $$renderer2.push("<!--[-->");
            Refresh_cw($$renderer2, { size: 10, class: "animate-spin" });
          } else {
            $$renderer2.push("<!--[!-->");
            Check($$renderer2, { size: 10 });
          }
          $$renderer2.push(`<!--]--> VERIFICAR</button>`);
        } else {
          $$renderer2.push("<!--[!-->");
        }
        $$renderer2.push(`<!--]--> `);
        if (domain.verification_status === "verified" && !domain.is_active) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<button class="btn-sm text-[10px] flex items-center gap-1 bg-emerald-600 text-white hover:bg-emerald-700"${attr("disabled", !!actionLoading[domain.id], true)}>`);
          if (actionLoading[domain.id] === "activate") {
            $$renderer2.push("<!--[-->");
            Refresh_cw($$renderer2, { size: 10, class: "animate-spin" });
          } else {
            $$renderer2.push("<!--[!-->");
            Zap($$renderer2, { size: 10 });
          }
          $$renderer2.push(`<!--]--> ACTIVAR</button>`);
        } else {
          $$renderer2.push("<!--[!-->");
        }
        $$renderer2.push(`<!--]--> `);
        if (domain.is_active && !domain.nginx_configured) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<button class="btn-secondary btn-sm text-[10px] flex items-center gap-1"${attr("disabled", !!actionLoading[domain.id], true)}>`);
          if (actionLoading[domain.id] === "nginx") {
            $$renderer2.push("<!--[-->");
            Refresh_cw($$renderer2, { size: 10, class: "animate-spin" });
          } else {
            $$renderer2.push("<!--[!-->");
            Server($$renderer2, { size: 10 });
          }
          $$renderer2.push(`<!--]--> NGINX</button>`);
        } else {
          $$renderer2.push("<!--[!-->");
        }
        $$renderer2.push(`<!--]--> `);
        if (domain.is_active) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<button class="btn-sm text-[10px] flex items-center gap-1 bg-amber-100 text-amber-800 hover:bg-amber-200"${attr("disabled", !!actionLoading[domain.id], true)}>`);
          X($$renderer2, { size: 10 });
          $$renderer2.push(`<!----> OFF</button>`);
        } else {
          $$renderer2.push("<!--[!-->");
        }
        $$renderer2.push(`<!--]--> <button class="btn-danger btn-sm text-[10px] flex items-center gap-1">`);
        Trash_2($$renderer2, { size: 10 });
        $$renderer2.push(`<!----></button></div></td></tr>`);
      }
      $$renderer2.push(`<!--]--></tbody></table></div>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    if (customers.length > 0) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="card"><h3 class="section-heading mb-3 flex items-center gap-2">`);
      Info($$renderer2, { size: 14 });
      $$renderer2.push(`<!----> CUOTA DE DOMINIOS POR PLAN <span class="ml-auto text-[10px] text-gray-400 font-normal normal-case">-1 = ilimitado · 0 = sin dominios</span></h3> <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3"><!--[-->`);
      const each_array_5 = ensure_array_like(customers);
      for (let $$index_7 = 0, $$length = each_array_5.length; $$index_7 < $$length; $$index_7++) {
        let c = each_array_5[$$index_7];
        $$renderer2.push(`<div${attr_class(`flex items-center justify-between p-3 border border-border-light rounded-md ${stringify(!c.can_add && c.max_domains !== 0 ? "border-red-200 bg-red-50/50" : "")}`)}><div class="flex-1 min-w-0"><div class="text-sm font-medium truncate">${escape_html(c.company_name)}</div> <div class="text-xs text-gray-500 font-mono">${escape_html(c.plan_name)}</div></div> `);
        if (editingQuotaCustomerId === c.id) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="flex items-center gap-1 ml-2"><input type="number" min="-1" class="w-16 border border-border-light rounded px-1.5 py-0.5 text-xs font-mono text-center focus:outline-none focus:ring-1 focus:ring-primary"${attr("value", editingMaxDomains)}/> <button class="p-1 rounded text-emerald-600 hover:bg-emerald-50 disabled:opacity-50"${attr("disabled", savingQuota, true)} title="Guardar">`);
          Check($$renderer2, { size: 13 });
          $$renderer2.push(`<!----></button> <button class="p-1 rounded text-gray-400 hover:bg-gray-100" title="Cancelar">`);
          X($$renderer2, { size: 13 });
          $$renderer2.push(`<!----></button></div>`);
        } else {
          $$renderer2.push("<!--[!-->");
          $$renderer2.push(`<div class="flex items-center gap-2 ml-2"><div class="text-right">`);
          if (c.unlimited) {
            $$renderer2.push("<!--[-->");
            $$renderer2.push(`<span class="text-emerald-600 text-sm font-semibold">∞</span> <div class="text-[10px] text-gray-400">${escape_html(c.used_domains)} usado(s)</div>`);
          } else if (c.max_domains === 0) {
            $$renderer2.push("<!--[1-->");
            $$renderer2.push(`<span class="text-gray-400 text-xs">No disponible</span>`);
          } else {
            $$renderer2.push("<!--[!-->");
            $$renderer2.push(`<div${attr_class(`text-sm font-mono font-semibold ${stringify(c.can_add ? "text-emerald-600" : "text-red-600")}`)}>${escape_html(c.used_domains)}/${escape_html(c.max_domains)}</div> `);
            if (!c.can_add) {
              $$renderer2.push("<!--[-->");
              $$renderer2.push(`<div class="text-[10px] text-red-500 flex items-center gap-0.5">`);
              Triangle_alert($$renderer2, { size: 8 });
              $$renderer2.push(`<!----> Límite</div>`);
            } else {
              $$renderer2.push("<!--[!-->");
            }
            $$renderer2.push(`<!--]-->`);
          }
          $$renderer2.push(`<!--]--></div> <button class="p-1 rounded text-gray-400 hover:text-primary hover:bg-gray-100 transition-colors" title="Editar cuota del plan">`);
          Pencil($$renderer2, { size: 12 });
          $$renderer2.push(`<!----></button> <button class="p-1 rounded text-gray-400 hover:text-primary hover:bg-gray-100 transition-colors" title="Ver dominios vinculados">`);
          Chevron_down($$renderer2, {
            size: 12,
            class: expandedLinkedCustomerId === c.id ? "rotate-180 transition-transform" : "transition-transform"
          });
          $$renderer2.push(`<!----></button></div>`);
        }
        $$renderer2.push(`<!--]--></div> `);
        if (expandedLinkedCustomerId === c.id) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="mt-2 w-full border border-border-light rounded-md p-2 bg-gray-50">`);
          if (loadingLinkedByCustomer[c.id]) {
            $$renderer2.push("<!--[-->");
            $$renderer2.push(`<div class="text-xs text-gray-500 flex items-center gap-1">`);
            Refresh_cw($$renderer2, { size: 12, class: "animate-spin" });
            $$renderer2.push(`<!----> Cargando dominios vinculados...</div>`);
          } else if (linkedDomainsByCustomer[c.id]) {
            $$renderer2.push("<!--[1-->");
            const linked = linkedDomainsByCustomer[c.id];
            $$renderer2.push(`<div class="text-[11px] text-gray-600 mb-2 flex flex-wrap gap-2"><span>Total: <span class="font-semibold">${escape_html(linked.summary.total)}</span></span> <span>Base: <span class="font-semibold">${escape_html(linked.summary.base)}</span></span> <span>Custom: <span class="font-semibold">${escape_html(linked.summary.custom)}</span></span> <span>Sajet: <span class="font-semibold">${escape_html(linked.summary.odoo)}</span></span></div> `);
            if (linked.odoo_error) {
              $$renderer2.push("<!--[-->");
              $$renderer2.push(`<div class="text-[10px] text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1 mb-2">Sajet no disponible: ${escape_html(linked.odoo_error)}</div>`);
            } else {
              $$renderer2.push("<!--[!-->");
            }
            $$renderer2.push(`<!--]--> `);
            if (linked.domains.length === 0) {
              $$renderer2.push("<!--[-->");
              $$renderer2.push(`<div class="text-xs text-gray-500">Sin dominios vinculados detectados.</div>`);
            } else {
              $$renderer2.push("<!--[!-->");
              $$renderer2.push(`<div class="space-y-1 max-h-40 overflow-auto pr-1"><!--[-->`);
              const each_array_6 = ensure_array_like(linked.domains);
              for (let $$index_6 = 0, $$length2 = each_array_6.length; $$index_6 < $$length2; $$index_6++) {
                let d = each_array_6[$$index_6];
                $$renderer2.push(`<div class="text-xs bg-white border border-border-light rounded px-2 py-1.5"><div class="font-mono text-[11px] truncate">${escape_html(d.domain)}</div> <div class="mt-1 flex flex-wrap items-center gap-1"><!--[-->`);
                const each_array_7 = ensure_array_like(d.sources);
                for (let $$index_5 = 0, $$length3 = each_array_7.length; $$index_5 < $$length3; $$index_5++) {
                  let src = each_array_7[$$index_5];
                  $$renderer2.push(`<span${attr_class(`text-[10px] px-1.5 py-0.5 rounded ${sourceClass(src)}`)}>${escape_html(sourceLabel(src))}</span>`);
                }
                $$renderer2.push(`<!--]--> `);
                if (d.verification_status) {
                  $$renderer2.push("<!--[-->");
                  $$renderer2.push(`<span class="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-700">${escape_html(d.verification_status)}</span>`);
                } else {
                  $$renderer2.push("<!--[!-->");
                }
                $$renderer2.push(`<!--]--></div></div>`);
              }
              $$renderer2.push(`<!--]--></div>`);
            }
            $$renderer2.push(`<!--]-->`);
          } else {
            $$renderer2.push("<!--[!-->");
          }
          $$renderer2.push(`<!--]--></div>`);
        } else {
          $$renderer2.push("<!--[!-->");
        }
        $$renderer2.push(`<!--]-->`);
      }
      $$renderer2.push(`<!--]--></div></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function _page($$renderer) {
  Domains($$renderer);
}
export {
  _page as default
};
