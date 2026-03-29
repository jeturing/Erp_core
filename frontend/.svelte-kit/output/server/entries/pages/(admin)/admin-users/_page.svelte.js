import "clsx";
import { d as escape_html, f as derived } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/toast.js";
import { P as Plus } from "../../../../chunks/plus.js";
function AdminUsers($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let users = [];
    let activeCount = derived(() => users.filter((u) => u.is_active).length);
    let adminCount = derived(() => users.filter((u) => u.role === "admin" && u.is_active).length);
    $$renderer2.push(`<div class="space-y-6"><div class="flex items-center justify-between"><div><h1 class="page-title">USUARIOS ADMIN</h1> <p class="page-subtitle">Gestión de administradores, operadores y visores de la plataforma</p></div> <button class="btn-accent px-4 py-2 flex items-center gap-2">`);
    Plus($$renderer2, { size: 14 });
    $$renderer2.push(`<!----> NUEVO USUARIO</button></div> <div class="grid grid-cols-2 md:grid-cols-4 gap-4"><div class="stat-card card"><div class="stat-value">${escape_html(users.length)}</div> <div class="stat-label">Total Usuarios</div></div> <div class="stat-card card"><div class="stat-value">${escape_html(activeCount())}</div> <div class="stat-label">Activos</div></div> <div class="stat-card card"><div class="stat-value">${escape_html(adminCount())}</div> <div class="stat-label">Admins</div></div> <div class="stat-card card"><div class="stat-value">${escape_html(users.length - activeCount())}</div> <div class="stat-label">Inactivos</div></div></div> <div class="card p-0 overflow-hidden">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="p-8 text-center text-gray-500 text-sm">Cargando usuarios...</div>`);
    }
    $$renderer2.push(`<!--]--></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
function _page($$renderer) {
  AdminUsers($$renderer);
}
export {
  _page as default
};
