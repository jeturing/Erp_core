<script lang="ts">
  import { onMount } from 'svelte';
  import { quotasApi } from '../lib/api';
  import type { AllQuotasResponse, CustomerQuotaSummary, CustomerQuotas, CustomerEmailLimits } from '../lib/api/quotas';
  import { toasts } from '../lib/stores';
  import {
    Gauge, RefreshCw, Search, ChevronDown, ChevronRight,
    Users, Globe, Building2, HardDrive, Archive, Zap,
    AlertTriangle, CheckCircle, Mail, Pencil,
  } from 'lucide-svelte';

  let customers: CustomerQuotaSummary[] = [];
  let total = 0;
  let loading = true;
  let search = '';
  let expandedId: number | null = null;
  let expandedQuotas: CustomerQuotas | null = null;
  let expandedEmailLimits: CustomerEmailLimits | null = null;
  let loadingDetail = false;
  let emailModalOpen = false;
  let emailSaving = false;
  let emailForm = {
    max_emails_monthly: 0,
    email_rate_per_minute: 0,
    email_rate_per_hour: 0,
    email_rate_per_day: 0,
  };

  const RESOURCE_ICONS: Record<string, any> = {
    users: Users,
    domains: Globe,
    websites: Globe,
    companies: Building2,
    storage_mb: HardDrive,
    backups: Archive,
    api_calls: Zap,
  };

  const RESOURCE_LABELS: Record<string, string> = {
    users: 'Usuarios',
    domains: 'Dominios',
    websites: 'Sitios web',
    companies: 'Empresas',
    storage_mb: 'Almacenamiento (MB)',
    backups: 'Backups',
    api_calls: 'Llamadas API',
  };

  async function loadAll() {
    loading = true;
    try {
      const res: AllQuotasResponse = await quotasApi.getAllQuotas();
      customers = res.customers ?? [];
      total = res.total ?? 0;
    } catch (e: any) {
      toasts.error(e.message ?? 'Error cargando quotas');
    } finally {
      loading = false;
    }
  }

  async function toggleDetail(customerId: number) {
    if (expandedId === customerId) {
      expandedId = null;
      expandedQuotas = null;
      expandedEmailLimits = null;
      return;
    }
    expandedId = customerId;
    loadingDetail = true;
    try {
      const [quotaRes, emailRes] = await Promise.all([
        quotasApi.getCustomerQuotas(customerId),
        quotasApi.getCustomerEmailLimits(customerId),
      ]);
      expandedQuotas = quotaRes;
      expandedEmailLimits = emailRes;
    } catch (e: any) {
      toasts.error(e.message ?? 'Error cargando detalle');
      expandedEmailLimits = null;
    } finally {
      loadingDetail = false;
    }
  }

  function openEmailModal() {
    if (!expandedEmailLimits) return;
    emailForm = {
      max_emails_monthly: expandedEmailLimits.limits.max_emails_monthly,
      email_rate_per_minute: expandedEmailLimits.limits.email_rate_per_minute,
      email_rate_per_hour: expandedEmailLimits.limits.email_rate_per_hour,
      email_rate_per_day: expandedEmailLimits.limits.email_rate_per_day,
    };
    emailModalOpen = true;
  }

  async function saveEmailLimits() {
    if (!expandedId) return;
    emailSaving = true;
    try {
      const res = await quotasApi.updateCustomerEmailLimits(expandedId, emailForm);
      expandedEmailLimits = {
        ...(expandedEmailLimits as CustomerEmailLimits),
        limits: res.limits,
      };
      toasts.success('Límites de correo actualizados');
      emailModalOpen = false;
    } catch (e: any) {
      toasts.error(e.message ?? 'No se pudo actualizar límites de correo');
    } finally {
      emailSaving = false;
    }
  }

  function usagePercent(used: number, limit: number, unlimited: boolean): number {
    if (unlimited || limit <= 0) return 0;
    return Math.min(100, Math.round((used / limit) * 100));
  }

  function barColor(pct: number, exceeded: boolean): string {
    if (exceeded) return 'bg-red-500';
    if (pct >= 90) return 'bg-amber-500';
    if (pct >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  }

  function countExceeded(resources: Record<string, { exceeded: boolean }>): number {
    return Object.values(resources).filter(r => r.exceeded).length;
  }

  $: filtered = customers.filter(c =>
    !search ||
    c.company_name?.toLowerCase().includes(search.toLowerCase()) ||
    c.subdomain?.toLowerCase().includes(search.toLowerCase()) ||
    c.plan_name?.toLowerCase().includes(search.toLowerCase())
  );

  onMount(loadAll);
</script>

<div class="p-6">
  <!-- Header -->
  <div class="flex items-center justify-between mb-6">
    <div>
      <h1 class="page-title flex items-center gap-2"><Gauge size={22} /> Quotas de Recursos</h1>
      <p class="page-subtitle mt-1">Uso de recursos por cliente vs. los límites de su plan</p>
    </div>
    <div class="flex items-center gap-2">
      <span class="text-sm text-gray-500">{total} cliente{total !== 1 ? 's' : ''}</span>
      <a class="btn-ghost btn-sm" href="/postal-email"><Mail size={14} /> Correo</a>
      <button class="btn-ghost btn-sm" onclick={loadAll}><RefreshCw size={14} /> Recargar</button>
    </div>
  </div>

  <!-- Search -->
  <div class="relative max-w-md mb-4">
    <Search size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
    <input type="text" bind:value={search} placeholder="Buscar cliente, subdominio o plan…" class="input-field pl-9 w-full" />
  </div>

  {#if loading}
    <div class="flex justify-center py-12"><div class="spinner"></div></div>
  {:else if filtered.length === 0}
    <div class="empty-state">
      <Gauge size={40} class="text-gray-600 mb-2" />
      <p class="text-gray-400">No hay clientes{search ? ' que coincidan' : ' con quotas'}</p>
    </div>
  {:else}
    <div class="space-y-2">
      {#each filtered as customer}
        {@const exceeded = countExceeded(customer.resources)}
        <div class="card">
          <button type="button" class="w-full flex items-center justify-between p-4 text-left hover:bg-white/[0.02] transition-colors" onclick={() => toggleDetail(customer.customer_id)}>
            <div class="flex items-center gap-4 min-w-0">
              <div class="w-10 h-10 rounded-lg bg-dark-subtle flex items-center justify-center shrink-0">
                {#if exceeded > 0}
                  <AlertTriangle size={18} class="text-red-400" />
                {:else}
                  <CheckCircle size={18} class="text-green-400" />
                {/if}
              </div>
              <div class="min-w-0">
                <div class="font-medium text-sm">{customer.company_name}</div>
                <div class="text-xs text-gray-500">{customer.subdomain} · {customer.plan_name}</div>
              </div>
            </div>
            <div class="flex items-center gap-3">
              {#if exceeded > 0}
                <span class="badge badge-error text-xs">{exceeded} excedido{exceeded > 1 ? 's' : ''}</span>
              {:else}
                <span class="badge badge-success text-xs">OK</span>
              {/if}
              <!-- Mini bars preview -->
              <div class="hidden md:flex items-center gap-1">
                {#each Object.entries(customer.resources) as [key, res]}
                  {@const pct = usagePercent(res.used, res.limit, res.unlimited)}
                  <div class="w-8 h-2 rounded-full bg-dark-subtle overflow-hidden" title="{RESOURCE_LABELS[key] ?? key}: {res.used}/{res.unlimited ? '∞' : res.limit}">
                    <div class="h-full rounded-full {barColor(pct, res.exceeded)}" style="width: {res.unlimited ? 0 : pct}%"></div>
                  </div>
                {/each}
              </div>
              {#if expandedId === customer.customer_id}
                <ChevronDown size={16} class="text-gray-500" />
              {:else}
                <ChevronRight size={16} class="text-gray-500" />
              {/if}
            </div>
          </button>

          {#if expandedId === customer.customer_id}
            <div class="border-t border-border-dark px-4 py-4">
              {#if loadingDetail}
                <div class="flex justify-center py-4"><div class="spinner"></div></div>
              {:else if expandedQuotas}
                {#if expandedEmailLimits}
                  <div class="mb-4 rounded-lg border border-border-dark bg-dark-subtle p-4">
                    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                      <div>
                        <div class="text-xs uppercase tracking-wide text-gray-500">Límites de correo</div>
                        <div class="text-sm text-text-primary mt-1">
                          Mes: <b>{expandedEmailLimits.limits.max_emails_monthly.toLocaleString()}</b> ·
                          Min: <b>{expandedEmailLimits.limits.email_rate_per_minute.toLocaleString()}</b> ·
                          Hora: <b>{expandedEmailLimits.limits.email_rate_per_hour.toLocaleString()}</b> ·
                          Día: <b>{expandedEmailLimits.limits.email_rate_per_day.toLocaleString()}</b>
                        </div>
                        <div class="text-xs text-gray-500 mt-1">Fuente: {expandedEmailLimits.source === 'addon' ? 'Perfil add-on' : 'Plan/partner'}</div>
                      </div>
                      <button class="btn-sm btn-secondary" onclick={openEmailModal}>
                        <Pencil size={12} /> Editar límites
                      </button>
                    </div>
                  </div>
                {/if}

                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  {#each Object.entries(expandedQuotas.quotas) as [key, quota]}
                    {@const pct = usagePercent(quota.used, quota.limit, quota.unlimited)}
                    {@const IconComp = RESOURCE_ICONS[key] ?? Gauge}
                    <div class="bg-dark-subtle rounded-lg p-4">
                      <div class="flex items-center gap-2 mb-2">
                        <IconComp size={14} class="text-gray-400" />
                        <span class="text-xs uppercase tracking-wider text-gray-500">{RESOURCE_LABELS[key] ?? key}</span>
                      </div>
                      <div class="flex items-end justify-between mb-2">
                        <span class="text-2xl font-bold tabular-nums">{quota.used.toLocaleString()}</span>
                        <span class="text-sm text-gray-500">/ {quota.unlimited ? '∞' : quota.limit.toLocaleString()}</span>
                      </div>
                      {#if !quota.unlimited}
                        <div class="w-full h-2 rounded-full bg-black/30 overflow-hidden">
                          <div class="h-full rounded-full transition-all {barColor(pct, quota.exceeded)}" style="width: {pct}%"></div>
                        </div>
                        <div class="flex items-center justify-between mt-1">
                          <span class="text-xs text-gray-500">{pct}%</span>
                          {#if quota.exceeded}
                            <span class="text-xs text-red-400 font-semibold">Excedido</span>
                          {:else if quota.available !== null}
                            <span class="text-xs text-gray-500">{quota.available} disponible{quota.available !== 1 ? 's' : ''}</span>
                          {/if}
                        </div>
                      {:else}
                        <div class="text-xs text-gray-500 mt-1">Sin límite (ilimitado)</div>
                      {/if}
                    </div>
                  {/each}
                </div>
              {:else}
                <p class="text-sm text-gray-500">No se pudo cargar el detalle</p>
              {/if}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

{#if emailModalOpen}
  <div class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" role="dialog">
    <div class="bg-charcoal rounded-xl border border-border-dark w-full max-w-xl">
      <div class="flex items-center justify-between p-5 border-b border-border-dark">
        <h3 class="text-lg font-semibold text-text-light">Editar límites de correo por tenant</h3>
        <button class="text-gray-400 hover:text-text-light" onclick={() => (emailModalOpen = false)}>×</button>
      </div>
      <form class="p-5 grid grid-cols-1 sm:grid-cols-2 gap-4" onsubmit={(e) => { e.preventDefault(); saveEmailLimits(); }}>
        <div>
          <label class="label" for="email-max-monthly">Máximo mensual</label>
          <input id="email-max-monthly" class="input w-full" type="number" min="0" bind:value={emailForm.max_emails_monthly} />
        </div>
        <div>
          <label class="label" for="email-rate-minute">Rate por minuto</label>
          <input id="email-rate-minute" class="input w-full" type="number" min="0" bind:value={emailForm.email_rate_per_minute} />
        </div>
        <div>
          <label class="label" for="email-rate-hour">Rate por hora</label>
          <input id="email-rate-hour" class="input w-full" type="number" min="0" bind:value={emailForm.email_rate_per_hour} />
        </div>
        <div>
          <label class="label" for="email-rate-day">Rate por día</label>
          <input id="email-rate-day" class="input w-full" type="number" min="0" bind:value={emailForm.email_rate_per_day} />
        </div>
        <div class="sm:col-span-2 flex justify-end gap-2 pt-2">
          <button type="button" class="btn-secondary" onclick={() => (emailModalOpen = false)}>Cancelar</button>
          <button type="submit" class="btn-accent" disabled={emailSaving}>{emailSaving ? 'Guardando...' : 'Guardar'}</button>
        </div>
      </form>
    </div>
  </div>
{/if}
