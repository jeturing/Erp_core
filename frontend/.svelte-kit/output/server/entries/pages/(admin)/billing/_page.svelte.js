import "clsx";
import { c as attr } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/tenants.js";
import "../../../../chunks/toast.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
function Billing($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let loading = true;
    $$renderer2.push(`<div class="p-6 lg:p-8 space-y-6"><div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"><div><h1 class="page-title">BILLING</h1> <p class="page-subtitle mt-1">Métricas financieras, suscripciones del canal y distribución de planes</p></div> <button class="btn btn-secondary btn-sm"${attr("disabled", loading, true)}>`);
    Refresh_cw($$renderer2, { size: 13, class: "animate-spin" });
    $$renderer2.push(`<!----> Actualizar</button></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="py-24 flex justify-center"><div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin"></div></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Billing($$renderer);
}
export {
  _page as default
};
