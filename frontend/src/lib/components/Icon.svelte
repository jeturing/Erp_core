<script lang="ts">
  // Icon component using Lucide icons
  import type { ComponentType } from 'svelte';
  
  export let icon: ComponentType;
  export let size: number = 20;
  export let strokeWidth: number = 2;
  export let className: string = '';
</script>

<svelte:component 
  this={icon} 
  {size} 
  {strokeWidth}
  class={className}
/>
