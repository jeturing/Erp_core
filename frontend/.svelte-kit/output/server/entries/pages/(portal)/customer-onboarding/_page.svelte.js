import "clsx";
import { h as sanitize_props, i as spread_props, j as slot, d as escape_html } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import "../../../../chunks/tenants.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/root.js";
import "../../../../chunks/state.svelte.js";
import { L as Lock } from "../../../../chunks/lock.js";
import { I as Icon } from "../../../../chunks/Icon.js";
import { F as File_text } from "../../../../chunks/file-text.js";
import { C as Credit_card } from "../../../../chunks/credit-card.js";
import { C as Circle_check_big } from "../../../../chunks/circle-check-big.js";
import { L as Loader_circle } from "../../../../chunks/loader-circle.js";
function User($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["path", { "d": "M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" }],
    ["circle", { "cx": "12", "cy": "7", "r": "4" }]
  ];
  Icon($$renderer, spread_props([
    { name: "user" },
    $$sanitized_props,
    {
      /**
       * @component @name User
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMTkgMjF2LTJhNCA0IDAgMCAwLTQtNEg5YTQgNCAwIDAgMC00IDR2MiIgLz4KICA8Y2lyY2xlIGN4PSIxMiIgY3k9IjciIHI9IjQiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/user
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
function CustomerOnboarding($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let isDominican;
    let currentStep = 0;
    let visibleSteps = [];
    let profileForm = { country: "" };
    const stepLabels = [
      { icon: Lock, label: "Contraseña" },
      { icon: User, label: "Perfil" },
      { icon: File_text, label: "Fiscal (RD)" },
      { icon: Credit_card, label: "Pago" },
      { icon: Circle_check_big, label: "Completado" }
    ];
    visibleSteps[currentStep]?.key ?? "password";
    isDominican = profileForm.country === "DO";
    visibleSteps.length > 0 ? visibleSteps : isDominican ? stepLabels : stepLabels.filter((_, i) => i !== 2);
    visibleSteps.length > 0 ? currentStep : isDominican ? currentStep : currentStep;
    $$renderer2.push(`<div class="min-h-screen bg-bg-page p-4 sm:p-8"><div class="max-w-3xl mx-auto space-y-8"><div class="text-center"><h1 class="text-3xl font-bold text-text-light mb-2">${escape_html(
      // Load available plans
      /* plans not available, show fallback */
      // Load customer TOS
      // Sign TOS
      "Bienvenido a Sajet"
    )}</h1> <p class="text-gray-400">${escape_html("Complete su configuración para comenzar a usar la plataforma")}</p></div> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="flex items-center justify-center py-20">`);
      Loader_circle($$renderer2, { size: 32, class: "animate-spin text-terracotta" });
      $$renderer2.push(`<!----></div>`);
    }
    $$renderer2.push(`<!--]--></div></div>`);
  });
}
function _page($$renderer) {
  CustomerOnboarding($$renderer);
}
export {
  _page as default
};
