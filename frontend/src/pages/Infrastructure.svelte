<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { infrastructureApi } from '../lib/api';
  import { toasts } from '../lib/stores/toast';
  import { formatPercent } from '../lib/utils/formatters';
  import type { NodeSummary, ContainerItem, ClusterSummary } from '../lib/types';
  import { RefreshCw, Server, ChevronDown, ChevronUp, Plus, Copy, Database, Wifi, WifiOff, Activity } from 'lucide-svelte';

  let nodes: NodeSummary[] = [];
  let containers: ContainerItem[] = [];
  let summary: ClusterSummary | null = null;
  let loading = true;
  let showContainers = false;
  let creatingNode = false;
  let createMode: 'new' | 'clone' = 'new';
  let cloneFromNodeId: number | null = null;

  // Live stats per node: nodeId → stats object
  let liveStats: Record<number, any> = {};
  let liveLoading: Record<number, boolean> = {};
  let pollingInterval: ReturnType<typeof setInterval> | null = null;

  let nodeForm = {
    name: '',
    hostname: '',
    total_cpu_cores: 8,
    total_ram_gb: 16,
    total_storage_gb: 250,
    region: 'do-sto-domingo',
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

  async function fetchLiveStats(nodeId: number) {
    liveLoading[nodeId] = true;
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const res = await fetch(`/api/nodes/${nodeId}/live-stats`, {
        credentials: 'include',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        liveStats[nodeId] = data;
        liveStats = { ...liveStats };
      }
    } catch (err) {
      // silently fail
    } finally {
      liveLoading[nodeId] = false;
      liveLoading = { ...liveLoading };
    }
  }

  async function refreshAllLive() {
    if (nodes.length === 0) return;
    await Promise.all(nodes.map((n) => fetchLiveStats(n.id)));
  }

  onMount(async () => {
    await loadData();
    // Cargar stats en vivo al inicio y luego cada 30s
    await refreshAllLive();
    pollingInterval = setInterval(refreshAllLive, 30_000);
  });

  onDestroy(() => {
    if (pollingInterval) clearInterval(pollingInterval);
  });

  // ── helpers ──────────────────────────────────────────
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

  function usageRingColor(pct: number) {
    if (pct >= 85) return '#ef4444';
    if (pct >= 65) return '#f59e0b';
    return '#22c55e';
  }

  // SVG ring gauge (r=18 → circumference ≈ 113)
  function ringDashoffset(pct: number, r = 18): string {
    const circ = 2 * Math.PI * r;
    return String(circ - (circ * Math.min(100, pct)) / 100);
  }

  function fmtMb(mb: number): string {
    if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
    return `${mb} MB`;
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
      nodeForm = { ...nodeForm, name: '', hostname: '', api_token_id: '' };
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
  <!-- Header -->
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
      <h1 class="page-title">INFRASTRUCTURE</h1>
      <p class="page-subtitle mt-1">Monitoreo en vivo · Nodos LXC · Cluster</p>
    </div>
    <div class="flex items-center gap-2">
      <button class="btn btn-secondary btn-sm" on:click={refreshAllLive}>
        <Activity size={13} />
        Live refresh
      </button>
      <button class="btn btn-secondary btn-sm" on:click={loadData} disabled={loading}>
        <RefreshCw size={13} class={loading ? 'animate-spin' : ''} />
        Recargar
      </button>
    </div>
  </div>

  {#if loading}
    <div class="py-24 flex justify-center">
      <div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin"></div>
    </div>
  {:else}

    <!-- ── LIVE NODE CARDS ────────────────────────────── -->
    <div>
      <div class="flex items-center gap-2 mb-4">
        <Server size={15} class="text-gray-400" />
        <h2 class="section-heading">Monitoreo en vivo</h2>
        <span class="text-[11px] text-gray-400 bg-gray-100 rounded-full px-2 py-0.5">Actualiza cada 30s</span>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {#each nodes as node (node.id)}
          {@const live = liveStats[node.id]}
          {@const isLoading = liveLoading[node.id]}
          {@const online = live?.online ?? false}
          {@const cpuPct  = live?.cpu?.usage_percent  ?? 0}
          {@const ramPct  = live?.ram?.usage_percent  ?? 0}
          {@const diskPct = live?.disk?.usage_percent ?? 0}
          <div class="card p-5 flex flex-col gap-3 {online ? 'border-green-200' : 'border-red-200 opacity-75'}">
            <!-- Node header -->
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <div class="flex items-center gap-1.5">
                  {#if node.is_database_node}
                    <Database size={13} class="text-blue-500 flex-shrink-0" />
                  {:else}
                    <Server size={13} class="text-gray-400 flex-shrink-0" />
                  {/if}
                  <span class="font-jakarta font-bold text-sm text-text-primary truncate">{node.name}</span>
                </div>
                <span class="text-[11px] font-mono text-gray-400">{node.hostname}</span>
                {#if live?.uptime}
                  <p class="text-[10px] text-gray-400 mt-0.5 truncate">{live.uptime}</p>
                {/if}
              </div>
              <div class="flex-shrink-0 flex flex-col items-end gap-1">
                {#if isLoading}
                  <div class="w-5 h-5 border border-gray-300 border-t-transparent rounded-full animate-spin"></div>
                {:else if online}
                  <Wifi size={14} class="text-green-500" />
                {:else}
                  <WifiOff size={14} class="text-red-400" />
                {/if}
                {#if node.is_database_node}
                  <span class="text-[10px] font-semibold text-blue-600 bg-blue-50 rounded px-1.5 py-0.5">DB</span>
                {/if}
              </div>
            </div>

            {#if online && live}
              <!-- Gauge rings row -->
              <div class="flex justify-around items-center py-1">
                {#each [
                  { label: 'CPU', pct: cpuPct, sub: `${cpuPct.toFixed(0)}%` },
                  { label: 'RAM', pct: ramPct, sub: `${fmtMb(live.ram.used_mb)}` },
                  { label: 'Disk', pct: diskPct, sub: `${live.disk.used_gb}G / ${live.disk.total_gb}G` },
                ] as g}
                  <div class="flex flex-col items-center gap-1">
                    <svg width="48" height="48" viewBox="0 0 48 48">
                      <circle cx="24" cy="24" r="18" fill="none" stroke="#e5e7eb" stroke-width="5"/>
                      <circle
                        cx="24" cy="24" r="18" fill="none"
                        stroke={usageRingColor(g.pct)}
                        stroke-width="5"
                        stroke-linecap="round"
                        stroke-dasharray="{2 * Math.PI * 18}"
                        stroke-dashoffset="{ringDashoffset(g.pct)}"
                        transform="rotate(-90 24 24)"
                        style="transition: stroke-dashoffset 0.6s ease"
                      />
                      <text x="24" y="28" text-anchor="middle" font-size="9" font-weight="bold" fill="#374151">
                        {g.pct.toFixed(0)}%
                      </text>
                    </svg>
                    <span class="text-[10px] font-semibold text-gray-500">{g.label}</span>
                    <span class="text-[10px] text-gray-400 max-w-[56px] text-center leading-tight">{g.sub}</span>
                  </div>
                {/each}
              </div>

              <!-- Load avg + cores -->
              <div class="flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-gray-500 bg-gray-50 rounded-lg px-3 py-2">
                <span><span class="font-semibold text-gray-700">{live.cpu.cores}</span> cores</span>
                {#if live.cpu.load_avg}
                  <span>Load <span class="font-semibold text-gray-700">{live.cpu.load_avg['1m']}</span> / {live.cpu.load_avg['5m']} / {live.cpu.load_avg['15m']}</span>
                {/if}
                <span>RAM free <span class="font-semibold text-gray-700">{fmtMb(live.ram.free_mb)}</span></span>
                <span>Disk free <span class="font-semibold text-gray-700">{live.disk.free_gb} GB</span></span>
              </div>

            {:else if !isLoading}
              <!-- Offline state -->
              <div class="flex items-center gap-2 py-4 justify-center">
                <WifiOff size={16} class="text-red-400" />
                <span class="text-sm text-red-400 font-medium">Sin respuesta SSH</span>
              </div>
              {#if live?.error}
                <p class="text-[11px] text-red-300 text-center font-mono truncate">{live.error}</p>
              {/if}
            {:else}
              <!-- Loading state -->
              <div class="flex items-center gap-2 py-4 justify-center">
                <div class="w-4 h-4 border border-gray-300 border-t-primary rounded-full animate-spin"></div>
                <span class="text-sm text-gray-400">Conectando...</span>
              </div>
            {/if}

            <!-- Footer: refresh button -->
            <button
              class="text-[11px] text-gray-400 hover:text-primary transition-colors flex items-center gap-1 self-end mt-auto"
              on:click={() => fetchLiveStats(node.id)}
              disabled={isLoading}
            >
              <RefreshCw size={10} class={isLoading ? 'animate-spin' : ''} />
              Actualizar
            </button>
          </div>
        {:else}
          <div class="col-span-4 py-16 text-center text-gray-400 text-sm">
            No hay nodos registrados
          </div>
        {/each}
      </div>
    </div>

    <!-- ── CLUSTER SUMMARY STATS ──────────────────────── -->
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
          <div class="h-full rounded-full {usageColor(summary?.resources.cpu.usage_percent ?? 0)} transition-all" style="width: {Math.min(100, summary?.resources.cpu.usage_percent ?? 0)}%"></div>
        </div>
      </div>
      <div class="stat-card">
        <span class="stat-label">RAM Promedio</span>
        <span class="stat-value">{formatPercent(summary?.resources.ram.usage_percent ?? 0)}</span>
        <div class="h-1.5 rounded-full bg-border-light overflow-hidden mt-1">
          <div class="h-full rounded-full {usageColor(summary?.resources.ram.usage_percent ?? 0)} transition-all" style="width: {Math.min(100, summary?.resources.ram.usage_percent ?? 0)}%"></div>
        </div>
        <span class="text-[11px] text-gray-500">{(summary?.resources.ram.used_gb ?? 0).toFixed(1)} / {(summary?.resources.ram.total_gb ?? 0).toFixed(1)} GB</span>
      </div>
    </div>

    <!-- ── NODES TABLE ────────────────────────────────── -->
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
              <th>IP / VMID</th>
              <th>Tipo</th>
              <th>Estado</th>
              <th>CPU%</th>
              <th>RAM%</th>
              <th>Disk%</th>
              <th>Últ. check</th>
            </tr>
          </thead>
          <tbody>
            {#each nodes as node (node.id)}
              {@const live = liveStats[node.id]}
              {@const cpuPct  = live?.online ? live.cpu.usage_percent  : node.resources.cpu.usage_percent}
              {@const ramPct  = live?.online ? live.ram.usage_percent  : node.resources.ram.usage_percent}
              {@const diskPct = live?.online ? live.disk.usage_percent : node.resources.storage.usage_percent}
              <tr>
                <td>
                  <div class="flex flex-col gap-0.5">
                    <span class="font-semibold text-text-primary">{node.name}</span>
                    <span class="text-[11px] text-gray-400">{node.region}</span>
                  </div>
                </td>
                <td class="font-mono text-[11px] text-text-secondary">{node.hostname}</td>
                <td>
                  {#if node.is_database_node}
                    <span class="badge badge-info">DB Node</span>
                  {:else}
                    <span class="badge badge-neutral">App Node</span>
                  {/if}
                </td>
                <td>
                  {#if live?.online === false}
                    <span class="badge badge-error">offline</span>
                  {:else}
                    <span class="badge {statusBadge(node.status)}">{node.status}</span>
                  {/if}
                </td>
                <td>
                  <div class="flex items-center gap-2 min-w-[72px]">
                    <div class="flex-1 h-1.5 rounded-full bg-border-light overflow-hidden">
                      <div class="h-full rounded-full {usageColor(cpuPct)} transition-all" style="width: {Math.min(100, cpuPct)}%"></div>
                    </div>
                    <span class="text-[11px] text-text-secondary w-8 text-right">{cpuPct.toFixed(0)}%</span>
                  </div>
                </td>
                <td>
                  <div class="flex items-center gap-2 min-w-[72px]">
                    <div class="flex-1 h-1.5 rounded-full bg-border-light overflow-hidden">
                      <div class="h-full rounded-full {usageColor(ramPct)} transition-all" style="width: {Math.min(100, ramPct)}%"></div>
                    </div>
                    <span class="text-[11px] text-text-secondary w-8 text-right">{ramPct.toFixed(0)}%</span>
                  </div>
                </td>
                <td>
                  <div class="flex items-center gap-2 min-w-[72px]">
                    <div class="flex-1 h-1.5 rounded-full bg-border-light overflow-hidden">
                      <div class="h-full rounded-full {usageColor(diskPct)} transition-all" style="width: {Math.min(100, diskPct)}%"></div>
                    </div>
                    <span class="text-[11px] text-text-secondary w-8 text-right">{diskPct.toFixed(0)}%</span>
                  </div>
                </td>
                <td class="text-[11px] text-gray-400">
                  {#if node.last_health_check}
                    {new Date(node.last_health_check).toLocaleTimeString('es-DO', {hour:'2-digit',minute:'2-digit'})}
                  {:else}—{/if}
                </td>
              </tr>
            {:else}
              <tr>
                <td colspan="8" class="text-center text-gray-500 py-12 text-sm">No hay nodos disponibles</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── NODE CREATE / CLONE ────────────────────────── -->
    <div class="card p-6 space-y-4">
      <div class="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h2 class="section-heading">Registrar nodo</h2>
          <p class="text-xs text-gray-500 mt-1">Agrega nodos nuevos al cluster o clona la configuración de un nodo existente.</p>
        </div>
        <div class="flex items-center gap-2">
          <button class="btn btn-sm {createMode === 'new' ? 'btn-primary' : 'btn-secondary'}" on:click={() => (createMode = 'new')} type="button">
            <Plus size={12} /> Nuevo nodo
          </button>
          <button class="btn btn-sm {createMode === 'clone' ? 'btn-primary' : 'btn-secondary'}" on:click={() => (createMode = 'clone')} type="button">
            <Copy size={12} /> Clonar template
          </button>
        </div>
      </div>

      {#if createMode === 'clone'}
        <div>
          <label class="label">Template base</label>
          <select class="input" bind:value={cloneFromNodeId} on:change={(e) => applyCloneTemplate(Number((e.currentTarget as HTMLSelectElement).value) || null)}>
            <option value="">Selecciona un nodo existente...</option>
            {#each nodes as n}
              <option value={n.id}>{n.name} ({n.hostname})</option>
            {/each}
          </select>
        </div>
      {/if}

      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div><label class="label">Nombre</label><input class="input" type="text" bind:value={nodeForm.name} placeholder="pve-node-03" /></div>
        <div><label class="label">IP / Hostname</label><input class="input" type="text" bind:value={nodeForm.hostname} placeholder="10.10.10.150" /></div>
        <div><label class="label">Región</label><input class="input" type="text" bind:value={nodeForm.region} placeholder="do-sto-domingo" /></div>
        <div><label class="label">CPU Cores</label><input class="input" type="number" min="1" bind:value={nodeForm.total_cpu_cores} /></div>
        <div><label class="label">RAM (GB)</label><input class="input" type="number" min="1" step="0.5" bind:value={nodeForm.total_ram_gb} /></div>
        <div><label class="label">Storage (GB)</label><input class="input" type="number" min="10" bind:value={nodeForm.total_storage_gb} /></div>
        <div><label class="label">Max containers</label><input class="input" type="number" min="1" bind:value={nodeForm.max_containers} /></div>
        <div><label class="label">SSH user</label><input class="input" type="text" bind:value={nodeForm.ssh_user} /></div>
        <div><label class="label">API token ID (opcional)</label><input class="input" type="text" bind:value={nodeForm.api_token_id} placeholder="root@pam!erp-core" /></div>
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
            <Plus size={12} /> Registrar nodo
          {/if}
        </button>
      </div>
    </div>

    <!-- ── CONTAINERS TABLE ───────────────────────────── -->
    <div class="card p-0 overflow-hidden">
      <button class="w-full flex items-center justify-between px-6 py-4 border-b border-border-light hover:bg-bg-card/50 transition-colors" on:click={() => showContainers = !showContainers}>
        <div class="flex items-center gap-2">
          <span class="section-heading">Todos los Containers</span>
          <span class="badge badge-neutral">{containers.length}</span>
        </div>
        {#if showContainers}<ChevronUp size={16} class="text-gray-400" />{:else}<ChevronDown size={16} class="text-gray-400" />{/if}
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
                  <td><span class="badge {containerStatusBadge(ct.status)}">{ct.status}</span></td>
                  <td class="font-mono text-[11px] text-text-secondary">{ct.ip || '-'}</td>
                  <td class="text-text-secondary text-sm">{ct.usage.ram_mb > 0 ? ct.usage.ram_mb.toFixed(0) : ct.resources.ram_mb}</td>
                  <td class="text-text-secondary text-sm">{ct.usage.disk_gb > 0 ? ct.usage.disk_gb.toFixed(1) : ct.resources.disk_gb}</td>
                </tr>
              {:else}
                <tr><td colspan="7" class="text-center text-gray-500 py-8 text-sm">No hay containers disponibles</td></tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </div>

  {/if}
</div>

