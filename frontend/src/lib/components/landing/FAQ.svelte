<script lang="ts">
  import { ChevronDown } from 'lucide-svelte';

  const faqs = [
    {
      q: '¿Necesito una tarjeta de crédito para el período de prueba?',
      a: 'No. Los 14 días de prueba son completamente gratis, sin necesidad de tarjeta de crédito ni compromiso. Solo te pedimos tu correo electrónico.',
    },
    {
      q: '¿Puedo cambiar de plan en cualquier momento?',
      a: 'Sí, puedes subir o bajar de plan en cualquier momento. Los ajustes se prorratean automáticamente en tu próxima factura.',
    },
    {
      q: '¿Sajet funciona para empresas en República Dominicana?',
      a: 'Absolutamente. Sajet fue diseñado desde cero para el mercado dominicano: soporte para NCF, e-CF / facturación electrónica ante la DGII (vía República FEL), DOP y USD, e integraciones locales.',
    },
    {
      q: '¿Qué incluye la integración de facturación electrónica (e-CF)?',
      a: 'Sajet se integra nativamente con República FEL, proveedor certificado por la DGII. La generación, firma y envío de comprobantes fiscales electrónicos se gestiona directamente desde Sajet. El servicio FEL se contrata por separado (desde $50/mes según volumen).',
    },
    {
      q: '¿Cuántos usuarios puedo agregar a mi plan?',
      a: 'Depende del plan: Básico admite hasta 10 usuarios, Profesional hasta 50, y Empresarial es ilimitado. Puedes usar la calculadora de precios para ver el costo exacto según la cantidad de usuarios que necesitas.',
    },
    {
      q: '¿Cómo funciona el soporte?',
      a: 'Todos los planes incluyen soporte por correo y chat. El plan Profesional incluye soporte prioritario con respuesta en 4 horas. El plan Empresarial incluye un gerente de cuenta dedicado y soporte 24/7.',
    },
  ];

  let openIndex: number | null = null;

  function toggle(i: number) {
    openIndex = openIndex === i ? null : i;
  }
</script>

<section id="faq" class="bg-white py-24">
  <div class="max-w-2xl mx-auto px-6">
    <div class="text-center mb-12">
      <span class="inline-flex items-center gap-2 rounded-full bg-primary-light text-primary text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">
        FAQ
      </span>
      <h2 class="text-4xl font-jakarta font-bold text-slate-dark">
        Preguntas frecuentes
      </h2>
      <p class="text-base font-inter text-slate mt-3 max-w-md mx-auto">
        ¿Algo que no encontraste aquí? Escríbenos por WhatsApp o correo y te respondemos en minutos.
      </p>
    </div>

    <div class="divide-y divide-border">
      {#each faqs as faq, i}
        <div>
          <button
            type="button"
            class="w-full flex items-center justify-between gap-4 py-5 text-left focus:outline-none group"
            on:click={() => toggle(i)}
            aria-expanded={openIndex === i}
          >
            <span class="text-base font-jakarta font-semibold text-slate-dark group-hover:text-primary transition-colors">
              {faq.q}
            </span>
            <ChevronDown
              class="w-5 h-5 text-slate flex-shrink-0 transition-transform duration-200 {openIndex === i ? 'rotate-180 text-primary' : ''}"
            />
          </button>

          {#if openIndex === i}
            <div class="pb-5">
              <p class="text-sm font-inter text-slate leading-relaxed">{faq.a}</p>
            </div>
          {/if}
        </div>
      {/each}
    </div>

    <div class="mt-10 text-center">
      <p class="text-sm font-inter text-slate mb-3">¿Más preguntas?</p>
      <a
        href="https://wa.me/4012001999"
        target="_blank"
        rel="noopener noreferrer"
        class="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-jakarta font-semibold px-5 py-2.5 rounded-btn transition-colors shadow-soft"
      >
        <!-- WhatsApp icon inline -->
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>
          <path d="M12 0C5.373 0 0 5.373 0 12c0 2.123.558 4.115 1.535 5.836L.057 23.944l6.264-1.449A11.94 11.94 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.818a9.818 9.818 0 01-5.013-1.373l-.359-.214-3.724.861.882-3.624-.234-.373A9.818 9.818 0 012.182 12C2.182 6.567 6.567 2.182 12 2.182S21.818 6.567 21.818 12 17.433 21.818 12 21.818z"/>
        </svg>
        Chatear en WhatsApp
      </a>
    </div>
  </div>
</section>
