<script lang="ts">
  import { onMount } from 'svelte';
  import { tunnelsApi } from '../lib/api';
  import { toasts } from '../lib/stores/toast';
  import { formatDate } from '../lib/utils/formatters';
  import { RefreshCw, Wifi, WifiOff, Globe, Server, Link, Trash2, RotateCw, ChevronDown, ChevronUp, CreditCard, Plug, Unplug } from 'lucide-svelte';
  import type { Tunnel, TunnelStats, DeploymentItem } from '../lib/api/tunnels';

  let tunnels = $state<Tunnel[]>([]);
  let loading = $state(true);
  let warning = $state<string | null>(null);
  let totalTunnels = $state(0);
  let stats = $state<TunnelStats>({ healthy: 0, down: 0, inactive: 0, total_dns_cnames: 0 });
  let searchQuery = $state('');
  let filterStatus = $state<string>('all');
  let expandedTunnel = $state<string | null>(null);

  // Link modal state
  let showLinkModal = $state(false);
  let linkingTunnel = $state<Tunnel | null>(null);
  let deployments = $state<DeploymentItem[]>([]);
  let deploymentsLoading = $state(false);
  let selectedDeploymentId = $state<number | null>(null);
  let linkingInProgress = $state(false);

  // Stripe link state
  let showStripeModal = $state(false);
  let stripeTunnel = $state<Tunnel | null>(null);
  let subscriptions = $state<{id: number; plan_name: string; status: string; customer_email: string; stripe_id: string}[]>([]);
  let selectedSubId = $state<number | null>(null);

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
    if (!window.confirm('¿Eliminar el tunnel "' + tunnel.name + '"?\n\nEsta acción no se puede deshacer.')) return;
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

  async function openLinkModal(tunnel: Tunnel) {
    linkingTunnel = tunnel;
    showLinkModal = true;
    selectedDeploymentId = tunnel.deployment?.id ?? null;
    deploymentsLoading = true;
    try {
      const data = await tunnelsApi.listDeployments();
      deployments = data.deployments ?? [];
    } catch (e: any) {
      toasts.error('Error cargando deployments');
      deployments = [];
    } finally {
      deploymentsLoading = false;
    }
  }

  async function handleLink() {
    if (!linkingTunnel || !selectedDeploymentId) return;
    linkingInProgress = true;
    try {
      const res = await tunnelsApi.linkDeployment(linkingTunnel.id, selectedDeploymentId) as any;
      toasts.success(res.message || 'Tunnel vinculado');
      showLinkModal = false;
      linkingTunnel = null;
      await loadTunnels();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error vinculando tunnel');
    } finally {
      linkingInProgress = false;
    }
  }

  async function handleUnlink(tunnel: Tunnel) {
    if (!window.confirm('¿Desvincular el tunnel "' + tunnel.name + '" de "' + (tunnel.deployment?.subdomain ?? '') + '"?')) return;
    try {
      const res = await tunnelsApi.unlinkDeployment(tunnel.id) as any;
      toasts.success(res.message || 'Tunnel desvinculado');
      await loadTunnels();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error desvinculando');
    }
  }

  async function openStripeModal(tunnel: Tunnel) {
    stripeTunnel = tunnel;
    showStripeModal = true;
    selectedSubId = null;
    try {
      const data = await tunnelsApi.listDeployments();
      const deps = data.deployments ?? [];
      const subsMap = new Map<number, typeof subscriptions[0]>();
      for (const d of deps) {
        if (d.subscription_id) {
          subsMap.set(d.subscription_id, {
            id: d.subscription_id,
            plan_name: d.plan_type || 'basic',
            status: d.stripe_status || 'unknown',
            customer_email: d.company_name || d.subdomain,
            stripe_id: d.stripe_subscription_id || '',
          });
        }
      }
      subscriptions = Array.from(subsMap.values());
    } catch {
      subscriptions = [];
    }
  }

  async function handleStripeLink() {
    if (!stripeTunnel || !selectedSubId) return;
    linkingInProgress = true;
    try {
      const res = await tunnelsApi.linkStripe(stripeTunnel.id, selectedSubId) as any;
      toasts.success(res.message || 'Stripe vinculado');
      showStripeModal = false;
      stripeTunnel = null;
      await loadTunnels();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error vinculando Stripe');
    } finally {
      linkingInProgress = false;
    }
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
  <div class="flex items-center justify-between flex-wrap gap-4">
    <div>
      <h1 class="page-title">CLOUDFLARE TUNNELS</h1>
      <p class="page-subtitle">Gestión de túneles — vincular tenants & Stripe</p>
    </div>
    <button class="btn-secondary px-4 py-2 flex items-center gap-2" onclick={loadTunnels} disabled={loading}>
      <RefreshCw size={14} class={loading ? 'animate-spin' : ''} />
      ACTUALIZAR
    </button>
  </div>

  {#if warning}
    <div class="bg-amber-50 border border-amber-200 px-4 py-3 flex items-start gap-3 rounded">
      <span class="text-amber-600 text-sm">⚠️</span>
      <p class="text-sm text-amber-700">{warning}</p>
    </div>
  {/if}

  <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
    <div class="stat-card card">
      <div class="stat-value text-2xl font-bold">{totalTunnels}</div>
      <div class="stat-label text-xs text-gray-500 uppercase">Total Tunnels</div>
    </div>
    <div class="stat-card card">
      <div class="stat-value text-2xl font-bold text-emerald-600">{stats.healthy}</div>
      <div class="stat-label text-xs text-gray-500 uppercase flex items-center gap-1"><Wifi size={12} class="text-emerald-500" /> Healthy</div>
    </div>
    <div class="stat-card card">
      <div class="stat-value text-2xl font-bold text-red-600">{stats.down}</div>
      <div class="stat-label text-xs text-gray-500 uppercase flex items-center gap-1"><WifiOff size={12} class="text-red-500" /> Down</div>
    </div>
    <div class="stat-card card">
      <div class="stat-value text-2xl font-bold text-amber-600">{stats.inactive}</div>
      <div class="stat-label text-xs text-gray-500 uppercase">Inactive</div>
    </div>
    <div class="stat-card card">
      <div class="stat-value text-2xl font-bold text-blue-600">{stats.total_dns_cnames}</div>
      <div class="stat-label text-xs text-gray-500 uppercase flex items-center gap-1"><Globe size={12} class="text-blue-500" /> DNS CNAMEs</div>
    </div>
  </div>

  <div class="flex items-center gap-4 flex-wrap">
    <input type="text" placeholder="Buscar por nombre, ID o subdominio..." class="input flex-1 min-w-[200px]" bind:value={searchQuery} />
    <select class="input w-auto" bind:value={filterStatus}>
      <option value="all">Todos los estados</option>
      <option value="healthy">Healthy</option>
      <option value="down">Down</option>
      <option value="inactive">Inactive</option>
    </select>
    <span class="text-xs text-gray-500">{filteredTunnels.length} de {totalTunnels}</span>
  </div>

  <div class="card p-0 overflow-hidden">
    {#if loading}
      <div class="p-8 text-center text-gray-500 text-sm">
        <RefreshCw size={20} class="animate-spin mx-auto mb-2" />
        Cargando tunnels desde Cloudflare API...
      </div>
    {:else if filteredTunnels.length === 0}
      <div class="p-8 text-center text-gray-500 text-sm">
        {searchQuery || filterStatus !== 'all' ? 'No hay tunnels que coincidan' : 'No hay tunnels registrados'}
      </div>
    {:else}
      <table class="table w-full">
        <thead>
          <tr>
            <th class="w-8"></th>
            <th>NOMBRE</th>
            <th>ESTADO</th>
            <th>CONN</th>
            <th>DNS</th>
            <th>TENANT</th>
            <th>STRIPE</th>
            <th>CREADO</th>
            <th>ACCIONES</th>
          </tr>
        </thead>
        <tbody>
          {#each filteredTunnels as tunnel (tunnel.id)}
            <tr class="hover:bg-gray-50 cursor-pointer" onclick={() => toggleExpand(tunnel.id)}>
              <td class="text-center">
                {#if expandedTunnel === tunnel.id}<ChevronUp size={14} class="text-gray-400" />{:else}<ChevronDown size={14} class="text-gray-400" />{/if}
              </td>
              <td>
                <div class="text-sm font-medium">{tunnel.name}</div>
                <div class="font-mono text-[10px] text-gray-400">{tunnel.id.slice(0, 12)}...</div>
              </td>
              <td><span class={statusBadge(tunnel.status)}>{statusLabel(tunnel.status)}</span></td>
              <td class="text-center"><span class="text-sm font-medium {tunnel.connections_count > 0 ? 'text-emerald-600' : 'text-gray-400'}">{tunnel.connections_count}</span></td>
              <td class="text-center"><span class="text-sm {tunnel.dns_count > 0 ? 'text-blue-600 font-medium' : 'text-gray-400'}">{tunnel.dns_count ?? 0}</span></td>
              <td class="text-sm">
                {#if tunnel.deployment}
                  <div class="text-gray-700 font-medium">{tunnel.deployment.subdomain ?? '-'}</div>
                  <div class="text-[10px] text-gray-400">{tunnel.deployment.plan ?? ''}</div>
                {:else}<span class="text-gray-300">—</span>{/if}
              </td>
              <td class="text-sm">
                {#if tunnel.deployment?.stripe}
                  <div class="flex items-center gap-1">
                    <CreditCard size={12} class="text-purple-500" />
                    <span class="text-xs {tunnel.deployment.stripe.status === 'active' ? 'text-emerald-600' : 'text-gray-500'}">{tunnel.deployment.stripe.status ?? '—'}</span>
                  </div>
                {:else}<span class="text-gray-300">—</span>{/if}
              </td>
              <td class="text-xs text-gray-500">{formatDate(tunnel.created_at)}</td>
              <td>
                <div class="flex items-center gap-1" onclick={(e) => e.stopPropagation()}>
                  {#if tunnel.deployment}
                    <button class="btn-secondary btn-sm p-1.5" onclick={() => handleUnlink(tunnel)} title="Desvincular tenant"><Unplug size={12} /></button>
                  {:else}
                    <button class="btn-accent btn-sm p-1.5" onclick={() => openLinkModal(tunnel)} title="Vincular a tenant"><Plug size={12} /></button>
                  {/if}
                  {#if tunnel.deployment && !tunnel.deployment.stripe}
                    <button class="btn-secondary btn-sm p-1.5" onclick={() => openStripeModal(tunnel)} title="Vincular Stripe"><CreditCard size={12} /></button>
                  {/if}
                  <button class="btn-secondary btn-sm p-1.5" onclick={() => handleRestart(tunnel.id)} title="Limpiar conexiones"><RotateCw size={12} /></button>
                  <button class="btn-danger btn-sm p-1.5" onclick={() => handleDelete(tunnel)} title="Eliminar tunnel"><Trash2 size={12} /></button>
                </div>
              </td>
            </tr>
            {#if expandedTunnel === tunnel.id}
              <tr class="bg-gray-50/80">
                <td colspan="9" class="px-6 py-4">
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
                    <div>
                      <h4 class="text-xs uppercase text-gray-400 font-semibold mb-2 flex items-center gap-1"><Server size={12} /> Conexiones ({tunnel.connections?.length ?? 0})</h4>
                      {#if (tunnel.connections ?? []).length > 0}
                        <div class="space-y-1">
                          {#each tunnel.connections as conn}
                            <div class="bg-white border rounded px-3 py-1.5 text-xs">
                              <span class="font-mono font-medium text-blue-600">{conn.colo_name}</span>
                              <span class="text-gray-400 mx-1">|</span>
                              <span class="text-gray-500">{conn.origin_ip || '—'}</span>
                              {#if conn.is_pending_reconnect}<span class="text-amber-500 ml-1">(reconectando)</span>{/if}
                            </div>
                          {/each}
                        </div>
                      {:else}<p class="text-xs text-gray-400 italic">Sin conexiones activas</p>{/if}
                    </div>
                    <div>
                      <h4 class="text-xs uppercase text-gray-400 font-semibold mb-2 flex items-center gap-1"><Globe size={12} /> DNS Records ({tunnel.dns_count ?? 0})</h4>
                      {#if (tunnel.dns_records ?? []).length > 0}
                        <div class="space-y-1">
                          {#each tunnel.dns_records as dns}
                            <div class="bg-white border rounded px-3 py-1.5 text-xs flex items-center gap-2">
                              <Link size={10} class="text-blue-400 shrink-0" />
                              <a href="https://{dns.name}" target="_blank" rel="noopener" class="text-blue-600 hover:underline truncate">{dns.name}</a>
                              {#if dns.proxied}<span class="text-orange-500 text-[9px] uppercase font-semibold shrink-0">proxied</span>{/if}
                            </div>
                          {/each}
                        </div>
                      {:else}<p class="text-xs text-gray-400 italic">Sin registros DNS</p>{/if}
                    </div>
                    <div>
                      <h4 class="text-xs uppercase text-gray-400 font-semibold mb-2 flex items-center gap-1"><CreditCard size={12} /> Deployment & Stripe</h4>
                      {#if tunnel.deployment}
                        <div class="bg-white border rounded px-3 py-2 text-xs space-y-1.5">
                          <div class="flex justify-between"><span class="text-gray-400">Subdominio</span><span class="font-medium">{tunnel.deployment.subdomain}</span></div>
                          {#if tunnel.deployment.url}<div class="flex justify-between"><span class="text-gray-400">URL</span><a href={tunnel.deployment.url} target="_blank" class="text-blue-600 hover:underline truncate max-w-[180px]">{tunnel.deployment.url}</a></div>{/if}
                          {#if tunnel.deployment.direct_url}<div class="flex justify-between"><span class="text-gray-400">Direct</span><span class="font-mono text-gray-600">{tunnel.deployment.direct_url}</span></div>{/if}
                          {#if tunnel.deployment.plan}<div class="flex justify-between"><span class="text-gray-400">Plan</span><span class="uppercase text-[10px] font-semibold text-purple-600">{tunnel.deployment.plan}</span></div>{/if}
                          {#if tunnel.deployment.database_name}<div class="flex justify-between"><span class="text-gray-400">DB</span><span class="font-mono text-gray-600">{tunnel.deployment.database_name}</span></div>{/if}
                          {#if tunnel.deployment.stripe}
                            <hr class="my-1 border-gray-100" />
                            <div class="flex justify-between"><span class="text-gray-400">Stripe</span><span class="{tunnel.deployment.stripe.status === 'active' ? 'text-emerald-600' : 'text-gray-500'} font-medium">{tunnel.deployment.stripe.status ?? '—'}</span></div>
                            {#if tunnel.deployment.stripe.plan_name}<div class="flex justify-between"><span class="text-gray-400">Plan Stripe</span><span class="text-gray-700">{tunnel.deployment.stripe.plan_name}</span></div>{/if}
                          {:else}
                            <hr class="my-1 border-gray-100" />
                            <button class="btn-secondary btn-sm w-full text-xs mt-1 flex items-center justify-center gap-1" onclick={(e) => { e.stopPropagation(); openStripeModal(tunnel); }}>
                              <CreditCard size={10} /> Vincular a Stripe
                            </button>
                          {/if}
                        </div>
                      {:else}
                        <div class="text-center py-3">
                          <p class="text-xs text-gray-400 italic mb-2">Sin deployment asociado</p>
                          <button class="btn-accent btn-sm text-xs flex items-center gap-1 mx-auto" onclick={(e) => { e.stopPropagation(); openLinkModal(tunnel); }}>
                            <Plug size={10} /> Vincular Tenant
                          </button>
                        </div>
                      {/if}
                    </div>
                  </div>
                  <div class="mt-3 pt-3 border-t border-gray-200 flex items-center gap-4 text-[10px] text-gray-400">
                    <span>ID: <span class="font-mono select-all">{tunnel.id}</span></span>
                    <span>Tipo: {tunnel.tunnel_type}</span>
                    {#if tunnel.remote_config}<span class="text-orange-500 font-medium">Remote Config</span>{/if}
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

{#if showLinkModal && linkingTunnel}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onclick={() => showLinkModal = false}>
    <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4" onclick={(e) => e.stopPropagation()}>
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-sm font-semibold uppercase text-gray-700">Vincular Tunnel a Tenant</h3>
        <p class="text-xs text-gray-400 mt-1">Tunnel: <span class="font-mono font-medium text-blue-600">{linkingTunnel.name}</span></p>
      </div>
      <div class="px-6 py-4 max-h-[400px] overflow-y-auto">
        {#if deploymentsLoading}
          <div class="text-center py-8 text-gray-400 text-sm"><RefreshCw size={16} class="animate-spin mx-auto mb-2" />Cargando deployments...</div>
        {:else if deployments.length === 0}
          <p class="text-center text-gray-400 text-sm py-8">No hay deployments disponibles</p>
        {:else}
          <div class="space-y-2">
            {#each deployments as dep (dep.id)}
              <label class="flex items-center gap-3 p-3 border rounded cursor-pointer transition-colors {selectedDeploymentId === dep.id ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:bg-gray-50'}">
                <input type="radio" name="deployment" value={dep.id} class="accent-indigo-600" checked={selectedDeploymentId === dep.id} onchange={() => selectedDeploymentId = dep.id} />
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-sm">{dep.subdomain}</span>
                    {#if dep.plan_type}<span class="text-[10px] uppercase font-semibold text-purple-600 bg-purple-50 px-1.5 py-0.5 rounded">{dep.plan_type}</span>{/if}
                    {#if dep.tunnel_id}<span class="text-[10px] text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded">ya vinculado</span>{/if}
                  </div>
                  <div class="text-[10px] text-gray-400 mt-0.5">{dep.company_name ?? '—'}{#if dep.database_name} · DB: {dep.database_name}{/if}{#if dep.stripe_subscription_id} · Stripe: {dep.stripe_status}{/if}</div>
                </div>
              </label>
            {/each}
          </div>
        {/if}
      </div>
      <div class="px-6 py-3 border-t border-gray-200 flex justify-end gap-3">
        <button class="btn-secondary px-4 py-2 text-sm" onclick={() => showLinkModal = false}>CANCELAR</button>
        <button class="btn-accent px-4 py-2 text-sm flex items-center gap-2 disabled:opacity-50" disabled={!selectedDeploymentId || linkingInProgress} onclick={handleLink}>
          {#if linkingInProgress}<RefreshCw size={12} class="animate-spin" />{:else}<Plug size={12} />{/if} VINCULAR
        </button>
      </div>
    </div>
  </div>
{/if}

{#if showStripeModal && stripeTunnel}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onclick={() => showStripeModal = false}>
    <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4" onclick={(e) => e.stopPropagation()}>
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-sm font-semibold uppercase text-gray-700">Vincular a Suscripción Stripe</h3>
        <p class="text-xs text-gray-400 mt-1">Tunnel: <span class="font-mono font-medium text-blue-600">{stripeTunnel.name}</span>{#if stripeTunnel.deployment} · Tenant: <span class="font-medium">{stripeTunnel.deployment.subdomain}</span>{/if}</p>
      </div>
      <div class="px-6 py-4 max-h-[400px] overflow-y-auto">
        {#if subscriptions.length === 0}
          <p class="text-center text-gray-400 text-sm py-8">No hay suscripciones disponibles</p>
        {:else}
          <div class="space-y-2">
            {#each subscriptions as sub (sub.id)}
              <label class="flex items-center gap-3 p-3 border rounded cursor-pointer transition-colors {selectedSubId === sub.id ? 'border-purple-500 bg-purple-50' : 'border-gray-200 hover:bg-gray-50'}">
                <input type="radio" name="subscription" value={sub.id} class="accent-purple-600" checked={selectedSubId === sub.id} onchange={() => selectedSubId = sub.id} />
                <div class="flex-1">
                  <div class="flex items-center gap-2">
                    <CreditCard size={12} class="text-purple-500" />
                    <span class="font-medium text-sm">Sub #{sub.id}</span>
                    <span class="text-[10px] uppercase font-semibold text-purple-600">{sub.plan_name}</span>
                    <span class="text-[10px] {sub.status === 'active' ? 'text-emerald-600' : 'text-gray-400'}">{sub.status}</span>
                  </div>
                  <div class="text-[10px] text-gray-400 mt-0.5">{sub.customer_email}{#if sub.stripe_id} · {sub.stripe_id.slice(0, 20)}...{/if}</div>
                </div>
              </label>
            {/each}
          </div>
        {/if}
      </div>
      <div class="px-6 py-3 border-t border-gray-200 flex justify-end gap-3">
        <button class="btn-secondary px-4 py-2 text-sm" onclick={() => showStripeModal = false}>CANCELAR</button>
        <button class="btn-accent px-4 py-2 text-sm flex items-center gap-2 disabled:opacity-50" disabled={!selectedSubId || linkingInProgress} onclick={handleStripeLink}>
          {#if linkingInProgress}<RefreshCw size={12} class="animate-spin" />{:else}<CreditCard size={12} />{/if} VINCULAR STRIPE
        </button>
      </div>
    </div>
  </div>
{/if}
