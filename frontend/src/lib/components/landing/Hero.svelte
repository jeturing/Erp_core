<script lang="ts">
  import { onMount } from 'svelte';
  import { t } from 'svelte-i18n';
  import { ArrowRight, Building2, Calculator, Handshake } from 'lucide-svelte';

  export let stats: any[] = [];
  /** Optional partner branding — used for future white-label hero customization */
  export const partnerBranding: any = null;

  $: displayStats = stats.length > 0 ? stats : [
    { value: '500+', label: $t('hero.stat_companies') },
    { value: '99.9%', label: $t('hero.stat_uptime') },
    { value: '24/7',  label: $t('hero.stat_support') },
    { value: '50+',   label: $t('hero.stat_partners') },
  ];

  // Dashboard mockup live metrics
  const metrics = [
    { label: 'Ingresos',  value: '$84,290', delta: '+12.4%', color: '#00FF9F' },
    { label: 'Clientes',  value: '1,847',   delta: '+8.1%',  color: '#0EA5E9' },
    { label: 'Facturas',  value: '342',      delta: '+5.3%',  color: '#a78bfa' },
    { label: 'Pendiente', value: '$9,140',   delta: '-2.1%',  color: '#f59e0b' },
  ];

  let visible = false;
  onMount(() => { requestAnimationFrame(() => { visible = true; }); });
</script>

<!--
  HERO — Jeturing Brand v2
  Design system: DESIGN.md (Linear.app-inspired dark canvas + Electric Green)
  Brand: Deep Blue #003B73 + Electric Green #00FF9F
-->
<section
  class="relative min-h-screen flex items-center justify-center overflow-hidden pt-20"
  style="background: #020e1f;"
