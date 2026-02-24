<script lang="ts">
  import { onMount } from 'svelte';
  import { domainsStore, domainStats } from '../lib/stores';
  import { toasts } from '../lib/stores/toast';
  import { api } from '../lib/api/client';
  import { plansApi, type Plan } from '../lib/api/plans';
  import { formatDate } from '../lib/utils/formatters';
  import {
    Plus, Check, X, CircleCheck, CircleX, Globe, Shield, ShieldCheck,
    Server, RefreshCw, Trash2, ChevronDown, ExternalLink, Info, Zap,
    AlertTriangle, Pencil
  } from 'lucide-svelte';
  import type { Domain } from '../lib/types';

  // ─── State ───
  let domains = $state<Domain[]>([]);
  let showForm = $state(false);
  let loading = $state(true);
  let createInstructions = $state<any>(null);

  // Customer selector
  interface CustomerOption {
    id: number;
    company_name: string;
    subdomain: string;
    plan_name: string;
    plan_key: string;
    max_domains: number;
    used_domains: number;
    can_add: boolean;
    unlimited: boolean;
  }
  let customers = $state<CustomerOption[]>([]);
  let selectedCustomerId = $state<number | null>(null);
  let loadingCustomers = $state(false);

  // Plans (for quota editing)
  let plans = $state<Plan[]>([]);
  let editingQuotaCustomerId = $state<number | null>(null);
  let editingMaxDomains = $state<number>(0);
  let savingQuota = $state(false);

  // Selected customer quota
  let selectedCustomer = $derived(customers.find(c => c.id === selectedCustomerId) ?? null);

  // Filter
  let filterCustomerId = $state<number | null>(null);
  let filterStatus = $state<string>('');

  // Form fields
  let formExternalDomain = $state('');
  let formLoading = $state(false);

  // Action loading per domain
  let actionLoading = $state<Record<number, string>>({});

  const unsubscribe = domainsStore.subscribe((state: any) => {
    domains = state.items ?? [];
    loading = state.loading ?? false;
  });

  onMount(() => {
    loadCustomers();
    loadPlans();
    domainsStore.load();
    return unsubscribe;
  });

  async function loadPlans() {
    try {
      plans = await plansApi.list();
    } catch (e) {
      console.error('Error loading plans:', e);
    }
  }

  function startEditQuota(c: CustomerOption) {
    editingQuotaCustomerId = c.id;
    // plan_key coincide con Plan.name; usar max_domains actual del customer
    editingMaxDomains = c.max_domains;
  }

  function cancelEditQuota() {
    editingQuotaCustomerId = null;
    editingMaxDomains = 0;
  }

  async function saveQuota(c: CustomerOption) {
    // Buscar el plan por plan_key
    const plan = plans.find(p => p.name === c.plan_key);
    if (!plan) {
      toasts.error(`No se encontró el plan "${c.plan_key}"`);
      return;
    }
    savingQuota = true;
    try {
      await plansApi.setMaxDomains(plan.id, editingMaxDomains);
      toasts.success(`Cuota actualizada para plan ${plan.name}: ${editingMaxDomains === -1 ? '∞ (ilimitado)' : editingMaxDomains} dominio(s)`);
      editingQuotaCustomerId = null;
      // Refresh para reflejar el cambio
      await Promise.all([loadCustomers(), loadPlans()]);
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al guardar cuota');
    } finally {
      savingQuota = false;
    }
  }

  async function loadCustomers() {
    loadingCustomers = true;
    try {
      const res = await api.get<{ items: CustomerOption[]; total: number }>('/api/domains/customers-with-plans');
      customers = res.items ?? [];
    } catch (e: any) {
      console.error('Error loading customers:', e);
    } finally {
      loadingCustomers = false;
    }
  }

  async function handleCreate(e: Event) {
    e.preventDefault();
    if (!selectedCustomerId) {
      toasts.error('Seleccione un cliente');
      return;
    }
    if (!formExternalDomain.trim()) {
      toasts.error('Ingrese el dominio externo');
      return;
    }
    formLoading = true;
    createInstructions = null;
    try {
      const result = await domainsStore.create({
        external_domain: formExternalDomain.trim().toLowerCase(),
        customer_id: selectedCustomerId,
      });
      toasts.success('Dominio registrado exitosamente');
      if (result?.instructions) {
        createInstructions = result.instructions;
      }
      formExternalDomain = '';
      // Refresh customer quotas
      loadCustomers();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al registrar dominio');
    } finally {
      formLoading = false;
    }
  }

  async function handleConfigureCF(id: number) {
    actionLoading = { ...actionLoading, [id]: 'cf' };
    try {
      await domainsStore.configureCloudflare(id);
      await domainsStore.load(filterCustomerId ? { customer_id: filterCustomerId } : undefined);
      toasts.success('Cloudflare configurado');
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error configurando Cloudflare');
    } finally {
      const { [id]: _, ...rest } = actionLoading;
      actionLoading = rest;
    }
  }

  async function handleVerify(id: number) {
    actionLoading = { ...actionLoading, [id]: 'verify' };
    try {
      const result = await domainsStore.verify(id);
      if (result?.success) {
        toasts.success('DNS verificado correctamente');
      } else {
        toasts.warning(result?.message ?? 'DNS aún no propagado');
      }
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al verificar');
    } finally {
      const { [id]: _, ...rest } = actionLoading;
      actionLoading = rest;
    }
  }

  async function handleActivate(id: number) {
    actionLoading = { ...actionLoading, [id]: 'activate' };
    try {
      await domainsStore.activate(id);
      toasts.success('Dominio activado');
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al activar');
    } finally {
      const { [id]: _, ...rest } = actionLoading;
      actionLoading = rest;
    }
  }

  async function handleDeactivate(id: number) {
    actionLoading = { ...actionLoading, [id]: 'deactivate' };
    try {
      await domainsStore.deactivate(id);
      toasts.success('Dominio desactivado');
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al desactivar');
    } finally {
      const { [id]: _, ...rest } = actionLoading;
      actionLoading = rest;
    }
  }

  async function handleConfigureNginx(id: number) {
    actionLoading = { ...actionLoading, [id]: 'nginx' };
    try {
      const res = await api.post<{ success: boolean; message?: string }>(`/api/domains/${id}/configure-nginx`);
      if (res.success) {
        toasts.success('Nginx configurado en PCT160 + CT105');
        await domainsStore.load(filterCustomerId ? { customer_id: filterCustomerId } : undefined);
      } else {
        toasts.error('Error configurando nginx');
      }
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error configurando nginx');
    } finally {
      const { [id]: _, ...rest } = actionLoading;
      actionLoading = rest;
    }
  }

  async function handleDelete(domain: Domain) {
    if (!window.confirm(`¿Eliminar el dominio "${domain.external_domain}"?\nEsto eliminará la configuración de Cloudflare y Nginx asociada.`)) return;
    try {
      await domainsStore.delete(domain.id as number);
      toasts.success('Dominio eliminado');
      loadCustomers();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al eliminar dominio');
    }
  }

  async function handleFilter() {
    const params: any = {};
    if (filterCustomerId) params.customer_id = filterCustomerId;
    if (filterStatus) params.status = filterStatus;
    await domainsStore.load(params);
  }

  function getDomainStep(d: Domain): number {
    if (d.is_active && (d as any).nginx_configured) return 5;
    if (d.is_active) return 4;
    if (d.verification_status === 'verified') return 3;
    if (d.cloudflare_configured) return 2;
    return 1;
  }

  function getStepLabel(step: number): string {
    const labels: Record<number, string> = {
      1: 'Registrado',
      2: 'CF Configurado',
      3: 'DNS Verificado',
      4: 'Activo',
      5: 'Operativo',
    };
    return labels[step] ?? 'Desconocido';
  }

  function getCustomerForDomain(d: Domain): CustomerOption | undefined {
    return customers.find(c => c.id === d.customer_id);
  }
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between flex-wrap gap-3">
    <div>
      <h1 class="page-title">DOMINIOS EXTERNOS</h1>
      <p class="page-subtitle">Vincular dominios personalizados a tenants según plan</p>
    </div>
    <button class="btn-accent px-4 py-2 flex items-center gap-2" onclick={() => { showForm = !showForm; if (!showForm) createInstructions = null; }}>
      <Plus size={14} />
      NUEVO DOMINIO
    </button>
  </div>

  <!-- Stats -->
  <div class="grid grid-cols-2 sm:grid-cols-5 gap-3">
    <div class="stat-card card">
      <div class="stat-value">{$domainStats.total}</div>
      <div class="stat-label">Total</div>
    </div>
    <div class="stat-card card">
      <div class="stat-value text-emerald-500">{$domainStats.active}</div>
      <div class="stat-label">Activos</div>
    </div>
    <div class="stat-card card">
      <div class="stat-value text-emerald-600">{$domainStats.verified}</div>
      <div class="stat-label">Verificados</div>
    </div>
    <div class="stat-card card">
      <div class="stat-value text-amber-500">{$domainStats.pending}</div>
      <div class="stat-label">Pendientes</div>
    </div>
    <div class="stat-card card">
      <div class="stat-value text-red-500">{$domainStats.failed}</div>
      <div class="stat-label">Fallidos</div>
    </div>
  </div>

  <!-- Create Form -->
  {#if showForm}
    <div class="card border-l-2 border-l-terracotta">
      <h3 class="section-heading mb-5 flex items-center gap-2">
        <Globe size={16} />
        VINCULAR DOMINIO EXTERNO
      </h3>

      <form onsubmit={handleCreate} class="space-y-4">
        <!-- Customer Selector -->
        <div>
          <label class="label" for="f-customer">Cliente <span class="text-red-400">*</span></label>
          <select
            id="f-customer"
            class="input w-full px-3 py-2"
            bind:value={selectedCustomerId}
            required
          >
            <option value={null}>— Seleccione un cliente —</option>
            {#each customers as c (c.id)}
              <option value={c.id} disabled={!c.can_add}>
                {c.company_name} ({c.subdomain}) — {c.plan_name}
                {#if c.unlimited}
                  [∞ dominios]
                {:else if c.max_domains === 0}
                  [sin dominios custom]
                {:else}
                  [{c.used_domains}/{c.max_domains} usados]
                {/if}
                {#if !c.can_add}
                  ⛔ LÍMITE
                {/if}
              </option>
            {/each}
          </select>
        </div>

        <!-- Quota Badge -->
        {#if selectedCustomer}
          <div class="flex items-center gap-3 p-3 rounded-md {selectedCustomer.can_add ? 'bg-emerald-50 border border-emerald-200' : 'bg-red-50 border border-red-200'}">
            <Info size={16} class={selectedCustomer.can_add ? 'text-emerald-600' : 'text-red-600'} />
            <div class="text-sm">
              <span class="font-semibold">{selectedCustomer.company_name}</span>
              — Plan: <span class="font-mono text-xs px-1.5 py-0.5 bg-white rounded border">{selectedCustomer.plan_name}</span>
              {#if selectedCustomer.unlimited}
                — <span class="text-emerald-600 font-semibold">Dominios ilimitados</span>
              {:else if selectedCustomer.max_domains === 0}
                — <span class="text-red-600 font-semibold">Plan no permite dominios custom</span>
                <span class="text-xs text-gray-500 ml-1">(upgrade necesario)</span>
              {:else}
                — Dominios: <span class="font-mono font-semibold">{selectedCustomer.used_domains}/{selectedCustomer.max_domains}</span>
                {#if !selectedCustomer.can_add}
                  <span class="text-red-600 font-semibold ml-1">— LÍMITE ALCANZADO</span>
                {/if}
              {/if}
            </div>
          </div>
        {/if}

        <!-- Domain Input -->
        <div>
          <label class="label" for="f-external">Dominio externo <span class="text-red-400">*</span></label>
          <div class="flex items-stretch">
            <span class="bg-bg-card border border-border-light border-r-0 px-3 py-2 text-sm text-gray-400 whitespace-nowrap flex items-center">
              <Globe size={14} class="mr-1.5" /> https://
            </span>
            <input
              id="f-external"
              class="input flex-1 px-3 py-2 font-mono"
              type="text"
              bind:value={formExternalDomain}
              placeholder="midominio.com"
              required
              disabled={!selectedCustomer?.can_add}
            />
          </div>
          <p class="text-xs text-gray-500 mt-1">
            El dominio del cliente que se vinculará a <code class="font-mono bg-gray-100 px-1 rounded">{selectedCustomer?.subdomain ?? '???'}.sajet.us</code>
          </p>
        </div>

        <!-- Info box -->
        <div class="bg-blue-50 border border-blue-200 p-3 rounded-md text-xs text-blue-800 space-y-1">
          <p class="font-semibold">Flujo automático al crear:</p>
          <ol class="list-decimal list-inside space-y-0.5 ml-2">
            <li>Se registra el dominio y genera subdominio <code>.sajet.us</code></li>
            <li>Se crea CNAME en Cloudflare (zona sajet.us)</li>
            <li>El cliente configura CNAME en su DNS externo</li>
            <li>Se verifica propagación DNS</li>
            <li>Se configura nginx (PCT160 + CT105) y se activa</li>
          </ol>
        </div>

        <div class="flex gap-3 pt-2">
          <button type="button" class="btn-secondary px-4 py-2" onclick={() => { showForm = false; createInstructions = null; }}>CANCELAR</button>
          <button
            type="submit"
            class="btn-accent px-4 py-2 disabled:opacity-60 flex items-center gap-2"
            disabled={formLoading || !selectedCustomer?.can_add}
          >
            {#if formLoading}
              <RefreshCw size={14} class="animate-spin" /> REGISTRANDO...
            {:else}
              <Plus size={14} /> REGISTRAR DOMINIO
            {/if}
          </button>
        </div>
      </form>

      <!-- CNAME Instructions after creation -->
      {#if createInstructions}
        <div class="mt-4 bg-emerald-50 border border-emerald-200 p-4 rounded-md">
          <p class="text-xs uppercase tracking-widest font-semibold text-emerald-700 mb-3 flex items-center gap-2">
            <ShieldCheck size={14} /> Instrucciones para el cliente
          </p>
          <div class="bg-white border border-emerald-100 p-3 rounded font-mono text-xs text-emerald-900 space-y-1">
            <p>{createInstructions.step1 ?? createInstructions.step_1 ?? ''}</p>
            {#if createInstructions.record_type}
              <p class="mt-2">
                <span class="font-semibold">Tipo:</span> {createInstructions.record_type}
                <span class="mx-2">|</span>
                <span class="font-semibold">Nombre:</span> {createInstructions.record_name}
                <span class="mx-2">|</span>
                <span class="font-semibold">Valor:</span> {createInstructions.record_value}
              </p>
            {/if}
            <p class="mt-1">{createInstructions.step2 ?? createInstructions.step_2 ?? ''}</p>
          </div>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Filters -->
  <div class="card">
    <div class="flex flex-wrap items-end gap-4">
      <div class="flex-1 min-w-[200px]">
        <label class="label" for="filter-customer">Filtrar por cliente</label>
        <select id="filter-customer" class="input w-full px-3 py-2" bind:value={filterCustomerId} onchange={handleFilter}>
          <option value={null}>Todos los clientes</option>
          {#each customers as c (c.id)}
            <option value={c.id}>{c.company_name} ({c.subdomain})</option>
          {/each}
        </select>
      </div>
      <div class="min-w-[160px]">
        <label class="label" for="filter-status">Estado</label>
        <select id="filter-status" class="input w-full px-3 py-2" bind:value={filterStatus} onchange={handleFilter}>
          <option value="">Todos</option>
          <option value="pending">Pendiente</option>
          <option value="verifying">Verificando</option>
          <option value="verified">Verificado</option>
          <option value="failed">Fallido</option>
        </select>
      </div>
      <button class="btn-secondary px-3 py-2 flex items-center gap-1" onclick={() => { filterCustomerId = null; filterStatus = ''; domainsStore.load(); }}>
        <X size={14} /> Limpiar
      </button>
    </div>
  </div>

  <!-- Domains Table -->
  <div class="card p-0 overflow-hidden">
    {#if loading}
      <div class="p-8 text-center text-gray-500 text-sm flex items-center justify-center gap-2">
        <RefreshCw size={16} class="animate-spin" /> Cargando dominios...
      </div>
    {:else if domains.length === 0}
      <div class="p-12 text-center">
        <Globe size={48} class="mx-auto text-gray-300 mb-3" />
        <p class="text-gray-500 text-sm">No hay dominios registrados</p>
        <p class="text-gray-400 text-xs mt-1">Haga clic en "NUEVO DOMINIO" para vincular un dominio externo</p>
      </div>
    {:else}
      <div class="overflow-x-auto">
        <table class="table w-full">
          <thead>
            <tr>
              <th>CLIENTE</th>
              <th>DOMINIO EXTERNO</th>
              <th>SUBDOMINIO SAJET</th>
              <th>PROGRESO</th>
              <th>ESTADO</th>
              <th>CREADO</th>
              <th>ACCIONES</th>
            </tr>
          </thead>
          <tbody>
            {#each domains as domain (domain.id)}
              {@const step = getDomainStep(domain)}
              {@const customer = getCustomerForDomain(domain)}
              <tr class={!domain.is_active ? 'opacity-60' : ''}>
                <!-- Cliente -->
                <td>
                  <div class="text-sm font-medium">{customer?.company_name ?? `#${domain.customer_id}`}</div>
                  {#if customer}
                    <div class="text-xs text-gray-400 font-mono">
                      {customer.plan_name}
                      {#if customer.unlimited}
                        · ∞
                      {:else if customer.max_domains > 0}
                        · {customer.used_domains}/{customer.max_domains}
                      {/if}
                    </div>
                  {/if}
                </td>

                <!-- Dominio externo -->
                <td>
                  <div class="flex items-center gap-1.5">
                    <Globe size={14} class={domain.is_active ? 'text-emerald-500' : 'text-gray-400'} />
                    <span class="font-mono text-sm">{domain.external_domain}</span>
                  </div>
                  {#if domain.is_active}
                    <a href="https://{domain.external_domain}" target="_blank" rel="noopener" class="text-xs text-blue-500 hover:underline flex items-center gap-0.5 mt-0.5">
                      <ExternalLink size={10} /> Abrir
                    </a>
                  {/if}
                </td>

                <!-- Subdominio sajet -->
                <td>
                  <span class="text-sm text-gray-600 font-mono">{domain.sajet_full_domain ?? domain.sajet_subdomain + '.sajet.us'}</span>
                </td>

                <!-- Progress Steps -->
                <td>
                  <div class="flex items-center gap-0.5">
                    {#each [1, 2, 3, 4, 5] as s}
                      <div
                        class="w-5 h-1.5 rounded-full {s <= step ? 'bg-emerald-500' : 'bg-gray-200'}"
                        title={getStepLabel(s)}
                      ></div>
                    {/each}
                    <span class="text-xs text-gray-500 ml-1.5">{getStepLabel(step)}</span>
                  </div>
                </td>

                <!-- Estado -->
                <td>
                  <div class="flex flex-col gap-1">
                    {#if domain.verification_status === 'verified'}
                      <span class="badge-success text-[10px]">Verificado</span>
                    {:else if domain.verification_status === 'pending'}
                      <span class="badge-warning text-[10px]">DNS Pendiente</span>
                    {:else if domain.verification_status === 'verifying'}
                      <span class="badge-warning text-[10px]">Verificando</span>
                    {:else}
                      <span class="badge-error text-[10px]">{domain.verification_status}</span>
                    {/if}
                    <div class="flex items-center gap-2 text-[10px]">
                      <span class="flex items-center gap-0.5" title="Cloudflare">
                        {#if domain.cloudflare_configured}
                          <Shield size={10} class="text-emerald-500" /> CF
                        {:else}
                          <Shield size={10} class="text-gray-300" /> CF
                        {/if}
                      </span>
                      <span class="flex items-center gap-0.5" title="Nginx">
                        {#if (domain as any).nginx_configured}
                          <Server size={10} class="text-emerald-500" /> NGX
                        {:else}
                          <Server size={10} class="text-gray-300" /> NGX
                        {/if}
                      </span>
                      <span class="flex items-center gap-0.5" title="Activo">
                        {#if domain.is_active}
                          <Zap size={10} class="text-emerald-500" /> ON
                        {:else}
                          <Zap size={10} class="text-gray-300" /> OFF
                        {/if}
                      </span>
                    </div>
                  </div>
                </td>

                <!-- Creado -->
                <td class="text-xs text-gray-500">{formatDate(domain.created_at)}</td>

                <!-- Acciones -->
                <td>
                  <div class="flex items-center gap-1 flex-wrap">
                    {#if !domain.cloudflare_configured}
                      <button
                        class="btn-secondary btn-sm text-[10px] flex items-center gap-1"
                        onclick={() => handleConfigureCF(domain.id as number)}
                        disabled={!!actionLoading[domain.id as number]}
                      >
                        {#if actionLoading[domain.id as number] === 'cf'}
                          <RefreshCw size={10} class="animate-spin" />
                        {:else}
                          <Shield size={10} />
                        {/if}
                        CF
                      </button>
                    {/if}

                    {#if domain.cloudflare_configured && domain.verification_status !== 'verified'}
                      <button
                        class="btn-secondary btn-sm text-[10px] flex items-center gap-1"
                        onclick={() => handleVerify(domain.id as number)}
                        disabled={!!actionLoading[domain.id as number]}
                      >
                        {#if actionLoading[domain.id as number] === 'verify'}
                          <RefreshCw size={10} class="animate-spin" />
                        {:else}
                          <Check size={10} />
                        {/if}
                        VERIFICAR
                      </button>
                    {/if}

                    {#if domain.verification_status === 'verified' && !domain.is_active}
                      <button
                        class="btn-sm text-[10px] flex items-center gap-1 bg-emerald-600 text-white hover:bg-emerald-700"
                        onclick={() => handleActivate(domain.id as number)}
                        disabled={!!actionLoading[domain.id as number]}
                      >
                        {#if actionLoading[domain.id as number] === 'activate'}
                          <RefreshCw size={10} class="animate-spin" />
                        {:else}
                          <Zap size={10} />
                        {/if}
                        ACTIVAR
                      </button>
                    {/if}

                    {#if domain.is_active && !(domain as any).nginx_configured}
                      <button
                        class="btn-secondary btn-sm text-[10px] flex items-center gap-1"
                        onclick={() => handleConfigureNginx(domain.id as number)}
                        disabled={!!actionLoading[domain.id as number]}
                      >
                        {#if actionLoading[domain.id as number] === 'nginx'}
                          <RefreshCw size={10} class="animate-spin" />
                        {:else}
                          <Server size={10} />
                        {/if}
                        NGINX
                      </button>
                    {/if}

                    {#if domain.is_active}
                      <button
                        class="btn-sm text-[10px] flex items-center gap-1 bg-amber-100 text-amber-800 hover:bg-amber-200"
                        onclick={() => handleDeactivate(domain.id as number)}
                        disabled={!!actionLoading[domain.id as number]}
                      >
                        <X size={10} /> OFF
                      </button>
                    {/if}

                    <button
                      class="btn-danger btn-sm text-[10px] flex items-center gap-1"
                      onclick={() => handleDelete(domain)}
                    >
                      <Trash2 size={10} />
                    </button>
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>

  <!-- Plan Quota Legend -->
  {#if customers.length > 0}
    <div class="card">
      <h3 class="section-heading mb-3 flex items-center gap-2">
        <Info size={14} />
        CUOTA DE DOMINIOS POR PLAN
        <span class="ml-auto text-[10px] text-gray-400 font-normal normal-case">-1 = ilimitado · 0 = sin dominios</span>
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {#each customers as c (c.id)}
          <div class="flex items-center justify-between p-3 border border-border-light rounded-md {!c.can_add && c.max_domains !== 0 ? 'border-red-200 bg-red-50/50' : ''}">
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium truncate">{c.company_name}</div>
              <div class="text-xs text-gray-500 font-mono">{c.plan_name}</div>
            </div>

            {#if editingQuotaCustomerId === c.id}
              <!-- Inline editor -->
              <div class="flex items-center gap-1 ml-2">
                <input
                  type="number"
                  min="-1"
                  class="w-16 border border-border-light rounded px-1.5 py-0.5 text-xs font-mono text-center focus:outline-none focus:ring-1 focus:ring-primary"
                  bind:value={editingMaxDomains}
                  onkeydown={(e) => { if (e.key === 'Enter') saveQuota(c); if (e.key === 'Escape') cancelEditQuota(); }}
                />
                <button
                  class="p-1 rounded text-emerald-600 hover:bg-emerald-50 disabled:opacity-50"
                  onclick={() => saveQuota(c)}
                  disabled={savingQuota}
                  title="Guardar"
                >
                  <Check size={13} />
                </button>
                <button
                  class="p-1 rounded text-gray-400 hover:bg-gray-100"
                  onclick={cancelEditQuota}
                  title="Cancelar"
                >
                  <X size={13} />
                </button>
              </div>
            {:else}
              <!-- Read-only display + edit button -->
              <div class="flex items-center gap-2 ml-2">
                <div class="text-right">
                  {#if c.unlimited}
                    <span class="text-emerald-600 text-sm font-semibold">∞</span>
                    <div class="text-[10px] text-gray-400">{c.used_domains} usado(s)</div>
                  {:else if c.max_domains === 0}
                    <span class="text-gray-400 text-xs">No disponible</span>
                  {:else}
                    <div class="text-sm font-mono font-semibold {c.can_add ? 'text-emerald-600' : 'text-red-600'}">{c.used_domains}/{c.max_domains}</div>
                    {#if !c.can_add}
                      <div class="text-[10px] text-red-500 flex items-center gap-0.5">
                        <AlertTriangle size={8} /> Límite
                      </div>
                    {/if}
                  {/if}
                </div>
                <button
                  class="p-1 rounded text-gray-400 hover:text-primary hover:bg-gray-100 transition-colors"
                  onclick={() => startEditQuota(c)}
                  title="Editar cuota del plan"
                >
                  <Pencil size={12} />
                </button>
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>
