import "clsx";
import { c as attr } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/tenants.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { U as Users } from "../../../../chunks/users.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
import { Z as Zap } from "../../../../chunks/zap.js";
import { S as Search } from "../../../../chunks/search.js";
function Seats($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let overviewLoading = true;
    let search = "";
    let syncing = false;
    $$renderer2.push(`<div class="p-6 space-y-6"><div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"><div><h1 class="page-title flex items-center gap-2">`);
    Users($$renderer2, { size: 24 });
    $$renderer2.push(`<!----> Seats</h1> <p class="page-subtitle">Asientos por tenant, agrupados por partner y sincronización con Stripe</p></div> <div class="flex gap-2"><button class="btn-secondary flex items-center gap-2"${attr("disabled", overviewLoading, true)}>`);
    Refresh_cw($$renderer2, { size: 14, class: "animate-spin" });
    $$renderer2.push(`<!----> Actualizar</button> <button class="btn-accent flex items-center gap-2"${attr("disabled", syncing, true)}>`);
    Zap($$renderer2, { size: 14, class: "" });
    $$renderer2.push(`<!----> Sync Stripe</button></div></div> <div class="relative max-w-xl">`);
    Search($$renderer2, {
      size: 16,
      class: "absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"
    });
    $$renderer2.push(`<!----> <input type="text"${attr("value", search)} placeholder="Buscar por tenant, partner, plan, email o subscription..." class="input pl-10 w-full"/></div> <div class="grid grid-cols-1 xl:grid-cols-3 gap-6"><div class="xl:col-span-1 space-y-4">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="card p-8 text-center text-gray-500">Cargando tenants...</div>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="xl:col-span-2 space-y-6">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-center py-16 text-gray-500"><div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin mx-auto"></div> <p class="mt-3">Cargando datos de seats...</p></div>`);
    }
    $$renderer2.push(`<!--]--></div></div></div>`);
  });
}
function _page($$renderer) {
  Seats($$renderer);
}
export {
  _page as default
};
