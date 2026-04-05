<script lang="ts">
  import { t } from 'svelte-i18n';
  import { ArrowRight } from 'lucide-svelte';
</script>

<!--
  FinalCTA v2 — Jeturing Brand
  Dark premium section with Electric Green as hero accent
  Inspired by: Linear.app, Stripe (awesome-design-md)
-->
<section
  id="cta-final"
  class="py-28 relative overflow-hidden"
  style="background:#020e1f; border-top:1px solid rgba(255,255,255,0.05);"
>
  <!-- Electric Green ambient top -->
  <div class="absolute top-0 left-1/2 -translate-x-1/2 pointer-events-none"
       style="width:700px; height:300px;
              background:radial-gradient(ellipse at 50% 0%, rgba(0,255,159,0.12) 0%, transparent 65%);
              filter:blur(50px);"></div>
  <!-- Deep blue bottom glow -->
  <div class="absolute bottom-0 left-1/2 -translate-x-1/2 pointer-events-none"
       style="width:500px; height:200px;
              background:radial-gradient(ellipse, rgba(0,59,115,0.35) 0%, transparent 70%);
              filter:blur(60px);"></div>

  <div class="relative max-w-2xl mx-auto px-6 text-center">

    <!-- Green label pill -->
    <div class="inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 mb-8 text-[11px] font-inter font-semibold tracking-[0.10em] uppercase"
         style="background:rgba(0,255,159,0.09); border:1px solid rgba(0,255,159,0.28); color:#00FF9F;">
      <span class="w-1.5 h-1.5 rounded-full" style="background:#00FF9F; box-shadow:0 0 6px #00FF9F;"></span>
      Empieza hoy
    </div>

    <!-- Headline -->
    <h2
      class="font-jakarta font-extrabold text-[#f0f4ff] mb-5 leading-[1.08]"
      style="font-size:clamp(2rem, 5vw, 3.2rem); letter-spacing:-1.4px;"
    >
      {$t('final_cta.headline')}<br />
      <span style="color:#00FF9F; text-shadow:0 0 32px rgba(0,255,159,0.30);">
        {$t('final_cta.headline_highlight')}
      </span>
    </h2>

    <!-- Subheading -->
    <p class="font-inter text-[#7a8fa6] mb-10 max-w-lg mx-auto leading-relaxed text-[16px]">
      {$t('final_cta.subheading')}
    </p>

    <!-- CTAs -->
    <div class="flex flex-col sm:flex-row items-center justify-center gap-3">
      <a
        href="/signup"
        class="inline-flex items-center gap-2 font-inter font-semibold text-[14px] px-8 py-3.5 rounded-lg transition-all duration-150 hover:-translate-y-px w-full sm:w-auto justify-center"
        style="background:#00FF9F; color:#020e1f; box-shadow:0 4px 20px rgba(0,255,159,0.30);"
        on:mouseenter={(e)=>e.currentTarget.style.boxShadow='0 8px 30px rgba(0,255,159,0.45)'}
        on:mouseleave={(e)=>e.currentTarget.style.boxShadow='0 4px 20px rgba(0,255,159,0.30)'}
      >
        {$t('final_cta.cta_primary')}
        <ArrowRight class="w-4 h-4" />
      </a>
      <a
        href="mailto:ventas@sajet.us?subject=Quiero%20hablar%20con%20SAJET"
        class="inline-flex items-center gap-2 font-inter font-medium text-[14px] text-[#c8d3e8] px-8 py-3.5 rounded-lg transition-all hover:-translate-y-px w-full sm:w-auto justify-center"
        style="border:1px solid rgba(255,255,255,0.12); background:rgba(255,255,255,0.04);"
      >
        {$t('final_cta.cta_secondary')}
      </a>
    </div>

    <!-- Trust micro-copy -->
    <p class="text-[11px] font-inter text-[#4a6080] mt-8">
      Sin tarjeta de crédito · 14 días gratis · Cancela cuando quieras
    </p>
  </div>
</section>
