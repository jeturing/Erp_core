<script lang="ts">
  import { onMount } from 'svelte';
  import { brandingApi } from '../lib/api';
  import { toasts } from '../lib/stores';
  import type { BrandingProfile } from '../lib/types';
  import {
    Palette, Plus, RefreshCw, Pencil, Eye, Globe, Mail,
    ExternalLink,
  } from 'lucide-svelte';

  let profiles: BrandingProfile[] = [];
  let loading = true;

  // Form
  let showForm = false;
  let editingId: number | null = null;
  let saving = false;
  let form = {
    partner_id: 0, brand_name: '', logo_url: '', favicon_url: '',
    primary_color: '#C05A3C', secondary_color: '#1a1a1a',
    support_email: '', support_url: '', custom_css: '',
  };

  // Preview
  let previewId: number | null = null;

  function resetForm() {
    form = {
      partner_id: 0, brand_name: '', logo_url: '', favicon_url: '',
      primary_color: '#C05A3C', secondary_color: '#1a1a1a',
      support_email: '', support_url: '', custom_css: '',
    };
    editingId = null;
  }

  async function loadProfiles() {
    loading = true;
    try {
      const res = await brandingApi.list();
      profiles = res.items;
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  async function handleSubmit() {
    saving = true;
    try {
      if (editingId) {
        await brandingApi.update(editingId, form as any);
        toasts.success('Perfil de branding actualizado');
      } else {
        await brandingApi.create(form as any);
        toasts.success('Perfil de branding creado');
      }
      showForm = false;
      resetForm();
      await loadProfiles();
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      saving = false;
    }
  }

  function editProfile(p: BrandingProfile) {
    editingId = p.id;
    form = {
      partner_id: p.partner_id,
      brand_name: p.brand_name,
      logo_url: p.logo_url || '',
      favicon_url: p.favicon_url || '',
      primary_color: p.primary_color || '#C05A3C',
      secondary_color: p.secondary_color || '#1a1a1a',
      support_email: p.support_email || '',
      support_url: p.support_url || '',
      custom_css: p.custom_css || '',
    };
    showForm = true;
  }

  onMount(loadProfiles);
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><Palette size={24} /> White-Label Branding</h1>
      <p class="page-subtitle">Perfiles de marca para partners — personalización completa</p>
    </div>
    <div class="flex gap-2">
      <button class="btn-secondary flex items-center gap-2" on:click={loadProfiles} disabled={loading}>
        <RefreshCw size={14} class={loading ? 'animate-spin' : ''} /> Actualizar
      </button>
      <button class="btn-accent flex items-center gap-2" on:click={() => { resetForm(); showForm = true; }}>
        <Plus size={16} /> Nuevo Perfil
      </button>
    </div>
  </div>

  <!-- KPIs -->
  <div class="grid grid-cols-2 sm:grid-cols-3 gap-4">
    <div class="stat-card">
      <span class="stat-label">Total Perfiles</span>
      <span class="stat-value">{profiles.length}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Activos</span>
      <span class="stat-value text-success">{profiles.filter(p => p.is_active).length}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Con CSS Custom</span>
      <span class="stat-value text-info">{profiles.filter(p => p.custom_css).length}</span>
    </div>
  </div>

  <!-- Form -->
  {#if showForm}
    <div class="card p-6 border border-border-dark">
      <h2 class="section-heading mb-4">{editingId ? 'Editar' : 'Nuevo'} Perfil de Branding</h2>
      <form on:submit|preventDefault={handleSubmit} class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="label">Partner ID *</label>
          <input type="number" bind:value={form.partner_id} required min="1" class="input w-full" disabled={!!editingId} />
        </div>
        <div>
          <label class="label">Nombre de marca *</label>
          <input type="text" bind:value={form.brand_name} required class="input w-full" placeholder="Mi Empresa ERP" />
        </div>
        <div>
          <label class="label">URL Logo</label>
          <input type="url" bind:value={form.logo_url} class="input w-full" placeholder="https://..." />
        </div>
        <div>
          <label class="label">URL Favicon</label>
          <input type="url" bind:value={form.favicon_url} class="input w-full" placeholder="https://..." />
        </div>
        <div>
          <label class="label">Color primario</label>
          <div class="flex gap-2 items-center">
            <input type="color" bind:value={form.primary_color} class="w-10 h-10 cursor-pointer border border-border-light" />
            <input type="text" bind:value={form.primary_color} class="input flex-1" />
          </div>
        </div>
        <div>
          <label class="label">Color secundario</label>
          <div class="flex gap-2 items-center">
            <input type="color" bind:value={form.secondary_color} class="w-10 h-10 cursor-pointer border border-border-light" />
            <input type="text" bind:value={form.secondary_color} class="input flex-1" />
          </div>
        </div>
        <div>
          <label class="label">Email de soporte</label>
          <input type="email" bind:value={form.support_email} class="input w-full" placeholder="soporte@miempresa.com" />
        </div>
        <div>
          <label class="label">URL de soporte</label>
          <input type="url" bind:value={form.support_url} class="input w-full" placeholder="https://soporte.miempresa.com" />
        </div>
        <div class="md:col-span-2">
          <label class="label">CSS Personalizado</label>
          <textarea bind:value={form.custom_css} rows="4" class="input w-full font-mono text-xs" placeholder={":root { --brand-primary: #C05A3C; }"}></textarea>
        </div>
        <div class="md:col-span-2 flex gap-3">
          <button type="submit" class="btn-accent" disabled={saving}>{saving ? 'Guardando...' : editingId ? 'Guardar' : 'Crear'}</button>
          <button type="button" class="btn-secondary" on:click={() => { showForm = false; resetForm(); }}>Cancelar</button>
        </div>
      </form>
    </div>
  {/if}

  <!-- Profile Cards -->
  {#if loading}
    <div class="text-center py-16 text-gray-500">
      <div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin mx-auto"></div>
    </div>
  {:else if profiles.length === 0}
    <div class="text-center py-16 text-gray-500">No hay perfiles de branding</div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {#each profiles as p}
        <div class="card hover:shadow-md transition-shadow">
          <!-- Brand Header -->
          <div class="flex items-center gap-3 mb-4">
            <div class="w-12 h-12 rounded flex items-center justify-center text-white font-bold text-lg flex-shrink-0"
                 style="background-color: {p.primary_color || '#C05A3C'}">
              {p.brand_name.charAt(0).toUpperCase()}
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="font-semibold text-text-primary truncate">{p.brand_name}</h3>
              <span class="text-[11px] text-gray-500">Partner #{p.partner_id}</span>
            </div>
            <span class="badge-{p.is_active ? 'success' : 'neutral'}">{p.is_active ? 'Activo' : 'Inactivo'}</span>
          </div>

          <!-- Colors -->
          <div class="flex items-center gap-3 mb-3">
            <div class="flex items-center gap-2">
              <div class="w-6 h-6 border border-border-light" style="background-color: {p.primary_color || '#ccc'}"></div>
              <span class="text-[11px] font-mono text-gray-500">{p.primary_color || '—'}</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-6 h-6 border border-border-light" style="background-color: {p.secondary_color || '#ccc'}"></div>
              <span class="text-[11px] font-mono text-gray-500">{p.secondary_color || '—'}</span>
            </div>
          </div>

          <!-- Links -->
          <div class="space-y-1 text-sm mb-3">
            {#if p.support_email}
              <div class="flex items-center gap-2 text-gray-500">
                <Mail size={14} /> <span class="truncate">{p.support_email}</span>
              </div>
            {/if}
            {#if p.support_url}
              <div class="flex items-center gap-2 text-gray-500">
                <ExternalLink size={14} /> <a href={p.support_url} target="_blank" class="truncate text-info hover:underline">{p.support_url}</a>
              </div>
            {/if}
          </div>

          <!-- Assets -->
          <div class="flex gap-2 mb-3">
            {#if p.logo_url}
              <span class="badge-success text-[9px]">Logo ✓</span>
            {:else}
              <span class="badge-neutral text-[9px]">Sin logo</span>
            {/if}
            {#if p.favicon_url}
              <span class="badge-success text-[9px]">Favicon ✓</span>
            {:else}
              <span class="badge-neutral text-[9px]">Sin favicon</span>
            {/if}
            {#if p.custom_css}
              <span class="badge-info text-[9px]">CSS custom</span>
            {/if}
          </div>

          <!-- Actions -->
          <div class="border-t border-border-light pt-3 flex justify-end gap-2">
            <button class="btn-sm btn-secondary flex items-center gap-1" on:click={() => editProfile(p)}>
              <Pencil size={13} /> Editar
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
