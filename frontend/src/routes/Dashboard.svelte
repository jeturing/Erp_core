<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { dashboard, auth } from '../lib/stores';
  import { tenantsApi } from '../lib/api';
  import { formatCurrency, formatDate, formatPercent } from '../lib/utils/formatters';
  import { RefreshCw, CircleAlert, CircleCheck, TriangleAlert, CircleX } from 'lucide-svelte';
  import type { Tenant } from '../lib/types';

  let recentTenants: Tenant[] = [];
  let tenantsError = '';

  async function loadTenants() {
    try {
      const r = await tenantsApi.list();
      recentTenants = [...r.items].sort((a, b) => {
        return (b.created_at ? new Date(b.created_at).getTime() : 0) -
               (a.created_at ? new Date(a.created_at).getTime() : 0);
      }).slice(0, 5);
      tenantsError = '';
    } catch (e) {
      tenantsError = e instanceof Error ? e.message : 'Error cargando tenants';
    }
  }

  async function handleRefresh() {
    await Promise.all([dashboard.load(), loadTenants()]);
  }

  onMount(async () => {
    await dashboard.load();
    await loadTenants();
    dashboard.startAutoRefresh(60000);
  });
  onDestroy(() => dashboard.stopAutoRefresh());

  function statusBadge(status: string) {
    if (status === 'active') return 'badge-success';
    if (status === 'provisioning' || status === 'pending') return 'badge-warning';
    if (status === 'suspended' || status === 'payment_failed') return 'badge-error';
    return 'badge-neutral';
  }

  // System status mocks (in real app would come from /api/logs/status)
  const systemItems = [
    { label: 'API FastAPI',       key: 'api' },
    { label: 'Base de Datos',     key: 'db' },
    { label: 'Servicio de Túnel', key: 'tunnel' },
    { label: 'CDN / Storage',     key: 'cdn' },
  ];
</script>

