<script lang="ts">
  import { onMount } from 'svelte';
  import api from '../lib/api/client';
  import { toasts } from '../lib/stores';
  import { formatDate } from '../lib/utils/formatters';
  import {
    BarChart2, RefreshCw, TrendingUp, Users, Handshake, Target,
    Server, ClipboardList, FileText, CheckCircle, XCircle,
    AlertTriangle, DollarSign, Activity,
  } from 'lucide-svelte';

  let data: any = null;
  let loading = true;
  let generatedAt: string | null = null;

  async function load() {
    loading = true;
    try {
      data = await api.get('/api/reports/overview');
      generatedAt = data?.generated_at ?? null;
    } catch (e: any) {
      toasts.error(e.message ?? 'Error cargando reportes');
    } finally {
      loading = false;
    }
  }

  function fmt(n: number, decimals = 0): string {
    return (n ?? 0).toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  }

  function fmtUSD(n: number): string {
    return '$' + fmt(n, 2);
  }

  function pct(used: number, total: number): number {
    if (!total) return 0;
    return Math.round((used / total) * 100);
  }

  function healthColor(status: string): string {
    if (status === 'ok') return 'text-green-400';
    if (status === 'warning') return 'text-yellow-400';
    return 'text-red-400';
  }

  function healthIcon(status: string) {
    if (status === 'ok') return CheckCircle;
    if (status === 'warning') return AlertTriangle;
    return XCircle;
  }

  onMount(load);
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div>
      <h1 class="page-title flex items-center gap-2"><BarChart2 size={24} /> Reportes</h1>
      <p class="page-subtitle">
        Vista consolidada de KPIs del negocio
        {#if generatedAt}<span class="ml-1 text-[11px] opacity-50">· {formatDate(generatedAt)}</span>{/if}
      </p>
    </div>
    <button class="btn-secondary flex items-center gap-2" on:click={load} disabled={loading}>
      <RefreshCw size={14} class={loading ? 'animate-spin' : ''} /> Actualizar
    </button>
  </div>

  {#if loading}
    <div class="card p-10 text-center text-gray-500">
      <RefreshCw size={24} class="animate-spin mx-auto mb-3" />
      Cargando reportes...
    </div>
  {:else if !data}
    <div class="card p-8 text-center text-gray-500">No hay datos disponibles.</div>
  {:else}

    <!-- Revenue KPIs -->
    <section>
      <h2 class="section-title flex items-center gap-2 mb-3"><TrendingUp size={16} /> Revenue</h2>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div class="card p-4">
          <p class="text-xs text-gray-500 mb-1">MRR</p>
          <p class="text-2xl font-bold text-green-400">{fmtUSD(data.revenue?.mrr)}</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-gray-500 mb-1">ARR</p>
          <p class="text-2xl font-bold">{fmtUSD(data.revenue?.arr)}</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-gray-500 mb-1">Pendiente cobro</p>
          <p class="text-2xl font-bold text-yellow-400">{fmtUSD(data.revenue?.pending_amount)}</p>
          <p class="text-[10px] text-gray-500">{data.revenue?.pending_count} suscripciones</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-gray-500 mb-1">Churn (30d)</p>
          <p class="text-2xl font-bold {data.revenue?.churn_rate > 5 ? 'text-red-400' : ''}">{fmt(data.revenue?.churn_rate, 1)}%</p>
          <p class="text-[10px] text-gray-500">{data.revenue?.cancelled_30d} cancelaciones</p>
        </div>
      </div>
      <div class="grid grid-cols-2 sm:grid-cols-3 gap-4 mt-4">
        <div class="card p-4">
          <p class="text-xs text-gray-500 mb-1">Total usuarios activos</p>
          <p class="text-xl font-bold">{fmt(data.revenue?.total_users)}</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-gray-500 mb-1">Nuevos este mes</p>
          <p class="text-xl font-bold text-blue-400">{data.revenue?.new_this_month ?? 0}</p>
        </div>
        <!-- Plan distribution -->
        <div class="card p-4">
          <p class="text-xs text-gray-500 mb-2">Distribución de planes</p>
          <div class="space-y-1">
            {#each Object.entries(data.revenue?.plan_distribution ?? {}) as [plan, info]}
              <div class="flex items-center justify-between text-xs">
                <span class="capitalize text-gray-400">{plan}</span>
                <span class="font-mono">{(info as any).count}</span>
              </div>
            {/each}
          </div>
        </div>
      </div>
    </section>

    <!-- Customers & Partners -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <section class="card p-5">
        <h2 class="text-sm font-semibold mb-3 flex items-center gap-2"><Users size={15} /> Clientes</h2>
        <div class="grid grid-cols-3 gap-3 text-center">
          <div>
            <p class="text-2xl font-bold">{data.customers?.total ?? 0}</p>
            <p class="text-[10px] text-gray-500">Total</p>
          </div>
          <div>
            <p class="text-2xl font-bold text-green-400">{data.customers?.active ?? 0}</p>
            <p class="text-[10px] text-gray-500">Activos</p>
          </div>
          <div>
            <p class="text-2xl font-bold text-red-400">{data.customers?.suspended ?? 0}</p>
            <p class="text-[10px] text-gray-500">Suspendidos</p>
          </div>
        </div>
      </section>

      <section class="card p-5">
        <h2 class="text-sm font-semibold mb-3 flex items-center gap-2"><Handshake size={15} /> Partners</h2>
        <div class="grid grid-cols-3 gap-3 text-center">
          <div>
            <p class="text-2xl font-bold">{data.partners?.total ?? 0}</p>
            <p class="text-[10px] text-gray-500">Total</p>
          </div>
          <div>
            <p class="text-2xl font-bold text-green-400">{data.partners?.active ?? 0}</p>
            <p class="text-[10px] text-gray-500">Activos</p>
          </div>
          <div>
            <p class="text-2xl font-bold text-yellow-400">{data.partners?.pending ?? 0}</p>
            <p class="text-[10px] text-gray-500">Pendientes</p>
          </div>
        </div>
      </section>
    </div>

    <!-- Leads & Commissions -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <section class="card p-5">
        <h2 class="text-sm font-semibold mb-3 flex items-center gap-2"><Target size={15} /> Leads</h2>
        <div class="grid grid-cols-3 gap-3 text-center mb-3">
          <div>
            <p class="text-xl font-bold">{data.leads?.total ?? 0}</p>
            <p class="text-[10px] text-gray-500">Total</p>
          </div>
          <div>
            <p class="text-xl font-bold text-blue-400">{data.leads?.active ?? 0}</p>
            <p class="text-[10px] text-gray-500">Activos</p>
          </div>
          <div>
            <p class="text-xl font-bold text-green-400">{data.leads?.won ?? 0}</p>
            <p class="text-[10px] text-gray-500">Ganados</p>
          </div>
        </div>
        <div class="border-t border-border-light pt-3">
          <p class="text-xs text-gray-500">Pipeline total</p>
          <p class="text-lg font-bold text-yellow-400">{fmtUSD(data.leads?.pipeline_value)}</p>
        </div>
      </section>

      <section class="card p-5">
        <h2 class="text-sm font-semibold mb-3 flex items-center gap-2"><DollarSign size={15} /> Comisiones</h2>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between">
            <span class="text-gray-400">Total partners</span>
            <span class="font-mono">{fmtUSD(data.commissions?.total_partner)}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-400">Pendiente</span>
            <span class="font-mono text-yellow-400">{fmtUSD(data.commissions?.pending)}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-400">Pagado</span>
            <span class="font-mono text-green-400">{fmtUSD(data.commissions?.paid)}</span>
          </div>
          <div class="flex justify-between border-t border-border-light pt-2">
            <span class="text-gray-500 text-xs">Jeturing share</span>
            <span class="font-mono text-xs">{fmtUSD(data.commissions?.jeturing_share)}</span>
          </div>
        </div>
      </section>
    </div>

    <!-- Work Orders & Invoices -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <section class="card p-5">
        <h2 class="text-sm font-semibold mb-3 flex items-center gap-2"><ClipboardList size={15} /> Work Orders</h2>
        <div class="grid grid-cols-2 gap-3">
          <div class="text-center">
            <p class="text-2xl font-bold">{data.work_orders?.total ?? 0}</p>
            <p class="text-[10px] text-gray-500">Total</p>
          </div>
          <div class="text-center">
            <p class="text-2xl font-bold text-green-400">{data.work_orders?.completed ?? 0}</p>
            <p class="text-[10px] text-gray-500">Completadas</p>
          </div>
          <div class="text-center">
            <p class="text-xl font-bold text-yellow-400">{data.work_orders?.in_progress ?? 0}</p>
            <p class="text-[10px] text-gray-500">En progreso</p>
          </div>
          <div class="text-center">
            <p class="text-xl font-bold text-gray-400">{data.work_orders?.requested ?? 0}</p>
            <p class="text-[10px] text-gray-500">Solicitadas</p>
          </div>
        </div>
      </section>

      <section class="card p-5">
        <h2 class="text-sm font-semibold mb-3 flex items-center gap-2"><FileText size={15} /> Facturas</h2>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between">
            <span class="text-gray-400">Total facturas</span>
            <span class="font-mono">{data.invoices?.total ?? 0}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-400">Pagadas</span>
            <span class="font-mono text-green-400">{data.invoices?.paid ?? 0}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-400">Pendientes</span>
            <span class="font-mono text-yellow-400">{data.invoices?.pending ?? 0}</span>
          </div>
          <div class="flex justify-between border-t border-border-light pt-2">
            <span class="text-gray-500 text-xs">Monto cobrado</span>
            <span class="font-mono text-xs text-green-400">{fmtUSD(data.invoices?.paid_amount)}</span>
          </div>
        </div>
      </section>
    </div>

    <!-- Infrastructure -->
    {#if data.infrastructure}
      <section class="card p-5">
        <h2 class="text-sm font-semibold mb-4 flex items-center gap-2"><Server size={15} /> Infraestructura</h2>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
          {#each [
            { label: 'CPU', used: data.infrastructure.cpu?.percent ?? 0 },
            { label: 'RAM', used: data.infrastructure.ram?.percent ?? 0 },
            { label: 'Disco', used: data.infrastructure.disk?.percent ?? 0 },
          ] as res}
            <div>
              <div class="flex justify-between text-xs mb-1">
                <span class="text-gray-400">{res.label}</span>
                <span class="font-mono {res.used > 90 ? 'text-red-400' : res.used > 75 ? 'text-yellow-400' : ''}">{res.used}%</span>
              </div>
              <div class="h-2 bg-bg-page rounded-full overflow-hidden">
                <div
                  class="h-2 rounded-full {res.used > 90 ? 'bg-red-500' : res.used > 75 ? 'bg-yellow-500' : 'bg-green-500'}"
                  style="width: {res.used}%"
                ></div>
              </div>
            </div>
          {/each}
        </div>
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span class="text-gray-500 text-xs">Nodos</span>
            <p>{data.infrastructure.nodes_online}/{data.infrastructure.nodes_total} online</p>
          </div>
          <div>
            <span class="text-gray-500 text-xs">Contenedores</span>
            <p>{data.infrastructure.containers_running}/{data.infrastructure.containers_total} running</p>
          </div>
        </div>
      </section>
    {/if}

    <!-- System Health -->
    {#if data.system_health?.length}
      <section class="card p-5">
        <h2 class="text-sm font-semibold mb-3 flex items-center gap-2"><Activity size={15} /> System Health</h2>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {#each data.system_health as item}
            <div class="flex items-start gap-2">
              <svelte:component this={healthIcon(item.status)} size={14} class="{healthColor(item.status)} mt-0.5 flex-shrink-0" />
              <div>
                <p class="text-sm font-medium">{item.name}</p>
                <p class="text-[11px] text-gray-500">{item.detail}</p>
              </div>
            </div>
          {/each}
        </div>
      </section>
    {/if}

    <!-- Top Partners -->
    {#if data.partners?.top?.length}
      <section class="card p-5">
        <h2 class="text-sm font-semibold mb-3 flex items-center gap-2"><Handshake size={15} /> Top Partners por Revenue</h2>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-border-light text-xs text-gray-500">
                <th class="text-left py-2 pr-4">Partner</th>
                <th class="text-right py-2 pr-4">Leads</th>
                <th class="text-right py-2 pr-4">Revenue</th>
                <th class="text-right py-2">Comisiones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border-light">
              {#each data.partners.top as p}
                <tr class="hover:bg-bg-page transition-colors">
                  <td class="py-2 pr-4 font-medium">{p.company_name}</td>
                  <td class="py-2 pr-4 text-right text-gray-400">{p.leads}</td>
                  <td class="py-2 pr-4 text-right font-mono">{fmtUSD(p.total_revenue)}</td>
                  <td class="py-2 text-right font-mono text-green-400">{fmtUSD(p.total_commissions)}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </section>
    {/if}

    <!-- Recent Activity -->
    {#if data.recent_activity?.length}
      <section class="card p-5">
        <h2 class="text-sm font-semibold mb-3 flex items-center gap-2"><Activity size={15} /> Actividad Reciente</h2>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-border-light text-xs text-gray-500">
                <th class="text-left py-2 pr-4">Empresa</th>
                <th class="text-left py-2 pr-4">Subdominio</th>
                <th class="text-left py-2 pr-4">Plan</th>
                <th class="text-right py-2 pr-4">MRR</th>
                <th class="text-right py-2">Alta</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border-light">
              {#each data.recent_activity as c}
                <tr class="hover:bg-bg-page transition-colors">
                  <td class="py-2 pr-4 font-medium">{c.company_name}</td>
                  <td class="py-2 pr-4 font-mono text-xs text-gray-400">{c.subdomain}</td>
                  <td class="py-2 pr-4 capitalize">{c.plan}</td>
                  <td class="py-2 pr-4 text-right font-mono text-green-400">{fmtUSD(c.monthly_amount)}</td>
                  <td class="py-2 text-right text-[11px] text-gray-500">{formatDate(c.created_at)}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </section>
    {/if}

  {/if}
</div>
