import "clsx";
import { c as attr } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { U as Users } from "../../../../chunks/users.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
import { Z as Zap } from "../../../../chunks/zap.js";
function Seats($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let loading = true;
    let syncing = false;
    let subFilter = "";
    $$renderer2.push(`<div class="p-6 space-y-6"><div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"><div><h1 class="page-title flex items-center gap-2">`);
    Users($$renderer2, { size: 24 });
    $$renderer2.push(`<!----> Seats</h1> <p class="page-subtitle">High Water Mark, eventos de usuarios y sincronización Stripe</p></div> <div class="flex gap-2"><button class="btn-secondary flex items-center gap-2"${attr("disabled", loading, true)}>`);
    Refresh_cw($$renderer2, { size: 14, class: "animate-spin" });
    $$renderer2.push(`<!----> Actualizar</button> <button class="btn-accent flex items-center gap-2"${attr("disabled", syncing, true)}>`);
    Zap($$renderer2, { size: 14, class: "" });
    $$renderer2.push(`<!----> Sync Stripe</button></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="flex gap-3"><div class="relative flex-1 max-w-xs"><input type="text"${attr("value", subFilter)} placeholder="Subscription ID..." class="input w-full"/></div> <button class="btn-secondary btn-sm">Filtrar</button></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-center py-16 text-gray-500"><div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin mx-auto"></div> <p class="mt-3">Cargando datos de seats...</p></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Seats($$renderer);
}
export {
  _page as default
};
