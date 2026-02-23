<script lang="ts">
  import { t } from 'svelte-i18n';

  const industryKeys = [
    'industry_retail',
    'industry_manufacturing',
    'industry_services',
    'industry_healthcare',
    'industry_distribution',
    'industry_consulting',
  ];

  const industryIcons = ['🛒', '🏭', '💼', '🏥', '🚚', '📋'];
</script>

<section class="bg-cloud py-16 border-y border-border">
  <div class="max-w-6xl mx-auto px-6">
    <p class="text-center text-sm font-inter text-slate tracking-wide mb-8">
      {$t('social_proof.trusted_by')}
    </p>
    <div class="flex flex-wrap justify-center items-center gap-8">
      {#each industryKeys as key, i}
        <div class="flex items-center gap-2 text-slate/60">
          <div class="w-8 h-8 rounded-card-sm bg-primary-light flex items-center justify-center">
            <span class="text-xs">{industryIcons[i]}</span>
          </div>
          <span class="text-sm font-inter font-medium text-slate">{$t(`social_proof.${key}`)}</span>
        </div>
      {/each}
    </div>
  </div>
</section>
