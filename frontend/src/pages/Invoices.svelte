<script lang="ts">
  import { onMount } from 'svelte';
  import { invoicesApi } from '../lib/api';
  import { toasts } from '../lib/stores';
  import type { InvoiceItem } from '../lib/types';
  import { formatCurrency, formatDate } from '../lib/utils/formatters';
  import {
    FileText, RefreshCw, Search, ChevronLeft, ChevronRight,
    Plus, CheckCircle, DollarSign, Clock, AlertCircle, Filter,
  } from 'lucide-svelte';

  let invoices: InvoiceItem[] = [];
  let total = 0;
  let loading = true;
  let search = '';
  let statusFilter = '';
  let typeFilter = '';
  const PAGE_SIZE = 20;
  let currentPage = 0;

  // Generate form
  let showGenerateForm = false;
  let generateForm = { subscription_id: 0, period_start: '', period_end: '' };
  let generating = false;

  async function loadInvoices(page = 0) {
    loading = true;
    try {
      const res = await invoicesApi.list({
        status: statusFilter || undefined,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      });
      invoices = res.items;
      total = res.total;
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  async function handleGenerate() {
    generating = true;
    try {
      const res = await invoicesApi.generate({
        subscription_id: generateForm.subscription_id,
        period_start: generateForm.period_start || undefined,
        period_end: generateForm.period_end || undefined,
      });
      toasts.success(`Factura ${res.invoice.invoice_number} generada`);
      showGenerateForm = false;
      generateForm = { subscription_id: 0, period_start: '', period_end: '' };
      await loadInvoices(currentPage);
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      generating = false;
    }
  }

  async function markPaid(inv: InvoiceItem) {
    if (!confirm(`¿Marcar ${inv.invoice_number} como pagada?`)) return;
    try {
      await invoicesApi.markPaid(inv.id);
      toasts.success(`${inv.invoice_number} marcada como pagada`);
      await loadInvoices(currentPage);
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  function statusBadge(status: string) {
    const map: Record<string, string> = {
      paid: 'badge-success', issued: 'badge-info', draft: 'badge-neutral',
      overdue: 'badge-error', void: 'badge-neutral', credited: 'badge-warning',
    };
    return map[status] || 'badge-neutral';
  }

  function typeBadge(t: string) {
    const map: Record<string, string> = {
      SUBSCRIPTION: 'badge-info', SETUP: 'badge-pro', ADDON: 'badge-warning',
      INTERCOMPANY: 'badge-enterprise', CREDIT_NOTE: 'badge-error',
    };
    return map[t] || 'badge-neutral';
  }

  $: totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  $: startItem = currentPage * PAGE_SIZE + 1;
  $: endItem = Math.min((currentPage + 1) * PAGE_SIZE, total);

  $: filtered = invoices.filter(i =>
    (i.invoice_number || '').toLowerCase().includes(search.toLowerCase())
  );

  $: totalAmount = invoices.reduce((s, i) => s + i.total, 0);
  $: paidCount = invoices.filter(i => i.status === 'paid').length;
  $: pendingCount = invoices.filter(i => i.status === 'issued' || i.status === 'draft').length;

  async function goToPage(page: number) {
    if (page < 0 || page >= totalPages) return;
    currentPage = page;
    await loadInvoices(currentPage);
  }

  onMount(() => loadInvoices(0));
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><FileText size={24} /> Facturas</h1>
      <p class="page-subtitle">Facturación SaaS — Direct, Partner e Intercompany</p>
    </div>
    <div class="flex gap-2">
      <button class="btn-secondary flex items-center gap-2" on:click={() => loadInvoices(currentPage)} disabled={loading}>
        <RefreshCw size={14} class={loading ? 'animate-spin' : ''} /> Actualizar
      </button>
      <button class="btn-accent flex items-center gap-2" on:click={() => showGenerateForm = true}>
        <Plus size={16} /> Generar Factura
      </button>
    </div>
  </div>

  <!-- KPIs -->
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
    <div class="stat-card">
      <span class="stat-label">Total Facturas</span>
      <span class="stat-value">{total}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Monto Total</span>
      <span class="stat-value text-success">{formatCurrency(totalAmount)}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Pagadas</span>
      <span class="stat-value text-success">{paidCount}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Pendientes</span>
      <span class="stat-value text-warning">{pendingCount}</span>
    </div>
  </div>

  <!-- Generate Form -->
  {#if showGenerateForm}
    <div class="card p-6 border border-border-dark">
      <h2 class="section-heading mb-4">Generar Factura</h2>
      <form on:submit|preventDefault={handleGenerate} class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="label">Subscription ID *</label>
          <input type="number" bind:value={generateForm.subscription_id} required min="1" class="input w-full" />
        </div>
        <div>
          <label class="label">Período inicio</label>
          <input type="date" bind:value={generateForm.period_start} class="input w-full" />
        </div>
        <div>
          <label class="label">Período fin</label>
          <input type="date" bind:value={generateForm.period_end} class="input w-full" />
        </div>
        <div class="md:col-span-3 flex gap-3">
          <button type="submit" class="btn-accent" disabled={generating}>
            {generating ? 'Generando...' : 'Generar'}
          </button>
          <button type="button" class="btn-secondary" on:click={() => showGenerateForm = false}>Cancelar</button>
        </div>
      </form>
    </div>
  {/if}

  <!-- Filters -->
  <div class="flex flex-col sm:flex-row gap-3">
    <div class="relative flex-1">
      <Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
      <input type="text" bind:value={search} placeholder="Buscar por número..." class="input pl-10 w-full" />
    </div>
    <select bind:value={statusFilter} on:change={() => { currentPage = 0; loadInvoices(0); }} class="input w-auto">
      <option value="">Todos los estados</option>
      <option value="draft">Draft</option>
      <option value="issued">Issued</option>
      <option value="paid">Paid</option>
      <option value="overdue">Overdue</option>
      <option value="void">Void</option>
    </select>
  </div>

  <!-- Table -->
  {#if loading}
    <div class="text-center py-16 text-gray-500">
      <div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin mx-auto"></div>
    </div>
  {:else}
    <div class="card p-0 overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b border-border-light">
        <span class="section-heading">Facturas</span>
        {#if total > 0}
          <span class="text-[11px] text-gray-500">{startItem}–{endItem} de {total}</span>
        {/if}
      </div>
      <div class="overflow-x-auto">
        <table class="table w-full">
          <thead>
            <tr>
              <th>Número</th>
              <th>Tipo</th>
              <th>Emisor</th>
              <th>Subtotal</th>
              <th>Tax</th>
              <th>Total</th>
              <th>Estado</th>
              <th>Fecha</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {#each filtered as inv}
              <tr>
                <td class="font-mono font-semibold text-text-primary">{inv.invoice_number}</td>
                <td><span class={typeBadge(inv.invoice_type)}>{inv.invoice_type}</span></td>
                <td class="text-sm">{inv.issuer || '—'}</td>
                <td class="text-sm">{formatCurrency(inv.subtotal)}</td>
                <td class="text-sm text-gray-500">{formatCurrency(inv.tax_amount)}</td>
                <td class="font-semibold">{formatCurrency(inv.total)}</td>
                <td><span class={statusBadge(inv.status)}>{inv.status}</span></td>
                <td class="text-sm text-text-secondary">{formatDate(inv.issued_at || inv.created_at)}</td>
                <td>
                  {#if inv.status !== 'paid' && inv.status !== 'void'}
                    <button class="btn-sm btn-accent" title="Marcar pagada" on:click={() => markPaid(inv)}>
                      <CheckCircle size={14} />
                    </button>
                  {/if}
                </td>
              </tr>
            {:else}
              <tr>
                <td colspan="9" class="text-center text-gray-500 py-12">No hay facturas</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
      {#if totalPages > 1}
        <div class="flex items-center justify-between px-6 py-3 border-t border-border-light">
          <span class="text-[11px] text-gray-500">Página {currentPage + 1} de {totalPages}</span>
          <div class="flex items-center gap-2">
            <button class="btn btn-secondary btn-sm" on:click={() => goToPage(currentPage - 1)} disabled={currentPage === 0}>
              <ChevronLeft size={13} /> Anterior
            </button>
            <button class="btn btn-secondary btn-sm" on:click={() => goToPage(currentPage + 1)} disabled={currentPage >= totalPages - 1}>
              Siguiente <ChevronRight size={13} />
            </button>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>
