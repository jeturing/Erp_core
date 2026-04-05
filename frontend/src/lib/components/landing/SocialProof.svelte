<script>
  import { onMount } from 'svelte';
  let visible = false;

  onMount(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { visible = true; observer.disconnect(); } },
      { threshold: 0.2 }
    );
    const el = document.getElementById('socialproof-section');
    if (el) observer.observe(el);
  });

  const logos = ['TecHeels', 'AgroLife', 'Esecure', 'Partner+', 'Socios +'];
</script>

<!-- Stripe: white section with blue-tinted shadows, crisp -->
<section id="socialproof-section" style="
  background:#ffffff;
  border-top:1px solid #e5edf5;
  border-bottom:1px solid #e5edf5;
  padding:56px 24px;
">
  <div style="max-width:960px; margin:0 auto; text-align:center;">
    <p style="
      font-size:12px; font-weight:600; letter-spacing:0.12em; text-transform:uppercase;
      color:#64748d; margin-bottom:40px;
      opacity:{visible?1:0}; transform:translateY({visible?'0px':'10px'});
      transition:opacity 0.5s cubic-bezier(.16,1,.3,1), transform 0.5s cubic-bezier(.16,1,.3,1);
    ">Empresas que confían en SAJET</p>

    <div style="display:flex; gap:48px; justify-content:center; flex-wrap:wrap; align-items:center;">
      {#each logos as logo, i}
        <div style="
          font-family:'Plus Jakarta Sans',system-ui,sans-serif;
          font-size:15px; font-weight:700; letter-spacing:-0.02em;
          color:#273951; opacity:{visible?0.6:0};
          transform:translateY({visible?'0px':'8px'});
          transition:opacity 0.5s {0.1+i*0.06}s cubic-bezier(.16,1,.3,1), transform 0.5s {0.1+i*0.06}s cubic-bezier(.16,1,.3,1);
        ">{logo}</div>
      {/each}
    </div>

    <!-- Stats row -->
    <div style="display:flex; gap:48px; justify-content:center; flex-wrap:wrap; margin-top:56px; padding-top:40px; border-top:1px solid #e5edf5;">
      {#each [
        { num:'150+', label:'Tenants activos' },
        { num:'99.8%', label:'Uptime 2025' },
        { num:'4.9★', label:'Satisfacción media' },
      ] as stat, i}
        <div style="
          text-align:center;
          opacity:{visible?1:0}; transform:translateY({visible?'0px':'12px'});
          transition:opacity 0.6s {0.3+i*0.08}s cubic-bezier(.16,1,.3,1), transform 0.6s {0.3+i*0.08}s cubic-bezier(.16,1,.3,1);
        ">
          <div style="font-size:2.2rem; font-weight:700; color:#003B73; letter-spacing:-0.04em; font-variant-numeric:tabular-nums;">{stat.num}</div>
          <div style="font-size:13px; color:#64748d; margin-top:4px;">{stat.label}</div>
        </div>
      {/each}
    </div>
  </div>
</section>
