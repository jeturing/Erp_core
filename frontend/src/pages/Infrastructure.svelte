<script lang="ts">
  import { onMount } from 'svelte';
  import { Card, Badge, Button, Spinner } from '../lib/components';
  import { infrastructureApi } from '../lib/api';
  import type { ClusterStatus, ClusterSummary, ContainerItem, NodeSummary } from '../lib/types';

  let loading = true;
  let error = '';

  let nodes: NodeSummary[] = [];
  let clusterStatus: ClusterStatus | null = null;
  let clusterSummary: ClusterSummary | null = null;
  let containers: ContainerItem[] = [];

  async function loadData() {
    loading = true;
    error = '';
    try {
      const [nodesData, statusData, summaryData, containersData] = await Promise.all([
        infrastructureApi.getNodes(),
        infrastructureApi.getClusterStatus(),
        infrastructureApi.getClusterSummary(),
        infrastructureApi.getContainers(),
      ]);
      nodes = nodesData.items;
      clusterStatus = statusData;
      clusterSummary = summaryData;
      containers = containersData.items;
    } catch (err) {
      error = err instanceof Error ? err.message : 'No se pudo cargar infraestructura';
    } finally {
      loading = false;
    }
  }

  onMount(loadData);

  function healthVariant(value: string) {
    if (value === 'healthy' || value === 'online' || value === 'running') return 'success';
    if (value === 'warning' || value === 'maintenance') return 'warning';
    if (value === 'critical' || value === 'offline' || value === 'stopped') return 'error';
    return 'secondary';
  }

  function asPercent(value: number) {
    return `${Math.round(value || 0)}%`;
  }
</script>

<div class="p-6 lg:p-8 space-y-6">
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold text-white">Infrastructure</h1>
      <p class="text-secondary-400 mt-1">Nodos, estado del cluster y contenedores activos</p>
    </div>
    <Button variant="secondary" on:click={loadData}>Actualizar</Button>
  </div>

  {#if loading}
    <div class="py-16 flex justify-center"><Spinner size="lg" /></div>
  {:else if error}
    <Card>
      <p class="text-error text-sm">{error}</p>
    </Card>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <p class="text-xs uppercase tracking-wider text-secondary-500">Health</p>
        <div class="mt-2"><Badge variant={healthVariant(clusterSummary?.health || 'critical')}>{clusterSummary?.health || 'unknown'}</Badge></div>
      </Card>
      <Card>
        <p class="text-xs uppercase tracking-wider text-secondary-500">Nodos online</p>
        <p class="mt-2 text-2xl font-bold text-white">{clusterSummary?.nodes.online || 0} / {clusterSummary?.nodes.total || 0}</p>
      </Card>
      <Card>
        <p class="text-xs uppercase tracking-wider text-secondary-500">Contenedores</p>
        <p class="mt-2 text-2xl font-bold text-white">{clusterSummary?.containers.running || 0} / {clusterSummary?.containers.total || 0}</p>
      </Card>
      <Card>
        <p class="text-xs uppercase tracking-wider text-secondary-500">RAM cluster</p>
        <p class="mt-2 text-2xl font-bold text-white">{asPercent(clusterSummary?.resources.ram.usage_percent || 0)}</p>
      </Card>
    </div>

    <Card title="Resumen de recursos" subtitle="/api/nodes/metrics/summary">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div class="rounded-lg bg-surface-highlight border border-surface-border p-4">
          <p class="text-secondary-400">CPU</p>
          <p class="mt-1 text-white font-semibold">{clusterSummary?.resources.cpu.cores || 0} cores</p>
          <p class="text-secondary-500">Uso: {asPercent(clusterSummary?.resources.cpu.usage_percent || 0)}</p>
        </div>
        <div class="rounded-lg bg-surface-highlight border border-surface-border p-4">
          <p class="text-secondary-400">RAM</p>
          <p class="mt-1 text-white font-semibold">{clusterSummary?.resources.ram.used_gb || 0} / {clusterSummary?.resources.ram.total_gb || 0} GB</p>
          <p class="text-secondary-500">Uso: {asPercent(clusterSummary?.resources.ram.usage_percent || 0)}</p>
        </div>
        <div class="rounded-lg bg-surface-highlight border border-surface-border p-4">
          <p class="text-secondary-400">Storage</p>
          <p class="mt-1 text-white font-semibold">{clusterSummary?.resources.storage.used_gb || 0} / {clusterSummary?.resources.storage.total_gb || 0} GB</p>
          <p class="text-secondary-500">Uso: {asPercent(clusterSummary?.resources.storage.usage_percent || 0)}</p>
        </div>
      </div>
    </Card>

    <Card title="Nodos" subtitle="/api/nodes" padding="none">
      <div class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr>
              <th>Nodo</th>
              <th>Estado</th>
              <th>Containers</th>
              <th>CPU</th>
              <th>RAM</th>
              <th>Storage</th>
            </tr>
          </thead>
          <tbody>
            {#each nodes as node}
              <tr>
                <td>
                  <p class="font-medium text-white">{node.name}</p>
                  <p class="text-xs text-secondary-500">{node.hostname}</p>
                </td>
                <td><Badge variant={healthVariant(node.status)}>{node.status}</Badge></td>
                <td class="text-secondary-300">{node.containers.current} / {node.containers.max}</td>
                <td class="text-secondary-300">{asPercent(node.resources.cpu.usage_percent)}</td>
                <td class="text-secondary-300">{asPercent(node.resources.ram.usage_percent)}</td>
                <td class="text-secondary-300">{asPercent(node.resources.storage.usage_percent)}</td>
              </tr>
            {:else}
              <tr>
                <td colspan="6" class="text-center text-secondary-500 py-8">No hay nodos registrados</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </Card>

    <Card title="Contenedores" subtitle="/api/nodes/containers/all" padding="none">
      <div class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr>
              <th>Hostname</th>
              <th>Nodo</th>
              <th>Estado</th>
              <th>IP</th>
              <th>CPU</th>
              <th>RAM (MB)</th>
            </tr>
          </thead>
          <tbody>
            {#each containers.slice(0, 20) as container}
              <tr>
                <td class="text-white font-medium">{container.hostname}</td>
                <td class="text-secondary-300">{container.node || '-'}</td>
                <td><Badge variant={healthVariant(container.status)}>{container.status}</Badge></td>
                <td class="text-secondary-300">{container.ip || '-'}</td>
                <td class="text-secondary-300">{asPercent(container.usage.cpu_percent)}</td>
                <td class="text-secondary-300">{container.usage.ram_mb}</td>
              </tr>
            {:else}
              <tr>
                <td colspan="6" class="text-center text-secondary-500 py-8">No hay contenedores detectados</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </Card>

    {#if clusterStatus}
      <Card title="Estado global del cluster" subtitle="/api/nodes/status">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <p class="text-secondary-400">Health</p>
            <Badge variant={healthVariant(clusterStatus.cluster_health)}>{clusterStatus.cluster_health}</Badge>
          </div>
          <div>
            <p class="text-secondary-400">Nodos online</p>
            <p class="text-white font-medium">{clusterStatus.online_nodes} / {clusterStatus.total_nodes}</p>
          </div>
          <div>
            <p class="text-secondary-400">RAM usada</p>
            <p class="text-white font-medium">{clusterStatus.used_ram_gb} / {clusterStatus.total_ram_gb} GB</p>
          </div>
        </div>
      </Card>
    {/if}
  {/if}
</div>
