<script lang="ts">
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import Button from './Button.svelte';

  export let isOpen: boolean = false;
  export let title: string = '';
  export let size: 'sm' | 'md' | 'lg' | 'xl' = 'md';
  export let showFooter: boolean = true;
  export let confirmText: string = 'Guardar';
  export let cancelText: string = 'Cancelar';
  export let confirmVariant: 'primary' | 'danger' | 'secondary' = 'primary';
  export let loading: boolean = false;

  const dispatch = createEventDispatcher<{ close: undefined; confirm: undefined }>();

  const sizes = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
  };

  const modalTitleId = `modal-title-${Math.random().toString(36).slice(2, 9)}`;

  function close() {
    if (!loading) {
      isOpen = false;
      dispatch('close');
    }
  }

  function confirm() {
    dispatch('confirm');
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape' && isOpen) {
      close();
    }
  }

  onMount(() => {
    document.addEventListener('keydown', handleKeydown);
  });

  onDestroy(() => {
    document.removeEventListener('keydown', handleKeydown);
    document.body.style.overflow = '';
  });

  $: {
    document.body.style.overflow = isOpen ? 'hidden' : '';
  }
</script>

{#if isOpen}
  <div
    class="fixed inset-0 z-50 overflow-y-auto"
    role="dialog"
    aria-modal="true"
    aria-labelledby={modalTitleId}
    transition:fade={{ duration: 150 }}
  >
    <button
      type="button"
      class="fixed inset-0 bg-black/50"
      aria-label="Cerrar modal"
      on:click={close}
    ></button>

    <div class="relative flex min-h-full items-center justify-center p-4">
      <div
        class="w-full {sizes[size]} bg-surface-card rounded-xl shadow-2xl border border-surface-border"
        transition:fly={{ y: 20, duration: 200 }}
      >
        <div class="flex items-center justify-between px-6 py-4 border-b border-surface-border">
          <h3 id={modalTitleId} class="text-lg font-semibold text-white">{title}</h3>
          <button
            type="button"
            class="text-secondary-400 hover:text-secondary-200 transition-colors"
            on:click={close}
            disabled={loading}
            aria-label="Cerrar"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="px-6 py-4">
          <slot></slot>
        </div>

        {#if showFooter}
          <div class="flex justify-end gap-3 px-6 py-4 border-t border-surface-border bg-surface-dark rounded-b-xl">
            <Button variant="ghost" on:click={close} disabled={loading}>
              {cancelText}
            </Button>
            <Button variant={confirmVariant} on:click={confirm} {loading}>
              {confirmText}
            </Button>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}
