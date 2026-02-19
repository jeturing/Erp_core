<script lang="ts">
  import { onMount } from 'svelte';
  import { workOrdersApi } from '../lib/api';
  import { toasts } from '../lib/stores';
  import type { WorkOrderItem } from '../lib/types';
  import { formatDate } from '../lib/utils/formatters';
  import {
    ClipboardList, Plus, RefreshCw, Search, ChevronRight,
    Clock, CheckCircle, XCircle, PlayCircle, AlertCircle, Ban,
  } from 'lucide-svelte';

  let workOrders: WorkOrderItem[] = [];
  let total = 0;
  let loading = true;
  let search = '';
  let statusFilter = '';

  // Create form
  let showForm = false;
  let creating = false;
  let form = {
    subscription_id: 0, customer_id: undefined as number | undefined,
    partner_id: undefined as number | undefined,
    work_type: 'provision', description: '',
  };

  // Detail panel
  let selectedWO: WorkOrderItem | null = null;
  let updatingStatus = false;

  async function loadWorkOrders() {
    loading = true;
    try {
      const res = await workOrdersApi.list({
        status: statusFilter || undefined,
        limit: 50,
      });
      workOrders = res?.items ?? [];
      total = res?.total ?? 0;
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  async function handleCreate() {
    creating = true;
    try {
      const res = await workOrdersApi.create({
        subscription_id: form.subscription_id,
        customer_id: form.customer_id || undefined,
        partner_id: form.partner_id || undefined,
        work_type: form.work_type,
        description: form.description,
      });
      toasts.success(`Work Order ${res.work_order.order_number} creada`);
      showForm = false;
      form = { subscription_id: 0, customer_id: undefined, partner_id: undefined, work_type: 'provision', description: '' };
      await loadWorkOrders();
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      creating = false;
    }
  }

  async function updateStatus(wo: WorkOrderItem, newStatus: string) {
    updatingStatus = true;
    try {
      await workOrdersApi.updateStatus(wo.id, { status: newStatus });
      toasts.success(`${wo.order_number} → ${newStatus}`);
      await loadWorkOrders();
      if (selectedWO?.id === wo.id) {
        selectedWO = workOrders.find(w => w.id === wo.id) || null;
      }
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      updatingStatus = false;
    }
  }

  function statusIcon(status: string) {
    switch (status) {
      case 'requested': return { icon: Clock, color: 'text-warning', badge: 'badge-warning' };
      case 'approved': return { icon: CheckCircle, color: 'text-info', badge: 'badge-info' };
      case 'in_progress': return { icon: PlayCircle, color: 'text-terracotta', badge: 'badge-pro' };
      case 'completed': return { icon: CheckCircle, color: 'text-success', badge: 'badge-success' };
      case 'rejected': return { icon: XCircle, color: 'text-error', badge: 'badge-error' };
      case 'cancelled': return { icon: Ban, color: 'text-gray-400', badge: 'badge-neutral' };
      default: return { icon: AlertCircle, color: 'text-gray-400', badge: 'badge-neutral' };
    }
  }

  function nextStatuses(current: string): string[] {
    switch (current) {
      case 'requested': return ['approved', 'rejected'];
      case 'approved': return ['in_progress', 'cancelled'];
      case 'in_progress': return ['completed', 'cancelled'];
      default: return [];
    }
  }

  $: filtered = (workOrders || []).filter(w =>
    (w.order_number || '').toLowerCase().includes(search.toLowerCase()) ||
    w.work_type.toLowerCase().includes(search.toLowerCase()) ||
    w.description.toLowerCase().includes(search.toLowerCase())
  );

  $: requested = (workOrders || []).filter(w => w.status === 'requested').length;
  $: inProgress = (workOrders || []).filter(w => w.status === 'in_progress').length;
  $: completed = (workOrders || []).filter(w => w.status === 'completed').length;

  onMount(loadWorkOrders);
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><ClipboardList size={24} /> Work Orders</h1>
      <p class="page-subtitle">Órdenes de trabajo con gating de pago</p>
    </div>
    <div class="flex gap-2">
      <button class="btn-secondary flex items-center gap-2" on:click={loadWorkOrders} disabled={loading}>
        <RefreshCw size={14} class={loading ? 'animate-spin' : ''} /> Actualizar
      </button>
      <button class="btn-accent flex items-center gap-2" on:click={() => showForm = true}>
        <Plus size={16} /> Nueva Orden
      </button>
    </div>
  </div>

  <!-- KPIs -->
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
    <div class="stat-card">
      <span class="stat-label">Total</span>
      <span class="stat-value">{total}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Solicitadas</span>
      <span class="stat-value text-warning">{requested}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">En progreso</span>
      <span class="stat-value text-terracotta">{inProgress}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Completadas</span>
      <span class="stat-value text-success">{completed}</span>
    </div>
  </div>

  <!-- Create Form -->
  {#if showForm}
    <div class="card p-6 border border-border-dark">
      <h2 class="section-heading mb-4">Nueva Work Order</h2>
      <form on:submit|preventDefault={handleCreate} class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="label">Subscription ID *</label>
          <input type="number" bind:value={form.subscription_id} required min="1" class="input w-full" />
        </div>
        <div>
          <label class="label">Tipo de trabajo *</label>
          <select bind:value={form.work_type} class="input w-full">
            <option value="provision">Provisioning</option>
            <option value="migration">Migración</option>
            <option value="configuration">Configuración</option>
            <option value="support">Soporte</option>
            <option value="custom">Custom</option>
          </select>
        </div>
        <div>
          <label class="label">Customer ID</label>
          <input type="number" bind:value={form.customer_id} min="1" class="input w-full" />
        </div>
        <div>
          <label class="label">Partner ID</label>
          <input type="number" bind:value={form.partner_id} min="1" class="input w-full" />
        </div>
        <div class="md:col-span-2">
          <label class="label">Descripción *</label>
          <textarea bind:value={form.description} required rows="3" class="input w-full" placeholder="Detalles del trabajo a realizar..."></textarea>
        </div>
        <div class="md:col-span-2 flex gap-3">
          <button type="submit" class="btn-accent" disabled={creating}>{creating ? 'Creando...' : 'Crear'}</button>
          <button type="button" class="btn-secondary" on:click={() => showForm = false}>Cancelar</button>
        </div>
      </form>
    </div>
  {/if}

  <!-- Filters -->
  <div class="flex flex-col sm:flex-row gap-3">
    <div class="relative flex-1">
      <Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
      <input type="text" bind:value={search} placeholder="Buscar por número, tipo o descripción..." class="input pl-10 w-full" />
    </div>
    <select bind:value={statusFilter} on:change={() => loadWorkOrders()} class="input w-auto">
      <option value="">Todos los estados</option>
      <option value="requested">Solicitada</option>
      <option value="approved">Aprobada</option>
      <option value="in_progress">En progreso</option>
      <option value="completed">Completada</option>
      <option value="rejected">Rechazada</option>
      <option value="cancelled">Cancelada</option>
    </select>
  </div>

  <!-- Table -->
  {#if loading}
    <div class="text-center py-16 text-gray-500">
      <div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin mx-auto"></div>
    </div>
  {:else if filtered.length === 0}
    <div class="text-center py-16 text-gray-500">No hay work orders</div>
  {:else}
    <div class="overflow-x-auto">
      <table class="table w-full">
        <thead>
          <tr>
            <th>Orden</th>
            <th>Tipo</th>
            <th>Descripción</th>
            <th>Solicitado</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#each filtered as wo}
            {@const si = statusIcon(wo.status)}
            <tr class="cursor-pointer hover:bg-bg-card/50" on:click={() => selectedWO = wo}>
              <td class="font-mono font-semibold text-text-primary">{wo.order_number}</td>
              <td><span class="badge-info">{wo.work_type}</span></td>
              <td class="text-sm text-text-secondary max-w-xs truncate">{wo.description}</td>
              <td class="text-sm text-text-secondary">{formatDate(wo.requested_at || wo.created_at)}</td>
              <td>
                <span class={si.badge}>
                  <svelte:component this={si.icon} size={12} />
                  {wo.status.replace('_', ' ')}
                </span>
              </td>
              <td>
                <div class="flex gap-1" on:click|stopPropagation>
                  {#each nextStatuses(wo.status) as ns}
                    <button class="btn-sm {ns === 'rejected' || ns === 'cancelled' ? 'btn-danger' : 'btn-accent'}" on:click={() => updateStatus(wo, ns)} disabled={updatingStatus}>
                      {ns.replace('_', ' ')}
                    </button>
                  {/each}
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}

  <!-- Detail panel -->
  {#if selectedWO}
    <div class="card border border-border-dark">
      <div class="flex items-center justify-between mb-4">
        <h2 class="section-heading">Detalle: {selectedWO.order_number}</h2>
        <button class="btn-ghost btn-sm" on:click={() => selectedWO = null}>✕ Cerrar</button>
      </div>
      <div class="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
        <div><span class="text-[11px] text-gray-500 block">Tipo</span><span class="badge-info mt-1">{selectedWO.work_type}</span></div>
        <div><span class="text-[11px] text-gray-500 block">Estado</span><span class="{statusIcon(selectedWO.status).badge} mt-1">{selectedWO.status}</span></div>
        <div><span class="text-[11px] text-gray-500 block">Subscription</span>#{selectedWO.subscription_id || '—'}</div>
        <div><span class="text-[11px] text-gray-500 block">Customer</span>#{selectedWO.customer_id || '—'}</div>
        <div><span class="text-[11px] text-gray-500 block">Partner</span>#{selectedWO.partner_id || '—'}</div>
        <div><span class="text-[11px] text-gray-500 block">Solicitado por</span>{selectedWO.requested_by || '—'}</div>
        <div><span class="text-[11px] text-gray-500 block">Aprobado por</span>{selectedWO.approved_by || '—'}</div>
        <div><span class="text-[11px] text-gray-500 block">Completado por</span>{selectedWO.completed_by || '—'}</div>
        <div><span class="text-[11px] text-gray-500 block">Creado</span>{formatDate(selectedWO.created_at)}</div>
      </div>
      <div class="mt-4">
        <span class="text-[11px] text-gray-500 block mb-1">Descripción</span>
        <p class="text-sm text-text-secondary bg-bg-page p-3 border border-border-light">{selectedWO.description}</p>
      </div>
      {#if selectedWO.notes}
        <div class="mt-3">
          <span class="text-[11px] text-gray-500 block mb-1">Notas</span>
          <p class="text-sm text-text-secondary">{selectedWO.notes}</p>
        </div>
      {/if}
    </div>
  {/if}
</div>
