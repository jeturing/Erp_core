<script lang="ts">
  import { onMount } from 'svelte';
  import { Modal } from '../lib/components';
  import { settingsApi } from '../lib/api';
  import { toasts } from '../lib/stores/toast';
  import { formatDateTime } from '../lib/utils/formatters';
  import type { SettingsEntry, OdooSettingsResponse } from '../lib/types';
  import { Pencil, Eye, EyeOff, RefreshCw, Settings as SettingsIcon } from 'lucide-svelte';

  let loading = true;
  let byCategory: Record<string, SettingsEntry[]> = {};
  let odooConfig: OdooSettingsResponse | null = null;

  // Edit setting modal
  let showEditModal = false;
  let editLoading = false;
  let editError = '';
  let editEntry: SettingsEntry | null = null;
  let editValue = '';
  let showEditValue = false;

  // Edit Odoo modal
  let showOdooModal = false;
  let odooLoading = false;
  let odooError = '';
  let odooForm = {
    admin_login: '',
    admin_password: '',
    master_password: '',
    db_user: '',
    db_password: '',
    default_lang: '',
    default_country: '',
    base_domain: '',
    template_db: '',
  };

  // Reveal secrets per key
  let revealedKeys: Set<string> = new Set();

  async function loadSettings() {
    loading = true;
    try {
      const [settingsRes, odooRes] = await Promise.all([
        settingsApi.getAll(),
        settingsApi.getOdooCurrent(),
      ]);
      byCategory = settingsRes.by_category;
      odooConfig = odooRes;
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error cargando configuración');
    } finally {
      loading = false;
    }
  }

  onMount(loadSettings);

  function toggleReveal(key: string) {
    const next = new Set(revealedKeys);
    if (next.has(key)) { next.delete(key); } else { next.add(key); }
    revealedKeys = next;
  }

  function openEditModal(entry: SettingsEntry) {
    editEntry = entry;
    editValue = entry.is_secret ? '' : (entry.value || '');
    editError = '';
    showEditValue = false;
    showEditModal = true;
  }

  async function handleEditSave() {
    if (!editEntry) return;
    editError = '';
    if (!editValue.trim() && !editEntry.is_secret) { editError = 'El valor no puede estar vacío'; return; }
    editLoading = true;
    try {
      await settingsApi.updateConfig(editEntry.key, editValue, editEntry.description);
      showEditModal = false;
      toasts.success(`Configuración "${editEntry.key}" actualizada`);
      await loadSettings();
    } catch (err) {
      editError = err instanceof Error ? err.message : 'Error actualizando configuración';
    } finally {
      editLoading = false;
    }
  }

  function openOdooModal() {
    if (!odooConfig) return;
    const c = odooConfig.config;
    odooForm = {
      admin_login: c.admin_login || '',
      admin_password: '',
      master_password: '',
      db_user: c.db_user || '',
      db_password: '',
      default_lang: c.default_lang || '',
      default_country: c.default_country || '',
      base_domain: c.base_domain || '',
      template_db: c.template_db || '',
    };
    odooError = '';
    showOdooModal = true;
  }

  async function handleOdooSave() {
    odooError = '';
    odooLoading = true;
    try {
      const payload: Record<string, string> = {};
      for (const [k, v] of Object.entries(odooForm)) {
        if (v.trim()) payload[k] = v.trim();
      }
      await settingsApi.updateOdooConfig(payload);
      showOdooModal = false;
      toasts.success('Configuración de Odoo actualizada');
      await loadSettings();
    } catch (err) {
      odooError = err instanceof Error ? err.message : 'Error actualizando configuración Odoo';
    } finally {
      odooLoading = false;
    }
  }

  const CATEGORY_LABELS: Record<string, string> = {
    general: 'General',
    security: 'Seguridad',
    email: 'Email',
    billing: 'Billing',
    infrastructure: 'Infraestructura',
    notifications: 'Notificaciones',
    integrations: 'Integraciones',
  };

  function categoryLabel(cat: string) {
    return CATEGORY_LABELS[cat] || cat.charAt(0).toUpperCase() + cat.slice(1);
  }

  function maskValue(value: string) {
    if (!value) return '—';
    return '••••••••';
  }
</script>

