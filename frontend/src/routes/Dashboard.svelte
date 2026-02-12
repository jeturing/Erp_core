<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { dashboard, auth } from '../lib/stores';
  import { Card, StatCard, Badge, Spinner, Button } from '../lib/components';
  import { 
    Users, 
    DollarSign, 
    Server, 
    Activity,
    TrendingUp,
    AlertCircle,
    RefreshCw,
    Building2,
    CreditCard
  } from 'lucide-svelte';
  
  // Load dashboard data on mount
  onMount(async () => {
    await dashboard.load();
    dashboard.startAutoRefresh(60000); // Refresh every minute
  });
  
  onDestroy(() => {
    dashboard.stopAutoRefresh();
  });
  
  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  }
  
  function formatDate(dateString: string): string {
    return new Intl.DateTimeFormat('es-ES', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    }).format(new Date(dateString));
  }
  
  function getPlanBadgeVariant(plan: string): 'basic' | 'pro' | 'enterprise' {
    return plan as 'basic' | 'pro' | 'enterprise';
  }
  
  function getStatusBadgeVariant(status: string): 'success' | 'warning' | 'error' {
    switch (status) {
      case 'active':
      case 'running':
        return 'success';
      case 'pending':
      case 'deploying':
        return 'warning';
      case 'suspended':
      case 'deleted':
      case 'stopped':
        return 'error';
      default:
        return 'warning';
    }
  }
  
  async function handleRefresh() {
    await dashboard.load();
  }
</script>

