<script lang="ts">
  import { onMount } from 'svelte';
  import { tunnelsApi } from '../lib/api';
  import { toasts } from '../lib/stores/toast';
  import { formatDate } from '../lib/utils/formatters';
  import { RefreshCw, Wifi, WifiOff, Globe, Server, Link, Trash2, RotateCw, Eye, ChevronDown, ChevronUp, CreditCard } from 'lucide-svelte';
  import type { Tunnel, TunnelStats } from '../lib/api/tunnels';

  let tunnels = $state<Tunnel[]>([]);
  let loading = $state(true);
  let warning = $state<string | null>(null);
  let totalTunnels = $state(0);
  let stats = $state<TunnelStats>({ healthy: 0, down: 0, inactive: 0, total_dns_cnames: 0 });
  let searchQuery = $state('');
  let filterStatus = $state<string>('all');
  let expandedTunnel = $state<string | null>(null);

  // Filtrado reactivo
  let filteredTunnels = $derived(
    (tunnels || []).filter(t => {
      const matchesSearch = !searchQuery ||
        t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (t.deployment?.subdomain || '').toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus = filterStatus === 'all' || t.status === filterStatus;
      return matchesSearch && matchesStatus;
    })
  );

  async function loadTunnels() {
    loading = true;
    try {
      const data = await tunnelsApi.list();
      tunnels = data.tunnels ?? [];
      totalTunnels = data.total ?? tunnels.length;
      stats = data.stats ?? { healthy: 0, down: 0, inactive: 0, total_dns_cnames: 0 };
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
      toasts.success('Conexiones del tunnel limpiadas');
      await loadTunnels();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al reiniciar tunnel');
    }
  }

  async function handleDelete(tunnel: Tunnel) {
    if (!window.confirm(`¿Eliminar el tunnel "${tunnel.name}" (${tunnel.id.slice(0, 8)})?\n\nEsta acción no se puede deshacer.`)) return;
    try {
      await tunnelsApi.delete(tunnel.id);
      toasts.success('Tunnel eliminado');
      await loadTunnels();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al eliminar tunnel');
    }
  }

  function toggleExpand(id: string) {
    expandedTunnel = expandedTunnel === id ? null : id;
  }

  function statusBadge(status: string): string {
    switch (status) {
      case 'healthy': return 'badge-success';
      case 'down': return 'badge-error';
      case 'inactive': return 'badge-warning';
      default: return 'badge-warning';
    }
  }

  function statusLabel(status: string): string {
    switch (status) {
      case 'healthy': return '● Healthy';
      case 'down': return '○ Down';
      case 'inactive': return '◌ Inactive';
      default: return status;
    }
  }

  onMount(loadTunnels);
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between flex-wrap gap-4">
    <div>
      <h1 class="page-title">CLOUDFLARE TUNNELS</h1>
      <p class="page-subtitle">Gestión de túneles de red — API REST v4</p>
    </div>
    <button class="btn-secondary px-4 py-2 flex items-center gap-2" onclick={loadTunnels} disabled={loading}>
      <RefreshCw size={14} class={loading ? 'animate-spin' : ''} />
      ACTUALIZAR
    </button>
  </div>

  <!-- Warning banner -->
  {#if warning}
    <div class="bg-amber-50 border border-amber-200 px-4 py-3 flex items-start gap-3 rounded">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-amber-600 shrink-0 mt-0.5">
        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      <p class="text-sm text-amber-700">{warning}</p>
    </div>
  {/if}

  <!-- Stats Cards -->
  <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
    <div class="stat-card card">
      <div class="stat-value text-2xl font-bold">{totalTunnels}</div>
      <div class="stat-label text-xs text-gray-500 uppercase">Total Tunnels</div>
    </div>
    <div class="stat-card card">
      <div class="stat-value text-2xl font-bold text-emerald-600">{stats.healthy}</div>
      <div class="stat-label text-xs text-gray-500 uppercase flex items-center gap-1">
        <Wifi size={12} class="text-emerald-500" /> Healthy
      </div>
    </div>
    <div class="stat-card card">
      <div class="stat-value text-2xl font-bold text-red-600">{stats.down}</div>
      <div class="stat-label text-xs text-gray-500 uppercase flex items-center gap-1">
        <WifiOff size={12} class="text-red-500" /> Down
      </div>
    </div>
    <div class="stat-card card">
      <div class="stat-value text-2xl font-bold text-amber-600">{stats.inactive}</div>
      <div class="stat-label text-xs text-gray-500 uppercase">Inactive</div>
    </div>
    <div class="stat-card card">
      <div class="stat-value text-2xl font-bold text-blue-600">{stats.total_dns_cnames}</div>
      <div class="stat-label text-xs text-gray-500 uppercase flex items-center gap-1">
        <Globe size={12} class="text-blue-500" /> DNS CNAMEs
      </div>
    </div>
  </div>

  <!-- Filters -->
  <div class="flex items-center gap-4 flex-wrap">
    <input
      type="text"
      placeholder="Buscar por nombre, ID o subdominio..."
      class="input flex-1 min-w-[200px]"
      bind:value={searchQuery}
    />
    <select class="input w-auto" bind:value={filterStatus}>
      <option value="all">Todos los estados</option>
      <option value="healthy">Healthy</option>
      <option value="down">Down</option>
      <option value="inactive">Inactive</option>
    </select>
    <span class="text-xs text-gray-500">{filteredTunnels.length} de {totalTunnels}</span>
  </div>

  <!-- Tunnels Table -->
  <div class="card p-0 overflow-hidden">
    {#if loading}
      <div class="p-8 text-center text-gray-500 text-sm">
        <RefreshCw size={20} class="animate-spin mx-auto mb-2" />
        Cargando tunnels desde Cloudflare API...
      </div>
    {:else if filteredTunnels.length === 0}
      <div class="p-8 text-center text-gray-500 text-sm">
        {#if searchQuery || filterStatus !== 'all'}
          No hay tunnels que coincidan con el filtro
        {:else}
          No hay tunnels registrados
        {/if}
      </div>
    {:else}
      <table class="table w-full">
        <thead>
          <tr>
            <th class="w-8"></th>
            <th>NOMBRE</th>
            <th>ESTADO</th>
            <th>CONEXIONES</th>
            <th>DNS</th>
            <th>TENANT</th>
            <th>STRIPE</th>
            <th>CREADO</th>
            <th>ACCIONES</th>
          </tr>
        </thead>
        <tbody>
          {#each filteredTunnels as tunnel (tunnel.id)}
            <!-- Main row -->
            <tr class="hover:bg-gray-50 cursor-pointer" onclick={() => toggleExpand(tunnel.id)}>
              <td class="text-center">
                {#if expandedTunnel === tunnel.id}
                  <ChevronUp size={14} class="text-gray-400" />
                {:else}
                  <ChevronDown size={14} class="text-gray-400" />
                {/if}
              </td>
              <td>
                <div class="text-sm font-medium">{tunnel.name}</div>
                <div class="font-mono text-[10px] text-gray-400">{tunnel.id.slice(0, 12)}...</div>
              </td>
              <td>
                <span class={statusBadge(tunnel.status)}>{statusLabel(tunnel.status)}</span>
              </td>
              <td class="text-center">
                <span class="text-sm font-medium {tunnel.connections_count > 0 ? 'text-emerald-600' : 'text-gray-400'}">
                  {tunnel.connections_count}
                </span>
              </td>
              <td class="text-center">
                <span class="text-sm {tunnel.dns_count > 0 ? 'text-blue-600 font-medium' : 'text-gray-400'}">
                  {tunnel.dns_count ?? 0}
                </span>
              </td>
              <td class="text-sm">
                {#if tunnel.deployment}
                  <div class="text-gray-700 font-medium">{tunnel.deployment.subdomain ?? '-'}</div>
                  <div class="text-[10px] text-gray-400">{tunnel.deployment.plan ?? ''}</div>
                {:else}
                  <span class="text-gray-300">—</span>
                {/if}
              </td>
              <td class="text-sm">
                {#if tunnel.deployment?.stripe}
                  <div class="flex items-center gap-1">
                    <CreditCard size={12} class="text-purple-500" />
                    <span class="text-xs {tunnel.deployment.stripe.status === 'active' ? 'text-emerald-600' : 'text-gray-500'}">
                      {tunnel.deployment.stripe.status ?? '—'}
                    </span>
                  </div>
                {:else}
                  <span class="text-gray-300">—</span>
                {/if}
              </td>
              <td class="text-xs text-gray-500">{formatDate(tunnel.created_at)}</td>
              <td>
                <div class="flex items-center gap-1" onclick={(e) => e.stopPropagation()}>
                  <button class="btn-secondary btn-sm p-1.5" onclick={() => handleRestart(tunnel.id)} title="Limpiar conexiones">
                    <RotateCw size={12} />
                  </button>
                  <button class="btn-danger btn-sm p-1.5" onclick={() => handleDelete(tunnel)} title="Eliminar tunnel">
                    <Trash2 size={12} />
                  </button>
                </div>
              </td>
            </tr>

            <!-- Expanded detail row -->
            {#if expandedTunnel === tunnel.id}
              <tr class="bg-gray-50/80">
                <td colspan="9" class="px-6 py-4">
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">

                    <!-- Conexiones -->
                    <div>
                      <h4 class="text-xs uppercase text-gray-400 font-semibold mb-2 flex items-center gap-1">
                        <Server size={12} /> Conexiones ({tunnel.connections?.length ?? 0})
                      </h4>
                      {#if (tunnel.connections ?? []).length > 0}
                        <div class="space-y-1">
                          {#each tunnel.connections as conn}
                            <div class="bg-white border rounded px-3 py-1.5 text-xs">
                              <span class="font-mono font-medium text-blue-600">{conn.colo_name}</span>
                              <span class="text-gray-400 mx-1">|</span>
                              <span class="text-gray-500">{conn.origin_ip || '—'}</span>
                              {#if conn.is_pending_reconnect}
                                <span class="text-amber-500 ml-1">(reconectando)</span>
                              {/if}
                            </div>
                          {/each}
                        </div>
                      {:else}
                        <p class="text-xs text-gray-400 italic">Sin conexiones activas</p>
                      {/if}
                    </div>

                    <!-- DNS Records -->
                    <div>
                      <h4 class="text-xs uppercase text-gray-400 font-semibold mb-2 flex items-center gap-1">
                        <Globe size={12} /> DNS Records ({tunnel.dns_count ?? 0})
                      </h4>
                      {#if (tunnel.dns_records ?? []).length > 0}
                        <div class="space-y-1">
                          {#each tunnel.dns_records as dns}
                            <div class="bg-white border rounded px-3 py-1.5 text-xs flex items-center gap-2">
                              <Link size={10} class="text-blue-400 shrink-0" />
                              <a href="https://{dns.name}" target="_blank" rel="noopener"
                                class="text-blue-600 hover:underline truncate">{dns.name}</a>
                              {#if dns.proxied}
                                <span class="text-orange-500 text-[9px] uppercase font-semibold shrink-0">proxied</span>
                              {/if}
                            </div>
                          {/each}
                        </div>
                      {:else}
                        <p class="text-xs text-gray-400 italic">Sin registros DNS asociados</p>
                      {/if}
                    </div>

                    <!-- Deployment / Stripe -->
                    <div>
                      <h4 class="text-xs uppercase text-gray-400 font-semibold mb-2 flex items-center gap-1">
                        <CreditCard size={12} /> Deployment & Stripe
                      </h4>
                      {#if tunnel.deployment}
                        <div class="bg-white border rounded px-3 py-2 text-xs space-y-1.5">
                          <div class="flex justify-between">
                            <span class="text-gray-400">Subdominio</span>
                            <span class="font-medium">{tunnel.deployment.subdomain}</span>
                          </div>
                          {#if tunnel.deployment.url}
                            <div class="flex justify-between">
                              <span class="text-gray-400">URL</span>
                              <a href={tunnel.deployment.url} target="_blank" class="text-blue-600 hover:underline truncate max-w-[180px]">{tunnel.deployment.url}</a>
                            </div>
                          {/if}
                          {#if tunnel.deployment.direct_url}
                            <div class="flex justify-between">
                              <span class="text-gray-400">Direct</span>
                              <span class="font-mono text-gray-600">{tunnel.deployment.direct_url}</span>
                            </div>
                          {/if}
                          {#if tunnel.deployment.plan}
                            <div class="flex justify-between">
                              <span class="text-gray-400">Plan</span>
                              <span class="uppercase text-[10px] font-semibold text-purple-600">{tunnel.deployment.plan}</span>
                            </div>
                          {/if}
                          {#if tunnel.deployment.database_name}
                            <div class="flex justify-between">
                              <span class="text-gray-400">DB</span>
                              <span class="font-mono text-gray-600">{tunnel.deployment.database_name}</span>
                            </div>
                          {/if}
                          {#if tunnel.deployment.stripe}
                            <hr class="my-1 border-gray-100" />
                            <div class="flex justify-between">
                              <span class="text-gray-400">Stripe</span>
                              <span class="{tunnel.deployment.stripe.status === 'active' ? 'text-emerald-600' : 'text-gray-500'} font-medium">
                                {tunnel.deployment.stripe.status ?? '—'}
                              </span>
                            </div>
                            {#if tunnel.deployment.stripe.plan_name}
                              <div class="flex justify-between">
                                <span class="text-gray-400">Plan Stripe</span>
                                <span class="text-gray-700">{tunnel.deployment.stripe.plan_name}</span>
                              </div>
                            {/if}
                          {/if}
                        </div>
                      {:else}
                        <p class="text-xs text-gray-400 italic">Sin deployment asociado en la BD</p>
                      {/if}
                    </div>

                  </div>

                  <!-- Full Tunnel ID -->
                  <div class="mt-3 pt-3 border-t border-gray-200 flex items-center gap-4 text-[10px] text-gray-400">
                    <span>ID: <span class="font-mono select-all">{tunnel.id}</span></span>
                    <span>Tipo: {tunnel.tunnel_type}</span>
                    {#if tunnel.remote_config}
                      <span class="text-orange-500 font-medium">Remote Config</span>
                    {/if}
                  </div>
                </td>
              </tr>
            {/if}
          {/each}
        </tbody>
      </table>
    {/if}
  </div>
</div>
