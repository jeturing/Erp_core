import { a as attr_style, c as attr, d as escape_html, e as ensure_array_like, s as store_get, u as unsubscribe_stores, o as bind_props, b as stringify } from "./index2.js";
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
import { A as Arrow_right } from "./arrow-right.js";
import { M as Menu } from "./menu.js";
function NavBar($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let brandName;
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
      scrolled = window.scrollY > 24;
    }
    if (typeof window !== "undefined") {
      window.addEventListener("scroll", handleScroll, { passive: true });
    }
    brandName = partnerBranding?.brand_name || "SAJET";
    $$renderer2.push(`<nav class="fixed top-0 left-0 right-0 z-50 transition-all duration-300"${attr_style(`background:${stringify(scrolled ? "rgba(2,14,31,0.97)" : "rgba(2,14,31,0.72)")}; backdrop-filter:blur(18px); -webkit-backdrop-filter:blur(18px); border-bottom:1px solid ${stringify(scrolled ? "rgba(255,255,255,0.10)" : "rgba(255,255,255,0.06)")};`)}><div class="max-w-6xl mx-auto px-6 py-3.5 flex items-center justify-between"><a href="/" class="flex items-center gap-2.5 group">`);
    if (partnerBranding?.logo_url) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<img${attr("src", partnerBranding.logo_url)}${attr("alt", brandName)} class="h-7"/>`);
    } else {
      $$renderer2.push("<!--[!-->");
      $$renderer2.push(`<div class="w-7 h-7 rounded-lg flex items-center justify-center font-jakarta font-bold text-sm text-[#020e1f] transition-transform group-hover:scale-105" style="background:#00FF9F; box-shadow:0 0 12px rgba(0,255,159,0.30);">${escape_html(brandName[0])}</div>`);
    }
    $$renderer2.push(`<!--]--> <span class="font-jakarta font-bold text-sm tracking-[0.05em] text-[#f0f4ff]">${escape_html(brandName)}</span></a> <div class="hidden md:flex items-center gap-7"><!--[-->`);
    const each_array = ensure_array_like(navLinks);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let link = each_array[$$index];
      $$renderer2.push(`<a${attr("href", link.href)} class="text-[13px] font-inter text-[#7a8fa6] hover:text-[#f0f4ff] transition-colors duration-150">${escape_html(link.label || (link.labelKey ? store_get($$store_subs ??= {}, "$t", $format)(link.labelKey) : ""))}</a>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="hidden md:flex items-center gap-2"><button class="h-8 px-2.5 rounded-lg flex items-center gap-1 text-[#7a8fa6] hover:text-[#f0f4ff] transition-colors"${attr("title", store_get($$store_subs ??= {}, "$t", $format)("nav.language"))}>`);
    Globe($$renderer2, { class: "w-4 h-4", strokeWidth: 1.5 });
    $$renderer2.push(`<!----> <span class="text-[11px] font-inter font-semibold">${escape_html(store_get($$store_subs ??= {}, "$localeStore", localeStore) === "es" ? "ES" : "EN")}</span></button> <button class="text-[13px] font-inter text-[#7a8fa6] hover:text-[#f0f4ff] transition-colors px-3 py-1.5">${escape_html(store_get($$store_subs ??= {}, "$t", $format)("common.login"))}</button> <button class="flex items-center gap-1.5 text-[13px] font-inter font-semibold px-4 py-2 rounded-lg transition-all duration-150 hover:-translate-y-px" style="background:#00FF9F; color:#020e1f; box-shadow:0 4px 14px rgba(0,255,159,0.20);">${escape_html(store_get($$store_subs ??= {}, "$localeStore", localeStore) === "es" ? "Crear empresa" : "Start free")} `);
    Arrow_right($$renderer2, { class: "w-3.5 h-3.5" });
    $$renderer2.push(`<!----></button></div> <button class="md:hidden w-9 h-9 flex items-center justify-center rounded-lg text-[#c8d3e8] transition-colors" style="background:rgba(255,255,255,0.05);" aria-label="Toggle menu">`);
    {
      $$renderer2.push("<!--[!-->");
      Menu($$renderer2, { class: "w-5 h-5" });
    }
    $$renderer2.push(`<!--]--></button></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></nav>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
    bind_props($$props, { partnerBranding });
  });
}
function Footer($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    $$renderer2.push(`<footer style="background: #020e1f; border-top: 1px solid rgba(0,255,159,0.08); padding: 64px 24px 40px;"><div style="max-width:1080px; margin:0 auto;"><div style="display:grid; grid-template-columns:2fr 1fr 1fr 1fr; gap:48px; margin-bottom:56px;"><div><div style="display:flex; align-items:center; gap:10px; margin-bottom:20px;"><div style="width:32px; height:32px; background:linear-gradient(135deg,#003B73,#00569e); border-radius:6px; display:flex; align-items:center; justify-content:center; box-shadow:0 0 0 1px rgba(0,255,159,0.2);"><span style="color:#00FF9F; font-weight:800; font-size:14px; font-family:'Plus Jakarta Sans',system-ui;">S</span></div> <span style="font-family:'Plus Jakarta Sans',system-ui; font-weight:700; font-size:17px; color:#f0f4ff; letter-spacing:-0.02em;">SAJET</span></div> <p style="font-size:14px; line-height:1.65; color:#7a8fa6; font-weight:300; max-width:260px; margin:0 0 24px;">ERP multi-tenant para empresas que exigen confiabilidad, escala y control real de sus datos.</p> <div style="display:flex; gap:16px;"><!--[-->`);
    const each_array = ensure_array_like(["segrd.com", "jeturing.com"]);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let link = each_array[$$index];
      $$renderer2.push(`<a${attr("href", `https://${stringify(link)}`)} target="_blank" rel="noopener" style="font-size:12px; color:#7a8fa6; text-decoration:none; transition:color 0.2s;">${escape_html(link)}</a>`);
    }
    $$renderer2.push(`<!--]--></div></div> <!--[-->`);
    const each_array_1 = ensure_array_like([
      {
        title: "Producto",
        links: [
          "Características",
          "Precios",
          "Seguridad",
          "API",
          "Changelog"
        ]
      },
      {
        title: "Empresa",
        links: ["Nosotros", "Blog", "Careers", "Prensa", "Contacto"]
      },
      {
        title: "Legal",
        links: ["Privacidad", "Términos", "SLA", "Cookies", "GDPR"]
      }
    ]);
    for (let $$index_2 = 0, $$length = each_array_1.length; $$index_2 < $$length; $$index_2++) {
      let col = each_array_1[$$index_2];
      $$renderer2.push(`<div><h4 style="font-size:11px; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:#f0f4ff; margin:0 0 20px;">${escape_html(col.title)}</h4> <ul style="list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:12px;"><!--[-->`);
      const each_array_2 = ensure_array_like(col.links);
      for (let $$index_1 = 0, $$length2 = each_array_2.length; $$index_1 < $$length2; $$index_1++) {
        let link = each_array_2[$$index_1];
        $$renderer2.push(`<li><a href="#" style="font-size:13px; color:#7a8fa6; text-decoration:none; transition:color 0.2s; font-weight:300;">${escape_html(link)}</a></li>`);
      }
      $$renderer2.push(`<!--]--></ul></div>`);
    }
    $$renderer2.push(`<!--]--></div> <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px; padding-top:32px; border-top:1px solid rgba(255,255,255,0.06);"><p style="font-size:12px; color:#7a8fa6; margin:0; font-weight:300;">© ${escape_html((/* @__PURE__ */ new Date()).getFullYear())} Jeturing. Todos los derechos reservados.</p> <div style="display:flex; align-items:center; gap:6px;"><div style="width:6px; height:6px; border-radius:50%; background:#00FF9F; box-shadow:0 0 6px rgba(0,255,159,0.6);"></div> <span style="font-size:12px; color:#7a8fa6; font-weight:300;">Todos los sistemas operativos</span></div></div></div></footer>`);
  });
}
export {
  Footer as F,
  NavBar as N
};
