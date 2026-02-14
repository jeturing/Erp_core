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
  import Tenants from './pages/Tenants.svelte';
  import Infrastructure from './pages/Infrastructure.svelte';
  import Billing from './pages/Billing.svelte';
  import Settings from './pages/Settings.svelte';
  import Logs from './pages/Logs.svelte';
  import Tunnels from './pages/Tunnels.svelte';
  import Roles from './pages/Roles.svelte';
  import { Button, Spinner, Toast } from './lib/components';

  type AppPage =
    | 'landing'
    | 'login'
    | 'dashboard'
    | 'portal'
    | 'tenants'
    | 'domains'
    | 'infrastructure'
    | 'billing'
    | 'settings'
    | 'logs'
    | 'tunnels'
    | 'roles'
    | 'notfound';

  let currentRoute = 'landing';
  let currentPage: AppPage = 'landing';
  let fatalError: string | null = null;

  function getRouteFromLocation(): string {
    const hash = window.location.hash.replace(/^#\/?/, '');
    const hashRoute = hash.split('?')[0].split('/')[0];
    if (hashRoute) {
      return hashRoute;
    }

    const path = window.location.pathname;
    if (path.startsWith('/admin')) return 'dashboard';
    if (path.startsWith('/tenant/portal')) return 'portal';
    if (path.startsWith('/login')) return 'login';
    return 'landing';
  }

  function setRouteHash(route: string) {
    window.location.hash = `#/${route}`;
  }

  function handleRouteChange() {
    const route = getRouteFromLocation();
    currentRoute = route;

    if (route === 'landing' || route === 'home' || route === '') {
      currentPage = 'landing';
      return;
    }

    if (route === 'login') {
      currentPage = 'login';
      return;
    }

    if (!$isAuthenticated && !$auth.isLoading) {
      currentPage = 'login';
      setRouteHash('login');
      return;
    }

    if ($currentUser?.role === 'tenant') {
      currentPage = 'portal';
      if (route !== 'portal') {
        setRouteHash('portal');
      }
      return;
    }

    switch (route) {
      case 'dashboard':
      case 'portal':
      case 'tenants':
      case 'domains':
      case 'infrastructure':
      case 'billing':
      case 'settings':
      case 'logs':
      case 'tunnels':
      case 'roles':
        currentPage = route;
        break;
      default:
        currentPage = 'notfound';
        break;
    }
  }

  onMount(() => {
    let active = true;

    const handleWindowError = (event: ErrorEvent) => {
      if (!event.error) {
        // Ignore resource-loading errors (ad blockers, external beacons, etc.).
        return;
      }
      fatalError = event.error?.message || event.message || 'Fallo inesperado en la aplicacion';
    };

    const handlePromiseError = (event: PromiseRejectionEvent) => {
      const reason = event.reason;
      fatalError = reason instanceof Error ? reason.message : 'Error no controlado en la aplicacion';
    };

    const init = async () => {
      await auth.init();
      if (active) {
        handleRouteChange();
      }
    };

    init();
    window.addEventListener('hashchange', handleRouteChange);
    window.addEventListener('error', handleWindowError);
    window.addEventListener('unhandledrejection', handlePromiseError);

    return () => {
      active = false;
      window.removeEventListener('hashchange', handleRouteChange);
      window.removeEventListener('error', handleWindowError);
      window.removeEventListener('unhandledrejection', handlePromiseError);
    };
  });

  $: if (!$auth.isLoading) {
    handleRouteChange();
  }
</script>

<div class="relative min-h-screen">
  {#if fatalError}
    <div class="min-h-screen bg-surface-dark flex items-center justify-center p-6">
      <div class="max-w-lg w-full rounded-xl border border-error/40 bg-error/10 p-6 text-center space-y-4">
        <h1 class="text-2xl font-bold text-white">La aplicacion encontro un error</h1>
        <p class="text-sm text-secondary-200">{fatalError}</p>
        <Button variant="secondary" on:click={() => window.location.reload()}>Recargar SPA</Button>
      </div>
    </div>
  {:else if $auth.isLoading && currentPage !== 'landing'}
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
    <Layout currentRoute={currentPage === 'notfound' ? currentRoute : currentPage}>
      {#if currentPage === 'dashboard'}
        <Dashboard />
      {:else if currentPage === 'tenants'}
        <Tenants />
      {:else if currentPage === 'domains'}
        <Domains />
      {:else if currentPage === 'infrastructure'}
        <Infrastructure />
      {:else if currentPage === 'billing'}
        <Billing />
      {:else if currentPage === 'settings'}
        <Settings />
      {:else if currentPage === 'logs'}
        <Logs />
      {:else if currentPage === 'tunnels'}
        <Tunnels />
      {:else if currentPage === 'roles'}
        <Roles />
      {:else}
        <div class="p-6">
          <h1 class="text-2xl font-bold text-white">404 - Pagina no encontrada</h1>
          <p class="text-secondary-400 mt-2">La ruta solicitada no existe dentro de la SPA.</p>
          <a href="#/dashboard" class="text-primary-400 hover:text-primary-300 mt-4 inline-block">Volver al Dashboard</a>
        </div>
      {/if}
    </Layout>
  {/if}

  <Toast />
</div>
