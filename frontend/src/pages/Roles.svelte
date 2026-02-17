<script lang="ts">
  import { onMount } from 'svelte';
  import { rolesApi } from '../lib/api';
  import { toasts } from '../lib/stores/toast';
  import { formatDate } from '../lib/utils/formatters';
  import { Lock, Plus } from 'lucide-svelte';

  interface Role {
    id: string | number;
    name: string;
    description?: string;
    permissions: string[];
    is_system?: boolean;
    created_at?: string;
  }

  let roles = $state<Role[]>([]);
  let loading = $state(true);
  let showAddForm = $state(false);

  // Add form
  let addName = $state('');
  let addDescription = $state('');
  let addPermissions = $state('');
  let addLoading = $state(false);

  // Edit state - inline per row
  let editingRoleId = $state<string | number | null>(null);
  let editName = $state('');
  let editDescription = $state('');
  let editPermissions = $state('');
  let editLoading = $state(false);

  async function loadRoles() {
    loading = true;
    try {
      const data = await rolesApi.list();
      roles = data.roles ?? [];
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al cargar roles');
    } finally {
      loading = false;
    }
  }

  async function handleCreate(e: Event) {
    e.preventDefault();
    addLoading = true;
    try {
      const permissions = addPermissions
        .split('\n')
        .map(p => p.trim())
        .filter(Boolean);
      await rolesApi.create({ name: addName, description: addDescription, permissions });
      toasts.success('Rol creado');
      showAddForm = false;
      addName = '';
      addDescription = '';
      addPermissions = '';
      await loadRoles();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al crear rol');
    } finally {
      addLoading = false;
    }
  }

  function startEdit(role: Role) {
    editingRoleId = role.id;
    editName = role.name;
    editDescription = role.description ?? '';
    editPermissions = (role.permissions ?? []).join('\n');
  }

  function cancelEdit() {
    editingRoleId = null;
    editName = '';
    editDescription = '';
    editPermissions = '';
  }

  async function handleUpdate(id: string | number) {
    editLoading = true;
    try {
      const permissions = editPermissions
        .split('\n')
        .map(p => p.trim())
        .filter(Boolean);
      await rolesApi.update(id as number, { name: editName, description: editDescription, permissions });
      toasts.success('Rol actualizado');
      cancelEdit();
      await loadRoles();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al actualizar rol');
    } finally {
      editLoading = false;
    }
  }

  onMount(loadRoles);
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="page-title">GESTIÓN DE ROLES</h1>
      <p class="page-subtitle">Control de permisos y acceso</p>
    </div>
    <button class="btn-accent px-4 py-2 flex items-center gap-2" onclick={() => showAddForm = !showAddForm}>
      <Plus size={14} />
      NUEVO ROL
    </button>
  </div>

  <!-- Inline Add Form -->
  {#if showAddForm}
    <div class="card border-l-2 border-l-terracotta">
      <h3 class="section-heading mb-5">NUEVO ROL</h3>
      <form onsubmit={handleCreate} class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="label" for="f-name">Nombre</label>
            <input id="f-name" class="input w-full px-3 py-2" type="text" bind:value={addName} placeholder="editor" required />
          </div>
          <div>
            <label class="label" for="f-desc">Descripción</label>
            <input id="f-desc" class="input w-full px-3 py-2" type="text" bind:value={addDescription} placeholder="Descripción del rol" />
          </div>
        </div>
        <div>
          <label class="label" for="f-perms">Permisos (uno por línea)</label>
          <textarea
            id="f-perms"
            class="input w-full px-3 py-2 font-mono text-xs"
            rows="5"
            bind:value={addPermissions}
            placeholder="tenants:read&#10;tenants:write&#10;billing:read"
          ></textarea>
        </div>
        <div class="flex gap-3 pt-2">
          <button type="button" class="btn-secondary px-4 py-2" onclick={() => showAddForm = false}>CANCELAR</button>
          <button type="submit" class="btn-accent px-4 py-2 disabled:opacity-60" disabled={addLoading}>
            {addLoading ? 'GUARDANDO...' : 'GUARDAR'}
          </button>
        </div>
      </form>
    </div>
  {/if}

  <!-- Table -->
  <div class="card p-0 overflow-hidden">
    {#if loading}
      <div class="p-8 text-center text-gray-500 text-sm">Cargando roles...</div>
    {:else if roles.length === 0}
      <div class="p-8 text-center text-gray-500 text-sm">No hay roles definidos</div>
    {:else}
      <table class="table w-full">
        <thead>
          <tr>
            <th>NOMBRE</th>
            <th>DESCRIPCIÓN</th>
            <th>PERMISOS</th>
            <th>TIPO</th>
            <th>CREADO</th>
            <th>ACCIONES</th>
          </tr>
        </thead>
        <tbody>
          {#each roles as role (role.id)}
            <tr>
              <td>
                <div class="flex items-center gap-2">
                  {#if role.is_system}
                    <Lock size={12} class="text-gray-400 shrink-0" />
                  {/if}
                  <span class="font-medium text-sm">{role.name}</span>
                </div>
              </td>
              <td class="text-sm text-gray-500">{role.description ?? '-'}</td>
              <td>
                <div class="flex flex-wrap gap-1">
                  {#each (role.permissions ?? []).slice(0, 3) as perm}
                    <span class="badge-neutral text-[10px]">{perm}</span>
                  {/each}
                  {#if (role.permissions ?? []).length > 3}
                    <span class="text-xs text-gray-400">+{(role.permissions ?? []).length - 3} más</span>
                  {/if}
                </div>
              </td>
              <td>
                {#if role.is_system}
                  <span class="badge-info">Sistema</span>
                {:else}
                  <span class="badge-neutral">Custom</span>
                {/if}
              </td>
              <td class="text-sm text-gray-500">{role.created_at ? formatDate(role.created_at) : '-'}</td>
              <td>
                {#if !role.is_system}
                  <button class="btn-secondary btn-sm" onclick={() => startEdit(role)}>EDITAR</button>
                {/if}
              </td>
            </tr>
            <!-- Inline edit row -->
            {#if editingRoleId === role.id}
              <tr class="bg-bg-page">
                <td colspan="6" class="py-4 px-6">
                  <div class="space-y-4">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label class="label" for="e-name-{role.id}">Nombre</label>
                        <input id="e-name-{role.id}" class="input w-full px-3 py-2" type="text" bind:value={editName} required />
                      </div>
                      <div>
                        <label class="label" for="e-desc-{role.id}">Descripción</label>
                        <input id="e-desc-{role.id}" class="input w-full px-3 py-2" type="text" bind:value={editDescription} />
                      </div>
                    </div>
                    <div>
                      <label class="label" for="e-perms-{role.id}">Permisos (uno por línea)</label>
                      <textarea
                        id="e-perms-{role.id}"
                        class="input w-full px-3 py-2 font-mono text-xs"
                        rows="5"
                        bind:value={editPermissions}
                      ></textarea>
                    </div>
                    <div class="flex gap-3">
                      <button class="btn-secondary btn-sm" onclick={cancelEdit}>CANCELAR</button>
                      <button
                        class="btn-accent btn-sm disabled:opacity-60"
                        disabled={editLoading}
                        onclick={() => handleUpdate(role.id)}
                      >
                        {editLoading ? 'GUARDANDO...' : 'GUARDAR'}
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
