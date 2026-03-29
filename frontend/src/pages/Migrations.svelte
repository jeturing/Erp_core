<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { migrationApi } from '../lib/api/migration';
  import type { DedicatedStatsResponse } from '../lib/api/migration';
  import { infrastructureApi } from '../lib/api/infrastructure';
  import { tenantsApi } from '../lib/api';
  import type {
    Tenant, NodeSummary, MigrationJob, MigrationJobListItem,
    MigrationState, TenantDeploymentSummary,
  } from '../lib/types';
  import { toasts } from '../lib/stores/toast';
  import { formatDate } from '../lib/utils/formatters';
  import {
    RefreshCw, ArrowRightLeft, Server, AlertTriangle,
    CheckCircle, XCircle, Clock, Loader, Search, ChevronDown,
    Zap, Package,
  } from 'lucide-svelte';

  // ── State ──
  let tenants = $state<Tenant[]>([]);
  let nodes = $state<NodeSummary[]>([]);
  let jobs = $state<MigrationJobListItem[]>([]);
  let activeJob = $state<MigrationJob | null>(null);
  let loading = $state(true);
  let loadingJobs = $state(false);
  let migrating = $state(false);
  let cancelling = $state(false);

  // Dedicated service state
  let provisioning = $state(false);
  let deprovisioning = $state(false);
  let dedicatedStats = $state<DedicatedStatsResponse['data'] | null>(null);
  let loadingStats = $state(false);

  // Filters & selection
  let searchQuery = $state('');
  let selectedSubdomain = $state('');
  let selectedTargetNodeId = $state<number | null>(null);
  let targetRuntimeMode = $state<'shared_pool' | 'dedicated_service'>('shared_pool');
  let jobsFilter = $state<string>('all');

  // Polling
  let pollTimer: ReturnType<typeof setInterval> | null = null;

  // ── Derived ──
  let migratableTenants = $derived(
    tenants.filter((t) => {
      const dep = t.deployment;
      return dep?.active_node_id != null && t.status === 'active';
    }),
  );

  let filteredTenants = $derived(
    migratableTenants.filter((t) => {
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      return (
        t.subdomain?.toLowerCase().includes(q) ||
        t.company_name?.toLowerCase().includes(q) ||
        t.email?.toLowerCase().includes(q)
      );
    }),
  );

  let selectedTenant = $derived(
    migratableTenants.find((t) => t.subdomain === selectedSubdomain) || null,
  );

  let eligibleTargets = $derived(
    selectedTenant?.deployment?.active_node_id != null
      ? nodes.filter(
          (n) =>
            n.can_host_tenants &&
            n.status === 'online' &&
            n.id !== selectedTenant!.deployment!.active_node_id,
        )
      : [],
  );

  let filteredJobs = $derived(
    jobsFilter === 'all'
      ? jobs
      : jobs.filter((j) => j.state === jobsFilter),
  );

  // ── Helpers ──
  const CANCELABLE: MigrationState[] = ['queued', 'preflight', 'preparing_target', 'warming_target'];
  const ACTIVE: MigrationState[] = ['queued', 'preflight', 'preparing_target', 'warming_target', 'cutover', 'verifying', 'rollback'];

  function stateColor(state: string): string {
    switch (state) {
      case 'completed': return 'text-green-400';
      case 'failed': return 'text-red-400';
      case 'rollback': return 'text-orange-400';
      case 'cutover': return 'text-yellow-300';
      case 'queued': return 'text-slate-400';
      default: return 'text-blue-400';
    }
  }

  function stateLabel(state: string): string {
    const labels: Record<string, string> = {
      idle: 'Inactivo',
      queued: 'En cola',
      preflight: 'Pre-vuelo',
      preparing_target: 'Preparando destino',
      warming_target: 'Calentando destino',
      cutover: 'Cortando tráfico',
      verifying: 'Verificando',
      rollback: 'Revirtiendo',
      completed: 'Completada',
      failed: 'Fallida',
    };
    return labels[state] || state;
  }

  function stateIcon(state: string) {
    switch (state) {
      case 'completed': return CheckCircle;
      case 'failed': return XCircle;
      case 'rollback': return AlertTriangle;
      case 'queued': return Clock;
      default: return Loader;
    }
  }

  // ── Data loading ──
  async function loadAll() {
    loading = true;
    try {
      const [tenantsRes, nodesRes, jobsRes] = await Promise.all([
        tenantsApi.list(),
        infrastructureApi.getNodes(),
        migrationApi.listJobs({ limit: 50 }),
      ]);
      tenants = tenantsRes.items ?? [];
      nodes = nodesRes.items ?? [];
      jobs = jobsRes.data ?? [];
    } catch (err: any) {
      toasts.error(`Error cargando datos: ${err.message}`);
    } finally {
      loading = false;
    }
  }

  async function loadJobs() {
    loadingJobs = true;
    try {
      const res = await migrationApi.listJobs({ limit: 50 });
      jobs = res.data ?? [];
    } catch (err: any) {
      toasts.error(`Error cargando jobs: ${err.message}`);
    } finally {
      loadingJobs = false;
    }
  }

  async function pollActiveJob() {
    if (!selectedSubdomain) return;
    try {
      const res = await migrationApi.getMigrationStatus(selectedSubdomain);
      activeJob = res.data;
      if (activeJob && !ACTIVE.includes(activeJob.state as MigrationState)) {
        // Migración terminada, recargar todo
        stopPolling();
        await loadAll();
        activeJob = null;
      }
    } catch {
      // silencioso en polling
    }
  }

  function startPolling() {
    stopPolling();
    pollTimer = setInterval(pollActiveJob, 5000);
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  // ── Actions ──
  async function handleStartMigration() {
    if (!selectedSubdomain || !selectedTargetNodeId) return;
    migrating = true;
    try {
      const res = await migrationApi.startMigration(selectedSubdomain, selectedTargetNodeId);
      if (res.success) {
        toasts.success(`Migración iniciada para ${selectedSubdomain}`);
        activeJob = res.data;
        startPolling();
        await loadJobs();
      }
    } catch (err: any) {
      toasts.error(`Error al iniciar: ${err.message}`);
    } finally {
      migrating = false;
    }
  }

  async function handleCancel() {
    if (!selectedSubdomain) return;
    cancelling = true;
    try {
      const res = await migrationApi.cancelMigration(selectedSubdomain, 'Cancelado por admin');
      if (res.success) {
        toasts.success('Migración cancelada');
        activeJob = null;
        stopPolling();
        await loadAll();
      }
    } catch (err: any) {
      toasts.error(`Error al cancelar: ${err.message}`);
    } finally {
      cancelling = false;
    }
  }

  // Check initial query param (from Tenants.svelte "Migrar" button)
  function checkInitialTenant() {
    const hash = window.location.hash;
    const match = hash.match(/[?&]tenant=([^&]+)/);
    if (match) {
      selectedSubdomain = decodeURIComponent(match[1]);
    }
  }

  onMount(async () => {
    checkInitialTenant();
    await loadAll();
    // If a tenant was pre-selected and has active migration, start polling
    if (selectedSubdomain) {
      try {
        const status = await migrationApi.getMigrationStatus(selectedSubdomain);
        if (status.data && ACTIVE.includes(status.data.state as MigrationState)) {
          activeJob = status.data;
          startPolling();
        }
      } catch { /* no active migration */ }
    }
  });

  onDestroy(stopPolling);
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="page-title">MIGRACIONES</h1>
      <p class="page-subtitle">Migración de tenants entre nodos del clúster</p>
    </div>
    <button class="btn-secondary px-4 py-2 flex items-center gap-2" onclick={loadAll} disabled={loading}>
      <RefreshCw size={14} class={loading ? 'animate-spin' : ''} />
      Recargar
    </button>
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-16">
      <Loader size={32} class="animate-spin text-slate-400" />
    </div>
  {:else}
    <!-- ═══ Panel: Iniciar migración ═══ -->
    <div class="card p-6 space-y-4">
      <h2 class="text-lg font-semibold text-white flex items-center gap-2">
        <ArrowRightLeft size={18} />
        Iniciar Migración
      </h2>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Tenant selector -->
        <div>
          <label for="tenant-select" class="block text-xs text-slate-400 mb-1 uppercase tracking-wider">Tenant</label>
          <div class="relative">
            <Search size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              bind:value={searchQuery}
              placeholder="Buscar tenant..."
              class="input-field pl-9 w-full"
            />
          </div>
          <select
            id="tenant-select"
            bind:value={selectedSubdomain}
            class="input-field w-full mt-2"
            onchange={() => { selectedTargetNodeId = null; activeJob = null; stopPolling(); }}
          >
            <option value="">— Seleccionar tenant —</option>
            {#each filteredTenants as t (t.subdomain)}
              <option value={t.subdomain}>
                {t.subdomain} ({t.company_name})
                {#if t.deployment?.active_node_name} — {t.deployment.active_node_name}{/if}
              </option>
            {/each}
          </select>
        </div>

        <!-- Current node info -->
        <div>
          <span class="block text-xs text-slate-400 mb-1 uppercase tracking-wider">Nodo Actual</span>
          {#if selectedTenant?.deployment}
            {@const dep = selectedTenant.deployment}
            <div class="bg-slate-800/50 rounded-lg p-3 border border-slate-700 space-y-1">
              <p class="text-sm text-white font-mono">{dep.active_node_name || '—'}</p>
              <p class="text-xs text-slate-400">
                Runtime: <span class="text-slate-300">{dep.runtime_mode || 'shared_pool'}</span>
              </p>
              <p class="text-xs text-slate-400">
                Estado: <span class={stateColor(dep.migration_state || 'idle')}>
                  {stateLabel(dep.migration_state || 'idle')}
                </span>
              </p>
              {#if dep.has_active_migration}
                <p class="text-xs text-yellow-400 flex items-center gap-1">
                  <AlertTriangle size={12} /> Migración activa
                </p>
              {/if}
            </div>
          {:else}
            <div class="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
              <p class="text-sm text-slate-500">Seleccione un tenant</p>
            </div>
          {/if}
        </div>

        <!-- Target node selector -->
        <div>
          <label for="target-node-select" class="block text-xs text-slate-400 mb-1 uppercase tracking-wider">Nodo Destino</label>
          <select
            id="target-node-select"
            bind:value={selectedTargetNodeId}
            class="input-field w-full"
            disabled={!selectedSubdomain || eligibleTargets.length === 0}
          >
            <option value={null}>— Seleccionar destino —</option>
            {#each eligibleTargets as node (node.id)}
              <option value={node.id}>
                {node.name} ({node.region}) — {node.available_slots} slots libres
              </option>
            {/each}
          </select>

          {#if selectedSubdomain && eligibleTargets.length === 0}
            <p class="text-xs text-orange-400 mt-1">No hay nodos elegibles disponibles</p>
          {/if}

          <!-- dedicated_service notice -->
          <div class="mt-3 bg-slate-800/40 rounded p-2 border border-slate-700/50">
            <p class="text-xs text-slate-500 italic">
              ⚠ Modo <code>dedicated_service</code> pendiente de backend — solo <code>shared_pool</code> disponible.
            </p>
          </div>
        </div>
      </div>

      <!-- Action buttons -->
      <div class="flex items-center gap-3 pt-2">
        <button
          class="btn-accent px-5 py-2 flex items-center gap-2"
          onclick={handleStartMigration}
          disabled={!selectedSubdomain || !selectedTargetNodeId || migrating || selectedTenant?.deployment?.has_active_migration}
        >
          {#if migrating}
            <Loader size={14} class="animate-spin" />
          {:else}
            <ArrowRightLeft size={14} />
          {/if}
          Iniciar Migración
        </button>

        {#if activeJob && CANCELABLE.includes(activeJob.state as MigrationState)}
          <button
            class="btn-secondary px-4 py-2 flex items-center gap-2 text-red-400 border-red-500/30 hover:bg-red-900/20"
            onclick={handleCancel}
            disabled={cancelling}
          >
            {#if cancelling}
              <Loader size={14} class="animate-spin" />
            {:else}
              <XCircle size={14} />
            {/if}
            Cancelar Migración
          </button>
        {/if}
      </div>
    </div>

    <!-- ═══ Panel: Job activo ═══ -->
    {#if activeJob}
      <div class="card p-6 space-y-3 border-l-4 border-blue-500">
        <h2 class="text-lg font-semibold text-white flex items-center gap-2">
          <Loader size={18} class="animate-spin" />
          Migración en Progreso
        </h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p class="text-xs text-slate-400 uppercase">Tenant</p>
            <p class="text-sm text-white font-mono">{activeJob.subdomain}</p>
          </div>
          <div>
            <p class="text-xs text-slate-400 uppercase">Estado</p>
            <p class="text-sm {stateColor(activeJob.state)} font-semibold">
              {stateLabel(activeJob.state)}
            </p>
          </div>
          <div>
            <p class="text-xs text-slate-400 uppercase">Origen → Destino</p>
            <p class="text-sm text-white">
              {activeJob.source_node_name || `#${activeJob.source_node_id}`} → {activeJob.target_node_name || `#${activeJob.target_node_id}`}
            </p>
          </div>
          <div>
            <p class="text-xs text-slate-400 uppercase">Iniciado</p>
            <p class="text-sm text-white">{formatDate(activeJob.created_at)}</p>
          </div>
        </div>

        {#if activeJob.preflight_result}
          <details class="mt-2">
            <summary class="text-xs text-slate-400 cursor-pointer hover:text-slate-300">
              Ver resultado preflight
            </summary>
            <pre class="mt-1 text-xs bg-slate-900 p-3 rounded overflow-auto max-h-40 text-slate-300">
{JSON.stringify(activeJob.preflight_result, null, 2)}</pre>
          </details>
        {/if}

        {#if activeJob.error_log}
          <div class="bg-red-900/20 border border-red-800/40 rounded p-3 mt-2">
            <p class="text-xs text-red-400 font-semibold uppercase">Error</p>
            <p class="text-sm text-red-300 font-mono whitespace-pre-wrap">{activeJob.error_log}</p>
          </div>
        {/if}

        {#if activeJob.rollback_reason}
          <div class="bg-orange-900/20 border border-orange-800/40 rounded p-3 mt-2">
            <p class="text-xs text-orange-400 font-semibold uppercase">Motivo Rollback</p>
            <p class="text-sm text-orange-300">{activeJob.rollback_reason}</p>
          </div>
        {/if}
      </div>
    {/if}

    <!-- ═══ Panel: Historial de Jobs ═══ -->
    <div class="card p-6 space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold text-white flex items-center gap-2">
          <Clock size={18} />
          Historial de Migraciones
        </h2>
        <div class="flex items-center gap-2">
          <select bind:value={jobsFilter} class="input-field text-sm">
            <option value="all">Todos</option>
            <option value="queued">En cola</option>
            <option value="preflight">Pre-vuelo</option>
            <option value="preparing_target">Preparando</option>
            <option value="cutover">Cutover</option>
            <option value="completed">Completadas</option>
            <option value="failed">Fallidas</option>
            <option value="rollback">Rollback</option>
          </select>
          <button class="btn-secondary px-3 py-1.5 flex items-center gap-1" onclick={loadJobs} disabled={loadingJobs}>
            <RefreshCw size={12} class={loadingJobs ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {#if filteredJobs.length === 0}
        <p class="text-sm text-slate-500 text-center py-6">No hay migraciones registradas</p>
      {:else}
        <div class="overflow-x-auto">
          <table class="data-table w-full">
            <thead>
              <tr>
                <th class="text-left">Tenant</th>
                <th class="text-left">Estado</th>
                <th class="text-left">Origen → Destino</th>
                <th class="text-left">Iniciado por</th>
                <th class="text-left">Creado</th>
                <th class="text-left">Completado</th>
              </tr>
            </thead>
            <tbody>
              {#each filteredJobs as job (job.id)}
                <tr class="hover:bg-slate-800/50 transition-colors cursor-default">
                  <td class="font-mono text-sm">{job.subdomain}</td>
                  <td>
                    {#snippet jobIcon()}
                      {@const Icon = stateIcon(job.state)}
                      <Icon size={14} />
                    {/snippet}
                    <span class="inline-flex items-center gap-1 text-sm {stateColor(job.state)}">
                      {@render jobIcon()}
                      {stateLabel(job.state)}
                    </span>
                  </td>
                  <td class="text-sm">
                    {job.source_node_name || `#${job.source_node_id}`} → {job.target_node_name || `#${job.target_node_id}`}
                  </td>
                  <td class="text-sm text-slate-400">{job.initiated_by}</td>
                  <td class="text-sm text-slate-400">{formatDate(job.created_at)}</td>
                  <td class="text-sm text-slate-400">{job.completed_at ? formatDate(job.completed_at) : '—'}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </div>

    <!-- ═══ Panel: Nodos del Clúster ═══ -->
    <div class="card p-6 space-y-4">
      <h2 class="text-lg font-semibold text-white flex items-center gap-2">
        <Server size={18} />
        Nodos del Clúster
      </h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {#each nodes as node (node.id)}
          <div class="bg-slate-800/50 rounded-lg p-4 border border-slate-700 space-y-2">
            <div class="flex items-center justify-between">
              <p class="text-white font-semibold">{node.name}</p>
              <span class="text-xs px-2 py-0.5 rounded-full {node.status === 'online' ? 'bg-green-900/40 text-green-400' : 'bg-red-900/40 text-red-400'}">
                {node.status}
              </span>
            </div>
            <p class="text-xs text-slate-400 font-mono">{node.hostname} · {node.region}</p>
            <div class="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span class="text-slate-500">Despliegues:</span>
                <span class="text-white ml-1">{node.active_deployments_count ?? 0}</span>
              </div>
              <div>
                <span class="text-slate-500">Slots libres:</span>
                <span class="text-white ml-1">{node.available_slots ?? 0}</span>
              </div>
              <div>
                <span class="text-slate-500">Migraciones:</span>
                <span class="text-white ml-1">{node.active_migrations_count ?? 0}</span>
              </div>
              <div>
                <span class="text-slate-500">Hospeda tenants:</span>
                <span class="ml-1 {node.can_host_tenants ? 'text-green-400' : 'text-red-400'}">
                  {node.can_host_tenants ? 'Sí' : 'No'}
                </span>
              </div>
            </div>
            <div class="text-xs text-slate-500">
              RAM: {node.resources.ram.used_gb.toFixed(1)}/{node.resources.ram.total_gb}GB
              · CPU: {node.resources.cpu.usage_percent.toFixed(0)}%
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>
