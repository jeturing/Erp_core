<script lang="ts">
  import { onMount } from 'svelte';
  import './app.css';
  import { auth, isAuthenticated, currentUser, localeStore } from './lib/stores';
  import { getInitialLocale } from './lib/i18n';
  import Layout from './lib/components/Layout.svelte';
  import Login from './routes/Login.svelte';
  import Landing from './routes/Landing.svelte';
  import AccountantsLanding from './routes/AccountantsLanding.svelte';
  import PartnerLanding from './routes/PartnerLanding.svelte';
  import PartnerSignup from './routes/PartnerSignup.svelte';
  import OnboardingAccess from './routes/OnboardingAccess.svelte';
  import Signup from './routes/Signup.svelte';
  import RecoverAccount from './routes/RecoverAccount.svelte';
  import AccountantPortal from './routes/AccountantPortal.svelte';
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
  import Dispersion from './pages/Dispersion.svelte';
  import WorkOrders from './pages/WorkOrders.svelte';
  import Audit from './pages/Audit.svelte';
  import Branding from './pages/Branding.svelte';
  import ServiceCatalog from './pages/ServiceCatalog.svelte';
  import CustomerOnboarding from './pages/CustomerOnboarding.svelte';
  import OnboardingConfig from './pages/OnboardingConfig.svelte';
  import Communications from './pages/Communications.svelte';
  import Reports from './pages/Reports.svelte';
  import AdminUsers from './pages/AdminUsers.svelte';
  import Agreements from './pages/Agreements.svelte';
  import Testimonials from './pages/Testimonials.svelte';
  import LandingSections from './pages/LandingSections.svelte';
  import Translations from './pages/Translations.svelte';
  import { Spinner } from './lib/components';
  import Toast from './lib/components/Toast.svelte';
  import OfflineBanner from './lib/components/OfflineBanner.svelte';

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
    | 'dispersion'
    | 'workorders'
    | 'audit'
    | 'branding'
    | 'catalog'
    | 'partner-portal'
    | 'customer-onboarding'
    | 'onboarding-config'
    | 'communications'
    | 'reports'
    | 'admin-users'
    | 'agreements'
    | 'testimonials'
    | 'landing-sections'
    | 'translations'
    | 'signup'
    | 'recover-account'
    | 'accountants'
    | 'plt'
    | 'partner-signup'
    | 'onboarding-access'
    | 'accountant-portal'
    | 'notfound';

  let currentRoute = 'landing';
  let currentPage: AppPage = 'landing';
  let partnerSlug = '';

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
    if (path.startsWith('/signup')) return 'signup';
    if (path.startsWith('/recover-account')) return 'recover-account';
    if (path.startsWith('/partner-signup')) return 'partner-signup';
    return 'landing';
  }

  function getPartnerSlugFromHash(): string {
    const hash = window.location.hash.replace(/^#\/?/, '');
    const parts = hash.split('?')[0].split('/');
    // #/plt/{slug}
    if (parts[0] === 'plt' && parts[1]) {
      return parts[1];
    }
    return '';
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

    if (route === 'accountants') {
      currentPage = 'accountants';
      return;
    }

    if (route === 'plt') {
      partnerSlug = getPartnerSlugFromHash();
      currentPage = 'plt';
      return;
    }

    if (route === 'login') {
      currentPage = 'login';
      return;
    }

    if (route === 'signup') {
      currentPage = 'signup';
      return;
    }

    if (route === 'recover-account') {
      currentPage = 'recover-account';
      return;
    }

    if (route === 'partner-signup') {
      currentPage = 'partner-signup';
      return;
    }

    if (route === 'customer-onboarding' && !$isAuthenticated && !$auth.isLoading) {
      currentPage = 'onboarding-access';
      return;
    }

    if (!$isAuthenticated && !$auth.isLoading) {
      currentPage = 'login';
      setRouteHash('login');
      return;
    }

    if ($currentUser?.role === 'tenant') {
      // Si el tenant tiene onboarding pendiente, redirigir al flujo de onboarding
      const onboardingStep = ($currentUser as any)?.onboarding_step ?? 999;
      if (onboardingStep < 4 && route !== 'customer-onboarding') {
        currentPage = 'customer-onboarding';
        setRouteHash('customer-onboarding');
        return;
      }
      if (route === 'customer-onboarding') {
        currentPage = 'customer-onboarding';
        return;
      }
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

    // Admin/operator/viewer que navega a rutas exclusivas de tenant/partner → redirigir a dashboard
    if (route === 'portal' && $currentUser?.role && !['tenant'].includes($currentUser.role)) {
      currentPage = 'dashboard';
      setRouteHash('dashboard');
      return;
    }
    if (route === 'partner-portal' && $currentUser?.role && !['partner'].includes($currentUser.role)) {
      currentPage = 'dashboard';
      setRouteHash('dashboard');
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
      case 'dispersion':
      case 'workorders':
      case 'audit':
      case 'branding':
      case 'catalog':
      case 'partner-portal':
      case 'customer-onboarding':
      case 'onboarding-config':
      case 'communications':
      case 'reports':
      case 'admin-users':
      case 'agreements':
      case 'testimonials':
      case 'landing-sections':
      case 'translations':
      case 'accountant-portal':
      case 'signup':
      case 'recover-account':
      case 'partner-signup':
      case 'onboarding-access':
        currentPage = route as AppPage;
        break;
      default:
        currentPage = 'notfound';
        break;
    }
  }

  onMount(() => {
    let active = true;

    // Sync locale store (i18n already initialized in main.ts)
    const initialLocale = getInitialLocale();
    localeStore.set(initialLocale as any);

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
<OfflineBanner />

{#if $auth.isLoading && currentPage !== 'landing'}
  <div class="min-h-screen bg-bg-page flex items-center justify-center">
    <div class="text-center">
      <Spinner size="lg" />
      <p class="mt-4 text-gray-500">Cargando...</p>
    </div>
  </div>
{:else if currentPage === 'landing'}
  <Landing />
{:else if currentPage === 'accountants'}
  <AccountantsLanding />
{:else if currentPage === 'plt'}
  <PartnerLanding code={partnerSlug} />
{:else if currentPage === 'login'}
  <Login />
{:else if currentPage === 'signup'}
  <Signup />
{:else if currentPage === 'recover-account'}
  <RecoverAccount />
{:else if currentPage === 'partner-signup'}
  <PartnerSignup />
{:else if currentPage === 'onboarding-access'}
  <OnboardingAccess />
{:else if currentPage === 'portal'}
  <TenantPortal />
{:else if currentPage === 'partner-portal'}
  <PartnerPortal />
{:else if currentPage === 'customer-onboarding'}
  <CustomerOnboarding />
{:else if currentPage === 'accountant-portal'}
  <AccountantPortal />
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
    {:else if currentPage === 'dispersion'}
      <Dispersion />
    {:else if currentPage === 'workorders'}
      <WorkOrders />
    {:else if currentPage === 'audit'}
      <Audit />
    {:else if currentPage === 'branding'}
      <Branding />
    {:else if currentPage === 'catalog'}
      <ServiceCatalog />
    {:else if currentPage === 'onboarding-config'}
      <OnboardingConfig />
    {:else if currentPage === 'communications'}
      <Communications />
    {:else if currentPage === 'reports'}
      <Reports />
    {:else if currentPage === 'admin-users'}
      <AdminUsers />
    {:else if currentPage === 'agreements'}
      <Agreements />
    {:else if currentPage === 'testimonials'}
      <Testimonials />
    {:else if currentPage === 'landing-sections'}
      <LandingSections />
    {:else if currentPage === 'translations'}
      <Translations />
    {:else}
      <div class="p-6">
        <h1 class="page-title">404 - Página no encontrada</h1>
        <p class="page-subtitle mt-2">La ruta solicitada no existe dentro de la SPA.</p>
        <a href="#/dashboard" class="text-terracotta hover:underline mt-4 inline-block text-sm">Volver al Dashboard</a>
      </div>
    {/if}
  </Layout>
{/if}
