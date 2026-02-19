<script lang="ts">
  import { onMount } from 'svelte';
  import { reconciliationApi } from '../lib/api';
  import { toasts } from '../lib/stores';
  import type { ReconciliationRun } from '../lib/types';
  import { formatCurrency, formatDate } from '../lib/utils/formatters';
  import {
    GitCompare, Play, RefreshCw, ChevronDown, ChevronUp,
    CheckCircle, AlertTriangle, XCircle,
  } from 'lucide-svelte';

  let runs: ReconciliationRun[] = [];
  let loading = true;
  let running = false;
  let expandedId: number | null = null;
  let expandedDetail: ReconciliationRun | null = null;

  // Run form
  let showRunForm = false;
  let runForm = { period_start: '', period_end: '' };

  async function loadRuns() {
    loading = true;
    try {
      const res = await reconciliationApi.list({ limit: 50 });
      runs = res?.items ?? [];
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  async function handleRun() {
    running = true;
    try {
      const res = await reconciliationApi.run({
        period_start: runForm.period_start || undefined,
        period_end: runForm.period_end || undefined,
      });
      toasts.success(`Reconciliación ejecutada — Discrepancia: ${formatCurrency(res.run.discrepancy)}`);
      showRunForm = false;
      runForm = { period_start: '', period_end: '' };
      await loadRuns();
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      running = false;
    }
  }

  async function toggleDetail(id: number) {
    if (expandedId === id) {
      expandedId = null;
      expandedDetail = null;
      return;
    }
    try {
      expandedDetail = await reconciliationApi.get(id);
      expandedId = id;
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  function discrepancyColor(d: number): string {
    if (Math.abs(d) < 0.01) return 'text-success';
    if (Math.abs(d) < 10) return 'text-warning';
    return 'text-error';
  }

  function statusIcon(status: string) {
    if (status === 'matched' || status === 'clean') return { icon: CheckCircle, color: 'text-success' };
    if (status === 'warning') return { icon: AlertTriangle, color: 'text-warning' };
    return { icon: XCircle, color: 'text-error' };
  }

  $: totalDiscrepancy = (runs || []).reduce((s, r) => s + Math.abs(r.discrepancy), 0);
  $: cleanRuns = (runs || []).filter(r => Math.abs(r.discrepancy) < 0.01).length;
  $: issueRuns = (runs || []).length - cleanRuns;

  onMount(loadRuns);
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><GitCompare size={24} /> Reconciliación</h1>
      <p class="page-subtitle">Stripe vs Base de Datos local — auditoría de ingresos</p>
    </div>
    <div class="flex gap-2">
      <button class="btn-secondary flex items-center gap-2" on:click={loadRuns} disabled={loading}>
        <RefreshCw size={14} class={loading ? 'animate-spin' : ''} /> Actualizar
      </button>
      <button class="btn-accent flex items-center gap-2" on:click={() => showRunForm = true}>
        <Play size={16} /> Ejecutar Reconciliación
      </button>
    </div>
  </div>

  <!-- KPIs -->
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
    <div class="stat-card">
      <span class="stat-label">Total Ejecuciones</span>
      <span class="stat-value">{runs.length}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Sin diferencias</span>
      <span class="stat-value text-success">{cleanRuns}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Con Issues</span>
      <span class="stat-value text-error">{issueRuns}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Discrepancia Total</span>
      <span class="stat-value {totalDiscrepancy > 0 ? 'text-warning' : 'text-success'}">{formatCurrency(totalDiscrepancy)}</span>
    </div>
  </div>

  <!-- Run Form -->
  {#if showRunForm}
    <div class="card p-6 border border-border-dark">
      <h2 class="section-heading mb-4">Ejecutar Reconciliación</h2>
      <form on:submit|preventDefault={handleRun} class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="label">Período inicio (opcional)</label>
          <input type="date" bind:value={runForm.period_start} class="input w-full" />
        </div>
        <div>
          <label class="label">Período fin (opcional)</label>
          <input type="date" bind:value={runForm.period_end} class="input w-full" />
        </div>
        <div class="md:col-span-2 flex gap-3">
          <button type="submit" class="btn-accent flex items-center gap-2" disabled={running}>
            <Play size={14} class={running ? 'animate-pulse' : ''} />
            {running ? 'Ejecutando...' : 'Ejecutar'}
          </button>
          <button type="button" class="btn-secondary" on:click={() => showRunForm = false}>Cancelar</button>
        </div>
      </form>
    </div>
  {/if}

  <!-- Results -->
  {#if loading}
    <div class="text-center py-16 text-gray-500">
      <div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin mx-auto"></div>
    </div>
  {:else if runs.length === 0}
    <div class="text-center py-16 text-gray-500">No hay ejecuciones de reconciliación</div>
  {:else}
    <div class="space-y-3">
      {#each runs as r}
        {@const si = statusIcon(r.status)}
        <div class="card p-0 overflow-hidden">
          <button class="w-full px-6 py-4 flex items-center justify-between hover:bg-bg-page/50 transition-colors" type="button" on:click={() => toggleDetail(r.id)}>
            <div class="flex items-center gap-4">
              <svelte:component this={si.icon} size={20} class={si.color} />
              <div class="text-left">
                <div class="font-semibold text-text-primary">Ejecución #{r.id}</div>
                <div class="text-[11px] text-gray-500">{formatDate(r.period_start)} — {formatDate(r.period_end)}</div>
              </div>
            </div>
            <div class="flex items-center gap-6">
              <div class="text-right">
                <div class="text-[11px] text-gray-500">Stripe</div>
                <div class="font-semibold">{formatCurrency(r.stripe_total)}</div>
              </div>
              <div class="text-right">
                <div class="text-[11px] text-gray-500">Local DB</div>
                <div class="font-semibold">{formatCurrency(r.local_total)}</div>
              </div>
              <div class="text-right">
                <div class="text-[11px] text-gray-500">Diferencia</div>
                <div class="font-bold {discrepancyColor(r.discrepancy)}">{formatCurrency(r.discrepancy)}</div>
              </div>
              {#if expandedId === r.id}<ChevronUp size={16} />{:else}<ChevronDown size={16} />{/if}
            </div>
          </button>

          {#if expandedId === r.id && expandedDetail}
            <div class="border-t border-border-light px-6 py-4 bg-bg-page">
              <div class="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-4">
                <div>
                  <span class="text-[11px] text-gray-500">Estado</span>
                  <div class="mt-1"><span class="badge-{r.status === 'matched' || r.status === 'clean' ? 'success' : r.status === 'warning' ? 'warning' : 'error'}">{r.status}</span></div>
                </div>
                <div>
                  <span class="text-[11px] text-gray-500">Ejecutado por</span>
                  <div class="text-sm mt-1">{r.run_by || '—'}</div>
                </div>
                <div>
                  <span class="text-[11px] text-gray-500">Fecha</span>
                  <div class="text-sm mt-1">{formatDate(r.created_at)}</div>
                </div>
              </div>
              {#if expandedDetail.discrepancy_details}
                <div class="mt-3">
                  <span class="section-heading mb-2 block">Detalles de Discrepancia</span>
                  <pre class="text-xs bg-bg-card p-3 border border-border-light overflow-auto max-h-48 font-mono">{JSON.stringify(expandedDetail.discrepancy_details, null, 2)}</pre>
                </div>
              {/if}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>
