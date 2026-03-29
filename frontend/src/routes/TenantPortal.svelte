<script lang="ts">
  import { onMount } from 'svelte';
  import {
    ExternalLink, Download, LogOut, Package, Users,
    LayoutGrid, ChartColumn, FileText, CircleUser, BookOpen,
    Building2, Globe, Shield, KeyRound, Plus, CheckCircle2,
    Clock, XCircle, AlertCircle, Eye, EyeOff
  } from 'lucide-svelte';
  import { auth, currentUser } from '../lib/stores';
  import { Spinner } from '../lib/components';
  import portalApi from '../lib/api/portal';
  import type { AddonSubscriptionItem, ServiceCatalogItemType, TenantPortalInfo, TenantPortalBilling } from '../lib/types';
  import type { PortalDomain, PortalUserAccount, PortalUsersResponse } from '../lib/api/portal';
  import { formatDate } from '../lib/utils/formatters';
  import { goto } from '$app/navigation';

  // ── Estado global ──
  let loading = true;
  let error = '';
  let info: TenantPortalInfo | null = null;
  let billing: TenantPortalBilling | null = null;

  // ── Tabs ──
  type Tab = 'dashboard' | 'domains' | 'users' | 'services' | 'security';
  let activeTab: Tab = 'dashboard';

  // ── Dominios ──
  let domains: PortalDomain[] = [];
  let domainsLoading = false;
  let domainsError = '';
  let showDomainModal = false;
  let domainInput = '';
  let domainSubmitting = false;
  let domainMsg = '';
  let domainMsgType: 'success' | 'error' = 'success';

  // ── Usuarios ──
  let usersData: PortalUsersResponse | null = null;
  let usersLoading = false;
  let usersError = '';

  // ── Servicios adicionales ──
  let serviceCatalog: ServiceCatalogItemType[] = [];
  let serviceSubscriptions: AddonSubscriptionItem[] = [];
  let servicesLoading = false;
  let servicesError = '';
  let serviceMsg = '';
  let serviceMsgType: 'success' | 'error' = 'success';
  let purchasingServiceId: number | null = null;

  // ── Seguridad / cambio de contraseña ──
  let pwCurrent = '';
  let pwNew = '';
  let pwConfirm = '';
  let pwSubmitting = false;
  let pwMsg = '';
  let pwMsgType: 'success' | 'error' = 'success';
  let showCurrent = false;
  let showNew = false;
  let showConfirm = false;

  const installedApps = [
    { label: 'CRM', icon: CircleUser, color: 'text-blue-500' },
    { label: 'Inventario', icon: Package, color: 'text-emerald-500' },
    { label: 'Facturación', icon: FileText, color: 'text-amber-500' },
    { label: 'RRHH', icon: Users, color: 'text-purple-500' },
    { label: 'Contabilidad', icon: BookOpen, color: 'text-rose-500' },
    { label: 'Ventas', icon: ChartColumn, color: 'text-indigo-500' },
  ];

  const planFeatures: Record<string, string[]> = {
    basic: ['Hasta 5 usuarios', 'Soporte por email', '5 apps instaladas'],
    pro: ['Hasta 15 usuarios', 'Soporte prioritario', '10 apps instaladas'],
    enterprise: ['Usuarios ilimitados', 'Soporte 24/7 dedicado', 'Apps ilimitadas'],
  };

  const planPrices: Record<string, string> = {
    basic: '$350/mes',
    pro: '$750/mes',
    enterprise: '$1,500/mes',
  };

  async function loadPortal() {
    loading = true;
    error = '';
    try {
      const [infoData, billingData] = await Promise.all([
        portalApi.getInfo(),
        portalApi.getBilling().catch(() => ({ invoices: [], payment_method: null })),
      ]);
      info = infoData;
      billing = billingData;
    } catch (err) {
      error = err instanceof Error ? err.message : 'No se pudo cargar el portal';
    } finally {
      loading = false;
    }
  }

  async function loadDomains() {
    domainsLoading = true;
    domainsError = '';
    try {
      const res = await portalApi.getMyDomains();
      domains = res.domains;
    } catch (err) {
      domainsError = err instanceof Error ? err.message : 'Error al cargar dominios';
    } finally {
      domainsLoading = false;
    }
  }

  async function loadUsers() {
    usersLoading = true;
    usersError = '';
    try {
      usersData = await portalApi.getUsers();
    } catch (err) {
      usersError = err instanceof Error ? err.message : 'Error al cargar usuarios';
    } finally {
      usersLoading = false;
    }
  }

  function isEmailPackage(item: Pick<ServiceCatalogItemType, 'service_code' | 'metadata_json'>): boolean {
    return item.service_code === 'postal_email_package' || item.metadata_json?.kind === 'postal_email_package';
  }

  function formatInteger(value: number | null | undefined): string {
    return new Intl.NumberFormat('es-DO').format(Number(value || 0));
  }

  async function loadServices() {
    servicesLoading = true;
    servicesError = '';
    try {
      const [catalogRes, subscriptionsRes] = await Promise.all([
        portalApi.getServiceCatalog(),
        portalApi.getServiceSubscriptions(),
      ]);
      serviceCatalog = catalogRes.items ?? [];
      serviceSubscriptions = subscriptionsRes.items ?? [];
    } catch (err) {
      servicesError = err instanceof Error ? err.message : 'Error al cargar servicios adicionales';
    } finally {
      servicesLoading = false;
    }
  }

  async function switchTab(tab: Tab) {
    activeTab = tab;
    if (tab === 'domains' && domains.length === 0 && !domainsLoading) loadDomains();
    if (tab === 'users' && !usersData && !usersLoading) loadUsers();
    if (tab === 'services' && serviceCatalog.length === 0 && !servicesLoading) loadServices();
  }

  async function submitDomain() {
    if (!domainInput.trim()) return;
    domainSubmitting = true;
    domainMsg = '';
    try {
      await portalApi.requestDomain(domainInput.trim());
      domainMsg = 'Dominio registrado. Pendiente de verificación DNS.';
      domainMsgType = 'success';
      domainInput = '';
      showDomainModal = false;
      loadDomains();
    } catch (err) {
      domainMsg = err instanceof Error ? err.message : 'Error al solicitar dominio';
      domainMsgType = 'error';
    } finally {
      domainSubmitting = false;
    }
  }

  async function submitChangePassword() {
    if (!pwCurrent || !pwNew || !pwConfirm) return;
    if (pwNew !== pwConfirm) {
      pwMsg = 'Las contraseñas nuevas no coinciden';
      pwMsgType = 'error';
      return;
    }
    pwSubmitting = true;
    pwMsg = '';
    try {
      const res = await portalApi.changePassword({
        current_password: pwCurrent,
        new_password: pwNew,
        confirm_password: pwConfirm,
      });
      pwMsg = res.message || 'Contraseña actualizada exitosamente';
      pwMsgType = 'success';
      pwCurrent = '';
      pwNew = '';
      pwConfirm = '';
    } catch (err) {
      pwMsg = err instanceof Error ? err.message : 'Error al cambiar contraseña';
      pwMsgType = 'error';
    } finally {
      pwSubmitting = false;
    }
  }

  async function purchaseAddon(item: ServiceCatalogItemType) {
    purchasingServiceId = item.id;
    serviceMsg = '';
    try {
      const result = await portalApi.purchaseService(item.id, 1);
      serviceMsg = result.message || `Servicio ${item.name} adquirido correctamente`;
      serviceMsgType = 'success';
      await loadServices();
      billing = await portalApi.getBilling().catch(() => billing);
      if (result.invoice?.payment_url) {
        window.open(result.invoice.payment_url, '_blank', 'noopener,noreferrer');
      }
    } catch (err) {
      serviceMsg = err instanceof Error ? err.message : 'No se pudo adquirir el servicio';
      serviceMsgType = 'error';
    } finally {
      purchasingServiceId = null;
    }
  }

  function handleLogout() {
    auth.logout();
    goto('/login');
  }

  function statusBadgeClass(status: string): string {
    if (status === 'active') return 'badge-success';
    if (status === 'pending' || status === 'past_due') return 'badge-warning';
    if (status === 'cancelled' || status === 'suspended') return 'badge-error';
    return 'badge-neutral';
  }

  function invoiceStatusClass(status: string): string {
    if (status === 'paid') return 'badge-success';
    if (status === 'open' || status === 'issued' || status === 'past_due' || status === 'overdue') return 'badge-warning';
    if (status === 'void' || status === 'uncollectible') return 'badge-error';
    return 'badge-neutral';
  }

  function invoicePrimaryAction(invoice: TenantPortalBilling['invoices'][number]) {
    if (invoice.payment_url) {
      return { label: 'PAGAR FACTURA', href: invoice.payment_url };
    }
    if (invoice.download_url) {
      return { label: 'DESCARGAR PDF', href: invoice.download_url };
    }
    if (invoice.view_url) {
      return { label: 'VER FACTURA', href: invoice.view_url };
    }
    return null;
  }

  function invoiceSecondaryDownload(invoice: TenantPortalBilling['invoices'][number]): string | null {
    if (!invoice.download_url || invoice.download_url === invoice.payment_url) {
      return null;
    }
    return invoice.download_url;
  }

  function accountStateBadge(account: PortalUserAccount): string {
    return account.active ? 'badge-success' : 'badge-neutral';
  }

  function accountMetaBadge(base: 'billable' | 'internal' | 'excluded'): string {
    if (base === 'billable') return 'badge-info';
    if (base === 'internal') return 'badge-warning';
    return 'badge-neutral';
  }

  function domainStatusClass(status: string): string {
    if (status === 'verified' || status === 'active') return 'badge-success';
    if (status === 'pending') return 'badge-warning';
    if (status === 'failed') return 'badge-error';
    return 'badge-neutral';
  }

  function domainStatusIcon(status: string) {
    if (status === 'verified' || status === 'active') return CheckCircle2;
    if (status === 'pending') return Clock;
    if (status === 'failed') return XCircle;
    return AlertCircle;
  }

  function seatEventLabel(type: string): string {
    const map: Record<string, string> = {
      USER_CREATED: 'Usuario creado',
      USER_DEACTIVATED: 'Usuario desactivado',
      USER_REACTIVATED: 'Usuario reactivado',
      FIRST_LOGIN: 'Primer login',
      HWM_SNAPSHOT: 'Snapshot de licencias',
    };
    return map[type] || type;
  }

  function getPlanFeatures(plan: string | null): string[] {
    if (!plan) return ['Hasta 5 usuarios', 'Soporte prioritario', '10 apps instaladas'];
    return planFeatures[plan.toLowerCase()] || ['Hasta 5 usuarios', 'Soporte prioritario', '10 apps instaladas'];
  }

  function getPlanPrice(plan: string | null): string {
    if (!plan) return '$750/mes';
    return planPrices[plan.toLowerCase()] || '$750/mes';
  }

  function formatCurrency(amount: number, currency: string): string {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: currency.toUpperCase(),
      minimumFractionDigits: 2,
    }).format(amount || 0);
  }

  onMount(loadPortal);
