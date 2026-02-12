<script lang="ts">
  import { auth, currentUser } from '../lib/stores';
  import { Button, Card, Spinner } from '../lib/components';
  import { onMount } from 'svelte';
  import { api } from '../lib/api';
  
  interface DomainInfo {
    id: number;
    external_domain: string;
    sajet_subdomain: string;
    verification_status: string;
    is_active: boolean;
    ssl_status: string;
  }
  
  let domains: DomainInfo[] = [];
  let loading = true;
  let error = '';
  
  onMount(async () => {
    await loadDomains();
  });
  
  async function loadDomains() {
    loading = true;
    try {
      const response = await api.get<{ items: DomainInfo[] }>('/api/domains/my-domains');
      domains = response.items || [];
    } catch (e) {
      // No hay dominios todavía
      domains = [];
    } finally {
      loading = false;
    }
  }
  
  function handleLogout() {
    auth.logout();
    window.location.hash = '#/login';
  }
</script>

<div class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
  <!-- Header -->
  <header class="bg-slate-800/50 border-b border-slate-700 backdrop-blur-sm sticky top-0 z-10">
    <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-emerald-500 flex items-center justify-center">
          <span class="text-slate-900 font-bold text-xl">J</span>
        </div>
        <div>
          <span class="text-xl font-bold text-white">Portal de Cliente</span>
          <p class="text-sm text-slate-400">Jeturing ERP</p>
        </div>
      </div>
      
      <div class="flex items-center gap-4">
        <div class="text-right">
          <p class="text-sm font-medium text-white">{$currentUser?.email || 'Usuario'}</p>
          <p class="text-xs text-emerald-400">{$currentUser?.company_name || 'Mi Empresa'}</p>
        </div>
        <Button variant="secondary" size="sm" on:click={handleLogout}>
          <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          Cerrar sesión
        </Button>
      </div>
    </div>
  </header>
  
  <main class="max-w-7xl mx-auto px-4 py-8">
    <!-- Welcome Banner -->
    <div class="bg-gradient-to-r from-emerald-600 to-teal-600 rounded-2xl p-8 mb-8 shadow-xl">
      <h1 class="text-3xl font-bold text-white mb-2">
        ¡Bienvenido, {$currentUser?.full_name || 'Cliente'}!
      </h1>
      <p class="text-emerald-100 text-lg">
        Gestiona tus servicios y dominios desde tu portal personalizado.
      </p>
    </div>
    
    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <Card>
        <div class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-slate-400">Plan Actual</p>
              <p class="text-2xl font-bold text-white capitalize">{$currentUser?.plan || 'Basic'}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <svg class="w-6 h-6 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
            </div>
          </div>
        </div>
      </Card>
      
      <Card>
        <div class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-slate-400">Dominios Activos</p>
              <p class="text-2xl font-bold text-white">{domains.filter(d => d.is_active).length}</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center">
              <svg class="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
              </svg>
            </div>
          </div>
        </div>
      </Card>
      
      <Card>
        <div class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-slate-400">Estado</p>
              <p class="text-2xl font-bold text-emerald-400">Activo</p>
            </div>
            <div class="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <svg class="w-6 h-6 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>
      </Card>
    </div>
    
    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Mis Dominios -->
      <Card>
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-semibold text-white">Mis Dominios</h2>
            <Button variant="primary" size="sm">
              <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              Solicitar Dominio
            </Button>
          </div>
          
          {#if loading}
            <div class="flex justify-center py-8">
              <Spinner />
            </div>
          {:else if domains.length === 0}
            <div class="text-center py-8">
              <svg class="w-16 h-16 mx-auto text-slate-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
              </svg>
              <p class="text-slate-400">No tienes dominios configurados todavía.</p>
              <p class="text-sm text-slate-500 mt-2">Solicita un dominio personalizado para tu empresa.</p>
            </div>
          {:else}
            <div class="space-y-3">
              {#each domains as domain}
                <div class="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="font-medium text-white">{domain.external_domain}</p>
                      <p class="text-sm text-slate-400">→ {domain.sajet_subdomain}.sajet.us</p>
                    </div>
                    <div class="flex items-center gap-2">
                      {#if domain.is_active}
                        <span class="px-2 py-1 text-xs rounded-full bg-emerald-500/20 text-emerald-400">
                          Activo
                        </span>
                      {:else if domain.verification_status === 'pending'}
                        <span class="px-2 py-1 text-xs rounded-full bg-yellow-500/20 text-yellow-400">
                          Pendiente
                        </span>
                      {:else}
                        <span class="px-2 py-1 text-xs rounded-full bg-slate-500/20 text-slate-400">
                          {domain.verification_status}
                        </span>
                      {/if}
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </Card>
      
      <!-- Acceso Rápido -->
      <Card>
        <div class="p-6">
          <h2 class="text-xl font-semibold text-white mb-6">Acceso Rápido</h2>
          
          <div class="space-y-4">
            <a href="#" class="block bg-slate-800/50 rounded-lg p-4 border border-slate-700 hover:border-emerald-500/50 transition-colors group">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-lg bg-orange-500/20 flex items-center justify-center">
                  <svg class="w-6 h-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <div class="flex-1">
                  <p class="font-medium text-white group-hover:text-emerald-400 transition-colors">Acceder a Sajet ERP</p>
                  <p class="text-sm text-slate-400">Tu panel de gestión empresarial</p>
                </div>
                <svg class="w-5 h-5 text-slate-500 group-hover:text-emerald-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </a>
            
            <a href="#" class="block bg-slate-800/50 rounded-lg p-4 border border-slate-700 hover:border-emerald-500/50 transition-colors group">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-lg bg-blue-500/20 flex items-center justify-center">
                  <svg class="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div class="flex-1">
                  <p class="font-medium text-white group-hover:text-emerald-400 transition-colors">Ver Facturas</p>
                  <p class="text-sm text-slate-400">Historial de facturación y pagos</p>
                </div>
                <svg class="w-5 h-5 text-slate-500 group-hover:text-emerald-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </a>
            
            <a href="mailto:soporte@jeturing.net" class="block bg-slate-800/50 rounded-lg p-4 border border-slate-700 hover:border-emerald-500/50 transition-colors group">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-lg bg-purple-500/20 flex items-center justify-center">
                  <svg class="w-6 h-6 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                </div>
                <div class="flex-1">
                  <p class="font-medium text-white group-hover:text-emerald-400 transition-colors">Soporte Técnico</p>
                  <p class="text-sm text-slate-400">Contacta con nuestro equipo</p>
                </div>
                <svg class="w-5 h-5 text-slate-500 group-hover:text-emerald-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </a>
          </div>
        </div>
      </Card>
    </div>
    
    <!-- Info Banner -->
    <div class="mt-8 bg-slate-800/30 rounded-xl p-6 border border-slate-700">
      <div class="flex items-start gap-4">
        <div class="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0">
          <svg class="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <h3 class="font-medium text-white">¿Necesitas más recursos?</h3>
          <p class="text-slate-400 mt-1">
            Actualiza tu plan para obtener más dominios, almacenamiento y funcionalidades premium.
            <a href="mailto:ventas@jeturing.net" class="text-emerald-400 hover:text-emerald-300">Contacta ventas</a>
          </p>
        </div>
      </div>
    </div>
  </main>
  
  <!-- Footer -->
  <footer class="border-t border-slate-800 mt-12">
    <div class="max-w-7xl mx-auto px-4 py-6">
      <p class="text-center text-sm text-slate-500">
        © 2026 Jeturing Technologies. Todos los derechos reservados.
      </p>
    </div>
  </footer>
</div>
