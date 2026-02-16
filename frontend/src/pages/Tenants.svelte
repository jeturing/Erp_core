<script lang="ts">
  import { onMount } from 'svelte';
  import { Modal } from '../lib/components';
  import { tenantsApi } from '../lib/api';
  import { toasts } from '../lib/stores/toast';
  import { formatDate } from '../lib/utils/formatters';
  import type { Tenant } from '../lib/types';
  import { Plus, KeyRound, ShieldOff, ShieldCheck, Trash2, Eye, EyeOff } from 'lucide-svelte';

  let tenants: Tenant[] = [];
  let loading = true;
  let search = '';

  // Create modal
  let showCreateModal = false;
  let creating = false;
  let createError = '';
  let showCreatePassword = false;
  let createForm = {
    subdomain: '',
    company_name: '',
    email: '',
    plan: 'basic' as 'basic' | 'pro' | 'enterprise',
    password: '',
    confirm_password: '',
  };

  // Password modal
  let showPasswordModal = false;
  let passwordLoading = false;
  let passwordError = '';
  let showNewPassword = false;
  let showConfirmPassword = false;
  let passwordTenant: Tenant | null = null;
  let newPassword = '';
  let confirmPassword = '';

  // Delete modal
  let showDeleteModal = false;
  let deleteTenant: Tenant | null = null;
  let deleteLoading = false;

  let actionLoading: Record<string, boolean> = {};

  async function loadTenants() {
    loading = true;
    try {
      const res = await tenantsApi.list();
      tenants = res.items;
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error cargando tenants');
    } finally {
      loading = false;
    }
  }

  onMount(loadTenants);

  $: filteredTenants = tenants.filter((t) => {
    const q = search.toLowerCase().trim();
    if (!q) return true;
    return `${t.company_name} ${t.email} ${t.subdomain}`.toLowerCase().includes(q);
  });

  $: totalActive = tenants.filter((t) => t.status === 'active').length;

  function statusBadge(status: string) {
    if (status === 'active') return 'badge-success';
    if (status === 'provisioning' || status === 'pending') return 'badge-warning';
    if (status === 'suspended' || status === 'payment_failed') return 'badge-error';
    return 'badge-neutral';
  }

  function planBadge(plan: string) {
    if (plan === 'enterprise') return 'badge-enterprise';
    if (plan === 'pro') return 'badge-pro';
    return 'badge-basic';
  }

  function resetCreateForm() {
    createForm = { subdomain: '', company_name: '', email: '', plan: 'basic', password: '', confirm_password: '' };
    createError = '';
    showCreatePassword = false;
  }

  async function handleCreate() {
    createError = '';
    if (!createForm.subdomain.trim()) { createError = 'El subdominio es obligatorio'; return; }
    if (!createForm.email.trim()) { createError = 'El email es obligatorio'; return; }
    if (createForm.password && createForm.password !== createForm.confirm_password) {
      createError = 'Las contraseñas no coinciden'; return;
    }
    creating = true;
    try {
      await tenantsApi.create({
        subdomain: createForm.subdomain.trim(),
        company_name: createForm.company_name.trim() || createForm.subdomain.trim(),
        admin_email: createForm.email.trim(),
        admin_password: createForm.password || undefined,
        plan: createForm.plan,
        use_fast_method: true,
      });
      showCreateModal = false;
      resetCreateForm();
      toasts.success('Tenant creado exitosamente');
      await loadTenants();
    } catch (err) {
      createError = err instanceof Error ? err.message : 'Error creando tenant';
    } finally {
      creating = false;
    }
  }

  function openPasswordModal(tenant: Tenant) {
    passwordTenant = tenant;
    newPassword = '';
    confirmPassword = '';
    passwordError = '';
    showNewPassword = false;
    showConfirmPassword = false;
    showPasswordModal = true;
  }

  async function handleChangePassword() {
    if (!passwordTenant) return;
    passwordError = '';
    if (newPassword.length < 6) { passwordError = 'La contraseña debe tener al menos 6 caracteres'; return; }
    if (newPassword !== confirmPassword) { passwordError = 'Las contraseñas no coinciden'; return; }
    passwordLoading = true;
    try {
      await tenantsApi.changePassword({ subdomain: passwordTenant.subdomain, new_password: newPassword });
      showPasswordModal = false;
      toasts.success(`Contraseña de ${passwordTenant.subdomain} actualizada`);
    } catch (err) {
      passwordError = err instanceof Error ? err.message : 'Error cambiando contraseña';
    } finally {
      passwordLoading = false;
    }
  }

  async function toggleSuspend(tenant: Tenant) {
    actionLoading = { ...actionLoading, [tenant.subdomain]: true };
    try {
      const isSuspending = tenant.status === 'active';
      await tenantsApi.suspend({ subdomain: tenant.subdomain, suspend: isSuspending });
      toasts.success(`Tenant ${isSuspending ? 'suspendido' : 'reactivado'}`);
      await loadTenants();
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error cambiando estado');
    } finally {
      actionLoading = { ...actionLoading, [tenant.subdomain]: false };
    }
  }

  function openDeleteModal(tenant: Tenant) {
    deleteTenant = tenant;
    showDeleteModal = true;
  }

  async function handleDelete() {
    if (!deleteTenant) return;
    deleteLoading = true;
    try {
      await tenantsApi.delete(deleteTenant.subdomain);
      showDeleteModal = false;
      toasts.success(`Tenant ${deleteTenant.subdomain} eliminado`);
      deleteTenant = null;
      await loadTenants();
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error eliminando tenant');
    } finally {
      deleteLoading = false;
    }
  }
