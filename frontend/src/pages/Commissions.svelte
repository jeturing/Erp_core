<script lang="ts">
  import { onMount } from 'svelte';
  import { partnersApi } from '../lib/api/partners';
  import type { CommissionItem, PartnerItem } from '../lib/types';
  import { toasts } from '../lib/stores';
  import {
    Percent, Plus, Search, CheckCircle, Clock, DollarSign,
    ArrowUpRight, Banknote,
  } from 'lucide-svelte';

  let commissions: CommissionItem[] = [];
  let partners: PartnerItem[] = [];
  let loading = true;
  let search = '';
  let partnerFilter = 0;
  let statusFilter = '';
  let summary = { total_partner_amount: 0, total_jeturing_amount: 0, total_pending_payout: 0, total_gross: 0 };
  let showForm = false;

  let form = {
    partner_id: 0,
    period_start: '',
    period_end: '',
    gross_revenue: 0,
    deductions: { fees: 0, refunds: 0, chargebacks: 0, taxes: 0 },
    notes: '',
  };

  function resetForm() {
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
    const end = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split('T')[0];
    form = { partner_id: 0, period_start: start, period_end: end, gross_revenue: 0, deductions: { fees: 0, refunds: 0, chargebacks: 0, taxes: 0 }, notes: '' };
  }

  async function loadData() {
    loading = true;
    try {
      const [commsRes, partnersRes] = await Promise.all([
        partnersApi.getCommissions(partnerFilter || undefined, statusFilter || undefined),
        partnersApi.getPartners(),
      ]);
      commissions = commsRes?.items ?? [];
      summary = commsRes?.summary ?? { total_partner_amount: 0, total_jeturing_amount: 0, total_pending_payout: 0, total_gross: 0 };
      partners = (partnersRes?.items ?? []).filter(p => p.status === 'active');
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  async function handleSubmit() {
    if (!form.partner_id) { toasts.error('Seleccione un partner'); return; }
    try {
      await partnersApi.createCommission({
        partner_id: form.partner_id,
        period_start: form.period_start,
        period_end: form.period_end,
        gross_revenue: form.gross_revenue,
        deductions: form.deductions,
        notes: form.notes,
      });
      toasts.success('Comisión creada');
      showForm = false;
      resetForm();
      await loadData();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  async function approveCommission(id: number) {
    try {
      await partnersApi.approveCommission(id);
      toasts.success('Comisión aprobada');
      await loadData();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  async function payCommission(id: number) {
    const ref = prompt('Referencia de pago (opcional):');
    try {
      await partnersApi.payCommission(id, ref || undefined);
      toasts.success('Comisión marcada como pagada');
      await loadData();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  $: filtered = (commissions || []).filter(c =>
    (c.partner_name || '').toLowerCase().includes(search.toLowerCase())
  );

  onMount(() => { resetForm(); loadData(); });
</script>

<div class="p-6 space-y-6">
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><Percent size={24} /> Comisiones</h1>
      <p class="page-subtitle">Split 50/50 sobre Ingresos Netos — Cláusula 8</p>
    </div>
    <button class="btn-accent flex items-center gap-2" on:click={() => { resetForm(); showForm = true; }}>
      <Plus size={16} /> Nueva Comisión
    </button>
  </div>

  <!-- Stats -->
  <div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
    <div class="stat-card">
      <div class="text-xs font-semibold uppercase text-gray-500 mb-1">Ingresos Brutos</div>
      <div class="text-2xl font-bold text-text-light">${summary.total_gross.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
    </div>
    <div class="stat-card">
      <div class="text-xs font-semibold uppercase text-gray-500 mb-1">Partners (50%)</div>
      <div class="text-2xl font-bold text-purple-400">${summary.total_partner_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
    </div>
    <div class="stat-card">
      <div class="text-xs font-semibold uppercase text-gray-500 mb-1">Jeturing (50%)</div>
      <div class="text-2xl font-bold text-blue-400">${summary.total_jeturing_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
    </div>
    <div class="stat-card">
      <div class="text-xs font-semibold uppercase text-gray-500 mb-1">Pendiente pago</div>
      <div class="text-2xl font-bold text-amber-400">${summary.total_pending_payout.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
    </div>
  </div>

  <!-- Filters -->
  <div class="flex flex-col sm:flex-row gap-3">
    <div class="relative flex-1">
      <Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
      <input type="text" bind:value={search} placeholder="Buscar por partner..." class="input pl-10 w-full" />
    </div>
    <select bind:value={partnerFilter} on:change={loadData} class="input w-auto">
      <option value={0}>Todos los partners</option>
      {#each partners as p}
        <option value={p.id}>{p.company_name}</option>
      {/each}
    </select>
    <select bind:value={statusFilter} on:change={loadData} class="input w-auto">
      <option value="">Todos los estados</option>
      <option value="pending">Pendiente</option>
      <option value="approved">Aprobada</option>
      <option value="paid">Pagada</option>
      <option value="disputed">Disputada</option>
    </select>
  </div>

  <!-- Form -->
  {#if showForm}
    <div class="card p-6 border border-border-dark">
      <h2 class="section-heading mb-4">Nueva Comisión</h2>
      <form on:submit|preventDefault={handleSubmit} class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="label">Partner *</label>
          <select bind:value={form.partner_id} required class="input w-full">
            <option value={0}>— Seleccionar —</option>
            {#each partners as p}
              <option value={p.id}>{p.company_name} ({p.commission_rate}%)</option>
            {/each}
          </select>
        </div>
        <div>
          <label class="label">Ingreso bruto ($) *</label>
          <input type="number" bind:value={form.gross_revenue} min="0" step="0.01" required class="input w-full" />
        </div>
        <div>
          <label class="label">Inicio período</label>
          <input type="date" bind:value={form.period_start} class="input w-full" />
        </div>
        <div>
          <label class="label">Fin período</label>
          <input type="date" bind:value={form.period_end} class="input w-full" />
        </div>
        <div class="md:col-span-2">
          <label class="label">Deducciones</label>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <label class="text-xs text-gray-500">Fees</label>
              <input type="number" bind:value={form.deductions.fees} min="0" step="0.01" class="input w-full" />
            </div>
            <div>
              <label class="text-xs text-gray-500">Refunds</label>
              <input type="number" bind:value={form.deductions.refunds} min="0" step="0.01" class="input w-full" />
            </div>
            <div>
              <label class="text-xs text-gray-500">Chargebacks</label>
              <input type="number" bind:value={form.deductions.chargebacks} min="0" step="0.01" class="input w-full" />
            </div>
            <div>
              <label class="text-xs text-gray-500">Taxes</label>
              <input type="number" bind:value={form.deductions.taxes} min="0" step="0.01" class="input w-full" />
            </div>
          </div>
        </div>
        <div class="md:col-span-2">
          <label class="label">Notas</label>
          <textarea bind:value={form.notes} rows="2" class="input w-full"></textarea>
        </div>
        <div class="md:col-span-2 flex gap-3">
          <button type="submit" class="btn-accent">Crear Comisión</button>
          <button type="button" class="btn-secondary" on:click={() => { showForm = false; }}>Cancelar</button>
        </div>
      </form>
    </div>
  {/if}

  <!-- Table -->
  {#if loading}
    <div class="text-center py-12 text-gray-500">Cargando comisiones...</div>
  {:else if filtered.length === 0}
    <div class="text-center py-12 text-gray-500">No hay comisiones registradas</div>
  {:else}
    <div class="overflow-x-auto">
      <table class="table w-full">
        <thead>
          <tr>
            <th>Partner</th>
            <th>Período</th>
            <th>Bruto</th>
            <th>Neto</th>
            <th>Partner $</th>
            <th>Jeturing $</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#each filtered as c}
            <tr>
              <td class="font-semibold text-text-light">{c.partner_name}</td>
              <td class="text-xs">
                {c.period_start ? new Date(c.period_start).toLocaleDateString() : '—'} →
                {c.period_end ? new Date(c.period_end).toLocaleDateString() : '—'}
              </td>
              <td class="font-mono text-sm">${c.gross_revenue.toLocaleString()}</td>
              <td class="font-mono text-sm">${c.net_revenue.toLocaleString()}</td>
              <td class="font-mono text-sm text-purple-400">${c.partner_amount.toLocaleString()}</td>
              <td class="font-mono text-sm text-blue-400">${c.jeturing_amount.toLocaleString()}</td>
              <td>
                {#if c.status === 'paid'}
                  <span class="badge-success flex items-center gap-1 w-fit"><CheckCircle size={12} /> Pagada</span>
                {:else if c.status === 'approved'}
                  <span class="badge-info flex items-center gap-1 w-fit"><ArrowUpRight size={12} /> Aprobada</span>
                {:else if c.status === 'pending'}
                  <span class="badge-warning flex items-center gap-1 w-fit"><Clock size={12} /> Pendiente</span>
                {:else}
                  <span class="badge-danger">{c.status}</span>
                {/if}
              </td>
              <td>
                <div class="flex gap-1">
                  {#if c.status === 'pending'}
                    <button class="btn-sm btn-accent" title="Aprobar" on:click={() => approveCommission(c.id)}><CheckCircle size={14} /></button>
                  {/if}
                  {#if c.status === 'approved'}
                    <button class="btn-sm btn-accent" title="Marcar pagada" on:click={() => payCommission(c.id)}><Banknote size={14} /></button>
                  {/if}
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
