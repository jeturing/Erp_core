<script lang="ts">
  import { t } from 'svelte-i18n';
  import { localeStore } from '../../stores';
  import { ArrowRight, Globe } from 'lucide-svelte';
  import { goto } from '$app/navigation';

  export let partnerBranding: any = null;

  const navLinks = [
    { label: 'Clientes', href: '/signup' },
    { labelKey: 'nav.for_accountants', href: '/accountants' },
    { labelKey: 'nav.partners', href: '/partner-signup' },
    { labelKey: 'nav.pricing', href: '#pricing' },
    { labelKey: 'nav.resources', href: '#faq' },
  ];

  function goToLogin() {
    goto('/login');
  }

  function handleCTA() {
    goto('/signup');
  }

  function toggleLanguage() {
    $localeStore === 'en' ? localeStore.set('es') : localeStore.set('en');
  }

  let scrolled = false;

  function handleScroll() {
    scrolled = window.scrollY > 10;
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('scroll', handleScroll);
  }

  $: logoColor = partnerBranding?.primary_color || '#1B4FD8';
  $: brandName = partnerBranding?.brand_name || 'SAJET';
</script>

<nav
  class="fixed top-0 left-0 right-0 z-50 transition-all duration-300"
  class:bg-white={scrolled}
  class:shadow-soft={scrolled}
  class:bg-transparent={!scrolled}
  style="border-bottom: {scrolled ? '1px solid #E2E8F0' : 'none'}"
>
  <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
    <!-- Logo -->
    <div class="flex items-center gap-3">
      {#if partnerBranding?.logo_url}
        <img src={partnerBranding.logo_url} alt={brandName} class="h-8" />
      {:else}
        <div class="w-8 h-8 rounded-btn flex items-center justify-center" style="background: {logoColor}">
          <span class="text-white font-jakarta font-bold text-sm">{brandName[0]}</span>
        </div>
      {/if}
      <span class="font-jakarta font-bold tracking-[0.08em] text-sm"
        style="color: {scrolled ? '#0F172A' : '#0F172A'}"
      >{brandName}</span>
    </div>

    <!-- Nav links -->
    <div class="hidden md:flex items-center gap-8">
      {#each navLinks as link}
        <a
          href={link.href}
          class="text-sm font-inter transition-colors"
          style="color: {scrolled ? '#64748B' : '#64748B'}"
        >{link.label || (link.labelKey ? $t(link.labelKey) : '')}</a>
      {/each}
    </div>

    <!-- CTA buttons + Language selector -->
    <div class="flex items-center gap-3">
      <!-- Language Selector -->
      <button
        class="w-10 h-10 rounded-lg flex items-center justify-center transition-colors"
        class:bg-primary-light={scrolled}
        class:hover:bg-cloud={!scrolled}
        title={$t('nav.language')}
        on:click={toggleLanguage}
      >
        <Globe class="w-5 h-5 text-slate" strokeWidth={1.5} />
        <span class="text-xs font-jakarta font-bold text-primary ml-1">{$localeStore === 'es' ? 'ES' : 'EN'}</span>
      </button>

      <a
        href="/accountants"
        class="text-sm font-inter text-slate hover:text-slate-dark transition-colors px-3 py-1.5"
      >
        {$t('common.join_accountant')}
      </a>
      <button
        class="text-sm font-inter text-slate hover:text-slate-dark transition-colors px-3 py-1.5"
        on:click={goToLogin}
      >
        {$t('common.login')}
      </button>
      <button
        class="text-sm font-inter font-semibold text-white px-5 py-2.5 rounded-btn transition-all hover:-translate-y-px hover:shadow-medium"
        style="background: {logoColor}"
        on:click={handleCTA}
      >
        {$localeStore === 'es' ? 'Crear empresa' : 'Create company'}
      </button>
    </div>
  </div>
</nav>