<div class="p-6 lg:p-8 space-y-6">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold text-white">Dashboard</h1>
      <p class="text-secondary-400 mt-1">
        Bienvenido, {$auth.user?.username || 'Admin'}
      </p>
    </div>
    
    <div class="flex items-center gap-3">
      {#if $dashboard.lastUpdated}
        <span class="text-sm text-secondary-500">
          Actualizado: {$dashboard.lastUpdated.toLocaleTimeString('es-ES')}
        </span>
      {/if}
      <Button 
        variant="secondary" 
        size="sm"
        on:click={handleRefresh}
        disabled={$dashboard.isLoading}
      >
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
          <p class="font-medium">Error al cargar datos</p>
          <p class="text-sm opacity-80">{$dashboard.error}</p>
        </div>
      </div>
      <div class="mt-4">
        <Button variant="secondary" on:click={handleRefresh}>
          Reintentar
        </Button>
      </div>
    </Card>
  {:else if $dashboard.data}
    <!-- Stats Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        value={$dashboard.data.customers?.total || 0}
        label="Total Clientes"
        change={12.5}
        icon={Users}
        iconBg="bg-primary-500/10"
        iconColor="text-primary-400"
      />
      
      <StatCard
        value={formatCurrency($dashboard.data.revenue?.mrr || 0)}
        label="MRR"
        change={8.2}
        icon={DollarSign}
        iconBg="bg-accent-500/10"
        iconColor="text-accent-400"
      />
      
      <StatCard
        value={$dashboard.data.customers?.active || 0}
        label="Clientes Activos"
        change={5.1}
        icon={Activity}
        iconBg="bg-success/10"
        iconColor="text-success"
      />
      
      <StatCard
        value={formatCurrency($dashboard.data.revenue?.arr || 0)}
        label="ARR"
        change={15.3}
        icon={TrendingUp}
        iconBg="bg-info/10"
        iconColor="text-info"
      />
    </div>
    
    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Customers by Plan -->
      <Card title="Clientes por Plan" subtitle="Distribución actual">
        <div class="space-y-4">
          {#each Object.entries($dashboard.data.customers?.by_plan || {}) as [plan, count]}
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class={`w-2 h-2 rounded-full ${
                  plan === 'enterprise' ? 'bg-accent-500' : 
                  plan === 'pro' ? 'bg-primary-500' : 
                  'bg-secondary-500'
                }`}></div>
                <span class="text-secondary-200 capitalize">{plan}</span>
              </div>
              <div class="flex items-center gap-3">
                <span class="text-white font-medium">{count}</span>
                <Badge variant={getPlanBadgeVariant(plan)}>
                  {plan}
                </Badge>
              </div>
            </div>
          {/each}
        </div>
        
        <!-- Plan Progress Bars -->
        <div class="mt-6 space-y-3">
          {#each Object.entries($dashboard.data.customers?.by_plan || {}) as [plan, count]}
            {@const total = Object.values($dashboard.data.customers?.by_plan || {}).reduce((a, b) => a + b, 0)}
            {@const percentage = total > 0 ? (count / total) * 100 : 0}
            <div>
              <div class="flex justify-between text-xs text-secondary-400 mb-1">
                <span class="capitalize">{plan}</span>
                <span>{percentage.toFixed(0)}%</span>
              </div>
              <div class="h-2 bg-surface-highlight rounded-full overflow-hidden">
                <div 
                  class={`h-full rounded-full transition-all duration-500 ${
                    plan === 'enterprise' ? 'bg-accent-500' : 
                    plan === 'pro' ? 'bg-primary-500' : 
                    'bg-secondary-500'
                  }`}
                  style="width: {percentage}%"
                ></div>
              </div>
            </div>
          {/each}
        </div>
      </Card>
      
      <!-- Recent Customers -->
      <Card title="Clientes Recientes" subtitle="Últimos registros" padding="none">
        <div class="overflow-x-auto">
          <table class="table">
            <thead>
              <tr>
                <th>Cliente</th>
                <th>Plan</th>
                <th>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {#each ($dashboard.data.recent_activity?.new_customers || []).slice(0, 5) as customer}
                <tr>
                  <td>
                    <div>
                      <p class="font-medium text-white">{customer.name}</p>
                      <p class="text-xs text-secondary-500">{customer.email}</p>
                    </div>
                  </td>
                  <td>
                    <Badge variant={getPlanBadgeVariant(customer.plan)}>
                      {customer.plan}
                    </Badge>
                  </td>
                  <td class="text-secondary-400">
                    {formatDate(customer.created_at)}
                  </td>
                </tr>
              {:else}
                <tr>
                  <td colspan="3" class="text-center text-secondary-500 py-8">
                    No hay clientes recientes
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
        
        <svelte:fragment slot="footer">
          <a href="#/customers" class="text-sm text-primary-400 hover:text-primary-300">
            Ver todos los clientes →
          </a>
        </svelte:fragment>
      </Card>
      
      <!-- Recent Deployments -->
      <Card title="Deployments Recientes" subtitle="Tenants activos" padding="none">
        <div class="overflow-x-auto">
          <table class="table">
            <thead>
              <tr>
                <th>Subdomain</th>
                <th>Estado</th>
                <th>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {#each ($dashboard.data.recent_activity?.recent_deployments || []).slice(0, 5) as deployment}
                <tr>
                  <td>
                    <div class="flex items-center gap-2">
                      <Server size={14} class="text-secondary-500" />
                      <span class="font-medium text-white">{deployment.subdomain}</span>
                    </div>
                  </td>
                  <td>
                    <Badge variant={getStatusBadgeVariant(deployment.status)} dot>
                      {deployment.status}
                    </Badge>
                  </td>
                  <td class="text-secondary-400">
                    {formatDate(deployment.created_at)}
                  </td>
                </tr>
              {:else}
                <tr>
                  <td colspan="3" class="text-center text-secondary-500 py-8">
                    No hay deployments recientes
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
        
        <svelte:fragment slot="footer">
          <a href="#/infrastructure" class="text-sm text-primary-400 hover:text-primary-300">
            Ver infraestructura →
          </a>
        </svelte:fragment>
      </Card>
    </div>
    
    <!-- Quick Actions -->
    <Card title="Acciones Rápidas">
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <a 
          href="#/customers/new" 
          class="flex flex-col items-center gap-3 p-4 rounded-lg bg-surface-highlight 
                 hover:bg-surface-border transition-colors cursor-pointer"
        >
          <div class="p-3 rounded-lg bg-primary-500/10">
            <Users size={24} class="text-primary-400" />
          </div>
          <span class="text-sm text-secondary-200">Nuevo Cliente</span>
        </a>
        
        <a 
          href="#/infrastructure/provision" 
          class="flex flex-col items-center gap-3 p-4 rounded-lg bg-surface-highlight 
                 hover:bg-surface-border transition-colors cursor-pointer"
        >
          <div class="p-3 rounded-lg bg-accent-500/10">
            <Server size={24} class="text-accent-400" />
          </div>
          <span class="text-sm text-secondary-200">Provisionar Tenant</span>
        </a>
        
        <a 
          href="#/billing" 
          class="flex flex-col items-center gap-3 p-4 rounded-lg bg-surface-highlight 
                 hover:bg-surface-border transition-colors cursor-pointer"
        >
          <div class="p-3 rounded-lg bg-success/10">
            <CreditCard size={24} class="text-success" />
          </div>
          <span class="text-sm text-secondary-200">Gestionar Pagos</span>
        </a>
        
        <a 
          href="#/reports" 
          class="flex flex-col items-center gap-3 p-4 rounded-lg bg-surface-highlight 
                 hover:bg-surface-border transition-colors cursor-pointer"
        >
          <div class="p-3 rounded-lg bg-info/10">
            <Building2 size={24} class="text-info" />
          </div>
          <span class="text-sm text-secondary-200">Ver Reportes</span>
        </a>
      </div>
    </Card>
  {/if}
</div>
