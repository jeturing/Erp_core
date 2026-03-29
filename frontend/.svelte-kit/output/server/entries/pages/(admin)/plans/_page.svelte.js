import "clsx";
import "../../../../chunks/client.js";
import { P as Plus } from "../../../../chunks/plus.js";
function Plans($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    $$renderer2.push(`<div class="p-6 space-y-6"><div class="flex items-center justify-between"><div><h1 class="page-title">Gestión de Planes</h1> <p class="page-subtitle">Administra planes, precios y facturación por usuario</p></div> <button class="btn-accent flex items-center gap-2">`);
    Plus($$renderer2, { size: 16 });
    $$renderer2.push(`<!----> Nuevo Plan</button></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="flex justify-center py-12"><div class="animate-spin rounded-full h-8 w-8 border-2 border-terracotta border-t-transparent"></div></div>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
function _page($$renderer) {
  Plans($$renderer);
}
export {
  _page as default
};
