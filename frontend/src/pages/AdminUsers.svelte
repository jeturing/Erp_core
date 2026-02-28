<script lang="ts">
  import { onMount } from 'svelte';
  import { adminUsersApi } from '../lib/api/adminUsers';
  import type { AdminUserItem } from '../lib/api/adminUsers';
  import { toasts } from '../lib/stores/toast';
  import { formatDate } from '../lib/utils/formatters';
  import { Plus, Shield, Eye, Wrench, UserX, UserCheck, KeyRound, Edit3, Trash2 } from 'lucide-svelte';

  let users = $state<AdminUserItem[]>([]);
  let loading = $state(true);

  // Modal form
  let showForm = $state(false);
  let formMode = $state<'create' | 'edit'>('create');
  let editId = $state<number | null>(null);
  let formEmail = $state('');
  let formDisplayName = $state('');
  let formPassword = $state('');
  let formRole = $state<'admin' | 'operator' | 'viewer' | 'segrd-admin' | 'segrd-user'>('admin');
  let formNotes = $state('');
  let formLoading = $state(false);

  // Password reset
  let resetId = $state<number | null>(null);
  let resetPassword = $state('');
  let resetLoading = $state(false);

  const roleLabels: Record<string, string> = {
    admin: 'Administrador',
    operator: 'Operador',
    viewer: 'Visor',
    'segrd-admin': 'SEGRD Admin',
    'segrd-user': 'SEGRD User',
  };

  const roleIcons: Record<string, any> = {
    admin: Shield,
    operator: Wrench,
    viewer: Eye,
    'segrd-admin': Shield,
    'segrd-user': UserCheck,
  };

  const roleColors: Record<string, string> = {
    admin: 'bg-terracotta/20 text-terracotta',
    operator: 'bg-blue-500/20 text-blue-400',
    viewer: 'bg-gray-500/20 text-gray-400',
    'segrd-admin': 'bg-emerald-500/20 text-emerald-300',
    'segrd-user': 'bg-cyan-500/20 text-cyan-300',
  };

  async function loadUsers() {
    loading = true;
    try {
      const data = await adminUsersApi.list();
      users = data.items ?? [];
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al cargar usuarios admin');
    } finally {
      loading = false;
    }
  }

  function openCreate() {
    formMode = 'create';
    editId = null;
    formEmail = '';
    formDisplayName = '';
    formPassword = '';
    formRole = 'admin';
    formNotes = '';
    showForm = true;
  }

  function openEdit(user: AdminUserItem) {
    formMode = 'edit';
    editId = user.id;
    formEmail = user.email;
    formDisplayName = user.display_name;
    formPassword = '';
    formRole = user.role;
    formNotes = user.notes || '';
    showForm = true;
  }

  async function handleSubmit(e: Event) {
    e.preventDefault();
    formLoading = true;
    try {
      if (formMode === 'create') {
        if (!formEmail || !formDisplayName || !formPassword) {
          toasts.error('Email, nombre y contraseña son obligatorios');
          return;
        }
        await adminUsersApi.create({
          email: formEmail,
          display_name: formDisplayName,
          password: formPassword,
          role: formRole,
          notes: formNotes || undefined,
        });
        toasts.success('Usuario creado exitosamente');
      } else if (editId) {
        await adminUsersApi.update(editId, {
          display_name: formDisplayName,
          role: formRole,
          notes: formNotes || undefined,
        });
        toasts.success('Usuario actualizado');
      }
      showForm = false;
      await loadUsers();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error');
    } finally {
      formLoading = false;
    }
  }

  async function toggleActive(user: AdminUserItem) {
    const action = user.is_active ? 'desactivar' : 'activar';
    if (!window.confirm(`¿${action.charAt(0).toUpperCase() + action.slice(1)} al usuario "${user.display_name}"?`)) return;
    try {
      await adminUsersApi.update(user.id, { is_active: !user.is_active });
      toasts.success(`Usuario ${user.is_active ? 'desactivado' : 'activado'}`);
      await loadUsers();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error');
    }
  }

  async function handleResetPassword() {
    if (!resetId || !resetPassword) {
      toasts.error('Ingresa una contraseña');
      return;
    }
    resetLoading = true;
    try {
      await adminUsersApi.update(resetId, { new_password: resetPassword });
      toasts.success('Contraseña actualizada');
      resetId = null;
      resetPassword = '';
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error');
    } finally {
      resetLoading = false;
    }
  }

  let activeCount = $derived(users.filter(u => u.is_active).length);
  let adminCount = $derived(users.filter(u => u.role === 'admin' && u.is_active).length);

  onMount(loadUsers);
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="page-title">USUARIOS ADMIN</h1>
      <p class="page-subtitle">Gestión de administradores, operadores y visores de la plataforma</p>
    </div>
    <button class="btn-accent px-4 py-2 flex items-center gap-2" onclick={openCreate}>
      <Plus size={14} />
      NUEVO USUARIO
    </button>
  </div>

  <!-- Stats -->
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
    <div class="stat-card card">
      <div class="stat-value">{users.length}</div>
      <div class="stat-label">Total Usuarios</div>
    </div>
    <div class="stat-card card">
      <div class="stat-value">{activeCount}</div>
      <div class="stat-label">Activos</div>
    </div>
    <div class="stat-card card">
      <div class="stat-value">{adminCount}</div>
      <div class="stat-label">Admins</div>
    </div>
    <div class="stat-card card">
      <div class="stat-value">{users.length - activeCount}</div>
      <div class="stat-label">Inactivos</div>
    </div>
  </div>

  <!-- Table -->
  <div class="card p-0 overflow-hidden">
    {#if loading}
      <div class="p-8 text-center text-gray-500 text-sm">Cargando usuarios...</div>
    {:else if users.length === 0}
      <div class="p-8 text-center text-gray-500 text-sm">No hay usuarios administrativos registrados</div>
    {:else}
      <table class="table w-full">
        <thead>
          <tr>
            <th>USUARIO</th>
            <th>ROL</th>
            <th>ESTADO</th>
            <th>ÚLTIMO LOGIN</th>
            <th>LOGINS</th>
            <th>CREADO</th>
            <th>ACCIONES</th>
          </tr>
        </thead>
        <tbody>
          {#each users as user (user.id)}
            <tr class={user.is_active ? '' : 'opacity-50'}>
              <td>
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 {roleColors[user.role] ?? 'bg-gray-500/20'}">
                    <svelte:component this={roleIcons[user.role] ?? Shield} size={14} />
                  </div>
                  <div>
                    <div class="font-medium text-text-primary text-sm">{user.display_name}</div>
                    <div class="text-xs text-gray-500">{user.email}</div>
                  </div>
                </div>
              </td>
              <td>
                <span class="badge-neutral text-xs font-semibold uppercase">{roleLabels[user.role] ?? user.role}</span>
              </td>
              <td>
                {#if user.is_active}
                  <span class="badge-success">Activo</span>
                {:else}
                  <span class="badge-neutral">Inactivo</span>
                {/if}
              </td>
              <td class="text-sm text-gray-500">
                {user.last_login_at ? formatDate(user.last_login_at) : 'Nunca'}
              </td>
              <td class="text-sm text-gray-500 text-center">{user.login_count}</td>
              <td class="text-sm text-gray-500">{formatDate(user.created_at)}</td>
              <td>
                <div class="flex items-center gap-2 flex-wrap">
                  <button class="btn-secondary btn-sm" title="Editar" onclick={() => openEdit(user)}>
                    <Edit3 size={14} />
                  </button>
                  <button
                    class="btn-secondary btn-sm"
                    title="Cambiar contraseña"
                    onclick={() => { resetId = resetId === user.id ? null : user.id; resetPassword = ''; }}
                  >
                    <KeyRound size={14} />
                  </button>
                  <button
                    class={user.is_active ? 'btn-danger btn-sm' : 'btn-secondary btn-sm'}
                    title={user.is_active ? 'Desactivar' : 'Activar'}
                    onclick={() => toggleActive(user)}
                  >
                    {#if user.is_active}
                      <UserX size={14} />
                    {:else}
                      <UserCheck size={14} />
                    {/if}
                  </button>
                </div>
              </td>
            </tr>
            <!-- Password reset row -->
            {#if resetId === user.id}
              <tr class="bg-bg-page">
                <td colspan="7" class="py-4 px-6">
                  <div class="flex items-end gap-4 flex-wrap">
                    <div>
                      <label class="label" for="rp-{user.id}">Nueva contraseña para {user.display_name}</label>
                      <input
                        id="rp-{user.id}"
                        type="password"
                        class="input px-3 py-2 w-64"
                        placeholder="••••••••"
                        bind:value={resetPassword}
                      />
                    </div>
                    <div class="flex gap-2">
                      <button class="btn-secondary btn-sm" onclick={() => { resetId = null; resetPassword = ''; }}>CANCELAR</button>
                      <button class="btn-accent btn-sm disabled:opacity-60" disabled={resetLoading} onclick={handleResetPassword}>
                        {resetLoading ? 'GUARDANDO...' : 'GUARDAR'}
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

<!-- Create/Edit Modal -->
{#if showForm}
  <div class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" role="dialog">
    <div class="bg-charcoal rounded-xl border border-border-dark w-full max-w-md">
      <div class="flex items-center justify-between p-6 border-b border-border-dark">
        <h2 class="text-lg font-semibold text-text-light">
          {formMode === 'create' ? 'Nuevo Usuario Admin' : 'Editar Usuario Admin'}
        </h2>
        <button class="text-gray-400 hover:text-text-light" onclick={() => showForm = false}>✕</button>
      </div>

      <form class="p-6 space-y-4" onsubmit={handleSubmit}>
        <div>
          <label class="label" for="au-email">Email</label>
          <input
            id="au-email"
            class="input w-full px-3 py-2"
            type="email"
            bind:value={formEmail}
            placeholder="usuario@empresa.com"
            required
            disabled={formMode === 'edit'}
          />
        </div>

        <div>
          <label class="label" for="au-name">Nombre</label>
          <input
            id="au-name"
            class="input w-full px-3 py-2"
            type="text"
            bind:value={formDisplayName}
            placeholder="Nombre completo"
            required
          />
        </div>

        {#if formMode === 'create'}
          <div>
            <label class="label" for="au-pass">Contraseña</label>
            <input
              id="au-pass"
              class="input w-full px-3 py-2"
              type="password"
              bind:value={formPassword}
              placeholder="••••••••"
              required
            />
          </div>
        {/if}

        <div>
          <label class="label" for="au-role">Rol</label>
          <select id="au-role" class="input w-full px-3 py-2" bind:value={formRole}>
            <option value="admin">👑 Administrador — acceso total</option>
            <option value="operator">🔧 Operador — operación diaria</option>
            <option value="viewer">👁️ Visor — solo lectura</option>
            <option value="segrd-admin">🛡️ SEGRD Admin — integración SEGRD</option>
            <option value="segrd-user">👤 SEGRD User — integración SEGRD</option>
          </select>
        </div>

        <div>
          <label class="label" for="au-notes">Notas (opcional)</label>
          <textarea
            id="au-notes"
            class="input w-full px-3 py-2 resize-none"
            rows="2"
            bind:value={formNotes}
            placeholder="Notas internas..."
          ></textarea>
        </div>

        <div class="flex gap-3 pt-2">
          <button type="button" class="btn-secondary flex-1" onclick={() => showForm = false}>CANCELAR</button>
          <button type="submit" class="btn-accent flex-1 disabled:opacity-60" disabled={formLoading}>
            {formLoading ? 'GUARDANDO...' : formMode === 'create' ? 'CREAR USUARIO' : 'GUARDAR CAMBIOS'}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}