>
  <!-- Layered background ambience -->
  <div class="absolute inset-0 pointer-events-none"
       style="background: radial-gradient(ellipse 80% 55% at 50% 0%, rgba(0,59,115,0.65) 0%, transparent 70%);"></div>
  <div class="absolute pointer-events-none"
       style="top:-80px;left:50%;transform:translateX(-50%);width:640px;height:420px;
              background:radial-gradient(ellipse at 50% 0%, rgba(0,255,159,0.11) 0%, transparent 65%);
              filter:blur(48px);"></div>
  <div class="absolute pointer-events-none"
       style="top:20%;left:-5%;width:500px;height:500px;
              background:radial-gradient(circle, rgba(0,59,115,0.28) 0%, transparent 70%);
              filter:blur(90px);"></div>
  <div class="absolute pointer-events-none"
       style="top:30%;right:-5%;width:400px;height:400px;
              background:radial-gradient(circle, rgba(6,182,212,0.10) 0%, transparent 70%);
              filter:blur(70px);"></div>
  <!-- bottom fade -->
  <div class="absolute bottom-0 left-0 right-0 h-48 pointer-events-none"
       style="background:linear-gradient(to bottom, transparent, #020e1f);"></div>
  <!-- subtle grid -->
  <div class="absolute inset-0 pointer-events-none"
       style="opacity:0.022;
              background-image:linear-gradient(rgba(255,255,255,0.6) 1px, transparent 1px),
                               linear-gradient(90deg,rgba(255,255,255,0.6) 1px, transparent 1px);
              background-size:60px 60px;"></div>

  <!-- ── Main content ── -->
  <div
    class="relative z-10 max-w-4xl mx-auto px-6 text-center"
    style="opacity:{visible?1:0}; transform:translateY({visible?0:18}px); transition:opacity 0.65s ease, transform 0.65s ease;"
  >
    <!-- Green pill label -->
    <div class="inline-flex items-center gap-2 rounded-full px-4 py-1.5 mb-8 text-[11px] font-inter font-semibold tracking-[0.10em] uppercase"
         style="background:rgba(0,255,159,0.09); border:1px solid rgba(0,255,159,0.28); color:#00FF9F;">
      <span class="w-1.5 h-1.5 rounded-full" style="background:#00FF9F; box-shadow:0 0 6px #00FF9F;"></span>
      {$t('hero.badge')}
    </div>

    <!-- Headline — compressed display type (Linear-inspired) -->
    <h1
      class="font-jakarta font-extrabold text-[#f0f4ff] mb-6 leading-[1.06]"
      style="font-size: clamp(2.4rem, 6vw, 3.9rem); letter-spacing: -1.8px;"
    >
      {$t('hero.headline')}<br />
      <span style="color:#00FF9F; text-shadow:0 0 36px rgba(0,255,159,0.35);">
        {$t('hero.headline_highlight')}
      </span>
    </h1>

    <!-- Subheading -->
    <p class="font-inter text-[#c8d3e8] max-w-2xl mx-auto mb-10 leading-relaxed"
       style="font-size:1.1rem; letter-spacing:-0.2px;">
      {$t('hero.subheading')}
    </p>

    <!-- Primary CTAs -->
    <div class="flex flex-col sm:flex-row items-center justify-center gap-3 mb-5">
      <a href="/signup"
         class="flex items-center gap-2 font-inter font-semibold text-[14px] px-7 py-3.5 rounded-lg w-full sm:w-auto justify-center transition-all duration-150 hover:-translate-y-px"
         style="background:#00FF9F; color:#020e1f; box-shadow:0 4px 18px rgba(0,255,159,0.30);"
         on:mouseenter={(e)=>e.currentTarget.style.boxShadow='0 8px 28px rgba(0,255,159,0.45)'}
         on:mouseleave={(e)=>e.currentTarget.style.boxShadow='0 4px 18px rgba(0,255,159,0.30)'}>
        {$t('common.get_started')}
        <ArrowRight class="w-4 h-4" />
      </a>
      <a href="/accountants"
         class="flex items-center gap-2 font-inter font-medium text-[14px] text-[#c8d3e8] px-7 py-3.5 rounded-lg w-full sm:w-auto justify-center transition-all hover:-translate-y-px"
         style="border:1px solid rgba(255,255,255,0.12); background:rgba(255,255,255,0.04);">
        <Calculator class="w-4 h-4 text-[#7a8fa6]" />
        {$t('common.join_accountant')}
      </a>
    </div>

    <!-- Role quick-links -->
    <div class="flex flex-wrap items-center justify-center gap-2.5 mb-8">
      {#each [
        { icon: Building2, label: 'Crear mi empresa', href: '/signup?mode=tenant' },
        { icon: Calculator, label: 'Soy contador',     href: '/signup?mode=accountant' },
        { icon: Handshake,  label: 'Quiero ser socio', href: '/partner-signup' },
      ] as item}
        <a href={item.href}
           class="inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 text-[12px] font-inter text-[#7a8fa6] transition-all hover:text-[#f0f4ff]"
           style="border:1px solid rgba(255,255,255,0.08); background:rgba(255,255,255,0.03);">
          {#if true}{@const C = item.icon as any}<C class="w-3.5 h-3.5" />{/if}
          {item.label}
        </a>
      {/each}
    </div>

    <!-- Trust line -->
    <p class="text-[12px] font-inter text-[#4a6080] mb-10">
      {$t('hero.trust_line')} · Sin tarjeta de crédito · Cancela cuando quieras
    </p>

    <!-- Stat badges -->
    <div class="flex flex-wrap justify-center gap-3 mb-14">
      {#each displayStats as stat}
        <div class="flex items-center gap-2 rounded-full px-5 py-2"
             style="border:1px solid rgba(255,255,255,0.08); background:rgba(255,255,255,0.04); backdrop-filter:blur(8px);">
          <span class="text-[15px] font-jakarta font-bold text-[#f0f4ff]">{stat.value}</span>
          <span class="text-[11px] font-inter text-[#7a8fa6]">{stat.label}</span>
        </div>
      {/each}
    </div>

    <!-- ── Dashboard mockup ── -->
    <div class="max-w-3xl mx-auto rounded-xl overflow-hidden"
         style="border:1px solid rgba(255,255,255,0.10);
                background:rgba(255,255,255,0.025);
                backdrop-filter:blur(20px);
                box-shadow:0 24px 80px rgba(0,0,0,0.60), 0 0 0 1px rgba(0,255,159,0.04);">
      <!-- Chrome bar -->
      <div class="flex items-center gap-2 px-4 py-3"
           style="background:rgba(255,255,255,0.04); border-bottom:1px solid rgba(255,255,255,0.08);">
        <span class="w-2.5 h-2.5 rounded-full" style="background:#ff5f56;"></span>
        <span class="w-2.5 h-2.5 rounded-full" style="background:#ffbd2e;"></span>
        <span class="w-2.5 h-2.5 rounded-full" style="background:#27c93f;"></span>
        <div class="flex-1 mx-4 rounded-md h-5 flex items-center px-3 gap-1.5"
             style="background:rgba(255,255,255,0.06);">
          <span class="w-2 h-2 rounded-full" style="background:rgba(0,255,159,0.5);"></span>
          <span class="text-[10px] font-mono" style="color:#4a6080;">app.sajet.us/dashboard</span>
        </div>
        <div class="flex gap-1.5">
          <div class="h-4 w-14 rounded text-[8px] flex items-center justify-center font-mono"
               style="background:rgba(0,255,159,0.14); color:#00FF9F;">● Live</div>
        </div>
      </div>

      <!-- Content -->
      <div class="p-5 space-y-4">
        <!-- Header row -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="h-3 w-28 rounded" style="background:rgba(255,255,255,0.12);"></div>
            <div class="h-3 w-14 rounded" style="background:rgba(255,255,255,0.06);"></div>
          </div>
          <div class="h-6 w-20 rounded-lg text-[9px] font-inter flex items-center justify-center"
               style="background:rgba(0,255,159,0.14); color:#00FF9F; border:1px solid rgba(0,255,159,0.20);">
            + Nueva factura
          </div>
        </div>

        <!-- Metric cards -->
        <div class="grid grid-cols-4 gap-3">
          {#each metrics as m}
            <div class="rounded-xl p-3.5 space-y-1.5"
                 style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.07);">
              <div class="text-[8px] font-inter uppercase tracking-widest" style="color:#4a6080;">{m.label}</div>
              <div class="text-[13px] font-mono font-semibold" style="color:{m.color};">{m.value}</div>
              <div class="text-[8px] font-inter px-1.5 py-0.5 rounded-full w-fit"
                   style="background:rgba(0,255,159,0.08); color:{m.color};">{m.delta}</div>
            </div>
          {/each}
        </div>

        <!-- Bar chart -->
        <div class="rounded-xl flex items-end px-3 pb-3 gap-1 pt-4"
             style="background:rgba(255,255,255,0.025); border:1px solid rgba(255,255,255,0.06); height:90px;">
          {#each [38,55,42,70,52,88,65,95,72,85,60,78] as h, i}
            <div class="flex-1 rounded-t"
                 style="height:{h}%; background:{i===7||i===11
                   ?'linear-gradient(to top,rgba(0,255,159,0.65),rgba(0,255,159,0.22))'
                   :'linear-gradient(to top,rgba(14,165,233,0.30),rgba(14,165,233,0.08))'};">
            </div>
          {/each}
        </div>

        <!-- Table rows -->
        <div class="space-y-1.5 pb-1">
          {#each [
            { name:'Distribuidora Nova', amount:'$3,200', status:'Pagado',   color:'#00FF9F' },
            { name:'Constructora Sur',   amount:'$1,850', status:'Pendiente',color:'#f59e0b' },
            { name:'Grupo Meridian LLC', amount:'$5,400', status:'Pagado',   color:'#00FF9F' },
          ] as row}
            <div class="flex gap-3 items-center px-3 py-2 rounded-lg"
                 style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05);">
              <div class="h-1.5 w-1.5 rounded-full" style="background:{row.color};"></div>
              <div class="text-[10px] font-inter flex-1" style="color:#c8d3e8;">{row.name}</div>
              <div class="text-[10px] font-mono" style="color:#f0f4ff;">{row.amount}</div>
              <div class="text-[8px] font-inter px-2 py-0.5 rounded-full"
                   style="color:{row.color}; border:1px solid rgba(0,255,159,0.18); background:rgba(0,255,159,0.07);">
                {row.status}
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>

  </div>
</section>
