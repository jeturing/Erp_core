<script lang="ts">
  import { onMount } from 'svelte';
  import {
    LogOut, LayoutDashboard, Users, Briefcase, DollarSign, CreditCard,
    UserCircle, Plus, TrendingUp, Building2, ExternalLink, RefreshCw,
    ChevronRight, ArrowUpRight, Loader2
  } from 'lucide-svelte';
  import { auth, currentUser } from '../lib/stores';
  import { Spinner } from '../lib/components';
  import PartnerOnboarding from '../lib/components/PartnerOnboarding.svelte';
  import partnerPortalApi from '../lib/api/partnerPortal';
  import type {
    PartnerOnboardingStatus, PartnerDashboard, PartnerLeadsResponse,
    PartnerLeadItem, PartnerProfile, PartnerClientItem, PartnerCommissionItem,
  } from '../lib/types';
  import { formatDate } from '../lib/utils/formatters';

  // State
  let loading = true;
  let error = '';
  let activeTab: 'dashboard' | 'leads' | 'clients' | 'commissions' | 'stripe' | 'profile' = 'dashboard';

  // Data
  let onboardingStatus: PartnerOnboardingStatus | null = null;
  let dashboard: PartnerDashboard | null = null;
  let leads: PartnerLeadsResponse | null = null;
  let clients: { items: PartnerClientItem[]; total: number } | null = null;
  let commissions: { items: PartnerCommissionItem[]; total: number; summary: { total_earned: number; pending: number; paid: number } } | null = null;
  let profile: PartnerProfile | null = null;

  // New Lead form
  let showNewLead = false;
  let newLead = { company_name: '', contact_name: '', contact_email: '', phone: '', country: '', notes: '', estimated_monthly_value: 0 };
  let savingLead = false;

  $: showOnboarding = onboardingStatus && onboardingStatus.current_step < 4;

  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }).format(amount || 0);
  }

  function statusColor(status: string | null): string {
    switch (status) {
      case 'new': return 'bg-blue-100 text-blue-700';
      case 'contacted': return 'bg-indigo-100 text-indigo-700';
      case 'qualified': case 'in_qualification': return 'bg-amber-100 text-amber-700';
      case 'proposal': return 'bg-purple-100 text-purple-700';
      case 'won': return 'bg-green-100 text-green-700';
      case 'lost': return 'bg-red-100 text-red-700';
      case 'active': return 'bg-green-100 text-green-700';
      case 'pending': return 'bg-amber-100 text-amber-700';
      case 'paid': return 'bg-green-100 text-green-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  }

  async function loadData() {
    loading = true;
    error = '';
    try {
      onboardingStatus = await partnerPortalApi.getOnboardingStatus();
      if (onboardingStatus.current_step >= 4) {
        await loadTabData();
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error al cargar el portal';
    } finally {
      loading = false;
    }
  }

  async function loadTabData() {
    try {
      switch (activeTab) {
        case 'dashboard':
          dashboard = await partnerPortalApi.getDashboard();
          break;
        case 'leads':
          leads = await partnerPortalApi.getLeads();
          break;
        case 'clients':
          clients = await partnerPortalApi.getClients();
          break;
        case 'commissions':
          commissions = await partnerPortalApi.getCommissions();
          break;
        case 'profile':
          profile = await partnerPortalApi.getProfile();
          break;
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error';
    }
  }

  async function switchTab(tab: typeof activeTab) {
    activeTab = tab;
    error = '';
    await loadTabData();
  }

  async function createLead() {
    if (!newLead.company_name.trim()) return;
    savingLead = true;
    try {
      await partnerPortalApi.createLead(newLead);
      newLead = { company_name: '', contact_name: '', contact_email: '', phone: '', country: '', notes: '', estimated_monthly_value: 0 };
      showNewLead = false;
      leads = await partnerPortalApi.getLeads();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error al crear lead';
    } finally {
      savingLead = false;
    }
  }

  async function openStripeDashboard() {
    try {
      const result = await partnerPortalApi.getStripeDashboardLink();
      if (result.url) window.open(result.url, '_blank');
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error al abrir Stripe';
    }
  }

  function handleLogout() {
    auth.logout();
    window.location.hash = '#/login';
  }

  function handleOnboardingComplete() {
    showOnboarding = false;
    loadData();
  }

  onMount(loadData);
</script>

{#if loading}
  <div class="min-h-screen bg-[#F5F3EF] flex items-center justify-center">
    <div class="text-center">
      <Spinner size="lg" />
      <p class="mt-4 text-gray-500">Cargando portal...</p>
    </div>
  </div>
{:else if showOnboarding && onboardingStatus}
  <PartnerOnboarding
    {onboardingStatus}
    {profile}
    on:complete={handleOnboardingComplete}
  />
{:else}
  <div class="min-h-screen bg-[#F5F3EF]">
    <!-- Top Navbar -->
    <header class="bg-[#1a1a1a] border-b border-[#2a2a2a] sticky top-0 z-20">
      <div class="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded bg-[#C05A3C] flex items-center justify-center">
            <span class="text-white font-bold text-sm">S</span>
          </div>
          <span class="text-white font-semibold tracking-[0.05em] text-sm">SAJET</span>
          <span class="text-gray-500 text-xs">PARTNER PORTAL</span>
        </div>

        <div class="flex items-center gap-2">
          <Building2 class="w-4 h-4 text-gray-400" />
          <span class="text-gray-300 text-sm font-medium">
            {dashboard?.partner?.company_name || $currentUser?.company_name || 'Partner'}
          </span>
        </div>

        <button
          class="flex items-center gap-1.5 text-[11px] font-semibold tracking-[0.08em] text-gray-400 hover:text-white uppercase transition-colors"
          on:click={handleLogout}
        >
          <LogOut class="w-3.5 h-3.5" />
          CERRAR SESIÓN
        </button>
      </div>
    </header>

    <!-- Tab Navigation -->
    <nav class="bg-white border-b border-gray-200 sticky top-[52px] z-10">
      <div class="max-w-7xl mx-auto px-6 flex gap-0">
        {#each [
          { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
          { key: 'leads', label: 'Leads', icon: Briefcase },
          { key: 'clients', label: 'Clientes', icon: Users },
          { key: 'commissions', label: 'Comisiones', icon: DollarSign },
          { key: 'stripe', label: 'Stripe', icon: CreditCard },
          { key: 'profile', label: 'Mi Perfil', icon: UserCircle },
        ] as tab}
          <button
            class="flex items-center gap-1.5 px-4 py-3 text-sm font-medium transition-colors border-b-2
              {activeTab === tab.key
                ? 'text-[#C05A3C] border-[#C05A3C]'
                : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'}"
            on:click={() => switchTab(tab.key)}
          >
            <svelte:component this={tab.icon} class="w-4 h-4" />
            {tab.label}
          </button>
        {/each}
      </div>
    </nav>

    <main class="max-w-7xl mx-auto px-6 py-6">
      {#if error}
        <div class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 mb-4">{error}</div>
      {/if}

      <!-- ═══ DASHBOARD ═══ -->
      {#if activeTab === 'dashboard' && dashboard}
        <!-- KPI Cards -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Leads Activos</span>
            <p class="text-2xl font-bold text-[#1a1a1a] mt-1">{dashboard.kpis.active_leads}</p>
            <p class="text-xs text-gray-400 mt-0.5">{dashboard.kpis.total_leads} totales</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Conversión</span>
            <p class="text-2xl font-bold text-[#4A7C59] mt-1">{dashboard.kpis.conversion_rate}%</p>
            <p class="text-xs text-gray-400 mt-0.5">{dashboard.kpis.won_leads} ganados</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Clientes Activos</span>
            <p class="text-2xl font-bold text-[#1a1a1a] mt-1">{dashboard.kpis.active_clients}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Pipeline Estimado</span>
            <p class="text-2xl font-bold text-[#C05A3C] mt-1">{formatCurrency(dashboard.kpis.estimated_pipeline)}</p>
            <p class="text-xs text-gray-400 mt-0.5">/mes potencial</p>
          </div>
        </div>

        <!-- Revenue Cards -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <div class="flex items-center justify-between mb-3">
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Total Ganado</span>
              <TrendingUp class="w-4 h-4 text-[#4A7C59]" />
            </div>
            <p class="text-3xl font-bold text-[#1a1a1a]">{formatCurrency(dashboard.kpis.total_earned)}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Comisiones Pendientes</span>
            <p class="text-3xl font-bold text-amber-600 mt-2">{formatCurrency(dashboard.kpis.pending_commissions)}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Comisiones Pagadas</span>
            <p class="text-3xl font-bold text-[#4A7C59] mt-2">{formatCurrency(dashboard.kpis.paid_commissions)}</p>
          </div>
        </div>

        <!-- Stripe Balance + Quick Actions -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {#if dashboard.stripe_balance}
            <div class="bg-white rounded-xl border border-gray-200 p-5">
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3 block">Balance Stripe</span>
              <div class="flex gap-8">
                <div>
                  <span class="text-xs text-gray-400">Disponible</span>
                  <p class="text-xl font-bold text-[#4A7C59]">{formatCurrency(dashboard.stripe_balance.available)}</p>
                </div>
                <div>
                  <span class="text-xs text-gray-400">Pendiente</span>
                  <p class="text-xl font-bold text-amber-600">{formatCurrency(dashboard.stripe_balance.pending)}</p>
                </div>
              </div>
              <button
                class="mt-4 text-sm text-[#635BFF] hover:underline flex items-center gap-1"
                on:click={openStripeDashboard}
              >
                <ExternalLink class="w-3 h-3" /> Abrir Dashboard Stripe
              </button>
            </div>
          {/if}

          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3 block">Acciones Rápidas</span>
            <div class="space-y-2">
              <button
                class="w-full text-left px-3 py-2.5 rounded-lg border border-gray-200 hover:border-[#C05A3C] transition-colors flex items-center justify-between text-sm"
                on:click={() => { switchTab('leads'); showNewLead = true; }}
              >
                <span class="flex items-center gap-2"><Plus class="w-4 h-4 text-[#C05A3C]" /> Registrar nuevo lead</span>
                <ChevronRight class="w-4 h-4 text-gray-400" />
              </button>
              <button
                class="w-full text-left px-3 py-2.5 rounded-lg border border-gray-200 hover:border-[#C05A3C] transition-colors flex items-center justify-between text-sm"
                on:click={() => switchTab('commissions')}
              >
                <span class="flex items-center gap-2"><DollarSign class="w-4 h-4 text-[#C05A3C]" /> Ver mis comisiones</span>
                <ChevronRight class="w-4 h-4 text-gray-400" />
              </button>
            </div>
          </div>
        </div>

      <!-- ═══ LEADS ═══ -->
      {:else if activeTab === 'leads'}
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-[#1a1a1a]">Mis Leads</h2>
          <button
            class="bg-[#C05A3C] text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-[#a94e33] transition-colors flex items-center gap-1.5"
            on:click={() => showNewLead = !showNewLead}
          >
            <Plus class="w-4 h-4" /> Nuevo Lead
          </button>
        </div>

        <!-- New Lead Form -->
        {#if showNewLead}
          <div class="bg-white rounded-xl border border-gray-200 p-5 mb-4">
            <h3 class="text-sm font-bold text-[#1a1a1a] mb-3">Registrar Lead</h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <input type="text" bind:value={newLead.company_name} placeholder="Empresa *"
                class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
              <input type="text" bind:value={newLead.contact_name} placeholder="Contacto"
                class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
              <input type="email" bind:value={newLead.contact_email} placeholder="Email"
                class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
              <input type="text" bind:value={newLead.phone} placeholder="Teléfono"
                class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
              <input type="text" bind:value={newLead.country} placeholder="País"
                class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
              <input type="number" bind:value={newLead.estimated_monthly_value} placeholder="Valor mensual estimado"
                class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
              <textarea bind:value={newLead.notes} placeholder="Notas" rows="2"
                class="sm:col-span-2 lg:col-span-3 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none resize-none"></textarea>
            </div>
            <div class="flex gap-2 mt-3 justify-end">
              <button class="text-sm text-gray-500 px-4 py-2 hover:text-gray-700" on:click={() => showNewLead = false}>Cancelar</button>
              <button
                class="bg-[#4A7C59] text-white text-sm font-semibold px-5 py-2 rounded-lg hover:bg-[#3d6a4b] transition-colors flex items-center gap-1.5"
                on:click={createLead} disabled={savingLead}
              >
                {#if savingLead}<Loader2 class="w-4 h-4 animate-spin" />{/if}
                Guardar Lead
              </button>
            </div>
          </div>
        {/if}

        <!-- Pipeline Summary -->
        {#if leads?.pipeline}
          <div class="flex flex-wrap gap-2 mb-4">
            {#each Object.entries(leads.pipeline) as [status, count]}
              {#if count > 0}
                <span class="px-2.5 py-1 rounded-full text-xs font-semibold {statusColor(status)}">
                  {status}: {count}
                </span>
              {/if}
            {/each}
          </div>
        {/if}

        <!-- Leads Table -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {#if leads?.items && leads.items.length > 0}
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gray-200 bg-gray-50">
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Empresa</th>
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Contacto</th>
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Estado</th>
                    <th class="text-right px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Valor/Mes</th>
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Fecha</th>
                  </tr>
                </thead>
                <tbody>
                  {#each leads.items as lead}
                    <tr class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td class="px-4 py-3">
                        <span class="text-sm font-medium text-[#1a1a1a]">{lead.company_name}</span>
                        {#if lead.contact_email}
                          <br><span class="text-xs text-gray-400">{lead.contact_email}</span>
                        {/if}
                      </td>
                      <td class="px-4 py-3 text-sm text-gray-600">{lead.contact_name || '—'}</td>
                      <td class="px-4 py-3">
                        <span class="px-2 py-0.5 rounded-full text-xs font-semibold {statusColor(lead.status)}">
                          {lead.status || 'new'}
                        </span>
                      </td>
                      <td class="px-4 py-3 text-right text-sm font-medium text-[#1a1a1a]">
                        {formatCurrency(lead.estimated_monthly_value)}
                      </td>
                      <td class="px-4 py-3 text-xs text-gray-400">
                        {lead.registered_at ? formatDate(lead.registered_at) : '—'}
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {:else}
            <div class="py-12 text-center">
              <Briefcase class="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p class="text-sm text-gray-500">No tienes leads registrados. ¡Crea tu primer lead!</p>
            </div>
          {/if}
        </div>

      <!-- ═══ CLIENTS ═══ -->
      {:else if activeTab === 'clients'}
        <h2 class="text-lg font-bold text-[#1a1a1a] mb-4">Mis Clientes</h2>
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {#if clients?.items && clients.items.length > 0}
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gray-200 bg-gray-50">
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Empresa</th>
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Plan</th>
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Estado</th>
                    <th class="text-right px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Monto/Mes</th>
                    <th class="text-right px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Usuarios</th>
                  </tr>
                </thead>
                <tbody>
                  {#each clients.items as client}
                    <tr class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td class="px-4 py-3">
                        <span class="text-sm font-medium text-[#1a1a1a]">{client.company_name}</span>
                        <br><span class="text-xs text-gray-400">{client.email}</span>
                      </td>
                      <td class="px-4 py-3 text-sm text-gray-600 capitalize">{client.plan || '—'}</td>
                      <td class="px-4 py-3">
                        <span class="px-2 py-0.5 rounded-full text-xs font-semibold {statusColor(client.status)}">
                          {client.status || '—'}
                        </span>
                      </td>
                      <td class="px-4 py-3 text-right text-sm font-medium">{formatCurrency(client.monthly_amount)}</td>
                      <td class="px-4 py-3 text-right text-sm text-gray-600">{client.user_count}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {:else}
            <div class="py-12 text-center">
              <Users class="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p class="text-sm text-gray-500">Aún no tienes clientes activos</p>
            </div>
          {/if}
        </div>

      <!-- ═══ COMMISSIONS ═══ -->
      {:else if activeTab === 'commissions'}
        <h2 class="text-lg font-bold text-[#1a1a1a] mb-4">Mis Comisiones</h2>

        {#if commissions?.summary}
          <div class="grid grid-cols-3 gap-4 mb-4">
            <div class="bg-white rounded-xl border border-gray-200 p-4 text-center">
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Total Ganado</span>
              <p class="text-xl font-bold text-[#1a1a1a] mt-1">{formatCurrency(commissions.summary.total_earned)}</p>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 p-4 text-center">
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Pendiente</span>
              <p class="text-xl font-bold text-amber-600 mt-1">{formatCurrency(commissions.summary.pending)}</p>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 p-4 text-center">
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Pagado</span>
              <p class="text-xl font-bold text-[#4A7C59] mt-1">{formatCurrency(commissions.summary.paid)}</p>
            </div>
          </div>
        {/if}

        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {#if commissions?.items && commissions.items.length > 0}
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gray-200 bg-gray-50">
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Período</th>
                    <th class="text-right px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Bruto</th>
                    <th class="text-right px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Mi Comisión</th>
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Estado</th>
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Pagado</th>
                  </tr>
                </thead>
                <tbody>
                  {#each commissions.items as c}
                    <tr class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td class="px-4 py-3 text-sm text-gray-600">
                        {c.period_start ? formatDate(c.period_start) : '—'} — {c.period_end ? formatDate(c.period_end) : '—'}
                      </td>
                      <td class="px-4 py-3 text-right text-sm">{formatCurrency(c.gross_revenue)}</td>
                      <td class="px-4 py-3 text-right text-sm font-bold text-[#C05A3C]">{formatCurrency(c.partner_amount)}</td>
                      <td class="px-4 py-3">
                        <span class="px-2 py-0.5 rounded-full text-xs font-semibold {statusColor(c.status)}">
                          {c.status || '—'}
                        </span>
                      </td>
                      <td class="px-4 py-3 text-xs text-gray-400">{c.paid_at ? formatDate(c.paid_at) : '—'}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {:else}
            <div class="py-12 text-center">
              <DollarSign class="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p class="text-sm text-gray-500">No hay comisiones registradas</p>
            </div>
          {/if}
        </div>

      <!-- ═══ STRIPE ═══ -->
      {:else if activeTab === 'stripe'}
        <h2 class="text-lg font-bold text-[#1a1a1a] mb-4">Stripe Connect</h2>
        <div class="bg-white rounded-xl border border-gray-200 p-6">
          {#if dashboard?.partner?.stripe_charges_enabled}
            <div class="flex items-center gap-3 mb-4">
              <div class="w-10 h-10 rounded-full bg-[#4A7C59] flex items-center justify-center">
                <CreditCard class="w-5 h-5 text-white" />
              </div>
              <div>
                <p class="text-sm font-bold text-[#1a1a1a]">Cuenta Stripe Activa</p>
                <p class="text-xs text-gray-500">Tus pagos y split de comisiones están funcionando</p>
              </div>
            </div>
            <button
              class="bg-[#635BFF] text-white text-sm font-semibold px-5 py-2.5 rounded-lg hover:bg-[#5851e0] transition-colors flex items-center gap-2"
              on:click={openStripeDashboard}
            >
              <ExternalLink class="w-4 h-4" /> Abrir Dashboard de Stripe
            </button>
          {:else}
            <div class="text-center py-6">
              <CreditCard class="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p class="text-sm text-gray-500 mb-4">No tienes una cuenta Stripe Connect activa</p>
              <button
                class="bg-[#635BFF] text-white text-sm font-semibold px-5 py-2.5 rounded-lg hover:bg-[#5851e0] transition-colors"
                on:click={async () => { try { const r = await partnerPortalApi.startStripe(); if (r.onboarding_url) window.open(r.onboarding_url, '_blank'); } catch (e) { error = e instanceof Error ? e.message : 'Error'; } }}
              >
                Conectar con Stripe
              </button>
            </div>
          {/if}
        </div>

      <!-- ═══ PROFILE ═══ -->
      {:else if activeTab === 'profile' && profile}
        <h2 class="text-lg font-bold text-[#1a1a1a] mb-4">Mi Perfil</h2>
        <div class="bg-white rounded-xl border border-gray-200 p-6">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Empresa</span>
              <p class="text-sm font-medium text-[#1a1a1a]">{profile.company_name}</p>
            </div>
            <div>
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Razón Social</span>
              <p class="text-sm text-gray-600">{profile.legal_name || '—'}</p>
            </div>
            <div>
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Email de Portal</span>
              <p class="text-sm text-gray-600">{profile.portal_email || profile.contact_email}</p>
            </div>
            <div>
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Contacto</span>
              <p class="text-sm text-gray-600">{profile.contact_name || '—'}</p>
            </div>
            <div>
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Teléfono</span>
              <p class="text-sm text-gray-600">{profile.phone || '—'}</p>
            </div>
            <div>
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">País</span>
              <p class="text-sm text-gray-600">{profile.country || '—'}</p>
            </div>
            <div>
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Tasa de Comisión</span>
              <p class="text-sm font-bold text-[#C05A3C]">{(profile.commission_rate * 100).toFixed(0)}%</p>
            </div>
            <div>
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Estado</span>
              <span class="px-2 py-0.5 rounded-full text-xs font-semibold {statusColor(profile.status)}">
                {profile.status}
              </span>
            </div>
            <div>
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Stripe Connect</span>
              <p class="text-sm">{profile.stripe_charges_enabled ? '✅ Activo' : '❌ No configurado'}</p>
            </div>
            <div>
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Contrato</span>
              <p class="text-sm text-gray-600">{profile.contract_reference || '—'}</p>
            </div>
          </div>
        </div>
      {/if}
    </main>
  </div>
{/if}
