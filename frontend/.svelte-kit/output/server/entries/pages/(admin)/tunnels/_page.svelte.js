import "clsx";
import { h as sanitize_props, i as spread_props, j as slot, c as attr, d as escape_html, e as ensure_array_like, f as derived } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/tenants.js";
import "../../../../chunks/toast.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
import { W as Wifi } from "../../../../chunks/wifi.js";
import { W as Wifi_off } from "../../../../chunks/wifi-off.js";
import { G as Globe } from "../../../../chunks/globe.js";
import { I as Icon } from "../../../../chunks/Icon.js";
function Circle_plus($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["circle", { "cx": "12", "cy": "12", "r": "10" }],
    ["path", { "d": "M8 12h8" }],
    ["path", { "d": "M12 8v8" }]
  ];
  Icon($$renderer, spread_props([
    { name: "circle-plus" },
    $$sanitized_props,
    {
      /**
       * @component @name CirclePlus
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCIgLz4KICA8cGF0aCBkPSJNOCAxMmg4IiAvPgogIDxwYXRoIGQ9Ik0xMiA4djgiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/circle-plus
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
function Tunnels($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let tunnels = [];
    let loading = true;
    let totalTunnels = 0;
    let stats = { healthy: 0, down: 0, inactive: 0, total_dns_cnames: 0 };
    let searchQuery = "";
    let filterStatus = "all";
    let deployments = [];
    let creatingTunnel = false;
    let createName = "";
    let createHostname = "";
    let createDomain = "";
    let createDeploymentId = "";
    let authorizedDomains = [];
    let filteredTunnels = derived(() => (tunnels || []).filter((t) => {
      const matchesStatus = filterStatus === "all";
      return matchesStatus;
    }));
    $$renderer2.push(`<div class="space-y-6"><div class="flex items-center justify-between flex-wrap gap-4"><div><h1 class="page-title">CLOUDFLARE TUNNELS</h1> <p class="page-subtitle">Gestión de túneles — vincular tenants &amp; Stripe</p></div> <button class="btn-secondary px-4 py-2 flex items-center gap-2"${attr("disabled", loading, true)}>`);
    Refresh_cw($$renderer2, { size: 14, class: "animate-spin" });
    $$renderer2.push(`<!----> ACTUALIZAR</button></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="grid grid-cols-2 md:grid-cols-5 gap-4"><div class="stat-card card"><div class="stat-value text-2xl font-bold">${escape_html(totalTunnels)}</div> <div class="stat-label text-xs text-gray-500 uppercase">Total Tunnels</div></div> <div class="stat-card card"><div class="stat-value text-2xl font-bold text-emerald-600">${escape_html(stats.healthy)}</div> <div class="stat-label text-xs text-gray-500 uppercase flex items-center gap-1">`);
    Wifi($$renderer2, { size: 12, class: "text-emerald-500" });
    $$renderer2.push(`<!----> Healthy</div></div> <div class="stat-card card"><div class="stat-value text-2xl font-bold text-red-600">${escape_html(stats.down)}</div> <div class="stat-label text-xs text-gray-500 uppercase flex items-center gap-1">`);
    Wifi_off($$renderer2, { size: 12, class: "text-red-500" });
    $$renderer2.push(`<!----> Down</div></div> <div class="stat-card card"><div class="stat-value text-2xl font-bold text-amber-600">${escape_html(stats.inactive)}</div> <div class="stat-label text-xs text-gray-500 uppercase">Inactive</div></div> <div class="stat-card card"><div class="stat-value text-2xl font-bold text-blue-600">${escape_html(stats.total_dns_cnames)}</div> <div class="stat-label text-xs text-gray-500 uppercase flex items-center gap-1">`);
    Globe($$renderer2, { size: 12, class: "text-blue-500" });
    $$renderer2.push(`<!----> DNS CNAMEs</div></div></div> <div class="card p-4 space-y-3"><div class="flex items-center justify-between gap-2 flex-wrap"><h3 class="text-sm font-semibold uppercase text-gray-700">Crear nuevo tunnel</h3> <span class="text-xs text-gray-400">Cloudflare + DNS opcional + vínculo a deployment</span></div> <div class="grid grid-cols-1 md:grid-cols-4 gap-3"><input class="input" type="text"${attr("value", createName)} placeholder="Nombre tunnel (ej: node-rd-01)"/> <input class="input" type="text"${attr("value", createHostname)} placeholder="Hostname (ej: nodo1)"/> `);
    $$renderer2.select({ class: "input", value: createDomain }, ($$renderer3) => {
      $$renderer3.option({ value: "" }, ($$renderer4) => {
        $$renderer4.push(`Sin DNS automático`);
      });
      $$renderer3.push(`<!--[-->`);
      const each_array = ensure_array_like(authorizedDomains);
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let d = each_array[$$index];
        $$renderer3.option({ value: d.domain }, ($$renderer4) => {
          $$renderer4.push(`${escape_html(d.domain)}`);
        });
      }
      $$renderer3.push(`<!--]-->`);
    });
    $$renderer2.push(` `);
    $$renderer2.select({ class: "input", value: createDeploymentId }, ($$renderer3) => {
      $$renderer3.option({ value: "" }, ($$renderer4) => {
        $$renderer4.push(`Sin vincular deployment`);
      });
      $$renderer3.push(`<!--[-->`);
      const each_array_1 = ensure_array_like(deployments);
      for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
        let dep = each_array_1[$$index_1];
        $$renderer3.option({ value: dep.id }, ($$renderer4) => {
          $$renderer4.push(`${escape_html(dep.subdomain)} (${escape_html(dep.company_name || "tenant")})`);
        });
      }
      $$renderer3.push(`<!--]-->`);
    });
    $$renderer2.push(`</div> <div class="flex justify-end"><button class="btn-accent px-4 py-2 text-sm flex items-center gap-2 disabled:opacity-50"${attr("disabled", creatingTunnel, true)}>`);
    {
      $$renderer2.push("<!--[!-->");
      Circle_plus($$renderer2, { size: 12 });
    }
    $$renderer2.push(`<!--]--> CREAR TUNNEL</button></div></div> <div class="flex items-center gap-4 flex-wrap"><input type="text" placeholder="Buscar por nombre, ID o subdominio..." class="input flex-1 min-w-[200px]"${attr("value", searchQuery)}/> `);
    $$renderer2.select({ class: "input w-auto", value: filterStatus }, ($$renderer3) => {
      $$renderer3.option({ value: "all" }, ($$renderer4) => {
        $$renderer4.push(`Todos los estados`);
      });
      $$renderer3.option({ value: "healthy" }, ($$renderer4) => {
        $$renderer4.push(`Healthy`);
      });
      $$renderer3.option({ value: "down" }, ($$renderer4) => {
        $$renderer4.push(`Down`);
      });
      $$renderer3.option({ value: "inactive" }, ($$renderer4) => {
        $$renderer4.push(`Inactive`);
      });
    });
    $$renderer2.push(` <span class="text-xs text-gray-500">${escape_html(filteredTunnels().length)} de ${escape_html(totalTunnels)}</span></div> <div class="card p-0 overflow-hidden">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="p-8 text-center text-gray-500 text-sm">`);
      Refresh_cw($$renderer2, { size: 20, class: "animate-spin mx-auto mb-2" });
      $$renderer2.push(`<!----> Cargando tunnels desde Cloudflare API...</div>`);
    }
    $$renderer2.push(`<!--]--></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
function _page($$renderer) {
  Tunnels($$renderer);
}
export {
  _page as default
};
