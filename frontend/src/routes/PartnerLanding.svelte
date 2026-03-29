<script lang="ts">
  import { onMount } from 'svelte';
  import Landing from './Landing.svelte';
  import { Spinner } from '../lib/components';

  /** Partner code extracted from the URL hash: #/plt/{code} */
  export let code: string = '';

  let partnerBranding: any = null;
  let loading = true;
  let error = false;

  onMount(async () => {
    if (!code) {
      error = true;
      loading = false;
      return;
    }
    try {
      const res = await fetch(`/api/public/partner/${code}`);
      if (res.ok) {
        partnerBranding = await res.json();
      } else {
        error = true;
      }
    } catch (e) {
      console.error('[PartnerLanding] Failed to load partner branding', e);
      error = true;
    } finally {
      loading = false;
    }
  });
</script>

{#if loading}
  <div class="min-h-screen bg-white flex items-center justify-center">
    <div class="text-center">
      <Spinner size="lg" />
      <p class="mt-4 text-sm font-inter text-slate">Loading partner experience...</p>
    </div>
  </div>
{:else if error}
  <div class="min-h-screen bg-white flex items-center justify-center">
    <div class="text-center max-w-md px-6">
      <h1 class="text-2xl font-jakarta font-bold text-slate-dark mb-3">Partner Not Found</h1>
      <p class="text-sm font-inter text-slate mb-6">
        The partner link you followed doesn't match any active partner. You can continue to the main site.
      </p>
      <a href="/" class="inline-flex items-center gap-2 bg-primary hover:bg-navy text-white font-jakarta font-semibold text-sm px-6 py-3 rounded-btn shadow-soft transition-all">
        Go to Sajet.us
      </a>
    </div>
  </div>
{:else}
  <Landing {partnerBranding} partnerCode={code} />
{/if}
