<script>
  import { onMount } from 'svelte';
  let visible = false;
  let open = null;

  onMount(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { visible = true; observer.disconnect(); } },
      { threshold: 0.1 }
    );
    const el = document.getElementById('faq-section');
    if (el) observer.observe(el);
  });

  const faqs = [
    { q:'¿Cuánto tiempo toma implementar SAJET?', a:'La mayoría de tenants están operativos en menos de 2 horas. Incluye onboarding asistido, migración de datos básica y configuración inicial de módulos.' },
    { q:'¿Puedo migrar mis datos desde otro ERP?', a:'Sí. Ofrecemos conectores para los principales ERPs del mercado y servicio de migración asistida para datos históricos.' },
    { q:'¿Cómo funciona la facturación electrónica?', a:'SAJET integra nativamente con los servicios de la DGII (República Dominicana) y otros sistemas fiscales latinoamericanos. El módulo e-CF está incluido en todos los planes.' },
    { q:'¿Mis datos están seguros?', a:'Infraestructura propia en servidores dedicados, cifrado AES-256 en reposo y TLS 1.3 en tránsito, backups diarios con retención de 30 días, y aislamiento total por tenant.' },
    { q:'¿Tienen soporte en español?', a:'Todo nuestro equipo de soporte opera en español, con horario extendido y SLA de respuesta < 4 horas en planes Professional y Enterprise.' },
  ];
</script>

<!-- Apple: dark section -->
<section id="faq-section" style="
  background:#000000;
  padding: clamp(80px,10vw,140px) 24px;
">
  <div style="max-width:720px; margin:0 auto;">
    <div style="text-align:center; margin-bottom:64px;">
      <p style="
        font-size:13px; font-weight:600; letter-spacing:0.12em; text-transform:uppercase;
        color:#00FF9F; margin-bottom:16px;
        opacity:{visible?1:0}; transform:translateY({visible?'0px':'10px'});
        transition:opacity 0.5s cubic-bezier(.16,1,.3,1), transform 0.5s cubic-bezier(.16,1,.3,1);
      ">Preguntas frecuentes</p>
      <h2 style="
        font-family:'Plus Jakarta Sans','Inter',system-ui,sans-serif;
        font-size:clamp(1.8rem,4.5vw,2.8rem); font-weight:700;
        letter-spacing:-0.035em; line-height:1.08;
        color:#f5f5f7; margin:0;
        opacity:{visible?1:0}; transform:translateY({visible?'0px':'18px'});
        transition:opacity 0.6s 0.08s cubic-bezier(.16,1,.3,1), transform 0.6s 0.08s cubic-bezier(.16,1,.3,1);
      ">Todo lo que necesitas saber.</h2>
    </div>

    <div style="display:flex; flex-direction:column; gap:2px;">
      {#each faqs as faq, i}
        <div style="
          border-bottom:1px solid rgba(255,255,255,0.08);
          opacity:{visible?1:0}; transform:translateY({visible?'0px':'16px'});
          transition:opacity 0.6s {0.1+i*0.07}s cubic-bezier(.16,1,.3,1), transform 0.6s {0.1+i*0.07}s cubic-bezier(.16,1,.3,1);
        ">
          <button
            style="
              width:100%; text-align:left; padding:24px 0; background:none; border:none;
              cursor:pointer; display:flex; justify-content:space-between; align-items:center; gap:16px;
            "
            on:click={() => open = open === i ? null : i}
          >
            <span style="font-size:17px; font-weight:500; color:{open===i?'#00FF9F':'#f5f5f7'}; line-height:1.4; letter-spacing:-0.01em; transition:color 0.2s;">{faq.q}</span>
            <span style="
              color:{open===i?'#00FF9F':'rgba(245,245,247,0.4)'};
              font-size:20px; flex-shrink:0; transform:rotate({open===i?45:0}deg);
              transition:transform 0.25s cubic-bezier(.16,1,.3,1), color 0.2s;
            ">+</span>
          </button>
          {#if open === i}
            <div style="padding:0 0 24px; font-size:15px; line-height:1.7; color:rgba(245,245,247,0.6); font-weight:300;">
              {faq.a}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  </div>
</section>
