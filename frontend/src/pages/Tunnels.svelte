<script lang="ts">
  import { onMount } from 'svelte';
  import { Badge, Button, Card, Input, Modal, Spinner } from '../lib/components';
  import { tunnelsApi } from '../lib/api';
  import type { Tunnel } from '../lib/types';

  let loading = true;
  let creating = false;
  let deleting = false;
  let error = '';
  let warning = '';

  let tunnels: Tunnel[] = [];
  let showCreateModal = false;
  let showDeleteModal = false;
  let selectedTunnel: Tunnel | null = null;
  let formError = '';

  let createForm = {
    subscription_id: '',
    container_id: '',
    local_port: 8069,
  };

  function statusVariant(status: string) {
    if (status === 'active' || status === 'healthy' || status === 'running') return 'success';
    if (status === 'warning' || status === 'degraded') return 'warning';
    if (status === 'error' || status === 'stopped') return 'error';
    return 'secondary';
  }

  async function loadData() {
    loading = true;
    error = '';
    warning = '';
    try {
      const response = await tunnelsApi.listTunnels();
      tunnels = response.tunnels || [];
      warning = response.warning || '';
    } catch (err) {
      error = err instanceof Error ? err.message : 'No se pudieron cargar tunnels';
    } finally {
      loading = false;
    }
  }

  async function handleCreate() {
    formError = '';
    if (!createForm.subscription_id.trim() || !createForm.container_id.trim()) {
      formError = 'Subscription ID y Container ID son obligatorios';
      return;
    }

    creating = true;
    try {
      await tunnelsApi.createTunnel({
        subscription_id: createForm.subscription_id.trim(),
        container_id: Number(createForm.container_id),
        local_port: Number(createForm.local_port) || 8069,
      });
      showCreateModal = false;
      createForm = { subscription_id: '', container_id: '', local_port: 8069 };
      await loadData();
    } catch (err) {
      formError = err instanceof Error ? err.message : 'No se pudo crear tunnel';
    } finally {
      creating = false;
    }
  }

  function openDeleteModal(tunnel: Tunnel) {
    selectedTunnel = tunnel;
    showDeleteModal = true;
  }

  async function handleDelete() {
    if (!selectedTunnel) return;
    deleting = true;
    formError = '';
    try {
      await tunnelsApi.deleteTunnel(selectedTunnel.id || selectedTunnel.name);
      showDeleteModal = false;
      selectedTunnel = null;
      await loadData();
    } catch (err) {
      formError = err instanceof Error ? err.message : 'No se pudo eliminar tunnel';
    } finally {
      deleting = false;
    }
  }

  onMount(loadData);
</script>

<div class="p-6 lg:p-8 space-y-6">
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold text-white">Tunnels</h1>
      <p class="text-secondary-400 mt-1">Gestion de Cloudflare Tunnels activos</p>
    </div>
    <div class="flex gap-2">
      <Button variant="secondary" on:click={loadData}>Actualizar</Button>
      <Button variant="accent" on:click={() => (showCreateModal = true)}>Crear tunnel</Button>
    </div>
  </div>

  {#if error}
    <Card><p class="text-sm text-error">{error}</p></Card>
  {/if}

  {#if warning}
    <Card><p class="text-sm text-warning">{warning}</p></Card>
  {/if}

  <Card title="Tunnels activos" subtitle="/api/tunnels" padding="none">
    {#if loading}
      <div class="py-12 flex justify-center"><Spinner size="lg" /></div>
    {:else}
      <div class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr>
              <th>Tunnel</th>
              <th>Estado</th>
              <th>Tenant</th>
              <th>Dominio</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {#each tunnels as tunnel}
              <tr>
                <td>
                  <p class="font-medium text-white">{tunnel.name}</p>
                  <p class="text-xs text-secondary-500">{tunnel.id}</p>
                </td>
                <td><Badge variant={statusVariant(tunnel.status)}>{tunnel.status || 'unknown'}</Badge></td>
                <td class="text-secondary-300">{tunnel.deployment?.subdomain || '-'}</td>
                <td class="text-secondary-300">{tunnel.deployment?.url || tunnel.deployment?.domain || '-'}</td>
                <td>
                  <Button size="sm" variant="danger" on:click={() => openDeleteModal(tunnel)}>Eliminar</Button>
                </td>
              </tr>
            {:else}
              <tr>
                <td colspan="5" class="text-center text-secondary-500 py-8">No hay tunnels activos</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </Card>
</div>

<Modal
  bind:isOpen={showCreateModal}
  title="Crear tunnel"
  confirmText="Crear"
  on:confirm={handleCreate}
  on:close={() => {
    showCreateModal = false;
    formError = '';
  }}
  loading={creating}
>
  <div class="space-y-4">
    {#if formError}
      <div class="rounded-lg border border-error/30 bg-error/10 px-3 py-2 text-sm text-error">{formError}</div>
    {/if}

    <Input label="Subscription ID" bind:value={createForm.subscription_id} placeholder="123" required />
    <Input label="Container ID" type="number" bind:value={createForm.container_id} placeholder="105" required />
    <Input label="Puerto local" type="number" bind:value={createForm.local_port} placeholder="8069" />
  </div>
</Modal>

<Modal
  bind:isOpen={showDeleteModal}
  title="Eliminar tunnel"
  confirmText="Eliminar"
  confirmVariant="danger"
  on:confirm={handleDelete}
  on:close={() => {
    showDeleteModal = false;
    selectedTunnel = null;
    formError = '';
  }}
  loading={deleting}
>
  {#if selectedTunnel}
    <div class="space-y-3 text-sm text-secondary-300">
      <p>
        Se eliminara el tunnel
        <strong class="text-error"> {selectedTunnel.name}</strong>.
      </p>
      <p class="text-secondary-500">Esta accion es irreversible.</p>
      {#if formError}
        <div class="rounded-lg border border-error/30 bg-error/10 px-3 py-2 text-sm text-error">{formError}</div>
      {/if}
    </div>
  {/if}
</Modal>
