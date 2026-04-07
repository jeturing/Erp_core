<script lang="ts">
  import { onMount } from 'svelte';
  import { neuralUsersApi } from '../lib/api/neuralUsers';
  import type { NeuralUserItem, UserTokenItem } from '../lib/api/neuralUsers';
  import { toasts } from '../lib/stores/toast';
  import { formatDate } from '../lib/utils/formatters';
  import { 
    Search, Shield, Users, Briefcase, RefreshCcw, 
    Key, ShieldCheck, ShieldAlert, Trash2, Zap, 
    AtSign, Calendar, LogIn, ExternalLink
  } from 'lucide-svelte';

  let searchQuery = $state('');
  let users = $state<NeuralUserItem[]>([]);
  let loadingSearch = $state(false);

  // Token management state
  let selectedUser = $state<NeuralUserItem | null>(null);
  let tokens = $state<UserTokenItem[]>([]);
  let loadingTokens = $state(false);
  let showTokenModal = $state(false);

  async function handleSearch() {
    if (!searchQuery.trim()) return;
    loadingSearch = true;
    try {
      const usersList = await neuralUsersApi.search(searchQuery);
      users = usersList;
      if (users.length === 0) {
        toasts.info('No se encontraron usuarios matching');
      }
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error en la búsqueda');
    } finally {
      loadingSearch = false;
    }
  }

  async function openTokens(user: NeuralUserItem) {
    selectedUser = user;
    showTokenModal = true;
    await loadTokens();
  }

  async function loadTokens() {
    if (!selectedUser) return;
    loadingTokens = true;
    try {
      const tokensList = await neuralUsersApi.getTokens(selectedUser.type, selectedUser.id);
      tokens = tokensList;
    } catch (e: any) {
      toasts.error('Error cargando tokens');
    } finally {
      loadingTokens = false;
    }
  }

  async function generateToken(tokenType: 'verification' | 'refresh') {
    if (!selectedUser) return;
    try {
      const res = await neuralUsersApi.generateToken(selectedUser.type, selectedUser.id, tokenType);
      if (res.success) {
        toasts.success(`Token ${tokenType} generado: ${res.data.token}`);
        await loadTokens();
      }
    } catch (e: any) {
      toasts.error('Error generando token');
    }
  }

  async function revokeToken(tokenId: number) {
    if (!confirm('¿Revocar este token permanentemente?')) return;
    try {
      const res = await neuralUsersApi.revokeToken(tokenId);
      if (res.success) {
        toasts.success('Token revocado');
        await loadTokens();
      }
    } catch (e: any) {
      toasts.error('Error revocando token');
    }
  }

  async function toggleBypassMfa(user: NeuralUserItem) {
    const action = user.onboarding_bypass ? 'desactivar' : 'activar';
    if (!confirm(`¿${action} bypass de MFA/Onboarding para ${user.email}? Esto también reseteará su TOTP si está activo.`)) return;
    
    try {
      const res = await neuralUsersApi.toggleBypassMfa(user.type, user.id);
      if (res.success) {
        toasts.success(`Bypass ${user.onboarding_bypass ? 'desactivado' : 'activado'} para ${user.email}`);
        // Refresh this user in the list
        await handleSearch();
      }
    } catch (e: any) {
      toasts.error('Error cambiando bypass');
    }
  }

  const typeLabels = {
    admin: { label: 'ADMIN', color: 'bg-terracotta/20 text-terracotta', icon: Shield },
    customer: { label: 'TENANT', color: 'bg-emerald-500/20 text-emerald-400', icon: Users },
    partner: { label: 'PARTNER', color: 'bg-blue-500/20 text-blue-400', icon: Briefcase }
  };

  onMount(() => {
    // Optional: search for all if needed
  });
</script>

