<!--
  GlassCard.svelte — Componente base del Design System SAJET
  Uso: <GlassCard glow accent="primary">...</GlassCard>
-->
<script lang="ts">
  import type { Snippet } from 'svelte'
  // lang="ts" required for TypeScript in Svelte components

  interface Props {
    glow?: boolean
    accent?: 'primary' | 'accent' | 'none'
    padding?: 'sm' | 'md' | 'lg'
    hover?: boolean
    class?: string
    children?: Snippet
  }

  let {
    glow = false,
    accent = 'none',
    padding = 'md',
    hover = true,
    class: cls = '',
    children
  }: Props = $props()

  const paddings = { sm: 'p-4', md: 'p-6', lg: 'p-8' }

  const glowColors = {
    primary: 'shadow-[0_0_40px_rgba(0,59,115,0.25)]',
    accent: 'shadow-[0_0_40px_rgba(0,255,159,0.12)]',
    none: ''
  }

  const borderAccents = {
    primary: 'border-[#003B73]/40',
    accent: 'border-[#00FF9F]/20',
    none: 'border-white/10'
  }
</script>

<div
  class="
    relative rounded-2xl border bg-white/5 backdrop-blur-xl overflow-hidden
    transition-all duration-300
    {paddings[padding]}
    {borderAccents[accent]}
    {glow ? glowColors[accent] : ''}
    {hover ? 'hover:bg-white/8 hover:border-[#00FF9F]/25' : ''}
    {cls}
  "
>
  {#if glow && accent !== 'none'}
    <div
      class="
        absolute -top-8 -right-8 w-40 h-40 rounded-full blur-3xl pointer-events-none
        {accent === 'accent' ? 'bg-[#00FF9F]/6' : 'bg-[#003B73]/20'}
      "
    ></div>
  {/if}
  {@render children?.()}
</div>
