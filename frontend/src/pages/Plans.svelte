<script lang="ts">
  import { onMount } from 'svelte';
  import { Package, Plus, Edit3, Trash2, Calculator, Users, DollarSign, Check, X, Globe, HardDrive, LayoutGrid, Building2, Archive, Zap } from 'lucide-svelte';
  import { billingApi } from '../lib/api/billing';
  import type { Plan, PlanCalculation } from '../lib/types';

  let plans: Plan[] = $state([]);
  let loading = $state(true);
  let error = $state('');

  // Modal state
  let showModal = $state(false);
  let editingPlan: Partial<Plan> | null = $state(null);
  let saving = $state(false);

  // Calculator
  let calcPlan = $state('');
  let calcUsers = $state(1);
  let calcResult: PlanCalculation | null = $state(null);
  let calculating = $state(false);

  // Form
  let form = $state({
    name: '',
    display_name: '',
    description: '',
    base_price: 0,
    price_per_user: 0,
    included_users: 1,
    max_users: 0,
    max_domains: 0,
    max_storage_mb: 0,
    max_websites: 1,
    max_companies: 1,
    max_backups: 0,
    max_api_calls_day: 0,
    stripe_price_id: '',
    stripe_product_id: '',
    features: '',
    sort_order: 0,
  });

  async function loadPlans() {
    loading = true;
    error = '';
    try {
      const data = await billingApi.getPlans(true);
      plans = data.items ?? [];
    } catch (e: any) {
      error = e.message || 'Error cargando planes';
    } finally {
      loading = false;
    }
  }

  function openCreate() {
    editingPlan = null;
    form = {
      name: '',
      display_name: '',
      description: '',
      base_price: 0,
      price_per_user: 0,
      included_users: 1,
      max_users: 0,
      max_domains: 0,
      max_storage_mb: 0,
      max_websites: 1,
      max_companies: 1,
      max_backups: 0,
      max_api_calls_day: 0,
      stripe_price_id: '',
      stripe_product_id: '',
      features: '',
      sort_order: plans.length + 1,
    };
    showModal = true;
  }

  function openEdit(plan: Plan) {
    editingPlan = plan;
    form = {
      name: plan.name,
      display_name: plan.display_name,
      description: plan.description || '',
      base_price: plan.base_price,
      price_per_user: plan.price_per_user,
      included_users: plan.included_users,
      max_users: plan.max_users,
      max_domains: plan.max_domains ?? 0,
      max_storage_mb: plan.max_storage_mb ?? 0,
      max_websites: plan.max_websites ?? 1,
      max_companies: plan.max_companies ?? 1,
      max_backups: plan.max_backups ?? 0,
      max_api_calls_day: plan.max_api_calls_day ?? 0,
      stripe_price_id: plan.stripe_price_id || '',
      stripe_product_id: plan.stripe_product_id || '',
      features: Array.isArray(plan.features) ? plan.features.join('\n') : '',
      sort_order: plan.sort_order,
    };
    showModal = true;
  }

  async function savePlan() {
    saving = true;
    try {
      const payload: any = {
        ...form,
        features: form.features ? JSON.stringify(form.features.split('\n').filter(f => f.trim())) : '[]',
        stripe_price_id: form.stripe_price_id || null,
        stripe_product_id: form.stripe_product_id || null,
      };

      if (editingPlan && editingPlan.id) {
        const { name, ...updateData } = payload;
        await billingApi.updatePlan(editingPlan.id, updateData);
      } else {
        await billingApi.createPlan(payload);
      }
      showModal = false;
      await loadPlans();
    } catch (e: any) {
      alert(e.message || 'Error guardando plan');
    } finally {
      saving = false;
    }
  }

  async function deletePlan(plan: Plan) {
    if (!confirm(`¿Desactivar plan "${plan.display_name}"? (${plan.active_subscribers} suscriptores activos)`)) return;
    try {
      await billingApi.deletePlan(plan.id);
      await loadPlans();
    } catch (e: any) {
      alert(e.message || 'Error eliminando plan');
    }
  }

  async function calculate() {
    if (!calcPlan || calcUsers < 1) return;
    calculating = true;
    try {
      calcResult = await billingApi.calculatePrice(calcPlan, calcUsers);
    } catch (e: any) {
      alert(e.message || 'Error calculando');
    } finally {
      calculating = false;
    }
  }

  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
  }

  function badgeClass(name: string): string {
    const map: Record<string, string> = {
      basic: 'badge-basic',
      pro: 'badge-pro',
      enterprise: 'badge-enterprise',
    };
    return map[name] || 'badge-neutral';
  }

  onMount(loadPlans);
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="page-title">Gestión de Planes</h1>
      <p class="page-subtitle">Administra planes, precios y facturación por usuario</p>
    </div>
    <button class="btn-accent flex items-center gap-2" onclick={openCreate}>
      <Plus size={16} />
      Nuevo Plan
    </button>
  </div>

  {#if error}
    <div class="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">{error}</div>
  {/if}

  {#if loading}
    <div class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-terracotta border-t-transparent"></div>
    </div>
  {:else}
    <!-- Plans Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {#each plans as plan (plan.id)}
        <div class="card relative {!plan.is_active ? 'opacity-60' : ''}">
          {#if !plan.is_active}
            <div class="absolute top-3 right-3 badge-error text-xs">Inactivo</div>
          {/if}

          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-lg bg-terracotta/20 flex items-center justify-center">
              <Package size={20} class="text-terracotta" />
            </div>
            <div>
              <h3 class="font-semibold text-text-light">{plan.display_name}</h3>
              <span class={badgeClass(plan.name)}>{plan.name}</span>
            </div>
          </div>

          <p class="text-gray-400 text-sm mb-4">{plan.description || 'Sin descripción'}</p>

          <!-- Pricing -->
          <div class="bg-dark-subtle rounded-lg p-4 mb-4">
            <div class="flex items-baseline gap-1 mb-2">
              <span class="text-3xl font-bold text-terracotta">{formatCurrency(plan.base_price)}</span>
              <span class="text-gray-500 text-sm">/mes</span>
            </div>
            <div class="text-sm text-gray-400 space-y-1">
              <div class="flex justify-between">
                <span>Usuarios incluidos</span>
                <span class="text-text-light font-medium">{plan.included_users}</span>
              </div>
              <div class="flex justify-between">
                <span>Precio por usuario extra</span>
                <span class="text-text-light font-medium">{formatCurrency(plan.price_per_user)}</span>
              </div>
              <div class="flex justify-between">
                <span>Máx. usuarios</span>
                <span class="text-text-light font-medium">{plan.max_users === 0 ? 'Ilimitado' : plan.max_users}</span>
              </div>
            </div>
          </div>

          <!-- Resource Quotas -->
          <div class="grid grid-cols-2 gap-2 mb-4 text-xs">
            <div class="flex items-center gap-1.5 text-gray-400" title="Dominios custom ({plan.max_domains === -1 ? 'ilimitado' : plan.max_domains === 0 ? 'no incluido' : plan.max_domains})">
              <Globe size={12} class="text-blue-400" />
              <span>Dominios: <span class="text-text-light font-medium">{plan.max_domains === -1 ? '∞' : plan.max_domains}</span></span>
            </div>
            <div class="flex items-center gap-1.5 text-gray-400" title="Almacenamiento ({plan.max_storage_mb === 0 ? 'ilimitado' : plan.max_storage_mb + ' MB'})">
              <HardDrive size={12} class="text-purple-400" />
              <span>Storage: <span class="text-text-light font-medium">{plan.max_storage_mb === 0 ? '∞' : plan.max_storage_mb + 'MB'}</span></span>
            </div>
            <div class="flex items-center gap-1.5 text-gray-400" title="Websites Odoo">
              <LayoutGrid size={12} class="text-green-400" />
              <span>Websites: <span class="text-text-light font-medium">{plan.max_websites}</span></span>
            </div>
            <div class="flex items-center gap-1.5 text-gray-400" title="Multi-company">
              <Building2 size={12} class="text-yellow-400" />
              <span>Companies: <span class="text-text-light font-medium">{plan.max_companies}</span></span>
            </div>
            <div class="flex items-center gap-1.5 text-gray-400" title="Backups retenidos ({plan.max_backups === 0 ? 'ilimitado' : plan.max_backups})">
              <Archive size={12} class="text-teal-400" />
              <span>Backups: <span class="text-text-light font-medium">{plan.max_backups === 0 ? '∞' : plan.max_backups}</span></span>
            </div>
            <div class="flex items-center gap-1.5 text-gray-400" title="API calls/día ({plan.max_api_calls_day === 0 ? 'ilimitado' : plan.max_api_calls_day})">
              <Zap size={12} class="text-orange-400" />
              <span>API/día: <span class="text-text-light font-medium">{plan.max_api_calls_day === 0 ? '∞' : plan.max_api_calls_day}</span></span>
            </div>
          </div>

          <!-- Features -->
          {#if plan.features && plan.features.length > 0}
            <ul class="space-y-1 mb-4">
              {#each plan.features as feature}
                <li class="flex items-center gap-2 text-sm text-gray-400">
                  <Check size={14} class="text-green-400 flex-shrink-0" />
                  {feature}
                </li>
              {/each}
            </ul>
          {/if}

          <!-- Stats -->
          <div class="flex items-center justify-between text-sm border-t border-border-dark pt-3 mt-3">
            <span class="text-gray-500">
              <Users size={14} class="inline mr-1" />
              {plan.active_subscribers} suscriptores
            </span>
            <span class="text-gray-500">
              <DollarSign size={14} class="inline mr-1" />
              MRR: {formatCurrency(plan.base_price * plan.active_subscribers)}
            </span>
          </div>

          <!-- Stripe -->
          {#if plan.stripe_price_id}
            <div class="text-xs text-gray-600 mt-2 truncate" title={plan.stripe_price_id}>
              Stripe: {plan.stripe_price_id}
            </div>
          {:else}
            <div class="text-xs text-yellow-500/60 mt-2">⚠ Sin Stripe Price ID</div>
          {/if}

          <!-- Actions -->
          <div class="flex gap-2 mt-4">
            <button class="btn-secondary btn-sm flex-1 flex items-center justify-center gap-1" onclick={() => openEdit(plan)}>
              <Edit3 size={14} /> Editar
            </button>
            <button
              class="btn-sm px-3 text-red-400 hover:bg-red-500/10 border border-border-dark rounded-lg transition-colors"
              onclick={() => deletePlan(plan)}
              disabled={plan.active_subscribers > 0}
              title={plan.active_subscribers > 0 ? 'No se puede desactivar con suscriptores activos' : 'Desactivar plan'}
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>
      {/each}
    </div>

    <!-- Price Calculator -->
    <div class="card">
      <h2 class="section-heading flex items-center gap-2 mb-4">
        <Calculator size={18} />
        Calculadora de Precios
      </h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="label" for="calc-plan">Plan</label>
          <select id="calc-plan" class="input" bind:value={calcPlan}>
            <option value="">Seleccionar plan...</option>
            {#each plans.filter(p => p.is_active) as p}
              <option value={p.name}>{p.display_name} ({formatCurrency(p.base_price)})</option>
            {/each}
          </select>
        </div>
        <div>
          <label class="label" for="calc-users">Cantidad de Usuarios</label>
          <div class="flex items-center gap-2">
            <button class="btn-secondary btn-sm" onclick={() => { calcUsers = Math.max(1, calcUsers - 1); calcResult = null; }}>−</button>
            <input id="calc-users" type="number" class="input text-center" min="1" bind:value={calcUsers} onchange={() => { calcResult = null; }} />
            <button class="btn-secondary btn-sm" onclick={() => { calcUsers++; calcResult = null; }}>+</button>
          </div>
        </div>
        <div class="flex items-end">
          <button class="btn-accent w-full" onclick={calculate} disabled={calculating || !calcPlan}>
            {calculating ? 'Calculando...' : 'Calcular'}
          </button>
        </div>
      </div>

      {#if calcResult}
        <div class="mt-4 bg-dark-subtle rounded-lg p-4">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div class="text-xs text-gray-500 uppercase">Base</div>
              <div class="text-lg font-bold text-text-light">{formatCurrency(calcResult.base_price)}</div>
            </div>
            <div>
              <div class="text-xs text-gray-500 uppercase">Usuarios Extra ({calcResult.extra_users})</div>
              <div class="text-lg font-bold text-text-light">{formatCurrency(calcResult.extra_cost)}</div>
            </div>
            <div>
              <div class="text-xs text-gray-500 uppercase">Total Mensual</div>
              <div class="text-2xl font-bold text-terracotta">{formatCurrency(calcResult.monthly_total)}</div>
            </div>
            <div>
              <div class="text-xs text-gray-500 uppercase">Total Anual</div>
              <div class="text-lg font-bold text-green-400">{formatCurrency(calcResult.monthly_total * 12)}</div>
            </div>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<!-- Edit/Create Modal -->
{#if showModal}
  <div class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" role="dialog">
    <div class="bg-charcoal rounded-xl border border-border-dark w-full max-w-lg max-h-[90vh] overflow-y-auto">
      <div class="flex items-center justify-between p-6 border-b border-border-dark">
        <h2 class="text-lg font-semibold text-text-light">{editingPlan ? 'Editar Plan' : 'Nuevo Plan'}</h2>
        <button class="text-gray-400 hover:text-text-light" onclick={() => { showModal = false; }}>
          <X size={20} />
        </button>
      </div>

      <form class="p-6 space-y-4" onsubmit={(e) => { e.preventDefault(); savePlan(); }}>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label" for="plan-name">Nombre (ID)</label>
            <input id="plan-name" class="input" bind:value={form.name} required disabled={!!editingPlan} placeholder="basic" />
          </div>
          <div>
            <label class="label" for="plan-display">Nombre visible</label>
            <input id="plan-display" class="input" bind:value={form.display_name} required placeholder="Basic" />
          </div>
        </div>

        <div>
          <label class="label" for="plan-desc">Descripción</label>
          <input id="plan-desc" class="input" bind:value={form.description} placeholder="Descripción del plan" />
        </div>

        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="label" for="plan-base">Precio Base (USD)</label>
            <input id="plan-base" type="number" step="0.01" class="input" bind:value={form.base_price} required />
          </div>
          <div>
            <label class="label" for="plan-ppu">Precio/Usuario Extra</label>
            <input id="plan-ppu" type="number" step="0.01" class="input" bind:value={form.price_per_user} />
          </div>
          <div>
            <label class="label" for="plan-incl">Usuarios Incluidos</label>
            <input id="plan-incl" type="number" min="0" class="input" bind:value={form.included_users} />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label" for="plan-max">Máx. Usuarios (0=ilimitado)</label>
            <input id="plan-max" type="number" min="0" class="input" bind:value={form.max_users} />
          </div>
          <div>
            <label class="label" for="plan-sort">Orden</label>
            <input id="plan-sort" type="number" class="input" bind:value={form.sort_order} />
          </div>
        </div>

        <!-- Resource Quotas -->
        <div class="border border-border-dark rounded-lg p-4 space-y-3">
          <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">Cuotas de Recursos</h3>
          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="label text-xs" for="plan-domains">Dominios (-1=∞, 0=no)</label>
              <input id="plan-domains" type="number" min="-1" class="input" bind:value={form.max_domains} />
            </div>
            <div>
              <label class="label text-xs" for="plan-storage">Storage MB (0=∞)</label>
              <input id="plan-storage" type="number" min="0" class="input" bind:value={form.max_storage_mb} />
            </div>
            <div>
              <label class="label text-xs" for="plan-websites">Websites</label>
              <input id="plan-websites" type="number" min="1" class="input" bind:value={form.max_websites} />
            </div>
            <div>
              <label class="label text-xs" for="plan-companies">Companies</label>
              <input id="plan-companies" type="number" min="1" class="input" bind:value={form.max_companies} />
            </div>
            <div>
              <label class="label text-xs" for="plan-backups">Backups (0=∞)</label>
              <input id="plan-backups" type="number" min="0" class="input" bind:value={form.max_backups} />
            </div>
            <div>
              <label class="label text-xs" for="plan-api">API calls/día (0=∞)</label>
              <input id="plan-api" type="number" min="0" class="input" bind:value={form.max_api_calls_day} />
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label" for="plan-stripe-price">Stripe Price ID</label>
            <input id="plan-stripe-price" class="input" bind:value={form.stripe_price_id} placeholder="price_1xxx..." />
          </div>
          <div>
            <label class="label" for="plan-stripe-prod">Stripe Product ID</label>
            <input id="plan-stripe-prod" class="input" bind:value={form.stripe_product_id} placeholder="prod_1xxx..." />
          </div>
        </div>

        <div>
          <label class="label" for="plan-features">Características (una por línea)</label>
          <textarea id="plan-features" class="input min-h-[100px]" bind:value={form.features} placeholder="1 usuario incluido&#10;Soporte por email&#10;Módulos básicos"></textarea>
        </div>

        <div class="flex gap-3 pt-2">
          <button type="submit" class="btn-accent flex-1" disabled={saving}>
            {saving ? 'Guardando...' : (editingPlan ? 'Actualizar' : 'Crear Plan')}
          </button>
          <button type="button" class="btn-secondary" onclick={() => { showModal = false; }}>Cancelar</button>
        </div>
      </form>
    </div>
  </div>
{/if}
