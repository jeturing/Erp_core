<script>
  import { onMount } from 'svelte';
  let visible = false;

  onMount(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { visible = true; observer.disconnect(); } },
      { threshold: 0.1 }
    );
    const el = document.getElementById('testimonials-section');
    if (el) observer.observe(el);
  });

  const testimonials = [
    {
      quote: "SAJET redujo nuestro tiempo de cierre mensual de 3 días a menos de 4 horas. La integración con facturación electrónica fue transparente.",
      name: "María González",
      role: "CFO, TecHeels",
      initials: "MG",
    },
    {
      quote: "El soporte de Jeturing es excepcionalmente rápido. Tuvimos una integración bancaria corriendo en menos de una semana.",
      name: "Carlos Reyes",
      role: "Director TI, AgroLife",
      initials: "CR",
    },
    {
      quote: "Multi-tenancy real, no simulado. Cada cliente tiene su espacio aislado y eso nos dio la confianza para escalar.",
      name: "Laura Méndez",
      role: "CTO, Esecure",
      initials: "LM",
    },
  ];
</script>

<!-- Stripe: white section, blue-tinted elevation cards -->
<section id="testimonials-section" style="
  background:#f5f5f7;
  padding: clamp(80px,10vw,140px) 24px;
">
  <div style="max-width:1080px; margin:0 auto;">
    <div style="text-align:center; margin-bottom:72px;">
      <p style="
        font-size:13px; font-weight:600; letter-spacing:0.12em; text-transform:uppercase;
        color:#003B73; margin-bottom:16px;
        opacity:{visible?1:0}; transform:translateY({visible?'0px':'10px'});
        transition:opacity 0.5s cubic-bezier(.16,1,.3,1), transform 0.5s cubic-bezier(.16,1,.3,1);
      ">Testimonios</p>
      <h2 style="
        font-family:'Plus Jakarta Sans','Inter',system-ui,sans-serif;
        font-size:clamp(1.8rem,4.5vw,2.8rem); font-weight:700;
        letter-spacing:-0.035em; line-height:1.08;
        color:#061b31; margin:0;
        opacity:{visible?1:0}; transform:translateY({visible?'0px':'18px'});
        transition:opacity 0.6s 0.08s cubic-bezier(.16,1,.3,1), transform 0.6s 0.08s cubic-bezier(.16,1,.3,1);
      ">Lo que dicen nuestros clientes.</h2>
    </div>

    <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:24px;">
      {#each testimonials as t, i}
        <div style="
          background:#ffffff;
          border:1px solid #e5edf5;
          border-radius:8px;
          padding:36px 32px;
          box-shadow:rgba(50,50,93,0.25) 0px 30px 45px -30px, rgba(0,0,0,0.1) 0px 18px 36px -18px;
          display:flex; flex-direction:column; justify-content:space-between;
          opacity:{visible?1:0}; transform:translateY({visible?'0px':'24px'});
          transition:opacity 0.65s {0.12+i*0.1}s cubic-bezier(.16,1,.3,1), transform 0.65s {0.12+i*0.1}s cubic-bezier(.16,1,.3,1), box-shadow 0.25s;
        "
          on:mouseenter={e => { e.currentTarget.style.boxShadow='rgba(50,50,93,0.35) 0px 40px 60px -30px, rgba(0,0,0,0.12) 0px 24px 48px -18px'; }}
          on:mouseleave={e => { e.currentTarget.style.boxShadow='rgba(50,50,93,0.25) 0px 30px 45px -30px, rgba(0,0,0,0.1) 0px 18px 36px -18px'; }}
          role="article"
        >
          <!-- Quote mark -->
          <div style="font-size:48px; color:#003B73; opacity:0.15; line-height:1; margin-bottom:16px; font-family:Georgia,serif;">"</div>
          <p style="font-size:16px; line-height:1.65; color:#273951; font-weight:300; margin:0 0 32px; flex:1;">{t.quote}</p>
          <div style="display:flex; align-items:center; gap:12px;">
            <div style="
              width:40px; height:40px; border-radius:50%;
              background:linear-gradient(135deg,#003B73,#00569e);
              display:flex; align-items:center; justify-content:center;
              font-size:13px; font-weight:700; color:#00FF9F; flex-shrink:0;
            ">{t.initials}</div>
            <div>
              <div style="font-size:14px; font-weight:600; color:#061b31;">{t.name}</div>
              <div style="font-size:12px; color:#64748d; margin-top:1px;">{t.role}</div>
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>
</section>
