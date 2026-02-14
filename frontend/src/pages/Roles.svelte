<script lang="ts">
  import { onMount } from 'svelte';
  import { Badge, Button, Card, Input, Modal, Spinner } from '../lib/components';
  import { rolesApi } from '../lib/api';
  import type { Role } from '../lib/types';
  import { formatDate } from '../lib/utils/formatters';

  let roles: Role[] = [];
  let loading = true;
  let saving = false;
  let error = '';
  let formError = '';
  let showModal = false;
  let editingRole: Role | null = null;

  let roleForm = {
    name: '',
    description: '',
    permissions: '',
  };

  async function loadRoles() {
    loading = true;
    error = '';
    try {
      const response = await rolesApi.listRoles();
      roles = response.items || [];
    } catch (err) {
      error = err instanceof Error ? err.message : 'No se pudieron cargar roles';
    } finally {
      loading = false;
    }
  }

  function openCreate() {
    editingRole = null;
    formError = '';
    roleForm = { name: '', description: '', permissions: '' };
    showModal = true;
  }

  function openEdit(role: Role) {
    editingRole = role;
    formError = '';
    roleForm = {
      name: role.name,
      description: role.description || '',
      permissions: (role.permissions || []).join(', '),
    };
    showModal = true;
  }

  function parsePermissions(raw: string): string[] {
    return raw
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
  }

  async function saveRole() {
    formError = '';
    if (!roleForm.name.trim()) {
      formError = 'El nombre del rol es obligatorio';
      return;
    }

    saving = true;
    try {
      const payload = {
        name: roleForm.name.trim(),
        description: roleForm.description.trim(),
        permissions: parsePermissions(roleForm.permissions),
      };

      if (editingRole) {
        await rolesApi.updateRole(editingRole.id, payload);
      } else {
        await rolesApi.createRole(payload);
      }

      showModal = false;
      editingRole = null;
      await loadRoles();
    } catch (err) {
      formError = err instanceof Error ? err.message : 'No se pudo guardar rol';
    } finally {
      saving = false;
    }
  }

  onMount(loadRoles);
</script>

<div class="p-6 lg:p-8 space-y-6">
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold text-white">Roles</h1>
      <p class="text-secondary-400 mt-1">Gestion de roles y permisos para administracion</p>
    </div>
    <div class="flex gap-2">
      <Button variant="secondary" on:click={loadRoles}>Actualizar</Button>
      <Button variant="accent" on:click={openCreate}>Nuevo rol</Button>
    </div>
  </div>

  {#if error}
    <Card><p class="text-sm text-error">{error}</p></Card>
  {/if}

  <Card title="Catalogo de roles" subtitle="/api/roles" padding="none">
    {#if loading}
      <div class="py-12 flex justify-center"><Spinner size="lg" /></div>
    {:else}
      <div class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr>
              <th>Rol</th>
              <th>Descripcion</th>
              <th>Permisos</th>
              <th>Tipo</th>
              <th>Actualizado</th>
              <th>Accion</th>
            </tr>
          </thead>
          <tbody>
            {#each roles as role}
              <tr>
                <td class="font-medium text-white">{role.name}</td>
                <td class="text-secondary-300">{role.description || '-'}</td>
                <td>
                  <div class="flex flex-wrap gap-1">
                    {#each role.permissions as permission}
                      <Badge variant="secondary">{permission}</Badge>
                    {:else}
                      <span class="text-secondary-500 text-xs">Sin permisos</span>
                    {/each}
                  </div>
                </td>
                <td><Badge variant={role.system ? 'info' : 'primary'}>{role.system ? 'system' : 'custom'}</Badge></td>
                <td class="text-secondary-300">{formatDate(role.updated_at)}</td>
                <td>
                  <Button size="sm" variant="secondary" on:click={() => openEdit(role)}>Editar</Button>
                </td>
              </tr>
            {:else}
              <tr>
                <td colspan="6" class="text-center text-secondary-500 py-8">No hay roles disponibles</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </Card>
</div>

<Modal
  bind:isOpen={showModal}
  title={editingRole ? `Editar rol: ${editingRole.name}` : 'Nuevo rol'}
  confirmText={editingRole ? 'Guardar cambios' : 'Crear rol'}
  on:confirm={saveRole}
  on:close={() => {
    showModal = false;
    editingRole = null;
    formError = '';
  }}
  loading={saving}
  size="lg"
>
  <div class="space-y-4">
    {#if formError}
      <div class="rounded-lg border border-error/30 bg-error/10 px-3 py-2 text-sm text-error">{formError}</div>
    {/if}

    <Input label="Nombre" bind:value={roleForm.name} placeholder="operator_finance" required />
    <Input label="Descripcion" bind:value={roleForm.description} placeholder="Rol para operaciones financieras" />
    <Input
      label="Permisos (separados por coma)"
      bind:value={roleForm.permissions}
      placeholder="billing:read, tenants:read"
      hint="Formato sugerido: modulo:accion"
    />
  </div>
</Modal>
