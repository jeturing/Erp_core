<script lang="ts">
  import { onMount } from 'svelte';
  import { seatsApi } from '../lib/api';
  import { partnersApi } from '../lib/api/partners';
  import { toasts } from '../lib/stores';
  import type { SeatHWMRecord, SeatSummaryResponse, SeatOverviewItem, SeatOverviewGroup } from '../lib/types';
  import {
    Users, RefreshCw, TrendingUp,
    Clock, Zap, BarChart3, Search, Unlink,
  } from 'lucide-svelte';

  let loading = true;
  let overviewLoading = true;
  let search = '';
  let overviewItems: SeatOverviewItem[] = [];
  let groupedByPartner: SeatOverviewGroup[] = [];
  let selectedTenant: SeatOverviewItem | null = null;

  let hwmRecords: SeatHWMRecord[] = [];
  let summary: SeatSummaryResponse | null = null;
  let syncing = false;
  let unlinkingTenantId: number | null = null;

  async function loadDetail(subscriptionId?: number) {
    loading = true;
    try {
      if (!subscriptionId) {
        hwmRecords = [];
        summary = null;
        return;
      }

      const [hwmRes, sumRes] = await Promise.all([
        seatsApi.getHWM(subscriptionId),
        seatsApi.getSummary(subscriptionId),
      ]);
      hwmRecords = hwmRes.items ?? hwmRes.records ?? [];
      summary = sumRes;
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  async function loadOverview() {
    overviewLoading = true;
    try {
      const res = await seatsApi.getOverview(search || undefined);
      overviewItems = res.items ?? [];
      groupedByPartner = res.groups ?? [];

      if (!selectedTenant && overviewItems.length > 0) {
        selectedTenant = overviewItems[0];
      } else if (selectedTenant) {
        const refreshed = overviewItems.find((item) => item.subscription_id === selectedTenant?.subscription_id);
        selectedTenant = refreshed || null;
      }

      await loadDetail(selectedTenant?.subscription_id);
    } catch (e: any) {
      toasts.error(e.message || 'No se pudo cargar el overview de seats');
      overviewItems = [];
      groupedByPartner = [];
      selectedTenant = null;
      await loadDetail(undefined);
    } finally {
      overviewLoading = false;
    }
  }

  async function handleSelectTenant(tenant: SeatOverviewItem) {
    selectedTenant = tenant;
    await loadDetail(tenant.subscription_id);
  }

  async function handleUnlinkTenant(tenant: SeatOverviewItem) {
    if (!tenant.partner_id) return;
    if (!confirm(`¿Desvincular "${tenant.company_name}" del partner de facturación?`)) return;
    unlinkingTenantId = tenant.customer_id;
    try {
      await partnersApi.unlinkCustomer(tenant.partner_id, tenant.customer_id);
      toasts.success('Tenant desvinculado del partner');
      await loadOverview();
    } catch (e: any) {
      toasts.error(e.message || 'No se pudo desvincular el tenant');
    } finally {
      unlinkingTenantId = null;
    }
  }

  async function handleSync() {
    syncing = true;
    try {
      const res = await seatsApi.syncStripe();
      const failed = (res as any).failed ?? (res as any).errors ?? 0;
      toasts.success(`Sync completado: ${res.synced} actualizados, ${failed} errores`);
      await loadOverview();
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

  onMount(loadOverview);
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><Users size={24} /> Seats</h1>
      <p class="page-subtitle">Asientos por tenant, agrupados por partner y sincronización con Stripe</p>
    </div>
    <div class="flex gap-2">
      <button class="btn-secondary flex items-center gap-2" on:click={loadOverview} disabled={overviewLoading}>
        <RefreshCw size={14} class={overviewLoading ? 'animate-spin' : ''} /> Actualizar
      </button>
      <button class="btn-accent flex items-center gap-2" on:click={handleSync} disabled={syncing}>
        <Zap size={14} class={syncing ? 'animate-pulse' : ''} /> Sync Stripe
      </button>
    </div>
  </div>

  <div class="relative max-w-xl">
    <Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
    <input
      type="text"
      bind:value={search}
      placeholder="Buscar por tenant, partner, plan, email o subscription..."
      class="input pl-10 w-full"
      on:keydown={(e) => e.key === 'Enter' && loadOverview()}
    />
  </div>

  <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
    <div class="xl:col-span-1 space-y-4">
      {#if overviewLoading}
        <div class="card p-8 text-center text-gray-500">Cargando tenants...</div>
      {:else if groupedByPartner.length === 0}
        <div class="card p-8 text-center text-gray-500">No hay tenants con seats para mostrar.</div>
      {:else}
        {#each groupedByPartner as group}
          <div class="card p-0 overflow-hidden">
            <div class="px-4 py-3 border-b border-border-light bg-dark-subtle">
              <div class="font-semibold text-sm">{group.partner_name}</div>
              <div class="text-xs text-gray-500">
                {group.subscriptions} suscripción(es) · {group.billable_count} seat(s) facturable(s)
              </div>
            </div>
            <div class="divide-y divide-border-light">
              {#each group.tenants as tenant}
                <div
                  class="w-full text-left px-4 py-3 hover:bg-cloud dark:hover:bg-dark-card transition-colors cursor-pointer {selectedTenant?.subscription_id === tenant.subscription_id ? 'bg-cloud dark:bg-dark-card' : ''}"
                  on:click={() => handleSelectTenant(tenant)}
                  on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && handleSelectTenant(tenant)}
                  role="button"
                  tabindex="0"
                >
                  <div class="flex items-start justify-between gap-2">
                    <div>
                      <div class="font-medium text-sm">{tenant.company_name}</div>
                      <div class="text-xs text-gray-500">{tenant.subdomain}.sajet.us · {tenant.plan_name || 'sin plan'}</div>
                    </div>
                    <div class="text-right text-xs">
                      <div class="text-text-primary font-semibold">{tenant.billable_count} billable</div>
                      <div class="text-gray-500">HWM {tenant.month_hwm}</div>
                    </div>
                  </div>
                  {#if tenant.partner_id}
                    <div class="mt-2">
                      <button
                        class="btn-sm btn-secondary text-xs"
                        disabled={unlinkingTenantId === tenant.customer_id}
                        on:click|stopPropagation={() => handleUnlinkTenant(tenant)}
                      >
                        <Unlink size={12} />
                        {unlinkingTenantId === tenant.customer_id ? 'Desvinculando...' : 'Desvincular partner'}
                      </button>
                    </div>
                  {/if}
                </div>
              {/each}
            </div>
          </div>
        {/each}
      {/if}
    </div>

    <div class="xl:col-span-2 space-y-6">
      {#if selectedTenant}
        <div class="card">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <h2 class="section-heading">{selectedTenant.company_name}</h2>
              <p class="text-xs text-gray-500">
                {selectedTenant.subdomain}.sajet.us · Sub #{selectedTenant.subscription_id}
                {#if selectedTenant.partner_name} · Partner: {selectedTenant.partner_name}{/if}
              </p>
            </div>
          </div>
        </div>
      {/if}

  <!-- KPIs -->
  {#if summary}
    <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
      <div class="stat-card">
        <span class="stat-label">Usuarios actuales</span>
        <span class="stat-value">{summary.current_count ?? summary.current_user_count ?? 0}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">HWM del período</span>
        <span class="stat-value text-terracotta">{summary.hwm_count ?? summary.month_hwm ?? 0}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">En gracia</span>
        <span class="stat-value text-warning">{summary.grace_count ?? summary.grace_active_count ?? 0}</span>
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

  <!-- HWM History -->
  {#if loading}
    <div class="text-center py-16 text-gray-500">
      <div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin mx-auto"></div>
      <p class="mt-3">Cargando datos de seats...</p>
    </div>
  {:else}
    {#if !selectedTenant}
      <div class="card p-8 text-center text-gray-500">
        Selecciona un tenant para cargar el historial de seats.
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
    {/if}

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
  </div>
</div>
