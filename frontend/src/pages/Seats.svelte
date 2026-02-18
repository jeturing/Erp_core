<script lang="ts">
  import { onMount } from 'svelte';
  import { seatsApi } from '../lib/api';
  import { toasts } from '../lib/stores';
  import type { SeatHWMRecord, SeatSummaryResponse } from '../lib/types';
  import {
    Users, RefreshCw, ArrowUpDown, TrendingUp,
    Clock, Zap, BarChart3, ChevronLeft, ChevronRight,
  } from 'lucide-svelte';

  let loading = true;
  let hwmRecords: SeatHWMRecord[] = [];
  let summary: SeatSummaryResponse | null = null;
  let syncing = false;
  let subFilter = '';

  async function loadData() {
    loading = true;
    try {
      const subId = subFilter ? parseInt(subFilter) : undefined;
      const [hwmRes, sumRes] = await Promise.all([
        seatsApi.getHWM(subId),
        seatsApi.getSummary(subId),
      ]);
      hwmRecords = hwmRes.items;
      summary = sumRes;
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  async function handleSync() {
    syncing = true;
    try {
      const res = await seatsApi.syncStripe();
      toasts.success(`Sync completado: ${res.synced} actualizados, ${res.errors} errores`);
      await loadData();
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      syncing = false;
    }
  }

  function formatDate(d: string | null): string {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' });
  }

  onMount(loadData);
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><Users size={24} /> Seats</h1>
      <p class="page-subtitle">High Water Mark, eventos de usuarios y sincronización Stripe</p>
    </div>
    <div class="flex gap-2">
      <button class="btn-secondary flex items-center gap-2" on:click={loadData} disabled={loading}>
        <RefreshCw size={14} class={loading ? 'animate-spin' : ''} /> Actualizar
      </button>
      <button class="btn-accent flex items-center gap-2" on:click={handleSync} disabled={syncing}>
        <Zap size={14} class={syncing ? 'animate-pulse' : ''} /> Sync Stripe
      </button>
    </div>
  </div>

  <!-- KPIs -->
  {#if summary}
    <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
      <div class="stat-card">
        <span class="stat-label">Usuarios actuales</span>
        <span class="stat-value">{summary.current_count}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">HWM del período</span>
        <span class="stat-value text-terracotta">{summary.hwm_count}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">En gracia</span>
        <span class="stat-value text-warning">{summary.grace_count}</span>
        <span class="text-[11px] text-gray-500">ventana 8h</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Facturables</span>
        <span class="stat-value text-success">{summary.billable_count}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Período</span>
        <span class="text-lg font-bold text-text-primary">{summary.period}</span>
      </div>
    </div>
  {/if}

  <!-- Filter -->
  <div class="flex gap-3">
    <div class="relative flex-1 max-w-xs">
      <input type="text" bind:value={subFilter} placeholder="Subscription ID (opcional)..." class="input w-full" on:keydown={(e) => e.key === 'Enter' && loadData()} />
    </div>
    <button class="btn-secondary btn-sm" on:click={loadData}>Filtrar</button>
  </div>

  <!-- HWM History -->
  {#if loading}
    <div class="text-center py-16 text-gray-500">
      <div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin mx-auto"></div>
      <p class="mt-3">Cargando datos de seats...</p>
    </div>
  {:else}
    <div class="card p-0 overflow-hidden">
      <div class="px-6 py-4 border-b border-border-light flex items-center justify-between">
        <span class="section-heading flex items-center gap-2"><BarChart3 size={16} /> Historial High Water Mark</span>
        <span class="text-[11px] text-gray-500">{hwmRecords.length} registros</span>
      </div>
      <div class="overflow-x-auto">
        <table class="table w-full">
          <thead>
            <tr>
              <th>ID</th>
              <th>Subscription</th>
              <th>Período</th>
              <th>HWM Count</th>
              <th>Stripe Sync</th>
              <th>Sync Date</th>
            </tr>
          </thead>
          <tbody>
            {#each hwmRecords as r}
              <tr>
                <td class="font-mono text-[11px] text-gray-400">{r.id}</td>
                <td class="font-mono text-sm">{r.subscription_id}</td>
                <td class="text-sm">{r.period_date}</td>
                <td>
                  <span class="inline-flex items-center gap-1.5 font-bold text-text-primary">
                    <TrendingUp size={14} class="text-terracotta" />
                    {r.hwm_count}
                  </span>
                </td>
                <td>
                  {#if r.stripe_qty_updated}
                    <span class="badge-success">Sincronizado</span>
                  {:else}
                    <span class="badge-warning">Pendiente</span>
                  {/if}
                </td>
                <td class="text-sm text-text-secondary">{formatDate(r.stripe_qty_updated_at)}</td>
              </tr>
            {:else}
              <tr>
                <td colspan="6" class="text-center text-gray-500 py-12">No hay registros HWM</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Last Event -->
    {#if summary?.last_event}
      <div class="card">
        <span class="section-heading mb-3 block">Último Evento</span>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <span class="text-[11px] text-gray-500 block">Tipo</span>
            <span class="badge-info mt-1">{summary.last_event.event_type}</span>
          </div>
          <div>
            <span class="text-[11px] text-gray-500 block">Usuario</span>
            <span class="text-sm font-mono">{summary.last_event.odoo_login || '—'}</span>
          </div>
          <div>
            <span class="text-[11px] text-gray-500 block">Count después</span>
            <span class="text-lg font-bold">{summary.last_event.user_count_after}</span>
          </div>
          <div>
            <span class="text-[11px] text-gray-500 block">Facturable</span>
            {#if summary.last_event.is_billable}
              <span class="badge-success">Sí</span>
            {:else}
              <span class="badge-neutral flex items-center gap-1 w-fit"><Clock size={12} /> En gracia</span>
            {/if}
          </div>
        </div>
      </div>
    {/if}
  {/if}
</div>
