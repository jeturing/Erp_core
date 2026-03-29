import "clsx";
import { c as attr, d as escape_html } from "../../../../chunks/index2.js";
import "../../../../chunks/client.js";
import { L as Languages } from "../../../../chunks/languages.js";
import { D as Download } from "../../../../chunks/download.js";
import { P as Plus } from "../../../../chunks/plus.js";
import { S as Search } from "../../../../chunks/search.js";
function Translations($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let selectedLocale = "en";
    let selectedContext = "";
    let searchQuery = "";
    let filteredTranslations = [];
    $$renderer2.push(`<div class="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8"><div class="max-w-7xl mx-auto"><div class="mb-8"><div class="flex items-center justify-between mb-6"><div class="flex items-center gap-3">`);
    Languages($$renderer2, { class: "w-8 h-8 text-purple-600" });
    $$renderer2.push(`<!----> <h1 class="text-3xl font-bold text-gray-900">Traducciones Dinámicas</h1></div> <div class="flex items-center gap-2"><button class="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition">`);
    Download($$renderer2, { class: "w-5 h-5" });
    $$renderer2.push(`<!----> Exportar CSV</button> <button class="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition">`);
    Plus($$renderer2, { class: "w-5 h-5" });
    $$renderer2.push(`<!----> Nueva Traducción</button></div></div> <div class="flex items-end gap-4 flex-wrap"><div><label class="block text-sm font-medium text-gray-700 mb-1">Idioma</label> `);
    $$renderer2.select(
      {
        value: selectedLocale,
        class: "px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
      },
      ($$renderer3) => {
        $$renderer3.option({ value: "" }, ($$renderer4) => {
          $$renderer4.push(`Todos`);
        });
        $$renderer3.option({ value: "en" }, ($$renderer4) => {
          $$renderer4.push(`English (en)`);
        });
        $$renderer3.option({ value: "es" }, ($$renderer4) => {
          $$renderer4.push(`Español (es)`);
        });
      }
    );
    $$renderer2.push(`</div> <div><label class="block text-sm font-medium text-gray-700 mb-1">Contexto</label> `);
    $$renderer2.select(
      {
        value: selectedContext,
        class: "px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
      },
      ($$renderer3) => {
        $$renderer3.option({ value: "" }, ($$renderer4) => {
          $$renderer4.push(`Todos`);
        });
        $$renderer3.option({ value: "landing" }, ($$renderer4) => {
          $$renderer4.push(`Landing`);
        });
        $$renderer3.option({ value: "seo" }, ($$renderer4) => {
          $$renderer4.push(`SEO`);
        });
        $$renderer3.option({ value: "pricing" }, ($$renderer4) => {
          $$renderer4.push(`Pricing`);
        });
        $$renderer3.option({ value: "footer" }, ($$renderer4) => {
          $$renderer4.push(`Footer`);
        });
        $$renderer3.option({ value: "email" }, ($$renderer4) => {
          $$renderer4.push(`Email`);
        });
      }
    );
    $$renderer2.push(`</div> <div class="flex-1 min-w-64"><label class="block text-sm font-medium text-gray-700 mb-1">Búsqueda</label> <div class="relative">`);
    Search($$renderer2, { class: "absolute left-3 top-2.5 w-5 h-5 text-gray-400" });
    $$renderer2.push(`<!----> <input type="text"${attr("value", searchQuery)} placeholder="Buscar por key o valor..." class="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"/></div></div> <div class="text-sm text-gray-600">${escape_html(filteredTranslations.length)} resultados</div></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="text-center py-12"><div class="inline-block"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div></div></div>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  Translations($$renderer);
}
export {
  _page as default
};
