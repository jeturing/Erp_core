import "clsx";
import { c as attr, e as ensure_array_like, d as escape_html } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { M as Mail } from "../../../../chunks/mail.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
import { S as Search } from "../../../../chunks/search.js";
import { F as Funnel } from "../../../../chunks/funnel.js";
function Communications($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let loading = true;
    let search = "";
    let typeFilter = "";
    let statusFilter = "";
    const EMAIL_TYPE_LABELS = {
      tenant_credentials: "Credenciales Tenant",
      password_reset: "Reset Contraseña",
      commission_notification: "Comisión",
      quotation: "Cotización",
      work_order_completion: "Work Order",
      generic: "Genérico"
    };
    $$renderer2.push(`<div class="p-6 space-y-6"><div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"><div><h1 class="page-title flex items-center gap-2">`);
    Mail($$renderer2, { size: 24 });
    $$renderer2.push(`<!----> Comunicaciones</h1> <p class="page-subtitle">Historial de emails transaccionales enviados por la plataforma</p></div> <button class="btn-secondary flex items-center gap-2"${attr("disabled", loading, true)}>`);
    Refresh_cw($$renderer2, { size: 14, class: "animate-spin" });
    $$renderer2.push(`<!----> Actualizar</button></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="card p-4"><div class="flex flex-wrap gap-3"><div class="flex items-center gap-2 flex-1 min-w-[200px]">`);
    Search($$renderer2, { size: 14, class: "text-gray-500 flex-shrink-0" });
    $$renderer2.push(`<!----> <input type="text" placeholder="Buscar por destinatario..."${attr("value", search)} class="input-field flex-1 text-sm"/></div> <div class="flex items-center gap-2">`);
    Funnel($$renderer2, { size: 14, class: "text-gray-500 flex-shrink-0" });
    $$renderer2.push(`<!----> `);
    $$renderer2.select({ value: typeFilter, class: "input-field text-sm" }, ($$renderer3) => {
      $$renderer3.option({ value: "" }, ($$renderer4) => {
        $$renderer4.push(`Todos los tipos`);
      });
      $$renderer3.push(`<!--[-->`);
      const each_array = ensure_array_like(Object.entries(EMAIL_TYPE_LABELS));
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let [key, label] = each_array[$$index];
        $$renderer3.option({ value: key }, ($$renderer4) => {
          $$renderer4.push(`${escape_html(label)}`);
        });
      }
      $$renderer3.push(`<!--]-->`);
    });
    $$renderer2.push(`</div> <div class="flex items-center gap-2">`);
    $$renderer2.select({ value: statusFilter, class: "input-field text-sm" }, ($$renderer3) => {
      $$renderer3.option({ value: "" }, ($$renderer4) => {
        $$renderer4.push(`Todos los estados`);
      });
      $$renderer3.option({ value: "sent" }, ($$renderer4) => {
        $$renderer4.push(`Enviado`);
      });
      $$renderer3.option({ value: "failed" }, ($$renderer4) => {
        $$renderer4.push(`Fallido`);
      });
    });
    $$renderer2.push(`</div> <button class="btn-primary text-sm">Buscar</button></div></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="card p-8 text-center text-gray-500">`);
      Refresh_cw($$renderer2, { size: 20, class: "animate-spin mx-auto mb-2" });
      $$renderer2.push(`<!----> Cargando historial...</div>`);
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Communications($$renderer);
}
export {
  _page as default
};
