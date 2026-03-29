import "clsx";
import { c as attr } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/root.js";
import "../../../../chunks/state.svelte.js";
function PartnerSignup($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let loading = false;
    let form = {
      company_name: "",
      contact_name: "",
      contact_email: "",
      phone: "",
      country: "DO",
      password: "",
      password_confirm: ""
    };
    $$renderer2.push(`<div class="min-h-screen bg-bg-page flex items-center justify-center p-6"><div class="w-full max-w-2xl bg-white border border-border-light rounded-lg p-8 shadow-soft"><h1 class="text-2xl font-bold text-text-primary mb-3">Programa de Socios SAJET</h1> <p class="text-sm text-gray-600 mb-6">Crea tu cuenta de socio para gestionar leads, comisiones y clientes.</p> `);
    {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<form class="space-y-4"><div class="grid sm:grid-cols-2 gap-4"><div><label class="label" for="company_name">Empresa *</label> <input id="company_name" class="input w-full"${attr("value", form.company_name)} required=""/></div> <div><label class="label" for="contact_name">Nombre de contacto *</label> <input id="contact_name" class="input w-full"${attr("value", form.contact_name)} required=""/></div></div> <div class="grid sm:grid-cols-2 gap-4"><div><label class="label" for="contact_email">Email *</label> <input id="contact_email" type="email" class="input w-full"${attr("value", form.contact_email)} required=""/></div> <div><label class="label" for="phone">Teléfono</label> <input id="phone" class="input w-full"${attr("value", form.phone)}/></div></div> <div><label class="label" for="country">País</label> <input id="country" class="input w-full"${attr("value", form.country)}/></div> <div class="grid sm:grid-cols-2 gap-4"><div><label class="label" for="password">Contraseña *</label> <input id="password" type="password" class="input w-full"${attr("value", form.password)} minlength="8" required=""/></div> <div><label class="label" for="password_confirm">Confirmar contraseña *</label> <input id="password_confirm" type="password" class="input w-full"${attr("value", form.password_confirm)} minlength="8" required=""/></div></div> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> <div class="grid gap-4 sm:grid-cols-2"><button class="btn-primary py-3 inline-flex items-center justify-center gap-2" type="submit"${attr("disabled", loading, true)}>`);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> Crear cuenta partner</button> <button class="btn-secondary py-3" type="button">Ya tengo cuenta</button></div></form>`);
    }
    $$renderer2.push(`<!--]--> <div class="mt-6 text-xs text-gray-500">Si ya recibiste invitación, inicia sesión con tu email y completa onboarding.</div></div></div>`);
  });
}
function _page($$renderer) {
  PartnerSignup($$renderer);
}
export {
  _page as default
};
