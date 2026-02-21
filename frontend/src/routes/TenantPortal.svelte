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
  import type { TenantPortalInfo, TenantPortalBilling } from '../lib/types';
  import type { PortalDomain, PortalUsersResponse } from '../lib/api/portal';
  import { formatDate } from '../lib/utils/formatters';

  // ── Estado global ──
  let loading = true;
  let error = '';
  let info: TenantPortalInfo | null = null;
  let billing: TenantPortalBilling | null = null;

  // ── Tabs ──
  type Tab = 'dashboard' | 'domains' | 'users' | 'security';
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

  async function switchTab(tab: Tab) {
    activeTab = tab;
    if (tab === 'domains' && domains.length === 0 && !domainsLoading) loadDomains();
    if (tab === 'users' && !usersData && !usersLoading) loadUsers();
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

  function handleLogout() {
    auth.logout();
    window.location.hash = '#/login';
  }

  function statusBadgeClass(status: string): string {
    if (status === 'active') return 'badge-success';
    if (status === 'pending' || status === 'past_due') return 'badge-warning';
    if (status === 'cancelled' || status === 'suspended') return 'badge-error';
    return 'badge-neutral';
  }

  function invoiceStatusClass(status: string): string {
    if (status === 'paid') return 'badge-success';
    if (status === 'open') return 'badge-warning';
    if (status === 'void' || status === 'uncollectible') return 'badge-error';
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
      HWM_SNAPSHOT: 'Snapshot HWM',
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
              ABRIR MI ODOO
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
                      {#if invoice.pdf_url || invoice.hosted_url}
                        <a href={invoice.pdf_url || invoice.hosted_url} target="_blank" rel="noreferrer"
                          class="btn btn-secondary btn-sm inline-flex items-center gap-1">
                          <Download class="w-3 h-3" /> DESCARGAR
                        </a>
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
            <p class="text-xs text-gray-500 mt-1">Asocia tu propio dominio a tu instancia Odoo</p>
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
          <li>En tu proveedor DNS crea un registro CNAME apuntando a:</li>
        </ol>
        <div class="mt-2 p-2 bg-amber-100 rounded font-mono text-xs text-amber-900">
          {info?.subdomain || 'tusubdominio'}.sajet.us
        </div>
        <p class="text-xs text-amber-600 mt-2">La verificación puede tardar hasta 48 horas.</p>
      </div>

    <!-- ===== USUARIOS ===== -->
    {:else if activeTab === 'users'}
      <div class="card">
        <span class="section-heading block mb-5">USUARIOS EN MI INSTANCIA</span>

        {#if usersLoading}
          <div class="py-10 flex justify-center"><Spinner /></div>
        {:else if usersError}
          <div class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{usersError}</div>
        {:else if usersData}
          <div class="grid grid-cols-2 gap-4 mb-6">
            <div class="rounded border border-border-light bg-bg-page p-4 text-center">
              <p class="text-3xl font-bold text-text-primary">{usersData.current_user_count}</p>
              <p class="text-xs text-gray-500 mt-1 uppercase tracking-widest">Usuarios activos</p>
            </div>
            <div class="rounded border border-border-light bg-bg-page p-4 text-center">
              <p class="text-3xl font-bold text-[#C05A3C]">{usersData.plan_user_limit}</p>
              <p class="text-xs text-gray-500 mt-1 uppercase tracking-widest">Límite del plan</p>
            </div>
          </div>

          {#if usersData.plan_user_limit > 0}
            {@const pct = Math.min(100, Math.round((usersData.current_user_count / usersData.plan_user_limit) * 100))}
            <div class="mb-6">
              <div class="flex justify-between text-xs text-gray-500 mb-1">
                <span>Uso de licencias</span><span>{pct}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div
                  class="h-2 rounded-full transition-all {pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-amber-500' : 'bg-emerald-500'}"
                  style="width: {pct}%"
                ></div>
              </div>
            </div>
          {/if}

          {#if usersData.seat_events.length > 0}
            <div class="border-t border-border-light pt-4">
              <p class="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">Historial de actividad</p>
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
                        {#if event.odoo_login}
                          <span class="text-gray-500 ml-2 font-mono text-xs">{event.odoo_login}</span>
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
            </div>
          {:else}
            <div class="py-8 flex flex-col items-center gap-2 text-center border-t border-border-light mt-4 pt-8">
              <Users class="w-8 h-8 text-border-light" />
              <p class="text-sm text-gray-500">No hay eventos de usuarios registrados aún</p>
            </div>
          {/if}
        {/if}
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
            <label class="block text-xs font-semibold text-text-secondary uppercase tracking-widest mb-1">Contraseña actual</label>
            <div class="relative">
              <input type={showCurrent ? 'text' : 'password'} bind:value={pwCurrent} required
                placeholder="••••••••" class="input input-bordered w-full pr-10" />
              <button type="button" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                on:click={() => showCurrent = !showCurrent}>
                <svelte:component this={showCurrent ? EyeOff : Eye} class="w-4 h-4" />
              </button>
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-text-secondary uppercase tracking-widest mb-1">Nueva contraseña</label>
            <div class="relative">
              <input type={showNew ? 'text' : 'password'} bind:value={pwNew} required minlength="8"
                placeholder="Mínimo 8 caracteres" class="input input-bordered w-full pr-10" />
              <button type="button" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                on:click={() => showNew = !showNew}>
                <svelte:component this={showNew ? EyeOff : Eye} class="w-4 h-4" />
              </button>
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-text-secondary uppercase tracking-widest mb-1">Confirmar nueva contraseña</label>
            <div class="relative">
              <input type={showConfirm ? 'text' : 'password'} bind:value={pwConfirm} required minlength="8"
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
        Introduce el dominio que quieres asociar a tu instancia Odoo.
        Después deberás crear un registro CNAME en tu proveedor DNS.
      </p>

      <form on:submit|preventDefault={submitDomain} class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-text-secondary uppercase tracking-widest mb-1">Dominio</label>
          <input type="text" bind:value={domainInput} placeholder="ej: miempresa.com" required
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
