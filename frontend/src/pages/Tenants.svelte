<script lang="ts">
  import { onMount } from 'svelte';
  import { Badge, Button, Card, Input, Modal, Spinner } from '../lib/components';
  import { tenantsApi } from '../lib/api';
  import { addToast } from '../lib/stores';
  import type { Tenant } from '../lib/types';

  let tenants: Tenant[] = [];
  let loading = true;
  let error = '';
  let search = '';

  let showCreateModal = false;
  let creating = false;
  let createError = '';
  let createForm = {
    subdomain: '',
    company_name: '',
    admin_email: '',
    admin_password: '',
    plan: 'basic' as 'basic' | 'pro' | 'enterprise',
  };

  let showPasswordModal = false;
  let passwordLoading = false;
  let passwordError = '';
  let passwordTenant: Tenant | null = null;
  let newPassword = '';

  let actionLoadingTenant = '';

  async function loadTenants() {
    loading = true;
    error = '';
    try {
      const response = await tenantsApi.list();
      tenants = response.items;
    } catch (err) {
      error = err instanceof Error ? err.message : 'No se pudo cargar tenants';
      addToast(error, 'error');
    } finally {
      loading = false;
    }
  }

  onMount(async () => {
    await loadTenants();
  });

  function statusVariant(status: string) {
    if (status === 'active') return 'success';
    if (status === 'provisioning' || status === 'pending') return 'warning';
    if (status === 'suspended' || status === 'payment_failed') return 'error';
    return 'secondary';
  }

  function planVariant(plan: string) {
    if (plan === 'enterprise') return 'enterprise';
    if (plan === 'pro') return 'pro';
    return 'basic';
  }

  async function handleCreateTenant() {
    createError = '';

    if (!createForm.subdomain.trim()) {
      createError = 'El subdominio es obligatorio';
      return;
    }

    creating = true;
    try {
      await tenantsApi.create({
        subdomain: createForm.subdomain.trim(),
        company_name: createForm.company_name.trim() || createForm.subdomain.trim(),
        admin_email: createForm.admin_email.trim() || undefined,
        admin_password: createForm.admin_password || undefined,
        plan: createForm.plan,
        use_fast_method: true,
      });

      showCreateModal = false;
      createForm = {
        subdomain: '',
        company_name: '',
        admin_email: '',
        admin_password: '',
        plan: 'basic',
      };
      addToast('Tenant creado correctamente', 'success');
      await loadTenants();
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'No se pudo crear tenant', 'error');
    } finally {
      creating = false;
    }
  }

  async function toggleSuspend(tenant: Tenant) {
    actionLoadingTenant = tenant.subdomain;
    try {
      await tenantsApi.suspend({
        subdomain: tenant.subdomain,
        suspend: tenant.status === 'active',
      });
      addToast(tenant.status === 'active' ? 'Tenant suspendido' : 'Tenant reactivado', 'success');
      await loadTenants();
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'No se pudo cambiar estado', 'error');
    } finally {
      actionLoadingTenant = '';
    }
  }

  function openPasswordModal(tenant: Tenant) {
    passwordTenant = tenant;
    newPassword = '';
    passwordError = '';
    showPasswordModal = true;
  }

  async function handleChangePassword() {
    if (!passwordTenant) return;
    if (newPassword.length < 6) {
      passwordError = 'La nueva contraseña debe tener al menos 6 caracteres';
      return;
    }

    passwordLoading = true;
    passwordError = '';

    try {
      await tenantsApi.changePassword({
        subdomain: passwordTenant.subdomain,
        new_password: newPassword,
      });
      showPasswordModal = false;
      passwordTenant = null;
      newPassword = '';
      addToast('Password actualizado correctamente', 'success');
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'No se pudo cambiar la contraseña', 'error');
    } finally {
      passwordLoading = false;
    }
  }

  $: filteredTenants = tenants.filter((tenant) => {
    const target = `${tenant.company_name} ${tenant.email} ${tenant.subdomain}`.toLowerCase();
    return target.includes(search.toLowerCase().trim());
  });
</script>

