<script lang="ts">
  import { t } from 'svelte-i18n';
  import { Receipt, ChartColumn, Package, Users, Zap, BarChart3 } from 'lucide-svelte';

  // Iconos mappeados a categorías de módulos
  const defaultFeatures = [
    {
      icon: Receipt,
      title: $t('features.finance'),
      desc: $t('features.finance_desc'),
    },
    {
      icon: ChartColumn,
      title: $t('features.sales'),
      desc: $t('features.sales_desc'),
    },
    {
      icon: Package,
      title: $t('features.inventory'),
      desc: $t('features.inventory_desc'),
    },
    {
      icon: Users,
      title: $t('features.hr'),
      desc: $t('features.hr_desc'),
    },
    {
      icon: Zap,
      title: $t('features.payments'),
      desc: $t('features.payments_desc'),
    },
    {
      icon: BarChart3,
      title: $t('features.reports'),
      desc: $t('features.reports_desc'),
    },
  ];

  export let features: any[] = [];

  $: displayFeatures = features.length > 0 ? features : defaultFeatures;
</script>

<section id="features" class="bg-gradient-subtle py-24">
  <div class="max-w-6xl mx-auto px-6">
    <div class="text-center mb-16">
      <span class="inline-flex items-center gap-2 rounded-full bg-primary-light text-primary text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">
        {$t('features.title')}
      </span>
      <h2 class="text-4xl font-jakarta font-bold text-slate-dark mb-4">
        {$t('features.subtitle')}
      </h2>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {#each displayFeatures as feature}
        <div class="rounded-card-sm border border-border bg-white p-6 hover:shadow-medium hover:border-primary/20 transition-all group">
          <div class="w-10 h-10 rounded-lg bg-primary-light flex items-center justify-center mb-4 group-hover:bg-primary/10 transition-colors">
            {#if feature.icon}
              <svelte:component this={feature.icon} class="w-5 h-5 text-primary" strokeWidth={1.5} />
            {/if}
          </div>
          <h3 class="text-base font-jakarta font-semibold text-slate-dark mb-2">{feature.title}</h3>
          <p class="text-sm font-inter text-slate leading-relaxed">{feature.desc}</p>
        </div>
      {/each}
    </div>
  </div>
</section>
