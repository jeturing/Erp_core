<script lang="ts">
  import { onMount } from 'svelte';
  import { tunnelsApi } from '../lib/api';
  import { toasts } from '../lib/stores/toast';
  import { formatDate } from '../lib/utils/formatters';
  import { RefreshCw } from 'lucide-svelte';
  import type { Tunnel, TunnelDeployment } from '../lib/api/tunnels';



  let tunnels = $state<Tunnel[]>([]);
  let loading = $state(true);
  let warning = $state<string | null>(null);
  let totalTunnels = $state(0);

  async function loadTunnels() {
    loading = true;
    try {
      const data = await tunnelsApi.list();
      tunnels = data.tunnels ?? [];
      totalTunnels = data.total ?? tunnels.length;
      warning = data.warning ?? null;
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al cargar tunnels');
    } finally {
      loading = false;
    }
  }

  async function handleRestart(id: string) {
    try {
      await tunnelsApi.restart(id);
      toasts.success('Tunnel reiniciado');
      await loadTunnels();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al reiniciar tunnel');
    }
  }

  async function handleDelete(tunnel: Tunnel) {
    if (!window.confirm(`¿Eliminar el tunnel "${tunnel.name}" (${tunnel.id.slice(0, 8)})?`)) return;
    try {
      await tunnelsApi.delete(tunnel.id);
      toasts.success('Tunnel eliminado');
      await loadTunnels();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al eliminar tunnel');
    }
  }

  onMount(loadTunnels);
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="page-title">CLOUDFLARE TUNNELS</h1>
      <p class="page-subtitle">Gestión de túneles de red</p>
    </div>
    <button class="btn-secondary px-4 py-2 flex items-center gap-2" onclick={loadTunnels} disabled={loading}>
      <RefreshCw size={14} class={loading ? 'animate-spin' : ''} />
      ACTUALIZAR
    </button>
  </div>

  <!-- Warning banner -->
  {#if warning}
    <div class="bg-amber-50 border border-amber-200 px-4 py-3 flex items-start gap-3">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-amber-600 shrink-0 mt-0.5">
        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      <p class="text-sm text-amber-700">{warning}</p>
    </div>
  {/if}

  <!-- Stat -->
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
    <div class="stat-card card">
      <div class="stat-value">{totalTunnels}</div>
      <div class="stat-label">Total Tunnels</div>
    </div>
  </div>

  <!-- Table -->
  <div class="card p-0 overflow-hidden">
    {#if loading}
      <div class="p-8 text-center text-gray-500 text-sm">Cargando tunnels...</div>
    {:else if tunnels.length === 0}
      <div class="p-8 text-center text-gray-500 text-sm">No hay tunnels registrados</div>
    {:else}
      <table class="table w-full">
        <thead>
          <tr>
            <th>ID</th>
            <th>NOMBRE</th>
            <th>ESTADO</th>
            <th>SUBDOMINIO</th>
            <th>DOMINIO</th>
            <th>CREADO</th>
            <th>ACCIONES</th>
          </tr>
        </thead>
        <tbody>
          {#each tunnels as tunnel (tunnel.id)}
            <tr>
              <td class="font-mono text-xs text-gray-500">{tunnel.id.slice(0, 8)}</td>
              <td class="text-sm font-medium">{tunnel.name}</td>
              <td>
                {#if tunnel.status === 'active' || tunnel.status === 'healthy'}
                  <span class="badge-success">{tunnel.status}</span>
                {:else if tunnel.status === 'inactive' || tunnel.status === 'down'}
                  <span class="badge-error">{tunnel.status}</span>
                {:else}
                  <span class="badge-warning">{tunnel.status}</span>
                {/if}
              </td>
              <td class="text-sm text-gray-600">{tunnel.deployment?.subdomain ?? '-'}</td>
              <td class="text-sm text-gray-600">{tunnel.deployment?.domain ?? '-'}</td>
              <td class="text-sm text-gray-500">{formatDate(tunnel.created_at)}</td>
              <td>
                <div class="flex items-center gap-2">
                  <button class="btn-secondary btn-sm" onclick={() => handleRestart(tunnel.id)}>REINICIAR</button>
                  <button class="btn-danger btn-sm" onclick={() => handleDelete(tunnel)}>ELIMINAR</button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>
</div>
