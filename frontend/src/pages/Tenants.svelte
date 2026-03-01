<script lang="ts">
  import { onMount } from 'svelte';
  import { tenantsApi } from '../lib/api';
  import { partnersApi } from '../lib/api/partners';
  import { toasts } from '../lib/stores/toast';
  import { currentUser } from '../lib/stores';
  import { formatDate } from '../lib/utils/formatters';
  import { Plus, RefreshCw, Search } from 'lucide-svelte';
  import type { Tenant } from '../lib/types';
  import type { PartnerItem } from '../lib/types';


  let tenants = $state<Tenant[]>([]);
  let partners = $state<PartnerItem[]>([]);
  let loading = $state(true);
  let searchQuery = $state('');
  let filterStatus = $state('all');
  let filterPlan = $state('all');
  let filterPartner = $state('all');
  let showForm = $state(false);

  // Form fields
  let formNombre = $state('');
  let formEmail = $state('');
  let formSubdomain = $state('');
  let formPlan = $state<'basic' | 'pro' | 'enterprise'>('basic');
  let formPassword = $state('');
  let formConfirmPassword = $state('');
  let formPartnerId = $state<number | null>(null);
  let formLoading = $state(false);

  // Per-row action state
  let expandedPasswordRow = $state<string | null>(null);
  let rowPassword = $state('');
  let rowConfirmPassword = $state('');
  let rowPasswordLoading = $state(false);
  let showDeleteModal = $state(false);
  let deleteTenantTarget = $state<Tenant | null>(null);
  let deleteConfirmInput = $state('');
  let deleteLoading = $state(false);
  let showSuspendModal = $state(false);
  let suspendTenantTarget = $state<Tenant | null>(null);
  let suspendLoading = $state(false);

  async function loadTenants() {
    loading = true;
    try {
      const [data, pData] = await Promise.all([
        tenantsApi.list(),
        partnersApi.getPartners('active').catch(() => ({ items: [] })),
      ]);
      tenants = data.items ?? [];
      partners = pData.items ?? [];
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al cargar tenants');
    } finally {
      loading = false;
    }
  }

  async function handleCreate(e: Event) {
    e.preventDefault();
    if (formPassword !== formConfirmPassword) {
      toasts.error('Las contraseñas no coinciden');
      return;
    }
    formLoading = true;
    try {
      await tenantsApi.create({
        subdomain: formSubdomain,
        company_name: formNombre,
        admin_email: formEmail,
        admin_password: formPassword,
        plan: formPlan,
        partner_id: formPartnerId,
      });
      toasts.success('Tenant creado exitosamente');
      showForm = false;
      formNombre = '';
      formEmail = '';
      formSubdomain = '';
      formPlan = 'basic';
      formPassword = '';
      formConfirmPassword = '';
      formPartnerId = null;
      await loadTenants();
    } catch (e: any) {
      const msg = e?.message ?? 'Error al crear tenant';
      toasts.error($currentUser?.role === 'admin' ? msg : 'Error al crear tenant');
    } finally {
      formLoading = false;
    }
  }

  function getProvisioningServerId(tenant: Tenant): string {
    return tenant.server_id || 'primary';
  }

  async function handleChangePassword(tenant: Tenant) {
    if (rowPassword !== rowConfirmPassword) {
      toasts.error('Las contraseñas no coinciden');
      return;
    }
    if (!rowPassword) {
      toasts.error('Ingresa una contraseña');
      return;
    }
    rowPasswordLoading = true;
    try {
      await tenantsApi.changePassword({
        subdomain: tenant.subdomain,
        new_password: rowPassword,
        server_id: getProvisioningServerId(tenant),
      });
      toasts.success('Contraseña actualizada');
      expandedPasswordRow = null;
      rowPassword = '';
      rowConfirmPassword = '';
    } catch (e: any) {
      const msg = e?.message ?? 'Error al cambiar contraseña';
      toasts.error($currentUser?.role === 'admin' ? msg : 'Error al cambiar contraseña');
    } finally {
      rowPasswordLoading = false;
    }
  }

  function openSuspendModal(tenant: Tenant) {
    suspendTenantTarget = tenant;
    showSuspendModal = true;
  }

  function closeSuspendModal(force = false) {
    if (suspendLoading && !force) return;
    showSuspendModal = false;
    suspendTenantTarget = null;
  }

  async function confirmSuspendTenant() {
    if (!suspendTenantTarget) return;
    const isActive = suspendTenantTarget.status === 'active';
    suspendLoading = true;
    try {
      await tenantsApi.suspend({
        subdomain: suspendTenantTarget.subdomain,
        suspend: isActive,
        server_id: getProvisioningServerId(suspendTenantTarget),
      });
      tenants = tenants.map((tenant) => {
        if (tenant.subdomain !== suspendTenantTarget?.subdomain) return tenant;
        return {
          ...tenant,
          status: isActive ? 'suspended' : 'active',
        };
      });
      toasts.success(`Tenant ${isActive ? 'suspendido' : 'reactivado'}`);
      closeSuspendModal(true);
      await loadTenants();
    } catch (e: any) {
      const msg = e?.message ?? 'Error al actualizar estado';
      toasts.error($currentUser?.role === 'admin' ? msg : 'Error al actualizar estado');
    } finally {
      suspendLoading = false;
    }
  }

  function openDeleteModal(tenant: Tenant) {
    deleteTenantTarget = tenant;
    deleteConfirmInput = '';
    showDeleteModal = true;
  }

  function closeDeleteModal(force = false) {
    if (deleteLoading && !force) return;
    showDeleteModal = false;
    deleteTenantTarget = null;
    deleteConfirmInput = '';
  }

  async function confirmDeleteTenant() {
    if (!deleteTenantTarget) return;
    const expected = deleteTenantTarget.subdomain.trim().toLowerCase();
    const typed = deleteConfirmInput.trim();
    if (typed.toLowerCase() !== expected) {
      toasts.error('Confirmación incorrecta. No se eliminó el tenant.');
      return;
    }

    deleteLoading = true;
    try {
      const targetSubdomain = deleteTenantTarget.subdomain;
      await tenantsApi.delete(targetSubdomain, typed, deleteTenantTarget.server_id || undefined);
      tenants = tenants.filter(t => t.subdomain !== targetSubdomain);
      toasts.success('Tenant eliminado');
      closeDeleteModal(true);
      await loadTenants();
    } catch (e: any) {
      const msg = e?.message ?? 'Error al eliminar tenant';
      toasts.error($currentUser?.role === 'admin' ? msg : 'Error al eliminar tenant');
    } finally {
      deleteLoading = false;
    }
  }

  async function handleDeleteModalSubmit(e: Event) {
    e.preventDefault();
    await confirmDeleteTenant();
  }

  function togglePasswordRow(subdomain: string) {
    if (expandedPasswordRow === subdomain) {
      expandedPasswordRow = null;
      rowPassword = '';
      rowConfirmPassword = '';
    } else {
      expandedPasswordRow = subdomain;
      rowPassword = '';
      rowConfirmPassword = '';
    }
  }

  function tenantRowKey(tenant: Tenant, index: number): string {
    const subdomain = tenant.subdomain || 'tenant';
    const server = tenant.server_id || tenant.server || 'local';
    return `${subdomain}:${server}:${tenant.id}:${index}`;
  }

  let filteredTenants = $derived(
    tenants.filter(t => {
      // Text search
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const match =
          t.subdomain?.toLowerCase().includes(q) ||
          t.email?.toLowerCase().includes(q) ||
          t.company_name?.toLowerCase().includes(q);
        if (!match) return false;
      }
      // Status filter
      if (filterStatus !== 'all' && t.status !== filterStatus) return false;
      // Plan filter
      if (filterPlan !== 'all' && (t.plan ?? 'basic') !== filterPlan) return false;
      // Partner filter
      if (filterPartner === 'none' && t.partner_name) return false;
      if (filterPartner !== 'all' && filterPartner !== 'none' && t.partner_name !== filterPartner) return false;
      return true;
    })
  );

  let totalTenants = $derived(tenants.length);
  let activeTenants = $derived(tenants.filter(t => t.status === 'active').length);
  let suspendedTenants = $derived(tenants.filter(t => t.status === 'suspended').length);
  let uniquePartnerNames = $derived([...new Set(tenants.map(t => t.partner_name).filter(Boolean))] as string[]);

  onMount(loadTenants);
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="page-title">TENANTS</h1>
      <p class="page-subtitle">Gestión de clientes y sus instancias</p>
    </div>
    <button class="btn-accent px-4 py-2 flex items-center gap-2" onclick={() => showForm = !showForm}>
      <Plus size={14} />
      NUEVO TENANT
    </button>
  </div>

  <!-- Inline Add Form -->
  {#if showForm}
    <div class="card border-l-2 border-l-terracotta">
      <h3 class="section-heading mb-5">NUEVO TENANT</h3>
      <form onsubmit={handleCreate} class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="label" for="f-nombre">Nombre empresa</label>
            <input id="f-nombre" class="input w-full px-3 py-2" type="text" bind:value={formNombre} placeholder="Empresa S.A." required />
          </div>
          <div>
            <label class="label" for="f-email">Email administrador</label>
            <input id="f-email" class="input w-full px-3 py-2" type="email" bind:value={formEmail} placeholder="admin@empresa.com" required />
          </div>
          <div>
            <label class="label" for="f-subdomain">Subdominio</label>
            <div class="flex items-stretch">
              <input
                id="f-subdomain"
                class="input flex-1 px-3 py-2 border-r-0"
                type="text"
                bind:value={formSubdomain}
                placeholder="mi-empresa"
                required
                pattern="[a-z0-9\-]+"
              />
              <span class="bg-bg-card border border-border-light px-3 py-2 text-sm text-gray-500 whitespace-nowrap">.sajet.us</span>
            </div>
          </div>
          <div>
            <label class="label" for="f-plan">Plan</label>
            <select id="f-plan" class="input w-full px-3 py-2" bind:value={formPlan}>
              <option value="basic">Basic</option>
              <option value="pro">Pro</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>
          <div>
            <label class="label" for="f-partner">Partner (opcional)</label>
            <select id="f-partner" class="input w-full px-3 py-2" bind:value={formPartnerId}>
              <option value={null}>— Directo (sin partner) —</option>
              {#each partners as p (p.id)}
                <option value={p.id}>{p.company_name}</option>
              {/each}
            </select>
          </div>
          <div>
            <label class="label" for="f-password">Contraseña</label>
            <input id="f-password" class="input w-full px-3 py-2" type="password" autocomplete="new-password" bind:value={formPassword} placeholder="••••••••" required />
          </div>
          <div>
            <label class="label" for="f-confirm">Confirmar contraseña</label>
            <input id="f-confirm" class="input w-full px-3 py-2" type="password" autocomplete="new-password" bind:value={formConfirmPassword} placeholder="••••••••" required />
          </div>
        </div>
        <div class="flex gap-3 pt-2">
          <button type="button" class="btn-secondary px-4 py-2" onclick={() => showForm = false}>CANCELAR</button>
          <button type="submit" class="btn-accent px-4 py-2 disabled:opacity-60" disabled={formLoading}>
            {formLoading ? 'CREANDO...' : 'CREAR TENANT'}
          </button>
        </div>
      </form>
    </div>
  {/if}

  <!-- Stats -->
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
    <div class="stat-card card">
      <div class="stat-value">{totalTenants}</div>
      <div class="stat-label">Total Tenants</div>
    </div>
    <div class="stat-card card">
      <div class="stat-value">{activeTenants}</div>
      <div class="stat-label">Activos</div>
    </div>
    <div class="stat-card card">
      <div class="stat-value">{suspendedTenants}</div>
      <div class="stat-label">Suspendidos</div>
    </div>
    <div class="stat-card card">
      <div class="stat-value">{filteredTenants.length}</div>
      <div class="stat-label">Mostrando</div>
    </div>
  </div>

  <!-- Search + Filters -->
  <div class="space-y-3">
    <div class="relative">
      <Search size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
      <input
        class="input w-full pl-9 pr-3 py-2"
        type="text"
        placeholder="Buscar por subdominio, email o empresa..."
        bind:value={searchQuery}
      />
    </div>
    <div class="flex flex-wrap gap-3">
      <select class="input px-3 py-2 text-sm" bind:value={filterStatus}>
        <option value="all">Estado: Todos</option>
        <option value="active">✅ Activos</option>
        <option value="suspended">⚠️ Suspendidos</option>
        <option value="pending">⏳ Pendientes</option>
      </select>
      <select class="input px-3 py-2 text-sm" bind:value={filterPlan}>
        <option value="all">Plan: Todos</option>
        <option value="basic">Basic</option>
        <option value="pro">Pro</option>
        <option value="enterprise">Enterprise</option>
      </select>
      <select class="input px-3 py-2 text-sm" bind:value={filterPartner}>
        <option value="all">Partner: Todos</option>
        <option value="none">🔹 Sin Partner (Directo)</option>
        {#each uniquePartnerNames as pn}
          <option value={pn}>{pn}</option>
        {/each}
      </select>
      {#if filterStatus !== 'all' || filterPlan !== 'all' || filterPartner !== 'all'}
        <button
          class="btn-secondary btn-sm text-xs"
          onclick={() => { filterStatus = 'all'; filterPlan = 'all'; filterPartner = 'all'; }}
        >
          ✕ Limpiar filtros
        </button>
      {/if}
    </div>
  </div>

  <!-- Table -->
  <div class="card p-0 overflow-hidden">
    {#if loading}
      <div class="p-8 text-center text-gray-500 text-sm">Cargando tenants...</div>
    {:else if filteredTenants.length === 0}
      <div class="p-8 text-center text-gray-500 text-sm">No se encontraron tenants</div>
    {:else}
      <table class="table w-full">
        <thead>
          <tr>
            <th>TENANT</th>
            <th>PLAN</th>
            <th>PARTNER</th>
            <th>ESTADO</th>
            <th>SERVIDOR</th>
            <th>CREADO</th>
            <th>ACCIONES</th>
          </tr>
        </thead>
        <tbody>
          {#each filteredTenants as tenant, i (tenantRowKey(tenant, i))}
            <tr>
              <td>
                <div class="font-medium text-text-primary text-sm">{tenant.company_name ?? '-'}</div>
                <div class="text-xs text-gray-500">{tenant.email ?? '-'}</div>
                <span class="badge-neutral text-[10px] mt-1 inline-block">{tenant.subdomain}.sajet.us</span>
              </td>
              <td>
                {#if tenant.plan === 'enterprise'}
                  <span class="badge-enterprise">{tenant.plan}</span>
                {:else if tenant.plan === 'pro'}
                  <span class="badge-pro">{tenant.plan}</span>
                {:else}
                  <span class="badge-basic">{tenant.plan ?? 'basic'}</span>
                {/if}
                {#if tenant.monthly_amount}
                  <div class="text-[10px] text-gray-400 mt-1">${tenant.monthly_amount}/mo</div>
                {/if}
              </td>
              <td>
                {#if tenant.partner_name}
                  <span class="badge-pro text-[10px]">{tenant.partner_name}</span>
                {:else}
                  <span class="text-xs text-gray-400">Directo</span>
                {/if}
              </td>
              <td>
                {#if tenant.status === 'active'}
                  <span class="badge-success">Activo</span>
                {:else if tenant.status === 'suspended'}
                  <span class="badge-warning">Suspendido</span>
                {:else}
                  <span class="badge-neutral">{tenant.status}</span>
                {/if}
              </td>
              <td class="text-sm text-gray-600">{tenant.server ?? '-'}</td>
              <td class="text-sm text-gray-500">{formatDate(tenant.created_at)}</td>
              <td>
                <div class="flex items-center gap-2 flex-wrap">
                  <button
                    class="btn-secondary btn-sm"
                    onclick={() => togglePasswordRow(tenant.subdomain)}
                  >
                    CAMBIAR CLAVE
                  </button>
                  <button
                    class={tenant.status === 'active' ? 'btn-danger btn-sm' : 'btn-secondary btn-sm'}
                    onclick={() => openSuspendModal(tenant)}
                  >
                    {tenant.status === 'active' ? 'SUSPENDER' : 'REACTIVAR'}
                  </button>
                  <button
                    class="btn-danger btn-sm"
                    onclick={() => openDeleteModal(tenant)}
                  >
                    ELIMINAR
                  </button>
                </div>
              </td>
            </tr>
            <!-- Inline password row -->
            {#if expandedPasswordRow === tenant.subdomain}
              <tr class="bg-bg-page">
                <td colspan="7" class="py-4 px-6">
                  <div class="flex items-end gap-4 flex-wrap">
                    <div>
                      <label class="label" for="rp-{tenant.subdomain}">Nueva contraseña</label>
                      <input
                        id="rp-{tenant.subdomain}"
                        type="password"
                        class="input px-3 py-2 w-48"
                        placeholder="••••••••"
                        bind:value={rowPassword}
                      />
                    </div>
                    <div>
                      <label class="label" for="rc-{tenant.subdomain}">Confirmar</label>
                      <input
                        id="rc-{tenant.subdomain}"
                        type="password"
                        class="input px-3 py-2 w-48"
                        placeholder="••••••••"
                        bind:value={rowConfirmPassword}
                      />
                    </div>
                    <div class="flex gap-2">
                      <button
                        class="btn-secondary btn-sm"
                        onclick={() => { expandedPasswordRow = null; rowPassword = ''; rowConfirmPassword = ''; }}
                      >CANCELAR</button>
                      <button
                        class="btn-accent btn-sm disabled:opacity-60"
                        disabled={rowPasswordLoading}
                        onclick={() => handleChangePassword(tenant)}
                      >
                        {rowPasswordLoading ? 'GUARDANDO...' : 'GUARDAR'}
                      </button>
                    </div>
                  </div>
                </td>
              </tr>
            {/if}
          {/each}
        </tbody>
      </table>
    {/if}
  </div>

  {#if showDeleteModal && deleteTenantTarget}
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label="Confirmar eliminación tenant">
      <button
        type="button"
        class="fixed inset-0 bg-black/70"
        aria-label="Cerrar modal"
        onclick={() => closeDeleteModal()}
      ></button>

      <div class="relative z-10 w-full max-w-lg card border border-red-700/40">
        <div class="mb-3">
          <h3 class="text-lg font-semibold text-text-primary">Confirmar eliminación</h3>
          <p class="text-sm text-gray-400 mt-1">
            Esta acción eliminará el tenant y no se puede deshacer.
          </p>
          <p class="text-sm text-gray-300 mt-2">
            Escribe exactamente:
            <span class="font-mono text-red-300">{deleteTenantTarget.subdomain}</span>
          </p>
        </div>

        <form class="space-y-4" onsubmit={handleDeleteModalSubmit}>
          <input
            class="input w-full px-3 py-2 font-mono"
            type="text"
            bind:value={deleteConfirmInput}
            placeholder={deleteTenantTarget.subdomain}
            autocomplete="off"
          />

          <div class="flex justify-end gap-2">
            <button type="button" class="btn-secondary btn-sm" onclick={() => closeDeleteModal()} disabled={deleteLoading}>
              CANCELAR
            </button>
            <button
              type="submit"
              class="btn-danger btn-sm disabled:opacity-60"
              disabled={deleteLoading}
            >
              {deleteLoading ? 'ELIMINANDO...' : 'ELIMINAR TENANT'}
            </button>
          </div>
        </form>
      </div>
    </div>
  {/if}

  {#if showSuspendModal && suspendTenantTarget}
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label="Confirmar suspensión tenant">
      <button
        type="button"
        class="fixed inset-0 bg-black/70"
        aria-label="Cerrar modal"
        onclick={() => closeSuspendModal()}
      ></button>

      <div class="relative z-10 w-full max-w-md card border border-amber-700/40">
        <div class="mb-3">
          <h3 class="text-lg font-semibold text-text-primary">
            {suspendTenantTarget.status === 'active' ? 'Confirmar suspensión' : 'Confirmar reactivación'}
          </h3>
          <p class="text-sm text-gray-300 mt-2">
            {#if suspendTenantTarget.status === 'active'}
              ¿Deseas suspender el tenant <span class="font-mono text-amber-300">{suspendTenantTarget.subdomain}</span>?
            {:else}
              ¿Deseas reactivar el tenant <span class="font-mono text-emerald-300">{suspendTenantTarget.subdomain}</span>?
            {/if}
          </p>
        </div>

        <div class="flex justify-end gap-2">
          <button type="button" class="btn-secondary btn-sm" onclick={() => closeSuspendModal()} disabled={suspendLoading}>
            CANCELAR
          </button>
          <button
            type="button"
            class={(suspendTenantTarget.status === 'active' ? 'btn-danger' : 'btn-accent') + ' btn-sm disabled:opacity-60'}
            onclick={confirmSuspendTenant}
            disabled={suspendLoading}
          >
            {#if suspendLoading}
              PROCESANDO...
            {:else if suspendTenantTarget.status === 'active'}
              SUSPENDER
            {:else}
              REACTIVAR
            {/if}
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>
