import "clsx";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/root.js";
import "../../../../chunks/state.svelte.js";
function OnboardingAccess($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    $$renderer2.push(`<div class="min-h-screen bg-bg-page flex items-center justify-center p-6"><div class="w-full max-w-2xl bg-white border border-border-light rounded-lg p-8 shadow-soft"><h1 class="text-2xl font-bold text-text-primary mb-3">Completa tu Onboarding</h1> <p class="text-sm text-gray-600 mb-6">Para continuar con la configuración de tu empresa debes iniciar sesión con tu cuenta de cliente.</p> <div class="grid gap-4 sm:grid-cols-2"><button class="btn-primary py-3">Ir a iniciar sesión</button> <button class="btn-secondary py-3">Volver al inicio</button></div> <div class="mt-6 text-xs text-gray-500">Después de autenticarte, el sistema te llevará automáticamente al paso pendiente del onboarding.</div></div></div>`);
  });
}
function _page($$renderer) {
  OnboardingAccess($$renderer);
}
export {
  _page as default
};
