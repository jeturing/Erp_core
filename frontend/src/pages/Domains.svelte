<script lang="ts">
  import { onMount } from 'svelte';
  import { Modal } from '../lib/components';
  import { domainsStore, domainStats } from '../lib/stores';
  import { toasts } from '../lib/stores/toast';
  import { formatDate } from '../lib/utils/formatters';
  import type { Domain } from '../lib/types';
  import { Plus, Check, X, RefreshCw, Trash2, Globe, ShieldCheck, ShieldOff } from 'lucide-svelte';

  // Store subscriptions
  let storeState = { items: [] as Domain[], total: 0, loading: false, error: null as string | null };
  let stats = { total: 0, active: 0, pending: 0, verified: 0, failed: 0 };

  domainsStore.subscribe((s) => { storeState = s; });
  domainStats.subscribe((s) => { stats = s; });

  // Create modal
  let showCreateModal = false;
  let creating = false;
  let createError = '';
  let cnameInstructions: null | { step1: string; record_type: string; record_name: string; record_value: string; step2: string } = null;
  let createForm = {
    external_domain: '',
    sajet_subdomain: '',
    target_node_ip: '',
    target_port: '',
    customer_id: '',
  };

  // Delete modal
  let showDeleteModal = false;
  let deleteDomain: Domain | null = null;
  let deleteLoading = false;

  // Action loading per domain
  let actionLoading: Record<number, boolean> = {};

  onMount(async () => {
    try {
      await domainsStore.load();
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error cargando dominios');
    }
  });

  async function handleRefresh() {
    try {
      await domainsStore.load();
      toasts.success('Dominios actualizados');
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error actualizando dominios');
    }
  }

  function resetCreateForm() {
    createForm = { external_domain: '', sajet_subdomain: '', target_node_ip: '', target_port: '', customer_id: '' };
    createError = '';
    cnameInstructions = null;
  }

  async function handleCreate() {
    createError = '';
    if (!createForm.external_domain.trim()) { createError = 'El dominio externo es obligatorio'; return; }
    if (!createForm.customer_id.trim()) { createError = 'El Customer ID es obligatorio'; return; }
    creating = true;
    try {
      const res = await domainsStore.create({
        external_domain: createForm.external_domain.trim(),
        customer_id: parseInt(createForm.customer_id),
        tenant_deployment_id: undefined,
      });
      if (res.instructions) {
        cnameInstructions = res.instructions;
      } else {
        showCreateModal = false;
        resetCreateForm();
        toasts.success('Dominio creado exitosamente');
      }
    } catch (err) {
      createError = err instanceof Error ? err.message : 'Error creando dominio';
    } finally {
      creating = false;
    }
  }

  function closeCnameModal() {
    cnameInstructions = null;
    showCreateModal = false;
    resetCreateForm();
  }

  async function handleVerify(domain: Domain) {
    actionLoading = { ...actionLoading, [domain.id]: true };
    try {
      const res = await domainsStore.verify(domain.id);
      if (res.success) {
        toasts.success(`Dominio verificado: ${domain.external_domain}`);
      } else {
        toasts.warning(res.message || 'Verificación pendiente');
      }
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error verificando dominio');
    } finally {
      actionLoading = { ...actionLoading, [domain.id]: false };
    }
  }

  async function handleToggleActive(domain: Domain) {
    actionLoading = { ...actionLoading, [domain.id]: true };
    try {
      if (domain.is_active) {
        await domainsStore.deactivate(domain.id);
        toasts.success('Dominio desactivado');
      } else {
        await domainsStore.activate(domain.id);
        toasts.success('Dominio activado');
      }
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error cambiando estado');
    } finally {
      actionLoading = { ...actionLoading, [domain.id]: false };
    }
  }

  function openDeleteModal(domain: Domain) {
    deleteDomain = domain;
    showDeleteModal = true;
  }

  async function handleDelete() {
    if (!deleteDomain) return;
    deleteLoading = true;
    try {
      await domainsStore.delete(deleteDomain.id);
      showDeleteModal = false;
      toasts.success(`Dominio ${deleteDomain.external_domain} eliminado`);
      deleteDomain = null;
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error eliminando dominio');
    } finally {
      deleteLoading = false;
    }
  }

  function statusBadge(status: string) {
    if (status === 'verified') return 'badge-success';
    if (status === 'pending' || status === 'verifying') return 'badge-warning';
    if (status === 'failed' || status === 'expired') return 'badge-error';
    return 'badge-neutral';
  }
