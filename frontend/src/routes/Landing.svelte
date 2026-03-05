<script lang="ts">
  import { onMount } from 'svelte';
  import { t, locale } from 'svelte-i18n';
  import NavBar from '../lib/components/landing/NavBar.svelte';
  import Hero from '../lib/components/landing/Hero.svelte';
  import SocialProof from '../lib/components/landing/SocialProof.svelte';
  import ValueProp from '../lib/components/landing/ValueProp.svelte';
  import FeaturesGrid from '../lib/components/landing/FeaturesGrid.svelte';
  import HowItWorks from '../lib/components/landing/HowItWorks.svelte';
  import ForPartners from '../lib/components/landing/ForPartners.svelte';
  import AccountantsSummary from '../lib/components/landing/AccountantsSummary.svelte';
  import Testimonials from '../lib/components/landing/Testimonials.svelte';
  import FAQ from '../lib/components/landing/FAQ.svelte';
  import PricingPreview from '../lib/components/landing/PricingPreview.svelte';
  import FinalCTA from '../lib/components/landing/FinalCTA.svelte';
  import Footer from '../lib/components/landing/Footer.svelte';

  /** Optional: partner branding for white-label URLs (/plt/{code}) */
  export let partnerBranding: any = null;
  export let partnerCode: string = '';

  // ── Live data from API (with fallbacks baked into each child) ──
  let stats: any = {};
  let plans: any[] = [];
  let features: any[] = [];
  let testimonials: any[] = [];

  let loaded = false;

  onMount(async () => {
    try {
      const [statsRes, plansRes, testimonialsRes] = await Promise.all([
        fetch('/api/public/stats'),
        fetch('/api/public/plans'),
        fetch('/api/public/testimonials'),
      ]);

      if (statsRes.ok) {
        const sd = await statsRes.json();
        stats = sd.stats || sd;
      }
      if (plansRes.ok) {
        const pd = await plansRes.json();
        plans = pd.plans || pd;
      }
      if (testimonialsRes.ok) {
        const td = await testimonialsRes.json();
        testimonials = td.testimonials || td;
      }
    } catch (e) {
      console.warn('[Landing] API unavailable, using fallback data', e);
    } finally {
      loaded = true;
    }
  });
</script>

<svelte:head>
  <title>{$t('seo.title')}</title>
  <meta name="description" content={$t('seo.description')} />
  <meta name="keywords" content={$t('seo.keywords')} />

  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://sajet.us" />
  <meta property="og:title" content={$t('seo.og_title')} />
  <meta property="og:description" content={$t('seo.og_description')} />
  <meta property="og:image" content="https://sajet.us/static/images/og-sajet-erp.png" />
  <meta property="og:image:alt" content={$t('seo.og_image_alt')} />
  <meta property="og:locale" content={$locale === 'es' ? 'es_LA' : 'en_US'} />
  <meta property="og:site_name" content="SAJET ERP" />

  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content={$t('seo.og_title')} />
  <meta name="twitter:description" content={$t('seo.og_description')} />
  <meta name="twitter:image" content="https://sajet.us/static/images/og-sajet-erp.png" />

  <!-- hreflang alternates -->
  <link rel="alternate" hreflang="en" href="https://sajet.us/" />
  <link rel="alternate" hreflang="es" href="https://sajet.us/?lang=es" />
  <link rel="alternate" hreflang="x-default" href="https://sajet.us/" />
  <link rel="canonical" href="https://sajet.us/" />

  <!-- Schema.org JSON-LD -->
  {@html `<script type="application/ld+json">${JSON.stringify({
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "SAJET ERP",
    "applicationCategory": "BusinessApplication",
    "operatingSystem": "Web",
    "url": "https://sajet.us",
    "description": $t('seo.description'),
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD",
      "description": "14-day free trial"
    },
    "publisher": {
      "@type": "Organization",
      "name": "Jeturing SRL",
      "url": "https://sajet.us"
    }
  })}</script>`}
</svelte:head>

<div class="min-h-screen bg-white font-inter">
  <NavBar {partnerBranding} />
  <Hero {stats} {partnerBranding} />
  <SocialProof />
  <ValueProp />
  <FeaturesGrid {features} />
  <HowItWorks />
  <PricingPreview {plans} {partnerCode} />
  <ForPartners />
  <AccountantsSummary />
  <Testimonials {testimonials} />
  <FAQ />
  <FinalCTA />
  <Footer />
</div>
