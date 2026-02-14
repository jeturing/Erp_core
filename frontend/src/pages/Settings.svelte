<script lang="ts">
  import { onMount } from 'svelte';
  import { Button, Card, Input, Modal, Spinner } from '../lib/components';
  import { settingsApi } from '../lib/api';
  import { addToast } from '../lib/stores';
  import type { OdooSettingsResponse, SettingsEntry } from '../lib/types';

  let loading = true;
  let saving = false;
  let error = '';
  let search = '';

  let settings: SettingsEntry[] = [];
  let odooConfig: OdooSettingsResponse['config'] | null = null;

  let showEditModal = false;
  let editingKey = '';
  let editingValue = '';
  let editingDescription = '';

  async function loadData() {
    loading = true;
    error = '';
    try {
      const [settingsData, odooData] = await Promise.all([settingsApi.getAll(), settingsApi.getOdooCurrent()]);
      settings = settingsData.configs;
      odooConfig = odooData.config;
    } catch (err) {
      error = err instanceof Error ? err.message : 'No se pudo cargar configuraciones';
      addToast(error, 'error');
    } finally {
      loading = false;
    }
  }

  onMount(loadData);

  function openEdit(entry: SettingsEntry) {
    editingKey = entry.key;
    editingValue = entry.is_secret ? '' : entry.value;
    editingDescription = entry.description || '';
    showEditModal = true;
  }

  async function saveConfig() {
    if (!editingKey) return;
    saving = true;
    error = '';
    try {
      await settingsApi.updateConfig(editingKey, editingValue, editingDescription || undefined);
      showEditModal = false;
      addToast(`Configuracion ${editingKey} actualizada`, 'success');
      await loadData();
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'No se pudo guardar configuracion', 'error');
    } finally {
      saving = false;
    }
  }

  async function saveOdooConfig() {
    if (!odooConfig) return;
    saving = true;
    error = '';
    try {
      await settingsApi.updateOdooConfig({
        admin_login: odooConfig.admin_login,
        admin_password: odooConfig.admin_password,
        master_password: odooConfig.master_password,
        db_user: odooConfig.db_user,
        db_password: odooConfig.db_password,
        default_lang: odooConfig.default_lang,
        default_country: odooConfig.default_country,
        base_domain: odooConfig.base_domain,
        template_db: odooConfig.template_db,
      });
      addToast('Configuracion Odoo actualizada', 'success');
      await loadData();
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'No se pudo actualizar configuracion Odoo', 'error');
    } finally {
      saving = false;
    }
  }

  $: filteredSettings = settings.filter((entry) => {
    const text = `${entry.key} ${entry.category || ''} ${entry.description || ''}`.toLowerCase();
    return text.includes(search.toLowerCase().trim());
  });
</script>

<div class="p-6 lg:p-8 space-y-6">
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold text-white">Settings</h1>
      <p class="text-secondary-400 mt-1">Configuracion global del sistema y parametros Odoo</p>
    </div>
    <Button variant="secondary" on:click={loadData}>Recargar</Button>
  </div>

  {#if error}
    <Card><p class="text-error text-sm">{error}</p></Card>
  {/if}

  {#if loading}
    <div class="py-16 flex justify-center"><Spinner size="lg" /></div>
  {:else}
    <Card title="Configuracion Odoo" subtitle="/api/settings/odoo/current">
      {#if odooConfig}
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input label="Admin Login" bind:value={odooConfig.admin_login} />
          <Input label="Admin Password" type="password" bind:value={odooConfig.admin_password} />
          <Input label="Master Password" type="password" bind:value={odooConfig.master_password} />
          <Input label="DB User" bind:value={odooConfig.db_user} />
          <Input label="DB Password" type="password" bind:value={odooConfig.db_password} />
          <Input label="Default Lang" bind:value={odooConfig.default_lang} />
          <Input label="Default Country" bind:value={odooConfig.default_country} />
          <Input label="Base Domain" bind:value={odooConfig.base_domain} />
          <Input label="Template DB" bind:value={odooConfig.template_db} />
        </div>
        <div class="mt-4">
          <Button variant="primary" on:click={saveOdooConfig} loading={saving}>Guardar configuracion Odoo</Button>
        </div>
      {/if}
    </Card>

    <Card title="Configuraciones del sistema" subtitle="/api/settings" padding="none">
      <div class="p-4 border-b border-surface-border">
        <Input label="Buscar clave" placeholder="ODOO_, STRIPE_, APP_..." bind:value={search} />
      </div>
      <div class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr>
              <th>Clave</th>
              <th>Categoria</th>
              <th>Valor</th>
              <th>Editable</th>
              <th>Accion</th>
            </tr>
          </thead>
          <tbody>
            {#each filteredSettings as item}
              <tr>
                <td class="font-mono text-xs text-secondary-200">{item.key}</td>
                <td class="text-secondary-300">{item.category || '-'}</td>
                <td class="text-secondary-300">{item.is_secret ? '********' : item.value}</td>
                <td class="text-secondary-300">{item.is_editable === false ? 'no' : 'si'}</td>
                <td>
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={item.is_editable === false}
                    on:click={() => openEdit(item)}
                  >
                    Editar
                  </Button>
                </td>
              </tr>
            {:else}
              <tr>
                <td colspan="5" class="text-center text-secondary-500 py-8">Sin resultados</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </Card>
  {/if}
</div>

<Modal
  bind:isOpen={showEditModal}
  title={`Editar configuracion: ${editingKey}`}
  confirmText="Guardar"
  on:confirm={saveConfig}
  on:close={() => (showEditModal = false)}
  loading={saving}
>
  <div class="space-y-4">
    <Input label="Valor" bind:value={editingValue} required />
    <Input label="Descripcion" bind:value={editingDescription} />
  </div>
</Modal>
