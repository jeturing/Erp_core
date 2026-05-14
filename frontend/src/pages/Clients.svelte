<script lang="ts">
  import { onMount } from 'svelte';
  import { Users, DollarSign, Shield, Edit3, Minus, Plus, RefreshCw, Search, CreditCard, Mail, KeyRound, Phone, Trash2, AlertTriangle, Power, PlayCircle, PauseCircle } from 'lucide-svelte';
  import { billingApi } from '../lib/api/billing';
  import { tenantsApi } from '../lib/api/tenants';
  import { workOrdersApi } from '../lib/api/workOrders';
  import CredentialsModal from '../lib/components/CredentialsModal.svelte';
  import type { CustomerItem, Plan } from '../lib/types';
  import type { BlueprintPackage } from '../lib/types';

  let customers: CustomerItem[] = $state([]);
  let plans: Plan[] = $state([]);
  let partners: Array<{ id: number; company_name: string; status: string; partner_code: string }> = $state([]);
  let loading = $state(true);
  let error = $state('');
  let searchQuery = $state('');
  let filterStatus = $state('all');
  let filterPlan = $state('all');
  let filterType = $state('all');
  let recalculating = $state(false);
  let customerActionLoading = $state<number | null>(null);

  // Summary
  let summary = $state({ total_users: 0, total_mrr: 0, admin_accounts: 0, billable_accounts: 0 });

  // Modal Nuevo Cliente + Blueprint
  let showNewClient = $state(false);
  let ncStep = $state(1);
  let blueprints: BlueprintPackage[] = $state([]);
  let blueprintsLoading = $state(false);
  let selectedBlueprint: BlueprintPackage | null = $state(null);
  let creatingClient = $state(false);
  let ncToast = $state('');
  let ncForm = $state({
    company_name: '',
    email: '',
    phone: '',
    full_name: '',
    subdomain: '',
    plan_name: 'basic',
    user_count: 1,
    partner_id: '',
    description: '',
  });

  // Modal Credenciales
  let showCredentialsModal = $state(false);
  let credentials = $state<{
    admin_login: string;
    admin_password: string;
    subdomain: string;
    company_name: string;
    tenant_url?: string;
  } | null>(null);
  let lastCreatedCustomerId: number | null = $state(null);

  async function openNewClient() {
    ncStep = 1; ncToast = '';
    selectedBlueprint = null;
    ncForm = { company_name: '', email: '', phone: '', full_name: '', subdomain: '', plan_name: 'basic', user_count: 1, partner_id: '', description: '' };
    showNewClient = true;
    if (partners.length === 0) {
      try { partners = (await billingApi.getPartners()).items; } catch { }
    }
    if (blueprints.length === 0) {
      blueprintsLoading = true;
      try { blueprints = await workOrdersApi.getBlueprints(); } catch { }
      blueprintsLoading = false;
    }
  }

  async function createClientWithWO() {
    if (!ncForm.company_name || !ncForm.email || !ncForm.phone || !ncForm.subdomain) {
      ncToast = 'Empresa, email, teléfono y subdominio son obligatorios'; return;
    }
    creatingClient = true; ncToast = '';
    try {
      // 1. Crear cliente via billing
      // Normalizar subdominio (minúsculas)
      const normalizedSubdomain = ncForm.subdomain.toLowerCase().replace(/[^a-z0-9-]/g, '-').replace(/^-|-$/g, '').replace(/-+/g, '-');

      const clientRes = await billingApi.createCustomer({
        company_name: ncForm.company_name,
        email: ncForm.email,
        phone: ncForm.phone,
        full_name: ncForm.full_name,
        subdomain: normalizedSubdomain,
        plan_name: ncForm.plan_name,
        user_count: ncForm.user_count,
        partner_id: ncForm.partner_id ? Number(ncForm.partner_id) : undefined,
      });
      
      const customerId = clientRes.id ?? clientRes.customer?.id;
      
      // Capturar credenciales del response
      if (clientRes.tenant && clientRes.tenant.admin_login && clientRes.tenant.admin_password) {
        credentials = {
          admin_login: clientRes.tenant.admin_login,
          admin_password: clientRes.tenant.admin_password,
          subdomain: ncForm.subdomain,
          company_name: ncForm.company_name,
          tenant_url: clientRes.tenant.url || `https://${ncForm.subdomain}.sajet.us`
        };
        lastCreatedCustomerId = customerId;
        showCredentialsModal = true;
      }
      
      // 2. Crear Work Order si hay blueprint
      if (customerId && selectedBlueprint) {
        await workOrdersApi.create({
          customer_id: customerId,
          blueprint_package_id: selectedBlueprint.id,
          selected_modules: selectedBlueprint.module_list,
          work_type: 'provision',
          description: ncForm.description || `Aprovisionamiento ${ncForm.company_name} — ${selectedBlueprint.name}`,
        });
      }
      
      showNewClient = false;
      await loadData();
    } catch (e: any) {
      ncToast = e.message || 'Error creando cliente';
    }
    creatingClient = false;
  }

  async function handleSendCredentialsEmail() {
    if (!lastCreatedCustomerId) return;
    try {
      await billingApi.sendCredentials(lastCreatedCustomerId);
    } catch (e: any) {
      console.error('Error enviando credenciales:', e);
      throw e;
    }
  }

  // Edit modal
  let showEdit = $state(false);
  let editCustomer: CustomerItem | null = $state(null);
  let editForm = $state({
    user_count: 1,
    plan_name: '',
    is_admin_account: false,
    company_name: '',
    stripe_customer_id: '',
    email: '',
    phone: '',
    stripe_action: '',
    discount_pct: 0,
    discount_reason: '',
    partner_id: -1 as number,
  });
  let saving = $state(false);
  let stripeSearchQuery = $state('');
  let stripeSearchResults = $state<Array<{ id: string; email: string | null; name: string | null; phone: string | null; created: number | null; metadata: Record<string, unknown> }>>([]);
  let stripeSearchLoading = $state(false);
  let statusActionLoading = $state('');

  let showDeleteModal = $state(false);
  let deleteCustomer: CustomerItem | null = $state(null);
  let deleteConfirmName = $state('');
  let deletingTenant = $state(false);

  let filtered = $derived(
    customers.filter(c => {
      // Text search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const match =
          c.company_name?.toLowerCase().includes(q) ||
          c.email?.toLowerCase().includes(q) ||
          c.subdomain?.toLowerCase().includes(q);
        if (!match) return false;
      }
      // Status filter
      if (filterStatus !== 'all') {
        const status = c.subscription?.status ?? 'none';
        if (filterStatus !== status) return false;
      }
      // Plan filter
      if (filterPlan !== 'all') {
        const plan = c.subscription?.plan_name ?? '';
        if (filterPlan !== plan) return false;
      }
      // Type filter (admin vs billable)
      if (filterType === 'admin' && !c.is_admin_account) return false;
      if (filterType === 'billable' && c.is_admin_account) return false;
      return true;
    })
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

  async function openEdit(customer: CustomerItem) {
    const defaultPlan = customer.subscription?.plan_name || plans[0]?.name || 'basic';
    editCustomer = customer;
    editForm = {
      user_count: customer.user_count,
      plan_name: defaultPlan,
      is_admin_account: customer.is_admin_account,
      company_name: customer.company_name,
      email: customer.email,
      phone: customer.phone || '',
      stripe_action: '',
      stripe_customer_id: customer.stripe_customer_id || '',
      discount_pct: customer.subscription?.discount_pct || 0,
      discount_reason: customer.subscription?.discount_reason || '',
      partner_id: customer.partner_id ?? -1,
    };
    stripeSearchQuery = customer.email || customer.company_name || '';
    stripeSearchResults = [];
    showEdit = true;
    if (partners.length === 0) {
      try { partners = (await billingApi.getPartners()).items; } catch { }
    }
  }

  async function saveCustomer() {
    if (!editCustomer) return;
    if (!editForm.phone.trim()) {
      alert('El teléfono es obligatorio');
      return;
    }
    if (!editForm.plan_name?.trim()) {
      alert('Debe seleccionar un plan válido');
      return;
    }
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

  async function handleStatusAction(action: string) {
    if (!editCustomer) return;
    const labels: Record<string, string> = {
      suspend_account: 'suspender la cuenta completamente',
      suspend_billing: 'suspender los cobros',
      reactivate: 'reactivar la cuenta',
    };
    if (!confirm(`¿Seguro que deseas ${labels[action] || action}?`)) return;
    statusActionLoading = action;
    try {
      const reason = prompt('Razón (opcional):') || undefined;
      const res = await billingApi.updateCustomerStatus(editCustomer.id, action, reason);
      alert(res.message);
      await loadData();
      // refresh editCustomer reference
      const updated = customers.find(c => c.id === editCustomer!.id);
      if (updated) editCustomer = updated;
    } catch (e: any) {
      alert(e.message || 'Error ejecutando acción');
    } finally {
      statusActionLoading = '';
    }
  }

  async function handleStripeSearch() {
    if (!stripeSearchQuery.trim()) {
      stripeSearchResults = [];
      return;
    }
    stripeSearchLoading = true;
    try {
      const res = await billingApi.searchStripeCustomers(stripeSearchQuery.trim(), 10);
      stripeSearchResults = res.items || [];
      if (stripeSearchResults.length === 0) {
        alert('No se encontraron cuentas Stripe para esa búsqueda');
      }
    } catch (e: any) {
      alert(e.message || 'Error buscando en Stripe');
    } finally {
      stripeSearchLoading = false;
    }
  }

  async function linkSelectedStripeCustomer(stripeCustomerId: string) {
    if (!editCustomer) return;
    saving = true;
    try {
      await billingApi.linkExistingStripeCustomer(editCustomer.id, stripeCustomerId);
      editForm.stripe_customer_id = stripeCustomerId;
      alert('Cuenta Stripe vinculada exitosamente');
      await loadData();
    } catch (e: any) {
      alert(e.message || 'Error vinculando cuenta Stripe');
    } finally {
      saving = false;
    }
  }

  function openDeleteTenantModal(customer: CustomerItem) {
    deleteCustomer = customer;
    deleteConfirmName = '';
    showDeleteModal = true;
  }

  async function confirmDeleteTenantAndAccount() {
    if (!deleteCustomer) return;
    const expected = deleteCustomer.subdomain.trim().toLowerCase();
    if (deleteConfirmName.trim().toLowerCase() !== expected) {
      alert(`Confirmación inválida. Debe escribir exactamente: ${deleteCustomer.subdomain}`);
      return;
    }
    deletingTenant = true;
    try {
      const res = await tenantsApi.delete(deleteCustomer.subdomain, deleteConfirmName.trim());
      alert(res.message || 'Tenant eliminado correctamente');
      showDeleteModal = false;
      deleteCustomer = null;
      deleteConfirmName = '';
      await loadData();
    } catch (e: any) {
      alert(e.message || 'Error eliminando tenant/cuenta');
    } finally {
      deletingTenant = false;
    }
  }

  async function linkStripeCustomer() {
    if (!editCustomer) return;
    saving = true;
    try {
      await billingApi.updateCustomer(editCustomer.id, {
        ...editForm,
        stripe_action: 'link'
      });
      editCustomer.stripe_customer_id = null; // Forzar recarga
      alert('Stripe Customer vinculado/creado exitosamente');
      await loadData();
      showEdit = false;
    } catch (e: any) {
      alert(e.message || 'Error vinculando Stripe Customer');
    } finally {
      saving = false;
    }
  }

  async function unlinkStripeCustomer() {
    if (!editCustomer) return;
    saving = true;
    try {
      await billingApi.updateCustomer(editCustomer.id, {
        stripe_action: 'unlink'
      });
      editForm.stripe_customer_id = '';
      alert('Stripe Customer desvinculado');
    } catch (e: any) {
      alert(e.message || 'Error desvinculando');
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

  async function createStripeCustomer(customer: CustomerItem) {
    customerActionLoading = customer.id;
    try {
      const result = await billingApi.createStripeCustomer(customer.id);
      alert(result.message || 'Stripe Customer procesado');
      await loadData();
    } catch (e: any) {
      alert(e.message || 'Error creando Stripe Customer');
    } finally {
      customerActionLoading = null;
    }
  }

  async function sendCredentials(customer: CustomerItem) {
    customerActionLoading = customer.id;
    try {
      const result = await billingApi.sendCredentials(customer.id);
      alert(result.message || 'Credenciales enviadas');
    } catch (e: any) {
      alert(e.message || 'Error enviando credenciales');
    } finally {
      customerActionLoading = null;
    }
  }

  async function resetPassword(customer: CustomerItem) {
    if (!confirm(`¿Resetear contraseña de ${customer.company_name}?`)) return;
    customerActionLoading = customer.id;
    try {
      const result = await billingApi.resetPassword(customer.id);
      alert(result.message || 'Contraseña reseteada');
    } catch (e: any) {
      alert(e.message || 'Error reseteando contraseña');
    } finally {
      customerActionLoading = null;
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
    <div class="flex items-center gap-2">
      <button class="btn-accent flex items-center gap-2" onclick={openNewClient}>
        <Plus size={16} /> Nuevo Cliente
      </button>
      <button class="btn-secondary flex items-center gap-2" onclick={recalculateAll} disabled={recalculating}>
        <RefreshCw size={16} class={recalculating ? 'animate-spin' : ''} />
        {recalculating ? 'Recalculando...' : 'Recalcular'}
      </button>
    </div>
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

  <!-- Search + Filters -->
  <div class="space-y-3">
    <div class="relative">
      <Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
      <input
        type="text"
        class="input pl-10"
        placeholder="Buscar por empresa, email o subdominio..."
        bind:value={searchQuery}
      />
    </div>
    <div class="flex flex-wrap gap-3">
      <select class="input px-3 py-2 text-sm" bind:value={filterStatus}>
        <option value="all">Estado: Todos</option>
        <option value="active">✅ Activo</option>
        <option value="pending">⏳ Pendiente</option>
        <option value="suspended">⚠️ Suspendido</option>
        <option value="none">🔹 Sin suscripción</option>
      </select>
      <select class="input px-3 py-2 text-sm" bind:value={filterPlan}>
        <option value="all">Plan: Todos</option>
        {#each plans as pl}
          <option value={pl.name}>{pl.display_name}</option>
        {/each}
      </select>
      <select class="input px-3 py-2 text-sm" bind:value={filterType}>
        <option value="all">Tipo: Todos</option>
        <option value="billable">💳 Facturables</option>
        <option value="admin">🛡️ Admin (Exentos)</option>
      </select>
      {#if filterStatus !== 'all' || filterPlan !== 'all' || filterType !== 'all'}
        <button
          class="btn-secondary btn-sm text-xs"
          onclick={() => { filterStatus = 'all'; filterPlan = 'all'; filterType = 'all'; }}
        >
          ✕ Limpiar filtros
        </button>
      {/if}
    </div>
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
                    {#if customer.phone}
                      <div class="text-xs text-gray-500">{customer.phone}</div>
                    {/if}
                    <div class="text-xs text-gray-600">{customer.subdomain}.sajet.us</div>
                  </div>
                </div>
              </td>
              <td>
                {#if sub}
                  <span class={badgeClass(sub.plan_name)}>{sub.plan_display_name || sub.plan_name}</span>
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
                <div class="flex justify-end gap-2">
                  <button
                    class="btn-secondary btn-sm"
                    onclick={() => createStripeCustomer(customer)}
                    title={customer.stripe_customer_id ? 'Stripe Customer ya existe' : 'Crear Stripe Customer'}
                    disabled={customerActionLoading === customer.id || !!customer.stripe_customer_id || customer.is_admin_account}
                  >
                    <CreditCard size={14} />
                  </button>
                  <button
                    class="btn-secondary btn-sm"
                    onclick={() => sendCredentials(customer)}
                    title="Enviar credenciales"
                    disabled={customerActionLoading === customer.id}
                  >
                    <Mail size={14} />
                  </button>
                  <button
                    class="btn-secondary btn-sm"
                    onclick={() => resetPassword(customer)}
                    title="Reset password"
                    disabled={customerActionLoading === customer.id}
                  >
                    <KeyRound size={14} />
                  </button>
                  <button
                    class="btn-secondary btn-sm"
                    onclick={() => openEdit(customer)}
                    title="Editar cliente"
                    disabled={customerActionLoading === customer.id}
                  >
                    <Edit3 size={14} />
                  </button>
                  <button
                    class="btn-danger btn-sm"
                    onclick={() => openDeleteTenantModal(customer)}
                    title="Eliminar cuenta y tenant"
                    disabled={customerActionLoading === customer.id}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
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
    <div class="bg-charcoal rounded-xl border border-border-dark w-full max-w-2xl">
      <div class="flex items-center justify-between p-6 border-b border-border-dark">
        <h2 class="text-lg font-semibold text-text-light">Editar Cliente</h2>
        <button class="text-gray-400 hover:text-text-light" onclick={() => { showEdit = false; }}>✕</button>
      </div>

      <div class="p-6 space-y-6 overflow-y-auto max-h-[80vh]">
        <!-- Datos principales -->
        <form class="space-y-4" onsubmit={(e) => { e.preventDefault(); saveCustomer(); }}>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label" for="edit-company">Empresa</label>
              <input id="edit-company" class="input" bind:value={editForm.company_name} />
            </div>

            <div>
              <label class="label" for="edit-email">Email</label>
              <input id="edit-email" type="email" class="input" bind:value={editForm.email} />
            </div>
          </div>

          <div>
            <label class="label" for="edit-phone">Teléfono *</label>
            <div class="relative">
              <Phone size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
              <input id="edit-phone" type="tel" class="input pl-9" bind:value={editForm.phone} placeholder="+1 809 555 1234" required />
            </div>
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

          <!-- Partner -->
          <div>
            <label class="label" for="edit-partner">Partner asignado</label>
            <select id="edit-partner" class="input" bind:value={editForm.partner_id}>
              <option value={0}>Sin partner (directo Jeturing)</option>
              {#each partners.filter(p => p.status === 'active') as partner}
                <option value={partner.id}>{partner.company_name} ({partner.partner_code})</option>
              {/each}
            </select>
          </div>

          <!-- Descuento -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label" for="edit-discount-pct">Descuento (%)</label>
              <input id="edit-discount-pct" type="number" min="0" max="100" step="0.1" class="input" bind:value={editForm.discount_pct} placeholder="0" />
            </div>
            <div>
              <label class="label" for="edit-discount-reason">Motivo</label>
              <input id="edit-discount-reason" type="text" class="input" bind:value={editForm.discount_reason} placeholder="Acuerdo comercial..." />
            </div>
          </div>
          {#if editForm.discount_pct > 0}
            <div class="bg-green-500/10 border border-green-500/30 rounded-lg p-3 text-green-400 text-xs">
              💰 Se aplicará un descuento del {editForm.discount_pct}% al monto calculado del plan.
            </div>
          {/if}

          <!-- Admin -->
          <div class="flex items-center gap-3">
            <input type="checkbox" id="edit-admin" bind:checked={editForm.is_admin_account} class="w-4 h-4" />
            <label for="edit-admin" class="text-sm text-gray-400">
              Cuenta de administración (exenta de facturación)
            </label>
          </div>

          {#if editForm.is_admin_account}
            <div class="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 text-yellow-400 text-sm flex items-center gap-2">
              <Shield size={16} />
              Esta cuenta no generará cobros
            </div>
          {/if}

          <button type="submit" class="btn-accent w-full" disabled={saving}>
            {saving ? 'Guardando...' : 'Guardar Cambios'}
          </button>
        </form>

        <!-- Stripe vinculación -->
        <div class="border-t border-border-dark pt-6">
          <h3 class="font-semibold text-text-light mb-4 flex items-center gap-2">
            <CreditCard size={18} />
            Vinculación con Stripe
          </h3>

          <div class="space-y-3">
            <div class="bg-dark-subtle rounded-lg p-4">
              <label class="text-sm text-gray-400 block mb-2">Stripe Customer ID</label>
              <input class="input w-full font-mono text-sm" bind:value={editForm.stripe_customer_id} placeholder="cus_xxx..." />
              {#if editForm.stripe_customer_id}
                <div class="text-xs text-green-400 mt-2 flex items-center gap-1">
                  ✓ Vinculado
                </div>
              {/if}
            </div>

            <div class="flex gap-2">
              <button 
                type="button"
                class="btn-secondary flex-1"
                onclick={linkStripeCustomer}
                disabled={saving}
                title="Buscar cliente en Stripe por email o crear uno nuevo"
              >
                <CreditCard size={14} />
                {editForm.stripe_customer_id ? 'Actualizar' : 'Buscar/Crear'} en Stripe
              </button>
              {#if editForm.stripe_customer_id}
                <button 
                  type="button"
                  class="btn-secondary"
                  onclick={unlinkStripeCustomer}
                  disabled={saving}
                  title="Desvincular de Stripe"
                >
                  ✕
                </button>
              {/if}
            </div>

            <div class="bg-dark-subtle rounded-lg p-4 space-y-3">
              <label class="text-sm text-gray-400 block">Buscar cuenta existente en Stripe</label>
              <div class="flex gap-2">
                <input
                  class="input flex-1"
                  placeholder="Buscar por email, nombre o ID"
                  bind:value={stripeSearchQuery}
                  onkeydown={(e) => e.key === 'Enter' && handleStripeSearch()}
                />
                <button type="button" class="btn-secondary" onclick={handleStripeSearch} disabled={stripeSearchLoading || saving}>
                  {stripeSearchLoading ? 'Buscando...' : 'Buscar'}
                </button>
              </div>

              {#if stripeSearchResults.length > 0}
                <div class="max-h-48 overflow-y-auto border border-border-dark rounded-lg divide-y divide-border-dark">
                  {#each stripeSearchResults as sc}
                    <div class="p-3 flex items-center justify-between gap-3">
                      <div class="text-xs">
                        <div class="font-mono text-text-light">{sc.id}</div>
                        <div class="text-gray-400">{sc.email || 'sin email'} {#if sc.name}· {sc.name}{/if}</div>
                      </div>
                      <button
                        type="button"
                        class="btn-secondary btn-sm"
                        onclick={() => linkSelectedStripeCustomer(sc.id)}
                        disabled={saving}
                      >
                        Vincular
                      </button>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>

            <div class="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 text-blue-400 text-xs">
              💡 Haz clic en "Buscar/Crear en Stripe" para:
              <ul class="list-disc list-inside mt-2 space-y-1">
                <li>Buscar cliente existente por email</li>
                <li>Crear nuevo cliente en Stripe si no existe</li>
                <li>Vincular automáticamente</li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Acciones de cuenta -->
        <div class="border-t border-border-dark pt-6">
          <h3 class="font-semibold text-text-light mb-4 flex items-center gap-2">
            <Power size={18} />
            Acciones de cuenta
          </h3>

          {#if editCustomer}
            {@const isSuspended = editCustomer.status === 'suspended'}
            {@const subSuspended = editCustomer.subscription?.status === 'suspended'}

            <div class="space-y-3">
              {#if !isSuspended && !subSuspended}
                <!-- Active account — show suspend options -->
                <button
                  type="button"
                  class="btn-secondary w-full flex items-center justify-center gap-2 text-yellow-400 border-yellow-500/40 hover:bg-yellow-500/10"
                  onclick={() => handleStatusAction('suspend_billing')}
                  disabled={!!statusActionLoading}
                >
                  <PauseCircle size={16} />
                  {statusActionLoading === 'suspend_billing' ? 'Suspendiendo...' : 'Suspender cobros'}
                </button>
                <button
                  type="button"
                  class="btn-secondary w-full flex items-center justify-center gap-2 text-red-400 border-red-500/40 hover:bg-red-500/10"
                  onclick={() => handleStatusAction('suspend_account')}
                  disabled={!!statusActionLoading}
                >
                  <Power size={16} />
                  {statusActionLoading === 'suspend_account' ? 'Suspendiendo...' : 'Suspender cuenta completa'}
                </button>
              {:else}
                <!-- Suspended — show reactivate -->
                <div class="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm flex items-center gap-2">
                  <AlertTriangle size={16} />
                  {isSuspended ? 'Cuenta suspendida' : 'Cobros suspendidos'}
                </div>
                <button
                  type="button"
                  class="btn-accent w-full flex items-center justify-center gap-2"
                  onclick={() => handleStatusAction('reactivate')}
                  disabled={!!statusActionLoading}
                >
                  <PlayCircle size={16} />
                  {statusActionLoading === 'reactivate' ? 'Reactivando...' : 'Reactivar cuenta'}
                </button>
              {/if}
            </div>
          {/if}
        </div>

        <!-- Botones finales -->
        <div class="border-t border-border-dark pt-4 flex gap-2">
          <button type="button" class="btn-secondary flex-1" onclick={() => { showEdit = false; }}>Cerrar</button>
        </div>
      </div>
    </div>
  </div>
{/if}

<!-- Modal Nuevo Cliente + Blueprint -->
{#if showNewClient}
  <div class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" role="dialog">
    <div class="bg-charcoal rounded-xl border border-border-dark w-full max-w-2xl flex flex-col" style="max-height: 90vh;">
      <!-- Header -->
      <div class="flex items-center justify-between p-5 border-b border-border-dark flex-shrink-0">
        <div>
          <h2 class="text-lg font-semibold text-text-light">Nuevo Cliente</h2>
          <div class="flex gap-2 mt-1 items-center">
            {#each [1,2,3] as step}
              <span class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
                {ncStep >= step ? 'bg-terracotta text-white' : 'bg-gray-700 text-gray-500'}">{step}</span>
            {/each}
            <span class="text-xs text-gray-500 ml-1">
              {ncStep === 1 ? 'Datos del cliente' : ncStep === 2 ? 'Selección de blueprint' : 'Confirmación'}
            </span>
          </div>
        </div>
        <button class="text-gray-400 hover:text-text-light" onclick={() => showNewClient = false}>✕</button>
      </div>

      <!-- Body -->
      <div class="p-5 overflow-y-auto flex-1">
        {#if ncToast}
          <div class="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-lg p-3 mb-3">{ncToast}</div>
        {/if}

        {#if ncStep === 1}
          <div class="grid grid-cols-2 gap-4">
            <div class="col-span-2">
              <label class="label">Empresa *</label>
              <input class="input w-full" bind:value={ncForm.company_name} placeholder="Nombre de la empresa" />
            </div>
            <div>
              <label class="label">Email *</label>
              <input type="email" class="input w-full" bind:value={ncForm.email} placeholder="contacto@empresa.com" />
            </div>
            <div>
              <label class="label">Teléfono *</label>
              <input type="tel" class="input w-full" bind:value={ncForm.phone} placeholder="+1 809 555 1234" />
            </div>
            <div>
              <label class="label">Nombre completo</label>
              <input class="input w-full" bind:value={ncForm.full_name} placeholder="Juan Pérez" />
            </div>
            <div>
              <label class="label">Subdominio *</label>
              <div class="flex items-center">
                <input class="input flex-1 rounded-r-none" bind:value={ncForm.subdomain} placeholder="miempresa" />
                <span class="bg-gray-700 border border-l-0 border-border-dark rounded-r-lg px-3 py-2 text-xs text-gray-400 whitespace-nowrap">.sajet.us</span>
              </div>
            </div>
            <div>
              <label class="label">Plan</label>
              <select class="input w-full" bind:value={ncForm.plan_name}>
                {#each plans as pl}
                  <option value={pl.name}>{pl.display_name}</option>
                {/each}
              </select>
            </div>
            <div>
              <label class="label">Usuarios</label>
              <input type="number" min="1" class="input w-full" bind:value={ncForm.user_count} />
            </div>
            <div>
              <label class="label">Partner (opcional)</label>
              <select class="input w-full" bind:value={ncForm.partner_id}>
                <option value="">Sin asignar</option>
                {#each partners.filter(p => p.status === 'active') as partner}
                  <option value={partner.id}>{partner.company_name} ({partner.partner_code})</option>
                {/each}
              </select>
            </div>
          </div>

        {:else if ncStep === 2}
          {#if blueprintsLoading}
            <div class="text-center py-8 text-gray-400">Cargando blueprints...</div>
          {:else}
            <p class="text-sm text-gray-400 mb-3">Selecciona el paquete de aplicaciones para este cliente:</p>
            <div class="grid grid-cols-2 gap-3">
              {#each blueprints as bp}
                <button onclick={() => selectedBlueprint = selectedBlueprint?.id === bp.id ? null : bp}
                  class="text-left p-4 rounded-xl border transition-all
                    {selectedBlueprint?.id === bp.id
                      ? 'border-terracotta bg-terracotta/10 ring-1 ring-terracotta'
                      : 'border-border-dark hover:border-gray-500 bg-gray-800/50'}">
                  <div class="font-medium text-text-light text-sm">{bp.name}</div>
                  {#if bp.description}
                    <div class="text-xs text-gray-400 mt-1 line-clamp-2">{bp.description}</div>
                  {/if}
                  <div class="text-xs text-gray-500 mt-2">{bp.module_count} módulos</div>
                </button>
              {/each}
              <button onclick={() => selectedBlueprint = null}
                class="text-left p-4 rounded-xl border transition-all
                  {selectedBlueprint === null
                    ? 'border-gray-500 bg-gray-700/30 ring-1 ring-gray-500'
                    : 'border-border-dark hover:border-gray-600 bg-gray-800/50'}">
                <div class="font-medium text-gray-300 text-sm">Sin blueprint</div>
                <div class="text-xs text-gray-500 mt-1">Solo crear cliente, sin Work Order</div>
              </button>
            </div>
            {#if selectedBlueprint}
              <div class="mt-4">
                <label class="label">Descripción de la orden (opcional)</label>
                <textarea bind:value={ncForm.description} rows="2"
                  placeholder="Instrucciones adicionales para el equipo técnico..."
                  class="input w-full resize-none"></textarea>
              </div>
            {/if}
          {/if}

        {:else}
          <div class="space-y-4">
            <div class="bg-gray-700/40 rounded-xl p-4 space-y-2 text-sm">
              <div class="text-xs text-gray-400 uppercase tracking-widest mb-2">Datos del cliente</div>
              <div><span class="text-gray-400">Empresa:</span> <span class="text-text-light font-medium">{ncForm.company_name}</span></div>
              <div><span class="text-gray-400">Email:</span> <span class="text-text-light">{ncForm.email}</span></div>
              <div><span class="text-gray-400">Teléfono:</span> <span class="text-text-light">{ncForm.phone}</span></div>
              <div><span class="text-gray-400">Subdominio:</span> <span class="text-blue-400 font-mono">{ncForm.subdomain}.sajet.us</span></div>
              <div><span class="text-gray-400">Plan:</span> <span class="text-text-light">{ncForm.plan_name}</span> — <span class="text-gray-400">{ncForm.user_count} usuario(s)</span></div>
            </div>
            {#if selectedBlueprint}
              <div class="bg-terracotta/10 border border-terracotta/30 rounded-xl p-4 text-sm">
                <div class="text-xs text-terracotta uppercase tracking-widest mb-2">Work Order — Blueprint</div>
                <div class="font-medium text-text-light">{selectedBlueprint.name}</div>
                <div class="text-xs text-gray-400 mt-1">{selectedBlueprint.module_count} módulos incluidos</div>
                {#if ncForm.description}
                  <div class="text-xs text-gray-400 mt-1 italic">{ncForm.description}</div>
                {/if}
              </div>
            {:else}
              <div class="bg-gray-700/30 border border-border-dark rounded-xl p-4 text-sm text-gray-400">
                Solo se creará el cliente sin Work Order de aprovisionamiento.
              </div>
            {/if}
          </div>
        {/if}
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-between p-5 border-t border-border-dark flex-shrink-0">
        <button onclick={() => { if (ncStep > 1) ncStep--; else showNewClient = false; }}
          class="btn-secondary">{ncStep > 1 ? '← Atrás' : 'Cancelar'}</button>
        {#if ncStep < 3}
          <button onclick={() => {
            ncToast = '';
            if (ncStep === 1 && (!ncForm.company_name || !ncForm.email || !ncForm.phone || !ncForm.subdomain)) {
              ncToast = 'Empresa, email, teléfono y subdominio son obligatorios'; return;
            }
            ncStep++;
          }} class="btn-accent">Siguiente →</button>
        {:else}
          <button onclick={createClientWithWO} disabled={creatingClient} class="btn-accent disabled:opacity-50">
            {creatingClient ? 'Creando...' : selectedBlueprint ? '✅ Crear Cliente + Work Order' : '✅ Crear Cliente'}
          </button>
        {/if}
      </div>
    </div>
  </div>
{/if}

<!-- Modal Credenciales -->
<CredentialsModal
  isOpen={showCredentialsModal}
  {credentials}
  onDismiss={() => {
    showCredentialsModal = false;
    credentials = null;
  }}
  onSendEmail={handleSendCredentialsEmail}
/>

<!-- Modal confirmar eliminación tenant + cuenta -->
{#if showDeleteModal && deleteCustomer}
  <div class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" role="dialog">
    <div class="bg-charcoal rounded-xl border border-border-dark w-full max-w-lg">
      <div class="flex items-center justify-between p-5 border-b border-border-dark">
        <h3 class="text-lg font-semibold text-red-400 flex items-center gap-2">
          <AlertTriangle size={18} /> Eliminar cuenta y tenant
        </h3>
        <button class="text-gray-400 hover:text-text-light" onclick={() => { showDeleteModal = false; }}>✕</button>
      </div>
      <div class="p-5 space-y-4">
        <p class="text-sm text-gray-300">
          Esta acción eliminará permanentemente la cuenta <strong>{deleteCustomer.company_name}</strong>
          y su tenant <strong>{deleteCustomer.subdomain}</strong>.
        </p>
        <p class="text-xs text-red-300/90">
          Para confirmar, escriba el nombre del tenant: <span class="font-mono">{deleteCustomer.subdomain}</span>
        </p>
        <input
          class="input w-full font-mono"
          placeholder={deleteCustomer.subdomain}
          bind:value={deleteConfirmName}
        />
      </div>
      <div class="p-5 border-t border-border-dark flex justify-end gap-2">
        <button class="btn-secondary" onclick={() => { showDeleteModal = false; }}>Cancelar</button>
        <button class="btn-danger" onclick={confirmDeleteTenantAndAccount} disabled={deletingTenant}>
          {deletingTenant ? 'Eliminando...' : 'Confirmar eliminación'}
        </button>
      </div>
    </div>
  </div>
{/if}