</script>

<div class="min-h-screen bg-[#F5F3EF]">
  <!-- Top Navbar -->
  <header class="bg-[#1a1a1a] border-b border-[#2a2a2a] sticky top-0 z-20">
    <div class="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded bg-[#C05A3C] flex items-center justify-center">
          <span class="text-white font-bold text-sm">S</span>
        </div>
        <span class="text-white font-semibold tracking-[0.05em] text-sm">SAJET</span>
      </div>

      <div class="flex items-center gap-2">
        <Building2 class="w-4 h-4 text-gray-400" />
        <span class="text-gray-300 text-sm font-medium">
          {$currentUser?.company_name || info?.company_name || 'Mi Empresa'}
        </span>
        {#if info}
          <span class="badge {statusBadgeClass(info.status)} ml-1">{info.status}</span>
        {/if}
      </div>

      <button
        class="flex items-center gap-1.5 text-[11px] font-semibold tracking-[0.08em] text-gray-400 hover:text-white uppercase transition-colors"
        on:click={handleLogout}
      >
        <LogOut class="w-3.5 h-3.5" />
        CERRAR SESIÓN
      </button>
    </div>

    <!-- Tabs -->
    <div class="max-w-6xl mx-auto px-6 flex gap-1">
      {#each [
        { id: 'dashboard', label: 'MI PORTAL',  icon: LayoutGrid },
        { id: 'domains',   label: 'DOMINIOS',   icon: Globe },
        { id: 'users',     label: 'USUARIOS',   icon: Users },
        { id: 'services',  label: 'SERVICIOS',  icon: Package },
        { id: 'security',  label: 'SEGURIDAD',  icon: Shield },
      ] as tab}
        <button
          class="flex items-center gap-1.5 px-4 py-2.5 text-[11px] font-semibold tracking-[0.08em] transition-colors border-b-2
            {activeTab === tab.id
              ? 'text-white border-[#C05A3C]'
              : 'text-gray-500 border-transparent hover:text-gray-300 hover:border-gray-600'}"
          on:click={() => switchTab(tab.id as Tab)}
        >
          <svelte:component this={tab.icon} class="w-3.5 h-3.5" />
          {tab.label}
        </button>
      {/each}
    </div>
  </header>

  <main class="max-w-6xl mx-auto px-6 py-8 space-y-6">
    {#if error}
      <div class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
    {/if}

    {#if loading}
      <div class="py-24 flex justify-center"><Spinner size="lg" /></div>

    <!-- ===== DASHBOARD ===== -->
    {:else if activeTab === 'dashboard' && info}
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="card flex flex-col gap-4">
          <div>
            <span class="section-heading block mb-3">MI PLAN ACTUAL</span>
            <div class="flex items-baseline gap-3 mb-1">
              <span class="text-2xl font-bold text-text-primary capitalize">{info.plan || 'Pro'}</span>
              <span class="text-xl font-semibold text-[#C05A3C]">{getPlanPrice(info.plan)}</span>
            </div>
            <p class="text-xs text-gray-500">Facturado mensualmente</p>
          </div>
          <div class="border-t border-border-light pt-4">
            <span class="section-heading block mb-3">INCLUYE</span>
            <ul class="space-y-2">
              {#each getPlanFeatures(info.plan) as feature}
                <li class="flex items-center gap-2 text-sm text-text-secondary">
                  <div class="w-1.5 h-1.5 rounded-full bg-[#4A7C59] flex-shrink-0"></div>
                  {feature}
                </li>
              {/each}
            </ul>
          </div>
          <div class="mt-auto pt-2">
            <button class="btn btn-ghost btn-sm w-full border border-border-light">CAMBIAR PLAN</button>
          </div>
        </div>

        <div class="card flex flex-col gap-4">
          <span class="section-heading block">MIS INSTANCIAS</span>
          <div class="rounded border border-border-light bg-bg-page p-4 space-y-3">
            <div class="flex items-center justify-between">
              <span class="font-mono text-sm font-semibold text-text-primary">{info.subdomain}.sajet.us</span>
              <span class="badge {statusBadgeClass(info.status)}">{info.status}</span>
            </div>
            {#if info.created_at}
              <div class="flex items-center justify-between text-xs">
                <span class="text-gray-500">Creado</span>
                <span class="text-text-secondary">{formatDate(info.created_at)}</span>
              </div>
            {/if}
            {#if info.subscription_id}
              <div class="flex items-center justify-between text-xs">
                <span class="text-gray-500">Suscripción ID</span>
                <span class="font-mono text-text-secondary">#{info.subscription_id}</span>
              </div>
            {/if}
          </div>
          {#if info.odoo_url || info.subdomain}
            <a
              href={info.odoo_url || `https://${info.subdomain}.sajet.us`}
              target="_blank" rel="noreferrer"
              class="btn btn-primary btn-sm flex items-center justify-center gap-2"
            >
              <ExternalLink class="w-3.5 h-3.5" />
              ABRIR MI SAJET
            </a>
          {/if}
          <div class="mt-auto text-xs text-gray-500">
            <span class="font-medium">Soporte:</span>
            <a href="mailto:soporte@sajet.us" class="text-[#C05A3C] ml-1 hover:underline">soporte@sajet.us</a>
          </div>
        </div>
      </div>

      <div class="card p-0 overflow-hidden">
        <div class="px-6 py-4 border-b border-border-light">
          <span class="section-heading">MIS FACTURAS</span>
        </div>
        {#if billing?.invoices && billing.invoices.length > 0}
          <div class="overflow-x-auto">
            <table class="table w-full">
              <thead>
                <tr><th>Número</th><th>Monto</th><th>Estado</th><th>Fecha</th><th>Acción</th></tr>
              </thead>
              <tbody>
                {#each billing.invoices as invoice}
                  <tr>
                    <td><span class="font-mono text-xs text-text-secondary">#{invoice.id.slice(-8).toUpperCase()}</span></td>
                    <td><span class="text-sm font-semibold text-text-primary">{formatCurrency(invoice.amount, invoice.currency)}</span></td>
                    <td><span class="badge {invoiceStatusClass(invoice.status)}">{invoice.status}</span></td>
                    <td><span class="text-xs text-text-secondary">{formatDate(invoice.date)}</span></td>
                    <td>
                      {#if invoicePrimaryAction(invoice)}
                        <div class="flex items-center gap-2">
                          <a href={invoicePrimaryAction(invoice)?.href} target="_blank" rel="noreferrer"
                            class="btn btn-secondary btn-sm inline-flex items-center gap-1">
                            <Download class="w-3 h-3" /> {invoicePrimaryAction(invoice)?.label}
                          </a>
                          {#if invoiceSecondaryDownload(invoice)}
                            <a href={invoiceSecondaryDownload(invoice) || undefined} target="_blank" rel="noreferrer"
                              class="btn btn-ghost btn-sm inline-flex items-center gap-1 border border-border-light">
                              <FileText class="w-3 h-3" /> PDF
                            </a>
                          {/if}
                        </div>
                      {:else}
                        <span class="text-xs text-gray-500">—</span>
                      {/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {:else}
          <div class="py-10 flex flex-col items-center gap-2">
            <FileText class="w-7 h-7 text-border-light" />
            <p class="text-sm text-gray-500">No hay facturas registradas</p>
          </div>
        {/if}
      </div>

      <div class="card">
        <div class="mb-4"><span class="section-heading block">APPS INSTALADAS EN TU INSTANCIA</span></div>
        <div class="grid grid-cols-3 sm:grid-cols-6 gap-4">
          {#each installedApps as app}
            <div class="flex flex-col items-center gap-2 p-3 rounded border border-border-light bg-bg-page hover:border-[#C05A3C] transition-colors cursor-default">
              <svelte:component this={app.icon} class="w-6 h-6 {app.color}" />
              <span class="text-[10px] font-semibold text-text-secondary text-center uppercase tracking-[0.06em]">{app.label}</span>
            </div>
          {/each}
        </div>
      </div>

    <!-- ===== DOMINIOS ===== -->
    {:else if activeTab === 'domains'}
      <div class="card">
        <div class="flex items-center justify-between mb-5">
          <div>
            <span class="section-heading block">MIS DOMINIOS PERSONALIZADOS</span>
            <p class="text-xs text-gray-500 mt-1">Asocia tu propio dominio a tu instancia Sajet</p>
          </div>
          <button
            class="btn btn-primary btn-sm flex items-center gap-1.5"
            on:click={() => { showDomainModal = true; domainMsg = ''; domainInput = ''; }}
          >
            <Plus class="w-3.5 h-3.5" />
            AGREGAR DOMINIO
          </button>
        </div>

        {#if domainsLoading}
          <div class="py-10 flex justify-center"><Spinner /></div>
        {:else if domainsError}
          <div class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{domainsError}</div>
        {:else if domains.length === 0}
          <div class="py-12 flex flex-col items-center gap-3 text-center">
            <Globe class="w-10 h-10 text-border-light" />
            <p class="text-sm font-semibold text-text-secondary">Aún no tienes dominios configurados</p>
            <p class="text-xs text-gray-500">Agrega tu dominio y configura el DNS para apuntar a tu instancia</p>
          </div>
        {:else}
          <div class="space-y-3">
            {#each domains as domain}
              <div class="flex items-center justify-between p-4 rounded border border-border-light bg-bg-page">
                <div class="flex items-center gap-3">
                  <svelte:component
                    this={domainStatusIcon(domain.verification_status)}
                    class="w-4 h-4 {domain.verification_status === 'verified' || domain.verification_status === 'active'
                      ? 'text-emerald-500'
                      : domain.verification_status === 'pending' ? 'text-amber-500' : 'text-red-500'}"
                  />
                  <div>
                    <p class="text-sm font-semibold text-text-primary font-mono">{domain.external_domain}</p>
                    {#if domain.sajet_full_domain}
                      <p class="text-xs text-gray-500">→ {domain.sajet_full_domain}</p>
                    {/if}
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <span class="badge {domainStatusClass(domain.verification_status)}">{domain.verification_status}</span>
                  {#if domain.is_active}
                    <span class="badge badge-success">Activo</span>
                  {:else}
                    <span class="badge badge-neutral">Inactivo</span>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        {/if}

        {#if domainMsg && !showDomainModal}
          <div class="mt-4 rounded border px-4 py-3 text-sm
            {domainMsgType === 'success' ? 'border-green-200 bg-green-50 text-green-700' : 'border-red-200 bg-red-50 text-red-700'}">
            {domainMsg}
          </div>
        {/if}
      </div>

      <div class="card border-amber-200 bg-amber-50">
        <p class="text-sm font-semibold text-amber-800 mb-2">Cómo configurar el DNS</p>
        <ol class="text-xs text-amber-700 space-y-1 list-decimal list-inside">
          <li>Agrega tu dominio usando el botón "Agregar dominio"</li>
          <li>En tu proveedor DNS crea un registro A hacia la IP pública de Sajet:</li>
        </ol>
        <div class="mt-2 p-2 bg-amber-100 rounded font-mono text-xs text-amber-900">
          208.115.125.29
        </div>
        <p class="text-xs text-amber-600 mt-2">No uses CNAME hacia <code>{info?.subdomain || 'tusubdominio'}.sajet.us</code>; la verificación puede tardar hasta 48 horas.</p>
      </div>

    <!-- ===== USUARIOS ===== -->
    {:else if activeTab === 'users'}
      <div class="card">
        <span class="section-heading block mb-5">USUARIOS DE MI INSTANCIA</span>

        {#if usersLoading}
          <div class="py-10 flex justify-center"><Spinner /></div>
        {:else if usersError}
          <div class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{usersError}</div>
        {:else if usersData}
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div class="rounded border border-border-light bg-bg-page p-4 text-center">
              <p class="text-3xl font-bold text-text-primary">{usersData.active_accounts}</p>
              <p class="text-xs text-gray-500 mt-1 uppercase tracking-widest">Usuarios activos</p>
            </div>
            <div class="rounded border border-border-light bg-bg-page p-4 text-center">
              <p class="text-3xl font-bold text-[#C05A3C]">{usersData.billable_active_accounts}</p>
              <p class="text-xs text-gray-500 mt-1 uppercase tracking-widest">Usuarios facturables</p>
            </div>
            <div class="rounded border border-border-light bg-bg-page p-4 text-center">
              {#if usersData.plan_user_limit > 0}
                <p class="text-3xl font-bold text-[#C05A3C]">{usersData.plan_user_limit}</p>
              {:else}
                <p class="text-2xl font-bold text-[#C05A3C]">Ilimitado</p>
              {/if}
              <p class="text-xs text-gray-500 mt-1 uppercase tracking-widest">Límite del plan</p>
            </div>
          </div>

          {#if usersData.plan_user_limit > 0}
            {@const pct = Math.min(100, Math.round((usersData.current_user_count / usersData.plan_user_limit) * 100))}
            <div class="mb-6">
              <div class="flex justify-between text-xs text-gray-500 mb-1">
                <span>Uso de licencias facturables</span><span>{pct}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div
                  class="h-2 rounded-full transition-all {pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-amber-500' : 'bg-emerald-500'}"
                  style="width: {pct}%"
                ></div>
              </div>
            </div>
          {/if}

          <div class="border-t border-border-light pt-4">
            <div class="flex items-center justify-between mb-3 gap-3">
              <p class="text-xs font-semibold text-gray-500 uppercase tracking-widest">Usuarios de tu instancia</p>
              <span class="text-[11px] text-gray-500">{usersData.accounts.length} registros</span>
            </div>

            {#if usersData.accounts.length > 0}
              <div class="overflow-x-auto rounded border border-border-light">
                <table class="table w-full bg-bg-page">
                  <thead>
                    <tr>
                      <th>Usuario</th>
                      <th>Correo</th>
                      <th>Estado</th>
                      <th>Perfil</th>
                      <th>Actualizado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each usersData.accounts as account}
                      <tr>
                        <td>
                          <div class="flex flex-col">
                            <span class="font-medium text-text-primary">{account.name || account.login || 'Sin nombre'}</span>
                            <span class="text-[11px] text-gray-500 font-mono">{account.login || '—'}</span>
                          </div>
                        </td>
                        <td class="text-sm text-text-secondary">{account.email || '—'}</td>
                        <td>
                          <span class="badge {accountStateBadge(account)}">{account.active ? 'Activo' : 'Inactivo'}</span>
                        </td>
                        <td>
                          <div class="flex flex-wrap gap-1">
                            {#if account.is_billable}
                              <span class="badge {accountMetaBadge('billable')}">Facturable</span>
                            {/if}
                            {#if account.is_admin}
                              <span class="badge {accountMetaBadge('internal')}">Interno</span>
                            {/if}
                            {#if account.is_excluded}
                              <span class="badge {accountMetaBadge('excluded')}">Excluido</span>
                            {/if}
                          </div>
                        </td>
                        <td class="text-xs text-gray-500">{formatDate(account.write_date || account.create_date)}</td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            {:else}
              <div class="py-8 flex flex-col items-center gap-2 text-center border border-border-light rounded bg-bg-page">
                <Users class="w-8 h-8 text-border-light" />
                <p class="text-sm text-gray-500">No pudimos obtener la lista viva de usuarios de tu instancia.</p>
              </div>
            {/if}
          </div>

          <div class="border-t border-border-light pt-4 mt-6">
            <p class="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">Historial de licencias</p>
            {#if usersData.seat_events.length > 0}
              <div class="space-y-2 max-h-80 overflow-y-auto">
                {#each usersData.seat_events as event}
                  <div class="flex items-center justify-between p-3 rounded border border-border-light bg-bg-page text-sm">
                    <div class="flex items-center gap-2">
                      <div class="w-2 h-2 rounded-full
                        {event.event_type === 'USER_CREATED' || event.event_type === 'USER_REACTIVATED' ? 'bg-emerald-500'
                          : event.event_type === 'USER_DEACTIVATED' ? 'bg-red-400'
                          : event.event_type === 'FIRST_LOGIN' ? 'bg-blue-400' : 'bg-gray-400'}"
                      ></div>
                      <div>
                        <span class="font-medium text-text-primary">{seatEventLabel(event.event_type)}</span>
                        {#if event.login}
                          <span class="text-gray-500 ml-2 font-mono text-xs">{event.login}</span>
                        {/if}
                      </div>
                    </div>
                    <div class="text-right">
                      <p class="text-xs text-gray-500">{event.created_at ? formatDate(event.created_at) : '—'}</p>
                      <p class="text-xs text-text-secondary">{event.user_count_after} usuarios</p>
                    </div>
                  </div>
                {/each}
              </div>
            {:else}
              <div class="py-8 flex flex-col items-center gap-2 text-center border border-border-light rounded bg-bg-page">
                <Users class="w-8 h-8 text-border-light" />
                <p class="text-sm text-gray-500">Aún no hay historial de licencias registrado.</p>
              </div>
            {/if}
          </div>
        {/if}
      </div>

    <!-- ===== SERVICIOS ===== -->
    {:else if activeTab === 'services'}
      <div class="space-y-6">
        <div class="card">
          <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-5">
            <div>
              <span class="section-heading block">SERVICIOS ADICIONALES</span>
              <p class="text-xs text-gray-500 mt-1">Compra paquetes complementarios y se facturan automáticamente a tu cuenta.</p>
            </div>
          </div>

          {#if serviceMsg}
            <div class="mb-4 rounded border px-4 py-3 text-sm
              {serviceMsgType === 'success' ? 'border-green-200 bg-green-50 text-green-700' : 'border-red-200 bg-red-50 text-red-700'}">
              {serviceMsg}
            </div>
          {/if}

          {#if servicesLoading}
            <div class="py-10 flex justify-center"><Spinner /></div>
          {:else if servicesError}
            <div class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{servicesError}</div>
          {:else}
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
              <div class="rounded border border-border-light bg-bg-page p-4">
                <p class="text-xs text-gray-500 uppercase tracking-widest">Servicios disponibles</p>
                <p class="mt-2 text-2xl font-bold text-text-primary">{serviceCatalog.length}</p>
              </div>
              <div class="rounded border border-border-light bg-bg-page p-4">
                <p class="text-xs text-gray-500 uppercase tracking-widest">Servicios activos</p>
                <p class="mt-2 text-2xl font-bold text-[#C05A3C]">{serviceSubscriptions.length}</p>
              </div>
              <div class="rounded border border-border-light bg-bg-page p-4">
                <p class="text-xs text-gray-500 uppercase tracking-widest">Facturación</p>
                <p class="mt-2 text-sm text-text-secondary">Las compras generan factura inmediata y se reflejan en próximas renovaciones.</p>
              </div>
            </div>

            <div class="grid grid-cols-1 xl:grid-cols-[0.9fr,1.1fr] gap-6">
              <div class="card">
                <div class="mb-4">
                  <span class="section-heading block">MIS SERVICIOS ACTIVOS</span>
                </div>

                {#if serviceSubscriptions.length === 0}
                  <div class="py-10 flex flex-col items-center gap-2 text-center">
                    <Package class="w-8 h-8 text-border-light" />
                    <p class="text-sm text-gray-500">Aún no tienes servicios adicionales activos.</p>
                  </div>
                {:else}
                  <div class="space-y-3">
                    {#each serviceSubscriptions as addon}
                      <div class="rounded border border-border-light bg-bg-page p-4">
                        <div class="flex items-start justify-between gap-3">
                          <div>
                            <div class="flex items-center gap-2 flex-wrap">
                              <p class="font-semibold text-text-primary">{addon.catalog_item?.name || addon.service_code || 'Servicio adicional'}</p>
                              {#if addon.catalog_item && isEmailPackage(addon.catalog_item)}
                                <span class="badge badge-info">Correo</span>
                              {/if}
                            </div>
                            {#if addon.catalog_item?.description}
                              <p class="text-sm text-gray-500 mt-1">{addon.catalog_item.description}</p>
                            {/if}
                          </div>
                          <div class="text-right">
                            <p class="text-sm font-semibold text-[#C05A3C]">{formatCurrency(addon.unit_price_monthly, addon.currency)}</p>
                            <p class="text-xs text-gray-500">x {addon.quantity} / mes</p>
                          </div>
                        </div>

                        {#if addon.catalog_item && isEmailPackage(addon.catalog_item)}
                          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
                            <div class="rounded border border-blue-100 bg-blue-50 px-3 py-2">
                              <p class="text-[10px] uppercase tracking-widest text-blue-700">Cuota mensual</p>
                              <p class="text-sm font-semibold text-blue-900">{formatInteger(Number(addon.catalog_item.metadata_json?.email_quota_monthly || 0))} emails</p>
                            </div>
                            <div class="rounded border border-emerald-100 bg-emerald-50 px-3 py-2">
                              <p class="text-[10px] uppercase tracking-widest text-emerald-700">Ventana 60 min</p>
                              <p class="text-sm font-semibold text-emerald-900">{formatInteger(Number(addon.catalog_item.metadata_json?.email_burst_limit_60m || 0))} envíos</p>
                            </div>
                            <div class="rounded border border-amber-100 bg-amber-50 px-3 py-2">
                              <p class="text-[10px] uppercase tracking-widest text-amber-700">Sobreuso</p>
                              <p class="text-sm font-semibold text-amber-900">{formatCurrency(Number(addon.catalog_item.metadata_json?.email_overage_price || 0), addon.currency)}</p>
                            </div>
                          </div>
                        {/if}
                      </div>
                    {/each}
                  </div>
                {/if}
              </div>

              <div class="card">
                <div class="mb-4">
                  <span class="section-heading block">CATÁLOGO DISPONIBLE</span>
                </div>

                {#if serviceCatalog.length === 0}
                  <div class="py-10 flex flex-col items-center gap-2 text-center">
                    <Package class="w-8 h-8 text-border-light" />
                    <p class="text-sm text-gray-500">No hay servicios disponibles en este momento.</p>
                  </div>
                {:else}
                  <div class="space-y-4">
                    {#each serviceCatalog as item}
                      <div class="rounded-xl border border-border-light bg-bg-page p-4">
                        <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                          <div class="flex-1">
                            <div class="flex items-center gap-2 flex-wrap">
                              <p class="font-semibold text-text-primary">{item.name}</p>
                              {#if item.is_included_in_plan}
                                <span class="badge badge-success">Incluido en tu plan</span>
                              {/if}
                              {#if item.discount_percent && item.discount_percent > 0}
                                <span class="badge badge-warning">-{item.discount_percent}%</span>
                              {/if}
                              {#if isEmailPackage(item)}
                                <span class="badge badge-info">Correo</span>
                              {/if}
                            </div>
                            {#if item.description}
                              <p class="text-sm text-gray-500 mt-1">{item.description}</p>
                            {/if}

                            {#if isEmailPackage(item)}
                              <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
                                <div class="rounded border border-blue-100 bg-blue-50 px-3 py-2">
                                  <p class="text-[10px] uppercase tracking-widest text-blue-700">Cuota mensual</p>
                                  <p class="text-sm font-semibold text-blue-900">{formatInteger(Number(item.metadata_json?.email_quota_monthly || 0))} emails</p>
                                </div>
                                <div class="rounded border border-emerald-100 bg-emerald-50 px-3 py-2">
                                  <p class="text-[10px] uppercase tracking-widest text-emerald-700">Ventana 60 min</p>
                                  <p class="text-sm font-semibold text-emerald-900">{formatInteger(Number(item.metadata_json?.email_burst_limit_60m || 0))} envíos</p>
                                </div>
                                <div class="rounded border border-amber-100 bg-amber-50 px-3 py-2">
                                  <p class="text-[10px] uppercase tracking-widest text-amber-700">Sobreuso</p>
                                  <p class="text-sm font-semibold text-amber-900">{formatCurrency(Number(item.metadata_json?.email_overage_price || 0), 'USD')}</p>
                                </div>
                              </div>
                            {/if}
                          </div>

                          <div class="w-full lg:w-56 rounded-lg border border-border-light bg-white px-4 py-3">
                            <p class="text-[10px] uppercase tracking-widest text-gray-500">Precio mensual</p>
                            <p class="text-2xl font-bold text-[#C05A3C] mt-1">{formatCurrency(item.effective_price_monthly ?? item.price_monthly, 'USD')}</p>
                            <p class="text-xs text-gray-500 mt-1">
                              {#if item.active_quantity && item.active_quantity > 0}
                                Activo: {item.active_quantity} paquete(s)
                              {:else}
                                Compra inmediata
                              {/if}
                            </p>

                            <button
                              class="btn btn-primary btn-sm w-full mt-4 flex items-center justify-center gap-2"
                              disabled={Boolean(item.is_included_in_plan) || purchasingServiceId === item.id}
                              on:click={() => purchaseAddon(item)}
                            >
                              {#if purchasingServiceId === item.id}
                                <Spinner size="sm" />
                              {/if}
                              {item.is_included_in_plan ? 'INCLUIDO' : item.active_quantity && item.active_quantity > 0 ? 'COMPRAR OTRO' : 'ADQUIRIR'}
                            </button>
                          </div>
                        </div>
                      </div>
                    {/each}
                  </div>
                {/if}
              </div>
            </div>
          {/if}
        </div>
      </div>

    <!-- ===== SEGURIDAD ===== -->
    {:else if activeTab === 'security'}
      <div class="card max-w-lg">
        <div class="flex items-center gap-3 mb-6">
          <div class="w-9 h-9 rounded-full bg-[#C05A3C]/10 flex items-center justify-center">
            <KeyRound class="w-5 h-5 text-[#C05A3C]" />
          </div>
          <div>
            <p class="font-semibold text-text-primary">Cambiar contraseña</p>
            <p class="text-xs text-gray-500">Actualiza tu contraseña de acceso al portal</p>
          </div>
        </div>

        <form on:submit|preventDefault={submitChangePassword} class="space-y-4">
          <div>
            <label for="tenant-current-password" class="block text-xs font-semibold text-text-secondary uppercase tracking-widest mb-1">Contraseña actual</label>
            <div class="relative">
              <input id="tenant-current-password" type={showCurrent ? 'text' : 'password'} bind:value={pwCurrent} required
                placeholder="••••••••" class="input input-bordered w-full pr-10" />
              <button type="button" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                on:click={() => showCurrent = !showCurrent}>
                <svelte:component this={showCurrent ? EyeOff : Eye} class="w-4 h-4" />
              </button>
            </div>
          </div>

          <div>
            <label for="tenant-new-password" class="block text-xs font-semibold text-text-secondary uppercase tracking-widest mb-1">Nueva contraseña</label>
            <div class="relative">
              <input id="tenant-new-password" type={showNew ? 'text' : 'password'} bind:value={pwNew} required minlength="8"
                placeholder="Mínimo 8 caracteres" class="input input-bordered w-full pr-10" />
              <button type="button" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                on:click={() => showNew = !showNew}>
                <svelte:component this={showNew ? EyeOff : Eye} class="w-4 h-4" />
              </button>
            </div>
          </div>

          <div>
            <label for="tenant-confirm-password" class="block text-xs font-semibold text-text-secondary uppercase tracking-widest mb-1">Confirmar nueva contraseña</label>
            <div class="relative">
              <input id="tenant-confirm-password" type={showConfirm ? 'text' : 'password'} bind:value={pwConfirm} required minlength="8"
                placeholder="Repite la nueva contraseña" class="input input-bordered w-full pr-10" />
              <button type="button" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                on:click={() => showConfirm = !showConfirm}>
                <svelte:component this={showConfirm ? EyeOff : Eye} class="w-4 h-4" />
              </button>
            </div>
          </div>

          {#if pwMsg}
            <div class="rounded border px-4 py-3 text-sm
              {pwMsgType === 'success' ? 'border-green-200 bg-green-50 text-green-700' : 'border-red-200 bg-red-50 text-red-700'}">
              {pwMsg}
            </div>
          {/if}

          <button type="submit" disabled={pwSubmitting}
            class="btn btn-primary w-full flex items-center justify-center gap-2">
            {#if pwSubmitting}<Spinner size="sm" />{/if}
            ACTUALIZAR CONTRASEÑA
          </button>
        </form>
      </div>

      <div class="card max-w-lg border-blue-200 bg-blue-50">
        <p class="text-sm font-semibold text-blue-800 mb-2">Recomendaciones de seguridad</p>
        <ul class="text-xs text-blue-700 space-y-1 list-disc list-inside">
          <li>Usa al menos 8 caracteres con letras y números</li>
          <li>No compartas tu contraseña con nadie</li>
          <li>Cambia tu contraseña periódicamente</li>
          <li>Evita usar la misma contraseña en otros servicios</li>
        </ul>
      </div>
    {/if}
  </main>
</div>

<!-- Modal: Agregar dominio -->
{#if showDomainModal}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
    <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-semibold text-text-primary">Agregar dominio personalizado</h3>
        <button class="text-gray-400 hover:text-gray-600" on:click={() => showDomainModal = false}>
          <XCircle class="w-5 h-5" />
        </button>
      </div>

      <p class="text-xs text-gray-500 mb-4">
        Introduce el dominio que quieres asociar a tu instancia Sajet.
        Después deberás crear un registro A hacia la IP pública de Sajet.
      </p>

      <form on:submit|preventDefault={submitDomain} class="space-y-4">
        <div>
          <label for="tenant-domain-input" class="block text-xs font-semibold text-text-secondary uppercase tracking-widest mb-1">Dominio</label>
          <input id="tenant-domain-input" type="text" bind:value={domainInput} placeholder="ej: miempresa.com" required
            class="input input-bordered w-full font-mono" />
        </div>

        {#if domainMsg}
          <div class="rounded border px-4 py-3 text-sm
            {domainMsgType === 'success' ? 'border-green-200 bg-green-50 text-green-700' : 'border-red-200 bg-red-50 text-red-700'}">
            {domainMsg}
          </div>
        {/if}

        <div class="flex gap-3">
          <button type="button" class="btn btn-ghost flex-1" on:click={() => showDomainModal = false}>
            Cancelar
          </button>
          <button type="submit" disabled={domainSubmitting}
            class="btn btn-primary flex-1 flex items-center justify-center gap-2">
            {#if domainSubmitting}<Spinner size="sm" />{/if}
            AGREGAR
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}
