<script lang="ts">
  import { onMount } from 'svelte';
  import { auth, currentUser } from '../lib/stores';
  import { Badge, Button, Card, Spinner } from '../lib/components';
  import { api, portalApi } from '../lib/api';
  import type { Domain, TenantPortalBilling, TenantPortalInfo } from '../lib/types';
  import { formatCurrency, formatDate } from '../lib/utils/formatters';

  let loading = true;
  let actionLoading = false;
  let error = '';
  let info: TenantPortalInfo | null = null;
  let billing: TenantPortalBilling | null = null;
  let domains: Domain[] = [];

  async function loadPortal() {
    loading = true;
    error = '';
    try {
      const [infoData, billingData, domainsData] = await Promise.all([
        portalApi.getInfo(),
        portalApi.getBilling().catch(() => ({ invoices: [], payment_method: null })),
        api.get<{ items: Domain[] }>('/api/domains/my-domains').catch(() => ({ items: [] })),
      ]);
      info = infoData;
      billing = billingData;
      domains = domainsData.items || [];
    } catch (err) {
      error = err instanceof Error ? err.message : 'No se pudo cargar portal tenant';
    } finally {
      loading = false;
    }
  }

  onMount(loadPortal);

  function handleLogout() {
    auth.logout();
    window.location.hash = '#/login';
  }

  function statusVariant(status: string) {
    if (status === 'active') return 'success';
    if (status === 'pending' || status === 'past_due') return 'warning';
    if (status === 'cancelled') return 'error';
    return 'secondary';
  }

  async function updatePayment() {
    actionLoading = true;
    error = '';
    try {
      const response = await portalApi.updatePaymentMethod();
      if (response.checkout_url) {
        window.location.href = response.checkout_url;
        return;
      }
      error = response.message || 'No se pudo generar checkout de pago';
    } catch (err) {
      error = err instanceof Error ? err.message : 'No se pudo iniciar actualizacion de pago';
    } finally {
      actionLoading = false;
    }
  }

  async function cancelSubscription() {
    if (!confirm('¿Confirmas cancelar tu suscripcion al cierre del periodo?')) {
      return;
    }

    actionLoading = true;
    error = '';
    try {
      const response = await portalApi.cancelSubscription();
      alert(response.message || 'Suscripcion cancelada');
      await loadPortal();
    } catch (err) {
      error = err instanceof Error ? err.message : 'No se pudo cancelar suscripcion';
    } finally {
      actionLoading = false;
    }
  }

</script>

