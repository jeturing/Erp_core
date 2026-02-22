<script lang="ts">
  import { onMount } from 'svelte';
  import { communicationsApi } from '../lib/api/communications';
  import type { EmailLog, EmailStats } from '../lib/api/communications';
  import { toasts } from '../lib/stores';
  import { formatDate } from '../lib/utils/formatters';
  import {
    Mail, RefreshCw, Search, ChevronLeft, ChevronRight,
    CheckCircle, XCircle, Clock, BarChart2, Filter, ChevronDown, ChevronUp,
  } from 'lucide-svelte';

  let logs: EmailLog[] = [];
  let stats: EmailStats | null = null;
  let total = 0;
  let loading = true;
  let statsLoading = true;
  let search = '';
  let typeFilter = '';
  let statusFilter = '';
  const PAGE_SIZE = 50;
  let currentPage = 0;
  let expandedId: number | null = null;

  const EMAIL_TYPE_LABELS: Record<string, string> = {
    tenant_credentials:    'Credenciales Tenant',
    password_reset:        'Reset Contraseña',
    commission_notification: 'Comisión',
    quotation:             'Cotización',
    work_order_completion: 'Work Order',
    generic:               'Genérico',
  };

  async function loadLogs(page = 0) {
    loading = true;
    try {
      const res = await communicationsApi.list({
        email_type: typeFilter || undefined,
        status: statusFilter || undefined,
        recipient: search || undefined,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      });
      logs = res?.items ?? [];
      total = res?.total ?? 0;
    } catch (e: any) {
      toasts.error(e.message ?? 'Error cargando historial');
    } finally {
      loading = false;
    }
  }

  async function loadStats() {
    statsLoading = true;
    try {
      stats = await communicationsApi.stats();
    } catch {
      // stats are optional — silently fail
    } finally {
      statsLoading = false;
    }
  }

  function statusBadge(status: string | null): string {
    if (status === 'sent') return 'badge-success';
    if (status === 'failed') return 'badge-error';
    return 'badge-neutral';
  }

  function typeLabel(type: string): string {
    return EMAIL_TYPE_LABELS[type] ?? type;
  }

  async function goToPage(page: number) {
    if (page < 0 || page >= totalPages) return;
    currentPage = page;
    await loadLogs(currentPage);
  }

  async function applyFilters() {
    currentPage = 0;
    await loadLogs(0);
  }

  $: totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  onMount(() => {
    loadLogs(0);
    loadStats();
  });
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><Mail size={24} /> Comunicaciones</h1>
      <p class="page-subtitle">Historial de emails transaccionales enviados por la plataforma</p>
    </div>
    <button class="btn-secondary flex items-center gap-2" on:click={() => { loadLogs(currentPage); loadStats(); }} disabled={loading}>
      <RefreshCw size={14} class={loading ? 'animate-spin' : ''} /> Actualizar
    </button>
  </div>

  <!-- Stats cards -->
  {#if !statsLoading && stats}
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <div class="card p-4">
        <p class="text-xs text-gray-500 mb-1">Total enviados</p>
        <p class="text-2xl font-bold">{stats.total.toLocaleString()}</p>
      </div>
      <div class="card p-4">
        <p class="text-xs text-gray-500 mb-1 flex items-center gap-1"><CheckCircle size={11} class="text-green-400" /> Exitosos</p>
        <p class="text-2xl font-bold text-green-400">{stats.sent.toLocaleString()}</p>
      </div>
      <div class="card p-4">
        <p class="text-xs text-gray-500 mb-1 flex items-center gap-1"><XCircle size={11} class="text-red-400" /> Fallidos</p>
        <p class="text-2xl font-bold text-red-400">{stats.failed.toLocaleString()}</p>
      </div>
      <div class="card p-4">
        <p class="text-xs text-gray-500 mb-1 flex items-center gap-1"><BarChart2 size={11} /> Tasa éxito</p>
        <p class="text-2xl font-bold">
          {stats.total > 0 ? Math.round((stats.sent / stats.total) * 100) : 0}%
        </p>
      </div>
    </div>
  {/if}

  <!-- Filters -->
  <div class="card p-4">
    <div class="flex flex-wrap gap-3">
      <div class="flex items-center gap-2 flex-1 min-w-[200px]">
        <Search size={14} class="text-gray-500 flex-shrink-0" />
        <input
          type="text"
          placeholder="Buscar por destinatario..."
          bind:value={search}
          on:keydown={(e) => e.key === 'Enter' && applyFilters()}
          class="input-field flex-1 text-sm"
        />
      </div>

      <div class="flex items-center gap-2">
        <Filter size={14} class="text-gray-500 flex-shrink-0" />
        <select bind:value={typeFilter} on:change={applyFilters} class="input-field text-sm">
          <option value="">Todos los tipos</option>
          {#each Object.entries(EMAIL_TYPE_LABELS) as [key, label]}
            <option value={key}>{label}</option>
          {/each}
        </select>
      </div>

      <div class="flex items-center gap-2">
        <select bind:value={statusFilter} on:change={applyFilters} class="input-field text-sm">
          <option value="">Todos los estados</option>
          <option value="sent">Enviado</option>
          <option value="failed">Fallido</option>
        </select>
      </div>

      <button class="btn-primary text-sm" on:click={applyFilters}>Buscar</button>
    </div>
  </div>

  <!-- Log table -->
  {#if loading}
    <div class="card p-8 text-center text-gray-500">
      <RefreshCw size={20} class="animate-spin mx-auto mb-2" />
      Cargando historial...
    </div>
  {:else if logs.length === 0}
    <div class="card p-8 text-center text-gray-500">
      <Mail size={32} class="mx-auto mb-3 opacity-30" />
      <p>No hay emails registrados{typeFilter || statusFilter || search ? ' para los filtros aplicados' : ''}.</p>
    </div>
  {:else}
    <div class="card overflow-hidden">
      <div class="px-6 py-3 border-b border-border-light flex items-center justify-between">
        <span class="text-sm text-gray-500">{total.toLocaleString()} registros</span>
        <span class="text-xs text-gray-600">
          {(currentPage * PAGE_SIZE) + 1}–{Math.min((currentPage + 1) * PAGE_SIZE, total)} de {total}
        </span>
      </div>

      <div class="divide-y divide-border-light">
        {#each logs as log (log.id)}
          <div>
            <button
              class="w-full flex items-start gap-4 px-6 py-4 hover:bg-bg-page text-left transition-colors"
              on:click={() => expandedId = expandedId === log.id ? null : log.id}
            >
              <!-- Status icon -->
              <div class="flex-shrink-0 mt-0.5">
                {#if log.status === 'sent'}
                  <CheckCircle size={16} class="text-green-400" />
                {:else if log.status === 'failed'}
                  <XCircle size={16} class="text-red-400" />
                {:else}
                  <Clock size={16} class="text-gray-500" />
                {/if}
              </div>

              <!-- Main info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-medium text-sm truncate">{log.recipient}</span>
                  <span class="badge-neutral text-[10px]">{typeLabel(log.email_type)}</span>
                  <span class="badge text-[10px] {statusBadge(log.status)}">{log.status ?? '—'}</span>
                </div>
                {#if log.subject}
                  <p class="text-xs text-gray-500 mt-0.5 truncate">{log.subject}</p>
                {/if}
              </div>

              <!-- Date + expand -->
              <div class="flex items-center gap-3 flex-shrink-0">
                <span class="text-[11px] text-gray-500">{formatDate(log.sent_at ?? log.created_at)}</span>
                {#if expandedId === log.id}<ChevronUp size={13} />{:else}<ChevronDown size={13} />{/if}
              </div>
            </button>

            {#if expandedId === log.id}
              <div class="px-6 pb-4 bg-bg-page border-t border-border-light">
                <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
                  <div><span class="text-[11px] text-gray-500 block">ID</span>{log.id}</div>
                  <div><span class="text-[11px] text-gray-500 block">Tipo</span>{typeLabel(log.email_type)}</div>
                  <div><span class="text-[11px] text-gray-500 block">Estado</span>{log.status ?? '—'}</div>
                  {#if log.customer_id}
                    <div><span class="text-[11px] text-gray-500 block">Customer ID</span>{log.customer_id}</div>
                  {/if}
                  {#if log.partner_id}
                    <div><span class="text-[11px] text-gray-500 block">Partner ID</span>{log.partner_id}</div>
                  {/if}
                  {#if log.related_id}
                    <div><span class="text-[11px] text-gray-500 block">Related ID</span>{log.related_id}</div>
                  {/if}
                  <div class="col-span-2 sm:col-span-3">
                    <span class="text-[11px] text-gray-500 block">Asunto</span>{log.subject ?? '—'}
                  </div>
                  {#if log.error_message}
                    <div class="col-span-2 sm:col-span-3">
                      <span class="text-[11px] text-gray-500 block">Error</span>
                      <pre class="text-xs bg-bg-card p-2 border border-border-light overflow-auto max-h-24 font-mono text-red-400">{log.error_message}</pre>
                    </div>
                  {/if}
                </div>
              </div>
            {/if}
          </div>
        {/each}
      </div>

      {#if totalPages > 1}
        <div class="flex items-center justify-between px-6 py-3 border-t border-border-light">
          <span class="text-[11px] text-gray-500">Página {currentPage + 1} de {totalPages}</span>
          <div class="flex items-center gap-2">
            <button class="btn-secondary text-sm" on:click={() => goToPage(currentPage - 1)} disabled={currentPage === 0}>
              <ChevronLeft size={13} /> Anterior
            </button>
            <button class="btn-secondary text-sm" on:click={() => goToPage(currentPage + 1)} disabled={currentPage >= totalPages - 1}>
              Siguiente <ChevronRight size={13} />
            </button>
          </div>
        </div>
      {/if}
    </div>
  {/if}

  <!-- By type breakdown -->
  {#if stats && Object.keys(stats.by_type).length > 0}
    <div class="card p-5">
      <h2 class="text-sm font-semibold mb-4 flex items-center gap-2"><BarChart2 size={15} /> Desglose por tipo</h2>
      <div class="space-y-2">
        {#each Object.entries(stats.by_type).sort(([,a],[,b]) => b - a) as [type, count]}
          <div class="flex items-center gap-3">
            <span class="text-sm w-48 truncate text-gray-400">{typeLabel(type)}</span>
            <div class="flex-1 bg-bg-page rounded-full h-2 overflow-hidden">
              <div
                class="h-2 bg-terracotta rounded-full"
                style="width: {stats ? Math.round((count / stats.total) * 100) : 0}%"
              ></div>
            </div>
            <span class="text-sm font-mono w-12 text-right">{count}</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>
