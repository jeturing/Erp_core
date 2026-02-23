<script lang="ts">
  import { t } from 'svelte-i18n';
  import { DollarSign, Palette, HeadphonesIcon } from 'lucide-svelte';

  const benefits = [
    {
      icon: DollarSign,
      title: $t('partners.recurring'),
      desc: $t('partners.recurring_desc'),
    },
    {
      icon: Palette,
      title: $t('partners.white_label'),
      desc: $t('partners.white_label_desc'),
    },
    {
      icon: HeadphonesIcon,
      title: $t('partners.support'),
      desc: $t('partners.support_desc'),
    },
  ];
</script>

<section id="partners" class="bg-[#0F172A] py-24">
  <div class="max-w-5xl mx-auto px-6">
    <div class="text-center mb-14">
      <span class="inline-flex items-center gap-2 rounded-full bg-emerald-500/15 text-emerald-400 text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">
        {$t('partners.title')}
      </span>
      <h2 class="text-4xl font-jakarta font-bold text-white mb-4">
        {$t('partners.subtitle')}
      </h2>
      <p class="text-base font-inter text-slate-400 max-w-xl mx-auto">
        {$t('partners.description')}
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
      {#each benefits as benefit}
        <div class="rounded-card-sm border border-white/10 bg-white/5 backdrop-blur-sm p-6 hover:border-emerald-400/30 hover:bg-white/[0.07] transition-all group">
          <div class="w-10 h-10 rounded-lg bg-emerald-500/15 flex items-center justify-center mb-4">
            <svelte:component this={benefit.icon} class="w-5 h-5 text-emerald-400" strokeWidth={1.5} />
          </div>
          <h3 class="text-base font-jakarta font-semibold text-white mb-2">{benefit.title}</h3>
          <p class="text-sm font-inter text-slate-400 leading-relaxed">{benefit.desc}</p>
        </div>
      {/each}
    </div>

    <div class="text-center">
      <a href="#/partner-signup" class="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-white font-jakarta font-semibold text-sm px-6 py-3 rounded-btn shadow-soft hover:shadow-medium transition-all">
        {$t('partners.cta')}
      </a>
    </div>
  </div>
</section>
