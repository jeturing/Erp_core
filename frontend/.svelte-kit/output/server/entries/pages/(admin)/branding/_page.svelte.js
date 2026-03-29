import "clsx";
import { c as attr, d as escape_html } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { P as Palette } from "../../../../chunks/palette.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
import { P as Plus } from "../../../../chunks/plus.js";
function Branding($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let profiles = [];
    let loading = true;
    $$renderer2.push(`<div class="p-6 space-y-6"><div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"><div><h1 class="page-title flex items-center gap-2">`);
    Palette($$renderer2, { size: 24 });
    $$renderer2.push(`<!----> White-Label Branding</h1> <p class="page-subtitle">Perfiles de marca para partners — personalización completa</p></div> <div class="flex gap-2"><button class="btn-secondary flex items-center gap-2"${attr("disabled", loading, true)}>`);
    Refresh_cw($$renderer2, { size: 14, class: "animate-spin" });
    $$renderer2.push(`<!----> Actualizar</button> <button class="btn-accent flex items-center gap-2">`);
    Plus($$renderer2, { size: 16 });
    $$renderer2.push(`<!----> Nuevo Perfil</button></div></div> <div class="grid grid-cols-2 sm:grid-cols-3 gap-4"><div class="stat-card"><span class="stat-label">Total Perfiles</span> <span class="stat-value">${escape_html(profiles.length)}</span></div> <div class="stat-card"><span class="stat-label">Activos</span> <span class="stat-value text-success">${escape_html(profiles.filter((p) => p.is_active).length)}</span></div> <div class="stat-card"><span class="stat-label">Con CSS Custom</span> <span class="stat-value text-info">${escape_html(profiles.filter((p) => p.custom_css).length)}</span></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-center py-16 text-gray-500"><div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin mx-auto"></div></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Branding($$renderer);
}
export {
  _page as default
};
