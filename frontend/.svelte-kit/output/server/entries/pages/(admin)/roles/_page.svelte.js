import "clsx";
import { d as escape_html, f as derived } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/toast.js";
import { P as Plus } from "../../../../chunks/plus.js";
function Roles($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let roles = [];
    let permCatalog = {};
    let totalPermsAvailable = derived(() => Object.values(permCatalog).reduce((sum, m) => sum + Object.keys(m.permissions).length, 0));
    $$renderer2.push(`<div class="space-y-6"><div class="flex items-center justify-between"><div><h1 class="page-title">GESTIÓN DE ROLES</h1> <p class="page-subtitle">Control de permisos, acceso y asignación de tenants</p></div> <button class="btn-accent px-4 py-2 flex items-center gap-2">`);
    Plus($$renderer2, { size: 14 });
    $$renderer2.push(`<!----> NUEVO ROL</button></div> <div class="grid grid-cols-2 md:grid-cols-4 gap-4"><div class="stat-card"><div class="text-xs text-gray-400 uppercase tracking-wide">Roles</div> <div class="text-2xl font-bold mt-1">${escape_html(roles.length)}</div></div> <div class="stat-card"><div class="text-xs text-gray-400 uppercase tracking-wide">Sistema</div> <div class="text-2xl font-bold mt-1">${escape_html(roles.filter((r) => r.system).length)}</div></div> <div class="stat-card"><div class="text-xs text-gray-400 uppercase tracking-wide">Custom</div> <div class="text-2xl font-bold mt-1">${escape_html(roles.filter((r) => !r.system).length)}</div></div> <div class="stat-card"><div class="text-xs text-gray-400 uppercase tracking-wide">Permisos Disp.</div> <div class="text-2xl font-bold mt-1">${escape_html(totalPermsAvailable())}</div></div></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="card p-12 text-center text-gray-500">Cargando roles...</div>`);
    }
    $$renderer2.push(`<!--]--></div>  `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
function _page($$renderer) {
  Roles($$renderer);
}
export {
  _page as default
};
