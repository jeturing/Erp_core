import "clsx";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/root.js";
import "../../../../chunks/state.svelte.js";
import { h as sanitize_props, i as spread_props, j as slot } from "../../../../chunks/index2.js";
import { I as Icon } from "../../../../chunks/Icon.js";
function Arrow_left($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["path", { "d": "m12 19-7-7 7-7" }],
    ["path", { "d": "M19 12H5" }]
  ];
  Icon($$renderer, spread_props([
    { name: "arrow-left" },
    $$sanitized_props,
    {
      /**
       * @component @name ArrowLeft
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJtMTIgMTktNy03IDctNyIgLz4KICA8cGF0aCBkPSJNMTkgMTJINSIgLz4KPC9zdmc+Cg==) - https://lucide.dev/icons/arrow-left
       * @see https://lucide.dev/guide/packages/lucide-svelte - Documentation
       *
       * @param {Object} props - Lucide icons props and any valid SVG attribute
       * @returns {FunctionalComponent} Svelte component
       *
       */
      iconNode,
      children: ($$renderer2) => {
        $$renderer2.push(`<!--[-->`);
        slot($$renderer2, $$props, "default", {});
        $$renderer2.push(`<!--]-->`);
      },
      $$slots: { default: true }
    }
  ]));
}
function Life_buoy($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["circle", { "cx": "12", "cy": "12", "r": "10" }],
    ["path", { "d": "m4.93 4.93 4.24 4.24" }],
    ["path", { "d": "m14.83 9.17 4.24-4.24" }],
    ["path", { "d": "m14.83 14.83 4.24 4.24" }],
    ["path", { "d": "m9.17 14.83-4.24 4.24" }],
    ["circle", { "cx": "12", "cy": "12", "r": "4" }]
  ];
  Icon($$renderer, spread_props([
    { name: "life-buoy" },
    $$sanitized_props,
    {
      /**
       * @component @name LifeBuoy
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCIgLz4KICA8cGF0aCBkPSJtNC45MyA0LjkzIDQuMjQgNC4yNCIgLz4KICA8cGF0aCBkPSJtMTQuODMgOS4xNyA0LjI0LTQuMjQiIC8+CiAgPHBhdGggZD0ibTE0LjgzIDE0LjgzIDQuMjQgNC4yNCIgLz4KICA8cGF0aCBkPSJtOS4xNyAxNC44My00LjI0IDQuMjQiIC8+CiAgPGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iNCIgLz4KPC9zdmc+Cg==) - https://lucide.dev/icons/life-buoy
       * @see https://lucide.dev/guide/packages/lucide-svelte - Documentation
       *
       * @param {Object} props - Lucide icons props and any valid SVG attribute
       * @returns {FunctionalComponent} Svelte component
       *
       */
      iconNode,
      children: ($$renderer2) => {
        $$renderer2.push(`<!--[-->`);
        slot($$renderer2, $$props, "default", {});
        $$renderer2.push(`<!--]-->`);
      },
      $$slots: { default: true }
    }
  ]));
}
function RecoverAccount($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    $$renderer2.push(`<div class="min-h-screen bg-bg-page p-6"><div class="max-w-2xl mx-auto space-y-6"><button class="btn-secondary px-3 py-2 text-sm inline-flex items-center gap-2">`);
    Arrow_left($$renderer2, { size: 14 });
    $$renderer2.push(`<!----> Volver a login</button> <div class="card p-6 sm:p-8 space-y-5"><h1 class="text-2xl font-bold text-text-primary">Recuperar acceso</h1> <p class="text-sm text-gray-600">Selecciona tu tipo de cuenta y te guiamos con el flujo correcto de recuperación.</p> <div class="grid sm:grid-cols-3 gap-3"><a class="border border-border-light rounded-md p-4 hover:border-[#003B73] transition-colors" href="mailto:soporte@sajet.us?subject=Recuperar%20acceso%20Tenant&amp;body=Email%20de%20la%20cuenta:%20"><p class="font-semibold text-sm text-text-primary mb-1">Tenant</p> <p class="text-xs text-gray-500">Restablecer contraseña de portal cliente.</p></a> <a class="border border-border-light rounded-md p-4 hover:border-[#003B73] transition-colors" href="mailto:soporte@sajet.us?subject=Recuperar%20acceso%20Accountant&amp;body=Email%20de%20la%20cuenta:%20"><p class="font-semibold text-sm text-text-primary mb-1">Accountant</p> <p class="text-xs text-gray-500">Recuperar acceso a cuentas multi-tenant.</p></a> <a class="border border-border-light rounded-md p-4 hover:border-[#003B73] transition-colors" href="mailto:soporte@sajet.us?subject=Recuperar%20acceso%20Partner&amp;body=Email%20de%20la%20cuenta:%20"><p class="font-semibold text-sm text-text-primary mb-1">Partner</p> <p class="text-xs text-gray-500">Recuperar acceso al portal de socios.</p></a></div> <div class="rounded border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700 flex items-center gap-2">`);
    Life_buoy($$renderer2, { size: 14 });
    $$renderer2.push(`<!----> Soporte: <a class="underline" href="mailto:soporte@sajet.us">soporte@sajet.us</a></div> <button class="btn-primary w-full py-3">Crear cuenta nueva</button></div></div></div>`);
  });
}
function _page($$renderer) {
  RecoverAccount($$renderer);
}
export {
  _page as default
};