<div class="p-6 lg:p-8 space-y-6">
  <div class="flex flex-col md:flex-row gap-4 md:items-center md:justify-between">
    <div>
      <h1 class="text-2xl font-bold text-white">Tenants</h1>
      <p class="text-secondary-400 mt-1">Listado operativo de clientes/tenants y acciones de provisioning</p>
    </div>

    <Button variant="accent" on:click={() => (showCreateModal = true)}>Nuevo tenant</Button>
  </div>

  <Card>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
      <Input label="Buscar" placeholder="empresa, email, subdominio" bind:value={search} />
      <div class="rounded-lg bg-surface-highlight border border-surface-border p-4">
        <p class="text-xs uppercase tracking-wider text-secondary-500">Total tenants</p>
        <p class="text-2xl font-bold text-white mt-1">{tenants.length}</p>
      </div>
      <div class="rounded-lg bg-surface-highlight border border-surface-border p-4">
        <p class="text-xs uppercase tracking-wider text-secondary-500">Activos</p>
        <p class="text-2xl font-bold text-white mt-1">{tenants.filter((t) => t.status === 'active').length}</p>
      </div>
    </div>
  </Card>

  <Card title="Listado de tenants" subtitle="Endpoints: /api/tenants + /api/provisioning/tenant/*" padding="none">
    {#if loading}
      <div class="py-14 flex justify-center">
        <Spinner size="lg" />
      </div>
    {:else if error}
      <div class="p-6 text-error text-sm">{error}</div>
    {:else}
      <div class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr>
              <th>Tenant</th>
              <th>Plan</th>
              <th>Estado</th>
              <th>Servidor</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {#each filteredTenants as tenant}
              <tr>
                <td>
                  <div>
                    <p class="font-medium text-white">{tenant.company_name || tenant.subdomain}</p>
                    <p class="text-xs text-secondary-500">{tenant.email}</p>
                    <p class="text-xs text-secondary-600">{tenant.subdomain}.sajet.us</p>
                  </div>
                </td>
                <td>
                  <Badge variant={planVariant(tenant.plan)}>{tenant.plan || 'basic'}</Badge>
                </td>
                <td>
                  <Badge variant={statusVariant(tenant.status)} dot>{tenant.status}</Badge>
                </td>
                <td class="text-secondary-300">{tenant.server || '-'}</td>
                <td>
                  <div class="flex flex-wrap gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      on:click={() => openPasswordModal(tenant)}
                      disabled={actionLoadingTenant === tenant.subdomain}
                    >
                      Password
                    </Button>
                    <Button
                      variant={tenant.status === 'active' ? 'danger' : 'primary'}
                      size="sm"
                      on:click={() => toggleSuspend(tenant)}
                      disabled={actionLoadingTenant === tenant.subdomain}
                    >
                      {tenant.status === 'active' ? 'Suspender' : 'Reactivar'}
                    </Button>
                  </div>
                </td>
              </tr>
            {:else}
              <tr>
                <td colspan="5" class="text-center text-secondary-500 py-8">No hay tenants que coincidan con la búsqueda</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </Card>
</div>

<Modal
  bind:isOpen={showCreateModal}
  title="Crear tenant"
  confirmText="Crear"
  on:confirm={handleCreateTenant}
  on:close={() => {
    showCreateModal = false;
    createError = '';
  }}
  loading={creating}
>
  <div class="space-y-4">
    {#if createError}
      <div class="p-3 rounded-lg bg-error/10 border border-error/20 text-sm text-error">{createError}</div>
    {/if}

    <Input label="Subdominio" placeholder="miempresa" bind:value={createForm.subdomain} required />
    <Input label="Empresa" placeholder="Mi Empresa SRL" bind:value={createForm.company_name} />
    <Input label="Email admin" type="email" placeholder="admin@empresa.com" bind:value={createForm.admin_email} />
    <Input label="Password admin" type="password" placeholder="******" bind:value={createForm.admin_password} />

    <div class="space-y-1.5">
      <label class="label" for="tenant-plan">Plan</label>
      <select id="tenant-plan" bind:value={createForm.plan} class="input">
        <option value="basic">Basic</option>
        <option value="pro">Pro</option>
        <option value="enterprise">Enterprise</option>
      </select>
    </div>
  </div>
</Modal>

<Modal
  bind:isOpen={showPasswordModal}
  title={`Cambiar password: ${passwordTenant?.subdomain || ''}`}
  confirmText="Actualizar"
  on:confirm={handleChangePassword}
  on:close={() => {
    showPasswordModal = false;
    passwordError = '';
  }}
  loading={passwordLoading}
>
  <div class="space-y-4">
    {#if passwordError}
      <div class="p-3 rounded-lg bg-error/10 border border-error/20 text-sm text-error">{passwordError}</div>
    {/if}
    <Input label="Nueva contraseña" type="password" bind:value={newPassword} required />
  </div>
</Modal>
