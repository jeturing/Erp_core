import "clsx";
import { c as attr, d as escape_html } from "../../../../chunks/index2.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/root.js";
import "../../../../chunks/state.svelte.js";
function Login($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let email = "";
    let password = "";
    let loading = false;
    $$renderer2.push(`<div class="min-h-screen flex"><div class="hidden lg:flex lg:w-1/2 bg-charcoal flex-col justify-between p-12"><div><div class="flex items-center gap-3 mb-16"><div class="w-10 h-10 bg-terracotta flex items-center justify-center"><span class="text-white font-bold text-xl">S</span></div> <span class="text-white font-bold text-lg tracking-widest uppercase">SAJET ERP</span></div> <div class="mt-16"><p class="text-gray-400 text-xs uppercase tracking-[0.15em] mb-6">Plataforma Empresarial</p> <h2 class="text-white text-4xl font-bold leading-tight mb-8">Gestión inteligente<br/>para tu empresa.</h2> <p class="text-gray-500 text-sm leading-relaxed max-w-sm">Controla tu empresa de una forma facil intuitiva y agil.</p></div></div> <div><p class="text-gray-600 text-xs">© 2026 Jeturing inc. Todos los derechos reservados.</p></div></div> <div class="w-full lg:w-1/2 bg-bg-page flex items-center justify-center p-8"><div class="w-full max-w-sm"><div class="flex lg:hidden items-center gap-3 mb-10"><div class="w-9 h-9 bg-terracotta flex items-center justify-center"><span class="text-white font-bold text-lg">S</span></div> <span class="font-bold text-base tracking-widest uppercase text-text-primary">SAJET ERP</span></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<h2 class="text-2xl font-bold text-text-primary mb-1">Iniciar Sesión</h2> <p class="text-sm text-gray-500 mb-8">Accede al panel de administración</p> <form class="space-y-5"><div><label class="label" for="email">Usuario o Email</label> <input id="email" type="text" class="input w-full px-3 py-2" placeholder="correo@empresa.com"${attr("value", email)} required="" autocomplete="username"/> <p class="text-[11px] text-gray-400 mt-1">${escape_html(email.includes("@") ? "Acceso como partner, empresa o admin" : "Acceso administrativo")}</p></div> <div><label class="label" for="password">Contraseña</label> <div class="relative"><input id="password"${attr("type", "password")} class="input w-full px-3 py-2 pr-10" placeholder="••••••••"${attr("value", password)} required="" autocomplete="current-password"/> <button type="button" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"${attr("aria-label", "Mostrar contraseña")}>`);
      {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`);
      }
      $$renderer2.push(`<!--]--></button></div></div> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> <button type="submit" class="btn-primary w-full py-3 mt-2 disabled:opacity-60"${attr("disabled", loading, true)}>${escape_html("Ingresar")}</button> <div class="flex items-center justify-between text-xs mt-3"><a href="/signup" class="text-[#C05A3C] hover:underline">Crear cuenta</a> <a href="/recover-account" class="text-[#C05A3C] hover:underline">Recuperar cuenta</a></div></form>`);
    }
    $$renderer2.push(`<!--]--></div></div></div>`);
  });
}
function _page($$renderer) {
  Login($$renderer);
}
export {
  _page as default
};
