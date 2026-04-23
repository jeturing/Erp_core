import "clsx";
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
    let clientServiceCatalog = [];
    let clientServiceSubscriptions = [];
    function isEmailPackage(item) {
      return item.service_code === "postal_email_package" || item.metadata_json?.kind === "postal_email_package";
    }
    clientServiceCatalog.filter((item) => isEmailPackage(item));
    clientServiceSubscriptions.filter((addon) => addon.catalog_item && isEmailPackage(addon.catalog_item));
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
