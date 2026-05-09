<script lang="ts">
  import { onMount } from 'svelte';
  import { partnersApi } from '../lib/api/partners';
  import type { QuotationItem, ServiceCatalogItemType, PartnerItem } from '../lib/types';
  import { toasts } from '../lib/stores';
  import {
    FileSpreadsheet, Plus, Search, Send, CheckCircle, Clock,
    XCircle, Pencil, Trash2, Eye, ShoppingBag,
  } from 'lucide-svelte';

  let quotations: QuotationItem[] = [];
  let catalog: ServiceCatalogItemType[] = [];
  let partners: PartnerItem[] = [];
  let loading = true;
  let search = '';
  let statusFilter = '';
  let summary = { total_value: 0, draft: 0, sent: 0, accepted: 0 };
  let showForm = false;
  let showCatalog = false;
  let catalogByCategory: Record<string, ServiceCatalogItemType[]> = {};

  const statusLabels: Record<string, string> = {
    draft: 'Borrador', sent: 'Enviada', accepted: 'Aceptada',
    rejected: 'Rechazada', expired: 'Expirada', invoiced: 'Facturada',
  };

  // Form
  let form = {
    partner_id: null as number | null,
    prospect_name: '',
    prospect_email: '',
    prospect_company: '',
    prospect_phone: '',
    lines: [] as Array<{ service_id?: number; name: string; unit: string; quantity: number; unit_price: number }>,
    partner_margin: 0,
    notes: '',
    terms: 'Precios en USD. Válido por 30 días. Sujeto a contrato de servicios.',
    valid_days: 30,
  };

  function resetForm() {
    form = {
      partner_id: null, prospect_name: '', prospect_email: '', prospect_company: '',
      prospect_phone: '', lines: [], partner_margin: 0, notes: '',
      terms: 'Precios en USD. Válido por 30 días. Sujeto a contrato de servicios.', valid_days: 30,
    };
  }

  function addLine() {
    form.lines = [...form.lines, { name: '', unit: 'Por mes', quantity: 1, unit_price: 0 }];
  }

  function addFromCatalog(item: ServiceCatalogItemType) {
    form.lines = [...form.lines, {
      service_id: item.id,
      name: item.name,
      unit: item.unit,
      quantity: 1,
      unit_price: item.price_monthly,
    }];
    toasts.success(`"${item.name}" añadido`);
  }

  function removeLine(idx: number) {
    form.lines = form.lines.filter((_, i) => i !== idx);
  }

  $: subtotal = form.lines.reduce((sum, l) => sum + l.quantity * l.unit_price, 0);
  $: total = subtotal + form.partner_margin;

  async function loadData() {
    loading = true;
    try {
      const [quotesRes, catalogRes, partnersRes] = await Promise.all([
        partnersApi.getQuotations(undefined, statusFilter || undefined),
        partnersApi.getCatalog(),
        partnersApi.getPartners(),
      ]);
      quotations = quotesRes.items ?? [];
      summary = quotesRes.summary;
      catalog = catalogRes.items ?? [];
      catalogByCategory = catalogRes.by_category ?? {};
      partners = partnersRes.items.filter(p => p.status === 'active');
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  async function handleSubmit() {
    if (form.lines.length === 0) { toasts.error('Añada al menos una línea'); return; }
    try {
      const data: any = { ...form };
      if (!data.partner_id) delete data.partner_id;
      await partnersApi.createQuotation(data);
      toasts.success('Cotización creada');
      showForm = false;
      resetForm();
      await loadData();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  async function sendQuotation(id: number) {
    try {
      await partnersApi.sendQuotation(id);
      toasts.success('Cotización marcada como enviada');
      await loadData();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  async function updateStatus(id: number, newStatus: string) {
    try {
      await partnersApi.updateQuotation(id, { status: newStatus } as any);
      toasts.success('Estado actualizado');
      await loadData();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  async function deleteQuotation(id: number) {
    if (!confirm('¿Eliminar esta cotización?')) return;
    try {
      await partnersApi.deleteQuotation(id);
      toasts.success('Cotización eliminada');
      await loadData();
    } catch (e: any) {
      toasts.error(e.message);
    }
  }

  $: filtered = quotations.filter(q =>
    (q.quote_number || '').toLowerCase().includes(search.toLowerCase()) ||
    (q.prospect_name || '').toLowerCase().includes(search.toLowerCase()) ||
    (q.prospect_company || '').toLowerCase().includes(search.toLowerCase()) ||
    (q.partner_name || q.provider_name || '').toLowerCase().includes(search.toLowerCase())
  );

  onMount(loadData);
</script>

<div class="p-6 space-y-6">
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><FileSpreadsheet size={24} /> Cotizaciones</h1>
      <p class="page-subtitle">Cotizaciones y catálogo de servicios SAJET</p>
    </div>
    <div class="flex gap-2">
      <button class="btn-secondary flex items-center gap-2" on:click={() => { showCatalog = !showCatalog; }}>
        <ShoppingBag size={16} /> Catálogo
      </button>
      <button class="btn-accent flex items-center gap-2" on:click={() => { resetForm(); showForm = true; }}>
        <Plus size={16} /> Nueva Cotización
      </button>
    </div>
  </div>

  <!-- Stats -->
  <div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
    <div class="stat-card">
      <div class="text-xs font-semibold uppercase text-gray-500 mb-1">Valor total</div>
      <div class="text-2xl font-bold text-text-light">${summary.total_value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
    </div>
    <div class="stat-card">
      <div class="text-xs font-semibold uppercase text-gray-500 mb-1">Borradores</div>
      <div class="text-2xl font-bold text-gray-400">{summary.draft}</div>
    </div>
    <div class="stat-card">
      <div class="text-xs font-semibold uppercase text-gray-500 mb-1">Enviadas</div>
      <div class="text-2xl font-bold text-blue-400">{summary.sent}</div>
    </div>
    <div class="stat-card">
      <div class="text-xs font-semibold uppercase text-gray-500 mb-1">Aceptadas</div>
      <div class="text-2xl font-bold text-emerald-400">{summary.accepted}</div>
    </div>
  </div>

  <!-- Service Catalog Panel -->
  {#if showCatalog}
    <div class="card p-6 border border-border-dark">
      <h2 class="section-heading mb-4">Catálogo de Servicios SAJET</h2>
      {#each Object.entries(catalogByCategory) as [category, items]}
        <div class="mb-4">
          <h3 class="text-sm font-semibold text-terracotta uppercase tracking-wide mb-2">{category.replace(/_/g, ' ')}</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
            {#each items as item}
              <div class="bg-dark-subtle rounded p-3 flex items-center justify-between">
                <div>
                  <div class="text-sm font-semibold text-text-light">{item.name}</div>
                  <div class="text-xs text-gray-500">{item.unit} · ${item.price_monthly.toLocaleString()}{item.price_max ? `–$${item.price_max.toLocaleString()}` : ''}/mes</div>
                  {#if item.is_addon}<span class="text-[10px] text-amber-400">Add-on</span>{/if}
                </div>
                {#if showForm}
                  <button class="btn-sm btn-accent" on:click={() => addFromCatalog(item)}>
                    <Plus size={14} />
                  </button>
                {/if}
              </div>
            {/each}
          </div>
        </div>
      {/each}
      {#if catalog.length === 0}
        <div class="text-center py-8 text-gray-500">Catálogo vacío — Seed pendiente</div>
      {/if}
    </div>
  {/if}

  <!-- Filters -->
  <div class="flex flex-col sm:flex-row gap-3">
    <div class="relative flex-1">
      <Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
      <input type="text" bind:value={search} placeholder="Buscar cotización..." class="input pl-10 w-full" />
    </div>
    <select bind:value={statusFilter} on:change={loadData} class="input w-auto">
      <option value="">Todos</option>
      {#each Object.entries(statusLabels) as [key, label]}
        <option value={key}>{label}</option>
      {/each}
    </select>
  </div>

  <!-- Quotation Form -->
  {#if showForm}
    <div class="card p-6 border border-border-dark">
      <h2 class="section-heading mb-4">Nueva Cotización</h2>
      <form on:submit|preventDefault={handleSubmit} class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="label">Partner / Proveedor (opcional)</label>
            <select bind:value={form.partner_id} class="input w-full">
              <option value={null}>— Admin directo —</option>
              {#each partners as p}
                <option value={p.id}>{p.company_name}</option>
              {/each}
            </select>
          </div>
          <div>
            <label class="label">Empresa prospecto</label>
            <input type="text" bind:value={form.prospect_company} class="input w-full" />
          </div>
          <div>
            <label class="label">Nombre contacto</label>
            <input type="text" bind:value={form.prospect_name} class="input w-full" />
          </div>
          <div>
            <label class="label">Email</label>
            <input type="email" bind:value={form.prospect_email} class="input w-full" />
          </div>
        </div>

        <!-- Lines -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="label">Líneas de cotización</label>
            <button type="button" class="btn-sm btn-secondary" on:click={addLine}><Plus size={14} /> Línea</button>
          </div>
          {#if form.lines.length === 0}
            <div class="text-sm text-gray-500 py-4 text-center">Añada líneas manualmente o desde el catálogo</div>
          {/if}
          {#each form.lines as line, i}
            <div class="grid grid-cols-12 gap-2 mb-2 items-end">
              <div class="col-span-4">
                {#if i === 0}<label class="text-xs text-gray-500">Servicio</label>{/if}
                <input type="text" bind:value={line.name} class="input w-full text-sm" placeholder="Nombre" />
              </div>
              <div class="col-span-2">
                {#if i === 0}<label class="text-xs text-gray-500">Unidad</label>{/if}
                <input type="text" bind:value={line.unit} class="input w-full text-sm" />
              </div>
              <div class="col-span-2">
                {#if i === 0}<label class="text-xs text-gray-500">Cant.</label>{/if}
                <input type="number" bind:value={line.quantity} min="1" class="input w-full text-sm" />
              </div>
              <div class="col-span-2">
                {#if i === 0}<label class="text-xs text-gray-500">Precio $</label>{/if}
                <input type="number" bind:value={line.unit_price} min="0" step="0.01" class="input w-full text-sm" />
              </div>
              <div class="col-span-1 text-right font-mono text-sm pt-1 text-text-light">
                ${(line.quantity * line.unit_price).toLocaleString()}
              </div>
              <div class="col-span-1">
                <button type="button" class="btn-sm btn-danger" on:click={() => removeLine(i)}><Trash2 size={12} /></button>
              </div>
            </div>
          {/each}
        </div>

        <!-- Totals -->
        <div class="flex justify-end gap-6 border-t border-border-dark pt-4">
          <div class="text-right">
            <div class="text-xs text-gray-500">Subtotal</div>
            <div class="text-lg font-mono font-bold text-text-light">${subtotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
          </div>
          <div>
            <label class="text-xs text-gray-500">Margen partner/proveedor $</label>
            <input type="number" bind:value={form.partner_margin} min="0" step="0.01" class="input w-24 text-sm" />
          </div>
          <div class="text-right">
            <div class="text-xs text-gray-500">Total mensual</div>
            <div class="text-xl font-mono font-bold text-emerald-400">${total.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="label">Notas</label>
            <textarea bind:value={form.notes} rows="2" class="input w-full"></textarea>
          </div>
          <div>
            <label class="label">Términos</label>
            <textarea bind:value={form.terms} rows="2" class="input w-full"></textarea>
          </div>
        </div>

        <div class="flex gap-3">
          <button type="submit" class="btn-accent">Crear Cotización</button>
          <button type="button" class="btn-secondary" on:click={() => { showForm = false; }}>Cancelar</button>
        </div>
      </form>
    </div>
  {/if}

  <!-- Table -->
  {#if loading}
    <div class="text-center py-12 text-gray-500">Cargando cotizaciones...</div>
  {:else if filtered.length === 0}
    <div class="text-center py-12 text-gray-500">No hay cotizaciones</div>
  {:else}
    <div class="overflow-x-auto">
      <table class="table w-full">
        <thead>
          <tr>
            <th>N°</th>
            <th>Prospecto</th>
            <th>Partner / Proveedor</th>
            <th>Líneas</th>
            <th>Total</th>
            <th>Estado</th>
            <th>Válida hasta</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#each filtered as q}
            <tr>
              <td class="font-mono text-sm text-terracotta">{q.quote_number}</td>
              <td>
                <div class="text-sm font-semibold text-text-light">{q.prospect_company || q.prospect_name || '—'}</div>
                {#if q.prospect_email}<div class="text-xs text-gray-500">{q.prospect_email}</div>{/if}
              </td>
              <td class="text-sm">{q.partner_name || q.provider_name || 'Admin'}</td>
              <td class="font-mono text-sm">{q.lines.length}</td>
              <td class="font-mono text-sm font-semibold text-emerald-400">${q.total_monthly.toLocaleString()}/mes</td>
              <td>
                {#if q.status === 'accepted'}
                  <span class="badge-success"><CheckCircle size={12} /> Aceptada</span>
                {:else if q.status === 'sent'}
                  <span class="badge-info"><Send size={12} /> Enviada</span>
                {:else if q.status === 'draft'}
                  <span class="badge-warning"><Clock size={12} /> Borrador</span>
                {:else if q.status === 'rejected'}
                  <span class="badge-danger"><XCircle size={12} /> Rechazada</span>
                {:else}
                  <span class="badge-danger">{q.status}</span>
                {/if}
              </td>
              <td class="text-xs">{q.valid_until ? new Date(q.valid_until).toLocaleDateString() : '—'}</td>
              <td>
                <div class="flex gap-1">
                  {#if q.status === 'draft'}
                    <button class="btn-sm btn-accent" title="Enviar" on:click={() => sendQuotation(q.id)}><Send size={14} /></button>
                    <button class="btn-sm btn-danger" title="Eliminar" on:click={() => deleteQuotation(q.id)}><Trash2 size={14} /></button>
                  {/if}
                  {#if q.status === 'sent'}
                    <button class="btn-sm btn-accent" title="Aceptar" on:click={() => updateStatus(q.id, 'accepted')}><CheckCircle size={14} /></button>
                    <button class="btn-sm btn-danger" title="Rechazar" on:click={() => updateStatus(q.id, 'rejected')}><XCircle size={14} /></button>
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
