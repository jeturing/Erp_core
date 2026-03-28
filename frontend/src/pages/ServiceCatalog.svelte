<script lang="ts">
  import { onMount } from 'svelte';
  import { partnersApi } from '../lib/api/partners';
  import { billingApi } from '../lib/api/billing';
  import { toasts } from '../lib/stores';
  import type { ServiceCatalogItemType, Plan, PlanCatalogLinkType } from '../lib/types';
  import {
    ShoppingBag, Plus, Pencil, Trash2, Search, Link2, Unlink,
    Package, Check, X, RotateCcw, DollarSign, Filter, ChevronDown,
    ChevronRight, Tag, Layers,
  } from 'lucide-svelte';

  // Data
  let catalog: ServiceCatalogItemType[] = $state([]);
  let plans: Plan[] = $state([]);
  let planLinks: PlanCatalogLinkType[] = $state([]);
  let categories: Array<{ value: string; label: string }> = $state([]);
  let loading = $state(true);
  let search = $state('');
  let categoryFilter = $state('');
  let showInactive = $state(false);

  // Modal state
  let showItemModal = $state(false);
  let editingItem: ServiceCatalogItemType | null = $state(null);
  let saving = $state(false);

  // Link modal
  let showLinkModal = $state(false);
  let linkingItem: ServiceCatalogItemType | null = $state(null);
  let linkForm = $state({ plan_id: 0, included_quantity: 1, is_included: true, discount_percent: 0, notes: '' });

  // Expanded categories
  let expandedCategories: Set<string> = $state(new Set());

  // Form
  let form = $state({
    category: '',
    name: '',
    description: '',
    unit: 'Por mes',
    price_monthly: 0,
    price_max: 0,
    is_addon: false,
    requires_service_id: null as number | null,
    min_quantity: 1,
    sort_order: 0,
    is_email_package: false,
    email_quota_monthly: 0,
    email_burst_limit_60m: 0,
    email_overage_price: 0,
  });

  const EMAIL_PACKAGE_CODE = 'postal_email_package';

  const unitOptions = [
    'Por mes', 'Por usuario', 'Por servidor', 'Por cuenta',
    'Por dominio', 'Por bloque', 'Por hora', 'Único',
  ];

  async function loadData() {
    loading = true;
    try {
      const [catalogRes, plansRes, linksRes] = await Promise.all([
        partnersApi.getCatalog(undefined, showInactive),
        billingApi.getPlans(true),
        partnersApi.getPlanCatalogLinks(),
      ]);
      catalog = catalogRes.items ?? [];
      categories = catalogRes.categories ?? [];
      plans = plansRes.items ?? [];
      planLinks = linksRes.links ?? [];

      // Expandir todas las categorías al cargar
      if (expandedCategories.size === 0) {
        categories.forEach(c => expandedCategories.add(c.value));
        expandedCategories = new Set(expandedCategories);
      }
    } catch (e: any) {
      toasts.error(e.message || 'Error cargando catálogo');
    } finally {
      loading = false;
    }
  }

  // Computed
  let filtered = $derived(catalog.filter(item => {
    const matchesSearch = !search ||
      item.name.toLowerCase().includes(search.toLowerCase()) ||
      (item.description || '').toLowerCase().includes(search.toLowerCase());
    const matchesCategory = !categoryFilter || item.category === categoryFilter;
    return matchesSearch && matchesCategory;
  }));

  let groupedByCategory = $derived((() => {
    const groups: Record<string, ServiceCatalogItemType[]> = {};
    for (const item of filtered) {
      const cat = item.category || 'other';
      if (!groups[cat]) groups[cat] = [];
      groups[cat].push(item);
    }
    return groups;
  })());

  let totalMonthlyRevenue = $derived(catalog.filter(i => i.is_active).reduce((s, i) => s + i.price_monthly, 0));
  let activeCount = $derived(catalog.filter(i => i.is_active).length);
  let addonCount = $derived(catalog.filter(i => i.is_addon && i.is_active).length);
  let linkedCount = $derived(catalog.filter(i => (i.linked_plans?.length || 0) > 0).length);

  function toggleCategory(cat: string) {
    if (expandedCategories.has(cat)) {
      expandedCategories.delete(cat);
    } else {
      expandedCategories.add(cat);
    }
    expandedCategories = new Set(expandedCategories);
  }

  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
  }

  function categoryLabel(value: string): string {
    return value.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }

  function categoryColor(cat: string): string {
    const colors: Record<string, string> = {
      saas_platform: 'text-blue-400',
      saas_support: 'text-emerald-400',
      core_financiero: 'text-amber-400',
      vciso: 'text-purple-400',
      soc: 'text-red-400',
      cloud_devops: 'text-cyan-400',
      payments_pos: 'text-pink-400',
    };
    return colors[cat] || 'text-gray-400';
  }

  function isEmailPackage(item: Pick<ServiceCatalogItemType, 'service_code' | 'metadata_json'>): boolean {
    return item.service_code === EMAIL_PACKAGE_CODE || item.metadata_json?.kind === EMAIL_PACKAGE_CODE;
  }

  function formatInteger(value: number | null | undefined): string {
    return new Intl.NumberFormat('es-DO').format(Number(value || 0));
  }

  // ── CRUD ──

  function openCreate() {
    editingItem = null;
    form = {
      category: categories[0]?.value || 'saas_platform',
      name: '',
      description: '',
      unit: 'Por mes',
      price_monthly: 0,
      price_max: 0,
      is_addon: false,
      requires_service_id: null,
      min_quantity: 1,
      sort_order: catalog.length + 1,
      is_email_package: false,
      email_quota_monthly: 0,
      email_burst_limit_60m: 0,
      email_overage_price: 0,
    };
    showItemModal = true;
  }

  function openEdit(item: ServiceCatalogItemType) {
    const emailPackage = isEmailPackage(item);
    editingItem = item;
    form = {
      category: item.category,
      name: item.name,
      description: item.description || '',
      unit: item.unit,
      price_monthly: item.price_monthly,
      price_max: item.price_max || 0,
      is_addon: item.is_addon,
      requires_service_id: item.requires_service_id,
      min_quantity: item.min_quantity,
      sort_order: item.sort_order,
      is_email_package: emailPackage,
      email_quota_monthly: Number(item.metadata_json?.email_quota_monthly || 0),
      email_burst_limit_60m: Number(item.metadata_json?.email_burst_limit_60m || 0),
      email_overage_price: Number(item.metadata_json?.email_overage_price || 0),
    };
    showItemModal = true;
  }

  async function saveItem() {
    if (!form.name.trim()) { toasts.error('Nombre requerido'); return; }
    if (form.price_monthly <= 0) { toasts.error('Precio debe ser mayor a 0'); return; }
    saving = true;
    try {
      const isEmailAddon = form.is_email_package;
      const payload: any = {
        category: form.category,
        name: form.name,
        description: form.description,
        unit: isEmailAddon ? 'Por mes' : form.unit,
        price_monthly: form.price_monthly,
        price_max: form.price_max || null,
        is_addon: isEmailAddon ? true : form.is_addon,
        requires_service_id: form.requires_service_id || null,
        min_quantity: form.min_quantity,
        sort_order: form.sort_order,
        service_code: isEmailAddon ? EMAIL_PACKAGE_CODE : null,
        metadata_json: isEmailAddon ? {
          kind: EMAIL_PACKAGE_CODE,
          email_quota_monthly: Number(form.email_quota_monthly || 0),
          email_burst_limit_60m: Number(form.email_burst_limit_60m || 0),
          email_overage_price: Number(form.email_overage_price || 0),
        } : null,
      };

      if (editingItem) {
        await partnersApi.updateCatalogItem(editingItem.id, payload);
        toasts.success('Servicio actualizado');
      } else {
        await partnersApi.createCatalogItem(payload);
        toasts.success('Servicio creado');
      }
      showItemModal = false;
      await loadData();
    } catch (e: any) {
      toasts.error(e.message || 'Error guardando');
    } finally {
      saving = false;
    }
  }

  async function deleteItem(item: ServiceCatalogItemType) {
    if (!confirm(`¿Desactivar "${item.name}"?`)) return;
    try {
      await partnersApi.deleteCatalogItem(item.id);
      toasts.success('Servicio desactivado');
      await loadData();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  async function reactivateItem(item: ServiceCatalogItemType) {
    try {
      await partnersApi.reactivateCatalogItem(item.id);
      toasts.success('Servicio reactivado');
      await loadData();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  // ── Plan Linking ──

  function openLinkModal(item: ServiceCatalogItemType) {
    linkingItem = item;
    // Filter out plans already linked
    const linkedPlanIds = (item.linked_plans || []).map(lp => lp.plan_id);
    const availablePlans = plans.filter(p => !linkedPlanIds.includes(p.id) && p.is_active);
    if (availablePlans.length === 0) {
      toasts.error('Todos los planes activos ya están vinculados a este servicio');
      return;
    }
    linkForm = { plan_id: availablePlans[0].id, included_quantity: 1, is_included: true, discount_percent: 0, notes: '' };
    showLinkModal = true;
  }

  async function savePlanLink() {
    if (!linkingItem || !linkForm.plan_id) return;
    try {
      await partnersApi.createPlanCatalogLink({
        plan_id: linkForm.plan_id,
        catalog_item_id: linkingItem.id,
        included_quantity: linkForm.included_quantity,
        is_included: linkForm.is_included,
        discount_percent: linkForm.discount_percent,
        notes: linkForm.notes || undefined,
      });
      toasts.success('Plan vinculado');
      showLinkModal = false;
      await loadData();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  async function unlinkPlan(linkId: number) {
    if (!confirm('¿Desvincular este plan?')) return;
    try {
      await partnersApi.deletePlanCatalogLink(linkId);
      toasts.success('Plan desvinculado');
      await loadData();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  onMount(loadData);
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><ShoppingBag size={24} /> Catálogo de Servicios SAJET</h1>
      <p class="page-subtitle">Administra servicios, precios y vinculación con planes</p>
    </div>
    <button class="btn-accent flex items-center gap-2" onclick={openCreate}>
      <Plus size={16} /> Nuevo Servicio
    </button>
  </div>

  <!-- Stats -->
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
    <div class="stat-card">
      <div class="text-xs font-semibold uppercase text-gray-500 mb-1">Servicios Activos</div>
      <div class="text-2xl font-bold text-text-light">{activeCount}</div>
    </div>
    <div class="stat-card">
      <div class="text-xs font-semibold uppercase text-gray-500 mb-1">Categorías</div>
      <div class="text-2xl font-bold text-blue-400">{Object.keys(groupedByCategory).length}</div>
    </div>
    <div class="stat-card">
      <div class="text-xs font-semibold uppercase text-gray-500 mb-1">Add-ons</div>
      <div class="text-2xl font-bold text-amber-400">{addonCount}</div>
    </div>
    <div class="stat-card">
      <div class="text-xs font-semibold uppercase text-gray-500 mb-1">Vinculados a Planes</div>
      <div class="text-2xl font-bold text-emerald-400">{linkedCount}</div>
    </div>
  </div>

  <!-- Filters -->
  <div class="flex flex-col sm:flex-row gap-3">
    <div class="relative flex-1">
      <Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
      <input type="text" bind:value={search} placeholder="Buscar servicio..." class="input pl-10 w-full" />
    </div>
    <select bind:value={categoryFilter} class="input w-auto">
      <option value="">Todas las categorías</option>
      {#each categories as cat}
        <option value={cat.value}>{cat.label}</option>
      {/each}
    </select>
    <label class="flex items-center gap-2 text-sm text-gray-400 cursor-pointer select-none">
      <input type="checkbox" bind:checked={showInactive} onchange={() => loadData()} class="accent-terracotta" />
      Mostrar inactivos
    </label>
  </div>

  {#if loading}
    <div class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-terracotta border-t-transparent"></div>
    </div>
  {:else if filtered.length === 0}
    <div class="text-center py-12 text-gray-500">
      <ShoppingBag size={48} class="mx-auto mb-3 opacity-30" />
      <p>No hay servicios en el catálogo</p>
      <button class="btn-accent mt-4" onclick={openCreate}>Crear el primer servicio</button>
    </div>
  {:else}
    <!-- Catalog by Category -->
    {#each Object.entries(groupedByCategory) as [category, items]}
      <div class="card">
        <button
          class="w-full flex items-center justify-between py-1 text-left"
          onclick={() => toggleCategory(category)}
        >
          <div class="flex items-center gap-3">
            <Layers size={18} class={categoryColor(category)} />
            <h2 class="text-base font-semibold text-text-light">{categoryLabel(category)}</h2>
            <span class="badge-neutral text-xs">{items.length} servicios</span>
          </div>
          {#if expandedCategories.has(category)}
            <ChevronDown size={18} class="text-gray-500" />
          {:else}
            <ChevronRight size={18} class="text-gray-500" />
          {/if}
        </button>

        {#if expandedCategories.has(category)}
          <div class="mt-4 space-y-3">
            {#each items as item (item.id)}
              <div class="bg-dark-subtle rounded-lg p-4 {!item.is_active ? 'opacity-50 border border-red-500/20' : ''}">
                <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
                  <!-- Info -->
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 flex-wrap">
                      <h3 class="font-semibold text-text-light">{item.name}</h3>
                      {#if item.is_addon}
                        <span class="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 font-semibold uppercase">Add-on</span>
                      {/if}
                      {#if isEmailPackage(item)}
                        <span class="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 font-semibold uppercase">Correo</span>
                      {/if}
                      {#if !item.is_active}
                        <span class="text-[10px] px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 font-semibold uppercase">Inactivo</span>
                      {/if}
                    </div>
                    {#if item.description}
                      <p class="text-sm text-gray-500 mt-0.5">{item.description}</p>
                    {/if}
                    <div class="flex items-center gap-4 mt-2 text-xs text-gray-500">
                      <span class="flex items-center gap-1"><Tag size={12} /> {item.unit}</span>
                      <span>Mín: {item.min_quantity}</span>
                      {#if item.requires_service_id}
                        <span class="text-amber-400">Requiere servicio #{item.requires_service_id}</span>
                      {/if}
                    </div>
                    {#if isEmailPackage(item)}
                      <div class="mt-3 grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
                        <div class="rounded border border-blue-500/20 bg-blue-500/5 px-2.5 py-2">
                          <span class="block text-gray-500 uppercase text-[10px] mb-1">Cuota mensual</span>
                          <span class="font-semibold text-blue-300">{formatInteger(Number(item.metadata_json?.email_quota_monthly || 0))} emails</span>
                        </div>
                        <div class="rounded border border-emerald-500/20 bg-emerald-500/5 px-2.5 py-2">
                          <span class="block text-gray-500 uppercase text-[10px] mb-1">Ventana 60m</span>
                          <span class="font-semibold text-emerald-300">{formatInteger(Number(item.metadata_json?.email_burst_limit_60m || 0))} envíos</span>
                        </div>
                        <div class="rounded border border-terracotta/20 bg-terracotta/5 px-2.5 py-2">
                          <span class="block text-gray-500 uppercase text-[10px] mb-1">Sobreuso</span>
                          <span class="font-semibold text-terracotta">{formatCurrency(Number(item.metadata_json?.email_overage_price || 0))}</span>
                        </div>
                      </div>
                    {/if}
                  </div>

                  <!-- Pricing -->
                  <div class="flex items-center gap-6 flex-shrink-0">
                    <div class="text-right">
                      <div class="text-lg font-bold text-terracotta font-mono">
                        {formatCurrency(item.price_monthly)}
                        {#if item.price_max}
                          <span class="text-gray-500">–</span> {formatCurrency(item.price_max)}
                        {/if}
                      </div>
                      <div class="text-[10px] text-gray-500 uppercase">/ mes</div>
                    </div>

                    <!-- Actions -->
                    <div class="flex items-center gap-1">
                      <button class="btn-sm btn-secondary" title="Vincular a plan" onclick={() => openLinkModal(item)}>
                        <Link2 size={14} />
                      </button>
                      <button class="btn-sm btn-secondary" title="Editar" onclick={() => openEdit(item)}>
                        <Pencil size={14} />
                      </button>
                      {#if item.is_active}
                        <button class="btn-sm text-red-400 hover:bg-red-500/10 border border-border-dark rounded-lg transition-colors" title="Desactivar" onclick={() => deleteItem(item)}>
                          <Trash2 size={14} />
                        </button>
                      {:else}
                        <button class="btn-sm text-emerald-400 hover:bg-emerald-500/10 border border-border-dark rounded-lg transition-colors" title="Reactivar" onclick={() => reactivateItem(item)}>
                          <RotateCcw size={14} />
                        </button>
                      {/if}
                    </div>
                  </div>
                </div>

                <!-- Linked Plans -->
                {#if item.linked_plans && item.linked_plans.length > 0}
                  <div class="mt-3 pt-3 border-t border-border-dark">
                    <div class="flex items-center gap-2 mb-2">
                      <Package size={14} class="text-gray-500" />
                      <span class="text-xs font-semibold text-gray-500 uppercase">Planes vinculados</span>
                    </div>
                    <div class="flex flex-wrap gap-2">
                      {#each item.linked_plans as lp}
                        <div class="flex items-center gap-1.5 bg-charcoal rounded px-2.5 py-1 text-xs border border-border-dark">
                          <Package size={12} class="text-terracotta" />
                          <span class="font-semibold text-text-light">{lp.plan_name}</span>
                          {#if lp.is_included}
                            <span class="text-emerald-400">✓ Incluido</span>
                          {:else}
                            <span class="text-amber-400">-{lp.discount_percent}%</span>
                          {/if}
                          <span class="text-gray-500">×{lp.included_quantity}</span>
                          <button class="ml-1 text-red-400 hover:text-red-300" title="Desvincular" onclick={() => unlinkPlan(lp.link_id)}>
                            <Unlink size={12} />
                          </button>
                        </div>
                      {/each}
                    </div>
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/each}
  {/if}
</div>

<!-- Create/Edit Item Modal -->
{#if showItemModal}
  <div class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" role="dialog">
    <div class="bg-charcoal rounded-xl border border-border-dark w-full max-w-lg max-h-[90vh] overflow-y-auto">
      <div class="flex items-center justify-between p-6 border-b border-border-dark">
        <h2 class="text-lg font-semibold text-text-light">{editingItem ? 'Editar Servicio' : 'Nuevo Servicio'}</h2>
        <button class="text-gray-400 hover:text-text-light" onclick={() => { showItemModal = false; }}>
          <X size={20} />
        </button>
      </div>

      <form class="p-6 space-y-4" onsubmit={(e) => { e.preventDefault(); saveItem(); }}>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label" for="cat-category">Categoría</label>
            <select id="cat-category" class="input w-full" bind:value={form.category} required>
              {#each categories as cat}
                <option value={cat.value}>{cat.label}</option>
              {/each}
            </select>
          </div>
          <div>
            <label class="label" for="cat-name">Nombre</label>
            <input id="cat-name" class="input w-full" bind:value={form.name} required placeholder="Odoo SaaS Basic" />
          </div>
        </div>

        <div>
          <label class="label" for="cat-desc">Descripción</label>
          <textarea id="cat-desc" class="input w-full" rows="2" bind:value={form.description} placeholder="Descripción del servicio"></textarea>
        </div>

        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="label" for="cat-price">Precio Mensual (USD)</label>
            <input id="cat-price" type="number" step="0.01" min="0" class="input w-full" bind:value={form.price_monthly} required />
          </div>
          <div>
            <label class="label" for="cat-pricemax">Precio Máx. (rango)</label>
            <input id="cat-pricemax" type="number" step="0.01" min="0" class="input w-full" bind:value={form.price_max} />
          </div>
          <div>
            <label class="label" for="cat-unit">Unidad</label>
            <select id="cat-unit" class="input w-full" bind:value={form.unit}>
              {#each unitOptions as u}
                <option value={u}>{u}</option>
              {/each}
            </select>
          </div>
        </div>

        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="label" for="cat-minqty">Cantidad Mín.</label>
            <input id="cat-minqty" type="number" min="1" class="input w-full" bind:value={form.min_quantity} />
          </div>
          <div>
            <label class="label" for="cat-sort">Orden</label>
            <input id="cat-sort" type="number" class="input w-full" bind:value={form.sort_order} />
          </div>
          <div>
            <label class="label" for="cat-dep">Requiere (ID)</label>
            <input id="cat-dep" type="number" min="0" class="input w-full" bind:value={form.requires_service_id} placeholder="Opcional" />
          </div>
        </div>

        <div>
          <label class="flex items-center gap-2 cursor-pointer select-none text-sm text-gray-400">
            <input type="checkbox" bind:checked={form.is_addon} class="accent-terracotta" />
            Es un add-on (requiere servicio base)
          </label>
        </div>

        <div class="rounded-lg border border-blue-500/20 bg-blue-500/5 p-4 space-y-3">
          <label class="flex items-center gap-2 cursor-pointer select-none text-sm text-blue-100 font-medium">
            <input
              type="checkbox"
              bind:checked={form.is_email_package}
              class="accent-terracotta"
              onchange={() => {
                if (form.is_email_package) {
                  form.is_addon = true;
                  form.unit = 'Por mes';
                }
              }}
            />
            Configurar como paquete de correo transaccional / masivo
          </label>

          {#if form.is_email_package}
            <p class="text-xs text-blue-200/80">
              Este servicio quedará listo para venderse en el portal del cliente y en el portal partner como paquete mensual de correo.
            </p>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label class="label" for="cat-email-quota">Cuota mensual</label>
                <input
                  id="cat-email-quota"
                  type="number"
                  min="0"
                  class="input w-full"
                  bind:value={form.email_quota_monthly}
                  placeholder="50000"
                />
              </div>
              <div>
                <label class="label" for="cat-email-burst">Límite 60 min</label>
                <input
                  id="cat-email-burst"
                  type="number"
                  min="0"
                  class="input w-full"
                  bind:value={form.email_burst_limit_60m}
                  placeholder="10000"
                />
              </div>
              <div>
                <label class="label" for="cat-email-overage">Precio sobreuso</label>
                <input
                  id="cat-email-overage"
                  type="number"
                  min="0"
                  step="0.0001"
                  class="input w-full"
                  bind:value={form.email_overage_price}
                  placeholder="0.0025"
                />
              </div>
            </div>
          {/if}
        </div>

        <div class="flex gap-3 pt-2">
          <button type="submit" class="btn-accent flex-1" disabled={saving}>
            {saving ? 'Guardando...' : (editingItem ? 'Actualizar' : 'Crear Servicio')}
          </button>
          <button type="button" class="btn-secondary" onclick={() => { showItemModal = false; }}>Cancelar</button>
        </div>
      </form>
    </div>
  </div>
{/if}

<!-- Link to Plan Modal -->
{#if showLinkModal && linkingItem}
  <div class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" role="dialog">
    <div class="bg-charcoal rounded-xl border border-border-dark w-full max-w-md">
      <div class="flex items-center justify-between p-6 border-b border-border-dark">
        <h2 class="text-lg font-semibold text-text-light">Vincular a Plan</h2>
        <button class="text-gray-400 hover:text-text-light" onclick={() => { showLinkModal = false; }}>
          <X size={20} />
        </button>
      </div>

      <form class="p-6 space-y-4" onsubmit={(e) => { e.preventDefault(); savePlanLink(); }}>
        <div class="bg-dark-subtle rounded p-3 text-sm">
          <span class="text-gray-500">Servicio:</span>
          <span class="font-semibold text-text-light ml-1">{linkingItem.name}</span>
          <span class="text-terracotta ml-1">({formatCurrency(linkingItem.price_monthly)}/mes)</span>
        </div>

        <div>
          <label class="label" for="link-plan">Plan</label>
          <select id="link-plan" class="input w-full" bind:value={linkForm.plan_id} required>
            {#each plans.filter(p => p.is_active && !(linkingItem?.linked_plans || []).some(lp => lp.plan_id === p.id)) as p}
              <option value={p.id}>{p.display_name} ({formatCurrency(p.base_price)})</option>
            {/each}
          </select>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label" for="link-qty">Cantidad Incluida</label>
            <input id="link-qty" type="number" min="1" class="input w-full" bind:value={linkForm.included_quantity} />
          </div>
          <div>
            <label class="label" for="link-discount">Descuento %</label>
            <input id="link-discount" type="number" min="0" max="100" step="0.1" class="input w-full" bind:value={linkForm.discount_percent} />
          </div>
        </div>

        <label class="flex items-center gap-2 cursor-pointer select-none text-sm text-gray-400">
          <input type="checkbox" bind:checked={linkForm.is_included} class="accent-terracotta" />
          Incluido en el plan (sin costo adicional)
        </label>

        <div>
          <label class="label" for="link-notes">Notas</label>
          <input id="link-notes" class="input w-full" bind:value={linkForm.notes} placeholder="Opcional" />
        </div>

        <div class="flex gap-3 pt-2">
          <button type="submit" class="btn-accent flex-1">Vincular</button>
          <button type="button" class="btn-secondary" onclick={() => { showLinkModal = false; }}>Cancelar</button>
        </div>
      </form>
    </div>
  </div>
{/if}
