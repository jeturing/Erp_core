<script lang="ts">
  import { onMount } from 'svelte';
  import { RefreshCw, Trash2, RotateCcw, AlertCircle, Globe, Wifi } from 'lucide-svelte';
  import { tunnelsApi } from '../lib/api/tunnels';
  import type { Tunnel } from '../lib/api/tunnels';
  import { Modal } from '../lib/components';
  import { toasts } from '../lib/stores/toast';
  import { formatDate } from '../lib/utils/formatters';

  let tunnels: Tunnel[] = [];
  let total = 0;
  let warning = '';
  let loading = false;
  let deleteModalOpen = false;
  let selectedTunnel: Tunnel | null = null;
  let deleteLoading = false;
  let restartingId: string | null = null;

  async function loadTunnels() {
    loading = true;
    warning = '';
    try {
      const resp = await tunnelsApi.list();
      tunnels = resp.tunnels || [];
      total = resp.total || 0;
      warning = resp.warning || '';
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error al cargar tunnels');
    } finally {
      loading = false;
    }
  }

  async function restartTunnel(tunnel: Tunnel) {
    restartingId = tunnel.id;
    try {
      await tunnelsApi.restart(tunnel.id);
      toasts.success(`Tunnel "${tunnel.name}" reiniciado correctamente`);
      await loadTunnels();
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : `Error al reiniciar tunnel ${tunnel.name}`);
    } finally {
      restartingId = null;
    }
  }

  function openDeleteModal(tunnel: Tunnel) {
    selectedTunnel = tunnel;
    deleteModalOpen = true;
  }

  async function confirmDelete() {
    if (!selectedTunnel) return;
    deleteLoading = true;
    try {
      await tunnelsApi.delete(selectedTunnel.id);
      toasts.success(`Tunnel "${selectedTunnel.name}" eliminado`);
      deleteModalOpen = false;
      selectedTunnel = null;
      await loadTunnels();
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error al eliminar tunnel');
    } finally {
      deleteLoading = false;
    }
  }

  function statusBadgeClass(status: string): string {
    if (status === 'healthy' || status === 'active' || status === 'running') return 'badge-success';
    if (status === 'degraded' || status === 'connecting') return 'badge-warning';
    if (status === 'inactive' || status === 'stopped') return 'badge-neutral';
    return 'badge-error';
  }

  function planBadgeClass(plan: string): string {
    if (plan === 'enterprise') return 'badge-info';
    if (plan === 'professional') return 'badge-success';
    if (plan === 'starter') return 'badge-neutral';
    return 'badge-neutral';
  }

  function truncateId(id: string): string {
    return id.length > 20 ? id.slice(0, 8) + '...' + id.slice(-8) : id;
  }

  onMount(loadTunnels);
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="page-title">CLOUDFLARE TUNNELS</h1>
      <p class="page-subtitle mt-1">Gestión de túneles Cloudflare para instancias</p>
    </div>
    <button class="btn btn-secondary btn-sm" on:click={loadTunnels} disabled={loading}>
      <RefreshCw class="w-3.5 h-3.5 mr-1.5 inline {loading ? 'animate-spin' : ''}" />
      ACTUALIZAR
    </button>
  </div>

  <!-- Warning banner -->
  {#if warning}
    <div class="flex items-start gap-3 rounded border border-amber-200 bg-amber-50 px-4 py-3">
      <AlertCircle class="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
      <div>
        <p class="text-sm font-semibold text-amber-800">Cloudflared no configurado</p>
        <p class="text-xs text-amber-700 mt-0.5">{warning}</p>
      </div>
    </div>
  {/if}

  <!-- Stats row -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
    <div class="stat-card">
      <div class="stat-value">{total}</div>
      <div class="stat-label">Total Tunnels</div>
    </div>
    <div class="stat-card">
      <div class="stat-value text-green-600">
        {tunnels.filter(t => t.status === 'healthy' || t.status === 'active' || t.status === 'running').length}
      </div>
      <div class="stat-label">Activos</div>
    </div>
    <div class="stat-card">
      <div class="stat-value text-amber-600">
        {tunnels.filter(t => t.status === 'degraded' || t.status === 'connecting').length}
      </div>
      <div class="stat-label">Degradados</div>
    </div>
    <div class="stat-card">
      <div class="stat-value text-gray-500">
        {tunnels.filter(t => t.status === 'inactive' || t.status === 'stopped').length}
      </div>
      <div class="stat-label">Inactivos</div>
    </div>
  </div>

  <!-- Table -->
  <div class="card p-0 overflow-hidden">
    {#if loading}
      <div class="py-16 flex items-center justify-center">
        <div class="text-sm text-gray-500 animate-pulse">Cargando tunnels...</div>
      </div>
    {:else if tunnels.length === 0}
      <div class="py-16 flex flex-col items-center justify-center gap-2">
        <Wifi class="w-8 h-8 text-border-light" />
        <p class="text-sm text-gray-500">No hay tunnels configurados</p>
        {#if warning}
          <p class="text-xs text-gray-500">Instala cloudflared para crear tunnels</p>
        {/if}
      </div>
    {:else}
      <div class="overflow-x-auto">
        <table class="table w-full">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nombre</th>
              <th>Estado</th>
              <th>Subdominio</th>
              <th>Dominio</th>
              <th>Plan</th>
              <th>Creado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {#each tunnels as tunnel}
              <tr>
                <td>
                  <span class="font-mono text-[11px] text-text-secondary" title={tunnel.id}>
                    {truncateId(tunnel.id)}
                  </span>
                </td>
                <td>
                  <div class="flex items-center gap-2">
                    <Globe class="w-3.5 h-3.5 text-gray-500 flex-shrink-0" />
                    <span class="text-sm font-medium text-text-primary">{tunnel.name}</span>
                  </div>
                </td>
                <td>
                  <span class="badge {statusBadgeClass(tunnel.status)}">{tunnel.status}</span>
                </td>
                <td>
                  {#if tunnel.deployment?.subdomain}
                    <span class="font-mono text-[11px] text-text-secondary">{tunnel.deployment.subdomain}</span>
                  {:else}
                    <span class="text-gray-500 text-xs">—</span>
                  {/if}
                </td>
                <td>
                  {#if tunnel.deployment?.domain}
                    <span class="text-sm text-text-secondary">{tunnel.deployment.domain}</span>
                  {:else}
                    <span class="text-gray-500 text-xs">—</span>
                  {/if}
                </td>
                <td>
                  {#if tunnel.deployment?.plan}
                    <span class="badge {planBadgeClass(tunnel.deployment.plan)}">{tunnel.deployment.plan}</span>
                  {:else}
                    <span class="text-gray-500 text-xs">—</span>
                  {/if}
                </td>
                <td>
                  <span class="text-xs text-text-secondary">{formatDate(tunnel.created_at)}</span>
                </td>
                <td>
                  <div class="flex items-center gap-1">
                    <button
                      class="btn btn-secondary btn-sm"
                      on:click={() => restartTunnel(tunnel)}
                      disabled={restartingId === tunnel.id}
                      title="Reiniciar tunnel"
                    >
                      <RotateCcw class="w-3 h-3 {restartingId === tunnel.id ? 'animate-spin' : ''}" />
                    </button>
                    <button
                      class="btn btn-danger btn-sm"
                      on:click={() => openDeleteModal(tunnel)}
                      title="Eliminar tunnel"
                    >
                      <Trash2 class="w-3 h-3" />
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
</div>

<!-- Delete confirmation modal -->
<Modal
  isOpen={deleteModalOpen}
  title="Eliminar Tunnel"
  confirmText="ELIMINAR"
  confirmVariant="danger"
  loading={deleteLoading}
  on:close={() => { deleteModalOpen = false; selectedTunnel = null; }}
  on:confirm={confirmDelete}
>
  {#if selectedTunnel}
    <div class="space-y-3">
      <p class="text-sm text-text-secondary">
        ¿Estás seguro de que deseas eliminar el tunnel <strong class="text-text-primary">{selectedTunnel.name}</strong>?
      </p>
      <div class="rounded bg-bg-page border border-border-light p-3">
        <p class="text-[10px] label mb-1">ID del tunnel</p>
        <p class="font-mono text-xs text-text-primary">{selectedTunnel.id}</p>
      </div>
      <p class="text-xs text-error">Esta acción no se puede deshacer. El tunnel será eliminado permanentemente.</p>
    </div>
  {/if}
</Modal>
