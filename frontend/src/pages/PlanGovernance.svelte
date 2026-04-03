<script lang="ts">
  import { onMount } from 'svelte';
  import { planGovernanceApi, type GovernanceCustomerSummary, type GovernancePlan } from '../lib/api/planGovernance';
  import { toasts } from '../lib/stores';
  import { ShieldCheck, RefreshCw, TriangleAlert, CheckCircle2, Search, Package, HardDrive, Users } from 'lucide-svelte';

  let loading = $state(true);
  let newOnly = $state(true);
  let search = $state('');
  let plans = $state<GovernancePlan[]>([]);
  let customers = $state<GovernanceCustomerSummary[]>([]);
  const filtered = $derived(customers.filter((item) => {
    const needle = search.toLowerCase();
    if (!needle) return true;
    return [item.company_name, item.subdomain, item.plan_name, item.top_resource_label]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(needle));
  }));

  async function loadData() {
    loading = true;
    try {
      const res = await planGovernanceApi.getSummary(newOnly);
      plans = res.plans ?? [];
      customers = res.customers ?? [];
    } catch (e: any) {
      toasts.error(e.message || 'Error cargando gobernanza de planes');
    } finally {
      loading = false;
    }
  }

  function badgeClass(status: string) {
    if (status === 'exceeded') return 'badge-error';
    if (status === 'critical') return 'badge-warning';
    if (status === 'warning') return 'badge-neutral';
    return 'badge-success';
  }

  function formatLimit(value: number, unit = '') {
    if (value === 0) return '∞';
    return `${value}${unit}`;
  }

  function formatStorageMb(value: number) {
    if (value === 0) return '∞';
    return `${(value / 1024).toFixed(value >= 1024 ? 1 : 2)} GB`;
  }

  onMount(loadData);
</script>

<div class="p-6 space-y-6">
  <div class="flex items-start justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><ShieldCheck size={22} /> Gobernanza de Planes</h1>
      <p class="page-subtitle">Fair use, límites efectivos y recomendación de upgrade para clientes nuevos.</p>
    </div>
    <button class="btn-secondary flex items-center gap-2" onclick={loadData}>
      <RefreshCw size={14} /> Recargar
    </button>
  </div>

  <div class="card p-4 grid grid-cols-1 lg:grid-cols-3 gap-4">
    {#each plans as plan}
      <div class="bg-dark-subtle rounded-lg p-4 border border-border-dark">
        <div class="flex items-center justify-between mb-3">
          <div>
            <div class="text-sm font-semibold text-text-light">{plan.display_name}</div>
            <div class="text-xs text-gray-500 uppercase">{plan.name}</div>
          </div>
          <span class="badge-neutral text-xs">{plan.quota_warning_percent}/{plan.quota_recommend_percent}/{plan.quota_block_percent}%</span>
        </div>
        <div class="space-y-2 text-sm text-gray-400">
          <div class="flex justify-between"><span class="flex items-center gap-1"><Users size={12} /> Usuarios</span><span class="text-text-light">{formatLimit(plan.max_users)}</span></div>
          <div class="flex justify-between"><span class="flex items-center gap-1"><HardDrive size={12} /> Storage</span><span class="text-text-light">{formatStorageMb(plan.max_storage_mb)}</span></div>
          <div class="flex justify-between"><span class="flex items-center gap-1"><Package size={12} /> SKU</span><span class="text-text-light">{formatLimit(plan.max_stock_sku)}</span></div>
          <div class="text-xs text-gray-500 pt-2">Solo clientes nuevos: <span class="text-text-light">{plan.fair_use_new_customers_only ? 'Sí' : 'No'}</span></div>
        </div>
      </div>
    {/each}
  </div>

  <div class="flex flex-col md:flex-row gap-3">
    <div class="relative flex-1">
      <Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
      <input class="input pl-10 w-full" bind:value={search} placeholder="Buscar cliente, subdominio, plan o cuota..." />
    </div>
    <label class="flex items-center gap-2 text-sm cursor-pointer px-3">
      <input type="checkbox" bind:checked={newOnly} class="accent-terracotta" onchange={loadData} />
      Solo clientes nuevos
    </label>
  </div>

  <div class="card overflow-hidden">
    {#if loading}
      <div class="p-8 text-center text-gray-400">Cargando gobernanza...</div>
    {:else if filtered.length === 0}
      <div class="p-8 text-center text-gray-400">No hay clientes para mostrar.</div>
    {:else}
      <div class="overflow-x-auto">
        <table class="table w-full text-sm">
          <thead>
            <tr>
              <th>Cliente</th>
              <th>Plan</th>
              <th>Policy</th>
              <th>Cuota líder</th>
              <th>Uso</th>
              <th>Estado</th>
              <th>Recomendación</th>
            </tr>
          </thead>
          <tbody>
            {#each filtered as item}
              <tr>
                <td>
                  <div class="font-medium text-text-light">{item.company_name}</div>
                  <div class="text-xs text-gray-500">{item.subdomain}</div>
                </td>
                <td>{item.plan_name}</td>
                <td>
                  <span class={item.fair_use_enabled ? 'badge-success text-xs' : 'badge-neutral text-xs'}>
                    {item.fair_use_enabled ? 'Nuevo' : 'Legacy'}
                  </span>
                </td>
                <td>{item.top_resource_label || '—'}</td>
                <td class="font-mono">{item.top_usage_percent?.toFixed?.(1) ?? item.top_usage_percent}%</td>
                <td>
                  <span class={`${badgeClass(item.top_status)} text-xs flex items-center gap-1 w-fit`}>
                    {#if item.top_status === 'ok'}<CheckCircle2 size={12} />{:else}<TriangleAlert size={12} />{/if}
                    {item.top_status}
                  </span>
                </td>
                <td>
                  {#if item.recommendation}
                    <div class="text-xs text-gray-400">
                      <div class="text-text-light font-medium">{item.recommendation.display_name}</div>
                      <div>por {item.recommendation.resource_label}</div>
                    </div>
                  {:else}
                    <span class="text-xs text-gray-500">Sin cambio</span>
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</div>
