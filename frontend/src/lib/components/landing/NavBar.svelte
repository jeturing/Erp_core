<script lang="ts">
  import { t } from 'svelte-i18n';
  import { localeStore } from '../../stores';
  import { ArrowRight, Globe, Menu, X } from 'lucide-svelte';
  import { goto } from '$app/navigation';

  export let partnerBranding: any = null;

  const navLinks = [
    { label: 'Clientes', href: '/signup' },
    { labelKey: 'nav.for_accountants', href: '/accountants' },
    { labelKey: 'nav.partners', href: '/partner-signup' },
    { labelKey: 'nav.pricing', href: '#pricing' },
    { labelKey: 'nav.resources', href: '#faq' },
  ];

  function goToLogin() { goto('/login'); }
  function handleCTA() { goto('/signup'); }
  function toggleLanguage() {
    $localeStore === 'en' ? localeStore.set('es') : localeStore.set('en');
  }

  let scrolled = false;
  let mobileOpen = false;

  function handleScroll() { scrolled = window.scrollY > 24; }

  if (typeof window !== 'undefined') {
    window.addEventListener('scroll', handleScroll, { passive: true });
  }

  $: brandName = partnerBranding?.brand_name || 'SAJET';
</script>

<!--
  NavBar v2 — Jeturing Brand
  Dark-first transparent nav, Electric Green CTA, mobile hamburger
  Inspired by: Linear.app DESIGN.md
-->
<nav
  class="fixed top-0 left-0 right-0 z-50 transition-all duration-300"
  style="background:{scrolled ? 'rgba(2,14,31,0.97)' : 'rgba(2,14,31,0.72)'};
         backdrop-filter:blur(18px);
         -webkit-backdrop-filter:blur(18px);
         border-bottom:1px solid {scrolled ? 'rgba(255,255,255,0.10)' : 'rgba(255,255,255,0.06)'};"
>
  <div class="max-w-6xl mx-auto px-6 py-3.5 flex items-center justify-between">

    <!-- Logo -->
    <a href="/" class="flex items-center gap-2.5 group">
      {#if partnerBranding?.logo_url}
        <img src={partnerBranding.logo_url} alt={brandName} class="h-7" />
      {:else}
        <div class="w-7 h-7 rounded-lg flex items-center justify-center font-jakarta font-bold text-sm text-[#020e1f] transition-transform group-hover:scale-105"
             style="background:#00FF9F; box-shadow:0 0 12px rgba(0,255,159,0.30);">
          {brandName[0]}
        </div>
      {/if}
      <span class="font-jakarta font-bold text-sm tracking-[0.05em] text-[#f0f4ff]">
        {brandName}
      </span>
    </a>

    <!-- Links — desktop -->
    <div class="hidden md:flex items-center gap-7">
      {#each navLinks as link}
        <a href={link.href}
           class="text-[13px] font-inter text-[#7a8fa6] hover:text-[#f0f4ff] transition-colors duration-150">
          {link.label || (link.labelKey ? $t(link.labelKey) : '')}
        </a>
      {/each}
    </div>

    <!-- Right actions — desktop -->
    <div class="hidden md:flex items-center gap-2">
      <!-- Language toggle -->
      <button
        class="h-8 px-2.5 rounded-lg flex items-center gap-1 text-[#7a8fa6] hover:text-[#f0f4ff] transition-colors"
        title={$t('nav.language')}
        on:click={toggleLanguage}
      >
        <Globe class="w-4 h-4" strokeWidth={1.5} />
        <span class="text-[11px] font-inter font-semibold">{$localeStore === 'es' ? 'ES' : 'EN'}</span>
      </button>

      <button class="text-[13px] font-inter text-[#7a8fa6] hover:text-[#f0f4ff] transition-colors px-3 py-1.5"
              on:click={goToLogin}>
        {$t('common.login')}
      </button>

      <!-- Electric Green primary CTA -->
      <button
        class="flex items-center gap-1.5 text-[13px] font-inter font-semibold px-4 py-2 rounded-lg transition-all duration-150 hover:-translate-y-px"
        style="background:#00FF9F; color:#020e1f; box-shadow:0 4px 14px rgba(0,255,159,0.20);"
        on:mouseenter={(e) => { e.currentTarget.style.boxShadow = '0 6px 22px rgba(0,255,159,0.38)'; }}
        on:mouseleave={(e) => { e.currentTarget.style.boxShadow = '0 4px 14px rgba(0,255,159,0.20)'; }}
        on:click={handleCTA}
      >
        {$localeStore === 'es' ? 'Crear empresa' : 'Start free'}
        <ArrowRight class="w-3.5 h-3.5" />
      </button>
    </div>

    <!-- Hamburger — mobile -->
    <button
      class="md:hidden w-9 h-9 flex items-center justify-center rounded-lg text-[#c8d3e8] transition-colors"
      style="background:rgba(255,255,255,0.05);"
      on:click={() => mobileOpen = !mobileOpen}
      aria-label="Toggle menu"
    >
      {#if mobileOpen}<X class="w-5 h-5" />{:else}<Menu class="w-5 h-5" />{/if}
    </button>
  </div>

  <!-- Mobile menu -->
  {#if mobileOpen}
    <div class="md:hidden px-6 pb-5 pt-2 flex flex-col gap-1"
         style="border-top:1px solid rgba(255,255,255,0.06);">
      {#each navLinks as link}
        <a href={link.href}
           class="text-sm font-inter text-[#c8d3e8] py-2.5 hover:text-[#00FF9F] transition-colors"
           on:click={() => mobileOpen = false}>
          {link.label || (link.labelKey ? $t(link.labelKey) : '')}
        </a>
      {/each}
      <div class="flex flex-col gap-2 mt-2 pt-3" style="border-top:1px solid rgba(255,255,255,0.06);">
        <button class="text-sm font-inter text-[#7a8fa6] text-left py-1" on:click={goToLogin}>
          {$t('common.login')}
        </button>
        <button class="text-sm font-inter font-semibold px-4 py-2.5 rounded-lg text-center"
                style="background:#00FF9F; color:#020e1f;"
                on:click={handleCTA}>
          {$localeStore === 'es' ? 'Crear empresa' : 'Start free'}
        </button>
      </div>
    </div>
  {/if}
</nav>