<div class="p-10 space-y-8">
  <!-- Header -->
  <div class="flex items-start justify-between">
    <div>
      <h1 class="page-title">DASHBOARD</h1>
      <p class="page-subtitle">
        Bienvenido, {$auth.user?.username || 'Admin'} · Informe al {new Date().toLocaleDateString('es-ES', { day: '2-digit', month: 'long', year: 'numeric' })}
      </p>
    </div>
    <div class="flex items-center gap-3">
      <a href="/docs" target="_blank" rel="noreferrer" class="btn-secondary btn-sm">
        Ir a Docs
      </a>
      <button class="btn-accent btn-sm" on:click={handleRefresh} disabled={$dashboard.isLoading}>
        <RefreshCw size={14} class={$dashboard.isLoading ? 'animate-spin' : ''} />
        EXPLORAR
      </button>
    </div>
  </div>

  {#if $dashboard.isLoading && !$dashboard.data}
    <div class="flex items-center justify-center py-20">
      <div class="w-8 h-8 border-2 border-terracotta border-t-transparent rounded-full animate-spin"></div>
    </div>
  {:else if $dashboard.error}
    <div class="card flex items-center gap-3 text-error">
      <CircleAlert size={20} />
      <span class="font-body text-sm">{$dashboard.error}</span>
      <button class="btn-secondary btn-sm ml-auto" on:click={handleRefresh}>Reintentar</button>
    </div>
  {:else if $dashboard.data}
    <!-- Stat cards -->
    <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
      <div class="stat-card">
        <span class="stat-label">Total Tenants</span>
        <span class="stat-value">{($dashboard.data.active_tenants ?? 0) + ($dashboard.data.pending_setup ?? 0)}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Tenants con MRR</span>
        <span class="stat-value">{$dashboard.data.active_tenants ?? 0}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">MRR Estimado</span>
        <span class="stat-value">{formatCurrency($dashboard.data.total_revenue)}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Provisión Pendiente</span>
        <span class="stat-value">{$dashboard.data.pending_setup ?? 0}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Infraestructura Activa</span>
        <span class="stat-value">{formatPercent($dashboard.data.cluster_load?.cpu ?? 0)} CPU</span>
      </div>
    </div>

    <!-- Two-column layout -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Recent activity -->
      <div class="lg:col-span-2 card p-0">
        <div class="flex items-center justify-between px-6 py-4 border-b border-border-light">
          <span class="section-heading">Actividad Reciente</span>
          <a href="#/tenants" class="text-[11px] uppercase tracking-widest text-gray-500 hover:text-terracotta font-sans">
            Ver todos →
          </a>
        </div>
        {#if tenantsError}
          <p class="p-6 text-sm text-error font-body">{tenantsError}</p>
        {:else}
          <div class="divide-y divide-border-light">
            {#each recentTenants as t}
              <div class="flex items-center justify-between px-6 py-3.5">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 bg-charcoal flex items-center justify-center flex-shrink-0">
                    <span class="text-text-light font-sans font-bold text-xs">
                      {(t.company_name || t.subdomain).charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <p class="text-sm font-semibold font-sans text-text-primary">{t.company_name || t.subdomain}</p>
                    <p class="text-xs text-gray-500 font-body">{t.email}</p>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <span class={statusBadge(t.status)}>{t.status}</span>
                  <span class="text-xs text-gray-400 font-body">{formatDate(t.created_at)}</span>
                </div>
              </div>
            {:else}
              <p class="px-6 py-8 text-sm text-gray-400 font-body text-center">Sin actividad reciente</p>
            {/each}
          </div>
        {/if}
      </div>

      <!-- System status -->
      <div class="card p-0">
        <div class="flex items-center justify-between px-6 py-4 border-b border-border-light">
          <span class="section-heading">Estado del Sistema</span>
          <a href="#/logs" class="text-[11px] uppercase tracking-widest text-gray-500 hover:text-terracotta font-sans">
            Ver logs →
          </a>
        </div>
        <div class="divide-y divide-border-light">
          {#each systemItems as item}
            <div class="flex items-center justify-between px-6 py-3.5">
              <span class="text-sm font-body text-text-secondary">{item.label}</span>
              <div class="flex items-center gap-2">
                <CircleCheck size={14} class="text-success" />
                <span class="text-[11px] font-semibold uppercase tracking-widest text-success font-sans">OK</span>
              </div>
            </div>
          {/each}
        </div>

        <!-- Cluster load bars -->
        <div class="px-6 py-4 border-t border-border-light space-y-3">
          <div>
            <div class="flex justify-between mb-1">
              <span class="text-[11px] uppercase tracking-widest text-gray-500 font-sans">CPU</span>
              <span class="text-[11px] font-semibold text-text-primary font-sans">{formatPercent($dashboard.data.cluster_load.cpu)}</span>
            </div>
            <div class="h-1.5 bg-border-light">
              <div class="h-full bg-charcoal" style={`width:${Math.min(100, $dashboard.data.cluster_load.cpu)}%`}></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between mb-1">
              <span class="text-[11px] uppercase tracking-widest text-gray-500 font-sans">RAM</span>
              <span class="text-[11px] font-semibold text-text-primary font-sans">{formatPercent($dashboard.data.cluster_load.ram)}</span>
            </div>
            <div class="h-1.5 bg-border-light">
              <div class="h-full bg-terracotta" style={`width:${Math.min(100, $dashboard.data.cluster_load.ram)}%`}></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick nav -->
    <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
      {#each [
        { href: '#/tenants',        label: 'Tenants' },
        { href: '#/domains',        label: 'Domains' },
        { href: '#/infrastructure', label: 'Infra' },
        { href: '#/billing',        label: 'Billing' },
        { href: '#/logs',           label: 'Logs' },
        { href: '#/settings',       label: 'Settings' },
      ] as link}
        <a href={link.href} class="card p-4 text-center hover:border-terracotta transition-colors">
          <span class="text-[11px] font-semibold uppercase tracking-widest text-text-secondary font-sans">{link.label}</span>
        </a>
      {/each}
    </div>
  {/if}
</div>
