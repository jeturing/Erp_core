<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { logsApi } from '../lib/api';
  import { toasts } from '../lib/stores/toast';
  import { RefreshCw } from 'lucide-svelte';
  import type { SystemStatus, LogEntry } from '../lib/api/logs';



  type LogTab = 'provisioning' | 'app' | 'sistema';

  let activeTab = $state<LogTab>('provisioning');
  let logs = $state<LogEntry[]>([]);
  let logsLoading = $state(false);
  let lineCount = $state(100);
  let levelFilter = $state('');
  let autoRefresh = $state(false);
  let systemStatus = $state<SystemStatus | null>(null);
  let statusLoading = $state(false);
  let refreshInterval: ReturnType<typeof setInterval> | null = null;
  let logContainer: HTMLDivElement;

  async function loadLogs() {
    logsLoading = true;
    try {
      let data: { logs: LogEntry[]; total: number; file?: string };
      if (activeTab === 'provisioning') {
        data = await logsApi.getProvisioningLogs(lineCount, levelFilter || undefined);
      } else if (activeTab === 'app') {
        data = await logsApi.getAppLogs(lineCount, levelFilter || undefined);
      } else {
        data = await logsApi.getSystemLogs(lineCount);
      }
      logs = data.logs ?? [];
      // Auto-scroll to bottom
      setTimeout(() => {
        if (logContainer) logContainer.scrollTop = logContainer.scrollHeight;
      }, 50);
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al cargar logs');
    } finally {
      logsLoading = false;
    }
  }

  async function loadStatus() {
    statusLoading = true;
    try {
      systemStatus = await logsApi.getSystemStatus();
    } catch (e: any) {
      // silently fail
    } finally {
      statusLoading = false;
    }
  }

  function toggleAutoRefresh() {
    autoRefresh = !autoRefresh;
    if (autoRefresh) {
      refreshInterval = setInterval(loadLogs, 10000);
    } else {
      if (refreshInterval) clearInterval(refreshInterval);
      refreshInterval = null;
    }
  }

  function switchTab(tab: LogTab) {
    activeTab = tab;
    logs = [];
    loadLogs();
  }

  function statusColor(status: string | undefined): string {
    if (!status) return 'bg-gray-400';
    const s = status.toLowerCase();
    if (s === 'ok' || s === 'healthy' || s === 'running') return 'bg-emerald-400';
    if (s === 'unknown') return 'bg-yellow-400';
    return 'bg-rose-400';
  }

  function lineClass(cls: string | undefined): string {
    if (!cls) return 'text-slate-400';
    return cls;
  }

  onMount(() => {
    loadLogs();
    loadStatus();
  });

  onDestroy(() => {
    if (refreshInterval) clearInterval(refreshInterval);
  });
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between flex-wrap gap-3">
    <div>
      <h1 class="page-title">LOGS DEL SISTEMA</h1>
      <p class="page-subtitle">Monitoreo y diagnóstico</p>
    </div>
    <div class="flex items-center gap-3 flex-wrap">
      <div>
        <select class="input px-3 py-2 text-sm" bind:value={lineCount} onchange={loadLogs}>
          <option value={50}>50 líneas</option>
          <option value={100}>100 líneas</option>
          <option value={200}>200 líneas</option>
          <option value={500}>500 líneas</option>
        </select>
      </div>
      {#if activeTab !== 'sistema'}
        <div>
          <select class="input px-3 py-2 text-sm" bind:value={levelFilter} onchange={loadLogs}>
            <option value="">Todos</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
          </select>
        </div>
      {/if}
      <button
        class="btn-sm {autoRefresh ? 'btn-accent' : 'btn-secondary'} px-3 py-2"
        onclick={toggleAutoRefresh}
      >
        AUTO {autoRefresh ? 'ON' : 'OFF'}
      </button>
      <button class="btn-secondary btn-sm px-3 py-2 flex items-center gap-1.5" onclick={loadLogs} disabled={logsLoading}>
        <RefreshCw size={13} class={logsLoading ? 'animate-spin' : ''} />
        ACTUALIZAR
      </button>
    </div>
  </div>

  <!-- Content -->
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- Logs panel (2/3) -->
    <div class="lg:col-span-2 space-y-4">
      <!-- Tabs -->
      <div class="flex gap-1 bg-bg-card border border-border-light p-1 w-fit">
        {#each [['provisioning', 'PROVISIONING'], ['app', 'APP'], ['sistema', 'SISTEMA']] as [tab, label]}
          <button
            type="button"
            class="px-4 py-1.5 text-[11px] uppercase tracking-[0.08em] font-semibold transition-colors {activeTab === tab ? 'bg-charcoal text-white' : 'text-gray-500 hover:text-text-primary'}"
            onclick={() => switchTab(tab as LogTab)}
          >
            {label}
          </button>
        {/each}
      </div>

      <!-- Log area -->
      <div
        bind:this={logContainer}
        class="bg-[#1a1a1a] overflow-y-auto font-mono text-xs leading-5 p-4"
        style="height:500px"
      >
        {#if logsLoading && logs.length === 0}
          <span class="text-slate-500">Cargando logs...</span>
        {:else if logs.length === 0}
          <span class="text-slate-500">Sin logs disponibles</span>
        {:else}
          {#each logs as entry, i (i)}
            <div class="{lineClass(entry.class)} whitespace-pre-wrap break-all">{entry.line}</div>
          {/each}
        {/if}
      </div>
    </div>

    <!-- System Status sidebar (1/3) -->
    <div class="space-y-4">
      <div class="card">
        <h3 class="section-heading mb-4">ESTADO DEL SISTEMA</h3>
        {#if statusLoading}
          <p class="text-sm text-gray-500">Cargando...</p>
        {:else}
          <div class="space-y-3">
            <!-- PostgreSQL -->
            <div class="flex items-start justify-between">
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full mt-0.5 {statusColor(systemStatus?.postgresql?.status)}"></div>
                <div>
                  <div class="text-xs font-semibold text-text-primary uppercase tracking-wide">PostgreSQL</div>
                  <div class="text-[11px] text-gray-500">{systemStatus?.postgresql?.status ?? 'unknown'}</div>
                </div>
              </div>
              {#if systemStatus?.postgresql?.latency_ms != null}
                <span class="text-[11px] text-gray-400">{systemStatus.postgresql.latency_ms}ms</span>
              {/if}
            </div>

            <!-- FastAPI -->
            <div class="flex items-start justify-between">
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full mt-0.5 {statusColor(systemStatus?.fastapi?.status)}"></div>
                <div>
                  <div class="text-xs font-semibold text-text-primary uppercase tracking-wide">FastAPI</div>
                  <div class="text-[11px] text-gray-500">{systemStatus?.fastapi?.status ?? 'unknown'}</div>
                </div>
              </div>
              {#if systemStatus?.fastapi?.port != null}
                <span class="text-[11px] text-gray-400">:{systemStatus.fastapi.port}</span>
              {/if}
            </div>

            <!-- LXC 105 -->
            <div class="flex items-start justify-between">
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full mt-0.5 {statusColor(systemStatus?.lxc_105?.status)}"></div>
                <div>
                  <div class="text-xs font-semibold text-text-primary uppercase tracking-wide">LXC 105</div>
                  <div class="text-[11px] text-gray-500">{systemStatus?.lxc_105?.status ?? 'unknown'}</div>
                </div>
              </div>
              {#if systemStatus?.lxc_105?.name}
                <span class="text-[11px] text-gray-400">{systemStatus.lxc_105.name}</span>
              {/if}
            </div>

            <!-- Disk -->
            <div class="flex items-start justify-between">
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full mt-0.5 {
                  systemStatus?.disk?.usage_percent != null
                    ? systemStatus.disk.usage_percent > 85 ? 'bg-rose-400' : systemStatus.disk.usage_percent > 70 ? 'bg-yellow-400' : 'bg-emerald-400'
                    : 'bg-gray-400'
                }"></div>
                <div>
                  <div class="text-xs font-semibold text-text-primary uppercase tracking-wide">Disco</div>
                  {#if systemStatus?.disk?.usage_percent != null}
                    <div class="text-[11px] text-gray-500">{systemStatus.disk.usage_percent}% usado</div>
                  {:else}
                    <div class="text-[11px] text-gray-500">unknown</div>
                  {/if}
                </div>
              </div>
              {#if systemStatus?.disk?.free_gb != null}
                <span class="text-[11px] text-gray-400">{systemStatus.disk.free_gb}GB libres</span>
              {/if}
            </div>
          </div>
        {/if}

        <button class="btn-secondary btn-sm w-full mt-4 flex items-center justify-center gap-1.5" onclick={loadStatus} disabled={statusLoading}>
          <RefreshCw size={12} class={statusLoading ? 'animate-spin' : ''} />
          ACTUALIZAR ESTADO
        </button>
      </div>
    </div>
  </div>
</div>
