<script lang="ts">
  import { t } from 'svelte-i18n';
  import { GitMerge, Cloud, Building2 } from 'lucide-svelte';

  const pillars = [
    {
      icon: GitMerge,
      title: $t('value_prop.one_source'),
      desc: $t('value_prop.one_source_desc'),
    },
    {
      icon: Cloud,
      title: $t('value_prop.managed_cloud'),
      desc: $t('value_prop.managed_cloud_desc'),
    },
    {
      icon: Building2,
      title: $t('value_prop.multi_company'),
      desc: $t('value_prop.multi_company_desc'),
    },
  ];
</script>

<section class="bg-white py-24">
  <div class="max-w-6xl mx-auto px-6">
    <div class="text-center mb-16">
      <span class="inline-flex items-center gap-2 rounded-full bg-primary-light text-primary text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">
        {$t('value_prop.badge')}
      </span>
      <h2 class="text-4xl font-jakarta font-bold text-slate-dark mb-4 whitespace-pre-line">
        {$t('value_prop.headline')}
      </h2>
      <p class="text-lg font-inter text-slate max-w-xl mx-auto leading-relaxed">
        {$t('value_prop.subheading')}
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      {#each pillars as pillar}
        <div class="rounded-card-lg border border-border bg-white p-8 hover:shadow-medium transition-all group">
          <div class="w-12 h-12 rounded-card-sm bg-primary-light flex items-center justify-center mb-5 group-hover:bg-primary/10 transition-colors">
            <svelte:component this={pillar.icon} class="w-6 h-6 text-primary" strokeWidth={1.5} />
          </div>
          <h3 class="text-xl font-jakarta font-semibold text-slate-dark mb-3">{pillar.title}</h3>
          <p class="text-base font-inter text-slate leading-relaxed">{pillar.desc}</p>
        </div>
      {/each}
    </div>
  </div>
</section>
