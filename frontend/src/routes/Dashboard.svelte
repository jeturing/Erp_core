<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { dashboard, auth } from '../lib/stores';
  import { Card, StatCard, Badge, Spinner, Button } from '../lib/components';
  import { RefreshCw, AlertCircle, Cpu, DollarSign, Users, Clock3 } from 'lucide-svelte';
  import { tenantsApi } from '../lib/api';
  import type { Tenant } from '../lib/types';
  import { formatCurrency, formatDate, formatPercent } from '../lib/utils/formatters';

  let recentTenants: Tenant[] = [];
  let tenantsError = '';

  async function loadTenants() {
    try {
      const response = await tenantsApi.list();
      recentTenants = [...response.items]
        .sort((a, b) => {
          const aDate = a.created_at ? new Date(a.created_at).getTime() : 0;
          const bDate = b.created_at ? new Date(b.created_at).getTime() : 0;
          return bDate - aDate;
        })
        .slice(0, 8);
      tenantsError = '';
    } catch (error) {
      tenantsError = error instanceof Error ? error.message : 'No se pudo cargar tenants';
    }
  }

  onMount(async () => {
    await dashboard.load();
    await loadTenants();
    dashboard.startAutoRefresh(60000);
  });

  onDestroy(() => {
    dashboard.stopAutoRefresh();
  });

  function statusVariant(status: string) {
    if (status === 'active') return 'success';
    if (status === 'pending' || status === 'provisioning') return 'warning';
    if (status === 'payment_failed' || status === 'suspended') return 'error';
    return 'secondary';
  }

  async function handleRefresh() {
    await Promise.all([dashboard.load(), loadTenants()]);
  }
</script>

