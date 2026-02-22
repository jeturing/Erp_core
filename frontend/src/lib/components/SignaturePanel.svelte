<script lang="ts">
  /**
   * SignaturePanel – Stripe-style typed signature.
   * User types their name → rendered in cursive as the "signature".
   * Emits `sign` event with { signer_name, signature_data }.
   */
  import { createEventDispatcher } from 'svelte';
  import { CheckCircle, Loader2 } from 'lucide-svelte';

  export let documentTitle: string = 'Acuerdo';
  export let htmlPreview: string = '';
  export let loading: boolean = false;
  export let signed: boolean = false;

  const dispatch = createEventDispatcher<{
    sign: { signer_name: string; signature_data: string };
  }>();

  let signerName = '';
  let agreed = false;
  let showPreview = false;

  $: canSign = signerName.trim().length >= 2 && agreed && !loading && !signed;

  function handleSign() {
    if (!canSign) return;
    // signature_data = cursive-rendered name as simple text marker (backend stores it)
    dispatch('sign', {
      signer_name: signerName.trim(),
      signature_data: `typed:${signerName.trim()}`,
    });
  }
</script>

<div class="space-y-4">
  <!-- Document title -->
  <div class="flex items-center justify-between">
    <h3 class="text-base font-semibold text-[#1a1a1a]">{documentTitle}</h3>
    {#if signed}
      <span class="inline-flex items-center gap-1 text-xs font-medium text-[#4A7C59]">
        <CheckCircle class="w-3.5 h-3.5" />
        Firmado
      </span>
    {/if}
  </div>

  <!-- Preview toggle -->
  {#if htmlPreview}
    <button
      class="text-xs text-[#C05A3C] hover:underline"
      on:click={() => showPreview = !showPreview}
    >
      {showPreview ? 'Ocultar documento' : 'Ver documento completo'}
    </button>

    {#if showPreview}
      <div class="border border-gray-200 rounded-lg p-4 bg-white max-h-64 overflow-y-auto prose prose-sm">
        {@html htmlPreview}
      </div>
    {/if}
  {/if}

  {#if !signed}
    <!-- Signature input -->
    <div>
      <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1.5">
        Escribe tu nombre completo para firmar
      </label>
      <input
        type="text"
        bind:value={signerName}
        class="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none"
        placeholder="Nombre y Apellido"
        disabled={loading}
      />
    </div>

    <!-- Signature preview (cursive) -->
    {#if signerName.trim().length >= 2}
      <div class="rounded-lg border-2 border-dashed border-gray-200 bg-gray-50 p-6 text-center">
        <p class="text-xs text-gray-400 uppercase tracking-wider mb-2">Vista previa de firma</p>
        <p
          class="text-3xl text-[#1a1a1a]"
          style="font-family: 'Dancing Script', 'Brush Script MT', 'Segoe Script', cursive; font-weight: 500;"
        >
          {signerName.trim()}
        </p>
      </div>
    {/if}

    <!-- Agreement checkbox -->
    <label class="flex items-start gap-2.5 text-sm text-gray-600 cursor-pointer">
      <input
        type="checkbox"
        bind:checked={agreed}
        class="rounded border-gray-300 text-[#C05A3C] focus:ring-[#C05A3C] mt-0.5"
        disabled={loading}
      />
      <span>
        He leído y acepto los términos de este <strong>{documentTitle}</strong>.
        Comprendo que esta firma digital tiene validez legal.
      </span>
    </label>

    <!-- Sign button -->
    <button
      class="w-full bg-[#C05A3C] text-white font-semibold py-2.5 rounded-lg hover:bg-[#a94e33] transition-colors flex items-center justify-center gap-2 text-sm disabled:opacity-60 disabled:cursor-not-allowed"
      on:click={handleSign}
      disabled={!canSign}
    >
      {#if loading}
        <Loader2 class="w-4 h-4 animate-spin" />
        Firmando...
      {:else}
        Firmar digitalmente
      {/if}
    </button>
  {:else}
    <!-- Already signed -->
    <div class="rounded-lg border border-[#4A7C59]/20 bg-[#4A7C59]/5 p-4 text-center">
      <p class="text-xs text-gray-400 uppercase tracking-wider mb-1">Firmado como</p>
      <p
        class="text-2xl text-[#1a1a1a]"
        style="font-family: 'Dancing Script', 'Brush Script MT', 'Segoe Script', cursive;"
      >
        {signerName || 'Firma registrada'}
      </p>
    </div>
  {/if}
</div>
