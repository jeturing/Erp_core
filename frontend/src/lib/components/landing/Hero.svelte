<script lang="ts">
  import { t } from 'svelte-i18n';
  import { ArrowRight, Play } from 'lucide-svelte';

  export let stats: any[] = [];
  export let partnerBranding: any = null;

  // Fallback stats
  $: displayStats = stats.length > 0 ? stats : [
    { value: '500+', label: 'Companies' },
    { value: '99.9%', label: 'Uptime' },
    { value: '24/7', label: 'Support' },
    { value: '50+', label: 'Partners' },
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
    <div class="flex flex-col sm:flex-row items-center justify-center gap-4 mb-10">
      <a
        href="#/customer-onboarding"
        class="flex items-center gap-2 text-navy font-inter font-semibold text-[15px] px-8 py-4 rounded-btn transition-all hover:-translate-y-px hover:shadow-elevated w-full sm:w-auto"
        style="background: white"
      >
        {$t('common.start_free_trial')}
        <ArrowRight class="w-4 h-4" />
      </a>
      <a
        href="#/demo"
        class="flex items-center gap-2 border border-white/30 text-white hover:bg-white/10 font-inter font-medium text-[15px] px-8 py-4 rounded-btn transition-all w-full sm:w-auto"
      >
        <Play class="w-4 h-4" />
        {$t('common.see_demo')}
      </a>
    </div>

    <!-- Trust line -->
    <p class="text-sm font-inter text-blue-200/60 mb-12">
      {$t('hero.trust_line')}
    </p>

    <!-- Stats badges -->
    <div class="flex flex-wrap justify-center gap-4">
      {#each displayStats as stat}
        <div class="flex items-center gap-2 rounded-full border border-white/15 bg-white/5 backdrop-blur-sm px-5 py-2.5">
          <span class="text-base font-jakarta font-bold text-white">{stat.value}</span>
          <span class="text-xs font-inter text-blue-200/70">{stat.label}</span>
        </div>
      {/each}
    </div>
  </div>
</section>
