import "clsx";
import { c as attr } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { A as Arrow_right_left } from "../../../../chunks/arrow-right-left.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
function Dispersion($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let refreshing = false;
    $$renderer2.push(`<div class="p-6 space-y-6"><div class="flex items-center justify-between"><div><h1 class="page-title flex items-center gap-2">`);
    Arrow_right_left($$renderer2, { size: 22 });
    $$renderer2.push(`<!----> Dispersión Mercury</h1> <p class="page-subtitle mt-1">Pagos directos a proveedores vía Mercury Banking — requieren autorización 4-ojos</p></div> <div class="flex items-center gap-2"><button class="btn-secondary flex items-center gap-1 text-sm"${attr("disabled", refreshing, true)}>`);
    Refresh_cw($$renderer2, { size: 14, class: "" });
    $$renderer2.push(`<!----> Actualizar</button> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-center py-16 text-gray-400">Cargando sistema de dispersión…</div>`);
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
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
function _page($$renderer) {
  Dispersion($$renderer);
}
export {
  _page as default
};
