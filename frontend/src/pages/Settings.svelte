<script lang="ts">
  import { onMount } from 'svelte';
  import { settingsApi } from '../lib/api';
  import { toasts } from '../lib/stores/toast';
  import { RefreshCw, Eye, EyeOff } from 'lucide-svelte';

  interface SettingsEntry {
    key: string;
    value: string;
    description?: string;
    category?: string;
    is_secret?: boolean;
    is_editable?: boolean;
  }

  interface OdooConfig {
    admin_login?: string;
    admin_password?: string;
    master_password?: string;
    db_user?: string;
    db_password?: string;
    default_lang?: string;
    default_country?: string;
    base_domain?: string;
    template_db?: string;
  }

  let byCategory = $state<Record<string, SettingsEntry[]>>({});
  let loading = $state(true);
  let odooConfig = $state<OdooConfig>({});
  let odooLoading = $state(false);
  let showOdooForm = $state(false);
  let odooFormData = $state<OdooConfig>({});

  // Per-row inline edit state
  let editingKey = $state<string | null>(null);
  let editingValue = $state('');
  let editingSecret = $state(false);
  let savingKey = $state<string | null>(null);
  let showSecretMap = $state<Record<string, boolean>>({});

  async function loadSettings() {
    loading = true;
    try {
      const data = await settingsApi.getAll();
      byCategory = data.by_category ?? {};
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al cargar configuraciones');
    } finally {
      loading = false;
    }
  }

  async function loadOdooConfig() {
    try {
      const data = await settingsApi.getOdooCurrent();
      odooConfig = data.config ?? {};
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al cargar config Odoo');
    }
  }

  function startEdit(entry: SettingsEntry) {
    editingKey = entry.key;
    editingValue = entry.value ?? '';
    editingSecret = entry.is_secret ?? false;
  }

  function cancelEdit() {
    editingKey = null;
    editingValue = '';
    editingSecret = false;
  }

  async function saveEdit(key: string) {
    savingKey = key;
    try {
      await settingsApi.updateConfig(key, editingValue);
      toasts.success('Configuración actualizada');
      editingKey = null;
      await loadSettings();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al guardar');
    } finally {
      savingKey = null;
    }
  }

  function startOdooEdit() {
    odooFormData = { ...odooConfig };
    showOdooForm = true;
  }

  async function saveOdooConfig(e: Event) {
    e.preventDefault();
    odooLoading = true;
    try {
      await settingsApi.updateOdooConfig(odooFormData);
      toasts.success('Configuración Odoo actualizada');
      showOdooForm = false;
      await loadOdooConfig();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al guardar config Odoo');
    } finally {
      odooLoading = false;
    }
  }

  function toggleShowSecret(key: string) {
    showSecretMap = { ...showSecretMap, [key]: !showSecretMap[key] };
  }

  onMount(() => {
    loadSettings();
    loadOdooConfig();
  });

  const categoryLabels: Record<string, string> = {
    auth: 'Autenticación',
    mail: 'Correo',
    system: 'Sistema',
    database: 'Base de datos',
    provisioning: 'Provisionamiento',
  };
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="page-title">SETTINGS</h1>
      <p class="page-subtitle">Configuración del sistema</p>
    </div>
    <button class="btn-secondary px-4 py-2 flex items-center gap-2" onclick={() => { loadSettings(); loadOdooConfig(); }}>
      <RefreshCw size={14} />
      ACTUALIZAR
    </button>
  </div>

  {#if loading}
    <div class="card p-8 text-center text-gray-500 text-sm">Cargando configuraciones...</div>
  {:else}
    {#each Object.entries(byCategory) as [category, entries]}
      <div class="card p-0 overflow-hidden">
        <div class="px-6 py-3 border-b border-border-light bg-bg-page">
          <span class="section-heading">{categoryLabels[category] ?? category.toUpperCase()}</span>
        </div>
        <table class="table w-full">
          <thead>
            <tr>
              <th style="width:25%">CLAVE</th>
              <th style="width:30%">DESCRIPCIÓN</th>
              <th>VALOR</th>
              <th style="width:120px"></th>
            </tr>
          </thead>
          <tbody>
            {#each entries as entry (entry.key)}
              <tr>
                <td class="font-mono text-xs">{entry.key}</td>
                <td class="text-xs text-gray-500">{entry.description ?? '-'}</td>
                <td>
                  {#if editingKey === entry.key}
                    <div class="flex items-center gap-2">
                      <div class="relative flex-1">
                        <input
                          class="input w-full px-3 py-1.5 text-sm pr-8"
                          type={editingSecret && !showSecretMap[entry.key] ? 'password' : 'text'}
                          bind:value={editingValue}
                        />
                        {#if editingSecret}
                          <button
                            type="button"
                            class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400"
                            onclick={() => toggleShowSecret(entry.key)}
                          >
                            {#if showSecretMap[entry.key]}
                              <EyeOff size={14} />
                            {:else}
                              <Eye size={14} />
                            {/if}
                          </button>
                        {/if}
                      </div>
                      <button
                        class="btn-secondary btn-sm"
                        onclick={cancelEdit}
                      >CANCELAR</button>
                      <button
                        class="btn-accent btn-sm disabled:opacity-60"
                        disabled={savingKey === entry.key}
                        onclick={() => saveEdit(entry.key)}
                      >
                        {savingKey === entry.key ? '...' : 'GUARDAR'}
                      </button>
                    </div>
                  {:else}
                    <span class="font-mono text-xs text-gray-700">
                      {entry.is_secret ? '••••••••' : (entry.value ?? '-')}
                    </span>
                  {/if}
                </td>
                <td>
                  {#if entry.is_editable !== false && editingKey !== entry.key}
                    <button class="btn-secondary btn-sm" onclick={() => startEdit(entry)}>EDITAR</button>
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/each}
  {/if}

  <!-- Odoo Config Section -->
  <div class="card">
    <div class="flex items-center justify-between mb-5">
      <h3 class="section-heading">CONFIGURACIÓN ODOO</h3>
      {#if !showOdooForm}
        <button class="btn-secondary px-4 py-2" onclick={startOdooEdit}>EDITAR ODOO</button>
      {/if}
    </div>

    {#if showOdooForm}
      <form onsubmit={saveOdooConfig} class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="label" for="o-admin-login">Admin Login</label>
            <input id="o-admin-login" class="input w-full px-3 py-2" type="text" bind:value={odooFormData.admin_login} />
          </div>
          <div>
            <label class="label" for="o-admin-pw">Admin Password</label>
            <input id="o-admin-pw" class="input w-full px-3 py-2" type="password" bind:value={odooFormData.admin_password} />
          </div>
          <div>
            <label class="label" for="o-master-pw">Master Password</label>
            <input id="o-master-pw" class="input w-full px-3 py-2" type="password" bind:value={odooFormData.master_password} />
          </div>
          <div>
            <label class="label" for="o-db-user">DB User</label>
            <input id="o-db-user" class="input w-full px-3 py-2" type="text" bind:value={odooFormData.db_user} />
          </div>
          <div>
            <label class="label" for="o-db-pw">DB Password</label>
            <input id="o-db-pw" class="input w-full px-3 py-2" type="password" bind:value={odooFormData.db_password} />
          </div>
          <div>
            <label class="label" for="o-lang">Default Lang</label>
            <input id="o-lang" class="input w-full px-3 py-2" type="text" bind:value={odooFormData.default_lang} placeholder="es_MX" />
          </div>
          <div>
            <label class="label" for="o-country">Default Country</label>
            <input id="o-country" class="input w-full px-3 py-2" type="text" bind:value={odooFormData.default_country} placeholder="MX" />
          </div>
          <div>
            <label class="label" for="o-base-domain">Base Domain</label>
            <input id="o-base-domain" class="input w-full px-3 py-2" type="text" bind:value={odooFormData.base_domain} placeholder="sajet.us" />
          </div>
          <div>
            <label class="label" for="o-template-db">Template DB</label>
            <input id="o-template-db" class="input w-full px-3 py-2" type="text" bind:value={odooFormData.template_db} />
          </div>
        </div>
        <div class="flex gap-3 pt-2">
          <button type="button" class="btn-secondary px-4 py-2" onclick={() => showOdooForm = false}>CANCELAR</button>
          <button type="submit" class="btn-accent px-4 py-2 disabled:opacity-60" disabled={odooLoading}>
            {odooLoading ? 'GUARDANDO...' : 'GUARDAR ODOO'}
          </button>
        </div>
      </form>
    {:else}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {#each [
          ['Admin Login', odooConfig.admin_login],
          ['Base Domain', odooConfig.base_domain],
          ['Template DB', odooConfig.template_db],
          ['Default Lang', odooConfig.default_lang],
          ['Default Country', odooConfig.default_country],
        ] as [label, value]}
          <div class="bg-bg-page border border-border-light p-3">
            <div class="label mb-1">{label}</div>
            <div class="font-mono text-sm text-text-primary">{value ?? '-'}</div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>
