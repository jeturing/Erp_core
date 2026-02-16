<script lang="ts">
  import { onMount } from 'svelte';
  import { billingApi } from '../lib/api';
  import { toasts } from '../lib/stores/toast';
  import { formatDate, formatCurrency, formatPercent } from '../lib/utils/formatters';
  import type { BillingMetrics, BillingInvoice } from '../lib/types';
  import { RefreshCw, ChevronLeft, ChevronRight } from 'lucide-svelte';

  let loading = true;
  let metrics: BillingMetrics | null = null;
  let invoices: BillingInvoice[] = [];
  let totalInvoices = 0;

  const PAGE_SIZE = 20;
  let currentPage = 0;

  async function loadMetrics() {
    try {
      metrics = await billingApi.getMetrics();
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error cargando métricas de billing');
    }
  }

  async function loadInvoices(page = 0) {
    try {
      const res = await billingApi.getInvoices(PAGE_SIZE, page * PAGE_SIZE);
      invoices = res.invoices;
      totalInvoices = res.total;
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error cargando facturas');
    }
  }

  async function loadAll() {
    loading = true;
    await Promise.all([loadMetrics(), loadInvoices(currentPage)]);
    loading = false;
  }

  onMount(loadAll);

  async function goToPage(page: number) {
    const maxPage = Math.ceil(totalInvoices / PAGE_SIZE) - 1;
    if (page < 0 || page > maxPage) return;
    currentPage = page;
    await loadInvoices(currentPage);
  }

  function statusBadge(status: string) {
    if (status === 'paid' || status === 'active') return 'badge-success';
    if (status === 'pending') return 'badge-warning';
    if (status === 'failed') return 'badge-error';
    if (status === 'cancelled') return 'badge-neutral';
    return 'badge-neutral';
  }

  function planBadge(plan: string) {
    if (plan === 'enterprise') return 'badge-enterprise';
    if (plan === 'pro') return 'badge-pro';
    return 'badge-basic';
  }

  $: totalPages = Math.max(1, Math.ceil(totalInvoices / PAGE_SIZE));
  $: startItem = currentPage * PAGE_SIZE + 1;
  $: endItem = Math.min((currentPage + 1) * PAGE_SIZE, totalInvoices);
</script>

