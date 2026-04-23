<script lang="ts">
  import { onMount } from 'svelte';
  import { animate, inView } from 'motion';
  import type { Snippet } from 'svelte';

  const { children, selector = '.stagger-item', staggerDelay = 0.06 }: {
    children: Snippet;
    selector?: string;
    staggerDelay?: number;
  } = $props();

  let container: HTMLElement;

  onMount(() => {
    if (!container) return;
    const items = container.querySelectorAll(selector);
    items.forEach((el, i) => {
      animate(el as HTMLElement, { opacity: [0, 1], y: [20, 0] }, {
        duration: 0.35,
        delay: i * staggerDelay,
        easing: [0.25, 0.46, 0.45, 0.94],
      });
    });
  });
</script>

<div bind:this={container}>
  {@render children()}
</div>