<div class="space-y-6">
  <!-- Header con Estética Neural -->
  <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-charcoal to-charcoal-light border border-border-dark p-8">
    <div class="absolute top-0 right-0 p-4 opacity-10">
      <Zap size={120} strokeWidth={0.5} />
    </div>
    <div class="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
      <div>
        <h1 class="text-3xl font-bold text-text-light tracking-tight flex items-center gap-3">
          <Zap class="text-accent" size={28} />
          NEURAL CENTER
        </h1>
        <p class="text-gray-400 mt-2 max-w-xl">
          Gestión centralizada de identidades administrativas, tenants y partners. 
          Control maestro de credenciales, bypass de seguridad y auditoría de sesiones.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <div class="relative group">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-accent transition-colors" size={18} />
          <input 
            type="text" 
            placeholder="Email, nombre o ID..." 
            class="input pl-10 pr-32 py-3 w-full md:w-80 shadow-2xl border-border-dark focus:border-accent"
            bind:value={searchQuery}
            onkeydown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button 
            class="absolute right-2 top-1/2 -translate-y-1/2 btn-accent px-4 py-1.5 text-xs font-bold uppercase"
            onclick={handleSearch}
            disabled={loadingSearch}
          >
            {loadingSearch ? 'BUSCANDO...' : 'BUSCAR'}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Search Results -->
  <div class="grid grid-cols-1 gap-4">
    {#if loadingSearch}
      <div class="card p-12 text-center animate-pulse">
        <div class="flex flex-col items-center gap-4">
          <RefreshCcw class="animate-spin text-accent" size={32} />
          <p class="text-gray-400 font-medium">Escaneando base de datos neural...</p>
        </div>
      </div>
    {:else if users.length > 0}
      {#each users as user}
        {@const IconComp = typeLabels[user.type].icon}
        <div class="card p-6 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 border-l-4 {user.is_active ? 'border-l-accent' : 'border-l-gray-600'} hover:border-l-terracotta transition-all">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl flex items-center justify-center {typeLabels[user.type].color}">
              <IconComp size={24} />
            </div>
            <div>
              <div class="flex items-center gap-2">
                <span class="text-lg font-bold text-text-light">{user.display_name}</span>
                <span class="text-[10px] font-black px-2 py-0.5 rounded-full {typeLabels[user.type].color}">
                  {typeLabels[user.type].label}
                </span>
                {#if user.onboarding_bypass}
                  <span class="bg-terracotta/20 text-terracotta text-[10px] font-black px-2 py-0.5 rounded-full flex items-center gap-1">
                    <Zap size={10} /> BYPASS ACTIVO
                  </span>
                {/if}
              </div>
              <div class="flex items-center gap-4 mt-1 text-sm text-gray-400">
                <span class="flex items-center gap-1"><AtSign size={14} /> {user.email}</span>
                <span class="flex items-center gap-1"><Calendar size={14} /> ID: {user.id}</span>
                {#if user.last_login_at}
                  <span class="flex items-center gap-1"><LogIn size={14} /> login: {formatDate(user.last_login_at)}</span>
                {/if}
              </div>
            </div>
          </div>

          <div class="flex items-center gap-3 w-full lg:w-auto">
            <button 
              class="btn-secondary flex-1 lg:flex-none flex items-center justify-center gap-2 py-2 px-4 text-xs font-bold"
              onclick={() => toggleBypassMfa(user)}
              title="Alternar bypass de onboarding y MFA"
            >
              {#if user.onboarding_bypass}
                <ShieldAlert size={16} class="text-terracotta" />
                QUITAR BYPASS
              {:else}
                <ShieldCheck size={16} class="text-accent" />
                ACTIVAR BYPASS
              {/if}
            </button>

            <button 
              class="btn-accent flex-1 lg:flex-none flex items-center justify-center gap-2 py-2 px-4 text-xs font-bold"
              onclick={() => openTokens(user)}
            >
              <Key size={16} />
              GESTIONAR TOKENS
            </button>

            <button 
              class="bg-gray-700 hover:bg-gray-600 text-text-light lg:p-2.5 rounded-lg transition-colors flex items-center justify-center"
              title="Ver Detalles Completos"
            >
              <ExternalLink size={18} />
            </button>
          </div>
        </div>
      {/each}
    {:else}
      <div class="card p-12 text-center bg-transparent border-dashed border-2 border-border-dark">
        <div class="flex flex-col items-center gap-4 text-gray-600">
          <Users size={48} strokeWidth={1} />
          <p class="font-medium">Ingresa un término de búsqueda para localizar usuarios en el ecosistema Sajet</p>
        </div>
      </div>
    {/if}
  </div>
</div>

<!-- Token Modal UI -->
{#if showTokenModal && selectedUser}
  <div class="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
    <div class="bg-charcoal border border-border-dark rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">
      <div class="p-6 border-b border-border-dark flex items-center justify-between bg-charcoal-light">
        <div>
          <h2 class="text-xl font-bold text-text-light flex items-center gap-2">
            <Key size={20} class="text-accent" />
            Control Maestro de Tokens
          </h2>
          <p class="text-gray-400 text-sm mt-1">Usuario: {selectedUser.email}</p>
        </div>
        <button class="text-gray-500 hover:text-text-light" onclick={() => showTokenModal = false}>✕</button>
      </div>

      <div class="flex-1 overflow-y-auto p-6 space-y-8">
        <!-- Actions -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="p-4 rounded-xl border border-accent/20 bg-accent/5 flex flex-col gap-3">
            <div class="font-bold text-accent text-sm flex items-center gap-2 uppercase tracking-widest">
              <Zap size={14} /> Token de Verificación
            </div>
            <p class="text-xs text-gray-400">Genera un token de 6 dígitos tipo "Steam Guard" para verificación de email o bypass manual de login.</p>
            <button 
              class="btn-accent w-full py-2 font-bold uppercase text-xs mt-2"
              onclick={() => generateToken('verification')}
            >
              Generar Nueva Clave
            </button>
          </div>

          <div class="p-4 rounded-xl border border-blue-500/20 bg-blue-500/5 flex flex-col gap-3">
            <div class="font-bold text-blue-400 text-sm flex items-center gap-2 uppercase tracking-widest">
              <RefreshCcw size={14} /> Token de Sesión (Refresh)
            </div>
            <p class="text-xs text-gray-400">Genera un long-lived refresh token para persistencia de sesión. Útil para troubleshoot de autenticación.</p>
            <button 
              class="bg-blue-600 hover:bg-blue-500 text-white rounded-lg w-full py-2 font-bold uppercase text-xs mt-2 transition-colors"
              onclick={() => generateToken('refresh')}
            >
              Generar Refresh Token
            </button>
          </div>
        </div>

        <!-- Token list -->
        <div>
          <h3 class="text-sm font-black text-gray-500 uppercase tracking-widest mb-4">Tokens Activos en BDA</h3>
          {#if loadingTokens}
            <p class="text-center text-gray-500 py-8 italic animate-pulse">Consultando el historial de credenciales...</p>
          {:else if tokens.length > 0}
            <div class="space-y-3">
              {#each tokens as token}
                <div class="bg-charcoal-light rounded-xl border border-border-dark p-4 flex items-center justify-between group">
                  <div class="flex items-center gap-4">
                    <div class="w-10 h-10 rounded-lg flex items-center justify-center {token.type === 'verification' ? 'bg-accent/10 text-accent' : 'bg-blue-500/10 text-blue-400'}">
                      {#if token.type === 'verification'}<ShieldCheck size={20} />{:else}<RefreshCcw size={20} />{/if}
                    </div>
                    <div>
                      <div class="flex items-center gap-2">
                        <code class="text-lg font-mono font-bold text-text-light">{token.token}</code>
                        <span class="text-[10px] font-black uppercase text-gray-500 bg-black/30 px-2 py-0.5 rounded">
                          {token.type}
                        </span>
                      </div>
                      <div class="text-[10px] text-gray-500 mt-1 uppercase">
                        Expira: {formatDate(token.expires_at)} • Creado: {formatDate(token.created_at)}
                      </div>
                    </div>
                  </div>
                  
                  <button 
                    class="p-2 text-gray-500 hover:text-terracotta hover:bg-terracotta/10 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                    onclick={() => revokeToken(token.id)}
                    title="Revocar Token"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              {/each}
            </div>
          {:else}
            <div class="p-12 border-2 border-dashed border-border-dark rounded-xl text-center text-gray-600">
              No hay credenciales temporales activas para este usuario.
            </div>
          {/if}
        </div>
      </div>
      
      <div class="p-6 border-t border-border-dark bg-charcoal-light text-right">
        <button class="btn-secondary px-8 py-2 font-bold uppercase" onclick={() => showTokenModal = false}>CERRAR</button>
      </div>
    </div>
  </div>
{/if}

<style>
  /* Neural aesthetic additions */
  .card:hover {
    box-shadow: 0 0 20px rgba(0, 255, 159, 0.05);
    background-color: rgba(43, 43, 43, 0.8);
  }
</style>
