<script lang="ts">
  import { TrendingUp, TrendingDown, Minus } from 'lucide-svelte';
  
  export let value: string | number;
  export let label: string;
  export let change: number | null = null;
  export let changeLabel: string = 'vs last month';
  export let icon: any = null;
  export let iconBg: string = 'bg-primary-500/10';
  export let iconColor: string = 'text-primary-400';
</script>

<div class="stat-card">
  <div class="flex items-start justify-between">
    <div class="flex-1">
      <p class="stat-label">{label}</p>
      <p class="stat-value mt-1">{value}</p>
      
      {#if change !== null}
        <div class="flex items-center gap-1 mt-2">
          {#if change > 0}
            <TrendingUp size={14} class="text-success" />
            <span class="stat-change-positive">+{change.toFixed(1)}%</span>
          {:else if change < 0}
            <TrendingDown size={14} class="text-error" />
            <span class="stat-change-negative">{change.toFixed(1)}%</span>
          {:else}
            <Minus size={14} class="text-secondary-400" />
            <span class="stat-change text-secondary-400">0%</span>
          {/if}
          <span class="text-xs text-secondary-500">{changeLabel}</span>
        </div>
      {/if}
    </div>
    
    {#if icon}
      <div class="p-3 rounded-lg {iconBg}">
        <svelte:component this={icon} size={24} class={iconColor} />
      </div>
    {/if}
  </div>
</div>
