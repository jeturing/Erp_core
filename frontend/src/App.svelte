<script lang="ts">
  import { onMount } from 'svelte';
  import './app.css';
  import { auth, isAuthenticated, currentUser } from './lib/stores';
  import Layout from './lib/components/Layout.svelte';
  import Login from './routes/Login.svelte';
  import Landing from './routes/Landing.svelte';
  import Dashboard from './routes/Dashboard.svelte';
  import TenantPortal from './routes/TenantPortal.svelte';
  import Domains from './pages/Domains.svelte';
  import { Spinner } from './lib/components';
  
  let currentRoute = 'landing';
  let currentPage: 'landing' | 'login' | 'dashboard' | 'portal' | 'customers' | 'domains' | 'infrastructure' | 'billing' | 'settings' = 'landing';
  
  // Simple hash-based routing
  function handleRouteChange() {
    const hash = window.location.hash.slice(2) || ''; // Remove '#/'
    const route = hash.split('/')[0] || '';
    currentRoute = route;
    
    // Determine which page to show
    if (route === '' || route === 'home') {
      // Landing page (no auth required)
      currentPage = 'landing';
    } else if (route === 'login') {
      currentPage = 'login';
    } else if (!$isAuthenticated && !$auth.isLoading) {
      // Redirect to login if not authenticated (for protected routes)
      window.location.hash = '#/login';
      currentPage = 'login';
    } else if ($currentUser?.role === 'tenant') {
      // Tenant users go to portal
      currentPage = 'portal';
      if (route !== 'portal') {
        window.location.hash = '#/portal';
      }
    } else {
      currentPage = route as typeof currentPage;
    }
  }
  
  onMount(async () => {
    // Initialize auth state
    await auth.init();
    
    // Handle initial route
    handleRouteChange();
    
    // Listen for hash changes
    window.addEventListener('hashchange', handleRouteChange);
    
    return () => {
      window.removeEventListener('hashchange', handleRouteChange);
    };
  });
  
  // React to auth changes
  $: if (!$auth.isLoading) {
    handleRouteChange();
  }
</script>

{#if $auth.isLoading && currentPage !== 'landing'}
  <div class="min-h-screen bg-surface-dark flex items-center justify-center">
    <div class="text-center">
      <Spinner size="lg" />
      <p class="mt-4 text-secondary-400">Cargando...</p>
    </div>
  </div>
{:else if currentPage === 'landing'}
  <Landing />
{:else if currentPage === 'login'}
  <Login />
{:else if currentPage === 'portal'}
  <TenantPortal />
{:else}
  <Layout {currentRoute}>
    {#if currentPage === 'dashboard'}
      <Dashboard />
    {:else if currentPage === 'customers'}
      <div class="p-6">
        <h1 class="text-2xl font-bold text-white">Clientes</h1>
        <p class="text-secondary-400 mt-2">Gestión de clientes - Próximamente</p>
      </div>
    {:else if currentPage === 'domains'}
      <Domains />
    {:else if currentPage === 'infrastructure'}
      <div class="p-6">
        <h1 class="text-2xl font-bold text-white">Infraestructura</h1>
        <p class="text-secondary-400 mt-2">Gestión de nodos y contenedores - Próximamente</p>
      </div>
    {:else if currentPage === 'billing'}
      <div class="p-6">
        <h1 class="text-2xl font-bold text-white">Facturación</h1>
        <p class="text-secondary-400 mt-2">Gestión de pagos y suscripciones - Próximamente</p>
      </div>
    {:else if currentPage === 'settings'}
      <div class="p-6">
        <h1 class="text-2xl font-bold text-white">Configuración</h1>
        <p class="text-secondary-400 mt-2">Ajustes del sistema - Próximamente</p>
      </div>
    {:else}
      <div class="p-6">
        <h1 class="text-2xl font-bold text-white">404 - Página no encontrada</h1>
        <p class="text-secondary-400 mt-2">La página que buscas no existe.</p>
        <a href="#/dashboard" class="text-primary-400 hover:text-primary-300 mt-4 inline-block">
          Volver al Dashboard
        </a>
      </div>
    {/if}
  </Layout>
{/if}
