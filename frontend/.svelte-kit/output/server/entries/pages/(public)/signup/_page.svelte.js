import "clsx";
import { e as ensure_array_like, d as escape_html, k as attr_class } from "../../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../../chunks/root.js";
import "../../../../chunks/state.svelte.js";
import { S as Star } from "../../../../chunks/star.js";
import { A as Arrow_right } from "../../../../chunks/arrow-right.js";
import { C as Calculator } from "../../../../chunks/calculator.js";
import { C as Circle_check_big } from "../../../../chunks/circle-check-big.js";
import { C as Chevron_up } from "../../../../chunks/chevron-up.js";
import { C as Chevron_down } from "../../../../chunks/chevron-down.js";
import { L as Lock } from "../../../../chunks/lock.js";
import { S as Shield_check } from "../../../../chunks/shield-check.js";
import { Z as Zap } from "../../../../chunks/zap.js";
import { B as Building_2 } from "../../../../chunks/building-2.js";
import { H as Handshake } from "../../../../chunks/handshake.js";
function Signup($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let openFaq = null;
    const faqs = [
      {
        q: "Cuanto tarda en activarse mi cuenta?",
        a: "Tu instancia Sajet se provisiona automaticamente en minutos una vez confirmado el pago. Recibiras un email con las credenciales."
      },
      {
        q: "Puedo cambiar de plan despues?",
        a: "Si, puedes cambiar de plan en cualquier momento desde el portal de cliente. Los cambios aplican al siguiente ciclo de facturacion."
      },
      {
        q: "Que significa que el partner queda pendiente de validacion?",
        a: "Al registrarte como partner, nuestro equipo revisa tu solicitud para confirmar que cumples los requisitos del programa. La validacion toma 24-48 horas habiles. No se activa ningun cobro hasta aprobar."
      },
      {
        q: "Como funciona la comision para partners?",
        a: "Los partners certificados reciben el 50% de los ingresos netos de cada cliente referido, pagado mensualmente via Stripe Connect."
      },
      {
        q: "Puedo empezar sin saber que ruta elegir?",
        a: "Si. La portada de alta te permite comparar empresa, firma contable y partner antes de entrar al formulario correcto."
      }
    ];
    const benefits = [
      {
        icon: Zap,
        title: "Activa en minutos",
        desc: "Provisioning automatico. Tu Sajet listo en menos de 5 minutos."
      },
      {
        icon: Shield_check,
        title: "Datos seguros",
        desc: "Base de datos aislada por tenant. Cumplimiento y operacion separada por cliente."
      },
      {
        icon: Circle_check_big,
        title: "Flujos claros",
        desc: "Cada tipo de usuario entra por su onboarding correcto desde el primer clic."
      },
      {
        icon: Star,
        title: "Soporte LATAM",
        desc: "Acompanamiento comercial y tecnico en espanol para toda la region."
      }
    ];
    const launchPaths = [
      {
        mode: "tenant",
        icon: Building_2,
        kicker: "Cliente / Empresa",
        title: "Abrir mi empresa en SAJET",
        desc: "Crea tu instancia Sajet, elige plan y sal a produccion con dominio propio y checkout en Stripe.",
        points: [
          "Instancia dedicada",
          "Dominio .sajet.us",
          "Activacion inmediata"
        ],
        featured: true
      },
      {
        mode: "accountant",
        icon: Calculator,
        kicker: "Contador / Firma",
        title: "Centralizar clientes contables",
        desc: "Activa un workspace para tu firma y entra al modelo multi-cliente con un recorrido pensado para despachos.",
        points: [
          "Ruta multi-cliente",
          "Branding de firma",
          "Alta contable guiada"
        ]
      },
      {
        mode: "partner",
        icon: Handshake,
        kicker: "Socio / Partner",
        title: "Revender y cobrar comisiones",
        desc: "Solicita acceso al programa de partners con portal, acuerdos, validacion y dispersion posterior por Stripe.",
        points: [
          "Comisiones recurrentes",
          "White-label",
          "Validacion del equipo SAJET"
        ]
      }
    ];
    const activationSteps = [
      "Eliges la ruta correcta: empresa, firma contable o socio.",
      "Completas tus datos y definimos el espacio inicial.",
      "Stripe procesa el alta y SAJET prepara tu entorno operativo."
    ];
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="min-h-screen bg-[#F5F3EF]"><nav class="sticky top-0 z-30 bg-[#F5F3EF]/95 backdrop-blur border-b border-[#D1CCC4]"><div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between gap-6"><a href="/" class="flex items-center gap-2.5"><div class="w-7 h-7 bg-[#003B73] flex items-center justify-center"><span class="text-white font-bold text-xs">S</span></div> <span class="font-bold text-[#1a1a1a] text-sm tracking-wide uppercase">Sajet ERP</span></a> <div class="hidden md:flex items-center gap-6 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-500"><button type="button" class="hover:text-[#003B73] transition-colors">Clientes</button> <button type="button" class="hover:text-[#003B73] transition-colors">Contadores</button> <button type="button" class="hover:text-[#003B73] transition-colors">Socios</button></div> <div class="flex items-center gap-3"><a href="/login" class="text-sm text-gray-500 hover:text-[#1a1a1a] transition-colors hidden sm:block">Iniciar sesion</a> <button type="button" class="bg-[#003B73] text-white text-xs font-bold uppercase tracking-widest px-5 py-2.5 hover:bg-[#002a55] transition-colors">Crear empresa</button></div></div></nav> <section class="max-w-6xl mx-auto px-6 pt-16 pb-16 grid lg:grid-cols-[1.2fr_0.8fr] gap-10 items-start"><div><div class="inline-flex items-center gap-2 bg-[#003B73]/10 text-[#003B73] text-xs font-semibold uppercase tracking-widest px-4 py-2 mb-8">`);
      Star($$renderer2, { size: 12 });
      $$renderer2.push(`<!----> ERP cloud multi-tenant para LATAM</div> <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-[#1a1a1a] leading-tight mb-6">Elige tu entrada a SAJET y <br/> <span class="text-[#003B73]">arranca con una ruta clara.</span></h1> <p class="text-lg text-gray-500 max-w-2xl mb-8 leading-relaxed">Empresas, firmas contables y socios no deberian caer en el mismo formulario sin contexto.
          Aqui eliges tu modalidad y continuas con un onboarding hecho para ese recorrido.</p> <div class="flex flex-col sm:flex-row gap-4 mb-6"><button type="button" class="bg-[#003B73] text-white font-bold uppercase tracking-widest text-sm px-8 py-4 hover:bg-[#002a55] transition-colors inline-flex items-center justify-center gap-2">Crear mi empresa `);
      Arrow_right($$renderer2, { size: 16 });
      $$renderer2.push(`<!----></button> <button type="button" class="border-2 border-[#003B73] text-[#003B73] font-bold uppercase tracking-widest text-sm px-8 py-4 hover:bg-[#003B73]/5 transition-colors inline-flex items-center justify-center gap-2">`);
      Calculator($$renderer2, { size: 16 });
      $$renderer2.push(`<!----> Soy contador</button></div> <p class="text-xs text-gray-400">Checkout, activacion y dispersion financiera se alinean con tu modelo operativo.</p></div> <div class="bg-[#1C1C1C] text-white p-8 lg:p-9"><p class="text-[11px] font-bold uppercase tracking-[0.24em] text-white/60 mb-4">Ruta guiada</p> <h2 class="text-2xl font-bold leading-tight mb-4">No es solo un alta: es el inicio del flujo correcto.</h2> <p class="text-sm text-white/70 leading-relaxed mb-6">SAJET usa una misma base operativa, pero cambia la experiencia segun si vas a crear una empresa,
          trabajar como firma contable o entrar como socio comercial.</p> <div class="space-y-4"><!--[-->`);
      const each_array = ensure_array_like(activationSteps);
      for (let index = 0, $$length = each_array.length; index < $$length; index++) {
        let step = each_array[index];
        $$renderer2.push(`<div class="flex gap-3 items-start"><span class="w-7 h-7 bg-white/10 text-white text-[11px] font-bold flex items-center justify-center shrink-0">${escape_html(index + 1)}</span> <p class="text-sm text-white/80 leading-relaxed">${escape_html(step)}</p></div>`);
      }
      $$renderer2.push(`<!--]--></div></div></section> <section class="max-w-6xl mx-auto px-6 pb-16"><div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4"><!--[-->`);
      const each_array_1 = ensure_array_like(benefits);
      for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
        let b = each_array_1[$$index_1];
        $$renderer2.push(`<div class="bg-white border border-[#D1CCC4] p-6"><div class="w-10 h-10 bg-[#003B73]/10 flex items-center justify-center mb-4">`);
        if (b.icon) {
          $$renderer2.push("<!--[-->");
          b.icon($$renderer2, { size: 20, class: "text-[#003B73]" });
          $$renderer2.push("<!--]-->");
        } else {
          $$renderer2.push("<!--[!-->");
          $$renderer2.push("<!--]-->");
        }
        $$renderer2.push(`</div> <h3 class="font-bold text-sm text-[#1a1a1a] mb-1">${escape_html(b.title)}</h3> <p class="text-xs text-gray-500 leading-relaxed">${escape_html(b.desc)}</p></div>`);
      }
      $$renderer2.push(`<!--]--></div></section> <section class="max-w-6xl mx-auto px-6 pb-20"><h2 class="text-2xl font-bold text-center text-[#1a1a1a] mb-3">Como quieres empezar?</h2> <p class="text-center text-sm text-gray-500 mb-10">Elige el camino que mejor se adapta a tu caso</p> <div class="grid lg:grid-cols-3 gap-6"><!--[-->`);
      const each_array_2 = ensure_array_like(launchPaths);
      for (let $$index_3 = 0, $$length = each_array_2.length; $$index_3 < $$length; $$index_3++) {
        let path = each_array_2[$$index_3];
        $$renderer2.push(`<div${attr_class(`${path.featured ? "bg-white border-2 border-[#003B73]" : "bg-white border border-[#D1CCC4]"} p-8`)}><p class="text-[11px] font-bold uppercase tracking-[0.22em] text-gray-400 mb-4">${escape_html(path.kicker)}</p> <div${attr_class(`w-12 h-12 flex items-center justify-center mb-5 ${path.featured ? "bg-[#003B73]/10" : "bg-[#E8E4DC]"}`)}>`);
        if (path.icon) {
          $$renderer2.push("<!--[-->");
          path.icon($$renderer2, { size: 24, class: "text-[#003B73]" });
          $$renderer2.push("<!--]-->");
        } else {
          $$renderer2.push("<!--[!-->");
          $$renderer2.push("<!--]-->");
        }
        $$renderer2.push(`</div> <h3 class="text-xl font-bold text-[#1a1a1a] mb-2">${escape_html(path.title)}</h3> <p class="text-sm text-gray-500 mb-5 leading-relaxed">${escape_html(path.desc)}</p> <ul class="space-y-2 mb-6"><!--[-->`);
        const each_array_3 = ensure_array_like(path.points);
        for (let $$index_2 = 0, $$length2 = each_array_3.length; $$index_2 < $$length2; $$index_2++) {
          let item = each_array_3[$$index_2];
          $$renderer2.push(`<li class="flex items-center gap-2 text-sm text-[#1a1a1a]">`);
          Circle_check_big($$renderer2, {
            size: 14,
            class: `${path.featured ? "text-[#003B73]" : "text-gray-300"} shrink-0`
          });
          $$renderer2.push(`<!----> ${escape_html(item)}</li>`);
        }
        $$renderer2.push(`<!--]--></ul> <button type="button"${attr_class(`w-full font-bold uppercase tracking-widest text-xs py-3.5 transition-colors ${path.featured ? "bg-[#003B73] text-white hover:bg-[#002a55]" : "border-2 border-[#003B73] text-[#003B73] hover:bg-[#003B73]/5"}`)}>${escape_html(path.mode === "partner" ? "Solicitar acceso" : "Elegir esta ruta")}</button></div>`);
      }
      $$renderer2.push(`<!--]--></div></section> <section class="max-w-3xl mx-auto px-6 pb-20"><h2 class="text-2xl font-bold text-center text-[#1a1a1a] mb-10">Preguntas frecuentes</h2> <div class="space-y-2"><!--[-->`);
      const each_array_4 = ensure_array_like(faqs);
      for (let i = 0, $$length = each_array_4.length; i < $$length; i++) {
        let faq = each_array_4[i];
        $$renderer2.push(`<div class="bg-white border border-[#D1CCC4]"><button type="button" class="w-full flex items-center justify-between px-5 py-4 text-left gap-4"><span class="text-sm font-semibold text-[#1a1a1a]">${escape_html(faq.q)}</span> `);
        if (openFaq === i) {
          $$renderer2.push("<!--[-->");
          Chevron_up($$renderer2, { size: 16, class: "text-gray-400 shrink-0" });
        } else {
          $$renderer2.push("<!--[!-->");
          Chevron_down($$renderer2, { size: 16, class: "text-gray-400 shrink-0" });
        }
        $$renderer2.push(`<!--]--></button> `);
        if (openFaq === i) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="px-5 pb-4 pt-3 text-sm text-gray-500 leading-relaxed border-t border-[#D1CCC4]">${escape_html(faq.a)}</div>`);
        } else {
          $$renderer2.push("<!--[!-->");
        }
        $$renderer2.push(`<!--]--></div>`);
      }
      $$renderer2.push(`<!--]--></div></section> <footer class="border-t border-[#D1CCC4] py-10"><div class="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4"><div class="flex items-center gap-2"><div class="w-6 h-6 bg-[#003B73] flex items-center justify-center"><span class="text-white font-bold text-[10px]">S</span></div> <span class="text-xs text-gray-400 uppercase tracking-widest font-bold">Sajet ERP · Jeturing</span></div> <div class="flex items-center gap-4 text-xs text-gray-400"><span class="flex items-center gap-1">`);
      Lock($$renderer2, { size: 11 });
      $$renderer2.push(`<!----> SSL · Datos cifrados</span> <span class="flex items-center gap-1">`);
      Shield_check($$renderer2, { size: 11 });
      $$renderer2.push(`<!----> Operacion separada por flujo</span> <a href="/login" class="hover:text-[#003B73] transition-colors">Iniciar sesion</a></div></div></footer></div>`);
    }
    $$renderer2.push(`<!--]-->`);
  });
}
function _page($$renderer) {
  Signup($$renderer);
}
export {
  _page as default
};
