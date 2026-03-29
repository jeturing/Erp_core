import { w as head, d as escape_html, e as ensure_array_like, c as attr, p as bind_props } from "./index2.js";
import { N as NavBar, F as Footer } from "./Footer.js";
import { S as Shield_check } from "./shield-check.js";
import { C as Circle_check } from "./circle-check.js";
import { A as Arrow_right } from "./arrow-right.js";
function PublicInfoPage($$renderer, $$props) {
  let page, formalRequestHref;
  let slug = $$props["slug"];
  const pages = {
    about: {
      eyebrow: "Empresa",
      title: "Sobre SAJET",
      intro: "SAJET es la plataforma ERP SaaS multi-tenant de Jeturing para operación empresarial, contable y comercial sobre infraestructura propia.",
      sections: [
        {
          title: "Qué resuelve",
          paragraphs: [
            "Centraliza onboarding, facturación, portales, branding partner y operación de tenants en una sola base de trabajo.",
            "La plataforma está orientada a empresas, firmas contables y socios comerciales con recorridos diferenciados desde la misma arquitectura."
          ]
        },
        {
          title: "Cómo opera",
          paragraphs: [
            "El frontend actual se publica como SPA y consume APIs de ERP Core para auth, tenants, billing, dominios, portales y administración.",
            "La capa de negocio y provisioning se ejecuta desde FastAPI con persistencia en PostgreSQL y automatización sobre Proxmox, Stripe y Cloudflare."
          ]
        }
      ]
    },
    privacy: {
      eyebrow: "Legal",
      title: "Política de privacidad",
      intro: "SAJET procesa datos de cuenta, operación, facturación y soporte para prestar el servicio, proteger la plataforma y cumplir obligaciones legales y contractuales.",
      sections: [
        {
          title: "Datos tratados",
          paragraphs: [
            "Se procesan datos de autenticación, contacto, actividad de cuenta, metadatos operativos, configuración de tenants y datos necesarios para onboarding, soporte y cobro.",
            "Los datos de pago se delegan a Stripe; SAJET no almacena números completos de tarjeta en la aplicación."
          ]
        },
        {
          title: "Uso y retención",
          paragraphs: [
            "Los datos se usan para prestar el servicio, asegurar la cuenta, resolver incidencias, generar facturación y mantener trazabilidad operativa.",
            "La retención depende del tipo de dato, obligaciones regulatorias y estado contractual del cliente. Solicitudes específicas pueden canalizarse por soporte."
          ]
        }
      ]
    },
    terms: {
      eyebrow: "Legal",
      title: "Términos del servicio",
      intro: "El uso de SAJET requiere credenciales válidas, cumplimiento de políticas de seguridad, uso legítimo de la plataforma y pago oportuno de los servicios contratados.",
      sections: [
        {
          title: "Uso aceptable",
          paragraphs: [
            "El cliente es responsable del uso de sus usuarios, configuración funcional, contenido cargado y resguardo de accesos administrativos.",
            "No está permitido usar la plataforma para fraude, abuso de recursos, intrusión, distribución de malware o actividades que comprometan a terceros."
          ]
        },
        {
          title: "Suspensión y baja",
          paragraphs: [
            "SAJET puede suspender acceso por incumplimiento de pago, abuso, riesgo operativo o incidentes de seguridad que exijan contención inmediata.",
            "La continuidad, restauración o exportación de datos después de suspensión depende del estado contractual y del proceso de soporte aplicable."
          ]
        }
      ]
    },
    "data-processing": {
      eyebrow: "Compliance",
      title: "Procesamiento de datos",
      intro: "SAJET actúa como procesador u operador técnico sobre datos necesarios para ejecutar el servicio contratado y mantener la plataforma disponible y segura.",
      sections: [
        {
          title: "Alcance",
          paragraphs: [
            "El procesamiento cubre almacenamiento, transporte, autenticación, observabilidad, respaldo y automatización operativa vinculada al tenant o portal contratado.",
            "Los subprocesadores y servicios externos se limitan a componentes necesarios para operación, pagos, correo transaccional, infraestructura y seguridad."
          ]
        },
        {
          title: "Instrucciones y soporte",
          paragraphs: [
            "Requerimientos de exportación, borrado o tratamiento especial de datos deben canalizarse por soporte comercial o técnico con validación de identidad.",
            "Cuando aplique un acuerdo específico de procesamiento, prevalece el contrato firmado con el cliente sobre este resumen público."
          ]
        }
      ]
    },
    security: {
      eyebrow: "Seguridad",
      title: "Seguridad de la plataforma",
      intro: "SAJET opera con controles de autenticación, aislamiento lógico por tenant, auditoría, validación de parámetros y hardening de la superficie web y API.",
      sections: [
        {
          title: "Controles activos",
          paragraphs: [
            "La aplicación usa JWT, cookies seguras, validación de permisos, middleware de seguridad, CSP, CORS dinámico y registros de auditoría sobre operaciones sensibles.",
            "Existen controles específicos para auth, onboarding, administración, facturación y sincronización operativa entre backend y portales."
          ]
        },
        {
          title: "Reporte de incidentes",
          paragraphs: [
            "Incidentes de seguridad, exposición de credenciales o actividad sospechosa deben reportarse de inmediato a soporte para iniciar contención y análisis.",
            "Las medidas y tiempos de respuesta dependen de severidad, criticidad del tenant y evidencia disponible al momento del reporte."
          ]
        }
      ]
    },
    sla: {
      eyebrow: "Operación",
      title: "Acuerdo de nivel de servicio",
      intro: "Los niveles de servicio varían por plan, criticidad y acuerdo comercial, pero SAJET opera con objetivos de continuidad, monitoreo y respuesta sobre la plataforma central.",
      sections: [
        {
          title: "Cobertura",
          paragraphs: [
            "La cobertura estándar incluye operación de la plataforma, monitoreo básico, atención de incidencias y continuidad razonable del servicio según el plan contratado.",
            "La recuperación ante fallos depende de la naturaleza del incidente, componentes afectados, dependencias externas y ventanas operativas disponibles."
          ]
        },
        {
          title: "Exclusiones",
          paragraphs: [
            "No se consideran incumplimientos de SLA los eventos originados por terceros, credenciales comprometidas del cliente, cambios no autorizados o fuerza mayor.",
            "Compromisos ampliados, soporte prioritario o RTO/RPO específicos deben pactarse de forma contractual."
          ]
        }
      ]
    }
  };
  page = pages[slug] ?? pages.about;
  formalRequestHref = `mailto:ventas@sajet.us?subject=${encodeURIComponent(`Consulta sobre ${slug} - SAJET`)}`;
  head("1197db0", $$renderer, ($$renderer2) => {
    $$renderer2.title(($$renderer3) => {
      $$renderer3.push(`<title>${escape_html(page.title)} | Sajet</title>`);
    });
    $$renderer2.push(`<meta name="description"${attr("content", page.intro)}/>`);
  });
  $$renderer.push(`<div class="min-h-screen bg-white font-inter">`);
  NavBar($$renderer, {});
  $$renderer.push(`<!----> <section class="bg-gradient-hero pt-32 pb-16"><div class="max-w-4xl mx-auto px-6 text-center"><span class="inline-flex items-center gap-2 rounded-full bg-white/10 border border-white/15 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-white/80">${escape_html(page.eyebrow)}</span> <h1 class="mt-6 text-4xl md:text-5xl font-jakarta font-extrabold text-white leading-tight">${escape_html(page.title)}</h1> <p class="mt-5 text-base md:text-lg text-white/80 max-w-2xl mx-auto leading-relaxed">${escape_html(page.intro)}</p></div></section> <section class="bg-[#F8FAFC] py-16"><div class="max-w-4xl mx-auto px-6"><div class="grid gap-6"><!--[-->`);
  const each_array = ensure_array_like(page.sections);
  for (let $$index_1 = 0, $$length = each_array.length; $$index_1 < $$length; $$index_1++) {
    let section = each_array[$$index_1];
    $$renderer.push(`<article class="rounded-card-lg border border-border bg-white p-6 shadow-soft"><div class="flex items-center gap-3 mb-4"><div class="w-10 h-10 rounded-full bg-primary-light flex items-center justify-center">`);
    Shield_check($$renderer, { class: "w-5 h-5 text-primary" });
    $$renderer.push(`<!----></div> <h2 class="text-xl font-jakarta font-bold text-slate-dark">${escape_html(section.title)}</h2></div> <div class="space-y-3"><!--[-->`);
    const each_array_1 = ensure_array_like(section.paragraphs);
    for (let $$index = 0, $$length2 = each_array_1.length; $$index < $$length2; $$index++) {
      let paragraph = each_array_1[$$index];
      $$renderer.push(`<p class="text-sm md:text-[15px] text-slate leading-relaxed">${escape_html(paragraph)}</p>`);
    }
    $$renderer.push(`<!--]--></div></article>`);
  }
  $$renderer.push(`<!--]--></div> <div class="mt-8 rounded-card-lg border border-primary/15 bg-white p-6 shadow-soft"><div class="flex items-start gap-3">`);
  Circle_check($$renderer, { class: "w-5 h-5 text-primary mt-0.5 flex-shrink-0" });
  $$renderer.push(`<!----> <div><p class="text-sm font-semibold text-slate-dark">Documento público resumido</p> <p class="mt-2 text-sm text-slate leading-relaxed">Este contenido resume la operación y criterios públicos vigentes de SAJET. Para contratos, anexos o versiones
              formales adaptadas a un cliente, canaliza la solicitud por ventas o soporte.</p></div></div> <div class="mt-5 flex flex-col sm:flex-row gap-3"><a href="/signup" class="inline-flex items-center justify-center gap-2 bg-primary hover:bg-navy text-white font-jakarta font-semibold text-sm px-6 py-3 rounded-btn transition-all">Crear cuenta `);
  Arrow_right($$renderer, { class: "w-4 h-4" });
  $$renderer.push(`<!----></a> <a${attr("href", formalRequestHref)} class="inline-flex items-center justify-center gap-2 border border-primary text-primary hover:bg-primary hover:text-white font-jakarta font-semibold text-sm px-6 py-3 rounded-btn transition-all">Solicitar versión formal</a></div></div></div></section> `);
  Footer($$renderer);
  $$renderer.push(`<!----></div>`);
  bind_props($$props, { slug });
}
export {
  PublicInfoPage as P
};
