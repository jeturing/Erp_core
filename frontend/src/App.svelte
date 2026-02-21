<script lang="ts">
  import { onMount } from 'svelte';
  import './app.css';
  import { auth, isAuthenticated, currentUser } from './lib/stores';
  import Layout from './lib/components/Layout.svelte';
  import Login from './routes/Login.svelte';
  import Landing from './routes/Landing.svelte';
  import Dashboard from './routes/Dashboard.svelte';
  import TenantPortal from './routes/TenantPortal.svelte';
  import PartnerPortal from './routes/PartnerPortal.svelte';
  import Domains from './pages/Domains.svelte';
  import Tenants from './pages/Tenants.svelte';
  import Infrastructure from './pages/Infrastructure.svelte';
  import Billing from './pages/Billing.svelte';
  import Settings from './pages/Settings.svelte';
  import Logs from './pages/Logs.svelte';
  import Tunnels from './pages/Tunnels.svelte';
  import Roles from './pages/Roles.svelte';
  import Plans from './pages/Plans.svelte';
  import Clients from './pages/Clients.svelte';
  import Partners from './pages/Partners.svelte';
  import Leads from './pages/Leads.svelte';
  import Commissions from './pages/Commissions.svelte';
  import Quotations from './pages/Quotations.svelte';
  import Blueprints from './pages/Blueprints.svelte';
  import Seats from './pages/Seats.svelte';
  import Invoices from './pages/Invoices.svelte';
  import Settlements from './pages/Settlements.svelte';
  import Reconciliation from './pages/Reconciliation.svelte';
  import WorkOrders from './pages/WorkOrders.svelte';
  import Audit from './pages/Audit.svelte';
  import Branding from './pages/Branding.svelte';
  import ServiceCatalog from './pages/ServiceCatalog.svelte';
  import { Spinner } from './lib/components';
  import Toast from './lib/components/Toast.svelte';

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
    | 'plans'
    | 'clients'
    | 'partners'
    | 'leads'
    | 'commissions'
    | 'quotations'
    | 'blueprints'
    | 'seats'
    | 'invoices'
    | 'settlements'
    | 'reconciliation'
    | 'workorders'
    | 'audit'
    | 'branding'
    | 'catalog'
    | 'partner-portal'
    | 'signup'
    | 'notfound';

  let currentRoute = 'landing';
  let currentPage: AppPage = 'landing';

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

    if ($currentUser?.role === 'partner') {
      currentPage = 'partner-portal';
      if (route !== 'partner-portal') {
        setRouteHash('partner-portal');
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
      case 'plans':
      case 'clients':
      case 'partners':
      case 'leads':
      case 'commissions':
      case 'quotations':
      case 'blueprints':
      case 'seats':
      case 'invoices':
      case 'settlements':
      case 'reconciliation':
      case 'workorders':
      case 'audit':
      case 'branding':
      case 'catalog':
      case 'partner-portal':
        currentPage = route as AppPage;
        break;
      default:
        currentPage = 'notfound';
        break;
    }
  }

  onMount(() => {
    let active = true;

    const init = async () => {
      await auth.init();
      if (active) {
        handleRouteChange();
      }
    };

    init();
    window.addEventListener('hashchange', handleRouteChange);

    return () => {
      active = false;
      window.removeEventListener('hashchange', handleRouteChange);
    };
  });

  $: if (!$auth.isLoading) {
    handleRouteChange();
  }
</script>

<Toast />

{#if $auth.isLoading && currentPage !== 'landing'}
  <div class="min-h-screen bg-bg-page flex items-center justify-center">
    <div class="text-center">
      <Spinner size="lg" />
      <p class="mt-4 text-gray-500">Cargando...</p>
    </div>
  </div>
{:else if currentPage === 'landing'}
  <Landing />
{:else if currentPage === 'login'}
  <Login />
{:else if currentPage === 'portal'}
  <TenantPortal />
{:else if currentPage === 'partner-portal'}
  <PartnerPortal />
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
    {:else if currentPage === 'plans'}
      <Plans />
    {:else if currentPage === 'clients'}
      <Clients />
    {:else if currentPage === 'partners'}
      <Partners />
    {:else if currentPage === 'leads'}
      <Leads />
    {:else if currentPage === 'commissions'}
      <Commissions />
    {:else if currentPage === 'quotations'}
      <Quotations />
    {:else if currentPage === 'blueprints'}
      <Blueprints />
    {:else if currentPage === 'seats'}
      <Seats />
    {:else if currentPage === 'invoices'}
      <Invoices />
    {:else if currentPage === 'settlements'}
      <Settlements />
    {:else if currentPage === 'reconciliation'}
      <Reconciliation />
    {:else if currentPage === 'workorders'}
      <WorkOrders />
    {:else if currentPage === 'audit'}
      <Audit />
    {:else if currentPage === 'branding'}
      <Branding />
    {:else if currentPage === 'catalog'}
      <ServiceCatalog />
    {:else}
      <div class="p-6">
        <h1 class="page-title">404 - Página no encontrada</h1>
        <p class="page-subtitle mt-2">La ruta solicitada no existe dentro de la SPA.</p>
        <a href="#/dashboard" class="text-terracotta hover:underline mt-4 inline-block text-sm">Volver al Dashboard</a>
      </div>
    {/if}
  </Layout>
{/if}