</script>

<div class="p-6 lg:p-8 space-y-6">
  <!-- Page Header -->
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
      <h1 class="page-title">TENANTS</h1>
      <p class="page-subtitle mt-1">Gestión operativa de clientes y acciones de provisioning</p>
    </div>
    <button class="btn btn-accent" on:click={() => { resetCreateForm(); showCreateModal = true; }}>
      <Plus size={14} />
      NUEVO TENANT
    </button>
  </div>

  <!-- Stats + Search -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <div class="md:col-span-1">
      <label class="label block mb-1" for="tenant-search">Buscar</label>
      <input
        id="tenant-search"
        class="input w-full"
        placeholder="empresa, email o subdominio..."
        bind:value={search}
      />
    </div>
    <div class="stat-card">
      <span class="stat-label">Total Tenants</span>
      <span class="stat-value">{tenants.length}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Activos</span>
      <span class="stat-value text-success">{totalActive}</span>
    </div>
  </div>

  <!-- Table -->
  <div class="card p-0 overflow-hidden">
    <div class="flex items-center justify-between px-6 py-4 border-b border-border-light">
      <span class="section-heading">Listado de Tenants</span>
      <span class="text-[11px] text-gray-500">{filteredTenants.length} resultado{filteredTenants.length !== 1 ? 's' : ''}</span>
    </div>
    {#if loading}
      <div class="py-16 flex justify-center">
        <div class="w-8 h-8 border-2 border-charcoal border-t-transparent rounded-full animate-spin"></div>
      </div>
    {:else}
      <div class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr>
              <th>Tenant</th>
              <th>Plan</th>
              <th>Estado</th>
              <th>Servidor</th>
              <th>Creado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {#each filteredTenants as tenant (tenant.id)}
              <tr>
                <td>
                  <div class="flex flex-col gap-0.5">
                    <span class="font-semibold text-text-primary">{tenant.company_name || tenant.subdomain}</span>
                    <span class="text-[11px] text-gray-500">{tenant.email}</span>
                    <span class="text-[11px] text-gray-400 font-mono">{tenant.subdomain}.sajet.us</span>
                  </div>
                </td>
                <td>
                  <span class="badge {planBadge(tenant.plan)}">{tenant.plan || 'basic'}</span>
                </td>
                <td>
                  <span class="badge {statusBadge(tenant.status)}">{tenant.status}</span>
                </td>
                <td class="text-text-secondary text-sm">{tenant.server || '-'}</td>
                <td class="text-text-secondary text-sm">{formatDate(tenant.created_at)}</td>
                <td>
                  <div class="flex flex-wrap gap-1.5">
                    <button
                      class="btn btn-secondary btn-sm"
                      on:click={() => openPasswordModal(tenant)}
                      disabled={actionLoading[tenant.subdomain]}
                      title="Cambiar contraseña"
                    >
                      <KeyRound size={12} />
                      Clave
                    </button>
                    <button
                      class="btn btn-sm {tenant.status === 'active' ? 'btn-danger' : 'btn-primary'}"
                      on:click={() => toggleSuspend(tenant)}
                      disabled={actionLoading[tenant.subdomain]}
                    >
                      {#if tenant.status === 'active'}
                        <ShieldOff size={12} />
                        Suspender
                      {:else}
                        <ShieldCheck size={12} />
                        Reactivar
                      {/if}
                    </button>
                    <button
                      class="btn btn-danger btn-sm"
                      on:click={() => openDeleteModal(tenant)}
                      disabled={actionLoading[tenant.subdomain]}
                      title="Eliminar tenant"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </td>
              </tr>
            {:else}
              <tr>
                <td colspan="6" class="text-center text-gray-500 py-12 text-sm">
                  {search ? 'No hay tenants que coincidan con la búsqueda' : 'No hay tenants registrados'}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</div>

<!-- Modal: Nuevo Tenant -->
<Modal
  bind:isOpen={showCreateModal}
  title="Nuevo Tenant"
  confirmText="CREAR TENANT"
  on:confirm={handleCreate}
  on:close={() => { showCreateModal = false; resetCreateForm(); }}
  loading={creating}
  size="md"
>
  <div class="space-y-4">
    {#if createError}
      <div class="p-3 rounded bg-error/10 border border-error/20 text-sm text-error">{createError}</div>
    {/if}

    <div>
      <label class="label block mb-1" for="create-company">Empresa</label>
      <input id="create-company" class="input w-full" placeholder="Mi Empresa SRL" bind:value={createForm.company_name} />
    </div>

    <div>
      <label class="label block mb-1" for="create-email">Email <span class="text-error">*</span></label>
      <input id="create-email" type="email" class="input w-full" placeholder="admin@empresa.com" bind:value={createForm.email} required />
    </div>

    <div>
      <label class="label block mb-1" for="create-subdomain">Subdominio <span class="text-error">*</span></label>
      <div class="flex items-center gap-0">
        <input id="create-subdomain" class="input w-full rounded-r-none" placeholder="miempresa" bind:value={createForm.subdomain} required />
        <span class="px-3 py-2 bg-bg-card border border-l-0 border-border-light text-gray-500 text-[11px] rounded-r-md whitespace-nowrap">.sajet.us</span>
      </div>
    </div>

    <div>
      <label class="label block mb-1" for="create-plan">Plan</label>
      <select id="create-plan" class="input w-full" bind:value={createForm.plan}>
        <option value="basic">Basic</option>
        <option value="pro">Pro</option>
        <option value="enterprise">Enterprise</option>
      </select>
    </div>

    <div>
      <label class="label block mb-1" for="create-password">Contraseña admin</label>
      <div class="relative">
        <input
          id="create-password"
          type={showCreatePassword ? 'text' : 'password'}
          class="input w-full pr-9"
          placeholder="••••••••"
          bind:value={createForm.password}
        />
        <button
          type="button"
          class="absolute inset-y-0 right-0 px-2.5 text-gray-500 hover:text-text-primary"
          on:click={() => showCreatePassword = !showCreatePassword}
        >
          {#if showCreatePassword}<EyeOff size={14} />{:else}<Eye size={14} />{/if}
        </button>
      </div>
    </div>

    {#if createForm.password}
      <div>
        <label class="label block mb-1" for="create-confirm-password">Confirmar contraseña</label>
        <input
          id="create-confirm-password"
          type="password"
          class="input w-full"
          placeholder="••••••••"
          bind:value={createForm.confirm_password}
        />
      </div>
    {/if}
  </div>
</Modal>

<!-- Modal: Cambiar Contraseña -->
<Modal
  bind:isOpen={showPasswordModal}
  title="Cambiar Contraseña"
  confirmText="ACTUALIZAR"
  on:confirm={handleChangePassword}
  on:close={() => { showPasswordModal = false; passwordError = ''; }}
  loading={passwordLoading}
  size="sm"
>
  <div class="space-y-4">
    {#if passwordError}
      <div class="p-3 rounded bg-error/10 border border-error/20 text-sm text-error">{passwordError}</div>
    {/if}

    <div>
      <label class="label block mb-1" for="pw-subdomain">Subdominio</label>
      <input id="pw-subdomain" class="input w-full opacity-60" value={passwordTenant?.subdomain || ''} readonly disabled />
    </div>

    <div>
      <label class="label block mb-1" for="new-password">Nueva Contraseña</label>
      <div class="relative">
        <input
          id="new-password"
          type={showNewPassword ? 'text' : 'password'}
          class="input w-full pr-9"
          placeholder="••••••••"
          bind:value={newPassword}
        />
        <button
          type="button"
          class="absolute inset-y-0 right-0 px-2.5 text-gray-500 hover:text-text-primary"
          on:click={() => showNewPassword = !showNewPassword}
        >
          {#if showNewPassword}<EyeOff size={14} />{:else}<Eye size={14} />{/if}
        </button>
      </div>
    </div>

    <div>
      <label class="label block mb-1" for="confirm-new-password">Confirmar Contraseña</label>
      <div class="relative">
        <input
          id="confirm-new-password"
          type={showConfirmPassword ? 'text' : 'password'}
          class="input w-full pr-9"
          placeholder="••••••••"
          bind:value={confirmPassword}
        />
        <button
          type="button"
          class="absolute inset-y-0 right-0 px-2.5 text-gray-500 hover:text-text-primary"
          on:click={() => showConfirmPassword = !showConfirmPassword}
        >
          {#if showConfirmPassword}<EyeOff size={14} />{:else}<Eye size={14} />{/if}
        </button>
      </div>
    </div>
  </div>
</Modal>

<!-- Modal: Confirmar Eliminación -->
<Modal
  bind:isOpen={showDeleteModal}
  title="Eliminar Tenant"
  confirmText="ELIMINAR"
  confirmVariant="danger"
  on:confirm={handleDelete}
  on:close={() => { showDeleteModal = false; deleteTenant = null; }}
  loading={deleteLoading}
  size="sm"
>
  <div class="space-y-3">
    <p class="text-sm text-text-secondary">
      Esta acción es <strong class="text-error">irreversible</strong>. Se eliminará permanentemente el tenant:
    </p>
    {#if deleteTenant}
      <div class="p-3 rounded bg-error/5 border border-error/20">
        <p class="font-semibold text-text-primary">{deleteTenant.company_name || deleteTenant.subdomain}</p>
        <p class="text-[11px] text-gray-500 font-mono">{deleteTenant.subdomain}.sajet.us</p>
      </div>
    {/if}
  </div>
</Modal>
