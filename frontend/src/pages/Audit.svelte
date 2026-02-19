<script lang="ts">
  import { onMount } from 'svelte';
  import { auditApi } from '../lib/api';
  import { toasts } from '../lib/stores';
  import type { AuditEvent } from '../lib/types';
  import { formatDate } from '../lib/utils/formatters';
  import {
    Shield, RefreshCw, Search, ChevronLeft, ChevronRight,
    User, Globe, Monitor, Activity, Filter, ChevronDown, ChevronUp,
  } from 'lucide-svelte';

  let events: AuditEvent[] = [];
  let total = 0;
  let loading = true;
  let search = '';
  let typeFilter = '';
  let resourceFilter = '';
  const PAGE_SIZE = 30;
  let currentPage = 0;
  let expandedId: number | null = null;

  async function loadEvents(page = 0) {
    loading = true;
    try {
      const res = await auditApi.list({
        event_type: typeFilter || undefined,
        resource: resourceFilter || undefined,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      });
      events = res?.items ?? [];
      total = res?.total ?? 0;
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  function statusColor(status: string | null): string {
    if (!status) return 'badge-neutral';
    if (status === 'success' || status === 'ok') return 'badge-success';
    if (status === 'error' || status === 'failed') return 'badge-error';
    if (status === 'warning') return 'badge-warning';
    return 'badge-info';
  }

  async function goToPage(page: number) {
    if (page < 0 || page >= totalPages) return;
    currentPage = page;
    await loadEvents(currentPage);
  }

  $: totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  $: startItem = currentPage * PAGE_SIZE + 1;
  $: endItem = Math.min((currentPage + 1) * PAGE_SIZE, total);

  $: filtered = (events || []).filter(e =>
    (e.event_type || '').toLowerCase().includes(search.toLowerCase()) ||
    (e.actor_username || '').toLowerCase().includes(search.toLowerCase()) ||
    (e.resource || '').toLowerCase().includes(search.toLowerCase()) ||
    (e.action || '').toLowerCase().includes(search.toLowerCase())
  );

  $: eventTypes = [...new Set((events || []).map(e => e.event_type).filter(Boolean))];

  onMount(() => loadEvents(0));
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><Shield size={24} /> Auditoría</h1>
      <p class="page-subtitle">Trail de eventos del sistema — persistente e inmutable</p>
    </div>
    <button class="btn-secondary flex items-center gap-2" on:click={() => loadEvents(currentPage)} disabled={loading}>
      <RefreshCw size={14} class={loading ? 'animate-spin' : ''} /> Actualizar
    </button>
  </div>

  <!-- KPIs -->
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
    <div class="stat-card">
      <span class="stat-label">Total Eventos</span>
      <span class="stat-value">{total}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Tipos únicos</span>
      <span class="stat-value text-info">{eventTypes.length}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Éxitos</span>
      <span class="stat-value text-success">{(events || []).filter(e => e.status === 'success' || e.status === 'ok').length}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Errores</span>
      <span class="stat-value text-error">{(events || []).filter(e => e.status === 'error' || e.status === 'failed').length}</span>
    </div>
  </div>

  <!-- Filters -->
  <div class="flex flex-col sm:flex-row gap-3">
    <div class="relative flex-1">
      <Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
      <input type="text" bind:value={search} placeholder="Buscar evento, actor, recurso..." class="input pl-10 w-full" />
    </div>
    <input type="text" bind:value={typeFilter} placeholder="Tipo de evento..." class="input w-auto" on:keydown={(e) => e.key === 'Enter' && loadEvents(0)} />
    <input type="text" bind:value={resourceFilter} placeholder="Recurso..." class="input w-auto" on:keydown={(e) => e.key === 'Enter' && loadEvents(0)} />
    <button class="btn-secondary btn-sm flex items-center gap-1" on:click={() => { currentPage = 0; loadEvents(0); }}>
      <Filter size={14} /> Filtrar
    </button>
  </div>

  <!-- Event List -->
  {#if loading}
    <div class="text-center py-16 text-gray-500">
      <div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin mx-auto"></div>
    </div>
  {:else if filtered.length === 0}
    <div class="text-center py-16 text-gray-500">No hay eventos de auditoría</div>
  {:else}
    <div class="card p-0 overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b border-border-light">
        <span class="section-heading">Eventos</span>
        {#if total > 0}
          <span class="text-[11px] text-gray-500">{startItem}–{endItem} de {total}</span>
        {/if}
      </div>

      <div class="divide-y divide-border-light">
        {#each filtered as evt}
          <div class="hover:bg-bg-page/50 transition-colors">
            <button class="w-full px-6 py-3 flex items-center gap-4 text-left" type="button" on:click={() => expandedId = expandedId === evt.id ? null : evt.id}>
              <div class="flex-shrink-0">
                <Activity size={16} class="text-gray-400" />
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-semibold text-text-primary text-sm">{evt.event_type}</span>
                  {#if evt.action}<span class="badge-info text-[9px]">{evt.action}</span>{/if}
                  {#if evt.status}<span class="{statusColor(evt.status)} text-[9px]">{evt.status}</span>{/if}
                </div>
                <div class="flex items-center gap-3 mt-1 text-[11px] text-gray-500">
                  {#if evt.actor_username}
                    <span class="flex items-center gap-1"><User size={11} /> {evt.actor_username}</span>
                  {/if}
                  {#if evt.resource}
                    <span class="flex items-center gap-1"><Monitor size={11} /> {evt.resource}</span>
                  {/if}
                  {#if evt.ip_address}
                    <span class="flex items-center gap-1"><Globe size={11} /> {evt.ip_address}</span>
                  {/if}
                </div>
              </div>
              <div class="text-right flex-shrink-0">
                <div class="text-[11px] text-gray-500">{formatDate(evt.created_at)}</div>
                {#if evt.actor_role}
                  <span class="badge-neutral text-[9px] mt-1">{evt.actor_role}</span>
                {/if}
              </div>
              <div class="flex-shrink-0">
                {#if expandedId === evt.id}<ChevronUp size={14} />{:else}<ChevronDown size={14} />{/if}
              </div>
            </button>

            {#if expandedId === evt.id}
              <div class="px-6 pb-4 bg-bg-page border-t border-border-light">
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3 text-sm">
                  <div><span class="text-[11px] text-gray-500 block">ID</span>{evt.id}</div>
                  <div><span class="text-[11px] text-gray-500 block">Actor ID</span>{evt.actor_id || '—'}</div>
                  <div><span class="text-[11px] text-gray-500 block">User Agent</span><span class="truncate block max-w-[200px] text-[11px]">{evt.user_agent || '—'}</span></div>
                  <div><span class="text-[11px] text-gray-500 block">IP</span>{evt.ip_address || '—'}</div>
                </div>
                {#if evt.details}
                  <div>
                    <span class="text-[11px] text-gray-500 block mb-1">Detalles</span>
                    <pre class="text-xs bg-bg-card p-3 border border-border-light overflow-auto max-h-40 font-mono">{JSON.stringify(evt.details, null, 2)}</pre>
                  </div>
                {/if}
              </div>
            {/if}
          </div>
        {/each}
      </div>

      {#if totalPages > 1}
        <div class="flex items-center justify-between px-6 py-3 border-t border-border-light">
          <span class="text-[11px] text-gray-500">Página {currentPage + 1} de {totalPages}</span>
          <div class="flex items-center gap-2">
            <button class="btn btn-secondary btn-sm" on:click={() => goToPage(currentPage - 1)} disabled={currentPage === 0}>
              <ChevronLeft size={13} /> Anterior
            </button>
            <button class="btn btn-secondary btn-sm" on:click={() => goToPage(currentPage + 1)} disabled={currentPage >= totalPages - 1}>
              Siguiente <ChevronRight size={13} />
            </button>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>
