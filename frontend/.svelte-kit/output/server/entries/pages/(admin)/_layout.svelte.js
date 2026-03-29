import { u as unsubscribe_stores, f as derived, s as store_get } from "../../../chunks/index2.js";
import { L as Layout } from "../../../chunks/Layout.js";
import { p as page } from "../../../chunks/stores.js";
function _layout($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let { children } = $$props;
    const currentRoute = derived(() => store_get($$store_subs ??= {}, "$page", page).url.pathname.replace(/^\//, "") || "dashboard");
    Layout($$renderer2, {
      currentRoute: currentRoute(),
      children: ($$renderer3) => {
        children($$renderer3);
        $$renderer3.push(`<!---->`);
      },
      $$slots: { default: true }
    });
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _layout as default
};