</script>

<div class="p-6 lg:p-8 space-y-6">
  <!-- Page Header -->
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
      <h1 class="page-title">DOMAINS</h1>
      <p class="page-subtitle mt-1">Gestión de dominios personalizados y configuración CNAME</p>
    </div>
    <div class="flex gap-2">
      <button class="btn btn-secondary btn-sm" on:click={handleRefresh} disabled={storeState.loading}>
        <RefreshCw size={13} class={storeState.loading ? 'animate-spin' : ''} />
        Actualizar
      </button>
      <button class="btn btn-accent" on:click={() => { resetCreateForm(); showCreateModal = true; }}>
        <Plus size={14} />
        NUEVO DOMINIO
      </button>
    </div>
  </div>

  <!-- Stat Cards -->
  <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
    <div class="stat-card">
      <span class="stat-label">Total Dominios</span>
      <span class="stat-value">{stats.total}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Verificados</span>
      <span class="stat-value text-success">{stats.verified}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Pendientes</span>
      <span class="stat-value text-warning">{stats.pending}</span>
    </div>
  </div>

  <!-- Table -->
  <div class="card p-0 overflow-hidden">
    <div class="flex items-center justify-between px-6 py-4 border-b border-border-light">
      <span class="section-heading">Dominios Registrados</span>
      {#if storeState.error}
        <span class="text-[11px] text-error">{storeState.error}</span>
      {/if}
    </div>

    {#if storeState.loading}
      <div class="py-16 flex justify-center">
        <div class="w-8 h-8 border-2 border-charcoal border-t-transparent rounded-full animate-spin"></div>
      </div>
    {:else}
      <div class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr>
              <th>Dominio Externo</th>
              <th>Subdominio Sajet</th>
              <th>Estado</th>
              <th>Cloudflare</th>
              <th>Activo</th>
              <th>Creado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {#each storeState.items as domain (domain.id)}
              <tr>
                <td>
                  <div class="flex items-center gap-1.5">
                    <Globe size={13} class="text-gray-400 shrink-0" />
                    <span class="font-medium text-text-primary">{domain.external_domain}</span>
                  </div>
                </td>
                <td class="text-text-secondary text-sm font-mono">{domain.sajet_subdomain}</td>
                <td>
                  <span class="badge {statusBadge(domain.verification_status)}">{domain.verification_status}</span>
                </td>
                <td>
                  {#if domain.cloudflare_configured}
                    <span class="flex items-center gap-1 text-success text-[11px]"><Check size={13} /> Configurado</span>
                  {:else}
                    <span class="flex items-center gap-1 text-gray-400 text-[11px]"><X size={13} /> No config.</span>
                  {/if}
                </td>
                <td>
                  {#if domain.is_active}
                    <span class="badge badge-success">Activo</span>
                  {:else}
                    <span class="badge badge-neutral">Inactivo</span>
                  {/if}
                </td>
                <td class="text-text-secondary text-sm">{formatDate(domain.created_at)}</td>
                <td>
                  <div class="flex flex-wrap gap-1.5">
                    <button
                      class="btn btn-secondary btn-sm"
                      on:click={() => handleVerify(domain)}
                      disabled={actionLoading[domain.id]}
                      title="Verificar dominio"
                    >
                      <RefreshCw size={12} class={actionLoading[domain.id] ? 'animate-spin' : ''} />
                      Verificar
                    </button>
                    <button
                      class="btn btn-sm {domain.is_active ? 'btn-secondary' : 'btn-primary'}"
                      on:click={() => handleToggleActive(domain)}
                      disabled={actionLoading[domain.id]}
                    >
                      {#if domain.is_active}
                        <ShieldOff size={12} /> Desactivar
                      {:else}
                        <ShieldCheck size={12} /> Activar
                      {/if}
                    </button>
                    <button
                      class="btn btn-danger btn-sm"
                      on:click={() => openDeleteModal(domain)}
                      disabled={actionLoading[domain.id]}
                      title="Eliminar dominio"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </td>
              </tr>
            {:else}
              <tr>
                <td colspan="7" class="text-center text-gray-500 py-12 text-sm">
                  No hay dominios registrados
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</div>

<!-- Modal: Nuevo Dominio -->
<Modal
  bind:isOpen={showCreateModal}
  title="Nuevo Dominio"
  confirmText={cnameInstructions ? 'CERRAR' : 'CREAR DOMINIO'}
  on:confirm={cnameInstructions ? closeCnameModal : handleCreate}
  on:close={() => { showCreateModal = false; resetCreateForm(); }}
  loading={creating}
  showFooter={true}
  size="md"
>
  {#if cnameInstructions}
    <!-- CNAME Instructions -->
    <div class="space-y-4">
      <div class="p-4 rounded bg-success/5 border border-success/20">
        <p class="text-sm font-semibold text-success mb-3">Dominio creado. Configura el registro CNAME:</p>
        <div class="space-y-2 text-sm">
          <p class="text-text-secondary">{cnameInstructions.step1}</p>
          <div class="p-3 rounded bg-bg-card border border-border-light font-mono text-[11px] space-y-1">
            <div class="flex gap-2">
              <span class="text-gray-500 w-20 shrink-0">Tipo:</span>
              <span class="text-text-primary">{cnameInstructions.record_type}</span>
            </div>
            <div class="flex gap-2">
              <span class="text-gray-500 w-20 shrink-0">Nombre:</span>
              <span class="text-text-primary break-all">{cnameInstructions.record_name}</span>
            </div>
            <div class="flex gap-2">
              <span class="text-gray-500 w-20 shrink-0">Valor:</span>
              <span class="text-text-primary break-all">{cnameInstructions.record_value}</span>
            </div>
          </div>
          <p class="text-text-secondary">{cnameInstructions.step2}</p>
        </div>
      </div>
    </div>
  {:else}
    <div class="space-y-4">
      {#if createError}
        <div class="p-3 rounded bg-error/10 border border-error/20 text-sm text-error">{createError}</div>
      {/if}

      <div>
        <label class="label block mb-1" for="ext-domain">Dominio Externo <span class="text-error">*</span></label>
        <input id="ext-domain" class="input w-full" placeholder="miempresa.com" bind:value={createForm.external_domain} />
      </div>

      <div>
        <label class="label block mb-1" for="cid">Customer ID <span class="text-error">*</span></label>
        <input id="cid" type="number" class="input w-full" placeholder="1" bind:value={createForm.customer_id} />
      </div>

      <div>
        <label class="label block mb-1" for="sajet-sub">Subdominio Sajet (opcional)</label>
        <input id="sajet-sub" class="input w-full" placeholder="cliente.sajet.us" bind:value={createForm.sajet_subdomain} />
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="label block mb-1" for="node-ip">IP Nodo Destino</label>
          <input id="node-ip" class="input w-full" placeholder="10.0.0.1" bind:value={createForm.target_node_ip} />
        </div>
        <div>
          <label class="label block mb-1" for="port">Puerto</label>
          <input id="port" type="number" class="input w-full" placeholder="8069" bind:value={createForm.target_port} />
        </div>
      </div>
    </div>
  {/if}
</Modal>

<!-- Modal: Confirmar Eliminación -->
<Modal
  bind:isOpen={showDeleteModal}
  title="Eliminar Dominio"
  confirmText="ELIMINAR"
  confirmVariant="danger"
  on:confirm={handleDelete}
  on:close={() => { showDeleteModal = false; deleteDomain = null; }}
  loading={deleteLoading}
  size="sm"
>
  <div class="space-y-3">
    <p class="text-sm text-text-secondary">
      Esta acción es <strong class="text-error">irreversible</strong>. Se eliminará el dominio:
    </p>
    {#if deleteDomain}
      <div class="p-3 rounded bg-error/5 border border-error/20">
        <p class="font-semibold text-text-primary">{deleteDomain.external_domain}</p>
        <p class="text-[11px] text-gray-500">ID: {deleteDomain.id}</p>
      </div>
    {/if}
  </div>
</Modal>
