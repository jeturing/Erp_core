<script lang="ts">
  import { t } from 'svelte-i18n';
  import { ArrowRight, Building2, Calculator, Handshake } from 'lucide-svelte';

  export let stats: any[] = [];
  export let partnerBranding: any = null;

  // Fallback stats
  $: displayStats = stats.length > 0 ? stats : [
    { value: '500+', label: $t('hero.stat_companies') },
    { value: '99.9%', label: $t('hero.stat_uptime') },
    { value: '24/7', label: $t('hero.stat_support') },
    { value: '50+', label: $t('hero.stat_partners') },
  ];

  $: bgColor = partnerBranding?.primary_color || '#1B4FD8';
</script>

<section class="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
  <!-- Background gradient -->
  <div class="absolute inset-0 bg-gradient-hero pointer-events-none"></div>
  <div class="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full bg-secondary/10 blur-3xl pointer-events-none"></div>

  <div class="relative z-10 max-w-4xl mx-auto px-6 text-center">
    <!-- Badge -->
    <div class="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-5 py-2 mb-8 backdrop-blur-sm">
      <span class="text-xs font-inter font-medium text-white/90 tracking-[0.08em] uppercase">
        ✦ {$t('hero.badge')}
      </span>
    </div>

    <!-- Headline -->
    <h1 class="text-5xl sm:text-6xl lg:text-7xl font-jakarta font-extrabold text-white leading-[1.1] mb-6">
      {$t('hero.headline')}<br />
      <span class="bg-clip-text text-transparent bg-gradient-to-r from-white via-blue-200 to-secondary">
        {$t('hero.headline_highlight')}
      </span>
    </h1>

    <!-- Subtext -->
    <p class="text-lg font-inter text-blue-100/80 max-w-2xl mx-auto mb-10 leading-relaxed">
      {$t('hero.subheading')}
    </p>

    <!-- CTA buttons -->
    <div class="flex flex-col sm:flex-row items-center justify-center gap-4 mb-5">
      <a
        href="/signup"
        class="flex items-center gap-2 text-navy font-inter font-semibold text-[15px] px-8 py-4 rounded-btn transition-all hover:-translate-y-px hover:shadow-elevated w-full sm:w-auto"
        style="background: white"
      >
        {$t('common.get_started')}
        <ArrowRight class="w-4 h-4" />
      </a>
      <a
        href="/accountants"
        class="flex items-center gap-2 border border-white/30 text-white hover:bg-white/10 font-inter font-medium text-[15px] px-8 py-4 rounded-btn transition-all w-full sm:w-auto"
      >
        <Calculator class="w-4 h-4" />
        {$t('common.join_accountant')}
      </a>
    </div>

    <div class="flex flex-wrap items-center justify-center gap-3 mb-10">
      <a
        href="/signup?mode=tenant"
        class="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-inter text-white/85 transition-all hover:bg-white/15"
      >
        <Building2 class="w-4 h-4" />
        Crear mi empresa
      </a>
      <a
        href="/signup?mode=accountant"
        class="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-inter text-white/85 transition-all hover:bg-white/15"
      >
        <Calculator class="w-4 h-4" />
        Soy contador
      </a>
      <a
        href="/partner-signup"
        class="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-inter text-white/85 transition-all hover:bg-white/15"
      >
        <Handshake class="w-4 h-4" />
        Quiero ser socio
      </a>
    </div>

    <!-- Trust line -->
    <p class="text-sm font-inter text-blue-200/60 mb-12">
      {$t('hero.trust_line')} · Cliente, contador o socio: cada ruta tiene su propio onboarding.
    </p>

    <!-- Stats badges -->
    <div class="flex flex-wrap justify-center gap-4 mb-14">
      {#each displayStats as stat}
        <div class="flex items-center gap-2 rounded-full border border-white/15 bg-white/5 backdrop-blur-sm px-5 py-2.5">
          <span class="text-base font-jakarta font-bold text-white">{stat.value}</span>
          <span class="text-xs font-inter text-blue-200/70">{stat.label}</span>
        </div>
      {/each}
    </div>

    <!-- Browser-frame mockup placeholder -->
    <div class="max-w-3xl mx-auto">
      <div class="rounded-xl border border-white/15 bg-white/5 backdrop-blur-md shadow-elevated overflow-hidden">
        <!-- Title bar -->
        <div class="flex items-center gap-2 px-4 py-2.5 bg-white/10 border-b border-white/10">
          <span class="w-3 h-3 rounded-full bg-red-400/80"></span>
          <span class="w-3 h-3 rounded-full bg-yellow-400/80"></span>
          <span class="w-3 h-3 rounded-full bg-green-400/80"></span>
          <span class="flex-1 mx-4 rounded-md bg-white/10 h-5 flex items-center px-3">
            <span class="text-[10px] text-blue-200/50 font-mono">app.sajet.us/dashboard</span>
          </span>
        </div>
        <!-- Content area — placeholder skeleton -->
        <div class="p-6 space-y-4">
          <!-- Top bar -->
          <div class="flex items-center justify-between">
            <div class="h-4 w-32 rounded bg-white/10"></div>
            <div class="flex gap-2">
              <div class="h-4 w-16 rounded bg-white/10"></div>
              <div class="h-4 w-16 rounded bg-secondary/30"></div>
            </div>
          </div>
          <!-- Metric cards row -->
          <div class="grid grid-cols-4 gap-3">
            <div class="rounded-lg bg-white/10 p-4 space-y-2">
              <div class="h-3 w-14 rounded bg-white/15"></div>
              <div class="h-6 w-20 rounded bg-secondary/25"></div>
            </div>
            <div class="rounded-lg bg-white/10 p-4 space-y-2">
              <div class="h-3 w-14 rounded bg-white/15"></div>
              <div class="h-6 w-16 rounded bg-emerald-400/25"></div>
            </div>
            <div class="rounded-lg bg-white/10 p-4 space-y-2">
              <div class="h-3 w-14 rounded bg-white/15"></div>
              <div class="h-6 w-18 rounded bg-amber-400/25"></div>
            </div>
            <div class="rounded-lg bg-white/10 p-4 space-y-2">
              <div class="h-3 w-14 rounded bg-white/15"></div>
              <div class="h-6 w-14 rounded bg-violet-400/25"></div>
            </div>
          </div>
          <!-- Chart area -->
          <div class="rounded-lg bg-white/10 h-32 flex items-end px-4 pb-3 gap-2">
            <div class="w-8 bg-secondary/30 rounded-t" style="height: 40%"></div>
            <div class="w-8 bg-secondary/30 rounded-t" style="height: 65%"></div>
            <div class="w-8 bg-secondary/30 rounded-t" style="height: 50%"></div>
            <div class="w-8 bg-secondary/30 rounded-t" style="height: 80%"></div>
            <div class="w-8 bg-secondary/30 rounded-t" style="height: 55%"></div>
            <div class="w-8 bg-secondary/30 rounded-t" style="height: 90%"></div>
            <div class="w-8 bg-secondary/30 rounded-t" style="height: 70%"></div>
            <div class="w-8 bg-secondary/40 rounded-t" style="height: 95%"></div>
          </div>
          <!-- Table rows -->
          <div class="space-y-2">
            <div class="flex gap-3 items-center">
              <div class="h-3 w-24 rounded bg-white/10"></div>
              <div class="h-3 flex-1 rounded bg-white/5"></div>
              <div class="h-3 w-16 rounded bg-emerald-400/20"></div>
            </div>
            <div class="flex gap-3 items-center">
              <div class="h-3 w-20 rounded bg-white/10"></div>
              <div class="h-3 flex-1 rounded bg-white/5"></div>
              <div class="h-3 w-16 rounded bg-amber-400/20"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