<div class="p-6 lg:p-8 space-y-6">
  <!-- Page Header -->
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
      <h1 class="page-title">BILLING</h1>
      <p class="page-subtitle mt-1">Métricas financieras, facturas y distribución de planes</p>
    </div>
    <button class="btn btn-secondary btn-sm" on:click={loadAll} disabled={loading}>
      <RefreshCw size={13} class={loading ? 'animate-spin' : ''} />
      Actualizar
    </button>
  </div>

  {#if loading}
    <div class="py-24 flex justify-center">
      <div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin"></div>
    </div>
  {:else}
    <!-- Stat Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="stat-card">
        <span class="stat-label">MRR Total</span>
        <span class="stat-value">{formatCurrency(metrics?.mrr_total ?? 0)}</span>
        <span class="text-[11px] text-gray-500">{metrics?.total_active ?? 0} suscriptores activos</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Ingresos del Mes</span>
        <span class="stat-value text-success">{formatCurrency(metrics?.month_revenue ?? 0)}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Pendiente</span>
        <span class="stat-value text-warning">{formatCurrency(metrics?.pending_amount ?? 0)}</span>
        <span class="text-[11px] text-gray-500">{metrics?.pending_count ?? 0} facturas pendientes</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Churn Rate (30d)</span>
        <span class="stat-value text-error">{(metrics?.churn_rate ?? 0).toFixed(1)}%</span>
        <span class="text-[11px] text-gray-500">{metrics?.cancelled_30d ?? 0} cancelaciones</span>
      </div>
    </div>

    <!-- Plan Distribution -->
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <span class="section-heading">Distribución por Plan</span>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <!-- Basic -->
        <div class="rounded-lg border border-border-light p-4 bg-bg-page">
          <div class="flex items-center justify-between mb-2">
            <span class="badge badge-basic">basic</span>
            <span class="text-[11px] text-gray-500">{metrics?.plan_distribution.basic.count ?? 0} tenants</span>
          </div>
          <p class="text-2xl font-bold text-text-primary">{formatCurrency(metrics?.plan_distribution.basic.revenue ?? 0)}</p>
          <p class="text-[11px] text-gray-500 mt-1">ingresos / mes</p>
        </div>
        <!-- Pro -->
        <div class="rounded-lg border border-border-light p-4 bg-bg-page">
          <div class="flex items-center justify-between mb-2">
            <span class="badge badge-pro">pro</span>
            <span class="text-[11px] text-gray-500">{metrics?.plan_distribution.pro.count ?? 0} tenants</span>
          </div>
          <p class="text-2xl font-bold text-text-primary">{formatCurrency(metrics?.plan_distribution.pro.revenue ?? 0)}</p>
          <p class="text-[11px] text-gray-500 mt-1">ingresos / mes</p>
        </div>
        <!-- Enterprise -->
        <div class="rounded-lg border border-border-light p-4 bg-bg-page">
          <div class="flex items-center justify-between mb-2">
            <span class="badge badge-enterprise">enterprise</span>
            <span class="text-[11px] text-gray-500">{metrics?.plan_distribution.enterprise.count ?? 0} tenants</span>
          </div>
          <p class="text-2xl font-bold text-text-primary">{formatCurrency(metrics?.plan_distribution.enterprise.revenue ?? 0)}</p>
          <p class="text-[11px] text-gray-500 mt-1">ingresos / mes</p>
        </div>
      </div>
    </div>

    <!-- Invoices Table -->
    <div class="card p-0 overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b border-border-light">
        <span class="section-heading">Facturas</span>
        {#if totalInvoices > 0}
          <span class="text-[11px] text-gray-500">{startItem}–{endItem} de {totalInvoices}</span>
        {/if}
      </div>

      <div class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr>
              <th>#</th>
              <th>Cliente</th>
              <th>Plan</th>
              <th>Monto</th>
              <th>Estado</th>
              <th>Fecha</th>
            </tr>
          </thead>
          <tbody>
            {#each invoices as invoice (invoice.id)}
              <tr>
                <td class="font-mono text-[11px] text-gray-400">{invoice.id}</td>
                <td>
                  <div class="flex flex-col gap-0.5">
                    <span class="font-semibold text-text-primary">{invoice.company_name}</span>
                    <span class="text-[11px] text-gray-500">{invoice.email}</span>
                    <span class="text-[11px] text-gray-400 font-mono">{invoice.subdomain}</span>
                  </div>
                </td>
                <td>
                  <span class="badge {planBadge(invoice.plan)}">{invoice.plan}</span>
                </td>
                <td class="font-semibold text-text-primary">{formatCurrency(invoice.amount)}</td>
                <td>
                  <span class="badge {statusBadge(invoice.status)}">{invoice.status}</span>
                </td>
                <td class="text-text-secondary text-sm">{formatDate(invoice.created_at)}</td>
              </tr>
            {:else}
              <tr>
                <td colspan="6" class="text-center text-gray-500 py-12 text-sm">No hay facturas disponibles</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      {#if totalPages > 1}
        <div class="flex items-center justify-between px-6 py-3 border-t border-border-light">
          <span class="text-[11px] text-gray-500">
            Página {currentPage + 1} de {totalPages}
          </span>
          <div class="flex items-center gap-2">
            <button
              class="btn btn-secondary btn-sm"
              on:click={() => goToPage(currentPage - 1)}
              disabled={currentPage === 0}
            >
              <ChevronLeft size={13} />
              Anterior
            </button>
            <button
              class="btn btn-secondary btn-sm"
              on:click={() => goToPage(currentPage + 1)}
              disabled={currentPage >= totalPages - 1}
            >
              Siguiente
              <ChevronRight size={13} />
            </button>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>
