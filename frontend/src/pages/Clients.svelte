<script lang="ts">
  import { onMount } from 'svelte';
  import { Users, DollarSign, Shield, Edit3, Minus, Plus, RefreshCw, Search, UserCheck, UserX } from 'lucide-svelte';
  import { billingApi } from '../lib/api/billing';
  import type { CustomerItem, Plan } from '../lib/types';

  let customers: CustomerItem[] = $state([]);
  let plans: Plan[] = $state([]);
  let loading = $state(true);
  let error = $state('');
  let searchQuery = $state('');
  let recalculating = $state(false);

  // Summary
  let summary = $state({ total_users: 0, total_mrr: 0, admin_accounts: 0, billable_accounts: 0 });

  // Edit modal
  let showEdit = $state(false);
  let editCustomer: CustomerItem | null = $state(null);
  let editForm = $state({ user_count: 1, plan_name: '', is_admin_account: false, company_name: '', stripe_customer_id: '' });
  let saving = $state(false);

  let filtered = $derived(
    searchQuery.trim()
      ? customers.filter(c =>
          c.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          c.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          c.subdomain?.toLowerCase().includes(searchQuery.toLowerCase())
        )
      : customers
  );

  async function loadData() {
    loading = true;
    error = '';
    try {
      const [custData, planData] = await Promise.all([
        billingApi.getCustomers(),
        billingApi.getPlans(),
      ]);
      customers = custData.items;
      summary = custData.summary;
      plans = planData.items;
    } catch (e: any) {
      error = e.message || 'Error cargando datos';
    } finally {
      loading = false;
    }
  }

  function openEdit(customer: CustomerItem) {
    editCustomer = customer;
    editForm = {
      user_count: customer.user_count,
      plan_name: customer.subscription?.plan_name || '',
      is_admin_account: customer.is_admin_account,
      company_name: customer.company_name,
      stripe_customer_id: customer.stripe_customer_id || '',
    };
    showEdit = true;
  }

  async function saveCustomer() {
    if (!editCustomer) return;
    saving = true;
    try {
      await billingApi.updateCustomer(editCustomer.id, editForm);
      showEdit = false;
      await loadData();
    } catch (e: any) {
      alert(e.message || 'Error actualizando');
    } finally {
      saving = false;
    }
  }

  async function changeUserCount(customer: CustomerItem, delta: number) {
    const newCount = Math.max(1, customer.user_count + delta);
    try {
      const result = await billingApi.updateUserCount(customer.id, newCount);
      // Actualizar localmente
      const idx = customers.findIndex(c => c.id === customer.id);
      if (idx >= 0) {
        customers[idx] = {
          ...customers[idx],
          user_count: result.new_user_count,
          subscription: customers[idx].subscription ? {
            ...customers[idx].subscription!,
            calculated_amount: result.new_monthly ?? customers[idx].subscription!.calculated_amount,
            monthly_amount: result.new_monthly ?? customers[idx].subscription!.monthly_amount,
          } : null,
        };
        // Recargar summary
        summary.total_users += delta;
        if (result.difference) {
          summary.total_mrr = Math.round((summary.total_mrr + result.difference) * 100) / 100;
        }
      }
    } catch (e: any) {
      alert(e.message || 'Error actualizando usuarios');
    }
  }

  async function recalculateAll() {
    if (!confirm('¿Recalcular montos de todas las suscripciones?')) return;
    recalculating = true;
    try {
      const result = await billingApi.recalculateAll();
      alert(result.message);
      await loadData();
    } catch (e: any) {
      alert(e.message || 'Error recalculando');
    } finally {
      recalculating = false;
    }
  }

  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
  }

  function badgeClass(name: string): string {
    const map: Record<string, string> = { basic: 'badge-basic', pro: 'badge-pro', enterprise: 'badge-enterprise' };
    return map[name] || 'badge-neutral';
  }

  onMount(loadData);
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between flex-wrap gap-4">
    <div>
      <h1 class="page-title">Gestión de Clientes</h1>
      <p class="page-subtitle">Administra clientes, usuarios y montos de facturación</p>
    </div>
    <button class="btn-secondary flex items-center gap-2" onclick={recalculateAll} disabled={recalculating}>
      <RefreshCw size={16} class={recalculating ? 'animate-spin' : ''} />
      {recalculating ? 'Recalculando...' : 'Recalcular Todo'}
    </button>
  </div>

  <!-- Summary Cards -->
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
    <div class="stat-card">
      <div class="stat-label">MRR Total</div>
      <div class="stat-value text-terracotta">{formatCurrency(summary.total_mrr)}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Cuentas Facturables</div>
      <div class="stat-value">{summary.billable_accounts}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Total Usuarios</div>
      <div class="stat-value">{summary.total_users}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Cuentas Admin</div>
      <div class="stat-value text-yellow-400">{summary.admin_accounts}</div>
    </div>
  </div>

  {#if error}
    <div class="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">{error}</div>
  {/if}

  <!-- Search -->
  <div class="relative">
    <Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
    <input
      type="text"
      class="input pl-10"
      placeholder="Buscar por empresa, email o subdominio..."
      bind:value={searchQuery}
    />
  </div>

  {#if loading}
    <div class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-terracotta border-t-transparent"></div>
    </div>
  {:else}
    <!-- Clients Table -->
    <div class="card overflow-x-auto">
      <table class="table w-full">
        <thead>
          <tr>
            <th>Cliente</th>
            <th>Plan</th>
            <th class="text-center">Usuarios</th>
            <th class="text-right">Monto/Mes</th>
            <th>Estado</th>
            <th class="text-right">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#each filtered as customer (customer.id)}
            {@const sub = customer.subscription}
            {@const isAdmin = customer.is_admin_account}
            <tr class={isAdmin ? 'opacity-60' : ''}>
              <td>
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 {isAdmin ? 'bg-yellow-500/20' : 'bg-terracotta/20'}">
                    {#if isAdmin}
                      <Shield size={14} class="text-yellow-400" />
                    {:else}
                      <Users size={14} class="text-terracotta" />
                    {/if}
                  </div>
                  <div>
                    <div class="font-medium text-text-light text-sm">{customer.company_name}</div>
                    <div class="text-xs text-gray-500">{customer.email}</div>
                    <div class="text-xs text-gray-600">{customer.subdomain}.sajet.us</div>
                  </div>
                </div>
              </td>
              <td>
                {#if sub}
                  <span class={badgeClass(sub.plan_name)}>{sub.plan_name}</span>
                {:else}
                  <span class="badge-neutral">Sin plan</span>
                {/if}
              </td>
              <td class="text-center">
                {#if isAdmin}
                  <span class="text-yellow-400 text-sm">Admin</span>
                {:else}
                  <div class="flex items-center justify-center gap-1">
                    <button
                      class="w-6 h-6 rounded bg-dark-subtle hover:bg-charcoal border border-border-dark flex items-center justify-center text-gray-400 hover:text-text-light transition-colors"
                      onclick={() => changeUserCount(customer, -1)}
                      disabled={customer.user_count <= 1}
                    >
                      <Minus size={12} />
                    </button>
                    <span class="w-8 text-center font-mono font-bold text-text-light">{customer.user_count}</span>
                    <button
                      class="w-6 h-6 rounded bg-dark-subtle hover:bg-charcoal border border-border-dark flex items-center justify-center text-gray-400 hover:text-text-light transition-colors"
                      onclick={() => changeUserCount(customer, 1)}
                    >
                      <Plus size={12} />
                    </button>
                  </div>
                {/if}
              </td>
              <td class="text-right">
                {#if isAdmin}
                  <span class="text-yellow-400 text-sm">Exento</span>
                {:else if sub}
                  <div>
                    <div class="font-bold text-text-light">{formatCurrency(sub.calculated_amount)}</div>
                    {#if sub.monthly_amount !== sub.calculated_amount}
                      <div class="text-xs text-gray-500 line-through">{formatCurrency(sub.monthly_amount)}</div>
                    {/if}
                  </div>
                {:else}
                  <span class="text-gray-500">-</span>
                {/if}
              </td>
              <td>
                {#if sub}
                  <span class="badge-{sub.status === 'active' ? 'success' : sub.status === 'pending' ? 'warning' : 'error'}">{sub.status}</span>
                {:else}
                  <span class="badge-neutral">N/A</span>
                {/if}
              </td>
              <td class="text-right">
                <button class="btn-secondary btn-sm" onclick={() => openEdit(customer)} title="Editar cliente">
                  <Edit3 size={14} />
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>

      {#if filtered.length === 0}
        <div class="text-center py-8 text-gray-500">
          {searchQuery ? 'Sin resultados para la búsqueda' : 'No hay clientes registrados'}
        </div>
      {/if}
    </div>
  {/if}
</div>

<!-- Edit Modal -->
{#if showEdit && editCustomer}
  <div class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" role="dialog">
    <div class="bg-charcoal rounded-xl border border-border-dark w-full max-w-md">
      <div class="flex items-center justify-between p-6 border-b border-border-dark">
        <h2 class="text-lg font-semibold text-text-light">Editar Cliente</h2>
        <button class="text-gray-400 hover:text-text-light" onclick={() => { showEdit = false; }}>✕</button>
      </div>

      <form class="p-6 space-y-4" onsubmit={(e) => { e.preventDefault(); saveCustomer(); }}>
        <div>
          <label class="label" for="edit-company">Empresa</label>
          <input id="edit-company" class="input" bind:value={editForm.company_name} />
        </div>

        <div>
          <label class="label" for="edit-email">Email</label>
          <input id="edit-email" class="input" value={editCustomer.email} disabled />
        </div>

        <div>
          <label class="label" for="edit-plan">Plan</label>
          <select id="edit-plan" class="input" bind:value={editForm.plan_name}>
            {#each plans as plan}
              <option value={plan.name}>{plan.display_name} ({formatCurrency(plan.base_price)}/mes)</option>
            {/each}
          </select>
        </div>

        <div>
          <label class="label" for="edit-users">Usuarios</label>
          <div class="flex items-center gap-3">
            <button type="button" class="btn-secondary btn-sm" onclick={() => { editForm.user_count = Math.max(1, editForm.user_count - 1); }}>−</button>
            <input id="edit-users" type="number" min="1" class="input text-center w-20" bind:value={editForm.user_count} />
            <button type="button" class="btn-secondary btn-sm" onclick={() => { editForm.user_count++; }}>+</button>
          </div>
        </div>

        <div>
          <label class="label" for="edit-stripe">Stripe Customer ID</label>
          <input id="edit-stripe" class="input" bind:value={editForm.stripe_customer_id} placeholder="cus_xxx..." />
        </div>

        <div class="flex items-center gap-3">
          <input type="checkbox" id="edit-admin" bind:checked={editForm.is_admin_account} class="w-4 h-4" />
          <label for="edit-admin" class="text-sm text-gray-400">
            Cuenta de administración (exenta de facturación)
          </label>
        </div>

        {#if editForm.is_admin_account}
          <div class="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 text-yellow-400 text-sm flex items-center gap-2">
            <Shield size={16} />
            Esta cuenta no generará cobros. admin@sajet.us
          </div>
        {/if}

        <div class="flex gap-3 pt-2">
          <button type="submit" class="btn-accent flex-1" disabled={saving}>
            {saving ? 'Guardando...' : 'Guardar Cambios'}
          </button>
          <button type="button" class="btn-secondary" onclick={() => { showEdit = false; }}>Cancelar</button>
        </div>
      </form>
    </div>
  </div>
{/if}
