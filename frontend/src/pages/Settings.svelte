<script lang="ts">
  import { onMount } from 'svelte';
  import { settingsApi } from '../lib/api';
  import { toasts } from '../lib/stores/toast';
  import { RefreshCw, Eye, EyeOff, Save, CreditCard, Shield, Database, Key, Server, ToggleLeft, ToggleRight, ChevronDown, ChevronUp, CheckCircle, AlertCircle, Lock } from 'lucide-svelte';
  import type { CredentialItem, CredentialCategory, StripeModeResponse } from '../lib/api/settings';

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

  /* ─── Tab state ─── */
  type TabId = 'credentials' | 'stripe' | 'system' | 'Sajet';
  let activeTab = $state<TabId>('credentials');

  /* ─── System config ─── */
  let byCategory = $state<Record<string, SettingsEntry[]>>({});
  let loading = $state(true);

  /* ─── Odoo ─── */
  let odooConfig = $state<OdooConfig>({});
  let odooLoading = $state(false);
  let showOdooForm = $state(false);
  let odooFormData = $state<OdooConfig>({});

  /* ─── Inline edit ─── */
  let editingKey = $state<string | null>(null);
  let editingValue = $state('');
  let editingSecret = $state(false);
  let savingKey = $state<string | null>(null);
  let showSecretMap = $state<Record<string, boolean>>({});

  /* ─── Credentials ─── */
  let credentials = $state<Record<string, CredentialCategory>>({});
  let credentialsLoading = $state(true);
  let credEditKey = $state<string | null>(null);
  let credEditValue = $state('');
  let credSaving = $state(false);
  let expandedCat = $state<string | null>(null);

  /* ─── Stripe mode ─── */
  let stripeMode = $state<StripeModeResponse | null>(null);
  let stripeModeLoading = $state(true);
  let stripeToggling = $state(false);
  let stripeTestKeys = $state({ secret: '', publishable: '', webhook: '' });
  let stripeLiveKeys = $state({ secret: '', publishable: '', webhook: '' });

  const categoryIcons: Record<string, typeof Shield> = {
    stripe: CreditCard,
    cloudflare: Shield,
    database: Database,
    auth: Key,
    infrastructure: Server,
  };

  const categoryLabels: Record<string, string> = {
    auth: 'Autenticación',
    mail: 'Correo',
    system: 'Sistema',
    database: 'Base de datos',
    provisioning: 'Provisionamiento',
  };

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
      toasts.error(e?.message ?? 'Error al cargar config');
    }
  }

  async function loadCredentials() {
    credentialsLoading = true;
    try {
      const data = await settingsApi.getCredentials();
      credentials = data.credentials ?? {};
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al cargar credenciales');
    } finally {
      credentialsLoading = false;
    }
  }

  async function loadStripeMode() {
    stripeModeLoading = true;
    try {
      stripeMode = await settingsApi.getStripeMode();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al cargar modo Stripe');
    } finally {
      stripeModeLoading = false;
    }
  }

  /* ─── System config inline edit ─── */
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

  /* ─── Odoo ─── */
  function startOdooEdit() {
    odooFormData = { ...odooConfig };
    showOdooForm = true;
  }

  async function saveOdooConfig(e: Event) {
    e.preventDefault();
    odooLoading = true;
    try {
      await settingsApi.updateOdooConfig(odooFormData);
      toasts.success('Configuración Sajet actualizada');
      showOdooForm = false;
      await loadOdooConfig();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al guardar config Sajet');
    } finally {
      odooLoading = false;
    }
  }

  /* ─── Credential edit ─── */
  function startCredEdit(item: CredentialItem) {
    credEditKey = item.key;
    credEditValue = item.is_set ? '' : '';
  }

  async function saveCredential(item: CredentialItem) {
    if (!credEditValue.trim()) {
      toasts.error('El valor no puede estar vacío');
      return;
    }
    credSaving = true;
    try {
      await settingsApi.updateCredential(item.key, credEditValue, 'general', item.is_secret);
      toasts.success(`${item.key} actualizado`);
      credEditKey = null;
      credEditValue = '';
      await loadCredentials();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al guardar');
    } finally {
      credSaving = false;
    }
  }

  /* ─── Stripe toggle ─── */
  async function toggleStripeMode() {
    if (!stripeMode) return;
    const newMode = stripeMode.mode === 'test' ? 'live' : 'test';

    const msg = newMode === 'live'
      ? '⚠️ ¿Cambiar a modo PRODUCCIÓN (live)?\n\nSe usarán las claves REALES de Stripe.'
      : '¿Cambiar a modo TEST?\n\nSe usarán las claves de prueba de Stripe.';
    if (!window.confirm(msg)) return;

    stripeToggling = true;
    try {
      const payload: any = { mode: newMode };
      // Include keys if provided
      if (newMode === 'test' && stripeTestKeys.secret) {
        payload.test_secret_key = stripeTestKeys.secret;
        payload.test_publishable_key = stripeTestKeys.publishable;
        payload.test_webhook_secret = stripeTestKeys.webhook;
      }
      if (newMode === 'live' && stripeLiveKeys.secret) {
        payload.live_secret_key = stripeLiveKeys.secret;
        payload.live_publishable_key = stripeLiveKeys.publishable;
        payload.live_webhook_secret = stripeLiveKeys.webhook;
      }
      const res = await settingsApi.setStripeMode(payload);
      toasts.success(res.message || `Modo cambiado a ${newMode.toUpperCase()}`);
      await loadStripeMode();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al cambiar modo Stripe');
    } finally {
      stripeToggling = false;
    }
  }

  function toggleShowSecret(key: string) {
    showSecretMap = { ...showSecretMap, [key]: !showSecretMap[key] };
  }

  function toggleCategory(cat: string) {
    expandedCat = expandedCat === cat ? null : cat;
  }

  onMount(() => {
    loadSettings();
    loadOdooConfig();
    loadCredentials();
    loadStripeMode();
  });
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between flex-wrap gap-4">
    <div>
      <h1 class="page-title">SETTINGS</h1>
      <p class="page-subtitle">Configuración del sistema, credenciales y Stripe</p>
    </div>
    <button class="btn-secondary px-4 py-2 flex items-center gap-2" onclick={() => { loadSettings(); loadOdooConfig(); loadCredentials(); loadStripeMode(); }}>
      <RefreshCw size={14} />
      ACTUALIZAR
    </button>
  </div>

  <!-- Tabs -->
  <div class="flex border-b border-gray-200 gap-1">
    {#each [
      { id: 'credentials' as TabId, label: 'Credenciales', icon: Key },
      { id: 'stripe' as TabId, label: 'Stripe', icon: CreditCard },
      { id: 'system' as TabId, label: 'Sistema', icon: Server },
      { id: 'odoo' as TabId, label: 'Sajet', icon: Database },
    ] as tab (tab.id)}
      <button
        class="px-4 py-2.5 text-sm font-medium flex items-center gap-2 border-b-2 transition-colors {activeTab === tab.id ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
        onclick={() => activeTab = tab.id}
      >
        <svelte:component this={tab.icon} size={14} />
        {tab.label}
      </button>
    {/each}
  </div>

  <!-- ═══════════ TAB: CREDENCIALES ═══════════ -->
  {#if activeTab === 'credentials'}
    {#if credentialsLoading}
      <div class="card p-8 text-center text-gray-500 text-sm">
        <RefreshCw size={16} class="animate-spin mx-auto mb-2" />
        Cargando credenciales...
      </div>
    {:else}
      <div class="space-y-4">
        {#each Object.entries(credentials) as [catKey, category] (catKey)}
          {@const Icon = categoryIcons[catKey] ?? Key}
          <div class="card p-0 overflow-hidden">
            <button
              class="w-full px-6 py-3 flex items-center justify-between bg-bg-page border-b border-border-light hover:bg-gray-50 transition-colors"
              onclick={() => toggleCategory(catKey)}
            >
              <div class="flex items-center gap-3">
                <Icon size={16} class="text-gray-500" />
                <span class="section-heading">{category.label}</span>
                <span class="text-xs text-gray-400">({category.items.length} claves)</span>
              </div>
              {#if expandedCat === catKey}<ChevronUp size={14} class="text-gray-400" />{:else}<ChevronDown size={14} class="text-gray-400" />{/if}
            </button>
            {#if expandedCat === catKey}
              <table class="table w-full">
                <thead>
                  <tr>
                    <th style="width:28%">CLAVE</th>
                    <th style="width:25%">DESCRIPCIÓN</th>
                    <th>VALOR</th>
                    <th style="width:80px">FUENTE</th>
                    <th style="width:100px"></th>
                  </tr>
                </thead>
                <tbody>
                  {#each category.items as item (item.key)}
                    <tr>
                      <td>
                        <div class="flex items-center gap-1.5">
                          {#if item.is_secret}<Lock size={10} class="text-amber-500 shrink-0" />{/if}
                          <span class="font-mono text-xs">{item.key}</span>
                        </div>
                      </td>
                      <td class="text-xs text-gray-500">{item.description}</td>
                      <td>
                        {#if credEditKey === item.key}
                          <div class="flex items-center gap-2">
                            <div class="relative flex-1">
                              <input
                                class="input w-full px-3 py-1.5 text-sm pr-8"
                                type={item.is_secret && !showSecretMap[item.key] ? 'password' : 'text'}
                                bind:value={credEditValue}
                                placeholder={item.is_set ? '(dejar vacío para no cambiar)' : 'Ingrese valor...'}
                              />
                              {#if item.is_secret}
                                <button type="button" class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400" onclick={() => toggleShowSecret(item.key)}>
                                  {#if showSecretMap[item.key]}<EyeOff size={14} />{:else}<Eye size={14} />{/if}
                                </button>
                              {/if}
                            </div>
                            <button class="btn-secondary btn-sm" onclick={() => { credEditKey = null; credEditValue = ''; }}>✕</button>
                            <button class="btn-accent btn-sm disabled:opacity-60" disabled={credSaving} onclick={() => saveCredential(item)}>
                              {#if credSaving}<RefreshCw size={12} class="animate-spin" />{:else}<Save size={12} />{/if}
                            </button>
                          </div>
                        {:else}
                          <div class="flex items-center gap-2">
                            {#if item.is_set}
                              {#if item.is_secret}
                                <span class="font-mono text-xs text-gray-400">••••••••</span>
                                <span class="text-[10px] text-gray-400">({item.raw_length} chars)</span>
                              {:else}
                                <span class="font-mono text-xs text-gray-700">{item.value}</span>
                              {/if}
                            {:else}
                              <span class="text-xs text-gray-300 italic">no configurado</span>
                            {/if}
                          </div>
                        {/if}
                      </td>
                      <td>
                        <span class="text-[10px] font-medium uppercase {item.source === 'database' ? 'text-emerald-600' : item.source === 'env' ? 'text-blue-600' : 'text-gray-300'}">{item.source}</span>
                      </td>
                      <td>
                        {#if credEditKey !== item.key}
                          <button class="btn-secondary btn-sm" onclick={() => startCredEdit(item)}>EDITAR</button>
                        {/if}
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            {/if}
          </div>
        {/each}
      </div>
    {/if}

  <!-- ═══════════ TAB: STRIPE ═══════════ -->
  {:else if activeTab === 'stripe'}
    <div class="space-y-6">
      <!-- Stripe Mode Toggle Card -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="section-heading flex items-center gap-2"><CreditCard size={16} /> MODO STRIPE</h3>
            <p class="text-xs text-gray-400 mt-1">Cambiar entre claves de prueba y producción</p>
          </div>
          {#if stripeModeLoading}
            <RefreshCw size={16} class="animate-spin text-gray-400" />
          {/if}
        </div>

        {#if stripeMode}
          <div class="flex items-center gap-6 mb-6">
            <!-- Toggle switch -->
            <div class="flex items-center gap-4">
              <span class="text-sm font-medium {stripeMode.mode === 'test' ? 'text-amber-600' : 'text-gray-400'}">TEST</span>
              <button
                class="relative w-14 h-7 rounded-full transition-colors {stripeMode.mode === 'live' ? 'bg-emerald-500' : 'bg-amber-400'} disabled:opacity-50"
                disabled={stripeToggling}
                onclick={toggleStripeMode}
              >
                <div class="absolute top-0.5 w-6 h-6 bg-white rounded-full shadow transition-transform {stripeMode.mode === 'live' ? 'translate-x-7' : 'translate-x-0.5'}"></div>
              </button>
              <span class="text-sm font-medium {stripeMode.mode === 'live' ? 'text-emerald-600' : 'text-gray-400'}">LIVE</span>
            </div>

            <!-- Status indicator -->
            <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg {stripeMode.mode === 'live' ? 'bg-emerald-50 border border-emerald-200' : 'bg-amber-50 border border-amber-200'}">
              {#if stripeMode.mode === 'live'}
                <CheckCircle size={14} class="text-emerald-600" />
                <span class="text-xs font-semibold text-emerald-700 uppercase">Producción</span>
              {:else}
                <AlertCircle size={14} class="text-amber-600" />
                <span class="text-xs font-semibold text-amber-700 uppercase">Pruebas</span>
              {/if}
            </div>
          </div>

          <!-- Active keys info -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div class="bg-bg-page border border-border-light rounded p-3">
              <div class="text-[10px] text-gray-400 uppercase font-semibold mb-1">Secret Key (prefijo)</div>
              <div class="font-mono text-sm text-gray-700">{stripeMode.active_secret_key_prefix || '—'}</div>
            </div>
            <div class="bg-bg-page border border-border-light rounded p-3">
              <div class="text-[10px] text-gray-400 uppercase font-semibold mb-1">Publishable Key</div>
              <div class="font-mono text-xs text-gray-700 truncate">{stripeMode.active_publishable_key || '—'}</div>
            </div>
          </div>

          <!-- Keys availability -->
          <div class="flex items-center gap-6 text-xs mb-6">
            <div class="flex items-center gap-1.5">
              {#if stripeMode.has_test_keys}<CheckCircle size={12} class="text-emerald-500" />{:else}<AlertCircle size={12} class="text-gray-300" />{/if}
              <span class="{stripeMode.has_test_keys ? 'text-gray-700' : 'text-gray-400'}">Claves TEST</span>
            </div>
            <div class="flex items-center gap-1.5">
              {#if stripeMode.has_live_keys}<CheckCircle size={12} class="text-emerald-500" />{:else}<AlertCircle size={12} class="text-gray-300" />{/if}
              <span class="{stripeMode.has_live_keys ? 'text-gray-700' : 'text-gray-400'}">Claves LIVE</span>
            </div>
          </div>

          <!-- Optional key override forms -->
          <details class="group">
            <summary class="cursor-pointer text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1 mb-3">
              <ChevronDown size={12} class="group-open:rotate-180 transition-transform" />
              Configurar claves manualmente
            </summary>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
              <!-- Test Keys -->
              <div class="space-y-3 p-4 border border-amber-200 bg-amber-50/50 rounded-lg">
                <h4 class="text-xs font-semibold text-amber-700 uppercase flex items-center gap-1"><AlertCircle size={12} /> Claves TEST</h4>
                <div>
                  <label class="label text-[10px]" for="sk-test">Secret Key (sk_test_...)</label>
                  <input id="sk-test" type="password" class="input w-full px-3 py-1.5 text-xs" placeholder="sk_test_..." bind:value={stripeTestKeys.secret} />
                </div>
                <div>
                  <label class="label text-[10px]" for="pk-test">Publishable Key (pk_test_...)</label>
                  <input id="pk-test" type="text" class="input w-full px-3 py-1.5 text-xs" placeholder="pk_test_..." bind:value={stripeTestKeys.publishable} />
                </div>
                <div>
                  <label class="label text-[10px]" for="wh-test">Webhook Secret</label>
                  <input id="wh-test" type="password" class="input w-full px-3 py-1.5 text-xs" placeholder="whsec_..." bind:value={stripeTestKeys.webhook} />
                </div>
              </div>
              <!-- Live Keys -->
              <div class="space-y-3 p-4 border border-emerald-200 bg-emerald-50/50 rounded-lg">
                <h4 class="text-xs font-semibold text-emerald-700 uppercase flex items-center gap-1"><CheckCircle size={12} /> Claves LIVE</h4>
                <div>
                  <label class="label text-[10px]" for="sk-live">Secret Key (sk_live_... / rk_live_...)</label>
                  <input id="sk-live" type="password" class="input w-full px-3 py-1.5 text-xs" placeholder="sk_live_..." bind:value={stripeLiveKeys.secret} />
                </div>
                <div>
                  <label class="label text-[10px]" for="pk-live">Publishable Key (pk_live_...)</label>
                  <input id="pk-live" type="text" class="input w-full px-3 py-1.5 text-xs" placeholder="pk_live_..." bind:value={stripeLiveKeys.publishable} />
                </div>
                <div>
                  <label class="label text-[10px]" for="wh-live">Webhook Secret</label>
                  <input id="wh-live" type="password" class="input w-full px-3 py-1.5 text-xs" placeholder="whsec_..." bind:value={stripeLiveKeys.webhook} />
                </div>
              </div>
            </div>
            <p class="text-[10px] text-gray-400 mt-2 italic">Las claves se guardan al cambiar de modo. Déjelas vacías para mantener las actuales.</p>
          </details>
        {:else}
          <p class="text-sm text-gray-400 italic">No se pudo obtener el estado de Stripe</p>
        {/if}
      </div>
    </div>

  <!-- ═══════════ TAB: SISTEMA ═══════════ -->
  {:else if activeTab === 'system'}
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
                            <button type="button" class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400" onclick={() => toggleShowSecret(entry.key)}>
                              {#if showSecretMap[entry.key]}<EyeOff size={14} />{:else}<Eye size={14} />{/if}
                            </button>
                          {/if}
                        </div>
                        <button class="btn-secondary btn-sm" onclick={cancelEdit}>CANCELAR</button>
                        <button class="btn-accent btn-sm disabled:opacity-60" disabled={savingKey === entry.key} onclick={() => saveEdit(entry.key)}>
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

  <!-- ═══════════ TAB: ODOO ═══════════ -->
  {:else if activeTab === 'odoo'}
    <div class="card">
      <div class="flex items-center justify-between mb-5">
        <h3 class="section-heading">CONFIGURACIÓN Sajet</h3>
        {#if !showOdooForm}
          <button class="btn-secondary px-4 py-2" onclick={startOdooEdit}>EDITAR Sajet</button>
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
              {odooLoading ? 'GUARDANDO...' : 'GUARDAR Sajet'}
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
  {/if}
</div>
