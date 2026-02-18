<script lang="ts">
  import { onMount } from 'svelte';
  import { partnersApi } from '../lib/api/partners';
  import type { PartnerItem } from '../lib/types';
  import { toasts } from '../lib/stores';
  import {
    Handshake, Plus, Search, Building2, Mail, Phone, Globe,
    CheckCircle, Clock, XCircle, Pencil, Trash2, UserCheck,
  } from 'lucide-svelte';

  let partners: PartnerItem[] = [];
  let loading = true;
  let search = '';
  let statusFilter = '';
  let showForm = false;
  let editingId: number | null = null;
  let summary = { active: 0, pending: 0, total_leads: 0 };

  // Form state
  let form = {
    company_name: '',
    legal_name: '',
    tax_id: '',
    contact_name: '',
    contact_email: '',
    phone: '',
    country: '',
    address: '',
    billing_scenario: 'jeturing_collects',
    commission_rate: 50,
    margin_cap: 30,
    contract_reference: '',
    notes: '',
  };

  function resetForm() {
    form = {
      company_name: '', legal_name: '', tax_id: '', contact_name: '',
      contact_email: '', phone: '', country: '', address: '',
      billing_scenario: 'jeturing_collects', commission_rate: 50, margin_cap: 30,
      contract_reference: '', notes: '',
    };
    editingId = null;
  }

  async function loadPartners() {
    loading = true;
    try {
      const res = await partnersApi.getPartners(statusFilter || undefined);
      partners = res.items;
      summary = res.summary;
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  async function handleSubmit() {
    try {
      if (editingId) {
        await partnersApi.updatePartner(editingId, form as any);
        toasts.success('Partner actualizado');
      } else {
        await partnersApi.createPartner(form as any);
        toasts.success('Partner creado');
      }
      showForm = false;
      resetForm();
      await loadPartners();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  function editPartner(p: PartnerItem) {
    editingId = p.id;
    form = {
      company_name: p.company_name || '',
      legal_name: p.legal_name || '',
      tax_id: p.tax_id || '',
      contact_name: p.contact_name || '',
      contact_email: p.contact_email || '',
      phone: p.phone || '',
      country: p.country || '',
      address: p.address || '',
      billing_scenario: p.billing_scenario || 'jeturing_collects',
      commission_rate: p.commission_rate ?? 50,
      margin_cap: p.margin_cap ?? 30,
      contract_reference: p.contract_reference || '',
      notes: p.notes || '',
    };
    showForm = true;
  }

  async function activatePartner(id: number) {
    try {
      await partnersApi.activatePartner(id);
      toasts.success('Partner activado');
      await loadPartners();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  async function deactivatePartner(id: number) {
    if (!confirm('¿Desactivar este partner?')) return;
    try {
      await partnersApi.deletePartner(id);
      toasts.success('Partner desactivado');
      await loadPartners();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  $: filtered = partners.filter(p =>
    p.company_name.toLowerCase().includes(search.toLowerCase()) ||
    p.contact_email.toLowerCase().includes(search.toLowerCase()) ||
    (p.contact_name || '').toLowerCase().includes(search.toLowerCase())
  );

  onMount(loadPartners);
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><Handshake size={24} /> Partners</h1>
      <p class="page-subtitle">Gestión de socios comerciales — Modelo 50/50</p>
    </div>
    <button class="btn-accent flex items-center gap-2" on:click={() => { resetForm(); showForm = true; }}>
      <Plus size={16} /> Nuevo Partner
    </button>
  </div>

  <!-- Stats -->
  <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
    <div class="stat-card">
      <div class="text-xs font-semibold uppercase text-gray-500 mb-1">Activos</div>
      <div class="text-2xl font-bold text-emerald-400">{summary.active}</div>
    </div>
    <div class="stat-card">
      <div class="text-xs font-semibold uppercase text-gray-500 mb-1">Pendientes</div>
      <div class="text-2xl font-bold text-amber-400">{summary.pending}</div>
    </div>
    <div class="stat-card">
      <div class="text-xs font-semibold uppercase text-gray-500 mb-1">Total Leads</div>
      <div class="text-2xl font-bold text-blue-400">{summary.total_leads}</div>
    </div>
  </div>

  <!-- Filters -->
  <div class="flex flex-col sm:flex-row gap-3">
    <div class="relative flex-1">
      <Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
      <input type="text" bind:value={search} placeholder="Buscar partner..." class="input pl-10 w-full" />
    </div>
    <select bind:value={statusFilter} on:change={loadPartners} class="input w-auto">
      <option value="">Todos los estados</option>
      <option value="active">Activos</option>
      <option value="pending">Pendientes</option>
      <option value="suspended">Suspendidos</option>
      <option value="terminated">Terminados</option>
    </select>
  </div>

  <!-- Form Modal -->
  {#if showForm}
    <div class="card p-6 border border-border-dark">
      <h2 class="section-heading mb-4">{editingId ? 'Editar' : 'Nuevo'} Partner</h2>
      <form on:submit|preventDefault={handleSubmit} class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="label">Empresa *</label>
          <input type="text" bind:value={form.company_name} required class="input w-full" />
        </div>
        <div>
          <label class="label">Razón Social</label>
          <input type="text" bind:value={form.legal_name} class="input w-full" />
        </div>
        <div>
          <label class="label">Tax ID / EIN</label>
          <input type="text" bind:value={form.tax_id} class="input w-full" />
        </div>
        <div>
          <label class="label">Contacto</label>
          <input type="text" bind:value={form.contact_name} class="input w-full" />
        </div>
        <div>
          <label class="label">Email *</label>
          <input type="email" bind:value={form.contact_email} required class="input w-full" />
        </div>
        <div>
          <label class="label">Teléfono</label>
          <input type="text" bind:value={form.phone} class="input w-full" />
        </div>
        <div>
          <label class="label">País</label>
          <input type="text" bind:value={form.country} class="input w-full" />
        </div>
        <div>
          <label class="label">Ref. Contrato</label>
          <input type="text" bind:value={form.contract_reference} class="input w-full" />
        </div>
        <div>
          <label class="label">Escenario de cobro</label>
          <select bind:value={form.billing_scenario} class="input w-full">
            <option value="jeturing_collects">Jeturing cobra al cliente</option>
            <option value="partner_collects">Partner cobra al cliente</option>
          </select>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label">Comisión %</label>
            <input type="number" bind:value={form.commission_rate} min="0" max="100" step="0.5" class="input w-full" />
          </div>
          <div>
            <label class="label">Cap margen %</label>
            <input type="number" bind:value={form.margin_cap} min="0" max="100" step="0.5" class="input w-full" />
          </div>
        </div>
        <div class="md:col-span-2">
          <label class="label">Notas</label>
          <textarea bind:value={form.notes} rows="2" class="input w-full"></textarea>
        </div>
        <div class="md:col-span-2 flex gap-3">
          <button type="submit" class="btn-accent">{editingId ? 'Guardar' : 'Crear'}</button>
          <button type="button" class="btn-secondary" on:click={() => { showForm = false; resetForm(); }}>Cancelar</button>
        </div>
      </form>
    </div>
  {/if}

  <!-- Table -->
  {#if loading}
    <div class="text-center py-12 text-gray-500">Cargando partners...</div>
  {:else if filtered.length === 0}
    <div class="text-center py-12 text-gray-500">No se encontraron partners</div>
  {:else}
    <div class="overflow-x-auto">
      <table class="table w-full">
        <thead>
          <tr>
            <th>Empresa</th>
            <th>Contacto</th>
            <th>Escenario</th>
            <th>Comisión</th>
            <th>Leads</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#each filtered as p}
            <tr>
              <td>
                <div class="font-semibold text-text-light">{p.company_name}</div>
                {#if p.legal_name}<div class="text-xs text-gray-500">{p.legal_name}</div>{/if}
              </td>
              <td>
                <div class="flex items-center gap-1 text-sm"><Mail size={12} /> {p.contact_email}</div>
                {#if p.contact_name}<div class="text-xs text-gray-500">{p.contact_name}</div>{/if}
              </td>
              <td>
                <span class="badge-{p.billing_scenario === 'jeturing_collects' ? 'info' : 'warning'}">
                  {p.billing_scenario === 'jeturing_collects' ? 'Jeturing cobra' : 'Partner cobra'}
                </span>
              </td>
              <td class="font-mono text-sm">{p.commission_rate}%</td>
              <td class="font-mono">{p.leads_count}</td>
              <td>
                {#if p.status === 'active'}
                  <span class="badge-success flex items-center gap-1 w-fit"><CheckCircle size={12} /> Activo</span>
                {:else if p.status === 'pending'}
                  <span class="badge-warning flex items-center gap-1 w-fit"><Clock size={12} /> Pendiente</span>
                {:else}
                  <span class="badge-danger flex items-center gap-1 w-fit"><XCircle size={12} /> {p.status}</span>
                {/if}
              </td>
              <td>
                <div class="flex gap-1">
                  <button class="btn-sm btn-secondary" title="Editar" on:click={() => editPartner(p)}><Pencil size={14} /></button>
                  {#if p.status === 'pending'}
                    <button class="btn-sm btn-accent" title="Activar" on:click={() => activatePartner(p.id)}><UserCheck size={14} /></button>
                  {/if}
                  {#if p.status !== 'terminated'}
                    <button class="btn-sm btn-danger" title="Desactivar" on:click={() => deactivatePartner(p.id)}><Trash2 size={14} /></button>
                  {/if}
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
