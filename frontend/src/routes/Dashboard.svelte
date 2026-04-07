<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { dashboard, auth } from '../lib/stores';
  import { formatCurrency, formatDate } from '../lib/utils/formatters';
  import {
    RefreshCw, CircleAlert, CircleCheck, TriangleAlert, CircleX,
    TrendingUp, TrendingDown, Users, Handshake, Target, DollarSign,
    Server, HardDrive, Cpu, MemoryStick, Activity, Zap,
    FileText, Scale, ClipboardList, GitCompareArrows,
    ChevronRight, ArrowUpRight, ArrowDownRight, Minus,
  } from 'lucide-svelte';
  import type { ReportsOverview } from '../lib/api/dashboard';

  // Reactive alias — safe defaults to avoid undefined access
  $: rawReport = $dashboard.report as ReportsOverview | null;
  $: report = rawReport ? {
    ...rawReport,
    system_health: rawReport.system_health ?? [],
    recent_activity: rawReport.recent_activity ?? [],
    recent_stripe_events: rawReport.recent_stripe_events ?? [],
    revenue: rawReport.revenue ?? { mrr: 0, arr: 0, pending_amount: 0, pending_count: 0, churn_rate: 0, total_users: 0, plan_distribution: {}, new_this_month: 0, cancelled_30d: 0 },
    customers: rawReport.customers ?? { total: 0, active: 0, suspended: 0, active_subscriptions: 0 },
    partners: { ...rawReport.partners ?? { total: 0, active: 0, pending: 0, top: [] }, top: rawReport.partners?.top ?? [] },
    leads: { ...rawReport.leads ?? { total: 0, active: 0, won: 0, pipeline_value: 0, pipeline: {} }, pipeline: rawReport.leads?.pipeline ?? {} },
    commissions: rawReport.commissions ?? { total_partner: 0, pending: 0, paid: 0, jeturing_share: 0 },
    infrastructure: rawReport.infrastructure ?? { nodes_total: 0, nodes_online: 0, containers_total: 0, containers_running: 0, cpu: { used: 0, total: 0, percent: 0 }, ram: { used: 0, total: 0, percent: 0 }, disk: { used: 0, total: 0, percent: 0 } },
    settlements: rawReport.settlements ?? { open: 0, closed: 0, total_partner_payout: 0 },
    work_orders: rawReport.work_orders ?? { total: 0, requested: 0, in_progress: 0, completed: 0 },
    reconciliation: rawReport.reconciliation ?? { total_runs: 0, clean: 0, issues: 0 },
    invoices: rawReport.invoices ?? { total: 0, paid: 0, pending: 0, total_amount: 0, paid_amount: 0 },
  } : null;

  async function handleRefresh() {
    await dashboard.load();
  }

  onMount(async () => {
    await dashboard.load();
    dashboard.startAutoRefresh(60000);
  });
  onDestroy(() => dashboard.stopAutoRefresh());

  // Helpers
  function pct(a: number, b: number): string {
    if (!b) return '0%';
    return `${Math.round(a / b * 100)}%`;
  }
  function delta(curr: number, prev: number): { value: string; positive: boolean; neutral: boolean } {
    if (!prev || prev === 0) return { value: '+0%', positive: true, neutral: true };
    const d = ((curr - prev) / prev) * 100;
    return {
      value: `${d >= 0 ? '+' : ''}${d.toFixed(1)}%`,
      positive: d >= 0,
      neutral: Math.abs(d) < 0.5,
    };
  }

  function statusIcon(s: string) {
    if (s === 'ok') return { icon: CircleCheck, color: 'text-success' };
    if (s === 'warning') return { icon: TriangleAlert, color: 'text-warning' };
    return { icon: CircleX, color: 'text-error' };
  }

  function statusBadge(status: string) {
    if (status === 'active') return 'badge-success';
    if (status === 'provisioning' || status === 'pending') return 'badge-warning';
    if (status === 'suspended' || status === 'payment_failed') return 'badge-error';
    return 'badge-neutral';
  }

  // Plan colors for distribution
  const planColors: Record<string, string> = {
    basic: '#6B7280',
    pro: '#C05A3C',
    enterprise: '#1a1a1a',
  };
</script>

