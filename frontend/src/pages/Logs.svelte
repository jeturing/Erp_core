<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { Badge, Button, Card, Spinner } from '../lib/components';
  import { logsApi } from '../lib/api';
  import type { LogEntry, SystemStatusResponse } from '../lib/types';

  type LogsTab = 'provisioning' | 'system';

  let activeTab: LogsTab = 'provisioning';
  let loading = true;
  let error = '';
  let lines = 100;
  let level = '';
  let autoRefresh = false;

  let provisioningLogs: LogEntry[] = [];
  let systemLogs: LogEntry[] = [];
  let status: SystemStatusResponse | null = null;

  let refreshInterval: number | null = null;

  function statusVariant(value: string) {
    if (['healthy', 'running', 'active'].includes(value)) return 'success';
    if (['warning', 'unknown'].includes(value)) return 'warning';
    if (['error', 'stopped'].includes(value)) return 'error';
    return 'secondary';
  }

  function cleanupRefresh() {
    if (refreshInterval) {
      clearInterval(refreshInterval);
      refreshInterval = null;
    }
  }

  function configureRefresh() {
    cleanupRefresh();
    if (!autoRefresh) return;
    refreshInterval = window.setInterval(() => {
      loadData(true);
    }, 8000);
  }

  async function loadData(silent = false) {
    if (!silent) {
      loading = true;
      error = '';
    }

    try {
      const statusPromise = logsApi.getSystemStatus();
      if (activeTab === 'provisioning') {
        const result = await logsApi.getProvisioningLogs(lines, level || undefined);
        provisioningLogs = result.logs || [];
      } else {
        const result = await logsApi.getSystemLogs(lines);
        systemLogs = result.logs || [];
      }
      status = await statusPromise;
    } catch (err) {
      error = err instanceof Error ? err.message : 'No se pudieron cargar logs';
    } finally {
      loading = false;
    }
  }

  function switchTab(tab: LogsTab) {
    if (activeTab === tab) return;
    activeTab = tab;
    loadData();
  }

  $: configureRefresh();

  onMount(loadData);
  onDestroy(cleanupRefresh);
</script>

<div class="p-6 lg:p-8 space-y-6">
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold text-white">Logs</h1>
      <p class="text-secondary-400 mt-1">Provisioning, sistema y estado operativo</p>
    </div>
    <div class="flex items-center gap-2">
      <Button variant="secondary" on:click={() => loadData()}>Actualizar</Button>
      <Button variant={autoRefresh ? 'accent' : 'ghost'} on:click={() => (autoRefresh = !autoRefresh)}>
        {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
      </Button>
    </div>
  </div>

  {#if error}
    <Card><p class="text-sm text-error">{error}</p></Card>
  {/if}

  <div class="grid grid-cols-1 lg:grid-cols-4 gap-4">
    <Card>
      <p class="text-xs uppercase tracking-wider text-secondary-500">PostgreSQL</p>
      <div class="mt-2">
        <Badge variant={statusVariant(status?.postgresql.status || 'unknown')}>{status?.postgresql.status || 'unknown'}</Badge>
      </div>
      {#if status?.postgresql.latency_ms !== undefined}
        <p class="text-xs text-secondary-400 mt-2">Latencia: {status.postgresql.latency_ms} ms</p>
      {/if}
    </Card>

    <Card>
      <p class="text-xs uppercase tracking-wider text-secondary-500">FastAPI</p>
      <div class="mt-2">
        <Badge variant={statusVariant(status?.fastapi.status || 'unknown')}>{status?.fastapi.status || 'unknown'}</Badge>
      </div>
      <p class="text-xs text-secondary-400 mt-2">Puerto: {status?.fastapi.port || '-'}</p>
    </Card>

    <Card>
      <p class="text-xs uppercase tracking-wider text-secondary-500">LXC</p>
      <div class="mt-2">
        <Badge variant={statusVariant(status?.lxc_105.status || 'unknown')}>{status?.lxc_105.status || 'unknown'}</Badge>
      </div>
      <p class="text-xs text-secondary-400 mt-2">{status?.lxc_105.name || 'Container'}</p>
    </Card>

    <Card>
      <p class="text-xs uppercase tracking-wider text-secondary-500">Disco /</p>
      <p class="mt-2 text-2xl font-bold text-white">{status?.disk.usage_percent || 0}%</p>
      <p class="text-xs text-secondary-400 mt-2">Libre: {status?.disk.free_gb || 0} GB</p>
    </Card>
  </div>

  <Card title="Visor de logs" subtitle="/api/logs/*" padding="none">
    <div class="border-b border-surface-border px-4 py-3 flex flex-wrap items-center gap-2">
      <Button variant={activeTab === 'provisioning' ? 'primary' : 'ghost'} size="sm" on:click={() => switchTab('provisioning')}>
        Provisioning
      </Button>
      <Button variant={activeTab === 'system' ? 'primary' : 'ghost'} size="sm" on:click={() => switchTab('system')}>
        System
      </Button>

      <div class="ml-auto flex flex-wrap gap-2 items-center">
        <label class="text-xs text-secondary-400" for="lines-select">Lineas</label>
        <select id="lines-select" bind:value={lines} class="input w-auto min-w-24" on:change={() => loadData()}>
          <option value={50}>50</option>
          <option value={100}>100</option>
          <option value={200}>200</option>
        </select>

        {#if activeTab === 'provisioning'}
          <label class="text-xs text-secondary-400" for="level-select">Nivel</label>
          <select id="level-select" bind:value={level} class="input w-auto min-w-28" on:change={() => loadData()}>
            <option value="">Todos</option>
            <option value="info">Info</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
            <option value="debug">Debug</option>
          </select>
        {/if}
      </div>
    </div>

    {#if loading}
      <div class="py-12 flex justify-center"><Spinner size="lg" /></div>
    {:else}
      <div class="max-h-[560px] overflow-auto p-4 bg-surface-dark">
        {#if activeTab === 'provisioning'}
          {#each provisioningLogs as entry}
            <p class={`font-mono text-xs leading-relaxed ${entry.class}`}>{entry.line}</p>
          {:else}
            <p class="text-sm text-secondary-500 py-8 text-center">Sin logs de provisioning</p>
          {/each}
        {:else}
          {#each systemLogs as entry}
            <p class={`font-mono text-xs leading-relaxed ${entry.class}`}>{entry.line}</p>
          {:else}
            <p class="text-sm text-secondary-500 py-8 text-center">Sin logs de sistema</p>
          {/each}
        {/if}
      </div>
    {/if}
  </Card>
</div>
