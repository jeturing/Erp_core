<script lang="ts">
  export let title: string = '';
  export let subtitle: string = '';
  export let hover: boolean = false;
  export let padding: 'none' | 'sm' | 'md' | 'lg' = 'md';
  
  const paddingClasses = {
    none: 'p-0',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };
</script>

<div class="{hover ? 'card-hover' : 'card'} {paddingClasses[padding]}">
  {#if title || $$slots.header}
    <div class="flex items-center justify-between mb-4">
      <div>
        {#if title}
          <h3 class="text-lg font-semibold text-white">{title}</h3>
        {/if}
        {#if subtitle}
          <p class="text-sm text-secondary-400 mt-0.5">{subtitle}</p>
        {/if}
      </div>
      {#if $$slots.header}
        <slot name="header" />
      {/if}
    </div>
  {/if}
  
  <slot />
  
  {#if $$slots.footer}
    <div class="mt-4 pt-4 border-t border-surface-border">
      <slot name="footer" />
    </div>
  {/if}
</div>
