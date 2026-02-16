<script lang="ts">
  import { onMount } from 'svelte';
  import { domainsStore, domainStats } from '../lib/stores';
  import { toasts } from '../lib/stores/toast';
  import { formatDate } from '../lib/utils/formatters';
  import { Plus, Check, X, CheckCircle, XCircle } from 'lucide-svelte';
  import type { Domain } from '../lib/types';


  let domains = $state<Domain[]>([]);
  let showForm = $state(false);
  let loading = $state(true);
  let createInstructions = $state<{ step1?: string; record_type?: string; record_name?: string; record_value?: string; step2?: string } | null>(null);

  // Form fields
  let formExternalDomain = $state('');
  let formSubdomain = $state('');
  let formNodeIp = $state('');
  let formPort = $state(8069);
  let formLoading = $state(false);

  const unsubscribe = domainsStore.subscribe((state: any) => {
    domains = state.items ?? [];
    loading = state.loading ?? false;
  });

  onMount(() => {
    domainsStore.load();
    return unsubscribe;
  });

  async function handleCreate(e: Event) {
    e.preventDefault();
    formLoading = true;
    createInstructions = null;
    try {
      const result = await domainsStore.create({
        external_domain: formExternalDomain,
        customer_id: 0,
      });
      toasts.success('Dominio agregado');
      if (result?.instructions) {
        createInstructions = result.instructions;
      }
      formExternalDomain = '';
      formSubdomain = '';
      formNodeIp = '';
      formPort = 8069;
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al agregar dominio');
    } finally {
      formLoading = false;
    }
  }

  async function handleVerify(id: number) {
    try {
      await domainsStore.verify(id);
      toasts.success('Verificación iniciada');
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al verificar');
    }
  }

  async function handleToggleActive(domain: Domain) {
    try {
      if (domain.is_active) {
        await domainsStore.deactivate(domain.id as number);
        toasts.success('Dominio desactivado');
      } else {
        await domainsStore.activate(domain.id as number);
        toasts.success('Dominio activado');
      }
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al cambiar estado');
    }
  }

  async function handleDelete(domain: Domain) {
    if (!window.confirm(`¿Eliminar el dominio "${domain.external_domain}"?`)) return;
    try {
      await domainsStore.delete(domain.id as number);
      toasts.success('Dominio eliminado');
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al eliminar dominio');
    }
  }
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="page-title">DOMAINS</h1>
      <p class="page-subtitle">Gestión de dominios externos y subdominios</p>
    </div>
    <button class="btn-accent px-4 py-2 flex items-center gap-2" onclick={() => showForm = !showForm}>
      <Plus size={14} />
      NUEVO DOMINIO
    </button>
  </div>

  <!-- Inline Add Form -->
  {#if showForm}
    <div class="card border-l-2 border-l-terracotta">
      <h3 class="section-heading mb-5">AGREGAR DOMINIO</h3>
      <form onsubmit={handleCreate} class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="label" for="f-external">Dominio externo</label>
            <input
              id="f-external"
              class="input w-full px-3 py-2"
              type="text"
              bind:value={formExternalDomain}
              placeholder="cliente.com"
              required
            />
          </div>
          <div>
            <label class="label" for="f-sub">Subdominio Sajet</label>
            <div class="flex items-stretch">
              <input
                id="f-sub"
                class="input flex-1 px-3 py-2 border-r-0"
                type="text"
                bind:value={formSubdomain}
                placeholder="cliente"
                required
              />
              <span class="bg-bg-card border border-border-light px-3 py-2 text-sm text-gray-500 whitespace-nowrap">.sajet.us</span>
            </div>
          </div>
          <div>
            <label class="label" for="f-ip">IP del nodo</label>
            <input
              id="f-ip"
              class="input w-full px-3 py-2"
              type="text"
              bind:value={formNodeIp}
              placeholder="192.168.1.100"
              required
            />
          </div>
          <div>
            <label class="label" for="f-port">Puerto</label>
            <input
              id="f-port"
              class="input w-full px-3 py-2"
              type="number"
              bind:value={formPort}
              min="1"
              max="65535"
              required
            />
          </div>
        </div>
        <div class="flex gap-3 pt-2">
          <button type="button" class="btn-secondary px-4 py-2" onclick={() => { showForm = false; createInstructions = null; }}>CANCELAR</button>
          <button type="submit" class="btn-accent px-4 py-2 disabled:opacity-60" disabled={formLoading}>
            {formLoading ? 'AGREGANDO...' : 'AGREGAR DOMINIO'}
          </button>
        </div>
      </form>

      {#if createInstructions}
        <div class="mt-4 bg-emerald-50 border border-emerald-200 p-4">
          <p class="text-xs uppercase tracking-[0.08em] font-semibold text-emerald-700 mb-2">Registro CNAME requerido</p>
          <pre class="font-mono text-xs text-emerald-800 bg-emerald-100 p-3 overflow-x-auto">{createInstructions ? `${createInstructions.step1 ?? ''}
Tipo: ${createInstructions.record_type ?? ''} | Nombre: ${createInstructions.record_name ?? ''} | Valor: ${createInstructions.record_value ?? ''}
${createInstructions.step2 ?? ''}` : ''}</pre>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Stats -->
  <div class="grid grid-cols-3 gap-4">
    <div class="stat-card card">
      <div class="stat-value">{$domainStats.total}</div>
      <div class="stat-label">Total</div>
    </div>
    <div class="stat-card card">
      <div class="stat-value">{$domainStats.verified}</div>
      <div class="stat-label">Verificados</div>
    </div>
    <div class="stat-card card">
      <div class="stat-value">{$domainStats.pending}</div>
      <div class="stat-label">Pendientes</div>
    </div>
  </div>

  <!-- Table -->
  <div class="card p-0 overflow-hidden">
    {#if loading}
      <div class="p-8 text-center text-gray-500 text-sm">Cargando dominios...</div>
    {:else if domains.length === 0}
      <div class="p-8 text-center text-gray-500 text-sm">No hay dominios registrados</div>
    {:else}
      <table class="table w-full">
        <thead>
          <tr>
            <th>DOMINIO EXTERNO</th>
            <th>SUBDOMINIO SAJET</th>
            <th>ESTADO</th>
            <th>CF</th>
            <th>ACTIVO</th>
            <th>CREADO</th>
            <th>ACCIONES</th>
          </tr>
        </thead>
        <tbody>
          {#each domains as domain (domain.id)}
            <tr>
              <td class="font-mono text-sm">{domain.external_domain}</td>
              <td class="text-sm text-gray-600">{domain.sajet_full_domain ?? domain.sajet_subdomain + '.sajet.us'}</td>
              <td>
                {#if domain.verification_status === 'verified'}
                  <span class="badge-success">Verificado</span>
                {:else if domain.verification_status === 'pending'}
                  <span class="badge-warning">Pendiente</span>
                {:else}
                  <span class="badge-error">{domain.verification_status}</span>
                {/if}
              </td>
              <td>
                {#if domain.cloudflare_configured}
                  <Check size={16} class="text-emerald-500" />
                {:else}
                  <X size={16} class="text-gray-400" />
                {/if}
              </td>
              <td>
                {#if domain.is_active}
                  <CheckCircle size={16} class="text-emerald-500" />
                {:else}
                  <XCircle size={16} class="text-gray-400" />
                {/if}
              </td>
              <td class="text-sm text-gray-500">{formatDate(domain.created_at)}</td>
              <td>
                <div class="flex items-center gap-2 flex-wrap">
                  <button class="btn-secondary btn-sm" onclick={() => handleVerify(domain.id as number)}>VERIFICAR</button>
                  <button class="btn-secondary btn-sm" onclick={() => handleToggleActive(domain)}>
                    {domain.is_active ? 'DESACTIVAR' : 'ACTIVAR'}
                  </button>
                  <button class="btn-danger btn-sm" onclick={() => handleDelete(domain)}>ELIMINAR</button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>
</div>
