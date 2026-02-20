<script lang="ts">
  import { onMount } from 'svelte';
  import { settlementsApi } from '../lib/api';
  import { toasts } from '../lib/stores';
  import type { SettlementPeriod, SettlementLine } from '../lib/types';
  import { formatCurrency, formatDate } from '../lib/utils/formatters';
  import {
    Scale, Plus, RefreshCw, ChevronDown, ChevronUp,
    Lock, DollarSign, ArrowRightLeft,
  } from 'lucide-svelte';

  let settlements: SettlementPeriod[] = [];
  let loading = true;
  let expandedId: number | null = null;
  let expandedLines: SettlementLine[] = [];
  let loadingDetail = false;

  // Create form
  let showForm = false;
  let form = { partner_id: 0, period_start: '', period_end: '' };
  let creating = false;

  async function loadSettlements() {
    loading = true;
    try {
      const res = await settlementsApi.list({ limit: 50 });
      settlements = res.items ?? [];
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  async function toggleDetail(id: number) {
    if (expandedId === id) {
      expandedId = null;
      expandedLines = [];
      return;
    }
    loadingDetail = true;
    try {
      const detail = await settlementsApi.get(id);
      expandedLines = detail.lines || [];
      expandedId = id;
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      loadingDetail = false;
    }
  }

  async function handleCreate() {
    creating = true;
    try {
      const res = await settlementsApi.create(form);
      toasts.success(`Liquidación creada: ID ${res.settlement.id}`);
      showForm = false;
      form = { partner_id: 0, period_start: '', period_end: '' };
      await loadSettlements();
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      creating = false;
    }
  }

  async function closeSettlement(id: number) {
    if (!confirm('¿Cerrar esta liquidación? Se calculará el split 50/50.')) return;
    try {
      await settlementsApi.close(id);
      toasts.success('Liquidación cerrada');
      await loadSettlements();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  function statusBadge(status: string) {
    const map: Record<string, string> = {
      draft: 'badge-neutral', pending_approval: 'badge-warning',
      approved: 'badge-info', transferred: 'badge-success', disputed: 'badge-error',
    };
    return map[status] || 'badge-neutral';
  }

  $: totalGross = (settlements || []).reduce((s, i) => s + i.gross_revenue, 0);
  $: totalJeturing = (settlements || []).reduce((s, i) => s + i.jeturing_share, 0);
  $: totalPartner = (settlements || []).reduce((s, i) => s + i.final_partner_payout, 0);

  onMount(loadSettlements);
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><Scale size={24} /> Liquidaciones</h1>
      <p class="page-subtitle">Settlement 50/50 — Partner ↔ Jeturing</p>
    </div>
    <div class="flex gap-2">
      <button class="btn-secondary flex items-center gap-2" on:click={loadSettlements} disabled={loading}>
        <RefreshCw size={14} class={loading ? 'animate-spin' : ''} /> Actualizar
      </button>
      <button class="btn-accent flex items-center gap-2" on:click={() => showForm = true}>
        <Plus size={16} /> Nueva Liquidación
      </button>
    </div>
  </div>

  <!-- KPIs -->
  <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
    <div class="stat-card">
      <span class="stat-label">Revenue Bruto Total</span>
      <span class="stat-value">{formatCurrency(totalGross)}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Share Jeturing</span>
      <span class="stat-value text-info">{formatCurrency(totalJeturing)}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Payout Partners</span>
      <span class="stat-value text-terracotta">{formatCurrency(totalPartner)}</span>
    </div>
  </div>

  <!-- Create Form -->
  {#if showForm}
    <div class="card p-6 border border-border-dark">
      <h2 class="section-heading mb-4">Nuevo Período de Liquidación</h2>
      <form on:submit|preventDefault={handleCreate} class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="label">Partner ID *</label>
          <input type="number" bind:value={form.partner_id} required min="1" class="input w-full" />
        </div>
        <div>
          <label class="label">Período inicio *</label>
          <input type="date" bind:value={form.period_start} required class="input w-full" />
        </div>
        <div>
          <label class="label">Período fin *</label>
          <input type="date" bind:value={form.period_end} required class="input w-full" />
        </div>
        <div class="md:col-span-3 flex gap-3">
          <button type="submit" class="btn-accent" disabled={creating}>{creating ? 'Creando...' : 'Crear'}</button>
          <button type="button" class="btn-secondary" on:click={() => showForm = false}>Cancelar</button>
        </div>
      </form>
    </div>
  {/if}

  <!-- Table -->
  {#if loading}
    <div class="text-center py-16 text-gray-500">
      <div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin mx-auto"></div>
    </div>
  {:else if settlements.length === 0}
    <div class="text-center py-16 text-gray-500">No hay liquidaciones registradas</div>
  {:else}
    <div class="space-y-3">
      {#each settlements as s}
        <div class="card p-0 overflow-hidden">
          <button class="w-full px-6 py-4 flex items-center justify-between hover:bg-bg-page/50 transition-colors" type="button" on:click={() => toggleDetail(s.id)}>
            <div class="flex items-center gap-4">
              <span class="font-mono text-sm text-gray-400">#{s.id}</span>
              <div class="text-left">
                <div class="font-semibold text-text-primary">Partner #{s.partner_id}</div>
                <div class="text-[11px] text-gray-500">{formatDate(s.period_start)} — {formatDate(s.period_end)}</div>
              </div>
            </div>
            <div class="flex items-center gap-6">
              <div class="text-right">
                <div class="text-sm text-gray-500">Gross</div>
                <div class="font-semibold">{formatCurrency(s.gross_revenue)}</div>
              </div>
              <div class="text-right">
                <div class="text-sm text-gray-500">Jeturing</div>
                <div class="font-semibold text-info">{formatCurrency(s.jeturing_share)}</div>
              </div>
              <div class="text-right">
                <div class="text-sm text-gray-500">Partner</div>
                <div class="font-semibold text-terracotta">{formatCurrency(s.final_partner_payout)}</div>
              </div>
              <span class={statusBadge(s.status)}>{s.status}</span>
              {#if expandedId === s.id}<ChevronUp size={16} />{:else}<ChevronDown size={16} />{/if}
            </div>
          </button>

          {#if expandedId === s.id}
            <div class="border-t border-border-light px-6 py-4 bg-bg-page">
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
                <div><span class="text-[11px] text-gray-500">Net Revenue</span><div class="font-semibold">{formatCurrency(s.net_revenue)}</div></div>
                <div><span class="text-[11px] text-gray-500">Offset</span><div class="font-semibold">{formatCurrency(s.offset_amount)}</div></div>
                <div><span class="text-[11px] text-gray-500">Transfer Ref</span><div class="text-sm font-mono">{s.transfer_reference || '—'}</div></div>
                <div><span class="text-[11px] text-gray-500">Aprobado por</span><div class="text-sm">{s.approved_by || '—'}</div></div>
              </div>
              {#if expandedLines.length > 0}
                <table class="table w-full text-sm">
                  <thead>
                    <tr>
                      <th>Desc</th>
                      <th>Gross</th>
                      <th>Fees</th>
                      <th>Net</th>
                      <th>Jeturing</th>
                      <th>Partner</th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each expandedLines as l}
                      <tr>
                        <td>{l.description || `Sub #${l.subscription_id}`}</td>
                        <td>{formatCurrency(l.gross_amount)}</td>
                        <td class="text-gray-500">{formatCurrency(l.stripe_fee + l.refunds + l.chargebacks)}</td>
                        <td>{formatCurrency(l.net_amount)}</td>
                        <td class="text-info">{formatCurrency(l.jeturing_amount)}</td>
                        <td class="text-terracotta">{formatCurrency(l.partner_amount)}</td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              {:else if loadingDetail}
                <p class="text-gray-500 text-sm">Cargando líneas...</p>
              {:else}
                <p class="text-gray-500 text-sm">Sin líneas de detalle</p>
              {/if}
              {#if s.status === 'draft' || s.status === 'pending_approval'}
                <div class="mt-4 flex justify-end">
                  <button class="btn-accent flex items-center gap-2" on:click={() => closeSettlement(s.id)}>
                    <Lock size={14} /> Cerrar Liquidación
                  </button>
                </div>
              {/if}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>