<div class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
  <header class="bg-slate-800/60 border-b border-slate-700 backdrop-blur-sm sticky top-0 z-10">
    <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-emerald-500 flex items-center justify-center">
          <span class="text-slate-900 font-bold text-xl">J</span>
        </div>
        <div>
          <span class="text-xl font-bold text-white">Portal tenant</span>
          <p class="text-sm text-slate-400">{$currentUser?.company_name || info?.company_name || 'Jeturing ERP'}</p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <div class="text-right hidden sm:block">
          <p class="text-sm text-white">{$currentUser?.email || info?.email || 'tenant'}</p>
          {#if info}
            <Badge variant={statusVariant(info.status)}>{info.status}</Badge>
          {/if}
        </div>
        <Button variant="secondary" size="sm" on:click={handleLogout}>Cerrar sesion</Button>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 py-8 space-y-6">
    {#if error}
      <div class="rounded-lg border border-error/30 bg-error/10 px-4 py-3 text-sm text-error">{error}</div>
    {/if}

    {#if loading}
      <div class="py-16 flex justify-center"><Spinner size="lg" /></div>
    {:else if info}
      <div class="bg-gradient-to-r from-emerald-600 to-teal-600 rounded-2xl p-8 shadow-xl">
        <h1 class="text-3xl font-bold text-white mb-2">Hola, {$currentUser?.username || info.company_name}</h1>
        <p class="text-emerald-100">Gestiona tu cuenta, facturacion y dominios desde un solo portal.</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <div class="p-2">
            <p class="text-sm text-slate-400">Plan actual</p>
            <p class="text-2xl font-bold text-white capitalize">{info.plan || $currentUser?.plan || 'basic'}</p>
          </div>
        </Card>

        <Card>
          <div class="p-2">
            <p class="text-sm text-slate-400">Dominios activos</p>
            <p class="text-2xl font-bold text-white">{domains.filter((item) => item.is_active).length}</p>
          </div>
        </Card>

        <Card>
          <div class="p-2">
            <p class="text-sm text-slate-400">Subdominio</p>
            <p class="text-2xl font-bold text-white">{info.subdomain}.sajet.us</p>
          </div>
        </Card>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card title="Mis dominios" subtitle="/api/domains/my-domains" padding="none">
          <div class="p-4 space-y-3">
            {#each domains as domain}
              <div class="bg-slate-800/40 rounded-lg p-4 border border-slate-700 flex items-center justify-between gap-3">
                <div>
                  <p class="font-medium text-white">{domain.external_domain}</p>
                  <p class="text-xs text-slate-400">{domain.sajet_full_domain}</p>
                </div>
                <Badge variant={domain.is_active ? 'success' : domain.verification_status === 'pending' ? 'warning' : 'secondary'}>
                  {domain.is_active ? 'activo' : domain.verification_status}
                </Badge>
              </div>
            {:else}
              <p class="text-sm text-slate-400">Aun no tienes dominios personalizados configurados.</p>
            {/each}
          </div>
        </Card>

        <Card title="Facturacion" subtitle="/tenant/api/billing" padding="none">
          <div class="p-4 space-y-4">
            {#if billing?.payment_method}
              <div class="rounded-lg border border-slate-700 p-3 bg-slate-800/30">
                <p class="text-sm text-slate-400">Metodo de pago</p>
                <p class="text-white font-medium mt-1 capitalize">
                  {billing.payment_method.brand} **** {billing.payment_method.last4}
                </p>
                <p class="text-xs text-slate-500">Expira {billing.payment_method.exp_month}/{billing.payment_method.exp_year}</p>
              </div>
            {:else}
              <p class="text-sm text-slate-400">No hay metodo de pago registrado.</p>
            {/if}

            <div class="space-y-2 max-h-60 overflow-auto pr-1">
              {#each billing?.invoices || [] as invoice}
                <div class="rounded-lg border border-slate-700 p-3 bg-slate-800/30 flex items-center justify-between gap-3">
                  <div>
                    <p class="text-sm text-white">{formatCurrency(invoice.amount, { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2 })} {invoice.currency.toUpperCase()}</p>
                    <p class="text-xs text-slate-500">{formatDate(invoice.date)}</p>
                  </div>
                  <Badge variant={invoice.status === 'paid' ? 'success' : invoice.status === 'open' ? 'warning' : 'secondary'}>
                    {invoice.status}
                  </Badge>
                </div>
              {:else}
                <p class="text-sm text-slate-400">No hay facturas registradas.</p>
              {/each}
            </div>

            <div class="flex flex-wrap gap-2 pt-2">
              <Button variant="primary" on:click={updatePayment} loading={actionLoading}>Actualizar pago</Button>
              <Button variant="danger" on:click={cancelSubscription} disabled={actionLoading}>Cancelar suscripcion</Button>
            </div>
          </div>
        </Card>
      </div>

      <Card title="Acceso rapido">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <a
            href={info.odoo_url || `https://${info.subdomain}.sajet.us`}
            target="_blank"
            rel="noreferrer"
            class="block p-4 rounded-lg bg-slate-800/50 border border-slate-700 hover:border-emerald-500/50 transition-colors"
          >
            <p class="text-white font-medium">Abrir Sajet ERP</p>
            <p class="text-sm text-slate-400">Acceso al sistema productivo</p>
          </a>

          <a
            href={billing?.invoices?.[0]?.hosted_url || 'mailto:soporte@jeturing.net'}
            target="_blank"
            rel="noreferrer"
            class="block p-4 rounded-lg bg-slate-800/50 border border-slate-700 hover:border-emerald-500/50 transition-colors"
          >
            <p class="text-white font-medium">Ultima factura</p>
            <p class="text-sm text-slate-400">Abrir factura hospedada en Stripe</p>
          </a>

          <a
            href="mailto:soporte@jeturing.net"
            class="block p-4 rounded-lg bg-slate-800/50 border border-slate-700 hover:border-emerald-500/50 transition-colors"
          >
            <p class="text-white font-medium">Soporte tecnico</p>
            <p class="text-sm text-slate-400">soporte@jeturing.net</p>
          </a>
        </div>
      </Card>
    {/if}
  </main>
</div>
