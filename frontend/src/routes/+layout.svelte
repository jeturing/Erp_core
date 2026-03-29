<script lang="ts">
  import '../app.css'
  import Toast from '$lib/components/Toast.svelte'
  import OfflineBanner from '$lib/components/OfflineBanner.svelte'
  import { auth } from '$lib/stores'
  import { onMount } from 'svelte'
  import { getInitialLocale } from '$lib/i18n'
  import { localeStore } from '$lib/stores/locale'
  import { Spinner } from '$lib/components'

  let { children } = $props()

  let authBootstrapped = $state(false)

  onMount(async () => {
    const initialLocale = getInitialLocale()
    localeStore.set(initialLocale as any)
    await auth.init()
    authBootstrapped = true
  })
</script>

<Toast />
<OfflineBanner />

{#if !authBootstrapped}
  <div class="min-h-screen bg-bg-page flex items-center justify-center">
    <div class="text-center">
      <Spinner size="lg" />
      <p class="mt-4 text-gray-500">Cargando...</p>
    </div>
  </div>
{:else}
  {@render children()}
{/if}
