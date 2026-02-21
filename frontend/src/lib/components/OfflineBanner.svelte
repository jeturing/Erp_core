<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { WifiOff, Wifi, X } from 'lucide-svelte';

  let isOnline = true;
  let showReconnected = false;
  let reconnectedTimer: ReturnType<typeof setTimeout>;

  function update() {
    const wasOffline = !isOnline;
    isOnline = navigator.onLine;
    if (wasOffline && isOnline) {
      showReconnected = true;
      reconnectedTimer = setTimeout(() => {
        showReconnected = false;
      }, 3000);
    }
  }

  onMount(() => {
    isOnline = navigator.onLine;
    window.addEventListener('online', update);
    window.addEventListener('offline', update);
  });

  onDestroy(() => {
    window.removeEventListener('online', update);
    window.removeEventListener('offline', update);
    clearTimeout(reconnectedTimer);
  });
</script>

{#if !isOnline}
  <!-- ── OFFLINE BANNER ── -->
  <div
    class="fixed top-0 left-0 right-0 z-[9999] flex items-center justify-center gap-2
           bg-amber-600 text-white px-4 py-2 text-sm font-medium shadow-lg"
    role="alert"
    aria-live="polite"
  >
    <WifiOff class="w-4 h-4 shrink-0" />
    <span>Sin conexión — mostrando datos en caché (solo lectura)</span>
  </div>

  <!-- Spacer to push content down so nothing is hidden under the banner -->
  <div class="h-9" aria-hidden="true"></div>

{:else if showReconnected}
  <!-- ── RECONNECTED TOAST ── -->
  <div
    class="fixed top-4 right-4 z-[9999] flex items-center gap-2
           bg-emerald-700 text-white px-4 py-2.5 rounded-lg shadow-lg text-sm font-medium
           animate-[fadeIn_0.2s_ease-out]"
    role="status"
  >
    <Wifi class="w-4 h-4 shrink-0 text-emerald-300" />
    Conexión restaurada
  </div>
{/if}
