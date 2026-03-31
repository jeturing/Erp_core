import { o as bind_props, f as derived, s as store_get, u as unsubscribe_stores } from "../../../../../chunks/index2.js";
import { a8 as fallback } from "../../../../../chunks/utils2.js";
import "../../../../../chunks/darkMode.js";
import "../../../../../chunks/toast.js";
import "@sveltejs/kit/internal";
import "../../../../../chunks/exports.js";
import "../../../../../chunks/utils.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../../../../chunks/root.js";
import "../../../../../chunks/state.svelte.js";
import { S as Spinner } from "../../../../../chunks/Spinner.js";
import { p as page } from "../../../../../chunks/stores.js";
function PartnerLanding($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let code = fallback($$props["code"], "");
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="min-h-screen bg-white flex items-center justify-center"><div class="text-center">`);
      Spinner($$renderer2, { size: "lg" });
      $$renderer2.push(`<!----> <p class="mt-4 text-sm font-inter text-slate">Loading partner experience...</p></div></div>`);
    }
    $$renderer2.push(`<!--]-->`);
    bind_props($$props, { code });
  });
}
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    const slug = derived(() => store_get($$store_subs ??= {}, "$page", page).params.slug);
    PartnerLanding($$renderer2, { code: slug() });
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
