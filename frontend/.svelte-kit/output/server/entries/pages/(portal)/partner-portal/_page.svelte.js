import "clsx";
import { o as onDestroy } from "../../../../chunks/index-server.js";
import "../../../../chunks/darkMode.js";
import "../../../../chunks/toast.js";
import { S as Spinner } from "../../../../chunks/Spinner.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/root.js";
import "../../../../chunks/state.svelte.js";
import "../../../../chunks/client.js";
import "../../../../chunks/tenants.js";
function PartnerPortal($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    function clearDeploymentPolling() {
    }
    onDestroy(clearDeploymentPolling);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="min-h-screen bg-[#F5F3EF] flex items-center justify-center"><div class="text-center">`);
      Spinner($$renderer2, { size: "lg" });
      $$renderer2.push(`<!----> <p class="mt-4 text-gray-500">Cargando portal...</p></div></div>`);
    }
    $$renderer2.push(`<!--]-->`);
  });
}
function _page($$renderer) {
  PartnerPortal($$renderer);
}
export {
  _page as default
};
