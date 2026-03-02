<script lang="ts">
  import { onMount } from 'svelte';
  import { infrastructureApi } from '../lib/api';
  import { toasts } from '../lib/stores/toast';
  import { formatPercent } from '../lib/utils/formatters';
  import type { NodeSummary, ContainerItem, ClusterSummary } from '../lib/types';
  import { RefreshCw, Server, ChevronDown, ChevronUp, Plus, Copy } from 'lucide-svelte';

  let nodes: NodeSummary[] = [];
  let containers: ContainerItem[] = [];
  let summary: ClusterSummary | null = null;
  let loading = true;
  let showContainers = false;
  let creatingNode = false;
  let createMode: 'new' | 'clone' = 'new';
  let cloneFromNodeId: number | null = null;

  let nodeForm = {
    name: '',
    hostname: '',
    total_cpu_cores: 8,
    total_ram_gb: 16,
    total_storage_gb: 250,
    region: 'default',
    ssh_port: 22,
    api_port: 8006,
    max_containers: 50,
    is_database_node: false,
    ssh_user: 'root',
    api_token_id: '',
  };

  async function loadData() {
    loading = true;
    try {
      const [nodesRes, summaryRes, containersRes] = await Promise.all([
        infrastructureApi.getNodes(),
        infrastructureApi.getClusterSummary(),
        infrastructureApi.getContainers(),
      ]);
      nodes = nodesRes.items ?? [];
      summary = summaryRes;
      containers = containersRes.items ?? [];
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error cargando infraestructura');
    } finally {
      loading = false;
    }
  }

  onMount(loadData);

  function statusBadge(status: string) {
    if (status === 'online') return 'badge-success';
    if (status === 'maintenance') return 'badge-warning';
    if (status === 'offline') return 'badge-error';
    return 'badge-neutral';
  }

  function containerStatusBadge(status: string) {
    if (status === 'running') return 'badge-success';
    if (status === 'paused') return 'badge-warning';
    if (status === 'stopped') return 'badge-error';
    return 'badge-neutral';
  }

  function healthBadge(health: string) {
    if (health === 'healthy') return 'badge-success';
    if (health === 'warning') return 'badge-warning';
    if (health === 'critical') return 'badge-error';
    return 'badge-neutral';
  }

  function usageColor(pct: number) {
    if (pct >= 85) return 'bg-error';
    if (pct >= 65) return 'bg-warning';
    return 'bg-success';
  }

  function applyCloneTemplate(nodeId: number | null) {
    cloneFromNodeId = nodeId;
    if (!nodeId) return;
    const tpl = nodes.find((n) => n.id === nodeId);
    if (!tpl) return;

    nodeForm = {
      ...nodeForm,
      total_cpu_cores: tpl.resources.cpu.total_cores,
      total_ram_gb: tpl.resources.ram.total_gb,
      total_storage_gb: tpl.resources.storage.total_gb,
      region: tpl.region || 'default',
      max_containers: tpl.containers.max || 50,
      is_database_node: tpl.is_database_node,
      ssh_port: 22,
      api_port: 8006,
      ssh_user: 'root',
      api_token_id: '',
      name: `${tpl.name}-clone`,
      hostname: `${tpl.hostname.split('.')[0]}-clone.local`,
    };
  }

  async function handleCreateNode() {
    if (!nodeForm.name.trim() || !nodeForm.hostname.trim()) {
      toasts.error('Nombre y hostname son obligatorios');
      return;
    }

    creatingNode = true;
    try {
      const payload = {
        ...nodeForm,
        name: nodeForm.name.trim(),
        hostname: nodeForm.hostname.trim(),
        api_token_id: nodeForm.api_token_id.trim() || null,
      };
      const res = await infrastructureApi.createNode(payload);
      toasts.success(`Nodo creado: ${res.name}`);

      nodeForm = {
        ...nodeForm,
        name: '',
        hostname: '',
        api_token_id: '',
      };
      cloneFromNodeId = null;
      await loadData();
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error creando nodo');
    } finally {
      creatingNode = false;
    }
  }
</script>

