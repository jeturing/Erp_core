import "clsx";
import { L as Layout } from "../../../../chunks/Layout.js";
import { S as Spinner } from "../../../../chunks/Spinner.js";
import "../../../../chunks/toast.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/root.js";
import "../../../../chunks/state.svelte.js";
import { U as User_plus } from "../../../../chunks/user-plus.js";
function AccountantPortal($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    Layout($$renderer2, {
      currentRoute: "accountant-portal",
      children: ($$renderer3) => {
        $$renderer3.push(`<div class="p-6 max-w-6xl mx-auto"><div class="flex items-center justify-between mb-8"><div><h1 class="text-2xl font-jakarta font-bold text-slate-dark">Accountant Dashboard</h1> <p class="text-sm font-inter text-slate mt-1">Manage all your client companies from one place.</p></div> <button class="inline-flex items-center gap-2 bg-primary hover:bg-navy text-white font-jakarta font-semibold text-sm px-4 py-2 rounded-btn shadow-soft transition-all">`);
        User_plus($$renderer3, { class: "w-4 h-4" });
        $$renderer3.push(`<!----> Invite Client</button></div> `);
        {
          $$renderer3.push("<!--[-->");
          $$renderer3.push(`<div class="flex items-center justify-center py-20">`);
          Spinner($$renderer3, { size: "lg" });
          $$renderer3.push(`<!----></div>`);
        }
        $$renderer3.push(`<!--]--></div>`);
      },
      $$slots: { default: true }
    });
  });
}
function _page($$renderer) {
  AccountantPortal($$renderer);
}
export {
  _page as default
};