<div class="p-6 lg:p-8 space-y-6">
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold text-white">Dashboard</h1>
      <p class="text-secondary-400 mt-1">Bienvenido, {$auth.user?.username || 'Admin'}</p>
    </div>

    <div class="flex items-center gap-3">
      {#if $dashboard.lastUpdated}
        <span class="text-sm text-secondary-500">Actualizado: {$dashboard.lastUpdated.toLocaleTimeString('es-ES')}</span>
      {/if}
      <Button variant="secondary" size="sm" on:click={handleRefresh} disabled={$dashboard.isLoading}>
        <RefreshCw size={16} class={$dashboard.isLoading ? 'animate-spin' : ''} />
        Actualizar
      </Button>
    </div>
  </div>

  {#if $dashboard.isLoading && !$dashboard.data}
    <div class="flex items-center justify-center py-20">
      <Spinner size="lg" />
    </div>
  {:else if $dashboard.error}
    <Card>
      <div class="flex items-center gap-4 text-error">
        <AlertCircle size={24} />
        <div>
          <p class="font-medium">Error al cargar metricas</p>
          <p class="text-sm opacity-80">{$dashboard.error}</p>
        </div>
      </div>
      <div class="mt-4">
        <Button variant="secondary" on:click={handleRefresh}>Reintentar</Button>
      </div>
    </Card>
  {:else if $dashboard.data}
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        value={formatCurrency($dashboard.data.total_revenue)}
        label="MRR Estimado"
        icon={DollarSign}
        iconBg="bg-accent-500/10"
        iconColor="text-accent-400"
      />

      <StatCard
        value={$dashboard.data.active_tenants}
        label="Tenants Activos"
        icon={Users}
        iconBg="bg-primary-500/10"
        iconColor="text-primary-300"
      />

      <StatCard
        value={$dashboard.data.pending_setup}
        label="Provision Pendiente"
        icon={Clock3}
        iconBg="bg-warning/10"
        iconColor="text-warning"
      />

      <StatCard
        value={`${formatPercent($dashboard.data.cluster_load.cpu)} / ${formatPercent($dashboard.data.cluster_load.ram)}`}
        label="Carga CPU/RAM"
        icon={Cpu}
        iconBg="bg-info/10"
        iconColor="text-info"
      />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <Card title="Carga del Cluster" subtitle="Uso reportado por backend">
        <div class="space-y-4">
          <div>
            <div class="flex justify-between text-sm text-secondary-300 mb-1">
              <span>CPU</span>
              <span>{formatPercent(Math.max(0, Math.round($dashboard.data.cluster_load.cpu)))}</span>
            </div>
            <div class="h-2 bg-surface-highlight rounded-full overflow-hidden">
              <div class="h-full bg-primary-500 rounded-full" style={`width: ${Math.min(100, $dashboard.data.cluster_load.cpu)}%`}></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-sm text-secondary-300 mb-1">
              <span>RAM</span>
              <span>{formatPercent(Math.max(0, Math.round($dashboard.data.cluster_load.ram)))}</span>
            </div>
            <div class="h-2 bg-surface-highlight rounded-full overflow-hidden">
              <div class="h-full bg-accent-500 rounded-full" style={`width: ${Math.min(100, $dashboard.data.cluster_load.ram)}%`}></div>
            </div>
          </div>
        </div>
      </Card>

      <Card title="Sistema" subtitle="Monitoreo y administracion">
        <div class="space-y-3">
          <a href="#/logs" class="block p-3 rounded-lg bg-surface-highlight hover:bg-surface-border transition-colors text-secondary-200">
            Ver logs del sistema
          </a>
          <a href="#/tunnels" class="block p-3 rounded-lg bg-surface-highlight hover:bg-surface-border transition-colors text-secondary-200">
            Gestionar tunnels Cloudflare
          </a>
          <a href="#/roles" class="block p-3 rounded-lg bg-surface-highlight hover:bg-surface-border transition-colors text-secondary-200">
            Configurar roles y permisos
          </a>
          <a href="#/infrastructure" class="block p-3 rounded-lg bg-surface-highlight hover:bg-surface-border transition-colors text-secondary-200">
            Ver estado de infraestructura
          </a>
        </div>
      </Card>

      <Card title="Navegacion Core" subtitle="Atajos de administracion">
        <div class="grid grid-cols-2 gap-3 text-sm">
          <a href="#/tenants" class="p-3 rounded-lg bg-surface-highlight hover:bg-surface-border transition-colors text-center">Tenants</a>
          <a href="#/domains" class="p-3 rounded-lg bg-surface-highlight hover:bg-surface-border transition-colors text-center">Domains</a>
          <a href="#/billing" class="p-3 rounded-lg bg-surface-highlight hover:bg-surface-border transition-colors text-center">Billing</a>
          <a href="#/settings" class="p-3 rounded-lg bg-surface-highlight hover:bg-surface-border transition-colors text-center">Settings</a>
        </div>
      </Card>
    </div>

    <Card title="Tenants Recientes" subtitle="Fuente: /api/tenants" padding="none">
      {#if tenantsError}
        <div class="p-6 text-error text-sm">{tenantsError}</div>
      {:else}
        <div class="overflow-x-auto">
          <table class="table">
            <thead>
              <tr>
                <th>Tenant</th>
                <th>Plan</th>
                <th>Estado</th>
                <th>Creado</th>
              </tr>
            </thead>
            <tbody>
              {#each recentTenants as tenant}
                <tr>
                  <td>
                    <div>
                      <p class="font-medium text-white">{tenant.company_name || tenant.subdomain}</p>
                      <p class="text-xs text-secondary-500">{tenant.email}</p>
                    </div>
                  </td>
                  <td>
                    <Badge variant={tenant.plan === 'enterprise' ? 'enterprise' : tenant.plan === 'pro' ? 'pro' : 'basic'}>
                      {tenant.plan || 'basic'}
                    </Badge>
                  </td>
                  <td>
                    <Badge variant={statusVariant(tenant.status)} dot>
                      {tenant.status}
                    </Badge>
                  </td>
                  <td class="text-secondary-400">{formatDate(tenant.created_at)}</td>
                </tr>
              {:else}
                <tr>
                  <td colspan="4" class="text-center text-secondary-500 py-8">No hay tenants para mostrar</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </Card>
  {/if}
</div>
