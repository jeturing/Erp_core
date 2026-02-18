<script lang="ts">
  import { onMount } from 'svelte';
  import { partnersApi } from '../lib/api/partners';
  import type { LeadItem, PartnerItem } from '../lib/types';
  import { toasts } from '../lib/stores';
  import {
    Target, Plus, Search, ArrowRight, Pencil, Trash2, Trophy,
    Phone, Mail, Building2, Filter,
  } from 'lucide-svelte';

  let leads: LeadItem[] = [];
  let partners: PartnerItem[] = [];
  let loading = true;
  let search = '';
  let partnerFilter = 0;
  let statusFilter = '';
  let pipeline: Record<string, number> = {};
  let totalEstimated = 0;
  let showForm = false;
  let editingId: number | null = null;

  const statusLabels: Record<string, string> = {
    new: 'Nuevo', contacted: 'Contactado', qualified: 'Calificado',
    proposal: 'Propuesta', won: 'Ganado', lost: 'Perdido', invalid: 'Inválido',
  };
  const statusColors: Record<string, string> = {
    new: 'bg-blue-500', contacted: 'bg-cyan-500', qualified: 'bg-amber-500',
    proposal: 'bg-purple-500', won: 'bg-emerald-500', lost: 'bg-red-500', invalid: 'bg-gray-500',
  };

  let form = {
    partner_id: 0,
    company_name: '',
    contact_name: '',
    contact_email: '',
    phone: '',
    country: '',
    notes: '',
    estimated_monthly_value: 0,
  };

  function resetForm() {
    form = { partner_id: 0, company_name: '', contact_name: '', contact_email: '', phone: '', country: '', notes: '', estimated_monthly_value: 0 };
    editingId = null;
  }

  async function loadData() {
    loading = true;
    try {
      const [leadsRes, partnersRes] = await Promise.all([
        partnersApi.getLeads(partnerFilter || undefined, statusFilter || undefined),
        partnersApi.getPartners(),
      ]);
      leads = leadsRes.items;
      pipeline = leadsRes.pipeline;
      totalEstimated = leadsRes.total_estimated_value;
      partners = partnersRes.items.filter(p => p.status === 'active');
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  async function handleSubmit() {
    try {
      if (editingId) {
        await partnersApi.updateLead(editingId, form as any);
        toasts.success('Lead actualizado');
      } else {
        if (!form.partner_id) { toasts.error('Seleccione un partner'); return; }
        await partnersApi.createLead(form as any);
        toasts.success('Lead registrado');
      }
      showForm = false;
      resetForm();
      await loadData();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  function editLead(l: LeadItem) {
    editingId = l.id;
    form = {
      partner_id: l.partner_id,
      company_name: l.company_name,
      contact_name: l.contact_name || '',
      contact_email: l.contact_email || '',
      phone: l.phone || '',
      country: l.country || '',
      notes: l.notes || '',
      estimated_monthly_value: l.estimated_monthly_value || 0,
    };
    showForm = true;
  }

  async function changeStatus(id: number, newStatus: string) {
    try {
      await partnersApi.updateLead(id, { status: newStatus } as any);
      toasts.success('Estado actualizado');
      await loadData();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  async function convertLead(id: number) {
    try {
      await partnersApi.convertLead(id);
      toasts.success('Lead convertido a cliente');
      await loadData();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  async function deleteLead(id: number) {
    if (!confirm('¿Eliminar este lead?')) return;
    try {
      await partnersApi.deleteLead(id);
      toasts.success('Lead eliminado');
      await loadData();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  $: filtered = leads.filter(l =>
    l.company_name.toLowerCase().includes(search.toLowerCase()) ||
    (l.contact_name || '').toLowerCase().includes(search.toLowerCase()) ||
    (l.contact_email || '').toLowerCase().includes(search.toLowerCase())
  );

  onMount(loadData);
</script>

<div class="p-6 space-y-6">
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><Target size={24} /> Pipeline de Leads</h1>
      <p class="page-subtitle">Prospectos registrados por partners — Cláusula 7</p>
    </div>
    <button class="btn-accent flex items-center gap-2" on:click={() => { resetForm(); showForm = true; }}>
      <Plus size={16} /> Nuevo Lead
    </button>
  </div>

  <!-- Pipeline stats -->
  <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
    {#each Object.entries(statusLabels) as [key, label]}
      <button
        class="card p-3 text-center hover:ring-1 hover:ring-terracotta transition-all cursor-pointer {statusFilter === key ? 'ring-2 ring-terracotta' : ''}"
        on:click={() => { statusFilter = statusFilter === key ? '' : key; loadData(); }}
      >
        <div class="text-xs text-gray-500 mb-1">{label}</div>
        <div class="text-lg font-bold text-text-light">{pipeline[key] || 0}</div>
        <div class="h-1 rounded-full mt-1 {statusColors[key]}" style="width: {Math.min(100, ((pipeline[key] || 0) / Math.max(1, leads.length)) * 100)}%"></div>
      </button>
    {/each}
  </div>

  <!-- Valor estimado -->
  <div class="stat-card">
    <div class="text-xs font-semibold uppercase text-gray-500 mb-1">Valor mensual estimado total</div>
    <div class="text-2xl font-bold text-emerald-400">${totalEstimated.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
  </div>

  <!-- Filters -->
  <div class="flex flex-col sm:flex-row gap-3">
    <div class="relative flex-1">
      <Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
      <input type="text" bind:value={search} placeholder="Buscar lead..." class="input pl-10 w-full" />
    </div>
    <select bind:value={partnerFilter} on:change={loadData} class="input w-auto">
      <option value={0}>Todos los partners</option>
      {#each partners as p}
        <option value={p.id}>{p.company_name}</option>
      {/each}
    </select>
  </div>

  <!-- Form -->
  {#if showForm}
    <div class="card p-6 border border-border-dark">
      <h2 class="section-heading mb-4">{editingId ? 'Editar' : 'Nuevo'} Lead</h2>
      <form on:submit|preventDefault={handleSubmit} class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="label">Partner *</label>
          <select bind:value={form.partner_id} required class="input w-full" disabled={!!editingId}>
            <option value={0}>— Seleccionar —</option>
            {#each partners as p}
              <option value={p.id}>{p.company_name}</option>
            {/each}
          </select>
        </div>
        <div>
          <label class="label">Empresa prospecto *</label>
          <input type="text" bind:value={form.company_name} required class="input w-full" />
        </div>
        <div>
          <label class="label">Contacto</label>
          <input type="text" bind:value={form.contact_name} class="input w-full" />
        </div>
        <div>
          <label class="label">Email</label>
          <input type="email" bind:value={form.contact_email} class="input w-full" />
        </div>
        <div>
          <label class="label">Teléfono</label>
          <input type="text" bind:value={form.phone} class="input w-full" />
        </div>
        <div>
          <label class="label">Valor mensual estimado ($)</label>
          <input type="number" bind:value={form.estimated_monthly_value} min="0" step="10" class="input w-full" />
        </div>
        <div class="md:col-span-2">
          <label class="label">Notas</label>
          <textarea bind:value={form.notes} rows="2" class="input w-full"></textarea>
        </div>
        <div class="md:col-span-2 flex gap-3">
          <button type="submit" class="btn-accent">{editingId ? 'Guardar' : 'Registrar'}</button>
          <button type="button" class="btn-secondary" on:click={() => { showForm = false; resetForm(); }}>Cancelar</button>
        </div>
      </form>
    </div>
  {/if}

  <!-- Table -->
  {#if loading}
    <div class="text-center py-12 text-gray-500">Cargando leads...</div>
  {:else if filtered.length === 0}
    <div class="text-center py-12 text-gray-500">No se encontraron leads</div>
  {:else}
    <div class="overflow-x-auto">
      <table class="table w-full">
        <thead>
          <tr>
            <th>Empresa</th>
            <th>Partner</th>
            <th>Contacto</th>
            <th>Valor est.</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#each filtered as l}
            <tr>
              <td>
                <div class="font-semibold text-text-light">{l.company_name}</div>
                {#if l.country}<div class="text-xs text-gray-500">{l.country}</div>{/if}
              </td>
              <td class="text-sm">{l.partner_name}</td>
              <td>
                {#if l.contact_email}<div class="flex items-center gap-1 text-sm"><Mail size={12} /> {l.contact_email}</div>{/if}
                {#if l.contact_name}<div class="text-xs text-gray-500">{l.contact_name}</div>{/if}
              </td>
              <td class="font-mono text-sm">${(l.estimated_monthly_value || 0).toLocaleString()}</td>
              <td>
                <select
                  value={l.status}
                  on:change={(e) => changeStatus(l.id, e.currentTarget.value)}
                  class="input text-xs py-1 px-2"
                >
                  {#each Object.entries(statusLabels) as [key, label]}
                    <option value={key}>{label}</option>
                  {/each}
                </select>
              </td>
              <td>
                <div class="flex gap-1">
                  <button class="btn-sm btn-secondary" title="Editar" on:click={() => editLead(l)}><Pencil size={14} /></button>
                  {#if l.status !== 'won'}
                    <button class="btn-sm btn-accent" title="Convertir" on:click={() => convertLead(l.id)}><Trophy size={14} /></button>
                  {/if}
                  <button class="btn-sm btn-danger" title="Eliminar" on:click={() => deleteLead(l.id)}><Trash2 size={14} /></button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
