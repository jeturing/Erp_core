<script lang="ts">
  import { t } from 'svelte-i18n';
  import { Receipt, ChartColumn, Package, Users, Zap, BarChart3 } from 'lucide-svelte';

  const defaultFeatures = [
    { icon: Receipt,     title: $t('features.finance'),   desc: $t('features.finance_desc') },
    { icon: ChartColumn, title: $t('features.sales'),     desc: $t('features.sales_desc') },
    { icon: Package,     title: $t('features.inventory'), desc: $t('features.inventory_desc') },
    { icon: Users,       title: $t('features.hr'),        desc: $t('features.hr_desc') },
    { icon: Zap,         title: $t('features.payments'),  desc: $t('features.payments_desc') },
    { icon: BarChart3,   title: $t('features.reports'),   desc: $t('features.reports_desc') },
  ];

  export let features: any[] = [];
  $: displayFeatures = features.length > 0 ? features : defaultFeatures;
</script>

<!--
  FeaturesGrid v2 — Jeturing Brand
  Dark canvas + translucent cards + Electric Green icon accents
  Inspired by: Linear.app, Vercel (awesome-design-md)
-->
<section
  id="features"
  class="py-28"
  style="background:#020e1f; border-top:1px solid rgba(255,255,255,0.05);"
>
  <div class="relative max-w-6xl mx-auto px-6">

    <!-- Ambient glow -->
    <div class="absolute -top-16 left-1/2 -translate-x-1/2 w-[500px] h-[200px] pointer-events-none"
         style="background:radial-gradient(ellipse, rgba(0,59,115,0.30) 0%, transparent 70%); filter:blur(60px);"></div>

    <!-- Section header -->
    <div class="text-center mb-16">
      <span class="inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 mb-5 text-[11px] font-inter font-semibold tracking-[0.10em] uppercase"
            style="background:rgba(0,255,159,0.09); border:1px solid rgba(0,255,159,0.25); color:#00FF9F;">
        <span class="w-1 h-1 rounded-full" style="background:#00FF9F;"></span>
        {$t('features.title')}
      </span>
      <h2 class="font-jakarta font-bold text-[#f0f4ff] mb-4"
          style="font-size:clamp(1.75rem, 4vw, 2.4rem); letter-spacing:-0.8px;">
        {$t('features.subtitle')}
      </h2>
      <p class="font-inter text-[#7a8fa6] max-w-xl mx-auto leading-relaxed text-[15px]">
        Todo lo que tu empresa necesita, en una sola plataforma.
      </p>
    </div>

    <!-- Cards grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {#each displayFeatures as feature}
        <div
          role="article"
          class="rounded-xl p-6 transition-all duration-200 cursor-default"
          style="background:rgba(255,255,255,0.025); border:1px solid rgba(255,255,255,0.07);"
          on:mouseenter={(e) => {
            e.currentTarget.style.background='rgba(0,255,159,0.04)';
            e.currentTarget.style.borderColor='rgba(0,255,159,0.22)';
            e.currentTarget.style.transform='translateY(-2px)';
            e.currentTarget.style.boxShadow='0 8px 32px rgba(0,0,0,0.35)';
          }}
          on:mouseleave={(e) => {
            e.currentTarget.style.background='rgba(255,255,255,0.025)';
            e.currentTarget.style.borderColor='rgba(255,255,255,0.07)';
            e.currentTarget.style.transform='translateY(0)';
            e.currentTarget.style.boxShadow='none';
          }}
        >
          <!-- Icon — Electric Green -->
          <div class="w-9 h-9 rounded-lg flex items-center justify-center mb-4"
               style="background:rgba(0,255,159,0.10); border:1px solid rgba(0,255,159,0.18);">
            {#if feature.icon}
              <svelte:component this={feature.icon} class="w-4 h-4" strokeWidth={1.5} style="color:#00FF9F;" />
            {/if}
          </div>
          <!-- Title -->
          <h3 class="font-jakarta font-semibold text-[#f0f4ff] mb-2 text-[15px]" style="letter-spacing:-0.2px;">
            {feature.title}
          </h3>
          <!-- Desc -->
          <p class="font-inter text-[#7a8fa6] text-[13px] leading-relaxed">
            {feature.desc}
          </p>
        </div>
      {/each}
    </div>

    <!-- Bottom ambient -->
    <div class="absolute -bottom-16 left-1/2 -translate-x-1/2 w-[600px] h-[180px] pointer-events-none"
         style="background:radial-gradient(ellipse, rgba(0,59,115,0.18) 0%, transparent 70%); filter:blur(60px);"></div>
  </div>
</section>
