import "clsx";
import { h as sanitize_props, i as spread_props, j as slot, k as attr_class, e as ensure_array_like, d as escape_html, b as stringify } from "../../../../chunks/index2.js";
import { a as api } from "../../../../chunks/client.js";
import "../../../../chunks/tenants.js";
import "../../../../chunks/darkMode.js";
import { t as toasts } from "../../../../chunks/toast.js";
import { F as File_text } from "../../../../chunks/file-text.js";
import { P as Plus } from "../../../../chunks/plus.js";
import { I as Icon } from "../../../../chunks/Icon.js";
import { T as Trash_2 } from "../../../../chunks/trash-2.js";
function Square_pen($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    [
      "path",
      {
        "d": "M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
      }
    ],
    [
      "path",
      {
        "d": "M18.375 2.625a1 1 0 0 1 3 3l-9.013 9.014a2 2 0 0 1-.853.505l-2.873.84a.5.5 0 0 1-.62-.62l.84-2.873a2 2 0 0 1 .506-.852z"
      }
    ]
  ];
  Icon($$renderer, spread_props([
    { name: "square-pen" },
    $$sanitized_props,
    {
      /**
       * @component @name SquarePen
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMTIgM0g1YTIgMiAwIDAgMC0yIDJ2MTRhMiAyIDAgMCAwIDIgMmgxNGEyIDIgMCAwIDAgMi0ydi03IiAvPgogIDxwYXRoIGQ9Ik0xOC4zNzUgMi42MjVhMSAxIDAgMCAxIDMgM2wtOS4wMTMgOS4wMTRhMiAyIDAgMCAxLS44NTMuNTA1bC0yLjg3My44NGEuNS41IDAgMCAxLS42Mi0uNjJsLjg0LTIuODczYTIgMiAwIDAgMSAuNTA2LS44NTJ6IiAvPgo8L3N2Zz4K) - https://lucide.dev/icons/square-pen
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
const agreementsApi = {
  // ── Templates (Admin) ──
  async listTemplates(params) {
    const qs = new URLSearchParams();
    if (params?.agreement_type) qs.set("agreement_type", params.agreement_type);
    if (params?.target) qs.set("target", params.target);
    if (params?.active_only !== void 0) qs.set("active_only", String(params.active_only));
    const query = qs.toString();
    return api.get(`/api/agreements/templates${query ? `?${query}` : ""}`);
  },
  async getTemplate(id) {
    return api.get(`/api/agreements/templates/${id}`);
  },
  async createTemplate(data) {
    return api.post("/api/agreements/templates", data);
  },
  async updateTemplate(id, data) {
    return api.put(`/api/agreements/templates/${id}`, data);
  },
  async deleteTemplate(id) {
    return api.delete(`/api/agreements/templates/${id}`);
  },
  // ── Required agreements (partner/customer flow) ──
  async getRequired(targetType) {
    return api.get(`/api/agreements/required/${targetType}`);
  },
  // ── Signing ──
  async sign(data) {
    return api.post("/api/agreements/sign", data);
  },
  // ── Signed agreements ──
  async listSigned(params) {
    const qs = new URLSearchParams();
    if (params?.partner_id) qs.set("partner_id", String(params.partner_id));
    if (params?.customer_id) qs.set("customer_id", String(params.customer_id));
    const query = qs.toString();
    return api.get(`/api/agreements/signed${query ? `?${query}` : ""}`);
  },
  getPdfUrl(id) {
    return `/api/agreements/signed/${id}/pdf`;
  }
};
function Agreements($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let templates = [];
    let loading = true;
    let filterType = "";
    let filterTarget = "";
    const typeLabels = {
      nda: "NDA",
      service_agreement: "Acuerdo de Servicio",
      terms_of_service: "Términos de Servicio",
      privacy_policy: "Política de Privacidad"
    };
    const targetLabels = { partner: "Partner", customer: "Cliente", both: "Ambos" };
    async function loadTemplates() {
      loading = true;
      try {
        const params = {};
        if (filterType) ;
        if (filterTarget) ;
        const res = await agreementsApi.listTemplates(params);
        templates = res.items;
      } catch (err) {
        toasts.error(err instanceof Error ? err.message : "Error cargando plantillas");
      } finally {
        loading = false;
      }
    }
    $$renderer2.push(`<div class="p-6 space-y-6"><div class="flex items-center justify-between"><div><h1 class="page-title flex items-center gap-2">`);
    File_text($$renderer2, { class: "w-6 h-6 text-terracotta" });
    $$renderer2.push(`<!----> Acuerdos y Contratos</h1> <p class="page-subtitle">Gestiona plantillas de NDA, TOS y acuerdos de servicio</p></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<button class="btn-primary flex items-center gap-2 text-sm">`);
      Plus($$renderer2, { class: "w-4 h-4" });
      $$renderer2.push(`<!----> Nueva Plantilla</button>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="flex gap-1 border-b border-gray-200"><button${attr_class(`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${stringify(
      "border-terracotta text-terracotta"
    )}`)}>Plantillas</button> <button${attr_class(`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${stringify("border-transparent text-gray-500 hover:text-gray-700")}`)}>Firmados</button></div> `);
    {
      $$renderer2.push("<!--[1-->");
      $$renderer2.push(`<div class="flex gap-3 flex-wrap">`);
      $$renderer2.select(
        {
          class: "input px-3 py-2 text-sm",
          value: filterType,
          onchange: loadTemplates
        },
        ($$renderer3) => {
          $$renderer3.option({ value: "" }, ($$renderer4) => {
            $$renderer4.push(`Todos los tipos`);
          });
          $$renderer3.option({ value: "nda" }, ($$renderer4) => {
            $$renderer4.push(`NDA`);
          });
          $$renderer3.option({ value: "service_agreement" }, ($$renderer4) => {
            $$renderer4.push(`Acuerdo de Servicio`);
          });
          $$renderer3.option({ value: "terms_of_service" }, ($$renderer4) => {
            $$renderer4.push(`Términos de Servicio`);
          });
          $$renderer3.option({ value: "privacy_policy" }, ($$renderer4) => {
            $$renderer4.push(`Política de Privacidad`);
          });
        }
      );
      $$renderer2.push(` `);
      $$renderer2.select(
        {
          class: "input px-3 py-2 text-sm",
          value: filterTarget,
          onchange: loadTemplates
        },
        ($$renderer3) => {
          $$renderer3.option({ value: "" }, ($$renderer4) => {
            $$renderer4.push(`Todos los destinatarios`);
          });
          $$renderer3.option({ value: "partner" }, ($$renderer4) => {
            $$renderer4.push(`Partner`);
          });
          $$renderer3.option({ value: "customer" }, ($$renderer4) => {
            $$renderer4.push(`Cliente`);
          });
          $$renderer3.option({ value: "both" }, ($$renderer4) => {
            $$renderer4.push(`Ambos`);
          });
        }
      );
      $$renderer2.push(`</div> <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">`);
      if (loading) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="p-8 text-center text-gray-400">Cargando...</div>`);
      } else if (templates.length === 0) {
        $$renderer2.push("<!--[1-->");
        $$renderer2.push(`<div class="p-8 text-center text-gray-400">No hay plantillas registradas</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<table class="w-full text-sm"><thead><tr class="border-b border-gray-100 bg-gray-50/50"><th class="text-left px-4 py-3 font-semibold text-gray-600">Título</th><th class="text-left px-4 py-3 font-semibold text-gray-600">Tipo</th><th class="text-left px-4 py-3 font-semibold text-gray-600">Destinatario</th><th class="text-center px-4 py-3 font-semibold text-gray-600">Versión</th><th class="text-center px-4 py-3 font-semibold text-gray-600">Estado</th><th class="text-center px-4 py-3 font-semibold text-gray-600">Obligatoria</th><th class="text-right px-4 py-3 font-semibold text-gray-600">Acciones</th></tr></thead><tbody><!--[-->`);
        const each_array = ensure_array_like(templates);
        for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
          let t = each_array[$$index];
          $$renderer2.push(`<tr class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors"><td class="px-4 py-3 font-medium text-text-primary">${escape_html(t.title)}</td><td class="px-4 py-3"><span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700">${escape_html(typeLabels[t.agreement_type] || t.agreement_type)}</span></td><td class="px-4 py-3 text-gray-600">${escape_html(targetLabels[t.target] || t.target)}</td><td class="px-4 py-3 text-center text-gray-500">${escape_html(t.version)}</td><td class="px-4 py-3 text-center"><span${attr_class(`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${stringify(t.is_active ? "bg-green-50 text-green-700" : "bg-gray-100 text-gray-500")}`)}>${escape_html(t.is_active ? "Activa" : "Inactiva")}</span></td><td class="px-4 py-3 text-center text-gray-500">${escape_html(t.is_required ? "Sí" : "No")}</td><td class="px-4 py-3 text-right"><div class="flex items-center justify-end gap-1"><button class="p-1.5 text-gray-400 hover:text-terracotta rounded transition-colors" title="Editar">`);
          Square_pen($$renderer2, { class: "w-4 h-4" });
          $$renderer2.push(`<!----></button> <button class="p-1.5 text-gray-400 hover:text-red-600 rounded transition-colors" title="Eliminar">`);
          Trash_2($$renderer2, { class: "w-4 h-4" });
          $$renderer2.push(`<!----></button></div></td></tr>`);
        }
        $$renderer2.push(`<!--]--></tbody></table>`);
      }
      $$renderer2.push(`<!--]--></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Agreements($$renderer);
}
export {
  _page as default
};
