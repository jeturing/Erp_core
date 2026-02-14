<script lang="ts">
  import type { HTMLInputAttributes } from 'svelte/elements';

  export let label: string = '';
  export let type: 'text' | 'email' | 'password' | 'number' | 'search' = 'text';
  export let placeholder: string = '';
  export let value: string | number = '';
  export let error: string = '';
  export let disabled: boolean = false;
  export let required: boolean = false;
  export let id: string = '';
  export let name: string = '';
  export let autocomplete: HTMLInputAttributes['autocomplete'] = undefined;
  export let hint: string | undefined = undefined;

  $: inputId = id || name || label.toLowerCase().replace(/\s+/g, '-');
</script>

<div class="space-y-1.5">
  {#if label}
    <label for={inputId} class="label">
      {label}
      {#if required}
        <span class="text-error" aria-hidden="true">*</span>
      {/if}
    </label>
  {/if}

  <input
    id={inputId}
    {name}
    {type}
    {placeholder}
    bind:value
    {disabled}
    {required}
    {autocomplete}
    aria-invalid={error ? 'true' : 'false'}
    class={error ? 'input-error' : 'input'}
    on:input
    on:change
    on:blur
    on:focus
  />

  {#if error}
    <p class="text-sm text-error">{error}</p>
  {:else if hint}
    <p class="text-xs text-secondary-500">{hint}</p>
  {/if}
</div>
