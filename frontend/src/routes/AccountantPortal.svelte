<script lang="ts">
  import { onMount } from 'svelte';
  import Layout from '../lib/components/Layout.svelte';
  import { Spinner } from '../lib/components';
  import {
    Building2, ArrowRightLeft, BarChart3, UserPlus,
    Users, DollarSign, FileText, TrendingUp
  } from 'lucide-svelte';

  let tenants: any[] = [];
  let dashboard: any = null;
  let loading = true;
  let switching = false;
  let error = '';

  async function fetchData() {
    try {
      const [tenantsRes, dashRes] = await Promise.all([
        fetch('/api/accountant/tenants', { credentials: 'include' }),
        fetch('/api/accountant/dashboard', { credentials: 'include' }),
      ]);
      if (tenantsRes.ok) tenants = await tenantsRes.json();
      if (dashRes.ok) dashboard = await dashRes.json();
    } catch (e) {
      error = 'Failed to load accountant data';
    } finally {
      loading = false;
    }
  }

  async function switchTenant(tenantId: number) {
    switching = true;
    try {
      const res = await fetch('/api/accountant/switch-tenant', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tenant_id: tenantId }),
      });
      if (res.ok) {
        // New JWT emitted — redirect to tenant portal
        window.location.hash = '#/portal';
        window.location.reload();
      } else {
        error = 'Access denied for this tenant';
      }
    } catch (e) {
      error = 'Switch failed';
    } finally {
      switching = false;
    }
  }

  onMount(fetchData);
</script>

<Layout currentRoute="accountant-portal">
  <div class="p-6 max-w-6xl mx-auto">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-jakarta font-bold text-slate-dark">Accountant Dashboard</h1>
        <p class="text-sm font-inter text-slate mt-1">Manage all your client companies from one place.</p>
      </div>
      <button
        class="inline-flex items-center gap-2 bg-primary hover:bg-navy text-white font-jakarta font-semibold text-sm px-4 py-2 rounded-btn shadow-soft transition-all"
        on:click={() => window.location.hash = '#/accountant-invite'}
      >
        <UserPlus class="w-4 h-4" />
        Invite Client
      </button>
    </div>

    {#if loading}
      <div class="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    {:else}
      {#if error}
        <div class="rounded-card-sm border border-red-200 bg-red-50 p-4 mb-6">
          <p class="text-sm font-inter text-red-700">{error}</p>
        </div>
      {/if}

      <!-- KPIs -->
      {#if dashboard}
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div class="rounded-card-sm border border-border bg-white p-4">
            <div class="flex items-center gap-2 mb-2">
              <Users class="w-4 h-4 text-primary" />
              <span class="text-xs font-inter text-slate">Total Clients</span>
            </div>
            <p class="text-2xl font-jakarta font-bold text-slate-dark">{dashboard.total_clients}</p>
          </div>
          <div class="rounded-card-sm border border-border bg-white p-4">
            <div class="flex items-center gap-2 mb-2">
              <DollarSign class="w-4 h-4 text-emerald-500" />
              <span class="text-xs font-inter text-slate">Total MRR</span>
            </div>
            <p class="text-2xl font-jakarta font-bold text-slate-dark">${dashboard.total_mrr?.toLocaleString() || '0'}</p>
          </div>
          <div class="rounded-card-sm border border-border bg-white p-4">
            <div class="flex items-center gap-2 mb-2">
              <FileText class="w-4 h-4 text-amber-500" />
              <span class="text-xs font-inter text-slate">Total Users</span>
            </div>
            <p class="text-2xl font-jakarta font-bold text-slate-dark">{dashboard.total_users}</p>
          </div>
          <div class="rounded-card-sm border border-border bg-white p-4">
            <div class="flex items-center gap-2 mb-2">
              <TrendingUp class="w-4 h-4 text-primary" />
              <span class="text-xs font-inter text-slate">Active Subs</span>
            </div>
            <p class="text-2xl font-jakarta font-bold text-slate-dark">{dashboard.active_subscriptions}</p>
          </div>
        </div>
      {/if}

      <!-- Client list -->
      <div class="rounded-card-lg border border-border bg-white overflow-hidden">
        <div class="px-5 py-4 border-b border-border">
          <h2 class="text-base font-jakarta font-semibold text-slate-dark">Your Clients</h2>
        </div>
        {#if tenants.length === 0}
          <div class="p-8 text-center">
            <Building2 class="w-10 h-10 text-slate mx-auto mb-3" strokeWidth={1.5} />
            <p class="text-sm font-inter text-slate">No clients assigned yet. Invite your first client to get started.</p>
          </div>
        {:else}
          <div class="divide-y divide-border">
            {#each tenants as tenant}
              <div class="flex items-center justify-between px-5 py-4 hover:bg-cloud/50 transition-colors">
                <div class="flex items-center gap-4">
                  <div class="w-10 h-10 rounded-lg bg-primary-light flex items-center justify-center">
                    <Building2 class="w-5 h-5 text-primary" strokeWidth={1.5} />
                  </div>
                  <div>
                    <p class="text-sm font-jakarta font-semibold text-slate-dark">{tenant.company_name}</p>
                    <p class="text-xs font-inter text-slate">
                      {tenant.plan_name || 'No plan'} · {tenant.user_count || 1} user{tenant.user_count !== 1 ? 's' : ''} · {tenant.access_level}
                    </p>
                  </div>
                </div>
                <button
                  class="inline-flex items-center gap-1.5 text-sm font-inter font-medium text-primary hover:text-navy transition-colors disabled:opacity-50"
                  on:click={() => switchTenant(tenant.tenant_id)}
                  disabled={switching}
                >
                  <ArrowRightLeft class="w-4 h-4" />
                  Switch
                </button>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/if}
  </div>
</Layout>
