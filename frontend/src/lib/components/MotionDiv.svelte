<script lang="ts">
  import { onMount } from 'svelte';
  import { animate } from 'motion';
  import type { Snippet } from 'svelte';

  const { children, delay = 0, variant = 'fadeUp' }: {
    children: Snippet;
    delay?: number;
    variant?: 'fadeUp' | 'fadeIn' | 'slideRight' | 'scaleIn';
  } = $props();

  let el: HTMLElement;

  const variants = {
    fadeUp: { opacity: [0, 1], y: [24, 0] },
    fadeIn: { opacity: [0, 1] },
    slideRight: { opacity: [0, 1], x: [-20, 0] },
    scaleIn: { opacity: [0, 1], scale: [0.97, 1] },
  };

  onMount(() => {
    if (el) {
      animate(el, variants[variant], {
        duration: 0.4,
        delay,
        easing: [0.25, 0.46, 0.45, 0.94],
      });
    }
  });
</script>

<div bind:this={el} style="opacity:0;">
  {@render children()}
</div>
