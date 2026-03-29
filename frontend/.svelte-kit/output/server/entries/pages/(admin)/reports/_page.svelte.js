import "clsx";
import { c as attr } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { C as Chart_no_axes_column } from "../../../../chunks/chart-no-axes-column.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
function Reports($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let loading = true;
    $$renderer2.push(`<div class="p-6 space-y-6"><div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"><div><h1 class="page-title flex items-center gap-2">`);
    Chart_no_axes_column($$renderer2, { size: 24 });
    $$renderer2.push(`<!----> Reportes</h1> <p class="page-subtitle">Vista consolidada de KPIs del negocio `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></p></div> <button class="btn-secondary flex items-center gap-2"${attr("disabled", loading, true)}>`);
    Refresh_cw($$renderer2, { size: 14, class: "animate-spin" });
    $$renderer2.push(`<!----> Actualizar</button></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="card p-10 text-center text-gray-500">`);
      Refresh_cw($$renderer2, { size: 24, class: "animate-spin mx-auto mb-3" });
      $$renderer2.push(`<!----> Cargando reportes...</div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Reports($$renderer);
}
export {
  _page as default
};
