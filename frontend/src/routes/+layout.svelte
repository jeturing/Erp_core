<script lang="ts">
  import '../app.css'
  import Toast from '$lib/components/Toast.svelte'
  import OfflineBanner from '$lib/components/OfflineBanner.svelte'
  import { authReady } from '$lib/stores'
  import { Spinner } from '$lib/components'

  let { children } = $props()

  // auth.init() is called in +layout.ts load(), authReady resolves when done.
  // We use this to show a spinner until auth is bootstrapped.
  let authBootstrapped = $state(false)

  $effect(() => {
    authReady.then(() => {
      authBootstrapped = true
    })
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
