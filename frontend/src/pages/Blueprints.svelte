<script lang="ts">
  import { onMount } from 'svelte';
  import { blueprintsApi } from '../lib/api/blueprints';
  import { toasts } from '../lib/stores';
  import type { BlueprintModule, BlueprintPackage } from '../lib/types';
  import {
    Boxes, Plus, Search, Package, Puzzle, Pencil,
    ToggleLeft, ToggleRight, RefreshCw, Download, X,
    CheckSquare, Square, ChevronDown, ChevronRight,
  } from 'lucide-svelte';

  // ── State ──
  let modules: BlueprintModule[] = [];
  let packages: BlueprintPackage[] = [];
  let categories: string[] = [];
  let loading = true;
  let importing = false;
  let activeTab: 'modules' | 'packages' = 'packages';
  let search = '';
  let filterCategory = '';
  let filterType: 'all' | 'core' | 'addon' = 'all';

  // Module form
  let showModuleForm = false;
  let editingModuleId: number | null = null;
  let moduleForm = {
    technical_name: '', display_name: '', description: '', category: '',
    version: '17.0.1.0', is_core: false, partner_allowed: true,
    price_monthly: 0, sort_order: 0,
  };

  // Package form + module picker
  let showPackageForm = false;
  let editingPackageId: number | null = null;
  let pkgModuleSearch = '';
  let pkgCategoryFilter = '';
  let packageForm = {
    name: '', display_name: '', description: '', plan_type: 'basic',
    base_price_monthly: 0, is_default: false, module_list: [] as string[],
  };

  // Categorías expandidas en el picker
  let expandedCategories = new Set<string>();

  // ── Derived ──
  $: filteredModules = modules.filter(m => {
    const q = search.toLowerCase();
    const matchSearch = !q ||
      m.technical_name.toLowerCase().includes(q) ||
      (m.display_name || '').toLowerCase().includes(q) ||
      (m.category || '').toLowerCase().includes(q);
    const matchCat = !filterCategory || m.category === filterCategory;
    const matchType = filterType === 'all' || (filterType === 'core' ? m.is_core : !m.is_core);
    return matchSearch && matchCat && matchType;
  });

  $: filteredPackages = packages.filter(p => {
    const q = search.toLowerCase();
    return !q || p.name.toLowerCase().includes(q) || (p.display_name || '').toLowerCase().includes(q);
  });

  $: pickerModules = modules.filter(m => {
    const q = pkgModuleSearch.toLowerCase();
    const matchSearch = !q || m.technical_name.includes(q) || (m.display_name || '').toLowerCase().includes(q);
    const matchCat = !pkgCategoryFilter || m.category === pkgCategoryFilter;
    return matchSearch && matchCat;
  });

  $: pickerByCategory = pickerModules.reduce((acc: Record<string, BlueprintModule[]>, m) => {
    const cat = m.category || 'General';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(m);
    return acc;
  }, {});

  $: coreModules = modules.filter(m => m.is_core).length;
  $: addonModules = modules.filter(m => !m.is_core).length;

  function toggleCategory(cat: string) {
    if (expandedCategories.has(cat)) expandedCategories.delete(cat);
    else expandedCategories.add(cat);
    expandedCategories = new Set(expandedCategories);
  }

  // ── API ──
  async function loadAll() {
    loading = true;
    try {
      const [modRes, pkgRes, catRes] = await Promise.all([
        blueprintsApi.getModules({ active_only: false }),
        blueprintsApi.getPackages(),
        blueprintsApi.getCategories().catch(() => [] as string[]),
      ]);
      modules = modRes?.items ?? (modRes as any) ?? [];
      packages = pkgRes?.items ?? (pkgRes as any) ?? [];
      categories = catRes ?? [];
      expandedCategories = new Set(categories.slice(0, 3));
    } catch (e: any) {
      toasts.error(e.message || 'Error cargando blueprints');
    } finally {
      loading = false;
    }
  }

  async function importFromFs() {
    importing = true;
    try {
      const res = await blueprintsApi.importFromFilesystem();
      toasts.success(`✅ Importados: ${res.created} nuevos, ${res.updated} actualizados (total: ${res.total_in_catalog})`);
      await loadAll();
    } catch (e: any) {
      toasts.error(e.message || 'Error al importar módulos');
    } finally {
      importing = false;
    }
  }

  // ── Module form ──
  function resetModuleForm() {
    moduleForm = { technical_name: '', display_name: '', description: '', category: '',
      version: '17.0.1.0', is_core: false, partner_allowed: true, price_monthly: 0, sort_order: 0 };
    editingModuleId = null;
  }

  function editModule(m: BlueprintModule) {
    editingModuleId = m.id;
    moduleForm = {
      technical_name: m.technical_name,
      display_name: m.display_name || '',
      description: m.description || '',
      category: m.category || '',
      version: m.version || '17.0.1.0',
      is_core: m.is_core,
      partner_allowed: m.partner_allowed,
      price_monthly: m.price_monthly,
      sort_order: m.sort_order ?? 0,
    };
    showModuleForm = true;
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

  // ── Package form ──
  function resetPackageForm() {
    packageForm = { name: '', display_name: '', description: '', plan_type: 'basic',
      base_price_monthly: 0, is_default: false, module_list: [] };
    pkgModuleSearch = ''; pkgCategoryFilter = '';
    editingPackageId = null;
  }

  function openNewPackage() {
    resetPackageForm();
    expandedCategories = new Set(categories.slice(0, 3));
    showPackageForm = true;
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
      module_list: Array.isArray(p.module_list) ? [...p.module_list] : [],
    };
    pkgModuleSearch = ''; pkgCategoryFilter = '';
    expandedCategories = new Set(categories.slice(0, 5));
    showPackageForm = true;
  }

  function toggleModuleInPackage(techName: string) {
    if (packageForm.module_list.includes(techName)) {
      packageForm.module_list = packageForm.module_list.filter(n => n !== techName);
    } else {
      packageForm.module_list = [...packageForm.module_list, techName];
    }
  }

  function toggleAllInCategory(cat: string) {
    const catModules = (pickerByCategory[cat] || []).map(m => m.technical_name);
    const allSelected = catModules.every(n => packageForm.module_list.includes(n));
    if (allSelected) {
      packageForm.module_list = packageForm.module_list.filter(n => !catModules.includes(n));
    } else {
      const toAdd = catModules.filter(n => !packageForm.module_list.includes(n));
      packageForm.module_list = [...packageForm.module_list, ...toAdd];
    }
  }

  function generateName(displayName: string): string {
    return 'pkg_' + displayName.toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  }

  function onDisplayNameInput() {
    if (!editingPackageId && !packageForm.name) {
      packageForm.name = generateName(packageForm.display_name);
    }
  }

  async function handlePackageSubmit() {
    if (!packageForm.name) packageForm.name = generateName(packageForm.display_name);
    try {
      if (editingPackageId) {
        await blueprintsApi.updatePackage(editingPackageId, { ...packageForm });
        toasts.success('Paquete actualizado');
      } else {
        await blueprintsApi.createPackage(packageForm as any);
        toasts.success('Paquete creado');
      }
      showPackageForm = false;
      resetPackageForm();
      await loadAll();
    } catch (e: any) {
      toasts.error(e.message || 'Error');
    }
  }

  onMount(loadAll);