<div class="p-6 lg:p-8 space-y-6">
  <!-- Page Header -->
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
      <h1 class="page-title">SETTINGS</h1>
      <p class="page-subtitle mt-1">Configuración global del sistema y parámetros de Odoo</p>
    </div>
    <button class="btn btn-secondary btn-sm" on:click={loadSettings} disabled={loading}>
      <RefreshCw size={13} class={loading ? 'animate-spin' : ''} />
      Actualizar
    </button>
  </div>

  {#if loading}
    <div class="py-24 flex justify-center">
      <div class="w-10 h-10 border-2 border-charcoal border-t-transparent rounded-full animate-spin"></div>
    </div>
  {:else}
    <!-- Settings by Category -->
    {#each Object.entries(byCategory) as [category, entries]}
      <div class="card p-0 overflow-hidden">
        <div class="flex items-center gap-2 px-6 py-4 border-b border-border-light">
          <SettingsIcon size={14} class="text-gray-400" />
          <span class="section-heading">{categoryLabel(category)}</span>
          <span class="text-[11px] text-gray-500 ml-auto">{entries.length} entradas</span>
        </div>
        <div class="divide-y divide-border-light">
          {#each entries as entry (entry.key)}
            <div class="flex items-start justify-between gap-4 px-6 py-4 hover:bg-bg-page/50 transition-colors">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-mono text-[12px] font-semibold text-text-primary">{entry.key}</span>
                  {#if entry.is_secret}
                    <span class="badge badge-warning">secreto</span>
                  {/if}
                  {#if entry.is_editable === false}
                    <span class="badge badge-neutral">solo lectura</span>
                  {/if}
                </div>
                {#if entry.description}
                  <p class="text-[11px] text-gray-500 mt-0.5">{entry.description}</p>
                {/if}
                <div class="flex items-center gap-1.5 mt-1.5">
                  {#if entry.is_secret}
                    <span class="font-mono text-[11px] text-text-secondary">
                      {revealedKeys.has(entry.key) ? (entry.value || '—') : maskValue(entry.value)}
                    </span>
                    <button
                      class="text-gray-400 hover:text-text-primary transition-colors p-0.5"
                      on:click={() => toggleReveal(entry.key)}
                      title={revealedKeys.has(entry.key) ? 'Ocultar' : 'Mostrar'}
                    >
                      {#if revealedKeys.has(entry.key)}
                        <EyeOff size={12} />
                      {:else}
                        <Eye size={12} />
                      {/if}
                    </button>
                  {:else}
                    <span class="font-mono text-[11px] text-text-secondary break-all">{entry.value || '—'}</span>
                  {/if}
                </div>
                {#if entry.updated_at}
                  <p class="text-[10px] text-gray-400 mt-1">Actualizado: {formatDateTime(entry.updated_at)}</p>
                {/if}
              </div>
              {#if entry.is_editable !== false}
                <button
                  class="btn btn-secondary btn-sm shrink-0"
                  on:click={() => openEditModal(entry)}
                  title="Editar"
                >
                  <Pencil size={12} />
                  Editar
                </button>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    {:else}
      <div class="card text-center text-gray-500 text-sm py-12">
        No hay configuraciones disponibles
      </div>
    {/each}

    <!-- Odoo Configuration Section -->
    {#if odooConfig}
      <div class="card p-0 overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-border-light">
          <div class="flex items-center gap-2">
            <span class="section-heading">Configuración de Odoo</span>
            <span class="badge badge-info">odoo</span>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-[11px] text-gray-500">Fuente: {odooConfig.source}</span>
            <button class="btn btn-secondary btn-sm" on:click={openOdooModal}>
              <Pencil size={12} />
              Editar Odoo
            </button>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-0 divide-y sm:divide-y-0 sm:divide-x divide-border-light">
          {#each Object.entries(odooConfig.config) as [key, value]}
            <div class="px-6 py-4 hover:bg-bg-page/50 transition-colors">
              <p class="label mb-1">{key.replace(/_/g, ' ')}</p>
              <div class="flex items-center gap-1.5">
                {#if key.includes('password')}
                  <span class="font-mono text-[11px] text-text-secondary">
                    {revealedKeys.has(`odoo_${key}`) ? (value || '—') : '••••••••'}
                  </span>
                  <button
                    class="text-gray-400 hover:text-text-primary transition-colors p-0.5"
                    on:click={() => toggleReveal(`odoo_${key}`)}
                  >
                    {#if revealedKeys.has(`odoo_${key}`)}
                      <EyeOff size={11} />
                    {:else}
                      <Eye size={11} />
                    {/if}
                  </button>
                {:else}
                  <span class="font-mono text-[11px] text-text-secondary break-all">{value || '—'}</span>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  {/if}
</div>

<!-- Modal: Editar Configuración -->
<Modal
  bind:isOpen={showEditModal}
  title="Editar Configuración"
  confirmText="GUARDAR"
  on:confirm={handleEditSave}
  on:close={() => { showEditModal = false; editError = ''; }}
  loading={editLoading}
  size="sm"
>
  <div class="space-y-4">
    {#if editError}
      <div class="p-3 rounded bg-error/10 border border-error/20 text-sm text-error">{editError}</div>
    {/if}

    <div>
      <label class="label block mb-1" for="edit-key">Clave</label>
      <input id="edit-key" class="input w-full opacity-60 font-mono text-[12px]" value={editEntry?.key || ''} readonly disabled />
    </div>

    {#if editEntry?.description}
      <div class="p-3 rounded bg-bg-page border border-border-light">
        <p class="text-[11px] text-gray-500">{editEntry.description}</p>
      </div>
    {/if}

    <div>
      <label class="label block mb-1" for="edit-value">
        Nuevo Valor
        {#if editEntry?.is_secret}
          <span class="badge badge-warning ml-1">secreto</span>
        {/if}
      </label>
      <div class="relative">
        <input
          id="edit-value"
          type={editEntry?.is_secret && !showEditValue ? 'password' : 'text'}
          class="input w-full {editEntry?.is_secret ? 'pr-9' : ''}"
          placeholder={editEntry?.is_secret ? 'Ingresa el nuevo valor secreto' : 'Nuevo valor'}
          bind:value={editValue}
        />
        {#if editEntry?.is_secret}
          <button
            type="button"
            class="absolute inset-y-0 right-0 px-2.5 text-gray-500 hover:text-text-primary"
            on:click={() => showEditValue = !showEditValue}
          >
            {#if showEditValue}<EyeOff size={14} />{:else}<Eye size={14} />{/if}
          </button>
        {/if}
      </div>
      {#if editEntry?.is_secret}
        <p class="text-[10px] text-gray-400 mt-1">Deja vacío para mantener el valor actual</p>
      {/if}
    </div>
  </div>
</Modal>

<!-- Modal: Editar Configuración Odoo -->
<Modal
  bind:isOpen={showOdooModal}
  title="Editar Configuración Odoo"
  confirmText="GUARDAR ODOO"
  on:confirm={handleOdooSave}
  on:close={() => { showOdooModal = false; odooError = ''; }}
  loading={odooLoading}
  size="lg"
>
  <div class="space-y-4">
    {#if odooError}
      <div class="p-3 rounded bg-error/10 border border-error/20 text-sm text-error">{odooError}</div>
    {/if}

    <p class="text-[11px] text-gray-500">Los campos vacíos no se modificarán. Solo se actualizarán los campos con valor.</p>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div>
        <label class="label block mb-1" for="odoo-admin-login">Admin Login</label>
        <input id="odoo-admin-login" class="input w-full" placeholder={odooConfig?.config.admin_login || 'admin'} bind:value={odooForm.admin_login} />
      </div>
      <div>
        <label class="label block mb-1" for="odoo-base-domain">Base Domain</label>
        <input id="odoo-base-domain" class="input w-full" placeholder={odooConfig?.config.base_domain || 'sajet.us'} bind:value={odooForm.base_domain} />
      </div>
      <div>
        <label class="label block mb-1" for="odoo-admin-password">Admin Password</label>
        <input id="odoo-admin-password" type="password" class="input w-full" placeholder="••••••••" bind:value={odooForm.admin_password} />
      </div>
      <div>
        <label class="label block mb-1" for="odoo-master-password">Master Password</label>
        <input id="odoo-master-password" type="password" class="input w-full" placeholder="••••••••" bind:value={odooForm.master_password} />
      </div>
      <div>
        <label class="label block mb-1" for="odoo-db-user">DB User</label>
        <input id="odoo-db-user" class="input w-full" placeholder={odooConfig?.config.db_user || 'odoo'} bind:value={odooForm.db_user} />
      </div>
      <div>
        <label class="label block mb-1" for="odoo-db-password">DB Password</label>
        <input id="odoo-db-password" type="password" class="input w-full" placeholder="••••••••" bind:value={odooForm.db_password} />
      </div>
      <div>
        <label class="label block mb-1" for="odoo-lang">Idioma por defecto</label>
        <input id="odoo-lang" class="input w-full" placeholder={odooConfig?.config.default_lang || 'es_MX'} bind:value={odooForm.default_lang} />
      </div>
      <div>
        <label class="label block mb-1" for="odoo-country">País por defecto</label>
        <input id="odoo-country" class="input w-full" placeholder={odooConfig?.config.default_country || 'MX'} bind:value={odooForm.default_country} />
      </div>
      <div class="sm:col-span-2">
        <label class="label block mb-1" for="odoo-template-db">Template DB</label>
        <input id="odoo-template-db" class="input w-full" placeholder={odooConfig?.config.template_db || 'template_sajet'} bind:value={odooForm.template_db} />
      </div>
    </div>
  </div>
</Modal>