<div class="p-6 lg:p-10 space-y-6">
  <!-- Header -->
  <div class="flex items-start justify-between">
    <div>
      <h1 class="page-title">DASHBOARD</h1>
      <p class="page-subtitle">
        Bienvenido, {$auth.user?.username || 'Admin'} · {new Date().toLocaleDateString('es-ES', { day: '2-digit', month: 'long', year: 'numeric' })}
        {#if $dashboard.lastUpdated}
          <span class="text-[10px] text-gray-400 ml-2">
            Actualizado {$dashboard.lastUpdated.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
          </span>
        {/if}
      </p>
    </div>
    <button class="btn-accent btn-sm flex items-center gap-2" on:click={handleRefresh} disabled={$dashboard.isLoading}>
      <RefreshCw size={14} class={$dashboard.isLoading ? 'animate-spin' : ''} />
      Actualizar
    </button>
  </div>

  {#if $dashboard.isLoading && !report}
    <div class="flex items-center justify-center py-20">
      <div class="w-8 h-8 border-2 border-terracotta border-t-transparent rounded-full animate-spin"></div>
    </div>
  {:else if $dashboard.error}
    <div class="card flex items-center gap-3 text-error">
      <CircleAlert size={20} />
      <span class="font-body text-sm">{$dashboard.error}</span>
      <button class="btn-secondary btn-sm ml-auto" on:click={handleRefresh}>Reintentar</button>
    </div>
  {:else if report}

    <!-- ═══════════════════════════════════════
         ROW 1: KEY REVENUE METRICS (5 cards)
    ═══════════════════════════════════════ -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
      <div class="stat-card">
        <span class="stat-label flex items-center gap-1"><DollarSign size={12} /> MRR</span>
        <span class="stat-value">{formatCurrency(report.revenue.mrr)}</span>
        <span class="text-[10px] text-gray-400">ARR {formatCurrency(report.revenue.arr)}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label flex items-center gap-1"><Users size={12} /> Clientes activos</span>
        <span class="stat-value">{report.customers.active}</span>
        <span class="text-[10px] text-gray-400">{report.customers.total} total · {report.revenue.total_users} users</span>
      </div>
      <div class="stat-card">
        <span class="stat-label flex items-center gap-1"><TrendingUp size={12} /> Nuevos este mes</span>
        <span class="stat-value text-success">{report.revenue.new_this_month}</span>
        <span class="text-[10px] text-gray-400">Churn {report.revenue.churn_rate}% ({report.revenue.cancelled_30d} cancel)</span>
      </div>
      <div class="stat-card">
        <span class="stat-label flex items-center gap-1"><Zap size={12} /> Pendiente cobro</span>
        <span class="stat-value text-warning">{formatCurrency(report.revenue.pending_amount)}</span>
        <span class="text-[10px] text-gray-400">{report.revenue.pending_count} suscripciones</span>
      </div>
      <div class="stat-card">
        <span class="stat-label flex items-center gap-1"><Target size={12} /> Pipeline valor</span>
        <span class="stat-value">{formatCurrency(report.leads.pipeline_value)}</span>
        <span class="text-[10px] text-gray-400">{report.leads.active} leads activos</span>
      </div>
    </div>

    <!-- ═══════════════════════════════════════
         ROW 2: PLAN DISTRIBUTION + PARTNERS/LEADS + COMMISSIONS
    ═══════════════════════════════════════ -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Plan Distribution -->
      <div class="card p-0">
        <div class="px-6 py-4 border-b border-border-light">
          <span class="section-heading">Distribución por Plan</span>
        </div>
        <div class="p-6 space-y-4">
          {#each Object.entries(report.revenue?.plan_distribution || {}) as [plan, data]}
            <div>
              <div class="flex justify-between mb-1.5">
                <span class="text-sm font-semibold font-sans capitalize">{plan}</span>
                <span class="text-sm font-body">{data.count} subs · {formatCurrency(data.revenue)}/mo</span>
              </div>
              <div class="h-2 bg-border-light rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all"
                  style="width: {report.customers.active_subscriptions ? Math.round(data.count / report.customers.active_subscriptions * 100) : 0}%; background-color: {planColors[plan] || '#999'}"
                ></div>
              </div>
              <span class="text-[10px] text-gray-400">{data.users} usuarios</span>
            </div>
          {:else}
            <p class="text-sm text-gray-400 text-center py-4">Sin suscripciones</p>
          {/each}
        </div>
      </div>

      <!-- Partners & Leads -->
      <div class="card p-0">
        <div class="px-6 py-4 border-b border-border-light flex items-center justify-between">
          <span class="section-heading">Partners & Pipeline</span>
          <a href="/partners" class="text-[11px] uppercase tracking-widest text-gray-500 hover:text-terracotta font-sans">Ver →</a>
        </div>
        <div class="divide-y divide-border-light">
          <div class="grid grid-cols-2 gap-4 px-6 py-4">
            <div>
              <div class="text-[11px] uppercase tracking-widest text-gray-500 font-sans mb-1">Partners</div>
              <div class="text-2xl font-bold font-sans">{report.partners.active}</div>
              <div class="text-[10px] text-gray-400">{report.partners.pending} pendientes</div>
            </div>
            <div>
              <div class="text-[11px] uppercase tracking-widest text-gray-500 font-sans mb-1">Leads</div>
              <div class="text-2xl font-bold font-sans">{report.leads.total}</div>
              <div class="text-[10px] text-gray-400">{report.leads.won} ganados</div>
            </div>
          </div>
          {#if (report.partners?.top || []).length > 0}
            <div class="px-6 py-3">
              <div class="text-[10px] uppercase tracking-widest text-gray-400 font-sans mb-2">Top Partners</div>
              {#each (report.partners?.top || []).slice(0, 3) as p}
                <div class="flex justify-between items-center py-1.5">
                  <span class="text-sm font-body text-text-primary truncate">{p.company_name}</span>
                  <span class="text-sm font-semibold font-sans">{formatCurrency(p.total_revenue)}</span>
                </div>
              {/each}
            </div>
          {/if}
          <!-- Pipeline mini -->
          <div class="px-6 py-3">
            <div class="text-[10px] uppercase tracking-widest text-gray-400 font-sans mb-2">Pipeline</div>
            <div class="flex gap-1.5 flex-wrap">
              {#each Object.entries(report.leads?.pipeline || {}) as [status, count]}
                <span class="badge-neutral text-[9px]">{status}: {count}</span>
              {/each}
            </div>
          </div>
        </div>
      </div>

      <!-- Commissions & Settlements -->
      <div class="card p-0">
        <div class="px-6 py-4 border-b border-border-light flex items-center justify-between">
          <span class="section-heading">Financiero</span>
          <a href="/commissions" class="text-[11px] uppercase tracking-widest text-gray-500 hover:text-terracotta font-sans">Ver →</a>
        </div>
        <div class="divide-y divide-border-light">
          <div class="grid grid-cols-2 gap-4 px-6 py-4">
            <div>
              <div class="text-[11px] uppercase tracking-widest text-gray-500 font-sans mb-1">Comisiones Partner</div>
              <div class="text-2xl font-bold font-sans">{formatCurrency(report.commissions.total_partner)}</div>
              <div class="text-[10px] text-gray-400">{formatCurrency(report.commissions.pending)} pendiente</div>
            </div>
            <div>
              <div class="text-[11px] uppercase tracking-widest text-gray-500 font-sans mb-1">Revenue Jeturing</div>
              <div class="text-2xl font-bold font-sans">{formatCurrency(report.commissions.jeturing_share)}</div>
              <div class="text-[10px] text-gray-400">{formatCurrency(report.commissions.paid)} pagado</div>
            </div>
          </div>
          <div class="grid grid-cols-3 gap-2 px-6 py-3 text-center">
            <div>
              <div class="text-[10px] uppercase tracking-widest text-gray-400 font-sans">Settlements</div>
              <div class="font-bold text-lg font-sans">{report.settlements.open + report.settlements.closed}</div>
              <div class="text-[10px] text-gray-400">{report.settlements.open} abiertos</div>
            </div>
            <div>
              <div class="text-[10px] uppercase tracking-widest text-gray-400 font-sans">Facturas</div>
              <div class="font-bold text-lg font-sans">{report.invoices.total}</div>
              <div class="text-[10px] text-gray-400">{report.invoices.pending} pendientes</div>
            </div>
            <div>
              <div class="text-[10px] uppercase tracking-widest text-gray-400 font-sans">Payout Total</div>
              <div class="font-bold text-lg font-sans">{formatCurrency(report.settlements.total_partner_payout)}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════
         ROW 3: OPERATIONS (Infra + Work Orders + Reconciliation)
    ═══════════════════════════════════════ -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Infrastructure -->
      <div class="card p-0">
        <div class="px-6 py-4 border-b border-border-light flex items-center justify-between">
          <span class="section-heading flex items-center gap-2"><Server size={16} /> Infraestructura</span>
          <a href="/infrastructure" class="text-[11px] uppercase tracking-widest text-gray-500 hover:text-terracotta font-sans">Ver →</a>
        </div>
        <div class="p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4 text-center">
            <div>
              <div class="text-2xl font-bold font-sans">{report.infrastructure.nodes_online}/{report.infrastructure.nodes_total}</div>
              <div class="text-[10px] uppercase tracking-widest text-gray-500">Nodos online</div>
            </div>
            <div>
              <div class="text-2xl font-bold font-sans">{report.infrastructure.containers_running}/{report.infrastructure.containers_total}</div>
              <div class="text-[10px] uppercase tracking-widest text-gray-500">Containers</div>
            </div>
          </div>
          <!-- CPU -->
          <div>
            <div class="flex justify-between mb-1">
              <span class="text-[11px] uppercase tracking-widest text-gray-500 font-sans flex items-center gap-1"><Cpu size={12} /> CPU</span>
              <span class="text-[11px] font-semibold text-text-primary font-sans">{report.infrastructure.cpu.percent}%</span>
            </div>
            <div class="h-1.5 bg-border-light rounded-full overflow-hidden">
              <div class="h-full bg-charcoal rounded-full transition-all" style="width:{Math.min(100, report.infrastructure.cpu.percent)}%"></div>
            </div>
          </div>
          <!-- RAM -->
          <div>
            <div class="flex justify-between mb-1">
              <span class="text-[11px] uppercase tracking-widest text-gray-500 font-sans flex items-center gap-1"><MemoryStick size={12} /> RAM</span>
              <span class="text-[11px] font-semibold text-text-primary font-sans">{report.infrastructure.ram.percent}%</span>
            </div>
            <div class="h-1.5 bg-border-light rounded-full overflow-hidden">
              <div class="h-full bg-terracotta rounded-full transition-all" style="width:{Math.min(100, report.infrastructure.ram.percent)}%"></div>
            </div>
          </div>
          <!-- Disk -->
          <div>
            <div class="flex justify-between mb-1">
              <span class="text-[11px] uppercase tracking-widest text-gray-500 font-sans flex items-center gap-1"><HardDrive size={12} /> Disco</span>
              <span class="text-[11px] font-semibold text-text-primary font-sans">{report.infrastructure.disk.percent}%</span>
            </div>
            <div class="h-1.5 bg-border-light rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all {report.infrastructure.disk.percent > 85 ? 'bg-error' : 'bg-charcoal'}" style="width:{Math.min(100, report.infrastructure.disk.percent)}%"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Work Orders & Reconciliation -->
      <div class="card p-0">
        <div class="px-6 py-4 border-b border-border-light flex items-center justify-between">
          <span class="section-heading flex items-center gap-2"><ClipboardList size={16} /> Operaciones</span>
          <a href="/workorders" class="text-[11px] uppercase tracking-widest text-gray-500 hover:text-terracotta font-sans">Ver →</a>
        </div>
        <div class="divide-y divide-border-light">
          <div class="grid grid-cols-4 gap-2 px-6 py-4 text-center">
            <div>
              <div class="font-bold text-lg font-sans">{report.work_orders.total}</div>
              <div class="text-[9px] uppercase tracking-widest text-gray-500">Total</div>
            </div>
            <div>
              <div class="font-bold text-lg font-sans text-warning">{report.work_orders.requested}</div>
              <div class="text-[9px] uppercase tracking-widest text-gray-500">Pedidas</div>
            </div>
            <div>
              <div class="font-bold text-lg font-sans text-info">{report.work_orders.in_progress}</div>
              <div class="text-[9px] uppercase tracking-widest text-gray-500">En curso</div>
            </div>
            <div>
              <div class="font-bold text-lg font-sans text-success">{report.work_orders.completed}</div>
              <div class="text-[9px] uppercase tracking-widest text-gray-500">Listas</div>
            </div>
          </div>
          <div class="px-6 py-4">
            <div class="flex items-center gap-2 mb-3">
              <GitCompareArrows size={16} />
              <span class="text-sm font-semibold font-sans">Conciliación Stripe ↔ DB</span>
            </div>
            <div class="grid grid-cols-3 gap-2 text-center">
              <div>
                <div class="font-bold text-lg font-sans">{report.reconciliation.total_runs}</div>
                <div class="text-[9px] uppercase tracking-widest text-gray-500">Corridas</div>
              </div>
              <div>
                <div class="font-bold text-lg font-sans text-success">{report.reconciliation.clean}</div>
                <div class="text-[9px] uppercase tracking-widest text-gray-500">OK</div>
              </div>
              <div>
                <div class="font-bold text-lg font-sans text-error">{report.reconciliation.issues}</div>
                <div class="text-[9px] uppercase tracking-widest text-gray-500">Issues</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- System Health -->
      <div class="card p-0">
        <div class="px-6 py-4 border-b border-border-light flex items-center justify-between">
          <span class="section-heading flex items-center gap-2"><Activity size={16} /> Estado del Sistema</span>
          <a href="/logs" class="text-[11px] uppercase tracking-widest text-gray-500 hover:text-terracotta font-sans">Logs →</a>
        </div>
        <div class="divide-y divide-border-light">
          {#each (report.system_health || []) as item}
            {@const si = statusIcon(item.status)}
            <div class="flex items-center justify-between px-6 py-3">
              <span class="text-sm font-body text-text-secondary">{item.name}</span>
              <div class="flex items-center gap-2">
                {#if true}{@const C = si.icon as any}<C size={14} class={si.color} />{/if}
                <span class="text-[11px] font-semibold uppercase tracking-widest {si.color} font-sans">{item.detail}</span>
              </div>
            </div>
          {/each}
        </div>

        <!-- Stripe Events -->
        {#if (report.recent_stripe_events || []).length > 0}
          <div class="px-6 py-3 border-t border-border-light">
            <div class="text-[10px] uppercase tracking-widest text-gray-400 font-sans mb-2">Últimos eventos Stripe</div>
            {#each (report.recent_stripe_events || []).slice(0, 4) as evt}
              <div class="flex justify-between py-1">
                <span class="text-[11px] font-mono text-gray-500 truncate">{evt.event_type}</span>
                <span class="text-[10px] text-gray-400">{evt.processed ? '✓' : '⏳'}</span>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>

    <!-- ═══════════════════════════════════════
         ROW 4: RECENT ACTIVITY TABLE
    ═══════════════════════════════════════ -->
    <div class="card p-0">
      <div class="flex items-center justify-between px-6 py-4 border-b border-border-light">
        <span class="section-heading">Actividad Reciente — Últimos Clientes</span>
        <a href="/tenants" class="text-[11px] uppercase tracking-widest text-gray-500 hover:text-terracotta font-sans">
          Ver todos →
        </a>
      </div>
      <div class="overflow-x-auto">
        <table class="table w-full">
          <thead>
            <tr>
              <th>Empresa</th>
              <th>Subdominio</th>
              <th>Plan</th>
              <th class="text-right">Users</th>
              <th class="text-right">MRR</th>
              <th>Estado</th>
              <th>Fecha</th>
            </tr>
          </thead>
          <tbody>
            {#each (report.recent_activity || []) as t}
              <tr>
                <td>
                  <div class="flex items-center gap-2">
                    <div class="w-7 h-7 bg-charcoal flex items-center justify-center flex-shrink-0">
                      <span class="text-text-light font-sans font-bold text-[10px]">{(t.company_name || t.subdomain).charAt(0).toUpperCase()}</span>
                    </div>
                    <div>
                      <div class="text-sm font-semibold font-sans text-text-primary">{t.company_name || '—'}</div>
                      <div class="text-[10px] text-gray-400">{t.email}</div>
                    </div>
                  </div>
                </td>
                <td class="text-[11px] font-mono text-gray-500">{t.subdomain}</td>
                <td><span class="badge-{t.plan === 'enterprise' ? 'enterprise' : t.plan === 'pro' ? 'pro' : 'basic'} text-[9px]">{t.plan}</span></td>
                <td class="text-right font-sans font-semibold">{t.user_count}</td>
                <td class="text-right font-sans font-semibold">{formatCurrency(t.monthly_amount)}</td>
                <td><span class={statusBadge(t.status)}>{t.status}</span></td>
                <td class="text-xs text-gray-400">{formatDate(t.created_at)}</td>
              </tr>
            {:else}
              <tr><td colspan="7" class="text-center text-gray-400 py-8">Sin actividad reciente</td></tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

    <!-- ═══════════════════════════════════════
         ROW 5: QUICK NAV
    ═══════════════════════════════════════ -->
    <div class="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-8 gap-2">
      {#each [
        { href: '/tenants',         label: 'Tenants' },
        { href: '/billing',         label: 'Billing' },
        { href: '/partners',        label: 'Partners' },
        { href: '/leads',           label: 'Leads' },
        { href: '/invoices',        label: 'Facturas' },
        { href: '/settlements',     label: 'Settlements' },
        { href: '/blueprints',      label: 'Blueprints' },
        { href: '/audit',           label: 'Auditoría' },
      ] as link}
        <a href={link.href} class="card p-3 text-center hover:border-terracotta transition-colors">
          <span class="text-[10px] font-semibold uppercase tracking-widest text-text-secondary font-sans">{link.label}</span>
        </a>
      {/each}
    </div>
  {/if}
</div>