</script>

<div class="p-6 space-y-5">
  <!-- ── Header ── -->
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><Boxes size={22} /> Blueprints</h1>
      <p class="page-subtitle">Catálogo de módulos y paquetes para tenants</p>
    </div>
    <div class="flex gap-2 flex-wrap">
      <button class="btn-secondary flex items-center gap-2 text-xs" on:click={loadAll} disabled={loading}>
        <RefreshCw size={13} class={loading ? 'animate-spin' : ''} /> Actualizar
      </button>
      <button class="btn-secondary flex items-center gap-2 text-xs" on:click={importFromFs} disabled={importing}
        title="Importar módulos desde /opt/extra-addons/V17">
        <Download size={13} class={importing ? 'animate-bounce' : ''} />
        {importing ? 'Importando...' : 'Importar V17'}
      </button>
      {#if activeTab === 'modules'}
        <button class="btn-accent flex items-center gap-2 text-xs" on:click={() => { resetModuleForm(); showModuleForm = true; }}>
          <Plus size={14} /> Nuevo Módulo
        </button>
      {:else}
        <button class="btn-accent flex items-center gap-2 text-xs" on:click={openNewPackage}>
          <Plus size={14} /> Nuevo Paquete
        </button>
      {/if}
    </div>
  </div>

  <!-- ── KPIs ── -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
    <div class="stat-card">
      <span class="stat-label">Total Módulos</span>
      <span class="stat-value">{modules.length}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Core</span>
      <span class="stat-value text-blue-400">{coreModules}</span>
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

  <!-- ── Tabs + Search ── -->
  <div class="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
    <div class="flex border border-border-dark overflow-hidden rounded">
      <button class="px-4 py-2 text-xs font-semibold uppercase tracking-wider transition-colors
        {activeTab === 'packages' ? 'bg-charcoal text-text-light' : 'bg-bg-card text-text-secondary hover:bg-border-light'}"
        on:click={() => activeTab = 'packages'}>
        <Package size={13} class="inline mr-1" /> Paquetes
      </button>
      <button class="px-4 py-2 text-xs font-semibold uppercase tracking-wider transition-colors
        {activeTab === 'modules' ? 'bg-charcoal text-text-light' : 'bg-bg-card text-text-secondary hover:bg-border-light'}"
        on:click={() => activeTab = 'modules'}>
        <Puzzle size={13} class="inline mr-1" /> Módulos ({modules.length})
      </button>
    </div>
    <div class="relative flex-1">
      <Search size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
      <input type="text" bind:value={search} placeholder="Buscar..." class="input pl-9 w-full text-sm" />
    </div>
    {#if activeTab === 'modules'}
      <select bind:value={filterCategory} class="input w-auto text-sm">
        <option value="">Todas las categorías</option>
        {#each categories as cat}
          <option value={cat}>{cat}</option>
        {/each}
      </select>
      <div class="flex gap-1">
        {#each [['all','Todos'], ['core','Core'], ['addon','Add-ons']] as [v, label]}
          <button on:click={() => filterType = v as any}
            class="px-2.5 py-1.5 text-xs rounded border transition-colors
              {filterType === v ? 'bg-terracotta text-white border-terracotta' : 'border-border-dark text-gray-400 hover:text-white'}">
            {label}
          </button>
        {/each}
      </div>
    {/if}
  </div>

  <!-- ── Module Form ── -->
  {#if showModuleForm}
    <div class="card p-5 border border-border-dark">
      <h2 class="section-heading mb-4">{editingModuleId ? 'Editar' : 'Nuevo'} Módulo</h2>
      <form on:submit|preventDefault={handleModuleSubmit} class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="label">Nombre técnico *</label>
          <input type="text" bind:value={moduleForm.technical_name} required class="input w-full font-mono text-sm"
            placeholder="crm_dashboard" disabled={!!editingModuleId} />
        </div>
        <div>
          <label class="label">Nombre visible *</label>
          <input type="text" bind:value={moduleForm.display_name} required class="input w-full" placeholder="CRM Dashboard" />
        </div>
        <div>
          <label class="label">Categoría</label>
          <input type="text" bind:value={moduleForm.category} list="cat-datalist" class="input w-full" placeholder="Ventas" />
          <datalist id="cat-datalist">
            {#each categories as cat}<option value={cat} />{/each}
          </datalist>
        </div>
        <div>
          <label class="label">Versión</label>
          <input type="text" bind:value={moduleForm.version} class="input w-full font-mono text-sm" />
        </div>
        <div class="flex items-center gap-6 pt-2">
          <label class="flex items-center gap-2 cursor-pointer text-sm">
            <input type="checkbox" bind:checked={moduleForm.is_core} class="w-4 h-4 accent-blue-500" />
            Módulo Core
          </label>
          <label class="flex items-center gap-2 cursor-pointer text-sm">
            <input type="checkbox" bind:checked={moduleForm.partner_allowed} class="w-4 h-4 accent-green-500" />
            Para Partners
          </label>
        </div>
        <div>
          <label class="label">Precio mensual ($)</label>
          <input type="number" bind:value={moduleForm.price_monthly} min="0" step="0.01" class="input w-full" />
        </div>
        <div class="md:col-span-2">
          <label class="label">Descripción</label>
          <textarea bind:value={moduleForm.description} rows="2" class="input w-full resize-none text-sm"></textarea>
        </div>
        <div class="md:col-span-2 flex gap-3">
          <button type="submit" class="btn-accent">{editingModuleId ? 'Guardar' : 'Crear'}</button>
          <button type="button" class="btn-secondary" on:click={() => { showModuleForm = false; resetModuleForm(); }}>Cancelar</button>
        </div>
      </form>
    </div>
  {/if}

  <!-- ── Package Form con picker por categoría ── -->
  {#if showPackageForm}
    <div class="card p-5 border border-border-dark space-y-4">
      <h2 class="section-heading">{editingPackageId ? 'Editar' : 'Nuevo'} Paquete</h2>
      <form on:submit|preventDefault={handlePackageSubmit}>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
          <div>
            <label class="label">Nombre visible *</label>
            <input type="text" bind:value={packageForm.display_name} required class="input w-full"
              placeholder="Restaurantes & Dark Kitchens" on:input={onDisplayNameInput} />
          </div>
          <div>
            <label class="label">Nombre clave (auto)</label>
            <input type="text" bind:value={packageForm.name} required class="input w-full font-mono text-sm"
              placeholder="pkg_restaurantes" />
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
          <div class="md:col-span-2">
            <label class="label">Descripción</label>
            <textarea bind:value={packageForm.description} rows="2" class="input w-full resize-none text-sm"></textarea>
          </div>
          <label class="flex items-center gap-2 cursor-pointer text-sm">
            <input type="checkbox" bind:checked={packageForm.is_default} class="w-4 h-4" />
            Paquete por defecto
          </label>
        </div>

        <!-- Módulos seleccionados como chips -->
        <div class="mb-4">
          <div class="flex items-center justify-between mb-2">
            <label class="label mb-0">
              Módulos incluidos
              <span class="ml-2 px-2 py-0.5 bg-terracotta/20 text-terracotta text-xs rounded-full font-bold">
                {packageForm.module_list.length}
              </span>
            </label>
            {#if packageForm.module_list.length > 0}
              <button type="button" class="text-xs text-gray-500 hover:text-red-400"
                on:click={() => packageForm.module_list = []}>Limpiar todo</button>
            {/if}
          </div>
          {#if packageForm.module_list.length === 0}
            <div class="text-sm text-gray-500 italic py-2">Ningún módulo — selecciona abajo ↓</div>
          {:else}
            <div class="flex flex-wrap gap-1.5 p-3 bg-bg-page rounded border border-border-dark max-h-28 overflow-y-auto">
              {#each packageForm.module_list as tn}
                {@const mod = modules.find(m => m.technical_name === tn)}
                <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium
                  {mod?.is_core ? 'bg-blue-500/15 text-blue-300 border border-blue-500/30' : 'bg-terracotta/15 text-orange-300 border border-terracotta/30'}">
                  {mod?.display_name || tn}
                  <button type="button" on:click={() => toggleModuleInPackage(tn)} class="ml-0.5 hover:text-red-400">
                    <X size={10} />
                  </button>
                </span>
              {/each}
            </div>
          {/if}
        </div>

        <!-- Picker de módulos con acordeón por categoría -->
        {#if modules.length > 0}
          <div class="border border-border-dark rounded-lg overflow-hidden">
            <div class="flex gap-2 p-3 bg-bg-page border-b border-border-dark">
              <div class="relative flex-1">
                <Search size={13} class="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" />
                <input type="text" bind:value={pkgModuleSearch} placeholder="Buscar módulo..."
                  class="input pl-8 py-1.5 text-xs w-full" />
              </div>
              <select bind:value={pkgCategoryFilter} class="input py-1.5 text-xs w-40">
                <option value="">Todas las categorías</option>
                {#each categories as cat}<option value={cat}>{cat}</option>{/each}
              </select>
            </div>
            <div class="max-h-72 overflow-y-auto divide-y divide-border-dark">
              {#each Object.entries(pickerByCategory) as [cat, mods]}
                {@const catSelected = mods.filter(m => packageForm.module_list.includes(m.technical_name)).length}
                {@const allCatSelected = catSelected === mods.length && mods.length > 0}
                {@const isOpen = expandedCategories.has(cat)}
                <!-- Header categoría -->
                <div class="flex items-center gap-2 px-3 py-2 bg-bg-card hover:bg-bg-page cursor-pointer group"
                  on:click={() => toggleCategory(cat)}>
                  <button type="button" class="p-0.5 rounded hover:bg-terracotta/20"
                    on:click|stopPropagation={() => toggleAllInCategory(cat)}
                    title={allCatSelected ? 'Deseleccionar categoría' : 'Seleccionar categoría'}>
                    {#if allCatSelected}
                      <CheckSquare size={15} class="text-terracotta" />
                    {:else if catSelected > 0}
                      <CheckSquare size={15} class="text-terracotta/50" />
                    {:else}
                      <Square size={15} class="text-gray-500 group-hover:text-gray-300" />
                    {/if}
                  </button>
                  <span class="text-xs font-semibold text-gray-300 uppercase tracking-wide flex-1">{cat}</span>
                  <span class="text-[10px] text-gray-500">{catSelected}/{mods.length}</span>
                  {#if isOpen}<ChevronDown size={12} class="text-gray-500" />
                  {:else}<ChevronRight size={12} class="text-gray-500" />{/if}
                </div>
                <!-- Módulos de la categoría -->
                {#if isOpen}
                  <div class="grid grid-cols-2 md:grid-cols-3 gap-0 bg-bg-page">
                    {#each mods as m}
                      {@const selected = packageForm.module_list.includes(m.technical_name)}
                      <label class="flex items-center gap-2 px-3 py-1.5 cursor-pointer hover:bg-bg-card transition-colors
                        {selected ? 'bg-terracotta/5' : ''}">
                        <input type="checkbox" checked={selected}
                          on:change={() => toggleModuleInPackage(m.technical_name)}
                          class="w-3.5 h-3.5 rounded accent-terracotta flex-shrink-0" />
                        <div class="min-w-0">
                          <div class="text-xs text-text-light truncate {selected ? 'font-medium' : ''}">
                            {m.display_name || m.technical_name}
                          </div>
                          {#if m.is_core}<span class="text-[9px] text-blue-400">core</span>{/if}
                        </div>
                      </label>
                    {/each}
                  </div>
                {/if}
              {/each}
              {#if Object.keys(pickerByCategory).length === 0}
                <div class="text-center py-6 text-gray-500 text-sm">
                  {modules.length === 0
                    ? 'Catálogo vacío. Usa "Importar V17" para cargar módulos.'
                    : 'Sin resultados para la búsqueda'}
                </div>
              {/if}
            </div>
          </div>
        {:else}
          <div class="border border-dashed border-border-dark rounded-lg p-6 text-center text-gray-500 text-sm">
            <Puzzle size={24} class="mx-auto mb-2 opacity-40" />
            El catálogo de módulos está vacío.<br>
            <button type="button" on:click={importFromFs} disabled={importing}
              class="text-terracotta hover:underline mt-1 inline-block">
              {importing ? 'Importando...' : 'Importar desde V17'}
            </button>
          </div>
        {/if}

        <div class="flex gap-3 mt-5 pt-4 border-t border-border-dark">
          <button type="submit" class="btn-accent">{editingPackageId ? 'Guardar cambios' : 'Crear paquete'}</button>
          <button type="button" class="btn-secondary" on:click={() => { showPackageForm = false; resetPackageForm(); }}>Cancelar</button>
        </div>
      </form>
    </div>
  {/if}

  <!-- ── Loading ── -->
  {#if loading}
    <div class="text-center py-16 text-gray-500">
      <div class="w-8 h-8 border-2 border-charcoal border-t-transparent rounded-full animate-spin mx-auto"></div>
      <p class="mt-3 text-sm">Cargando blueprints...</p>
    </div>

  <!-- ── Tab: Paquetes ── -->
  {:else if activeTab === 'packages'}
    {#if filteredPackages.length === 0}
      <div class="text-center py-16 text-gray-500 text-sm">
        {packages.length === 0 ? 'No hay paquetes. Crea uno o ejecuta el seed.' : 'Sin resultados'}
      </div>
    {:else}
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {#each filteredPackages as p}
          <div class="card hover:shadow-lg transition-shadow flex flex-col">
            <div class="flex items-start justify-between mb-2">
              <div>
                <h3 class="font-semibold text-text-primary text-sm">{p.display_name || p.name}</h3>
                <span class="text-[10px] text-gray-500 font-mono">{p.name}</span>
              </div>
              <div class="flex gap-1 flex-wrap justify-end">
                {#if p.plan_type}
                  <span class="text-[10px] px-1.5 py-0.5 rounded border
                    {p.plan_type === 'enterprise' ? 'border-purple-500/40 text-purple-400 bg-purple-500/10' :
                     p.plan_type === 'pro' ? 'border-blue-500/40 text-blue-400 bg-blue-500/10' :
                     'border-green-500/40 text-green-400 bg-green-500/10'}">
                    {p.plan_type}
                  </span>
                {/if}
                {#if p.is_default}
                  <span class="text-[10px] px-1.5 py-0.5 rounded border border-yellow-500/40 text-yellow-400 bg-yellow-500/10">default</span>
                {/if}
              </div>
            </div>
            {#if p.description}
              <p class="text-xs text-text-secondary mb-3 flex-1 line-clamp-2">{p.description}</p>
            {/if}
            <!-- Chips de módulos del paquete -->
            <div class="flex-1 mb-3">
              <div class="text-[10px] font-semibold uppercase text-gray-500 mb-1.5">
                {p.module_count || (Array.isArray(p.module_list) ? p.module_list.length : 0)} módulos
              </div>
              <div class="flex flex-wrap gap-1 max-h-20 overflow-hidden">
                {#each (Array.isArray(p.module_list) ? p.module_list : []).slice(0, 10) as tn}
                  {@const mod = modules.find(m => m.technical_name === tn)}
                  <span class="inline-block text-[10px] px-1.5 py-0.5 rounded
                    {mod?.is_core ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' : 'bg-gray-700 text-gray-300 border border-gray-600'}">
                    {mod?.display_name || tn}
                  </span>
                {/each}
                {#if (Array.isArray(p.module_list) ? p.module_list.length : 0) > 10}
                  <span class="text-[10px] text-gray-500 self-center">
                    +{(Array.isArray(p.module_list) ? p.module_list.length : 0) - 10} más
                  </span>
                {/if}
              </div>
            </div>
            <div class="mt-auto pt-3 border-t border-border-light flex items-center justify-between">
              <span class="text-lg font-bold text-text-primary">
                {p.base_price_monthly > 0 ? `$${p.base_price_monthly.toFixed(0)}/mes` : 'Incluido'}
              </span>
              <button class="btn-sm btn-secondary flex items-center gap-1" on:click={() => editPackage(p)}>
                <Pencil size={12} /> Editar
              </button>
            </div>
          </div>
        {/each}
      </div>
    {/if}

  <!-- ── Tab: Módulos ── -->
  {:else}
    {#if filteredModules.length === 0}
      <div class="text-center py-16 text-gray-500">
        {#if modules.length === 0}
          <Puzzle size={32} class="mx-auto mb-3 opacity-30" />
          <p class="text-sm">Catálogo vacío — usa el botón <strong>"Importar V17"</strong> para cargar módulos</p>
        {:else}
          <p class="text-sm">Sin módulos para los filtros seleccionados</p>
        {/if}
      </div>
    {:else}
      <div class="overflow-x-auto">
        <table class="table w-full text-sm">
          <thead>
            <tr>
              <th>Módulo</th>
              <th>Categoría</th>
              <th>Versión</th>
              <th>Tipo</th>
              <th>Partner</th>
              <th>Estado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {#each filteredModules as m}
              <tr>
                <td>
                  <div class="font-medium text-text-primary">{m.display_name || m.technical_name}</div>
                  <div class="text-[10px] text-gray-500 font-mono">{m.technical_name}</div>
                </td>
                <td class="text-xs">{m.category || '—'}</td>
                <td class="text-xs font-mono text-gray-400">{m.version || '—'}</td>
                <td>
                  <span class="text-[10px] px-1.5 py-0.5 rounded border
                    {m.is_core ? 'border-blue-500/40 text-blue-400 bg-blue-500/10' : 'border-orange-500/40 text-orange-400 bg-orange-500/10'}">
                    {m.is_core ? 'Core' : 'Add-on'}
                  </span>
                </td>
                <td>
                  {#if m.partner_allowed}
                    <ToggleRight size={16} class="text-green-400" />
                  {:else}
                    <ToggleLeft size={16} class="text-gray-600" />
                  {/if}
                </td>
                <td>
                  <span class="text-[10px] px-1.5 py-0.5 rounded border
                    {m.is_active ? 'border-green-500/40 text-green-400 bg-green-500/10' : 'border-gray-600 text-gray-500'}">
                    {m.is_active ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                <td>
                  <button class="btn-sm btn-secondary" on:click={() => editModule(m)}><Pencil size={12} /></button>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  {/if}
</div>

