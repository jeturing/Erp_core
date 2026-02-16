<script lang="ts">
  import { fly } from 'svelte/transition';
  import { toasts } from '../stores/toast';
  import { CheckCircle2, XCircle, AlertTriangle, Info, X } from 'lucide-svelte';

  const icons = {
    success: CheckCircle2,
    error: XCircle,
    warning: AlertTriangle,
    info: Info,
  };

  const colors = {
    success: 'bg-green-900/80 border-green-500/40 text-green-200',
    error: 'bg-red-900/80 border-red-500/40 text-red-200',
    warning: 'bg-yellow-900/80 border-yellow-500/40 text-yellow-200',
    info: 'bg-blue-900/80 border-blue-500/40 text-blue-200',
  };

  const iconColors = {
    success: 'text-green-400',
    error: 'text-red-400',
    warning: 'text-yellow-400',
    info: 'text-blue-400',
  };
</script>

<div class="fixed top-4 right-4 z-[100] flex flex-col gap-2 max-w-sm w-full pointer-events-none">
  {#each $toasts as toast (toast.id)}
    <div
      class="pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-lg border backdrop-blur-sm shadow-lg {colors[toast.variant]}"
      transition:fly={{ x: 300, duration: 300 }}
      role="alert"
    >
      <svelte:component this={icons[toast.variant]} size={20} class="flex-shrink-0 mt-0.5 {iconColors[toast.variant]}" />
      <p class="flex-1 text-sm">{toast.message}</p>
      <button
        type="button"
        class="flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity"
        on:click={() => toasts.remove(toast.id)}
        aria-label="Cerrar"
      >
        <X size={16} />
      </button>
    </div>
  {/each}
</div>
