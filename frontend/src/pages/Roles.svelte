<script lang="ts">
  import { onMount } from 'svelte';
  import { rolesApi } from '../lib/api';
  import type { Role, PermissionModule, RolePreset, AvailableTenant, AvailableUser } from '../lib/api/roles';
  import { toasts } from '../lib/stores/toast';
  import {
    Shield, Plus, Trash2, Edit3, X, ChevronDown, ChevronUp,
    Copy, Lock, Building2, Users, Check, Sparkles, ToggleLeft, ToggleRight,
    UserPlus, UserMinus, Mail
  } from 'lucide-svelte';

  // ── State ──
  let roles = $state<Role[]>([]);
  let permCatalog = $state<Record<string, PermissionModule>>({});
  let presets = $state<Record<string, RolePreset>>({});
  let availableTenants = $state<AvailableTenant[]>([]);
  let availableUsers = $state<AvailableUser[]>([]);
  let loading = $state(true);

  // ── Modal state ──
  let showModal = $state(false);
  let modalMode = $state<'create' | 'edit'>('create');
  let saving = $state(false);

  // ── Form fields ──
  let formName = $state('');
  let formDescription = $state('');
  let formColor = $state('#6b7280');
  let formPermissions = $state<Set<string>>(new Set());
  let formTenants = $state<Set<number>>(new Set());
  let formUsers = $state<Set<number>>(new Set());
  let editingRoleId = $state<number | null>(null);

  // ── UI toggles ──
  let expandedModules = $state<Set<string>>(new Set());
  let showPresets = $state(false);
  let confirmDeleteId = $state<number | null>(null);
  let showTenantPicker = $state(false);
  let showUserPicker = $state(false);
  let userSearchQuery = $state('');

  // ── Derived ──
  let sortedModules = $derived(Object.entries(permCatalog));
  let totalPermsAvailable = $derived(
    Object.values(permCatalog).reduce((sum, m) => sum + Object.keys(m.permissions).length, 0)
  );
  let filteredUsers = $derived(
    availableUsers.filter(u =>
      !userSearchQuery ||
      u.display_name.toLowerCase().includes(userSearchQuery.toLowerCase()) ||
      u.email.toLowerCase().includes(userSearchQuery.toLowerCase())
    )
  );

  const COLORS = [
    '#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#1abc9c',
    '#3498db', '#9b59b6', '#e91e63', '#00bcd4', '#795548',
    '#607d8b', '#6b7280',
  ];

  // ── Load data ──
  async function loadAll() {
    loading = true;
    try {
      const [rolesRes, catalogRes, presetsRes, tenantsRes, usersRes] = await Promise.all([
        rolesApi.list(),
        rolesApi.getPermissionsCatalog(),
        rolesApi.getPresets(),
        rolesApi.getAvailableTenants(),
        rolesApi.getAvailableUsers(),
      ]);
      roles = rolesRes.items ?? [];
      permCatalog = catalogRes.modules ?? {};
      presets = presetsRes.presets ?? {};
      availableTenants = tenantsRes.tenants ?? [];
      availableUsers = usersRes.users ?? [];
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al cargar datos');
    } finally {
      loading = false;
    }
  }

  // ── Modal helpers ──
  function openCreate() {
    modalMode = 'create';
    editingRoleId = null;
    formName = '';
    formDescription = '';
    formColor = '#6b7280';
    formPermissions = new Set();
    formTenants = new Set();
    formUsers = new Set();
    expandedModules = new Set();
    showPresets = true;
    showTenantPicker = false;
    showUserPicker = false;
    userSearchQuery = '';
    showModal = true;
  }

  function openEdit(role: Role) {
    modalMode = 'edit';
    editingRoleId = role.id;
    formName = role.name;
    formDescription = role.description ?? '';
    formColor = role.color ?? '#6b7280';
    formPermissions = new Set(role.permissions ?? []);
    formTenants = new Set(role.assigned_tenants ?? []);
    formUsers = new Set(role.assigned_users ?? []);
    expandedModules = new Set();
    showPresets = false;
    showTenantPicker = false;
    showUserPicker = false;
    userSearchQuery = '';
    showModal = true;
  }

  function closeModal() {
    showModal = false;
    editingRoleId = null;
  }

  // ── Permission toggle helpers ──
  function togglePerm(perm: string) {
    const next = new Set(formPermissions);
    if (next.has(perm)) next.delete(perm);
    else next.add(perm);
    formPermissions = next;
  }

  function toggleModule(moduleKey: string) {
    const mod = permCatalog[moduleKey];
    if (!mod) return;
    const modPerms = Object.keys(mod.permissions);
    const allOn = modPerms.every(p => formPermissions.has(p));
    const next = new Set(formPermissions);
    if (allOn) {
      modPerms.forEach(p => next.delete(p));
    } else {
      modPerms.forEach(p => next.add(p));
    }
    formPermissions = next;
  }

  function toggleExpandModule(key: string) {
    const next = new Set(expandedModules);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    expandedModules = next;
  }

  function moduleStatus(moduleKey: string): 'all' | 'partial' | 'none' {
    const mod = permCatalog[moduleKey];
    if (!mod) return 'none';
    const modPerms = Object.keys(mod.permissions);
    const count = modPerms.filter(p => formPermissions.has(p)).length;
    if (count === 0) return 'none';
    if (count === modPerms.length) return 'all';
    return 'partial';
  }

  function applyPreset(key: string) {
    const preset = presets[key];
    if (!preset) return;
    formName = preset.name;
    formDescription = preset.description;
    formColor = preset.color;
    formPermissions = new Set(preset.permissions);
    showPresets = false;
    toasts.success(`Plantilla "${preset.name}" aplicada`);
  }

  // ── Tenant helpers ──
  function toggleTenant(id: number) {
    const next = new Set(formTenants);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    formTenants = next;
  }

  // ── User helpers ──
  function toggleUser(id: number) {
    const next = new Set(formUsers);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    formUsers = next;
  }

  function userNames(role: Role): string[] {
    if (!role.assigned_users?.length) return [];
    return role.assigned_users
      .map(id => availableUsers.find(u => u.id === id)?.display_name ?? `#${id}`);
  }

  // ── CRUD ──
  async function handleSave() {
    if (!formName.trim()) {
      toasts.error('El nombre del rol es obligatorio');
      return;
    }
    saving = true;
    try {
      const payload = {
        name: formName.trim(),
        description: formDescription.trim(),
        permissions: Array.from(formPermissions),
        color: formColor,
        assigned_tenants: Array.from(formTenants),
        assigned_users: Array.from(formUsers),
      };
      if (modalMode === 'create') {
        await rolesApi.create(payload);
        toasts.success(`Rol "${formName}" creado`);
      } else if (editingRoleId !== null) {
        await rolesApi.update(editingRoleId, payload);
        toasts.success(`Rol "${formName}" actualizado`);
      }
      closeModal();
      await loadAll();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al guardar');
    } finally {
      saving = false;
    }
  }

  async function handleDelete(roleId: number) {
    try {
      await rolesApi.delete(roleId);
      toasts.success('Rol eliminado');
      confirmDeleteId = null;
      await loadAll();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al eliminar');
    }
  }

  function permCount(role: Role): string {
    if (role.permissions?.includes('*')) return 'Todos';
    return `${role.permissions?.length ?? 0}`;
  }

  function tenantNames(role: Role): string[] {
    if (!role.assigned_tenants?.length) return [];
    return role.assigned_tenants
      .map(id => availableTenants.find(t => t.id === id)?.tenant_name ?? `#${id}`)
      ;
  }

  onMount(loadAll);
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="page-title">GESTIÓN DE ROLES</h1>
      <p class="page-subtitle">Control de permisos, acceso y asignación de tenants</p>
    </div>
    <button class="btn-accent px-4 py-2 flex items-center gap-2" onclick={openCreate}>
      <Plus size={14} />
      NUEVO ROL
    </button>
  </div>

  <!-- Stats -->
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
    <div class="stat-card">
      <div class="text-xs text-gray-400 uppercase tracking-wide">Roles</div>
      <div class="text-2xl font-bold mt-1">{roles.length}</div>
    </div>
    <div class="stat-card">
      <div class="text-xs text-gray-400 uppercase tracking-wide">Sistema</div>
      <div class="text-2xl font-bold mt-1">{roles.filter(r => r.system).length}</div>
    </div>
    <div class="stat-card">
      <div class="text-xs text-gray-400 uppercase tracking-wide">Custom</div>
      <div class="text-2xl font-bold mt-1">{roles.filter(r => !r.system).length}</div>
    </div>
    <div class="stat-card">
      <div class="text-xs text-gray-400 uppercase tracking-wide">Permisos Disp.</div>
      <div class="text-2xl font-bold mt-1">{totalPermsAvailable}</div>
    </div>
  </div>

  <!-- Roles Grid -->
  {#if loading}
    <div class="card p-12 text-center text-gray-500">Cargando roles...</div>
  {:else if roles.length === 0}
    <div class="card p-12 text-center text-gray-500">No hay roles definidos</div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {#each roles as role (role.id)}
        {@const assignedNames = tenantNames(role)}
        {@const assignedUserNames = userNames(role)}
        <div class="card relative overflow-hidden group">
          <!-- Color bar top -->
          <div class="absolute top-0 left-0 right-0 h-1" style="background:{role.color ?? '#6b7280'}"></div>

          <div class="pt-3">
            <!-- Header -->
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center gap-2.5">
                <div class="w-9 h-9 rounded-lg flex items-center justify-center text-white font-bold text-sm" style="background:{role.color ?? '#6b7280'}">
                  {role.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <h3 class="font-semibold text-sm">{role.name}</h3>
                  {#if role.system}
                    <span class="inline-flex items-center gap-1 text-[10px] text-gray-400">
                      <Lock size={9} /> Sistema
                    </span>
                  {:else}
                    <span class="text-[10px] text-gray-500">Personalizado</span>
                  {/if}
                </div>
              </div>
              {#if !role.system}
                <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button class="p-1.5 rounded hover:bg-white/5 text-gray-400 hover:text-white transition-colors" onclick={() => openEdit(role)} title="Editar">
                    <Edit3 size={13} />
                  </button>
                  {#if confirmDeleteId === role.id}
                    <button class="p-1.5 rounded bg-red-600/20 text-red-400 hover:bg-red-600/40 transition-colors" onclick={() => handleDelete(role.id)} title="Confirmar eliminar">
                      <Check size={13} />
                    </button>
                    <button class="p-1.5 rounded hover:bg-white/5 text-gray-400" onclick={() => confirmDeleteId = null}>
                      <X size={13} />
                    </button>
                  {:else}
                    <button class="p-1.5 rounded hover:bg-white/5 text-gray-400 hover:text-red-400 transition-colors" onclick={() => confirmDeleteId = role.id} title="Eliminar">
                      <Trash2 size={13} />
                    </button>
                  {/if}
                </div>
              {/if}
            </div>

            <!-- Description -->
            <p class="text-xs text-gray-400 mb-3 line-clamp-2">{role.description || 'Sin descripción'}</p>

            <!-- Permissions count -->
            <div class="flex items-center gap-2 mb-2">
              <Shield size={12} class="text-gray-500" />
              <span class="text-xs text-gray-400">
                {#if role.permissions?.includes('*')}
                  <span class="text-amber-400 font-medium">Todos los permisos</span>
                {:else}
                  <span class="font-medium text-white">{role.permissions?.length ?? 0}</span> permisos
                {/if}
              </span>
            </div>

            <!-- Permission badges -->
            {#if !role.permissions?.includes('*')}
              <div class="flex flex-wrap gap-1 mb-3">
                {#each (role.permissions ?? []).slice(0, 5) as perm}
                  <span class="inline-block px-1.5 py-0.5 rounded text-[9px] font-mono bg-white/5 text-gray-300">{perm}</span>
                {/each}
                {#if (role.permissions ?? []).length > 5}
                  <span class="inline-block px-1.5 py-0.5 rounded text-[9px] bg-white/5 text-gray-500">+{(role.permissions ?? []).length - 5}</span>
                {/if}
              </div>
            {/if}

            <!-- Assigned Tenants -->
            {#if assignedNames.length > 0}
              <div class="border-t border-white/5 pt-2 mt-2">
                <div class="flex items-center gap-1.5 mb-1">
                  <Building2 size={11} class="text-gray-500" />
                  <span class="text-[10px] text-gray-500 uppercase tracking-wide">Tenants asignados</span>
                </div>
                <div class="flex flex-wrap gap-1">
                  {#each assignedNames.slice(0, 3) as tn}
                    <span class="badge-neutral text-[9px]">{tn}</span>
                  {/each}
                  {#if assignedNames.length > 3}
                    <span class="text-[9px] text-gray-500">+{assignedNames.length - 3}</span>
                  {/if}
                </div>
              </div>
            {/if}

            <!-- Assigned Users -->
            {#if assignedUserNames.length > 0}
              <div class="border-t border-white/5 pt-2 mt-2">
                <div class="flex items-center gap-1.5 mb-1">
                  <Users size={11} class="text-gray-500" />
                  <span class="text-[10px] text-gray-500 uppercase tracking-wide">Usuarios asignados</span>
                </div>
                <div class="flex flex-wrap gap-1">
                  {#each assignedUserNames.slice(0, 3) as un}
                    <span class="badge-neutral text-[9px]">{un}</span>
                  {/each}
                  {#if assignedUserNames.length > 3}
                    <span class="text-[9px] text-gray-500">+{assignedUserNames.length - 3}</span>
                  {/if}
                </div>
              </div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<!-- ═══════════════════════════════════════════ -->
<!-- MODAL: Crear / Editar Rol                   -->
<!-- ═══════════════════════════════════════════ -->
{#if showModal}
  <div class="fixed inset-0 z-50 flex items-start justify-center pt-8 pb-8 overflow-y-auto" role="dialog">
    <!-- Backdrop -->
    <div class="fixed inset-0 bg-black/60 backdrop-blur-sm" onclick={closeModal}></div>

    <!-- Modal content -->
    <div class="relative bg-[#1a1714] border border-white/10 rounded-xl w-full max-w-3xl mx-4 shadow-2xl">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-white/10">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm" style="background:{formColor}">
            {formName ? formName.charAt(0).toUpperCase() : 'R'}
          </div>
          <h2 class="text-lg font-semibold">{modalMode === 'create' ? 'Nuevo Rol' : 'Editar Rol'}</h2>
        </div>
        <button class="p-1.5 rounded hover:bg-white/10 text-gray-400" onclick={closeModal}>
          <X size={18} />
        </button>
      </div>

      <div class="p-6 space-y-6 max-h-[calc(100vh-12rem)] overflow-y-auto">

        <!-- ── Presets (solo en create) ── -->
        {#if modalMode === 'create'}
          <div>
            <button
              class="flex items-center gap-2 text-xs text-gray-400 hover:text-white transition-colors mb-3"
              onclick={() => showPresets = !showPresets}
            >
              <Sparkles size={13} />
              <span>Usar plantilla predefinida</span>
              {#if showPresets}<ChevronUp size={13} />{:else}<ChevronDown size={13} />{/if}
            </button>
            {#if showPresets}
              <div class="grid grid-cols-2 gap-2">
                {#each Object.entries(presets) as [key, preset]}
                  <button
                    class="text-left p-3 rounded-lg border border-white/10 hover:border-white/20 hover:bg-white/5 transition-all group/preset"
                    onclick={() => applyPreset(key)}
                  >
                    <div class="flex items-center gap-2 mb-1">
                      <div class="w-3 h-3 rounded-full" style="background:{preset.color}"></div>
                      <span class="text-sm font-medium group-hover/preset:text-white transition-colors">{preset.name}</span>
                    </div>
                    <p class="text-[10px] text-gray-500 line-clamp-1">{preset.description}</p>
                    <div class="text-[9px] text-gray-600 mt-1">{preset.permissions.length} permisos</div>
                  </button>
                {/each}
              </div>
            {/if}
          </div>
        {/if}

        <!-- ── Basic info ── -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="label" for="role-name">Nombre del rol *</label>
            <input
              id="role-name"
              class="input w-full px-3 py-2"
              type="text"
              bind:value={formName}
              placeholder="ej: account_manager"
              required
            />
          </div>
          <div>
            <label class="label" for="role-desc">Descripción</label>
            <input
              id="role-desc"
              class="input w-full px-3 py-2"
              type="text"
              bind:value={formDescription}
              placeholder="¿Qué puede hacer este rol?"
            />
          </div>
        </div>

        <!-- ── Color picker ── -->
        <div>
          <label class="label mb-2">Color del rol</label>
          <div class="flex gap-2 flex-wrap">
            {#each COLORS as c}
              <button
                class="w-7 h-7 rounded-lg border-2 transition-all hover:scale-110"
                style="background:{c}; border-color:{formColor === c ? 'white' : 'transparent'}"
                onclick={() => formColor = c}
              ></button>
            {/each}
          </div>
        </div>

        <!-- ── Permissions by module ── -->
        <div>
          <div class="flex items-center justify-between mb-3">
            <label class="label">Permisos ({formPermissions.size} seleccionados)</label>
            <div class="flex gap-2">
              <button
                class="text-[10px] text-gray-400 hover:text-white px-2 py-0.5 rounded border border-white/10 hover:border-white/20 transition-colors"
                onclick={() => {
                  const all = new Set<string>();
                  Object.values(permCatalog).forEach(m => Object.keys(m.permissions).forEach(p => all.add(p)));
                  formPermissions = all;
                }}
              >
                Seleccionar todo
              </button>
              <button
                class="text-[10px] text-gray-400 hover:text-white px-2 py-0.5 rounded border border-white/10 hover:border-white/20 transition-colors"
                onclick={() => formPermissions = new Set()}
              >
                Limpiar
              </button>
            </div>
          </div>

          <div class="space-y-1">
            {#each sortedModules as [moduleKey, mod]}
              {@const status = moduleStatus(moduleKey)}
              {@const isExpanded = expandedModules.has(moduleKey)}
              {@const modPerms = Object.entries(mod.permissions)}
              {@const activeCount = modPerms.filter(([p]) => formPermissions.has(p)).length}

              <div class="rounded-lg border border-white/5 overflow-hidden">
                <!-- Module header -->
                <div class="flex items-center justify-between px-3 py-2.5 bg-white/[0.02] cursor-pointer hover:bg-white/[0.04] transition-colors"
                     role="button" tabindex="0"
                     onclick={() => toggleExpandModule(moduleKey)}
                     onkeydown={(e) => e.key === 'Enter' && toggleExpandModule(moduleKey)}
                >
                  <div class="flex items-center gap-2.5">
                    {#if isExpanded}<ChevronUp size={13} class="text-gray-500" />{:else}<ChevronDown size={13} class="text-gray-500" />{/if}
                    <span class="text-sm font-medium">{mod.label}</span>
                    <span class="text-[10px] px-1.5 py-0.5 rounded-full {status === 'all' ? 'bg-green-500/20 text-green-400' : status === 'partial' ? 'bg-amber-500/20 text-amber-400' : 'bg-white/5 text-gray-500'}">
                      {activeCount}/{modPerms.length}
                    </span>
                  </div>
                  <!-- Module-level toggle -->
                  <button
                    class="p-1 rounded hover:bg-white/10 transition-colors"
                    onclick={(e: MouseEvent) => { e.stopPropagation(); toggleModule(moduleKey); }}
                    title={status === 'all' ? 'Desactivar todos' : 'Activar todos'}
                  >
                    {#if status === 'all'}
                      <ToggleRight size={20} class="text-green-400" />
                    {:else}
                      <ToggleLeft size={20} class="text-gray-500" />
                    {/if}
                  </button>
                </div>

                <!-- Permission rows (expanded) -->
                {#if isExpanded}
                  <div class="border-t border-white/5">
                    {#each modPerms as [permKey, permDesc], i}
                      {@const active = formPermissions.has(permKey)}
                      <div
                        class="flex items-center justify-between px-4 py-2 {i > 0 ? 'border-t border-white/[0.03]' : ''} hover:bg-white/[0.02] transition-colors cursor-pointer"
                        role="button" tabindex="0"
                        onclick={() => togglePerm(permKey)}
                        onkeydown={(e) => e.key === 'Enter' && togglePerm(permKey)}
                      >
                        <div class="flex-1 min-w-0">
                          <div class="text-xs font-mono {active ? 'text-white' : 'text-gray-500'} transition-colors">{permKey}</div>
                          <div class="text-[10px] text-gray-500 truncate">{permDesc}</div>
                        </div>
                        <div class="ml-3 shrink-0">
                          {#if active}
                            <div class="w-8 h-[18px] rounded-full bg-green-500/30 flex items-center justify-end px-0.5">
                              <div class="w-3.5 h-3.5 rounded-full bg-green-400"></div>
                            </div>
                          {:else}
                            <div class="w-8 h-[18px] rounded-full bg-white/10 flex items-center px-0.5">
                              <div class="w-3.5 h-3.5 rounded-full bg-gray-600"></div>
                            </div>
                          {/if}
                        </div>
                      </div>
                    {/each}
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        </div>

        <!-- ── Tenant assignment ── -->
        <div>
          <button
            class="flex items-center gap-2 text-xs text-gray-400 hover:text-white transition-colors mb-3"
            onclick={() => showTenantPicker = !showTenantPicker}
          >
            <Building2 size={13} />
            <span>Asignar tenants al rol ({formTenants.size} seleccionados)</span>
            {#if showTenantPicker}<ChevronUp size={13} />{:else}<ChevronDown size={13} />{/if}
          </button>
          {#if showTenantPicker}
            {#if availableTenants.length === 0}
              <p class="text-xs text-gray-500">No hay tenants disponibles</p>
            {:else}
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {#each availableTenants as tenant}
                  {@const selected = formTenants.has(tenant.id)}
                  <button
                    class="flex items-center gap-3 p-2.5 rounded-lg border text-left transition-all
                      {selected ? 'border-green-500/40 bg-green-500/10' : 'border-white/10 hover:border-white/20 hover:bg-white/5'}"
                    onclick={() => toggleTenant(tenant.id)}
                  >
                    <div class="w-7 h-7 rounded-md flex items-center justify-center shrink-0 {selected ? 'bg-green-500/30 text-green-400' : 'bg-white/5 text-gray-500'}">
                      {#if selected}<Check size={14} />{:else}<Building2 size={14} />{/if}
                    </div>
                    <div class="min-w-0">
                      <div class="text-xs font-medium truncate {selected ? 'text-white' : 'text-gray-300'}">{tenant.tenant_name}</div>
                      <div class="text-[10px] text-gray-500 truncate">{tenant.customer_name} • {tenant.domain || '—'}</div>
                    </div>
                  </button>
                {/each}
              </div>
            {/if}
          {/if}
        </div>

        <!-- ── User assignment ── -->
        <div>
          <button
            class="flex items-center gap-2 text-xs text-gray-400 hover:text-white transition-colors mb-3"
            onclick={() => { showUserPicker = !showUserPicker; userSearchQuery = ''; }}
          >
            <Users size={13} />
            <span>Asignar usuarios al rol ({formUsers.size} seleccionados)</span>
            {#if showUserPicker}<ChevronUp size={13} />{:else}<ChevronDown size={13} />{/if}
          </button>
          {#if showUserPicker}
            {#if availableUsers.length === 0}
              <p class="text-xs text-gray-500">No hay usuarios disponibles</p>
            {:else}
              <!-- Search -->
              <div class="relative mb-3">
                <input
                  type="text"
                  class="input w-full px-3 py-2 text-xs pl-8"
                  placeholder="Buscar usuario por nombre o email..."
                  bind:value={userSearchQuery}
                />
                <Users size={13} class="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" />
              </div>
              <div class="space-y-1.5 max-h-52 overflow-y-auto pr-1">
                {#each filteredUsers as user}
                  {@const selected = formUsers.has(user.id)}
                  <button
                    class="w-full flex items-center gap-3 p-2.5 rounded-lg border text-left transition-all
                      {selected ? 'border-blue-500/40 bg-blue-500/10' : 'border-white/10 hover:border-white/20 hover:bg-white/5'}"
                    onclick={() => toggleUser(user.id)}
                  >
                    <div class="w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs font-bold
                      {selected ? 'bg-blue-500/30 text-blue-300' : 'bg-white/5 text-gray-400'}">
                      {user.display_name.charAt(0).toUpperCase()}
                    </div>
                    <div class="min-w-0 flex-1">
                      <div class="text-xs font-medium truncate {selected ? 'text-white' : 'text-gray-300'}">{user.display_name}</div>
                      <div class="text-[10px] text-gray-500 truncate flex items-center gap-1">
                        <Mail size={9} />
                        {user.email}
                      </div>
                    </div>
                    <div class="shrink-0">
                      {#if selected}
                        <div class="w-5 h-5 rounded-full bg-blue-500/30 flex items-center justify-center">
                          <Check size={11} class="text-blue-300" />
                        </div>
                      {/if}
                    </div>
                  </button>
                {/each}
                {#if filteredUsers.length === 0}
                  <p class="text-xs text-gray-500 text-center py-3">Sin resultados para "{userSearchQuery}"</p>
                {/if}
              </div>
              {#if formUsers.size > 0}
                <div class="mt-2 flex flex-wrap gap-1">
                  {#each Array.from(formUsers) as uid}
                    {@const u = availableUsers.find(x => x.id === uid)}
                    {#if u}
                      <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] bg-blue-500/20 text-blue-300 border border-blue-500/30">
                        {u.display_name}
                        <button onclick={() => toggleUser(uid)} class="hover:text-white transition-colors ml-0.5">
                          <X size={9} />
                        </button>
                      </span>
                    {/if}
                  {/each}
                </div>
              {/if}
            {/if}
          {/if}
        </div>

      </div>

      <!-- Footer -->
      <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-white/10">
        <button class="btn-secondary px-5 py-2" onclick={closeModal}>CANCELAR</button>
        <button
          class="btn-accent px-5 py-2 flex items-center gap-2 disabled:opacity-50"
          disabled={saving || !formName.trim()}
          onclick={handleSave}
        >
          {#if saving}
            <span class="animate-spin">⟳</span> GUARDANDO...
          {:else}
            <Check size={14} />
            {modalMode === 'create' ? 'CREAR ROL' : 'GUARDAR CAMBIOS'}
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}
