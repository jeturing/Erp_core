<script lang="ts">
  import { onMount } from 'svelte';
  import { invoicesApi, stripeSyncApi } from '../lib/api';
  import type { SyncResult, SyncStatus } from '../lib/api/stripeSync';
  import { toasts } from '../lib/stores';
  import type { InvoiceItem } from '../lib/types';
  import { formatCurrency, formatDate } from '../lib/utils/formatters';
  import {
    FileText, RefreshCw, Search, ChevronLeft, ChevronRight,
    Plus, CheckCircle, DollarSign, Clock, AlertCircle, Filter,
    Zap, CloudDownload, Link2, Unlink, ExternalLink,
  } from 'lucide-svelte';

  let invoices: InvoiceItem[] = [];
  let total = 0;
  let loading = true;
  let search = '';
  let statusFilter = '';
  let typeFilter = '';
  const PAGE_SIZE = 20;
  let currentPage = 0;

  // Stripe Sync
  let syncing = false;
  let syncStatus: SyncStatus | null = null;
  let showSyncPanel = false;
  let lastSyncResult: SyncResult | null = null;

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
      invoices = res?.invoices ?? [];
      total = res?.total ?? 0;
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  async function loadSyncStatus() {
    try {
      syncStatus = await stripeSyncApi.getStatus();
    } catch (_) { /* silent */ }
  }

  async function runFullSync() {
    syncing = true;
    try {
      lastSyncResult = await stripeSyncApi.fullSync(6);
      toasts.success('Sincronización Stripe completada');
      await loadSyncStatus();
      await loadInvoices(currentPage);
    } catch (e: any) {
      toasts.error(`Error sync: ${e.message}`);
    } finally {
      syncing = false;
    }
  }

  async function syncOnlyInvoices() {
    syncing = true;
    try {
      lastSyncResult = await stripeSyncApi.syncInvoices(6);
      toasts.success('Facturas importadas de Stripe');
      await loadSyncStatus();
      await loadInvoices(currentPage);
    } catch (e: any) {
      toasts.error(`Error sync facturas: ${e.message}`);
    } finally {
      syncing = false;
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

  function stripeUrl(stripeId: string): string {
    return `https://dashboard.stripe.com/invoices/${stripeId}`;
  }

  $: totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  $: startItem = currentPage * PAGE_SIZE + 1;
  $: endItem = Math.min((currentPage + 1) * PAGE_SIZE, total);

  $: filtered = (invoices || []).filter(i =>
    (i.invoice_number || '').toLowerCase().includes(search.toLowerCase())
  );

  $: totalAmount = (invoices || []).reduce((s, i) => s + i.total, 0);
  $: paidCount = (invoices || []).filter(i => i.status === 'paid').length;
  $: pendingCount = (invoices || []).filter(i => i.status === 'issued' || i.status === 'draft').length;
  $: stripeLinked = (invoices || []).filter(i => i.stripe_invoice_id).length;

  async function goToPage(page: number) {
    if (page < 0 || page >= totalPages) return;
    currentPage = page;
    await loadInvoices(currentPage);
  }

  onMount(() => {
    loadInvoices(0);
    loadSyncStatus();
  });
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><FileText size={24} /> Facturas</h1>
      <p class="page-subtitle">Facturación SaaS — Fuente de verdad: Stripe</p>
    </div>
    <div class="flex gap-2">
      <button class="btn-secondary flex items-center gap-2" on:click={() => showSyncPanel = !showSyncPanel}>
        <Zap size={14} /> Stripe Sync
      </button>
      <button class="btn-secondary flex items-center gap-2" on:click={() => loadInvoices(currentPage)} disabled={loading}>
        <RefreshCw size={14} class={loading ? 'animate-spin' : ''} /> Actualizar
      </button>
      <button class="btn-accent flex items-center gap-2" on:click={() => showGenerateForm = true}>
        <Plus size={16} /> Generar Factura
      </button>
    </div>
  </div>

  <!-- Stripe Sync Panel -->
  {#if showSyncPanel}
    <div class="card p-6 border border-indigo-500/30 bg-gradient-to-r from-indigo-500/5 to-purple-500/5">
      <div class="flex items-center justify-between mb-4">
        <h2 class="section-heading flex items-center gap-2">
          <CloudDownload size={18} class="text-indigo-400" /> Sincronización Stripe
        </h2>
        <div class="flex gap-2">
          <button class="btn-secondary btn-sm flex items-center gap-1.5" on:click={syncOnlyInvoices} disabled={syncing}>
            <FileText size={13} /> Solo Facturas
          </button>
          <button class="btn-accent flex items-center gap-2" on:click={runFullSync} disabled={syncing}>
            {#if syncing}
              <RefreshCw size={14} class="animate-spin" /> Sincronizando...
            {:else}
              <Zap size={14} /> Sincronización Completa
            {/if}
          </button>
        </div>
      </div>

      <!-- Sync Status Grid -->
      {#if syncStatus}
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <div class="rounded-lg bg-surface-dark p-3 text-center">
            <div class="text-[11px] text-gray-500 uppercase tracking-wider">Clientes</div>
            <div class="text-lg font-bold text-text-primary">{syncStatus.database.customers.total}</div>
            <div class="flex items-center justify-center gap-1 text-[10px]">
              <Link2 size={10} class="text-emerald-400" />
              <span class="text-emerald-400">{syncStatus.database.customers.stripe_linked}</span>
              <span class="text-gray-600 mx-0.5">|</span>
              <Unlink size={10} class="text-amber-400" />
              <span class="text-amber-400">{syncStatus.database.customers.unlinked}</span>
            </div>
          </div>
          <div class="rounded-lg bg-surface-dark p-3 text-center">
            <div class="text-[11px] text-gray-500 uppercase tracking-wider">Suscripciones</div>
            <div class="text-lg font-bold text-text-primary">{syncStatus.database.subscriptions.active}</div>
            <div class="flex items-center justify-center gap-1 text-[10px]">
              <Link2 size={10} class="text-emerald-400" />
              <span class="text-emerald-400">{syncStatus.database.subscriptions.stripe_linked}</span>
              <span class="text-gray-600 mx-0.5">|</span>
              <Unlink size={10} class="text-amber-400" />
              <span class="text-amber-400">{syncStatus.database.subscriptions.unlinked}</span>
            </div>
          </div>
          <div class="rounded-lg bg-surface-dark p-3 text-center">
            <div class="text-[11px] text-gray-500 uppercase tracking-wider">Facturas Stripe</div>
            <div class="text-lg font-bold text-indigo-400">{syncStatus.database.invoices.from_stripe}</div>
            <div class="text-[10px] text-gray-500">de {syncStatus.database.invoices.total} total</div>
          </div>
          <div class="rounded-lg bg-surface-dark p-3 text-center">
            <div class="text-[11px] text-gray-500 uppercase tracking-wider">Exentos</div>
            <div class="text-lg font-bold text-gray-500">{syncStatus.database.customers.admin_accounts}</div>
            <div class="text-[10px] text-gray-500">cuentas admin</div>
          </div>
        </div>
        {#if syncStatus.last_sync}
          <p class="text-[11px] text-gray-500">Última sync: {formatDate(syncStatus.last_sync)}</p>
        {:else}
          <p class="text-[11px] text-amber-400">⚠ Nunca sincronizado — ejecuta una sincronización completa</p>
        {/if}
      {/if}

      <!-- Last Sync Result -->
      {#if lastSyncResult}
        <div class="mt-4 rounded-lg bg-surface-dark p-4 text-sm space-y-2">
          <h3 class="font-semibold text-emerald-400 flex items-center gap-1.5"><CheckCircle size={14} /> Resultado</h3>
          {#if lastSyncResult.customers}
            <p class="text-gray-400">
              <span class="text-text-primary font-mono">{lastSyncResult.customers.linked}</span> clientes vinculados,
              <span class="text-text-primary font-mono">{lastSyncResult.customers.already_linked}</span> ya estaban,
              <span class="text-text-primary font-mono">{lastSyncResult.customers.not_found}</span> sin match
            </p>
          {/if}
          {#if lastSyncResult.subscriptions}
            <p class="text-gray-400">
              <span class="text-text-primary font-mono">{lastSyncResult.subscriptions.linked}</span> subs vinculadas,
              <span class="text-text-primary font-mono">{lastSyncResult.subscriptions.created}</span> creadas,
              <span class="text-text-primary font-mono">{lastSyncResult.subscriptions.updated}</span> actualizadas
            </p>
          {/if}
          {#if lastSyncResult.invoices}
            <p class="text-gray-400">
              <span class="text-text-primary font-mono">{lastSyncResult.invoices.imported}</span> facturas importadas,
              <span class="text-text-primary font-mono">{lastSyncResult.invoices.updated}</span> actualizadas,
              <span class="text-text-primary font-mono">{lastSyncResult.invoices.skipped_existing}</span> ya existentes
            </p>
          {/if}
        </div>
      {/if}
    </div>
  {/if}

  <!-- KPIs -->
  <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
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
    <div class="stat-card">
      <span class="stat-label flex items-center gap-1"><Link2 size={12} /> Stripe</span>
      <span class="stat-value text-indigo-400">{stripeLinked}</span>
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
              <th>Cliente / Tenant</th>
              <th>Tipo</th>
              <th>Emisor</th>
              <th>Total</th>
              <th>Estado</th>
              <th>Stripe</th>
              <th>Fecha</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {#each filtered as inv}
              <tr>
                <td class="font-mono font-semibold text-text-primary">{inv.invoice_number}</td>
                <td>
                  <div class="flex flex-col">
                    <span class="text-sm text-text-primary font-medium">{inv.company_name || '—'}</span>
                    {#if inv.subdomain}
                      <a href="https://{inv.subdomain}.sajet.us" target="_blank" rel="noopener"
                         class="text-[11px] text-indigo-400 hover:text-indigo-300 flex items-center gap-0.5">
                        <ExternalLink size={9} />{inv.subdomain}.sajet.us
                      </a>
                    {:else if inv.email}
                      <span class="text-[11px] text-gray-500">{inv.email}</span>
                    {/if}
                  </div>
                </td>
                <td><span class={typeBadge(inv.invoice_type)}>{inv.invoice_type}</span></td>
                <td class="text-sm">{inv.issuer || '—'}</td>
                <td class="font-semibold">{formatCurrency(inv.total)}</td>
                <td><span class={statusBadge(inv.status)}>{inv.status}</span></td>
                <td>
                  {#if inv.stripe_invoice_id}
                    <a href={stripeUrl(inv.stripe_invoice_id)} target="_blank" rel="noopener"
                       class="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300 text-[11px] font-mono"
                       title={inv.stripe_invoice_id}>
                      <Link2 size={11} />
                      {inv.stripe_invoice_id.slice(0, 12)}…
                    </a>
                  {:else}
                    <span class="text-gray-600 text-[11px]">—</span>
                  {/if}
                </td>
                <td class="text-sm text-text-secondary">{formatDate(inv.issued_at || inv.created_at)}</td>
                <td>
                  <div class="flex items-center gap-1">
                    {#if inv.status !== 'paid' && inv.status !== 'void'}
                      <button class="btn-sm btn-accent" title="Marcar pagada" on:click={() => markPaid(inv)}>
                        <CheckCircle size={14} />
                      </button>
                    {/if}
                    {#if inv.stripe_invoice_id}
                      <a href={stripeUrl(inv.stripe_invoice_id)} target="_blank" rel="noopener"
                         class="btn-sm btn-secondary" title="Ver en Stripe">
                        <ExternalLink size={14} />
                      </a>
                    {/if}
                  </div>
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
