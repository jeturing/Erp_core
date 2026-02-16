<script lang="ts">
  import { onMount } from 'svelte';
  import { Plus, Edit, Shield, Lock } from 'lucide-svelte';
  import { rolesApi } from '../lib/api/roles';
  import type { Role } from '../lib/api/roles';
  import { Modal } from '../lib/components';
  import { toasts } from '../lib/stores/toast';
  import { formatDate } from '../lib/utils/formatters';

  let roles: Role[] = [];
  let total = 0;
  let loading = false;

  // Modal state
  let modalOpen = false;
  let modalLoading = false;
  let editingRole: Role | null = null;

  // Form fields
  let formName = '';
  let formDescription = '';
  let formPermissions = '';

  async function loadRoles() {
    loading = true;
    try {
      const resp = await rolesApi.list();
      roles = resp.roles || [];
      total = resp.total || 0;
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error al cargar roles');
    } finally {
      loading = false;
    }
  }

  function openCreateModal() {
    editingRole = null;
    formName = '';
    formDescription = '';
    formPermissions = '';
    modalOpen = true;
  }

  function openEditModal(role: Role) {
    if (role.is_system) return;
    editingRole = role;
    formName = role.name;
    formDescription = role.description || '';
    formPermissions = (role.permissions || []).join('\n');
    modalOpen = true;
  }

  function parsePermissions(raw: string): string[] {
    return raw
      .split(/[\n,]/)
      .map(p => p.trim())
      .filter(p => p.length > 0);
  }

  async function handleSave() {
    if (!formName.trim()) {
      toasts.warning('El nombre del rol es requerido');
      return;
    }

    modalLoading = true;
    const permissions = parsePermissions(formPermissions);

    try {
      if (editingRole) {
        await rolesApi.update(editingRole.id, {
          name: formName.trim(),
          description: formDescription.trim() || undefined,
          permissions,
        });
        toasts.success(`Rol "${formName}" actualizado correctamente`);
      } else {
        await rolesApi.create({
          name: formName.trim(),
          description: formDescription.trim() || undefined,
          permissions,
        });
        toasts.success(`Rol "${formName}" creado correctamente`);
      }
      modalOpen = false;
      await loadRoles();
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error al guardar el rol');
    } finally {
      modalLoading = false;
    }
  }

  function getVisiblePermissions(perms: string[]): string[] {
    return perms.slice(0, 3);
  }

  onMount(loadRoles);
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="page-title">GESTIÓN DE ROLES</h1>
      <p class="page-subtitle mt-1">Administración de roles y permisos del sistema</p>
    </div>
    <button class="btn btn-primary btn-sm" on:click={openCreateModal}>
      <Plus class="w-3.5 h-3.5 mr-1.5 inline" />
      NUEVO ROL
    </button>
  </div>

  <!-- Stats -->
  <div class="grid grid-cols-2 sm:grid-cols-3 gap-4">
    <div class="stat-card">
      <div class="stat-value">{total}</div>
      <div class="stat-label">Total Roles</div>
    </div>
    <div class="stat-card">
      <div class="stat-value text-amber-600">{roles.filter(r => r.is_system).length}</div>
      <div class="stat-label">Roles Sistema</div>
    </div>
    <div class="stat-card">
      <div class="stat-value text-text-primary">{roles.filter(r => !r.is_system).length}</div>
      <div class="stat-label">Roles Personalizados</div>
    </div>
  </div>

  <!-- Table -->
  <div class="card p-0 overflow-hidden">
    {#if loading}
      <div class="py-16 flex items-center justify-center">
        <div class="text-sm text-gray-500 animate-pulse">Cargando roles...</div>
      </div>
    {:else if roles.length === 0}
      <div class="py-16 flex flex-col items-center justify-center gap-2">
        <Shield class="w-8 h-8 text-border-light" />
        <p class="text-sm text-gray-500">No hay roles definidos</p>
      </div>
    {:else}
      <div class="overflow-x-auto">
        <table class="table w-full">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Descripción</th>
              <th>Permisos</th>
              <th>Tipo</th>
              <th>Creado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {#each roles as role}
              <tr>
                <td>
                  <div class="flex items-center gap-2">
                    {#if role.is_system}
                      <Lock class="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
                    {:else}
                      <Shield class="w-3.5 h-3.5 text-gray-500 flex-shrink-0" />
                    {/if}
                    <span class="text-sm font-semibold text-text-primary">{role.name}</span>
                  </div>
                </td>
                <td>
                  <span class="text-sm text-text-secondary">
                    {#if role.description}{role.description}{:else}<span class="text-gray-500 italic text-xs">Sin descripción</span>{/if}
                  </span>
                </td>
                <td>
                  <div class="flex items-center gap-1.5 flex-wrap">
                    {#if role.permissions && role.permissions.length > 0}
                      {#each getVisiblePermissions(role.permissions) as perm}
                        <span class="badge badge-info text-[9px]">{perm}</span>
                      {/each}
                      {#if role.permissions.length > 3}
                        <span class="badge badge-neutral text-[9px]">+{role.permissions.length - 3} más</span>
                      {/if}
                      <span class="text-[10px] text-gray-500 ml-1">({role.permissions.length})</span>
                    {:else}
                      <span class="text-xs text-gray-500 italic">Sin permisos</span>
                    {/if}
                  </div>
                </td>
                <td>
                  {#if role.is_system}
                    <span class="badge badge-warning">Sistema</span>
                  {:else}
                    <span class="badge badge-neutral">Custom</span>
                  {/if}
                </td>
                <td>
                  <span class="text-xs text-text-secondary">{formatDate(role.created_at)}</span>
                </td>
                <td>
                  <button
                    class="btn btn-secondary btn-sm {role.is_system ? 'opacity-40 cursor-not-allowed' : ''}"
                    on:click={() => openEditModal(role)}
                    disabled={role.is_system}
                    title={role.is_system ? 'Los roles del sistema no se pueden editar' : 'Editar rol'}
                  >
                    <Edit class="w-3 h-3 mr-1 inline" />
                    EDITAR
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

<!-- Create/Edit Modal -->
<Modal
  isOpen={modalOpen}
  title={editingRole ? `Editar Rol: ${editingRole.name}` : 'Nuevo Rol'}
  confirmText={editingRole ? 'GUARDAR CAMBIOS' : 'CREAR ROL'}
  loading={modalLoading}
  size="md"
  on:close={() => { modalOpen = false; }}
  on:confirm={handleSave}
>
  <div class="space-y-4">
    <div>
      <label class="label block mb-1.5" for="role-name">Nombre del Rol</label>
      <input
        id="role-name"
        class="input w-full px-3 py-2 text-sm rounded"
        type="text"
        placeholder="ej. Supervisor de Ventas"
        bind:value={formName}
        disabled={modalLoading}
      />
    </div>

    <div>
      <label class="label block mb-1.5" for="role-desc">Descripción</label>
      <input
        id="role-desc"
        class="input w-full px-3 py-2 text-sm rounded"
        type="text"
        placeholder="Descripción opcional del rol"
        bind:value={formDescription}
        disabled={modalLoading}
      />
    </div>

    <div>
      <label class="label block mb-1.5" for="role-perms">Permisos</label>
      <textarea
        id="role-perms"
        class="input w-full px-3 py-2 text-sm rounded font-mono resize-none"
        rows="6"
        placeholder="Un permiso por línea o separados por coma:&#10;read:tenants&#10;write:tenants&#10;admin:billing"
        bind:value={formPermissions}
        disabled={modalLoading}
      ></textarea>
      <p class="text-[10px] text-gray-500 mt-1">Un permiso por línea o separados por coma.</p>
    </div>

    {#if formPermissions}
      <div>
        <span class="label block mb-1.5">Vista previa de permisos</span>
        <div class="flex flex-wrap gap-1.5 p-3 bg-bg-page rounded border border-border-light min-h-[40px]">
          {#each parsePermissions(formPermissions) as perm}
            <span class="badge badge-info text-[10px]">{perm}</span>
          {/each}
        </div>
      </div>
    {/if}
  </div>
</Modal>
