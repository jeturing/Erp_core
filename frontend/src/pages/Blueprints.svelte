<script lang="ts">
  import { onMount } from 'svelte';
  import { blueprintsApi } from '../lib/api';
  import { toasts } from '../lib/stores';
  import type { BlueprintModule, BlueprintPackage } from '../lib/types';
  import {
    Boxes, Plus, Search, Package, Puzzle, Pencil,
    ToggleLeft, ToggleRight, DollarSign, RefreshCw,
  } from 'lucide-svelte';

  let modules: BlueprintModule[] = [];
  let packages: BlueprintPackage[] = [];
  let loading = true;
  let activeTab: 'modules' | 'packages' = 'modules';
  let search = '';

  // Module form
  let showModuleForm = false;
  let editingModuleId: number | null = null;
  let moduleForm = {
    technical_name: '', display_name: '', description: '', category: '',
    version: '1.0', is_core: false, partner_allowed: true,
    price_monthly: 0, sort_order: 0,
  };

  // Package form
  let showPackageForm = false;
  let editingPackageId: number | null = null;
  let packageForm = {
    name: '', display_name: '', description: '', plan_type: 'basic',
    base_price_monthly: 0, is_default: false, module_ids: [] as number[],
  };

  function resetModuleForm() {
    moduleForm = {
      technical_name: '', display_name: '', description: '', category: '',
      version: '1.0', is_core: false, partner_allowed: true,
      price_monthly: 0, sort_order: 0,
    };
    editingModuleId = null;
  }

  function resetPackageForm() {
    packageForm = {
      name: '', display_name: '', description: '', plan_type: 'basic',
      base_price_monthly: 0, is_default: false, module_ids: [],
    };
    editingPackageId = null;
  }

  async function loadAll() {
    loading = true;
    try {
      const [modRes, pkgRes] = await Promise.all([
        blueprintsApi.getModules(),
        blueprintsApi.getPackages(),
      ]);
      modules = modRes.items;
      packages = pkgRes.items;
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  async function handleModuleSubmit() {
    try {
      if (editingModuleId) {
        await blueprintsApi.updateModule(editingModuleId, moduleForm as any);
        toasts.success('Módulo actualizado');
      } else {
        await blueprintsApi.createModule(moduleForm as any);
        toasts.success('Módulo creado');
      }
      showModuleForm = false;
      resetModuleForm();
      await loadAll();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  async function handlePackageSubmit() {
    try {
      if (editingPackageId) {
        await blueprintsApi.updatePackage(editingPackageId, packageForm as any);
        toasts.success('Paquete actualizado');
      } else {
        await blueprintsApi.createPackage(packageForm as any);
        toasts.success('Paquete creado');
      }
      showPackageForm = false;
      resetPackageForm();
      await loadAll();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  function editModule(m: BlueprintModule) {
    editingModuleId = m.id;
    moduleForm = {
      technical_name: m.technical_name,
      display_name: m.display_name || '',
      description: m.description || '',
      category: m.category || '',
      version: m.version || '1.0',
      is_core: m.is_core,
      partner_allowed: m.partner_allowed,
      price_monthly: m.price_monthly,
      sort_order: m.sort_order,
    };
    showModuleForm = true;
  }

  function editPackage(p: BlueprintPackage) {
    editingPackageId = p.id;
    packageForm = {
      name: p.name,
      display_name: p.display_name || '',
      description: p.description || '',
      plan_type: p.plan_type || 'basic',
      base_price_monthly: p.base_price_monthly,
      is_default: p.is_default,
      module_ids: p.modules?.map(m => m.id) || [],
    };
    showPackageForm = true;
  }

  function toggleModuleInPackage(moduleId: number) {
    if (packageForm.module_ids.includes(moduleId)) {
      packageForm.module_ids = packageForm.module_ids.filter(id => id !== moduleId);
    } else {
      packageForm.module_ids = [...packageForm.module_ids, moduleId];
    }
  }

  $: filteredModules = modules.filter(m =>
    m.technical_name.toLowerCase().includes(search.toLowerCase()) ||
    (m.display_name || '').toLowerCase().includes(search.toLowerCase()) ||
    (m.category || '').toLowerCase().includes(search.toLowerCase())
  );

  $: filteredPackages = packages.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    (p.display_name || '').toLowerCase().includes(search.toLowerCase())
  );

  $: coreModules = modules.filter(m => m.is_core).length;
  $: addonModules = modules.filter(m => !m.is_core).length;

  onMount(loadAll);
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><Boxes size={24} /> Blueprints</h1>
      <p class="page-subtitle">Catálogo de módulos y paquetes para tenants</p>
    </div>
    <div class="flex gap-2">
      <button class="btn-secondary flex items-center gap-2" on:click={loadAll} disabled={loading}>
        <RefreshCw size={14} class={loading ? 'animate-spin' : ''} /> Actualizar
      </button>
      {#if activeTab === 'modules'}
        <button class="btn-accent flex items-center gap-2" on:click={() => { resetModuleForm(); showModuleForm = true; }}>
          <Plus size={16} /> Nuevo Módulo
        </button>
      {:else}
        <button class="btn-accent flex items-center gap-2" on:click={() => { resetPackageForm(); showPackageForm = true; }}>
          <Plus size={16} /> Nuevo Paquete
        </button>
      {/if}
    </div>
  </div>

  <!-- KPIs -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
    <div class="stat-card">
      <span class="stat-label">Total Módulos</span>
      <span class="stat-value">{modules.length}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Core</span>
      <span class="stat-value text-info">{coreModules}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Add-ons</span>
      <span class="stat-value text-terracotta">{addonModules}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Paquetes</span>
      <span class="stat-value">{packages.length}</span>
    </div>
  </div>

  <!-- Tabs + Search -->
  <div class="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
    <div class="flex border border-border-light overflow-hidden">
      <button class="px-4 py-2 text-xs font-semibold uppercase tracking-wider transition-colors {activeTab === 'modules' ? 'bg-charcoal text-text-light' : 'bg-bg-card text-text-secondary hover:bg-border-light'}" on:click={() => activeTab = 'modules'}>
        <Puzzle size={14} class="inline mr-1" /> Módulos
      </button>
      <button class="px-4 py-2 text-xs font-semibold uppercase tracking-wider transition-colors {activeTab === 'packages' ? 'bg-charcoal text-text-light' : 'bg-bg-card text-text-secondary hover:bg-border-light'}" on:click={() => activeTab = 'packages'}>
        <Package size={14} class="inline mr-1" /> Paquetes
      </button>
    </div>
    <div class="relative flex-1">
      <Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
      <input type="text" bind:value={search} placeholder="Buscar..." class="input pl-10 w-full" />
    </div>
  </div>

  <!-- Module Form -->
  {#if showModuleForm}
    <div class="card p-6 border border-border-dark">
      <h2 class="section-heading mb-4">{editingModuleId ? 'Editar' : 'Nuevo'} Módulo</h2>
      <form on:submit|preventDefault={handleModuleSubmit} class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="label">Nombre técnico *</label>
          <input type="text" bind:value={moduleForm.technical_name} required class="input w-full" placeholder="account_accountant" />
        </div>
        <div>
          <label class="label">Nombre visible *</label>
          <input type="text" bind:value={moduleForm.display_name} required class="input w-full" placeholder="Contabilidad" />
        </div>
        <div>
          <label class="label">Categoría</label>
          <input type="text" bind:value={moduleForm.category} class="input w-full" placeholder="Finanzas" />
        </div>
        <div>
          <label class="label">Versión</label>
          <input type="text" bind:value={moduleForm.version} class="input w-full" />
        </div>
        <div>
          <label class="label">Precio mensual ($)</label>
          <input type="number" bind:value={moduleForm.price_monthly} min="0" step="0.01" class="input w-full" />
        </div>
        <div>
          <label class="label">Orden</label>
          <input type="number" bind:value={moduleForm.sort_order} min="0" class="input w-full" />
        </div>
        <div class="flex items-center gap-6">
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" bind:checked={moduleForm.is_core} class="w-4 h-4" />
            <span class="text-sm">Módulo Core</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" bind:checked={moduleForm.partner_allowed} class="w-4 h-4" />
            <span class="text-sm">Disponible para Partners</span>
          </label>
        </div>
        <div class="md:col-span-2">
          <label class="label">Descripción</label>
          <textarea bind:value={moduleForm.description} rows="2" class="input w-full"></textarea>
        </div>
        <div class="md:col-span-2 flex gap-3">
          <button type="submit" class="btn-accent">{editingModuleId ? 'Guardar' : 'Crear'}</button>
          <button type="button" class="btn-secondary" on:click={() => { showModuleForm = false; resetModuleForm(); }}>Cancelar</button>
        </div>
      </form>
    </div>
  {/if}

  <!-- Package Form -->
  {#if showPackageForm}
    <div class="card p-6 border border-border-dark">
      <h2 class="section-heading mb-4">{editingPackageId ? 'Editar' : 'Nuevo'} Paquete</h2>
      <form on:submit|preventDefault={handlePackageSubmit} class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="label">Nombre clave *</label>
          <input type="text" bind:value={packageForm.name} required class="input w-full" placeholder="starter_pack" />
        </div>
        <div>
          <label class="label">Nombre visible *</label>
          <input type="text" bind:value={packageForm.display_name} required class="input w-full" placeholder="Pack Inicial" />
        </div>
        <div>
          <label class="label">Tipo de plan</label>
          <select bind:value={packageForm.plan_type} class="input w-full">
            <option value="basic">Basic</option>
            <option value="pro">Pro</option>
            <option value="enterprise">Enterprise</option>
          </select>
        </div>
        <div>
          <label class="label">Precio base mensual ($)</label>
          <input type="number" bind:value={packageForm.base_price_monthly} min="0" step="0.01" class="input w-full" />
        </div>
        <label class="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" bind:checked={packageForm.is_default} class="w-4 h-4" />
          <span class="text-sm">Paquete por defecto</span>
        </label>
        <div class="md:col-span-2">
          <label class="label">Descripción</label>
          <textarea bind:value={packageForm.description} rows="2" class="input w-full"></textarea>
        </div>
        <div class="md:col-span-2">
          <label class="label mb-2">Módulos incluidos</label>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-48 overflow-y-auto p-3 border border-border-light bg-bg-page">
            {#each modules.filter(m => m.is_active) as m}
              <label class="flex items-center gap-2 cursor-pointer text-sm p-1.5 hover:bg-bg-card transition-colors">
                <input type="checkbox" checked={packageForm.module_ids.includes(m.id)} on:change={() => toggleModuleInPackage(m.id)} class="w-4 h-4" />
                <span class="truncate">{m.display_name || m.technical_name}</span>
                {#if m.is_core}<span class="badge-info text-[9px] px-1.5 py-0.5">core</span>{/if}
              </label>
            {/each}
          </div>
          <span class="text-[11px] text-gray-500 mt-1">{packageForm.module_ids.length} módulos seleccionados</span>
        </div>
        <div class="md:col-span-2 flex gap-3">
          <button type="submit" class="btn-accent">{editingPackageId ? 'Guardar' : 'Crear'}</button>
          <button type="button" class="btn-secondary" on:click={() => { showPackageForm = false; resetPackageForm(); }}>Cancelar</button>
        </div>
      </form>
    </div>
  {/if}

  <!-- Content -->
  {#if loading}
    <div class="text-center py-16 text-gray-500">
      <div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin mx-auto"></div>
      <p class="mt-3">Cargando blueprints...</p>
    </div>
  {:else if activeTab === 'modules'}
    {#if filteredModules.length === 0}
      <div class="text-center py-16 text-gray-500">No se encontraron módulos</div>
    {:else}
      <div class="overflow-x-auto">
        <table class="table w-full">
          <thead>
            <tr>
              <th>Módulo</th>
              <th>Categoría</th>
              <th>Versión</th>
              <th>Precio/mes</th>
              <th>Tipo</th>
              <th>Partner</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {#each filteredModules as m}
              <tr>
                <td>
                  <div class="font-semibold text-text-primary">{m.display_name || m.technical_name}</div>
                  <div class="text-[11px] text-gray-500 font-mono">{m.technical_name}</div>
                </td>
                <td class="text-sm">{m.category || '—'}</td>
                <td class="text-sm font-mono">{m.version || '—'}</td>
                <td class="font-semibold">{m.price_monthly > 0 ? `$${m.price_monthly.toFixed(2)}` : 'Incluido'}</td>
                <td>
                  <span class="badge-{m.is_core ? 'info' : 'warning'}">{m.is_core ? 'Core' : 'Add-on'}</span>
                </td>
                <td>
                  {#if m.partner_allowed}
                    <ToggleRight size={18} class="text-success" />
                  {:else}
                    <ToggleLeft size={18} class="text-gray-400" />
                  {/if}
                </td>
                <td>
                  <span class="badge-{m.is_active ? 'success' : 'neutral'}">{m.is_active ? 'Activo' : 'Inactivo'}</span>
                </td>
                <td>
                  <button class="btn-sm btn-secondary" on:click={() => editModule(m)}><Pencil size={14} /></button>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  {:else}
    {#if filteredPackages.length === 0}
      <div class="text-center py-16 text-gray-500">No se encontraron paquetes</div>
    {:else}
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {#each filteredPackages as p}
          <div class="card hover:shadow-md transition-shadow">
            <div class="flex items-start justify-between mb-3">
              <div>
                <h3 class="font-semibold text-text-primary">{p.display_name || p.name}</h3>
                <span class="text-[11px] text-gray-500 font-mono">{p.name}</span>
              </div>
              <div class="flex gap-1">
                <span class="badge-{p.plan_type === 'enterprise' ? 'enterprise' : p.plan_type === 'pro' ? 'pro' : 'basic'}">{p.plan_type || 'basic'}</span>
                {#if p.is_default}<span class="badge-info">default</span>{/if}
              </div>
            </div>
            {#if p.description}
              <p class="text-sm text-text-secondary mb-3">{p.description}</p>
            {/if}
            <div class="flex items-center gap-2 mb-3">
              <DollarSign size={16} class="text-success" />
              <span class="text-xl font-bold">${p.base_price_monthly.toFixed(2)}</span>
              <span class="text-sm text-gray-500">/mes</span>
            </div>
            <div class="border-t border-border-light pt-3">
              <span class="text-[11px] font-semibold uppercase text-gray-500 mb-2 block">
                {p.modules?.length || 0} módulos incluidos
              </span>
              <div class="flex flex-wrap gap-1">
                {#each (p.modules || []).slice(0, 6) as m}
                  <span class="text-[10px] px-2 py-0.5 bg-bg-page border border-border-light text-text-secondary">{m.display_name || m.technical_name}</span>
                {/each}
                {#if (p.modules?.length || 0) > 6}
                  <span class="text-[10px] px-2 py-0.5 text-gray-500">+{(p.modules?.length || 0) - 6} más</span>
                {/if}
              </div>
            </div>
            <div class="mt-3 pt-3 border-t border-border-light flex justify-end">
              <button class="btn-sm btn-secondary" on:click={() => editPackage(p)}>
                <Pencil size={14} /> Editar
              </button>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  {/if}
</div>
