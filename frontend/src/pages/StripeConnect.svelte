<script lang="ts">
  import { onMount } from 'svelte';
  import { stripeConnectApi } from '../lib/api';
  import type { ConnectStatus, ConnectBalance } from '../lib/api/stripeConnect';
  import { toasts } from '../lib/stores';
  import {
    CreditCard, RefreshCw, ExternalLink, CheckCircle, XCircle,
    AlertTriangle, DollarSign, ArrowUpRight, Link, ChevronDown,
    Loader, Shield, Users,
  } from 'lucide-svelte';

  // We load partners from the partners API to list Connect accounts
  import { partnersApi } from '../lib/api';

  interface PartnerConnect {
    id: number;
    company_name: string;
    contact_email: string;
    stripe_account_id: string | null;
    status: ConnectStatus | null;
    balance: ConnectBalance | null;
    loading: boolean;
  }

  let partners: PartnerConnect[] = [];
  let loading = true;
  let expandedId: number | null = null;

  // Transfer modal
  let showTransfer = false;
  let transferPartnerId: number | null = null;
  let transferPartnerName = '';
  let transferAmount = 0;
  let transferDesc = '';
  let transferring = false;

  async function loadPartners() {
    loading = true;
    try {
      const res = await partnersApi.list();
      const list = res?.data ?? res?.partners ?? res ?? [];
      partners = (Array.isArray(list) ? list : []).map((p: any) => ({
        id: p.id,
        company_name: p.company_name ?? p.name ?? `Partner #${p.id}`,
        contact_email: p.contact_email ?? p.email ?? '',
        stripe_account_id: p.stripe_account_id ?? null,
        status: null,
        balance: null,
        loading: false,
      }));
    } catch (e: any) {
      toasts.error(e.message ?? 'Error cargando partners');
    } finally {
      loading = false;
    }
  }

  async function loadStatus(partner: PartnerConnect) {
    partner.loading = true;
    partners = partners;
    try {
      const status = await stripeConnectApi.getStatus(partner.id);
      partner.status = status;
      if (status.has_account && status.charges_enabled) {
        const balance = await stripeConnectApi.getBalance(partner.id);
        partner.balance = balance;
      }
    } catch (e: any) {
      toasts.error(`Error consultando status de ${partner.company_name}`);
    } finally {
      partner.loading = false;
      partners = partners;
    }
  }

  async function createAccount(partner: PartnerConnect) {
    partner.loading = true;
    partners = partners;
    try {
      const res = await stripeConnectApi.createAccount(partner.id);
      if (res.success) {
        partner.stripe_account_id = res.account_id;
        toasts.success(`Cuenta Connect creada para ${partner.company_name}`);
        if (res.onboarding_url) {
          window.open(res.onboarding_url, '_blank');
        }
        await loadStatus(partner);
      }
    } catch (e: any) {
      toasts.error(e.message ?? 'Error creando cuenta Connect');
    } finally {
      partner.loading = false;
      partners = partners;
    }
  }

  async function openOnboarding(partnerId: number) {
    try {
      const res = await stripeConnectApi.getOnboardingLink(partnerId);
      if (res.url) window.open(res.url, '_blank');
    } catch (e: any) {
      toasts.error(e.message ?? 'Error generando link de onboarding');
    }
  }

  async function openDashboard(partnerId: number) {
    try {
      const res = await stripeConnectApi.getDashboardLink(partnerId);
      if (res.url) window.open(res.url, '_blank');
    } catch (e: any) {
      toasts.error(e.message ?? 'Error generando link de dashboard');
    }
  }

  async function handleTransfer() {
    if (!transferPartnerId || transferAmount <= 0) return;
    transferring = true;
    try {
      const res = await stripeConnectApi.transfer({
        partner_id: transferPartnerId,
        amount: transferAmount,
        description: transferDesc || undefined,
      });
      if (res.success) {
        toasts.success(`Transferencia de $${transferAmount.toFixed(2)} ejecutada`);
        showTransfer = false;
        transferAmount = 0;
        transferDesc = '';
        // Reload balance
        const p = partners.find(x => x.id === transferPartnerId);
        if (p) await loadStatus(p);
      }
    } catch (e: any) {
      toasts.error(e.message ?? 'Error ejecutando transferencia');
    } finally {
      transferring = false;
    }
  }

  function toggleExpand(partner: PartnerConnect) {
    if (expandedId === partner.id) {
      expandedId = null;
    } else {
      expandedId = partner.id;
      if (!partner.status && partner.stripe_account_id) {
        loadStatus(partner);
      }
    }
  }

  function formatMoney(cents: number): string {
    return (cents / 100).toLocaleString('en-US', { style: 'currency', currency: 'USD' });
  }

  onMount(loadPartners);
