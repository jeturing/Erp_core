<script lang="ts">
  import { onMount } from 'svelte';
  import { apiKeysApi } from '../lib/api';
  import type { ApiKeyItem, ApiKeyStatus, ApiKeyTier, TierInfo } from '../lib/api/apiKeys';
  import { toasts } from '../lib/stores';
  import {
    Key, Plus, RefreshCw, Search, Copy, Eye, EyeOff, RotateCw,
    Trash2, ChevronLeft, ChevronRight, Filter, Shield, Zap,
    Clock, Activity, AlertTriangle, Check, X,
  } from 'lucide-svelte';

  let keys: ApiKeyItem[] = [];
  let total = 0;
  let loading = true;
  let currentPage = 1;
  const PAGE_SIZE = 20;
  let statusFilter: ApiKeyStatus | '' = '';
  let tierFilter: ApiKeyTier | '' = '';
  let search = '';
  let tiers: TierInfo[] = [];

  // Create modal
  let showCreate = false;
  let createName = '';
  let createDesc = '';
  let createScope: 'read_only' | 'read_write' | 'admin' = 'read_only';
  let createTier: ApiKeyTier = 'standard';
  let createExpiresDays: number | null = null;
  let creating = false;

  // New key reveal
  let revealedSecret: string | null = null;
  let copiedSecret = false;

  // Confirm modals
  let confirmAction: 'rotate' | 'revoke' | null = null;
  let confirmKeyId: string | null = null;
  let confirmKeyName = '';

  async function loadKeys() {
    loading = true;
    try {
      const res = await apiKeysApi.list({
        status_filter: statusFilter || undefined,
        tier_filter: tierFilter || undefined,
        page: currentPage,
        per_page: PAGE_SIZE,
      });
      keys = res.data ?? [];
      total = res.total ?? 0;
    } catch (e: any) {
      toasts.error(e.message ?? 'Error cargando API keys');
    } finally {
      loading = false;
    }
  }

  async function loadTiers() {
    try {
      const res = await apiKeysApi.getTiers();
      tiers = res.tiers ?? [];
    } catch { /* ignore */ }
  }

  async function handleCreate() {
    if (!createName.trim()) return;
    creating = true;
    try {
      const res = await apiKeysApi.create({
        name: createName.trim(),
        description: createDesc.trim() || undefined,
        scope: createScope,
        tier: createTier,
        expires_in_days: createExpiresDays ?? undefined,
      });
      if (res.data?.api_key) {
        revealedSecret = res.data.api_key;
      }
      showCreate = false;
      createName = '';
      createDesc = '';
      createScope = 'read_only';
      createTier = 'standard';
      createExpiresDays = null;
      toasts.success('API Key creada exitosamente');
      await loadKeys();
    } catch (e: any) {
      toasts.error(e.message ?? 'Error creando API key');
    } finally {
      creating = false;
    }
  }

  async function handleRotate(keyId: string) {
    try {
      const res = await apiKeysApi.rotate(keyId);
      if (res.data?.api_key) {
        revealedSecret = res.data.api_key;
      }
      confirmAction = null;
      toasts.success('API Key rotada — guarda la nueva clave');
      await loadKeys();
    } catch (e: any) {
      toasts.error(e.message ?? 'Error rotando key');
    }
  }

  async function handleRevoke(keyId: string) {
    try {
      await apiKeysApi.revoke(keyId);
      confirmAction = null;
      toasts.success('API Key revocada');
      await loadKeys();
    } catch (e: any) {
      toasts.error(e.message ?? 'Error revocando key');
    }
  }

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text).then(() => {
      copiedSecret = true;
      setTimeout(() => (copiedSecret = false), 2000);
    });
  }

  function statusBadge(status: ApiKeyStatus): string {
    switch (status) {
      case 'active': return 'badge-success';
      case 'revoked': return 'badge-error';
      case 'expired': return 'badge-warning';
      case 'rotated': return 'badge-info';
      default: return 'badge-neutral';
    }
  }

  function tierBadge(tier: ApiKeyTier): string {
    switch (tier) {
      case 'enterprise': case 'unlimited': return 'badge-warning';
      case 'premium': return 'badge-info';
      default: return 'badge-neutral';
    }
  }

  function formatDate(iso: string | null): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('es-DO', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  }

  function maskKey(keyId: string): string {
    if (keyId.length <= 12) return keyId;
    return keyId.substring(0, 12) + '••••••••';
  }

  $: totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  $: filtered = keys.filter(k =>
    !search || k.name.toLowerCase().includes(search.toLowerCase()) || k.key_id.toLowerCase().includes(search.toLowerCase())
  );

  onMount(() => {
    loadKeys();
    loadTiers();
  });
