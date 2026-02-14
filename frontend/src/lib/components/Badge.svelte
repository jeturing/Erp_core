<script lang="ts">
  export let variant:
    | 'success'
    | 'warning'
    | 'error'
    | 'info'
    | 'primary'
    | 'accent'
    | 'secondary'
    | 'basic'
    | 'pro'
    | 'enterprise' = 'primary';
  export let size: 'sm' | 'md' = 'md';
  export let dot: boolean = false;

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
  };
</script>

<span class="badge-{variant} {sizeClasses[size]}">
  {#if dot}
    <span class="w-1.5 h-1.5 rounded-full bg-current"></span>
  {/if}
  <slot />
</span>
