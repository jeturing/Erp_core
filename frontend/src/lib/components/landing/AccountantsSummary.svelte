<script lang="ts">
  import { t } from 'svelte-i18n';
  import { Calculator, ArrowRight, Eye, Building2, RefreshCw } from 'lucide-svelte';

  const benefits = [
    {
      icon: Eye,
      title: $t('accountants.benefit1_title'),
      desc: $t('accountants.benefit1_desc'),
    },
    {
      icon: Building2,
      title: $t('accountants.benefit2_title'),
      desc: $t('accountants.benefit2_desc'),
    },
    {
      icon: RefreshCw,
      title: $t('accountants.benefit3_title'),
      desc: $t('accountants.benefit3_desc'),
    },
  ];
</script>

<section class="bg-white py-24 border-t border-border">
  <div class="max-w-5xl mx-auto px-6">
    <div class="text-center mb-14">
      <span class="inline-flex items-center gap-2 rounded-full bg-blue-50 text-primary text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">
        <Calculator class="w-3.5 h-3.5" />
        {$t('accountants.badge')}
      </span>
      <h2 class="text-4xl font-jakarta font-bold text-slate-dark mb-4 whitespace-pre-line">
        {$t('accountants.headline')}<br />
        {$t('accountants.headline_highlight')}
      </h2>
      <p class="text-base font-inter text-slate max-w-xl mx-auto leading-relaxed">
        {$t('accountants.subheading')}
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
      {#each benefits as benefit}
        <div class="rounded-card-sm border border-border bg-cloud/50 p-6 hover:shadow-soft transition-all group">
          <div class="w-10 h-10 rounded-lg bg-primary-light flex items-center justify-center mb-4">
            <svelte:component this={benefit.icon} class="w-5 h-5 text-primary" strokeWidth={1.5} />
          </div>
          <h3 class="text-base font-jakarta font-semibold text-slate-dark mb-2">{benefit.title}</h3>
          <p class="text-sm font-inter text-slate leading-relaxed">{benefit.desc}</p>
        </div>
      {/each}
    </div>

    <div class="text-center">
      <a
        href="/accountants"
        class="inline-flex items-center gap-2 bg-primary hover:bg-navy text-white font-jakarta font-semibold text-sm px-6 py-3 rounded-btn shadow-soft hover:shadow-medium transition-all"
      >
        {$t('accountants.cta')}
        <ArrowRight class="w-4 h-4" />
      </a>
    </div>
  </div>
</section>
