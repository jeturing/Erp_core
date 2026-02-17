<script lang="ts">
  import { onMount } from 'svelte';
  import {
    ExternalLink, Download, LogOut, Package, Users, Headphones,
    LayoutGrid, ChartColumn, FileText, CircleUser, BookOpen,
    Building2
  } from 'lucide-svelte';
  import { auth, currentUser } from '../lib/stores';
  import { Spinner } from '../lib/components';
  import portalApi from '../lib/api/portal';
  import type { TenantPortalInfo, TenantPortalBilling } from '../lib/types';
  import { formatDate } from '../lib/utils/formatters';

  let loading = true;
  let error = '';
  let info: TenantPortalInfo | null = null;
  let billing: TenantPortalBilling | null = null;

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
      <!-- Logo -->
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded bg-[#C05A3C] flex items-center justify-center">
          <span class="text-white font-bold text-sm">S</span>
        </div>
        <span class="text-white font-semibold tracking-[0.05em] text-sm">SAJET</span>
      </div>

      <!-- Company name (center) -->
      <div class="flex items-center gap-2">
        <Building2 class="w-4 h-4 text-gray-400" />
        <span class="text-gray-300 text-sm font-medium">
          {$currentUser?.company_name || info?.company_name || 'Empresa Alpha SRL'}
        </span>
        {#if info}
          <span class="badge {statusBadgeClass(info.status)} ml-1">{info.status}</span>
        {/if}
      </div>

      <!-- Logout -->
      <button
        class="flex items-center gap-1.5 text-[11px] font-semibold tracking-[0.08em] text-gray-400 hover:text-white uppercase transition-colors"
        on:click={handleLogout}
      >
        <LogOut class="w-3.5 h-3.5" />
        CERRAR SESIÓN
      </button>
    </div>
  </header>

  <main class="max-w-6xl mx-auto px-6 py-8 space-y-6">
    {#if error}
      <div class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
    {/if}

    {#if loading}
      <div class="py-24 flex justify-center">
        <Spinner size="lg" />
      </div>
    {:else if info}
      <!-- 2-column top section -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- LEFT: Plan card -->
        <div class="card flex flex-col gap-4">
          <div>
            <span class="section-heading block mb-3">MI PLAN ACTUAL</span>
            <div class="flex items-baseline gap-3 mb-1">
              <span class="text-2xl font-bold text-text-primary capitalize">
                {info.plan || 'Pro'}
              </span>
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
            <button class="btn btn-ghost btn-sm w-full border border-border-light">
              CAMBIAR PLAN
            </button>
          </div>
        </div>

        <!-- RIGHT: My instances -->
        <div class="card flex flex-col gap-4">
          <span class="section-heading block">MIS INSTANCIAS</span>

          <div class="rounded border border-border-light bg-bg-page p-4 space-y-3">
            <div class="flex items-center justify-between">
              <span class="font-mono text-sm font-semibold text-text-primary">
                {info.subdomain}.sajet.us
              </span>
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
              target="_blank"
              rel="noreferrer"
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

      <!-- FULL WIDTH: Mis Facturas -->
      <div class="card p-0 overflow-hidden">
        <div class="px-6 py-4 border-b border-border-light">
          <span class="section-heading">MIS FACTURAS</span>
        </div>

        {#if billing?.invoices && billing.invoices.length > 0}
          <div class="overflow-x-auto">
            <table class="table w-full">
              <thead>
                <tr>
                  <th>Número</th>
                  <th>Monto</th>
                  <th>Estado</th>
                  <th>Fecha</th>
                  <th>Acción</th>
                </tr>
              </thead>
              <tbody>
                {#each billing.invoices as invoice}
                  <tr>
                    <td>
                      <span class="font-mono text-xs text-text-secondary">#{invoice.id.slice(-8).toUpperCase()}</span>
                    </td>
                    <td>
                      <span class="text-sm font-semibold text-text-primary">
                        {formatCurrency(invoice.amount, invoice.currency)}
                      </span>
                    </td>
                    <td>
                      <span class="badge {invoiceStatusClass(invoice.status)}">{invoice.status}</span>
                    </td>
                    <td>
                      <span class="text-xs text-text-secondary">{formatDate(invoice.date)}</span>
                    </td>
                    <td>
                      {#if invoice.pdf_url || invoice.hosted_url}
                        <a
                          href={invoice.pdf_url || invoice.hosted_url}
                          target="_blank"
                          rel="noreferrer"
                          class="btn btn-secondary btn-sm inline-flex items-center gap-1"
                        >
                          <Download class="w-3 h-3" />
                          DESCARGAR
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

      <!-- FULL WIDTH: Apps instaladas -->
      <div class="card">
        <div class="mb-4">
          <span class="section-heading block">APPS INSTALADAS EN TU INSTANCIA</span>
        </div>
        <div class="grid grid-cols-3 sm:grid-cols-6 gap-4">
          {#each installedApps as app}
            <div class="flex flex-col items-center gap-2 p-3 rounded border border-border-light bg-bg-page hover:border-[#C05A3C] transition-colors cursor-default">
              <svelte:component this={app.icon} class="w-6 h-6 {app.color}" />
              <span class="text-[10px] font-semibold text-text-secondary text-center uppercase tracking-[0.06em]">{app.label}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  </main>
</div>
