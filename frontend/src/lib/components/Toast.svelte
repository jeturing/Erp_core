<script lang="ts">
  import { fly, fade } from 'svelte/transition';
  import { toast, type ToastItem } from '../stores/toast';

  const variantClasses: Record<ToastItem['variant'], string> = {
    success: 'border-success/50 bg-success/15 text-success',
    error: 'border-error/50 bg-error/15 text-error',
    warning: 'border-warning/50 bg-warning/15 text-warning',
    info: 'border-info/50 bg-info/15 text-info',
  };
</script>

<div class="pointer-events-none fixed right-4 top-4 z-[100] w-full max-w-sm space-y-2">
  {#each $toast as item (item.id)}
    <div
      class={`pointer-events-auto rounded-lg border px-4 py-3 shadow-lg backdrop-blur-sm ${variantClasses[item.variant] || variantClasses.info}`}
      in:fly={{ x: 20, duration: 180 }}
      out:fade={{ duration: 140 }}
      role="status"
      aria-live="polite"
    >
      <div class="flex items-start gap-3">
        <p class="flex-1 text-sm font-medium">{item.message}</p>
        <button
          type="button"
          class="text-secondary-300 hover:text-white transition-colors"
          on:click={() => toast.removeToast(item.id)}
          aria-label="Cerrar notificacion"
        >
          ×
        </button>
      </div>
    </div>
  {/each}
</div>
