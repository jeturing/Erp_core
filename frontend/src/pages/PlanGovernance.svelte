<script lang="ts">
  import { onMount } from 'svelte';
  import { planGovernanceApi, type GovernanceCustomerSummary, type GovernancePlan } from '../lib/api/planGovernance';
  import { toasts } from '../lib/stores';
  import { ShieldCheck, RefreshCw, TriangleAlert, CheckCircle2, Search, Package, HardDrive, Users, Pencil, Save } from 'lucide-svelte';

  let loading = $state(true);
  let newOnly = $state(true);
  let search = $state('');
  let plans = $state<GovernancePlan[]>([]);
  let customers = $state<GovernanceCustomerSummary[]>([]);
  let planEditOpen = $state(false);
  let savingPlan = $state(false);
  let togglingCustomerId = $state<number | null>(null);
  let editingPlanId = $state<number | null>(null);
  let planDraft = $state({
    max_users: 0,
    max_storage_mb: 0,
    max_stock_sku: 0,
    max_emails_monthly: 0,
    email_rate_per_minute: 0,
    email_rate_per_hour: 0,
    email_rate_per_day: 0,
    quota_warning_percent: 80,
    quota_recommend_percent: 95,
    quota_block_percent: 100,
    fair_use_new_customers_only: true,
  });
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

  function openPlanEditor(plan: GovernancePlan) {
    editingPlanId = plan.id;
    planDraft = {
      max_users: plan.max_users,
      max_storage_mb: plan.max_storage_mb,
      max_stock_sku: plan.max_stock_sku,
      max_emails_monthly: plan.max_emails_monthly,
      email_rate_per_minute: plan.email_rate_per_minute,
      email_rate_per_hour: plan.email_rate_per_hour,
      email_rate_per_day: plan.email_rate_per_day,
      quota_warning_percent: plan.quota_warning_percent,
      quota_recommend_percent: plan.quota_recommend_percent,
      quota_block_percent: plan.quota_block_percent,
      fair_use_new_customers_only: plan.fair_use_new_customers_only,
    };
    planEditOpen = true;
  }

  async function savePlanGovernance() {
    if (!editingPlanId) return;
    savingPlan = true;
    try {
      await planGovernanceApi.updatePlanGovernance(editingPlanId, planDraft as any);
      toasts.success('Gobernanza del plan actualizada');
      planEditOpen = false;
      await loadData();
    } catch (e: any) {
      toasts.error(e.message || 'No se pudo guardar la gobernanza del plan');
    } finally {
      savingPlan = false;
    }
  }

  async function toggleFairUse(item: GovernanceCustomerSummary) {
    togglingCustomerId = item.customer_id;
    try {
      const next = !item.fair_use_enabled;
      await planGovernanceApi.setCustomerFairUse(item.customer_id, next);
      item.fair_use_enabled = next;
      customers = [...customers];
      toasts.success(`Fair use ${next ? 'activado' : 'desactivado'} para ${item.company_name}`);
    } catch (e: any) {
      toasts.error(e.message || 'No se pudo actualizar fair use');
    } finally {
      togglingCustomerId = null;
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
          <div class="flex justify-between"><span class="flex items-center gap-1">📧 Email/mes</span><span class="text-text-light">{formatLimit(plan.max_emails_monthly)}</span></div>
          <div class="flex justify-between"><span class="flex items-center gap-1">⏱ Min/Hora/Día</span><span class="text-text-light">{plan.email_rate_per_minute}/{plan.email_rate_per_hour}/{plan.email_rate_per_day}</span></div>
          <div class="text-xs text-gray-500 pt-2">Solo clientes nuevos: <span class="text-text-light">{plan.fair_use_new_customers_only ? 'Sí' : 'No'}</span></div>
          <button class="btn-sm btn-secondary mt-2" onclick={() => openPlanEditor(plan)}>
            <Pencil size={12} /> Editar límites
          </button>
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
              <th>Acciones</th>
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
                <td>
                  <button
                    class="btn-sm btn-secondary"
                    disabled={togglingCustomerId === item.customer_id}
                    onclick={() => toggleFairUse(item)}
                  >
                    {togglingCustomerId === item.customer_id ? '...' : (item.fair_use_enabled ? 'Desactivar fair use' : 'Activar fair use')}
                  </button>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</div>

{#if planEditOpen}
  <div class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" role="dialog">
    <div class="bg-charcoal rounded-xl border border-border-dark w-full max-w-2xl">
      <div class="flex items-center justify-between p-5 border-b border-border-dark">
        <h3 class="text-lg font-semibold text-text-light">Editar gobernanza del plan</h3>
        <button class="text-gray-400 hover:text-text-light" onclick={() => (planEditOpen = false)}>×</button>
      </div>
      <form class="p-5 grid grid-cols-1 sm:grid-cols-2 gap-4" onsubmit={(e) => { e.preventDefault(); savePlanGovernance(); }}>
        <div><label class="label" for="pg-max-users">Max usuarios</label><input id="pg-max-users" type="number" min="0" class="input w-full" bind:value={planDraft.max_users} /></div>
        <div><label class="label" for="pg-max-storage">Max storage (MB)</label><input id="pg-max-storage" type="number" min="0" class="input w-full" bind:value={planDraft.max_storage_mb} /></div>
        <div><label class="label" for="pg-max-sku">Max SKU</label><input id="pg-max-sku" type="number" min="0" class="input w-full" bind:value={planDraft.max_stock_sku} /></div>
        <div><label class="label" for="pg-max-emails">Max emails/mes</label><input id="pg-max-emails" type="number" min="0" class="input w-full" bind:value={planDraft.max_emails_monthly} /></div>
        <div><label class="label" for="pg-min">Rate/min</label><input id="pg-min" type="number" min="0" class="input w-full" bind:value={planDraft.email_rate_per_minute} /></div>
        <div><label class="label" for="pg-hour">Rate/hora</label><input id="pg-hour" type="number" min="0" class="input w-full" bind:value={planDraft.email_rate_per_hour} /></div>
        <div><label class="label" for="pg-day">Rate/día</label><input id="pg-day" type="number" min="0" class="input w-full" bind:value={planDraft.email_rate_per_day} /></div>
        <div><label class="label" for="pg-warning">Warning %</label><input id="pg-warning" type="number" min="0" max="100" class="input w-full" bind:value={planDraft.quota_warning_percent} /></div>
        <div><label class="label" for="pg-recommend">Recommend %</label><input id="pg-recommend" type="number" min="0" max="100" class="input w-full" bind:value={planDraft.quota_recommend_percent} /></div>
        <div><label class="label" for="pg-block">Block %</label><input id="pg-block" type="number" min="0" max="100" class="input w-full" bind:value={planDraft.quota_block_percent} /></div>
        <div class="sm:col-span-2">
          <label class="inline-flex items-center gap-2 text-sm text-gray-300">
            <input type="checkbox" bind:checked={planDraft.fair_use_new_customers_only} class="accent-terracotta" />
            Aplicar fair use solo a clientes nuevos
          </label>
        </div>
        <div class="sm:col-span-2 flex justify-end gap-2 pt-2">
          <button type="button" class="btn-secondary" onclick={() => (planEditOpen = false)}>Cancelar</button>
          <button type="submit" class="btn-accent" disabled={savingPlan}><Save size={12} /> {savingPlan ? 'Guardando...' : 'Guardar'}</button>
        </div>
      </form>
    </div>
  </div>
{/if}
