<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { RefreshCw, Activity, Server, Database, Wifi } from 'lucide-svelte';
  import { logsApi } from '../lib/api/logs';
  import type { LogEntry, SystemStatus } from '../lib/api/logs';
  import { toasts } from '../lib/stores/toast';

  type LogTab = 'provisioning' | 'app' | 'system';

  let activeTab: LogTab = 'provisioning';
  let lines: number = 100;
  let level: string = '';
  let logs: LogEntry[] = [];
  let status: SystemStatus | null = null;
  let loading = false;
  let statusLoading = false;
  let autoRefresh = false;
  let autoRefreshInterval: ReturnType<typeof setInterval> | null = null;
  let logFile: string | undefined;

  const lineCounts = [50, 100, 200, 500];
  const levels = [
    { value: '', label: 'Todos' },
    { value: 'INFO', label: 'INFO' },
    { value: 'WARNING', label: 'WARNING' },
    { value: 'ERROR', label: 'ERROR' },
  ];

  async function loadLogs() {
    loading = true;
    try {
      let response;
      if (activeTab === 'provisioning') {
        response = await logsApi.getProvisioningLogs(lines, level || undefined);
      } else if (activeTab === 'app') {
        response = await logsApi.getAppLogs(lines, level || undefined);
      } else {
        response = await logsApi.getSystemLogs(lines);
      }
      logs = response.logs || [];
      logFile = response.file;
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error al cargar logs');
      logs = [];
    } finally {
      loading = false;
    }
  }

  async function loadStatus() {
    statusLoading = true;
    try {
      status = await logsApi.getSystemStatus();
    } catch {
      // status panel best-effort
    } finally {
      statusLoading = false;
    }
  }

  function toggleAutoRefresh() {
    autoRefresh = !autoRefresh;
    if (autoRefresh) {
      autoRefreshInterval = setInterval(loadLogs, 10000);
      toasts.info('Auto-refresh activado (cada 10s)');
    } else {
      if (autoRefreshInterval) clearInterval(autoRefreshInterval);
      autoRefreshInterval = null;
      toasts.info('Auto-refresh desactivado');
    }
  }

  function switchTab(tab: LogTab) {
    activeTab = tab;
    logs = [];
    loadLogs();
  }

  function getLineClass(cls: string): string {
    if (cls === 'text-emerald-400') return 'text-emerald-400';
    if (cls === 'text-amber-400') return 'text-amber-400';
    if (cls === 'text-rose-400') return 'text-rose-400';
    return 'text-slate-400';
  }

  function statusDot(s: string): string {
    if (s === 'running' || s === 'ok' || s === 'healthy') return 'bg-green-500';
    if (s === 'degraded' || s === 'slow') return 'bg-yellow-500';
    return 'bg-red-500';
  }

  onMount(() => {
    loadLogs();
    loadStatus();
  });

  onDestroy(() => {
    if (autoRefreshInterval) clearInterval(autoRefreshInterval);
  });
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="page-title">LOGS DEL SISTEMA</h1>
      <p class="page-subtitle mt-1">
        {#if logFile}Archivo: <span class="font-mono text-xs">{logFile}</span>{:else}Monitoreo de logs en tiempo real{/if}
      </p>
    </div>
    <div class="flex items-center gap-2">
      <button
        class="btn btn-sm {autoRefresh ? 'btn-accent' : 'btn-secondary'}"
        on:click={toggleAutoRefresh}
      >
        <Activity class="w-3.5 h-3.5 mr-1 inline" />
        {autoRefresh ? 'AUTO ON' : 'AUTO OFF'}
      </button>
      <button class="btn btn-secondary btn-sm" on:click={loadLogs} disabled={loading}>
        <RefreshCw class="w-3.5 h-3.5 mr-1 inline {loading ? 'animate-spin' : ''}" />
        ACTUALIZAR
      </button>
    </div>
  </div>

  <div class="flex gap-6">
    <!-- Main log area -->
    <div class="flex-1 min-w-0 space-y-4">
      <!-- Controls -->
      <div class="card p-4 flex flex-wrap items-center gap-4">
        <!-- Tab switcher -->
        <div class="flex bg-bg-page rounded border border-border-light p-0.5 gap-0.5">
          {#each ([['provisioning','Provisioning'],['app','App'],['system','Sistema']] as const) as [tab, label]}
            <button
              class="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.08em] rounded transition-colors
                {activeTab === tab ? 'bg-charcoal text-white' : 'text-text-secondary hover:text-text-primary'}"
              on:click={() => switchTab(tab)}
            >
              {label}
            </button>
          {/each}
        </div>

        <!-- Line count -->
        <div class="flex items-center gap-1.5">
          <span class="label text-[10px]">Líneas:</span>
          <div class="flex gap-0.5">
            {#each lineCounts as count}
              <button
                class="px-2 py-1 text-[10px] font-semibold rounded border transition-colors
                  {lines === count
                    ? 'bg-charcoal text-white border-charcoal'
                    : 'bg-bg-card text-text-secondary border-border-light hover:border-charcoal'}"
                on:click={() => { lines = count; loadLogs(); }}
              >
                {count}
              </button>
            {/each}
          </div>
        </div>

        <!-- Level filter (not for system tab) -->
        {#if activeTab !== 'system'}
          <div class="flex items-center gap-1.5">
            <span class="label text-[10px]">Nivel:</span>
            <div class="flex gap-0.5">
              {#each levels as lvl}
                <button
                  class="px-2 py-1 text-[10px] font-semibold rounded border transition-colors
                    {level === lvl.value
                      ? 'bg-charcoal text-white border-charcoal'
                      : 'bg-bg-card text-text-secondary border-border-light hover:border-charcoal'}"
                  on:click={() => { level = lvl.value; loadLogs(); }}
                >
                  {lvl.label}
                </button>
              {/each}
            </div>
          </div>
        {/if}

        <span class="ml-auto text-[10px] text-gray-500">{logs.length} líneas</span>
      </div>

      <!-- Log viewer -->
      <div class="card p-0 overflow-hidden">
        <div
          class="h-[560px] overflow-y-auto bg-[#0d1117] rounded p-4 font-mono text-[11px] leading-relaxed"
        >
          {#if loading}
            <div class="flex items-center justify-center h-full">
              <div class="text-slate-400 text-xs animate-pulse">Cargando logs...</div>
            </div>
          {:else if logs.length === 0}
            <div class="flex items-center justify-center h-full">
              <p class="text-slate-500 text-xs">No hay logs disponibles</p>
            </div>
          {:else}
            {#each logs as entry}
              <div class="whitespace-pre-wrap break-all leading-5 hover:bg-white/5 px-1 rounded {getLineClass(entry.class)}">
                {entry.line}
              </div>
            {/each}
          {/if}
        </div>
      </div>
    </div>

    <!-- System status sidebar -->
    <div class="w-64 flex-shrink-0 space-y-4">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <span class="section-heading">Estado del Sistema</span>
          <button
            class="btn-ghost p-1 rounded"
            on:click={loadStatus}
            title="Actualizar estado"
          >
            <RefreshCw class="w-3.5 h-3.5 {statusLoading ? 'animate-spin' : ''}" />
          </button>
        </div>

        {#if status}
          <div class="space-y-3">
            <!-- PostgreSQL -->
            <div class="flex items-center justify-between py-2 border-b border-border-light">
              <div class="flex items-center gap-2">
                <Database class="w-3.5 h-3.5 text-gray-500" />
                <span class="text-xs font-medium text-text-primary">PostgreSQL</span>
              </div>
              <div class="flex items-center gap-1.5">
                <div class="w-2 h-2 rounded-full {statusDot(status.postgresql.status)}"></div>
                <span class="text-[10px] text-text-secondary capitalize">{status.postgresql.status}</span>
              </div>
            </div>
            {#if status.postgresql.latency_ms != null}
              <div class="text-[10px] text-gray-500 -mt-2 pb-2 border-b border-border-light">
                Latencia: {status.postgresql.latency_ms}ms
              </div>
            {/if}

            <!-- FastAPI -->
            <div class="flex items-center justify-between py-2 border-b border-border-light">
              <div class="flex items-center gap-2">
                <Wifi class="w-3.5 h-3.5 text-gray-500" />
                <span class="text-xs font-medium text-text-primary">FastAPI</span>
              </div>
              <div class="flex items-center gap-1.5">
                <div class="w-2 h-2 rounded-full {statusDot(status.fastapi.status)}"></div>
                <span class="text-[10px] text-text-secondary capitalize">{status.fastapi.status}</span>
              </div>
            </div>
            <div class="text-[10px] text-gray-500 -mt-2 pb-2 border-b border-border-light">
              Puerto: {status.fastapi.port}
            </div>

            <!-- LXC -->
            <div class="flex items-center justify-between py-2 border-b border-border-light">
              <div class="flex items-center gap-2">
                <Server class="w-3.5 h-3.5 text-gray-500" />
                <span class="text-xs font-medium text-text-primary">LXC 105</span>
              </div>
              <div class="flex items-center gap-1.5">
                <div class="w-2 h-2 rounded-full {statusDot(status.lxc_105.status)}"></div>
                <span class="text-[10px] text-text-secondary capitalize">{status.lxc_105.status}</span>
              </div>
            </div>
            <div class="text-[10px] text-gray-500 -mt-2 pb-2 border-b border-border-light">
              {status.lxc_105.name}
            </div>

            <!-- Disk -->
            <div class="py-2">
              <div class="flex items-center justify-between mb-1.5">
                <span class="text-xs font-medium text-text-primary">Disco</span>
                <span class="text-[10px] text-text-secondary">{status.disk.usage_percent}%</span>
              </div>
              <div class="w-full bg-bg-page rounded-full h-1.5">
                <div
                  class="h-1.5 rounded-full transition-all
                    {status.disk.usage_percent > 80
                      ? 'bg-red-500'
                      : status.disk.usage_percent > 60
                      ? 'bg-yellow-500'
                      : 'bg-green-500'}"
                  style="width: {status.disk.usage_percent}%"
                ></div>
              </div>
              <p class="text-[10px] text-gray-500 mt-1">{status.disk.free_gb} GB libres</p>
            </div>
          </div>
        {:else if statusLoading}
          <div class="py-4 text-center text-xs text-gray-500 animate-pulse">Cargando...</div>
        {:else}
          <div class="py-4 text-center text-xs text-gray-500">No disponible</div>
        {/if}
      </div>

      <!-- Legend -->
      <div class="card">
        <span class="section-heading block mb-3">Leyenda</span>
        <div class="space-y-1.5">
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-emerald-400"></div>
            <span class="text-[10px] text-text-secondary">INFO / OK</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-amber-400"></div>
            <span class="text-[10px] text-text-secondary">WARNING</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-rose-400"></div>
            <span class="text-[10px] text-text-secondary">ERROR</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-slate-400"></div>
            <span class="text-[10px] text-text-secondary">DEBUG / Sistema</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
