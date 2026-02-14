<script lang="ts">
  import { onMount } from 'svelte';
  import { Badge, Button, Card, Spinner } from '../lib/components';
  import { billingApi } from '../lib/api';
  import type { BillingInvoice, BillingMetrics, StripeEventItem } from '../lib/types';
  import { formatCurrency, formatDate, formatPercent } from '../lib/utils/formatters';

  let loading = true;
  let error = '';
  let metrics: BillingMetrics | null = null;
  let invoices: BillingInvoice[] = [];
  let events: StripeEventItem[] = [];

  async function loadData() {
    loading = true;
    error = '';
    try {
      const [metricsData, invoicesData, eventsData] = await Promise.all([
        billingApi.getMetrics(),
        billingApi.getInvoices(30, 0),
        billingApi.getStripeEvents(20),
      ]);
      metrics = metricsData;
      invoices = invoicesData.invoices;
      events = eventsData.events;
    } catch (err) {
      error = err instanceof Error ? err.message : 'No se pudo cargar billing';
    } finally {
      loading = false;
    }
  }

  onMount(loadData);

  function statusVariant(status: string) {
    if (status === 'paid' || status === 'active') return 'success';
    if (status === 'pending') return 'warning';
    if (status === 'failed' || status === 'cancelled') return 'error';
    return 'secondary';
  }
</script>

<div class="p-6 lg:p-8 space-y-6">
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold text-white">Billing</h1>
      <p class="text-secondary-400 mt-1">Metricas financieras, facturas y eventos Stripe</p>
    </div>
    <Button variant="secondary" on:click={loadData}>Actualizar</Button>
  </div>

  {#if loading}
    <div class="py-16 flex justify-center"><Spinner size="lg" /></div>
  {:else if error}
    <Card>
      <p class="text-error text-sm">{error}</p>
    </Card>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <p class="text-xs uppercase tracking-wider text-secondary-500">MRR</p>
        <p class="mt-2 text-2xl font-bold text-white">{formatCurrency(metrics?.mrr_total || 0)}</p>
      </Card>
      <Card>
        <p class="text-xs uppercase tracking-wider text-secondary-500">Pendiente</p>
        <p class="mt-2 text-2xl font-bold text-white">{formatCurrency(metrics?.pending_amount || 0)}</p>
        <p class="text-xs text-secondary-500 mt-1">{metrics?.pending_count || 0} suscripciones</p>
      </Card>
      <Card>
        <p class="text-xs uppercase tracking-wider text-secondary-500">Churn 30d</p>
        <p class="mt-2 text-2xl font-bold text-white">{formatPercent(metrics?.churn_rate || 0, 1)}</p>
      </Card>
      <Card>
        <p class="text-xs uppercase tracking-wider text-secondary-500">Activas</p>
        <p class="mt-2 text-2xl font-bold text-white">{metrics?.total_active || 0}</p>
      </Card>
    </div>

    <Card title="Distribucion por plan" subtitle="/api/billing/metrics">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div class="p-4 rounded-lg bg-surface-highlight border border-surface-border">
          <p class="text-secondary-400">Basic</p>
          <p class="text-white font-semibold mt-1">{metrics?.plan_distribution.basic.count || 0} tenants</p>
          <p class="text-secondary-500">{formatCurrency(metrics?.plan_distribution.basic.revenue || 0)}</p>
        </div>
        <div class="p-4 rounded-lg bg-surface-highlight border border-surface-border">
          <p class="text-secondary-400">Pro</p>
          <p class="text-white font-semibold mt-1">{metrics?.plan_distribution.pro.count || 0} tenants</p>
          <p class="text-secondary-500">{formatCurrency(metrics?.plan_distribution.pro.revenue || 0)}</p>
        </div>
        <div class="p-4 rounded-lg bg-surface-highlight border border-surface-border">
          <p class="text-secondary-400">Enterprise</p>
          <p class="text-white font-semibold mt-1">{metrics?.plan_distribution.enterprise.count || 0} tenants</p>
          <p class="text-secondary-500">{formatCurrency(metrics?.plan_distribution.enterprise.revenue || 0)}</p>
        </div>
      </div>
    </Card>

    <Card title="Facturas" subtitle="/api/billing/invoices" padding="none">
      <div class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr>
              <th>Cliente</th>
              <th>Plan</th>
              <th>Monto</th>
              <th>Estado</th>
              <th>Fecha</th>
            </tr>
          </thead>
          <tbody>
            {#each invoices as invoice}
              <tr>
                <td>
                  <p class="font-medium text-white">{invoice.company_name}</p>
                  <p class="text-xs text-secondary-500">{invoice.email}</p>
                </td>
                <td class="text-secondary-300">{invoice.plan}</td>
                <td class="text-secondary-300">{formatCurrency(invoice.amount)}</td>
                <td><Badge variant={statusVariant(invoice.status)}>{invoice.status}</Badge></td>
                <td class="text-secondary-300">{formatDate(invoice.created_at, { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</td>
              </tr>
            {:else}
              <tr>
                <td colspan="5" class="text-center text-secondary-500 py-8">No hay facturas disponibles</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </Card>

    <Card title="Eventos Stripe" subtitle="/api/billing/stripe-events" padding="none">
      <div class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr>
              <th>Event ID</th>
              <th>Tipo</th>
              <th>Procesado</th>
              <th>Fecha</th>
            </tr>
          </thead>
          <tbody>
            {#each events as event}
              <tr>
                <td class="font-mono text-xs text-secondary-300">{event.event_id}</td>
                <td class="text-secondary-300">{event.event_type}</td>
                <td>
                  <Badge variant={event.processed ? 'success' : 'warning'}>{event.processed ? 'si' : 'no'}</Badge>
                </td>
                <td class="text-secondary-300">{formatDate(event.created_at, { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</td>
              </tr>
            {:else}
              <tr>
                <td colspan="4" class="text-center text-secondary-500 py-8">No hay eventos recientes</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </Card>
  {/if}
</div>
