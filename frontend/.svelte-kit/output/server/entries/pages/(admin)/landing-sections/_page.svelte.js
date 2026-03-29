import "clsx";
import { d as escape_html } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import { F as File_text } from "../../../../chunks/file-text.js";
import { P as Plus } from "../../../../chunks/plus.js";
function LandingSections($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let sections = [];
    let selectedLocale = "en";
    $$renderer2.push(`<div class="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8"><div class="max-w-7xl mx-auto"><div class="mb-8"><div class="flex items-center justify-between mb-6"><div class="flex items-center gap-3">`);
    File_text($$renderer2, { class: "w-8 h-8 text-blue-600" });
    $$renderer2.push(`<!----> <h1 class="text-3xl font-bold text-gray-900">Secciones Landing</h1></div> <button class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">`);
    Plus($$renderer2, { class: "w-5 h-5" });
    $$renderer2.push(`<!----> Nueva Sección</button></div> <div class="flex items-center gap-4"><div><label class="block text-sm font-medium text-gray-700 mb-1">Idioma</label> `);
    $$renderer2.select(
      {
        value: selectedLocale,
        class: "px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
    $$renderer2.push(`</div> <div class="text-sm text-gray-600 mt-6">${escape_html(sections.length)} secciones</div></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-center py-12"><div class="inline-block"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div></div></div>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  LandingSections($$renderer);
}
export {
  _page as default
};
