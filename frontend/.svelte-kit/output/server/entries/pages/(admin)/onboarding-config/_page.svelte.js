import "clsx";
import { c as attr, b as stringify } from "../../../../chunks/index2.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { S as Settings } from "../../../../chunks/settings.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
import { S as Save } from "../../../../chunks/save.js";
import { L as Loader_circle } from "../../../../chunks/loader-circle.js";
function OnboardingConfig($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let loading = true;
    $$renderer2.push(`<div class="p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto"><div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6"><div><h1 class="text-2xl font-bold text-white flex items-center gap-2">`);
    Settings($$renderer2, { class: "w-6 h-6 text-blue-400" });
    $$renderer2.push(`<!----> Configuración de Onboarding</h1> <p class="text-slate-400 text-sm mt-1">Personaliza pasos, planes, menú del portal y textos de bienvenida.</p></div> <div class="flex gap-2"><button${attr("disabled", loading, true)} class="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm transition">`);
    Refresh_cw($$renderer2, {
      class: `w-4 h-4 ${stringify("animate-spin")}`
    });
    $$renderer2.push(`<!----> Recargar</button> <button${attr("disabled", loading, true)} class="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition disabled:opacity-50">`);
    {
      $$renderer2.push("<!--[!-->");
      Save($$renderer2, { class: "w-4 h-4" });
    }
    $$renderer2.push(`<!--]--> Guardar cambios</button></div></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="flex justify-center py-20">`);
      Loader_circle($$renderer2, { class: "w-10 h-10 text-blue-400 animate-spin" });
      $$renderer2.push(`<!----></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  OnboardingConfig($$renderer);
}
export {
  _page as default
};
