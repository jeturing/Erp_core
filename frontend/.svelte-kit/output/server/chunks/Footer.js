import { h as sanitize_props, i as spread_props, j as slot, k as attr_class, a as attr_style, c as attr, d as escape_html, e as ensure_array_like, s as store_get, u as unsubscribe_stores, p as bind_props, b as stringify, t as attributes } from "./index2.js";
import { $ as $format, l as localeStore } from "./darkMode.js";
import "./toast.js";
import { a8 as fallback } from "./utils2.js";
import "@sveltejs/kit/internal";
import "./exports.js";
import "./utils.js";
import "@sveltejs/kit/internal/server";
import "./root.js";
import "./state.svelte.js";
import { G as Globe } from "./globe.js";
import { I as Icon } from "./Icon.js";
function Linkedin($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    [
      "path",
      {
        "d": "M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"
      }
    ],
    ["rect", { "width": "4", "height": "12", "x": "2", "y": "9" }],
    ["circle", { "cx": "4", "cy": "4", "r": "2" }]
  ];
  Icon($$renderer, spread_props([
    { name: "linkedin" },
    $$sanitized_props,
    {
      /**
       * @component @name Linkedin
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMTYgOGE2IDYgMCAwIDEgNiA2djdoLTR2LTdhMiAyIDAgMCAwLTItMiAyIDIgMCAwIDAtMiAydjdoLTR2LTdhNiA2IDAgMCAxIDYtNnoiIC8+CiAgPHJlY3Qgd2lkdGg9IjQiIGhlaWdodD0iMTIiIHg9IjIiIHk9IjkiIC8+CiAgPGNpcmNsZSBjeD0iNCIgY3k9IjQiIHI9IjIiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/linkedin
       * @see https://lucide.dev/guide/packages/lucide-svelte - Documentation
       *
       * @param {Object} props - Lucide icons props and any valid SVG attribute
       * @returns {FunctionalComponent} Svelte component
       * @deprecated Brand icons have been deprecated and are due to be removed, please refer to https://github.com/lucide-icons/lucide/issues/670. We recommend using https://simpleicons.org/?q=linkedin instead. This icon will be removed in v1.0
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
function Youtube($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    [
      "path",
      {
        "d": "M2.5 17a24.12 24.12 0 0 1 0-10 2 2 0 0 1 1.4-1.4 49.56 49.56 0 0 1 16.2 0A2 2 0 0 1 21.5 7a24.12 24.12 0 0 1 0 10 2 2 0 0 1-1.4 1.4 49.55 49.55 0 0 1-16.2 0A2 2 0 0 1 2.5 17"
      }
    ],
    ["path", { "d": "m10 15 5-3-5-3z" }]
  ];
  Icon($$renderer, spread_props([
    { name: "youtube" },
    $$sanitized_props,
    {
      /**
       * @component @name Youtube
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMi41IDE3YTI0LjEyIDI0LjEyIDAgMCAxIDAtMTAgMiAyIDAgMCAxIDEuNC0xLjQgNDkuNTYgNDkuNTYgMCAwIDEgMTYuMiAwQTIgMiAwIDAgMSAyMS41IDdhMjQuMTIgMjQuMTIgMCAwIDEgMCAxMCAyIDIgMCAwIDEtMS40IDEuNCA0OS41NSA0OS41NSAwIDAgMS0xNi4yIDBBMiAyIDAgMCAxIDIuNSAxNyIgLz4KICA8cGF0aCBkPSJtMTAgMTUgNS0zLTUtM3oiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/youtube
       * @see https://lucide.dev/guide/packages/lucide-svelte - Documentation
       *
       * @param {Object} props - Lucide icons props and any valid SVG attribute
       * @returns {FunctionalComponent} Svelte component
       * @deprecated Brand icons have been deprecated and are due to be removed, please refer to https://github.com/lucide-icons/lucide/issues/670. We recommend using https://simpleicons.org/?q=youtube instead. This icon will be removed in v1.0
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
function NavBar($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let logoColor, brandName;
    let partnerBranding = fallback($$props["partnerBranding"], null);
    const navLinks = [
      { label: "Clientes", href: "/signup" },
      { labelKey: "nav.for_accountants", href: "/accountants" },
      { labelKey: "nav.partners", href: "/partner-signup" },
      { labelKey: "nav.pricing", href: "#pricing" },
      { labelKey: "nav.resources", href: "#faq" }
    ];
    let scrolled = false;
    function handleScroll() {
      scrolled = window.scrollY > 10;
    }
    if (typeof window !== "undefined") {
      window.addEventListener("scroll", handleScroll);
    }
    logoColor = partnerBranding?.primary_color || "#1B4FD8";
    brandName = partnerBranding?.brand_name || "SAJET";
    $$renderer2.push(`<nav${attr_class("fixed top-0 left-0 right-0 z-50 transition-all duration-300", void 0, {
      "bg-white": scrolled,
      "shadow-soft": scrolled,
      "bg-transparent": !scrolled
    })}${attr_style(`border-bottom: ${stringify(scrolled ? "1px solid #E2E8F0" : "none")}`)}><div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between"><div class="flex items-center gap-3">`);
    if (partnerBranding?.logo_url) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<img${attr("src", partnerBranding.logo_url)}${attr("alt", brandName)} class="h-8"/>`);
    } else {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<div class="w-8 h-8 rounded-btn flex items-center justify-center"${attr_style(`background: ${stringify(logoColor)}`)}><span class="text-white font-jakarta font-bold text-sm">${escape_html(brandName[0])}</span></div>`);
    }
    $$renderer2.push(`<!--]--> <span class="font-jakarta font-bold tracking-[0.08em] text-sm"${attr_style(`color: ${stringify(scrolled ? "#0F172A" : "#0F172A")}`)}>${escape_html(brandName)}</span></div> <div class="hidden md:flex items-center gap-8"><!--[-->`);
    const each_array = ensure_array_like(navLinks);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let link = each_array[$$index];
      $$renderer2.push(`<a${attr("href", link.href)} class="text-sm font-inter transition-colors"${attr_style(`color: ${stringify(scrolled ? "#64748B" : "#64748B")}`)}>${escape_html(link.label || (link.labelKey ? store_get($$store_subs ??= {}, "$t", $format)(link.labelKey) : ""))}</a>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="flex items-center gap-3"><button${attr_class("w-10 h-10 rounded-lg flex items-center justify-center transition-colors", void 0, { "bg-primary-light": scrolled, "hover:bg-cloud": !scrolled })}${attr("title", store_get($$store_subs ??= {}, "$t", $format)("nav.language"))}>`);
    Globe($$renderer2, { class: "w-5 h-5 text-slate", strokeWidth: 1.5 });
    $$renderer2.push(`<!----> <span class="text-xs font-jakarta font-bold text-primary ml-1">${escape_html(store_get($$store_subs ??= {}, "$localeStore", localeStore) === "es" ? "ES" : "EN")}</span></button> <a href="/accountants" class="text-sm font-inter text-slate hover:text-slate-dark transition-colors px-3 py-1.5">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("common.join_accountant"))}</a> <button class="text-sm font-inter text-slate hover:text-slate-dark transition-colors px-3 py-1.5">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("common.login"))}</button> <button class="text-sm font-inter font-semibold text-white px-5 py-2.5 rounded-btn transition-all hover:-translate-y-px hover:shadow-medium"${attr_style(`background: ${stringify(logoColor)}`)}>${escape_html(store_get($$store_subs ??= {}, "$localeStore", localeStore) === "es" ? "Crear empresa" : "Create company")}</button></div></div></nav>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
    bind_props($$props, { partnerBranding });
  });
}
function Footer($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    (/* @__PURE__ */ new Date()).getFullYear();
    const columns = [
      {
        title: store_get($$store_subs ??= {}, "$t", $format)("footer.product"),
        links: [
          {
            label: store_get($$store_subs ??= {}, "$t", $format)("footer.features"),
            href: "#features"
          },
          {
            label: store_get($$store_subs ??= {}, "$t", $format)("footer.pricing"),
            href: "#pricing"
          },
          {
            label: store_get($$store_subs ??= {}, "$t", $format)("footer.modules"),
            href: "#features"
          },
          {
            label: store_get($$store_subs ??= {}, "$t", $format)("footer.integrations"),
            href: "#faq"
          },
          {
            label: store_get($$store_subs ??= {}, "$t", $format)("footer.api_docs"),
            href: "/docs"
          }
        ]
      },
      {
        title: store_get($$store_subs ??= {}, "$t", $format)("footer.company"),
        links: [
          {
            label: store_get($$store_subs ??= {}, "$t", $format)("footer.about"),
            href: "/about"
          },
          {
            label: store_get($$store_subs ??= {}, "$t", $format)("nav.partners"),
            href: "#partners"
          },
          {
            label: store_get($$store_subs ??= {}, "$t", $format)("nav.for_accountants"),
            href: "/accountants"
          },
          {
            label: store_get($$store_subs ??= {}, "$t", $format)("footer.contact"),
            href: "https://wa.me/4012001999"
          }
        ]
      },
      {
        title: store_get($$store_subs ??= {}, "$t", $format)("footer.legal"),
        links: [
          {
            label: store_get($$store_subs ??= {}, "$t", $format)("footer.privacy"),
            href: "/privacy"
          },
          {
            label: store_get($$store_subs ??= {}, "$t", $format)("footer.terms"),
            href: "/terms"
          },
          {
            label: store_get($$store_subs ??= {}, "$t", $format)("footer.data_processing"),
            href: "/data-processing"
          },
          {
            label: store_get($$store_subs ??= {}, "$t", $format)("footer.security"),
            href: "/security"
          },
          {
            label: store_get($$store_subs ??= {}, "$t", $format)("footer.sla"),
            href: "/sla"
          }
        ]
      }
    ];
    $$renderer2.push(`<footer class="bg-[#0F172A] pt-16 pb-8"><div class="max-w-6xl mx-auto px-6"><div class="grid grid-cols-2 md:grid-cols-4 gap-10 mb-14"><div class="col-span-2 md:col-span-1"><a href="/" class="inline-block mb-4"><span class="text-xl font-jakarta font-extrabold text-white">Sajet<span class="text-secondary">.</span>us</span></a> <p class="text-sm font-inter text-slate-400 leading-relaxed mb-6">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("footer.brand_description"))}</p> <div class="flex items-center gap-3"><a href="https://www.linkedin.com/in/jhonatancarvajal/" target="_blank" rel="noopener" class="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-slate-400 hover:bg-primary hover:text-white transition-all" aria-label="LinkedIn">`);
    Linkedin($$renderer2, { class: "w-4 h-4" });
    $$renderer2.push(`<!----></a> <a href="https://wa.me/4012001999" target="_blank" rel="noopener" class="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-slate-400 hover:bg-emerald-500 hover:text-white transition-all" aria-label="WhatsApp"><svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"></path><path d="M12 0C5.373 0 0 5.373 0 12c0 2.123.558 4.115 1.535 5.836L.057 23.944l6.264-1.449A11.94 11.94 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.818a9.818 9.818 0 01-5.013-1.373l-.359-.214-3.724.861.882-3.624-.234-.373A9.818 9.818 0 012.182 12C2.182 6.567 6.567 2.182 12 2.182S21.818 6.567 21.818 12 17.433 21.818 12 21.818z"></path></svg></a> <a href="https://youtube.com/@sajet" target="_blank" rel="noopener" class="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-slate-400 hover:bg-red-600 hover:text-white transition-all" aria-label="YouTube">`);
    Youtube($$renderer2, { class: "w-4 h-4" });
    $$renderer2.push(`<!----></a></div></div> <!--[-->`);
    const each_array = ensure_array_like(columns);
    for (let $$index_1 = 0, $$length = each_array.length; $$index_1 < $$length; $$index_1++) {
      let col = each_array[$$index_1];
      $$renderer2.push(`<div><h4 class="text-sm font-jakarta font-semibold text-white mb-4">${escape_html(col.title)}</h4> <ul class="space-y-2.5"><!--[-->`);
      const each_array_1 = ensure_array_like(col.links);
      for (let $$index = 0, $$length2 = each_array_1.length; $$index < $$length2; $$index++) {
        let link = each_array_1[$$index];
        $$renderer2.push(`<li><a${attributes({
          href: link.href,
          class: "text-sm font-inter text-slate-400 hover:text-white transition-colors",
          ...link.href.startsWith("http") ? { target: "_blank", rel: "noopener noreferrer" } : {}
        })}>${escape_html(link.label)}</a></li>`);
      }
      $$renderer2.push(`<!--]--></ul></div>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="border-t border-white/10 pt-6 flex flex-col md:flex-row items-center justify-between gap-3"><p class="text-xs font-inter text-slate-500">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("footer.copyright"))}</p> <p class="text-xs font-inter text-slate-600">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("footer.powered_by"))} ${escape_html(store_get($$store_subs ??= {}, "$t", $format)("footer.company_name"))}</p></div></div></footer>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  Footer as F,
  NavBar as N
};
