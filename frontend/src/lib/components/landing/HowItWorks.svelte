<script>
  import { onMount } from 'svelte';
  let visible = false;

  onMount(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { visible = true; observer.disconnect(); } },
      { threshold: 0.12 }
    );
    const el = document.getElementById('howitworks-section');
    if (el) observer.observe(el);
  });

  const steps = [
    { num:'01', title:'Crea tu cuenta', desc:'Regístrate en minutos. Sin tarjeta, sin contratos. Solo tus datos.', color:'rgba(0,59,115,0.08)' },
    { num:'02', title:'Configura tu espacio', desc:'Personaliza módulos, usuarios y permisos según tu estructura.', color:'rgba(0,255,159,0.06)' },
    { num:'03', title:'Conecta tus sistemas', desc:'APIs abiertas para integrarse con lo que ya usas: bancos, facturación, CRM.', color:'rgba(0,59,115,0.08)' },
    { num:'04', title:'Opera y crece', desc:'Dashboards en tiempo real, reportes automáticos, alertas inteligentes.', color:'rgba(0,255,159,0.06)' },
  ];
</script>

<!-- Apple: dark cinematic section -->
<section id="howitworks-section" style="
  background: #000000;
  padding: clamp(80px, 10vw, 140px) 24px;
  position:relative; overflow:hidden;
">
  <!-- Ambient glow top-left -->
  <div style="position:absolute;top:-120px;left:-80px;width:500px;height:500px;border-radius:50%;background:radial-gradient(circle,rgba(0,59,115,0.3) 0%,transparent 70%);pointer-events:none;"></div>
  <!-- Ambient glow right -->
  <div style="position:absolute;bottom:-80px;right:-60px;width:400px;height:400px;border-radius:50%;background:radial-gradient(circle,rgba(0,255,159,0.08) 0%,transparent 70%);pointer-events:none;"></div>

  <div style="max-width:960px; margin:0 auto; position:relative; z-index:1;">

    <div style="text-align:center; margin-bottom:72px;">
      <p style="
        font-size:13px; font-weight:600; letter-spacing:0.12em; text-transform:uppercase;
        color:#00FF9F; margin-bottom:16px;
        opacity:{visible?1:0}; transform:translateY({visible?'0px':'12px'});
        transition:opacity 0.5s cubic-bezier(.16,1,.3,1), transform 0.5s cubic-bezier(.16,1,.3,1);
      ">Cómo funciona</p>
      <h2 style="
        font-family:'Plus Jakarta Sans','Inter',system-ui,sans-serif;
        font-size:clamp(2rem,5vw,3rem); font-weight:700;
        letter-spacing:-0.035em; line-height:1.07;
        color:#f5f5f7; margin:0;
        opacity:{visible?1:0}; transform:translateY({visible?'0px':'20px'});
        transition:opacity 0.6s 0.08s cubic-bezier(.16,1,.3,1), transform 0.6s 0.08s cubic-bezier(.16,1,.3,1);
      ">De cero a operando<br/>en cuatro pasos.</h2>
    </div>

    <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:2px; background:rgba(255,255,255,0.04); border-radius:12px; overflow:hidden;">
      {#each steps as step, i}
        <div style="
          background:#111111;
          padding:40px 28px;
          border-right: {i<steps.length-1 ? '1px solid rgba(255,255,255,0.06)' : 'none'};
          opacity:{visible?1:0}; transform:translateY({visible?'0px':'28px'});
          transition:opacity 0.65s {0.15+i*0.09}s cubic-bezier(.16,1,.3,1), transform 0.65s {0.15+i*0.09}s cubic-bezier(.16,1,.3,1), background 0.2s;
        "
          on:mouseenter={e => e.currentTarget.style.background='#1a1a1a'}
          on:mouseleave={e => e.currentTarget.style.background='#111111'}
          role="article"
        >
          <div style="font-size:11px; font-weight:700; letter-spacing:0.15em; color:#00FF9F; margin-bottom:20px; font-variant-numeric:tabular-nums;">{step.num}</div>
          <h3 style="font-size:18px; font-weight:600; color:#f5f5f7; margin:0 0 12px; letter-spacing:-0.02em;">{step.title}</h3>
          <p style="font-size:14px; line-height:1.65; color:rgba(245,245,247,0.55); margin:0; font-weight:300;">{step.desc}</p>
        </div>
      {/each}
    </div>

  </div>
</section>