</script>

<div class="p-6">
  <!-- Header -->
  <div class="flex items-center justify-between mb-6">
    <div>
      <h1 class="page-title flex items-center gap-2"><CreditCard size={22} /> Stripe Connect</h1>
      <p class="page-subtitle mt-1">Gestión de cuentas Connect Express para partners — onboarding, balance y transferencias</p>
    </div>
    <button class="btn-ghost btn-sm" onclick={loadPartners}><RefreshCw size={14} /> Recargar</button>
  </div>

  {#if loading}
    <div class="flex justify-center py-12"><div class="spinner"></div></div>
  {:else if partners.length === 0}
    <div class="empty-state">
      <Users size={40} class="text-gray-600 mb-2" />
      <p class="text-gray-400">No hay partners registrados</p>
    </div>
  {:else}
    <div class="space-y-3">
      {#each partners as partner}
        <div class="card">
          <!-- Partner row -->
          <button type="button" class="w-full flex items-center justify-between p-4 text-left hover:bg-white/[0.02] transition-colors" onclick={() => toggleExpand(partner)}>
            <div class="flex items-center gap-4 min-w-0">
              <div class="w-10 h-10 rounded-lg bg-dark-subtle flex items-center justify-center shrink-0">
                {#if partner.stripe_account_id}
                  <CreditCard size={18} class="text-green-400" />
                {:else}
                  <CreditCard size={18} class="text-gray-600" />
                {/if}
              </div>
              <div class="min-w-0">
                <div class="font-medium text-sm">{partner.company_name}</div>
                <div class="text-xs text-gray-500">{partner.contact_email}</div>
              </div>
            </div>
            <div class="flex items-center gap-3">
              {#if partner.stripe_account_id}
                <span class="badge badge-success text-xs">Connect activo</span>
                <code class="text-xs font-mono text-gray-500 hidden sm:block">{partner.stripe_account_id}</code>
              {:else}
                <span class="badge badge-neutral text-xs">Sin cuenta</span>
              {/if}
              <ChevronDown size={16} class="text-gray-500 transition-transform {expandedId === partner.id ? 'rotate-180' : ''}" />
            </div>
          </button>

          <!-- Expanded details -->
          {#if expandedId === partner.id}
            <div class="border-t border-border-dark px-4 py-4">
              {#if partner.loading}
                <div class="flex items-center gap-2 text-sm text-gray-400"><Loader size={14} class="animate-spin" /> Cargando status…</div>
              {:else if !partner.stripe_account_id}
                <div class="flex items-center justify-between">
                  <p class="text-sm text-gray-400">Este partner no tiene una cuenta Stripe Connect.</p>
                  <button class="btn-accent btn-sm" onclick={() => createAccount(partner)}>Crear Cuenta Connect</button>
                </div>
              {:else if partner.status}
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <!-- Status card -->
                  <div class="bg-dark-subtle rounded-lg p-4">
                    <h4 class="text-xs uppercase tracking-wider text-gray-500 mb-2">Estado de Cuenta</h4>
                    <div class="space-y-2 text-sm">
                      <div class="flex items-center gap-2">
                        {#if partner.status.charges_enabled}<CheckCircle size={14} class="text-green-400" />{:else}<XCircle size={14} class="text-red-400" />{/if}
                        <span>Cargos {partner.status.charges_enabled ? 'habilitados' : 'deshabilitados'}</span>
                      </div>
                      <div class="flex items-center gap-2">
                        {#if partner.status.payouts_enabled}<CheckCircle size={14} class="text-green-400" />{:else}<XCircle size={14} class="text-red-400" />{/if}
                        <span>Payouts {partner.status.payouts_enabled ? 'habilitados' : 'deshabilitados'}</span>
                      </div>
                      <div class="flex items-center gap-2">
                        {#if partner.status.onboarding_ready}<CheckCircle size={14} class="text-green-400" />{:else}<AlertTriangle size={14} class="text-amber-400" />{/if}
                        <span>Onboarding {partner.status.onboarding_ready ? 'completado' : 'pendiente'}</span>
                      </div>
                    </div>
                  </div>

                  <!-- Balance card -->
                  <div class="bg-dark-subtle rounded-lg p-4">
                    <h4 class="text-xs uppercase tracking-wider text-gray-500 mb-2">Balance</h4>
                    {#if partner.balance}
                      <div class="space-y-2">
                        {#each partner.balance.available as bal}
                          <div class="flex items-center justify-between">
                            <span class="text-sm text-gray-400">Disponible</span>
                            <span class="text-lg font-semibold text-green-400">{formatMoney(bal.amount)}</span>
                          </div>
                        {/each}
                        {#each partner.balance.pending as bal}
                          <div class="flex items-center justify-between">
                            <span class="text-sm text-gray-400">Pendiente</span>
                            <span class="text-sm text-amber-400">{formatMoney(bal.amount)}</span>
                          </div>
                        {/each}
                      </div>
                    {:else}
                      <p class="text-sm text-gray-500">No disponible</p>
                    {/if}
                  </div>

                  <!-- Actions card -->
                  <div class="bg-dark-subtle rounded-lg p-4">
                    <h4 class="text-xs uppercase tracking-wider text-gray-500 mb-2">Acciones</h4>
                    <div class="space-y-2">
                      {#if !partner.status.onboarding_ready}
                        <button class="btn-accent btn-sm w-full" onclick={() => openOnboarding(partner.id)}>
                          <Link size={13} /> Enviar a Onboarding
                        </button>
                      {/if}
                      {#if partner.status.charges_enabled}
                        <button class="btn-ghost btn-sm w-full" onclick={() => openDashboard(partner.id)}>
                          <ExternalLink size={13} /> Dashboard Stripe
                        </button>
                        <button class="btn-ghost btn-sm w-full" onclick={() => {
                          transferPartnerId = partner.id;
                          transferPartnerName = partner.company_name;
                          showTransfer = true;
                        }}>
                          <ArrowUpRight size={13} /> Transferir fondos
                        </button>
                      {/if}
                      <button class="btn-ghost btn-sm w-full" onclick={() => loadStatus(partner)}>
                        <RefreshCw size={13} /> Actualizar status
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Requirements -->
                {#if partner.status.requirements && (partner.status.requirements.currently_due.length > 0 || partner.status.requirements.past_due.length > 0)}
                  <div class="mt-4 p-3 bg-amber-900/20 border border-amber-700/30 rounded-lg">
                    <h4 class="text-xs uppercase tracking-wider text-amber-400 mb-2 flex items-center gap-1"><AlertTriangle size={12} /> Requisitos pendientes</h4>
                    <div class="flex flex-wrap gap-1">
                      {#each [...(partner.status.requirements.past_due ?? []), ...(partner.status.requirements.currently_due ?? [])] as req}
                        <span class="badge badge-warning text-xs">{req}</span>
                      {/each}
                    </div>
                  </div>
                {/if}
              {:else}
                <div class="flex items-center gap-2">
                  <button class="btn-ghost btn-sm" onclick={() => loadStatus(partner)}><RefreshCw size={13} /> Cargar status</button>
                </div>
              {/if}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

<!-- Transfer Modal -->
{#if showTransfer && transferPartnerId}
  <div class="modal-backdrop" onclick={() => (showTransfer = false)}>
    <div class="modal-panel max-w-sm" onclick={(e) => e.stopPropagation()}>
      <h2 class="text-lg font-semibold mb-4 flex items-center gap-2"><DollarSign size={18} /> Transferir a {transferPartnerName}</h2>
      <div class="space-y-4">
        <div>
          <label class="label-field">Monto (USD) *</label>
          <input type="number" bind:value={transferAmount} class="input-field w-full" placeholder="500.00" min="0.01" step="0.01" />
        </div>
        <div>
          <label class="label-field">Descripción</label>
          <input type="text" bind:value={transferDesc} class="input-field w-full" placeholder="Comisión Q1 2026" />
        </div>
      </div>
      <div class="flex justify-end gap-2 mt-6">
        <button class="btn-ghost btn-sm" onclick={() => (showTransfer = false)}>Cancelar</button>
        <button class="btn-accent btn-sm" disabled={transferring || transferAmount <= 0} onclick={handleTransfer}>
          {#if transferring}Procesando…{:else}Transferir ${transferAmount.toFixed(2)}{/if}
        </button>
      </div>
    </div>
  </div>
{/if}
