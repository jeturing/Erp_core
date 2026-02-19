<script lang="ts">
  import { onMount } from 'svelte';
  import { tenantsApi, api } from '../lib/api';
  import { partnersApi } from '../lib/api/partners';
  import { toasts } from '../lib/stores/toast';
  import { formatDate } from '../lib/utils/formatters';
  import { Plus, RefreshCw, Search } from 'lucide-svelte';
  import type { Tenant } from '../lib/types';
  import type { PartnerItem } from '../lib/types';


  let tenants = $state<Tenant[]>([]);
  let partners = $state<PartnerItem[]>([]);
  let loading = $state(true);
  let searchQuery = $state('');
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
      toasts.error(e?.message ?? 'Error al crear tenant');
    } finally {
      formLoading = false;
    }
  }

  async function handleChangePassword(subdomain: string) {
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
      await tenantsApi.changePassword({ subdomain, new_password: rowPassword });
      toasts.success('Contraseña actualizada');
      expandedPasswordRow = null;
      rowPassword = '';
      rowConfirmPassword = '';
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al cambiar contraseña');
    } finally {
      rowPasswordLoading = false;
    }
  }

  async function handleSuspend(tenant: Tenant) {
    const isActive = tenant.status === 'active';
    const action = isActive ? 'suspender' : 'reactivar';
    if (!window.confirm(`¿Deseas ${action} el tenant "${tenant.subdomain}"?`)) return;
    try {
      await tenantsApi.suspend({ subdomain: tenant.subdomain, suspend: isActive, server: tenant.server });
      toasts.success(`Tenant ${isActive ? 'suspendido' : 'reactivado'}`);
      await loadTenants();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al actualizar estado');
    }
  }

  async function handleDelete(tenant: Tenant) {
    if (!window.confirm(`¿Eliminar permanentemente el tenant "${tenant.subdomain}"? Esta acción no se puede deshacer.`)) return;
    try {
      await api.delete(`/api/tenants/${tenant.subdomain}?confirm=true`);
      toasts.success('Tenant eliminado');
      await loadTenants();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al eliminar tenant');
    }
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

  let filteredTenants = $derived(
    tenants.filter(t => {
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      return (
        t.subdomain?.toLowerCase().includes(q) ||
        t.email?.toLowerCase().includes(q) ||
        t.company_name?.toLowerCase().includes(q)
      );
    })
  );

  let totalTenants = $derived(tenants.length);
  let activeTenants = $derived(tenants.filter(t => t.status === 'active').length);

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
            <input id="f-password" class="input w-full px-3 py-2" type="password" bind:value={formPassword} placeholder="••••••••" required />
          </div>
          <div>
            <label class="label" for="f-confirm">Confirmar contraseña</label>
            <input id="f-confirm" class="input w-full px-3 py-2" type="password" bind:value={formConfirmPassword} placeholder="••••••••" required />
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
  </div>

  <!-- Search -->
  <div class="relative">
    <Search size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
    <input
      class="input w-full pl-9 pr-3 py-2"
      type="text"
      placeholder="Buscar por subdominio, email o empresa..."
      bind:value={searchQuery}
    />
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
          {#each filteredTenants as tenant (tenant.id)}
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
                    onclick={() => handleSuspend(tenant)}
                  >
                    {tenant.status === 'active' ? 'SUSPENDER' : 'REACTIVAR'}
                  </button>
                  <button
                    class="btn-danger btn-sm"
                    onclick={() => handleDelete(tenant)}
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
                        onclick={() => handleChangePassword(tenant.subdomain)}
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
</div>