<div class="p-6 lg:p-8 space-y-6">
  <!-- Page Header -->
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
      <h1 class="page-title">INFRASTRUCTURE</h1>
      <p class="page-subtitle mt-1">Estado del cluster Proxmox, nodos y contenedores</p>
    </div>
    <button class="btn btn-secondary btn-sm" on:click={loadData} disabled={loading}>
      <RefreshCw size={13} class={loading ? 'animate-spin' : ''} />
      Actualizar
    </button>
  </div>

  {#if loading}
    <div class="py-24 flex justify-center">
      <div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin"></div>
    </div>
  {:else}
    <!-- Node Create / Clone -->
    <div class="card p-6 space-y-4">
      <div class="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h2 class="section-heading">Escalado de nodos</h2>
          <p class="text-xs text-gray-500 mt-1">Agrega nodos nuevos o clona la configuración base de un nodo template.</p>
        </div>
        <div class="flex items-center gap-2">
          <button
            class="btn btn-sm {createMode === 'new' ? 'btn-primary' : 'btn-secondary'}"
            on:click={() => (createMode = 'new')}
            type="button"
          >
            <Plus size={12} /> Nuevo nodo
          </button>
          <button
            class="btn btn-sm {createMode === 'clone' ? 'btn-primary' : 'btn-secondary'}"
            on:click={() => (createMode = 'clone')}
            type="button"
          >
            <Copy size={12} /> Clonar template
          </button>
        </div>
      </div>

      {#if createMode === 'clone'}
        <div>
          <label class="label">Template base</label>
          <select
            class="input"
            bind:value={cloneFromNodeId}
            on:change={(e) => applyCloneTemplate(Number((e.currentTarget as HTMLSelectElement).value) || null)}
          >
            <option value="">Selecciona un nodo existente...</option>
            {#each nodes as n}
              <option value={n.id}>{n.name} ({n.hostname})</option>
            {/each}
          </select>
        </div>
      {/if}

      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <label class="label">Nombre</label>
          <input class="input" type="text" bind:value={nodeForm.name} placeholder="pve-node-03" />
        </div>
        <div>
          <label class="label">Hostname</label>
          <input class="input" type="text" bind:value={nodeForm.hostname} placeholder="10.10.10.150" />
        </div>
        <div>
          <label class="label">Región</label>
          <input class="input" type="text" bind:value={nodeForm.region} placeholder="do-santo-domingo" />
        </div>

        <div>
          <label class="label">CPU Cores</label>
          <input class="input" type="number" min="1" bind:value={nodeForm.total_cpu_cores} />
        </div>
        <div>
          <label class="label">RAM (GB)</label>
          <input class="input" type="number" min="1" step="0.5" bind:value={nodeForm.total_ram_gb} />
        </div>
        <div>
          <label class="label">Storage (GB)</label>
          <input class="input" type="number" min="10" step="1" bind:value={nodeForm.total_storage_gb} />
        </div>

        <div>
          <label class="label">Max containers</label>
          <input class="input" type="number" min="1" bind:value={nodeForm.max_containers} />
        </div>
        <div>
          <label class="label">SSH user</label>
          <input class="input" type="text" bind:value={nodeForm.ssh_user} />
        </div>
        <div>
          <label class="label">API token ID (opcional)</label>
          <input class="input" type="text" bind:value={nodeForm.api_token_id} placeholder="root@pam!erp-core" />
        </div>
      </div>

      <div class="flex items-center justify-between flex-wrap gap-3">
        <label class="flex items-center gap-2 text-sm text-gray-600">
          <input type="checkbox" bind:checked={nodeForm.is_database_node} />
          Nodo dedicado de base de datos
        </label>

        <button class="btn btn-primary btn-sm" on:click={handleCreateNode} disabled={creatingNode}>
          {#if creatingNode}
            <RefreshCw size={12} class="animate-spin" /> Creando...
          {:else if createMode === 'clone'}
            <Copy size={12} /> Clonar y crear nodo
          {:else}
            <Plus size={12} /> Crear nodo
          {/if}
        </button>
      </div>
    </div>

    <!-- Cluster Summary Stats -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="stat-card">
        <span class="stat-label">Nodos Online</span>
        <span class="stat-value text-success">{summary?.nodes.online ?? 0}<span class="text-base text-gray-400 font-normal ml-1">/ {summary?.nodes.total ?? 0}</span></span>
        {#if summary}
          <span class="badge {healthBadge(summary.health)} mt-1 self-start">{summary.health}</span>
        {/if}
      </div>
      <div class="stat-card">
        <span class="stat-label">Containers</span>
        <span class="stat-value">{summary?.containers.running ?? 0}<span class="text-base text-gray-400 font-normal ml-1">/ {summary?.containers.total ?? 0}</span></span>
        <span class="text-[11px] text-gray-500">corriendo / total</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">CPU Promedio</span>
        <span class="stat-value">{formatPercent(summary?.resources.cpu.usage_percent ?? 0)}</span>
        <div class="h-1.5 rounded-full bg-border-light overflow-hidden mt-1">
          <div
            class="h-full rounded-full {usageColor(summary?.resources.cpu.usage_percent ?? 0)} transition-all"
            style="width: {Math.min(100, summary?.resources.cpu.usage_percent ?? 0)}%"
          ></div>
        </div>
      </div>
      <div class="stat-card">
        <span class="stat-label">RAM Promedio</span>
        <span class="stat-value">{formatPercent(summary?.resources.ram.usage_percent ?? 0)}</span>
        <div class="h-1.5 rounded-full bg-border-light overflow-hidden mt-1">
          <div
            class="h-full rounded-full {usageColor(summary?.resources.ram.usage_percent ?? 0)} transition-all"
            style="width: {Math.min(100, summary?.resources.ram.usage_percent ?? 0)}%"
          ></div>
        </div>
        <span class="text-[11px] text-gray-500">{(summary?.resources.ram.used_gb ?? 0).toFixed(1)} / {(summary?.resources.ram.total_gb ?? 0).toFixed(1)} GB</span>
      </div>
    </div>

    <!-- Nodes Table -->
    <div class="card p-0 overflow-hidden">
      <div class="flex items-center gap-2 px-6 py-4 border-b border-border-light">
        <Server size={14} class="text-gray-400" />
        <span class="section-heading">Nodos del Cluster</span>
        <span class="text-[11px] text-gray-500 ml-auto">{nodes.length} nodo{nodes.length !== 1 ? 's' : ''}</span>
      </div>
      <div class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Región</th>
              <th>Estado</th>
              <th>Containers</th>
              <th>CPU%</th>
              <th>RAM%</th>
              <th>Storage%</th>
            </tr>
          </thead>
          <tbody>
            {#each nodes as node (node.id)}
              <tr>
                <td>
                  <div class="flex flex-col gap-0.5">
                    <span class="font-semibold text-text-primary">{node.name}</span>
                    <span class="text-[11px] text-gray-400 font-mono">{node.hostname}</span>
                    {#if node.is_database_node}
                      <span class="badge badge-info mt-0.5 self-start">DB Node</span>
                    {/if}
                  </div>
                </td>
                <td class="text-text-secondary text-sm">{node.region}</td>
                <td>
                  <span class="badge {statusBadge(node.status)}">{node.status}</span>
                </td>
                <td class="text-text-secondary text-sm">
                  {node.containers.current} / {node.containers.max}
                </td>
                <td>
                  <div class="flex items-center gap-2 min-w-[80px]">
                    <div class="flex-1 h-1.5 rounded-full bg-border-light overflow-hidden">
                      <div
                        class="h-full rounded-full {usageColor(node.resources.cpu.usage_percent)} transition-all"
                        style="width: {Math.min(100, node.resources.cpu.usage_percent)}%"
                      ></div>
                    </div>
                    <span class="text-[11px] text-text-secondary w-8 text-right">{formatPercent(node.resources.cpu.usage_percent)}</span>
                  </div>
                </td>
                <td>
                  <div class="flex items-center gap-2 min-w-[80px]">
                    <div class="flex-1 h-1.5 rounded-full bg-border-light overflow-hidden">
                      <div
                        class="h-full rounded-full {usageColor(node.resources.ram.usage_percent)} transition-all"
                        style="width: {Math.min(100, node.resources.ram.usage_percent)}%"
                      ></div>
                    </div>
                    <span class="text-[11px] text-text-secondary w-8 text-right">{formatPercent(node.resources.ram.usage_percent)}</span>
                  </div>
                </td>
                <td>
                  <div class="flex items-center gap-2 min-w-[80px]">
                    <div class="flex-1 h-1.5 rounded-full bg-border-light overflow-hidden">
                      <div
                        class="h-full rounded-full {usageColor(node.resources.storage.usage_percent)} transition-all"
                        style="width: {Math.min(100, node.resources.storage.usage_percent)}%"
                      ></div>
                    </div>
                    <span class="text-[11px] text-text-secondary w-8 text-right">{formatPercent(node.resources.storage.usage_percent)}</span>
                  </div>
                </td>
              </tr>
            {:else}
              <tr>
                <td colspan="7" class="text-center text-gray-500 py-12 text-sm">No hay nodos disponibles</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Containers Table (collapsible) -->
    <div class="card p-0 overflow-hidden">
      <button
        class="w-full flex items-center justify-between px-6 py-4 border-b border-border-light hover:bg-bg-card/50 transition-colors"
        on:click={() => showContainers = !showContainers}
      >
        <div class="flex items-center gap-2">
          <span class="section-heading">Todos los Containers</span>
          <span class="badge badge-neutral">{containers.length}</span>
        </div>
        {#if showContainers}
          <ChevronUp size={16} class="text-gray-400" />
        {:else}
          <ChevronDown size={16} class="text-gray-400" />
        {/if}
      </button>

      {#if showContainers}
        <div class="overflow-x-auto">
          <table class="table">
            <thead>
              <tr>
                <th>VMID</th>
                <th>Hostname</th>
                <th>Nodo</th>
                <th>Estado</th>
                <th>IP</th>
                <th>RAM (MB)</th>
                <th>Disco (GB)</th>
              </tr>
            </thead>
            <tbody>
              {#each containers as ct (ct.id)}
                <tr>
                  <td class="font-mono text-sm text-text-secondary">{ct.vmid}</td>
                  <td class="font-medium text-text-primary">{ct.hostname}</td>
                  <td class="text-text-secondary text-sm">{ct.node || '-'}</td>
                  <td>
                    <span class="badge {containerStatusBadge(ct.status)}">{ct.status}</span>
                  </td>
                  <td class="font-mono text-[11px] text-text-secondary">{ct.ip || '-'}</td>
                  <td class="text-text-secondary text-sm">{ct.usage.ram_mb > 0 ? ct.usage.ram_mb.toFixed(0) : ct.resources.ram_mb}</td>
                  <td class="text-text-secondary text-sm">{ct.usage.disk_gb > 0 ? ct.usage.disk_gb.toFixed(1) : ct.resources.disk_gb}</td>
                </tr>
              {:else}
                <tr>
                  <td colspan="7" class="text-center text-gray-500 py-8 text-sm">No hay containers disponibles</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </div>
  {/if}
</div>
