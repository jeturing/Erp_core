<script>
  import { onMount } from 'svelte';
  let visible = false;

  onMount(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { visible = true; observer.disconnect(); } },
      { threshold: 0.15 }
    );
    const el = document.getElementById('valueprop-section');
    if (el) observer.observe(el);
  });
</script>

<!-- Apple rhythm: white/light section alternating with dark -->
<section id="valueprop-section" style="
  background: #f5f5f7;
  padding: clamp(80px, 10vw, 140px) 24px;
">
  <div style="max-width:960px; margin:0 auto; text-align:center;">

    <p style="
      font-size:13px; font-weight:600; letter-spacing:0.12em; text-transform:uppercase;
      color:#003B73; margin-bottom:20px;
      opacity:{visible?1:0};
      transform:translateY({visible?'0px':'12px'});
      transition:opacity 0.55s cubic-bezier(.16,1,.3,1), transform 0.55s cubic-bezier(.16,1,.3,1);
    ">Por qué SAJET</p>

    <h2 style="
      font-family:'Plus Jakarta Sans','Inter',system-ui,sans-serif;
      font-size:clamp(2rem,5vw,3rem); font-weight:700;
      letter-spacing:-0.03em; line-height:1.08;
      color:#061b31; margin:0 0 24px;
      opacity:{visible?1:0};
      transform:translateY({visible?'0px':'20px'});
      transition:opacity 0.65s 0.1s cubic-bezier(.16,1,.3,1), transform 0.65s 0.1s cubic-bezier(.16,1,.3,1);
    ">Un ERP diseñado para<br/>la forma en que trabajas hoy.</h2>

    <p style="
      font-size:18px; line-height:1.6; color:#64748d; max-width:560px; margin:0 auto 64px;
      font-weight:300;
      opacity:{visible?1:0};
      transform:translateY({visible?'0px':'16px'});
      transition:opacity 0.65s 0.18s cubic-bezier(.16,1,.3,1), transform 0.65s 0.18s cubic-bezier(.16,1,.3,1);
    ">Sin instalaciones complicadas, sin curvas de aprendizaje interminables.
    Operativo desde el primer día.</p>

    <!-- Stripe-style metric cards with blue-tinted shadows -->
    <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:24px;">
      {#each [
        { num:'98%',  label:'Uptime garantizado', icon:'⚡' },
        { num:'<2h',  label:'Tiempo de onboarding', icon:'🚀' },
        { num:'40+',  label:'Módulos activos', icon:'🧩' },
        { num:'100%', label:'Datos en tu control', icon:'🔒' },
      ] as item, i}
        <div style="
          background:#ffffff;
          border:1px solid #e5edf5;
          border-radius:8px;
          padding:32px 24px;
          box-shadow:rgba(50,50,93,0.25) 0px 30px 45px -30px, rgba(0,0,0,0.1) 0px 18px 36px -18px;
          opacity:{visible?1:0};
          transform:translateY({visible?'0px':'24px'});
          transition:opacity 0.65s {0.22+i*0.07}s cubic-bezier(.16,1,.3,1), transform 0.65s {0.22+i*0.07}s cubic-bezier(.16,1,.3,1), box-shadow 0.25s, translate 0.25s;
        "
          on:mouseenter={e => { e.currentTarget.style.transform='translateY(-4px)'; e.currentTarget.style.boxShadow='rgba(50,50,93,0.35) 0px 40px 55px -30px, rgba(0,0,0,0.12) 0px 24px 48px -18px'; }}
          on:mouseleave={e => { e.currentTarget.style.transform=''; e.currentTarget.style.boxShadow='rgba(50,50,93,0.25) 0px 30px 45px -30px, rgba(0,0,0,0.1) 0px 18px 36px -18px'; }}
          role="article"
        >
          <div style="font-size:28px; margin-bottom:12px;">{item.icon}</div>
          <div style="font-size:clamp(2rem,4vw,2.8rem); font-weight:700; color:#003B73; letter-spacing:-0.04em; font-variant-numeric:tabular-nums;">{item.num}</div>
          <div style="font-size:13px; color:#64748d; margin-top:6px; font-weight:400;">{item.label}</div>
        </div>
      {/each}
    </div>

  </div>
</section>
