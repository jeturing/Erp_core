<script lang="ts">
  import { t } from 'svelte-i18n';
  import { ArrowRight, Play } from 'lucide-svelte';
</script>

<section id="cta-final" class="bg-gradient-hero py-24">
  <div class="max-w-3xl mx-auto px-6 text-center">
    <h2 class="text-4xl md:text-5xl font-jakarta font-extrabold text-white mb-6 leading-tight">
      {$t('final_cta.headline')}<br />
      {$t('final_cta.headline_highlight')}
    </h2>
    <p class="text-lg font-inter text-white/80 mb-10 max-w-xl mx-auto">
      {$t('final_cta.subheading')}
    </p>
    <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
      <a
        href="#/signup"
        class="inline-flex items-center gap-2 bg-white text-primary font-jakarta font-semibold text-sm px-8 py-3.5 rounded-btn shadow-medium hover:shadow-elevated hover:bg-cloud transition-all"
      >
        {$t('final_cta.cta_primary')}
        <ArrowRight class="w-4 h-4" />
      </a>
      <a
        href="#/contact"
        class="inline-flex items-center gap-2 border border-white/40 text-white font-jakarta font-semibold text-sm px-8 py-3.5 rounded-btn hover:bg-white/10 transition-all"
      >
        {$t('final_cta.cta_secondary')}
      </a>
    </div>
  </div>
</section>