</script>

<!-- Secret reveal banner -->
{#if revealedSecret}
  <div class="mx-6 mt-4 p-4 bg-amber-900/30 border border-amber-600/50 rounded-lg">
    <div class="flex items-start gap-3">
      <AlertTriangle class="text-amber-400 shrink-0 mt-0.5" size={20} />
      <div class="flex-1 min-w-0">
        <p class="text-amber-200 font-semibold text-sm mb-1">⚠️ Guarda esta clave ahora. No se volverá a mostrar.</p>
        <div class="flex items-center gap-2 bg-black/30 rounded px-3 py-2 font-mono text-xs text-gray-200 overflow-x-auto">
          <span class="truncate select-all">{revealedSecret}</span>
          <button type="button" class="shrink-0 p-1 hover:text-white" onclick={() => copyToClipboard(revealedSecret!)}>
            {#if copiedSecret}<Check size={14} class="text-green-400" />{:else}<Copy size={14} />{/if}
          </button>
        </div>
      </div>
      <button type="button" class="p-1 text-gray-400 hover:text-white" onclick={() => (revealedSecret = null)}>
        <X size={16} />
      </button>
    </div>
  </div>
{/if}

<div class="p-6">
  <!-- Header -->
  <div class="flex items-center justify-between mb-6">
    <div>
      <h1 class="page-title flex items-center gap-2"><Key size={22} /> API Keys</h1>
      <p class="page-subtitle mt-1">Gestión de claves API estilo Stripe — rate limiting, rotación y auditoría</p>
    </div>
    <div class="flex items-center gap-2">
      <button class="btn-ghost btn-sm" onclick={loadKeys}><RefreshCw size={14} /> Recargar</button>
      <button class="btn-accent btn-sm" onclick={() => (showCreate = true)}><Plus size={14} /> Nueva Key</button>
    </div>
  </div>

  <!-- Filters -->
  <div class="flex flex-wrap items-center gap-3 mb-4">
    <div class="relative flex-1 min-w-[200px] max-w-sm">
      <Search size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
      <input type="text" bind:value={search} placeholder="Buscar por nombre o key_id…" class="input-field pl-9 w-full" />
    </div>
    <select bind:value={statusFilter} onchange={() => { currentPage = 1; loadKeys(); }} class="input-field text-sm w-32">
      <option value="">Estado</option>
      <option value="active">Activa</option>
      <option value="revoked">Revocada</option>
      <option value="expired">Expirada</option>
      <option value="rotated">Rotada</option>
    </select>
    <select bind:value={tierFilter} onchange={() => { currentPage = 1; loadKeys(); }} class="input-field text-sm w-32">
      <option value="">Tier</option>
      <option value="free">Free</option>
      <option value="standard">Standard</option>
      <option value="premium">Premium</option>
      <option value="enterprise">Enterprise</option>
      <option value="unlimited">Unlimited</option>
    </select>
  </div>

  <!-- Table -->
  {#if loading}
    <div class="flex justify-center py-12"><div class="spinner"></div></div>
  {:else if filtered.length === 0}
    <div class="empty-state">
      <Key size={40} class="text-gray-600 mb-2" />
      <p class="text-gray-400">No hay API keys{search ? ' que coincidan con la búsqueda' : ''}</p>
    </div>
  {:else}
    <div class="overflow-x-auto">
      <table class="data-table w-full">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Key ID</th>
            <th>Estado</th>
            <th>Tier</th>
            <th>Scope</th>
            <th class="text-right">Uso hoy</th>
            <th class="text-right">Uso mes</th>
            <th>Último uso</th>
            <th>Creada</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {#each filtered as key}
            <tr class="hover:bg-white/[0.02]">
              <td>
                <div class="font-medium text-sm">{key.name}</div>
                {#if key.description}<div class="text-xs text-gray-500 truncate max-w-[200px]">{key.description}</div>{/if}
              </td>
              <td><code class="text-xs font-mono text-gray-400">{maskKey(key.key_id)}</code></td>
              <td><span class="badge {statusBadge(key.status)}">{key.status}</span></td>
              <td><span class="badge {tierBadge(key.tier)}">{key.tier}</span></td>
              <td><span class="text-xs text-gray-400">{key.scope.replace('_', ' ')}</span></td>
              <td class="text-right tabular-nums text-sm">{key.usage.today.toLocaleString()}</td>
              <td class="text-right tabular-nums text-sm">{key.usage.month.toLocaleString()}</td>
              <td class="text-xs text-gray-500">{formatDate(key.last_used_at)}</td>
              <td class="text-xs text-gray-500">{formatDate(key.created_at)}</td>
              <td>
                {#if key.status === 'active'}
                  <div class="flex items-center gap-1">
                    <button class="btn-ghost btn-xs" title="Rotar" onclick={() => { confirmAction = 'rotate'; confirmKeyId = key.key_id; confirmKeyName = key.name; }}>
                      <RotateCw size={13} />
                    </button>
                    <button class="btn-ghost btn-xs text-error" title="Revocar" onclick={() => { confirmAction = 'revoke'; confirmKeyId = key.key_id; confirmKeyName = key.name; }}>
                      <Trash2 size={13} />
                    </button>
                  </div>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    {#if totalPages > 1}
      <div class="flex items-center justify-between mt-4 text-sm text-gray-500">
        <span>Mostrando {(currentPage - 1) * PAGE_SIZE + 1}–{Math.min(currentPage * PAGE_SIZE, total)} de {total}</span>
        <div class="flex items-center gap-1">
          <button class="btn-ghost btn-xs" disabled={currentPage <= 1} onclick={() => { currentPage--; loadKeys(); }}>
            <ChevronLeft size={14} />
          </button>
          <span class="px-2">{currentPage} / {totalPages}</span>
          <button class="btn-ghost btn-xs" disabled={currentPage >= totalPages} onclick={() => { currentPage++; loadKeys(); }}>
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
    {/if}
  {/if}
</div>

<!-- Create Modal -->
{#if showCreate}
  <div class="modal-backdrop" onclick={() => (showCreate = false)}>
    <div class="modal-panel max-w-lg" onclick={(e) => e.stopPropagation()}>
      <h2 class="text-lg font-semibold mb-4 flex items-center gap-2"><Key size={18} /> Nueva API Key</h2>
      <div class="space-y-4">
        <div>
          <label class="label-field">Nombre *</label>
          <input type="text" bind:value={createName} class="input-field w-full" placeholder="Mi integración" />
        </div>
        <div>
          <label class="label-field">Descripción</label>
          <input type="text" bind:value={createDesc} class="input-field w-full" placeholder="Opcional" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label-field">Scope</label>
            <select bind:value={createScope} class="input-field w-full">
              <option value="read_only">Solo lectura</option>
              <option value="read_write">Lectura/Escritura</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div>
            <label class="label-field">Tier</label>
            <select bind:value={createTier} class="input-field w-full">
              <option value="free">Free</option>
              <option value="standard">Standard</option>
              <option value="premium">Premium</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>
        </div>
        <div>
          <label class="label-field">Expiración (días)</label>
          <input type="number" bind:value={createExpiresDays} class="input-field w-full" placeholder="Sin expiración" min="1" />
        </div>
      </div>
      <div class="flex justify-end gap-2 mt-6">
        <button class="btn-ghost btn-sm" onclick={() => (showCreate = false)}>Cancelar</button>
        <button class="btn-accent btn-sm" disabled={creating || !createName.trim()} onclick={handleCreate}>
          {#if creating}Creando…{:else}Crear Key{/if}
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Confirm Modal -->
{#if confirmAction && confirmKeyId}
  <div class="modal-backdrop" onclick={() => (confirmAction = null)}>
    <div class="modal-panel max-w-sm" onclick={(e) => e.stopPropagation()}>
      <h2 class="text-lg font-semibold mb-2">
        {confirmAction === 'rotate' ? '🔄 Rotar' : '🗑️ Revocar'} API Key
      </h2>
      <p class="text-sm text-gray-400 mb-4">
        {#if confirmAction === 'rotate'}
          Se generará una nueva clave para <strong>{confirmKeyName}</strong>. La clave anterior dejará de funcionar.
        {:else}
          Se revocará permanentemente <strong>{confirmKeyName}</strong>. Esta acción no se puede deshacer.
        {/if}
      </p>
      <div class="flex justify-end gap-2">
        <button class="btn-ghost btn-sm" onclick={() => (confirmAction = null)}>Cancelar</button>
        <button
          class={confirmAction === 'revoke' ? 'btn-error btn-sm' : 'btn-accent btn-sm'}
          onclick={() => {
            if (confirmAction === 'rotate') handleRotate(confirmKeyId!);
            else handleRevoke(confirmKeyId!);
          }}
        >
          {confirmAction === 'rotate' ? 'Rotar' : 'Revocar'}
        </button>
      </div>
    </div>
  </div>
{/if}
