import "clsx";
import { d as escape_html } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import { M as Message_circle } from "../../../../chunks/message-circle.js";
import { P as Plus } from "../../../../chunks/plus.js";
function Testimonials($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let testimonials = [];
    let selectedLocale = "en";
    $$renderer2.push(`<div class="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8"><div class="max-w-7xl mx-auto"><div class="mb-8"><div class="flex items-center justify-between mb-6"><div class="flex items-center gap-3">`);
    Message_circle($$renderer2, { class: "w-8 h-8 text-amber-600" });
    $$renderer2.push(`<!----> <h1 class="text-3xl font-bold text-gray-900">Testimonios</h1></div> <button class="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition">`);
    Plus($$renderer2, { class: "w-5 h-5" });
    $$renderer2.push(`<!----> Nuevo Testimonio</button></div> <div class="flex items-center gap-4"><div><label class="block text-sm font-medium text-gray-700 mb-1">Idioma</label> `);
    $$renderer2.select(
      {
        value: selectedLocale,
        class: "px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
      },
      ($$renderer3) => {
        $$renderer3.option({ value: "en" }, ($$renderer4) => {
          $$renderer4.push(`English (en)`);
        });
        $$renderer3.option({ value: "es" }, ($$renderer4) => {
          $$renderer4.push(`Español (es)`);
        });
      }
    );
    $$renderer2.push(`</div> <div class="text-sm text-gray-600 mt-6">${escape_html(testimonials.length)} testimonios</div></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-center py-12"><div class="inline-block"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div></div></div>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Testimonials($$renderer);
}
export {
  _page as default
};
