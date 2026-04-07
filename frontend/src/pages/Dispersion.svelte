<script lang="ts">
  import { onMount } from 'svelte';
  import { dispersionApi, type DispersionStatus, type PayoutRequest } from '../lib/api';
  import { toasts } from '../lib/stores';
  import {
    Zap, ZapOff, DollarSign, AlertCircle, CheckCircle2, Clock,
    XCircle, RefreshCw, Plus, ShieldCheck, Ban, ChevronDown,
    ChevronUp, Wallet, ArrowRightLeft, TrendingUp, Lock, Unlock,
    Info, Send,
  } from 'lucide-svelte';

  // ── state ──────────────────────────────────────────────────────────────────
  let status: DispersionStatus | null = null;
  let payouts: PayoutRequest[] = [];
  let loading = true;
  let statusFilter = '';
  let expandedId: number | null = null;
  let refreshing = false;

  // Modals
  let showCreateModal = false;
  let showAuthorizeModal = false;
  let showRejectModal = false;
  let selectedPayout: PayoutRequest | null = null;

  // Toggle feature flag
  let togglingFlag = false;
  let flagReason = '';
  let showFlagModal = false;

  // Create form
  let createForm = {
    provider_name: '',
    provider_account: '',
    provider_routing: '',
    amount_usd: 0,
    payment_method: 'ach',
    concept: '',
    reference: '',
    notes: '',
  };
  let creating = false;

  // Authorize
  let authorizeNote = '';
  let authorizing = false;

  // Reject
  let rejectReason = '';
  let rejecting = false;

  // ── helpers ────────────────────────────────────────────────────────────────
  const fmt = (n: number | null | undefined, digits = 2) =>
    n == null ? '—' : `$${Number(n).toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits })}`;

  const fmtDate = (s: string | null) =>
    s ? new Date(s).toLocaleString('es-DO', { dateStyle: 'short', timeStyle: 'short' }) : '—';

  const STATUS_LABEL: Record<string, string> = {
    pending_approval: 'Pendiente',
    authorized:       'Autorizado',
    processing:       'Procesando',
    completed:        'Completado',
    failed:           'Fallido',
    rejected:         'Rechazado',
  };

  const STATUS_CLASS: Record<string, string> = {
    pending_approval: 'bg-amber-100 text-amber-800',
    authorized:       'bg-blue-100 text-blue-800',
    processing:       'bg-purple-100 text-purple-800',
    completed:        'bg-green-100 text-green-800',
    failed:           'bg-red-100 text-red-800',
    rejected:         'bg-gray-100 text-gray-600',
  };

  // ── data loading ───────────────────────────────────────────────────────────
  async function loadAll() {
    loading = true;
    try {
      [status, { payouts: payouts }] = await Promise.all([
        dispersionApi.getStatus(),
        dispersionApi.listPayouts(statusFilter || undefined),
      ]);
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error cargando datos de dispersión');
    } finally {
      loading = false;
    }
  }

  async function refresh() {
    refreshing = true;
    await loadAll();
    refreshing = false;
  }

  onMount(loadAll);

  // ── feature flag ───────────────────────────────────────────────────────────
  async function handleToggleFlag() {
    if (!status) return;
    const newVal = !status.enabled;
    togglingFlag = true;
    try {
      await dispersionApi.setFeatureFlag(newVal, flagReason || undefined);
      toasts.success(`Dispersión Mercury ${newVal ? 'activada' : 'desactivada'}.`);
      showFlagModal = false;
      flagReason = '';
      await loadAll();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error cambiando flag');
    } finally {
      togglingFlag = false;
    }
  }

  // ── create payout ──────────────────────────────────────────────────────────
  async function handleCreate() {
    creating = true;
    try {
      const res = await dispersionApi.createPayout({
        provider_name:    createForm.provider_name,
        provider_account: createForm.provider_account,
        provider_routing: createForm.provider_routing,
        amount_usd:       Number(createForm.amount_usd),
        payment_method:   createForm.payment_method,
        concept:          createForm.concept,
        reference:        createForm.reference || undefined,
        notes:            createForm.notes || undefined,
      });
      toasts.success(`Solicitud #${(res as any).payout_id} creada. Pendiente de autorización.`);
      showCreateModal = false;
      createForm = { provider_name: '', provider_account: '', provider_routing: '', amount_usd: 0, payment_method: 'ach', concept: '', reference: '', notes: '' };
      await loadAll();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error creando solicitud');
    } finally {
      creating = false;
    }
  }

  // ── authorize ──────────────────────────────────────────────────────────────
  async function handleAuthorize() {
    if (!selectedPayout) return;
    authorizing = true;
    try {
      await dispersionApi.authorizePayout(selectedPayout.id, authorizeNote || undefined);
      toasts.success(`Pago #${selectedPayout.id} autorizado y enviado a Mercury.`);
      showAuthorizeModal = false;
      authorizeNote = '';
      selectedPayout = null;
      await loadAll();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error autorizando pago');
    } finally {
      authorizing = false;
    }
  }

  // ── reject ─────────────────────────────────────────────────────────────────
  async function handleReject() {
    if (!selectedPayout) return;
    if (!rejectReason.trim()) { toasts.error('Debes indicar el motivo del rechazo'); return; }
    rejecting = true;
    try {
      await dispersionApi.rejectPayout(selectedPayout.id, rejectReason);
      toasts.success(`Solicitud #${selectedPayout.id} rechazada.`);
      showRejectModal = false;
      rejectReason = '';
      selectedPayout = null;
      await loadAll();
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error rechazando pago');
    } finally {
      rejecting = false;
    }
  }

  function openAuthorize(p: PayoutRequest) { selectedPayout = p; showAuthorizeModal = true; }
  function openReject(p: PayoutRequest)    { selectedPayout = p; showRejectModal    = true; }
</script>

<!-- ═══════════════════════════════════════════════════════════════
     HEADER
════════════════════════════════════════════════════════════════ -->
<div class="p-6 space-y-6">
  <div class="flex items-center justify-between">
    <div>
      <h1 class="page-title flex items-center gap-2">
        <ArrowRightLeft size={22} />
        Dispersión Mercury
      </h1>
      <p class="page-subtitle mt-1">
        Pagos directos a proveedores vía Mercury Banking — requieren autorización 4-ojos
      </p>
    </div>
    <div class="flex items-center gap-2">
      <button
        on:click={refresh}
        class="btn-secondary flex items-center gap-1 text-sm"
        disabled={refreshing}
      >
        <RefreshCw size={14} class={refreshing ? 'animate-spin' : ''} />
        Actualizar
      </button>
      {#if status?.enabled}
        <button
          on:click={() => showCreateModal = true}
          class="btn-primary flex items-center gap-1 text-sm"
        >
          <Plus size={14} />
          Nueva Solicitud
        </button>
      {/if}
    </div>
  </div>

  {#if loading}
    <div class="text-center py-16 text-gray-400">Cargando sistema de dispersión…</div>
  {:else}

  <!-- ═══ FEATURE FLAG BANNER ═════════════════════════════════════════════ -->
  <div class="rounded-xl border-2 p-5 flex items-center justify-between
    {status?.enabled
      ? 'bg-green-50 border-green-300'
      : 'bg-amber-50 border-amber-300'}">
    <div class="flex items-center gap-3">
      {#if status?.enabled}
        <Zap size={28} class="text-green-600" />
        <div>
          <p class="font-semibold text-green-800">Dispersión Mercury ACTIVA</p>
          <p class="text-sm text-green-700">Los pagos a proveedores pueden crearse y autorizarse.</p>
        </div>
      {:else}
        <ZapOff size={28} class="text-amber-600" />
        <div>
          <p class="font-semibold text-amber-800">Dispersión Mercury INACTIVA</p>
          <p class="text-sm text-amber-700">Activa para permitir pagos directos. No se ejecutará ningún pago.</p>
        </div>
      {/if}
      <span class="text-xs text-gray-400 ml-2">
        (flag desde {status?.feature_flag_source === 'database' ? 'BD' : 'ENV'})
      </span>
    </div>
    <button
      on:click={() => showFlagModal = true}
      class="flex items-center gap-1 text-sm font-medium px-4 py-2 rounded-lg border transition
        {status?.enabled
          ? 'border-green-400 text-green-700 hover:bg-green-100'
          : 'border-amber-400 text-amber-700 hover:bg-amber-100'}"
    >
      {#if status?.enabled}
        <Lock size={14} /> Desactivar
      {:else}
        <Unlock size={14} /> Activar
      {/if}
    </button>
  </div>

  <!-- ═══ TARJETAS DE ESTADO ══════════════════════════════════════════════ -->
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
    <!-- Mercury Connection -->
    <div class="card p-4 flex items-center gap-3">
      <div class="p-2 rounded-lg {status?.mercury_connected ? 'bg-green-100' : 'bg-red-100'}">
        {#if status?.mercury_connected}
          <CheckCircle2 size={20} class="text-green-600" />
        {:else}
          <XCircle size={20} class="text-red-500" />
        {/if}
      </div>
      <div>
        <p class="text-xs text-gray-500">Mercury API</p>
        <p class="font-semibold text-sm {status?.mercury_connected ? 'text-green-700' : 'text-red-600'}">
          {status?.mercury_connected ? 'Conectado' : 'Sin conexión'}
        </p>
      </div>
    </div>

    <!-- CHECKING balance -->
    <div class="card p-4 flex items-center gap-3">
      <div class="p-2 rounded-lg bg-blue-100">
        <Wallet size={20} class="text-blue-600" />
      </div>
      <div>
        <p class="text-xs text-gray-500">CHECKING (Proveedores)</p>
        <p class="font-semibold text-sm">{fmt(status?.checking_balance)}</p>
      </div>
    </div>

    <!-- SAVINGS balance -->
    <div class="card p-4 flex items-center gap-3">
      <div class="p-2 rounded-lg bg-emerald-100">
        <TrendingUp size={20} class="text-emerald-600" />
      </div>
      <div>
        <p class="text-xs text-gray-500">SAVINGS (Reserva)</p>
        <p class="font-semibold text-sm">{fmt(status?.savings_balance)}</p>
      </div>
    </div>

    <!-- Límite diario -->
    <div class="card p-4 flex items-center gap-3">
      <div class="p-2 rounded-lg bg-purple-100">
        <DollarSign size={20} class="text-purple-600" />
      </div>
      <div>
        <p class="text-xs text-gray-500">Disponible hoy</p>
        <p class="font-semibold text-sm">{fmt(status?.remaining_today_usd)}</p>
        <p class="text-xs text-gray-400">de {fmt(status?.daily_limit_usd, 0)}</p>
      </div>
    </div>
  </div>

  <!-- ═══ CONTADORES DE PAYOUTS ═════════════════════════════════════════════ -->
  <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
    {#each [
      { key: 'pending_approval', label: 'Pendientes',  count: status?.pending_count,    color: 'amber',  icon: Clock       },
      { key: 'authorized',       label: 'Autorizados', count: status?.authorized_count, color: 'blue',   icon: ShieldCheck },
      { key: 'processing',       label: 'Procesando',  count: status?.processing_count, color: 'purple', icon: Send        },
      { key: 'completed',        label: 'Completados', count: status?.completed_today,  color: 'green',  icon: CheckCircle2},
      { key: 'failed',           label: 'Fallidos',    count: status?.failed_today,     color: 'red',    icon: AlertCircle },
    ] as item}
      <button
        on:click={() => { statusFilter = statusFilter === item.key ? '' : item.key; loadAll(); }}
        class="card p-4 text-center cursor-pointer transition hover:shadow-md
          {statusFilter === item.key ? 'ring-2 ring-offset-1 ring-terracotta' : ''}"
      >
        <p class="text-2xl font-bold text-{item.color}-600">{item.count ?? 0}</p>
        <p class="text-xs text-gray-500 mt-1">{item.label}
          {item.key === 'completed' || item.key === 'failed' ? ' (hoy)' : ''}
        </p>
      </button>
    {/each}
  </div>

  <!-- ═══ TABLA DE PAYOUTS ══════════════════════════════════════════════════ -->
  <div class="card overflow-hidden">
    <div class="flex items-center justify-between p-4 border-b border-gray-100">
      <h2 class="font-semibold text-gray-700 flex items-center gap-2">
        <ArrowRightLeft size={16} />
        Solicitudes de Pago
        {#if statusFilter}
          <span class="text-xs bg-terracotta/10 text-terracotta px-2 py-0.5 rounded-full">
            {STATUS_LABEL[statusFilter] ?? statusFilter}
          </span>
          <button on:click={() => { statusFilter = ''; loadAll(); }} class="text-gray-400 hover:text-gray-600 text-xs underline">
            limpiar
          </button>
        {/if}
      </h2>
    </div>

    {#if payouts.length === 0}
      <div class="text-center py-12 text-gray-400">
        <ArrowRightLeft size={32} class="mx-auto mb-2 opacity-30" />
        <p>No hay solicitudes{statusFilter ? ` con estado "${STATUS_LABEL[statusFilter]}"` : ''}.</p>
        {#if status?.enabled}
          <button on:click={() => showCreateModal = true} class="mt-3 text-terracotta text-sm underline">
            Crear primera solicitud
          </button>
        {/if}
      </div>
    {:else}
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
            <tr>
              <th class="px-4 py-3 text-left">#</th>
              <th class="px-4 py-3 text-left">Proveedor</th>
              <th class="px-4 py-3 text-left">Método</th>
              <th class="px-4 py-3 text-right">Monto</th>
              <th class="px-4 py-3 text-left">Estado</th>
              <th class="px-4 py-3 text-left">Creado por</th>
              <th class="px-4 py-3 text-left">Fecha</th>
              <th class="px-4 py-3 text-center">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            {#each payouts as p}
              <tr class="hover:bg-gray-50 transition">
                <td class="px-4 py-3 font-mono text-gray-500">#{p.id}</td>
                <td class="px-4 py-3">
                  <div class="font-medium text-gray-800">{p.provider_name}</div>
                  <div class="text-xs text-gray-400">{p.concept}</div>
                </td>
                <td class="px-4 py-3">
                  <span class="uppercase text-xs font-semibold px-2 py-0.5 rounded bg-gray-100 text-gray-600">
                    {p.payment_method}
                  </span>
                </td>
                <td class="px-4 py-3 text-right font-semibold">{fmt(p.amount_usd)}</td>
                <td class="px-4 py-3">
                  <span class="px-2 py-0.5 rounded-full text-xs font-medium {STATUS_CLASS[p.status] ?? ''}">
                    {STATUS_LABEL[p.status] ?? p.status}
                  </span>
                </td>
                <td class="px-4 py-3 text-gray-500 text-xs">{p.created_by}</td>
                <td class="px-4 py-3 text-gray-400 text-xs">{fmtDate(p.created_at)}</td>
                <td class="px-4 py-3">
                  <div class="flex items-center justify-center gap-1">
                    <!-- Expand detail -->
                    <button
                      on:click={() => expandedId = expandedId === p.id ? null : p.id}
                      class="p-1 hover:bg-gray-200 rounded"
                      title="Ver detalle"
                    >
                      {#if expandedId === p.id}
                        <ChevronUp size={14} />
                      {:else}
                        <ChevronDown size={14} />
                      {/if}
                    </button>

                    {#if p.status === 'pending_approval'}
                      <button
                        on:click={() => openAuthorize(p)}
                        class="p-1 hover:bg-green-100 rounded text-green-600"
                        title="Autorizar pago"
                      >
                        <ShieldCheck size={14} />
                      </button>
                      <button
                        on:click={() => openReject(p)}
                        class="p-1 hover:bg-red-100 rounded text-red-500"
                        title="Rechazar"
                      >
                        <Ban size={14} />
                      </button>
                    {/if}
                  </div>
                </td>
              </tr>

              <!-- ── Expanded detail row ── -->
              {#if expandedId === p.id}
                <tr>
                  <td colspan="8" class="px-6 pb-4 pt-1 bg-gray-50">
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                      <div><span class="text-gray-400">Cuenta destino</span><br /><span class="font-mono">{p.provider_account}</span></div>
                      <div><span class="text-gray-400">Ruta/SWIFT</span><br /><span class="font-mono">{p.provider_routing}</span></div>
                      <div><span class="text-gray-400">Referencia</span><br />{p.reference ?? '—'}</div>
                      <div><span class="text-gray-400">Mercury ID</span><br /><span class="font-mono">{p.mercury_payment_id ?? '—'}</span></div>
                      {#if p.notes}
                        <div class="col-span-2"><span class="text-gray-400">Notas</span><br />{p.notes}</div>
                      {/if}
                      {#if p.authorization_note}
                        <div class="col-span-2">
                          <span class="text-gray-400">Nota autorización</span>
                          <br /><span class="text-blue-700">{p.authorization_note}</span>
                          <span class="text-gray-400 ml-1">— {p.authorized_by} ({fmtDate(p.authorized_at)})</span>
                        </div>
                      {/if}
                      {#if p.rejection_reason}
                        <div class="col-span-2">
                          <span class="text-gray-400">Motivo rechazo</span>
                          <br /><span class="text-red-600">{p.rejection_reason}</span>
                          <span class="text-gray-400 ml-1">— {p.rejected_by} ({fmtDate(p.rejected_at)})</span>
                        </div>
                      {/if}
                      {#if p.error_message}
                        <div class="col-span-4">
                          <span class="text-gray-400">Error Mercury</span>
                          <br /><span class="text-red-600 font-mono">{p.error_message}</span>
                        </div>
                      {/if}
                    </div>
                  </td>
                </tr>
              {/if}
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>

  {/if}<!-- end if loading -->
</div>

<!-- ═══════════════════════════════════════════════════════════════
     MODAL — Feature Flag
════════════════════════════════════════════════════════════════ -->
{#if showFlagModal && status}
  <div class="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 space-y-4">
      <div class="flex items-center gap-3">
        {#if status.enabled}
          <Lock size={22} class="text-amber-500" />
          <h3 class="font-semibold text-gray-800">Desactivar Dispersión Mercury</h3>
        {:else}
          <Unlock size={22} class="text-green-500" />
          <h3 class="font-semibold text-gray-800">Activar Dispersión Mercury</h3>
        {/if}
      </div>

      {#if !status.enabled}
        <div class="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800 flex gap-2">
          <Info size={16} class="shrink-0 mt-0.5" />
          <span>Al activar, los administradores podrán crear y autorizar pagos directos a proveedores vía Mercury. <strong>Cada pago requiere aprobación de un segundo admin.</strong></span>
        </div>
      {:else}
        <div class="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm text-gray-700 flex gap-2">
          <Info size={16} class="shrink-0 mt-0.5" />
          <span>Al desactivar no se cancelarán pagos en procesamiento, pero no se podrán crear nuevas solicitudes.</span>
        </div>
      {/if}

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Motivo del cambio <span class="text-gray-400">(opcional)</span>
        </label>
        <textarea
          bind:value={flagReason}
          rows="2"
          placeholder="Ej: Activación para pago a proveedor ABC…"
          class="input w-full resize-none"
        />
      </div>

      <div class="flex gap-3 pt-2">
        <button
          on:click={() => { showFlagModal = false; flagReason = ''; }}
          class="btn-secondary flex-1"
        >Cancelar</button>
        <button
          on:click={handleToggleFlag}
          disabled={togglingFlag}
          class="flex-1 py-2 rounded-lg font-medium text-white transition
            {status.enabled ? 'bg-amber-500 hover:bg-amber-600' : 'bg-green-600 hover:bg-green-700'}"
        >
          {togglingFlag ? 'Guardando…' : (status.enabled ? 'Desactivar' : 'Activar')}
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- ═══════════════════════════════════════════════════════════════
     MODAL — Nueva Solicitud
════════════════════════════════════════════════════════════════ -->
{#if showCreateModal}
  <div class="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 space-y-4 max-h-[90vh] overflow-y-auto">
      <div class="flex items-center gap-2">
        <Plus size={20} class="text-terracotta" />
        <h3 class="font-semibold text-gray-800">Nueva Solicitud de Pago</h3>
      </div>

      <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800 flex gap-2">
        <ShieldCheck size={16} class="shrink-0 mt-0.5 text-blue-500" />
        <span>Esta solicitud quedará <strong>pendiente de autorización</strong> por otro administrador antes de ejecutarse.</span>
      </div>

      <div class="space-y-3">
        <div class="grid grid-cols-2 gap-3">
          <div class="col-span-2">
            <label class="block text-sm font-medium text-gray-700 mb-1">Nombre del Proveedor *</label>
            <input bind:value={createForm.provider_name} class="input w-full" placeholder="Ej: Proveedor XYZ S.A." />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Número de Cuenta *</label>
            <input bind:value={createForm.provider_account} class="input w-full font-mono" placeholder="123456789" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Ruta / SWIFT *</label>
            <input bind:value={createForm.provider_routing} class="input w-full font-mono" placeholder="091311229 o CHFGUS44" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Monto USD *</label>
            <input bind:value={createForm.amount_usd} type="number" min="0.01" step="0.01" class="input w-full" placeholder="0.00" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Método *</label>
            <select bind:value={createForm.payment_method} class="input w-full">
              <option value="ach">ACH (gratis, 1–3 días)</option>
              <option value="wire">Wire ($15, mismo día)</option>
            </select>
          </div>
          <div class="col-span-2">
            <label class="block text-sm font-medium text-gray-700 mb-1">Concepto / Descripción *</label>
            <input bind:value={createForm.concept} class="input w-full" placeholder="Ej: Pago factura #INV-2026-001" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Referencia interna</label>
            <input bind:value={createForm.reference} class="input w-full" placeholder="Ej: PO-2026-55" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Notas para el autorizador</label>
            <input bind:value={createForm.notes} class="input w-full" placeholder="Contexto adicional…" />
          </div>
        </div>
      </div>

      <div class="flex gap-3 pt-2">
        <button on:click={() => showCreateModal = false} class="btn-secondary flex-1">Cancelar</button>
        <button
          on:click={handleCreate}
          disabled={creating || !createForm.provider_name || !createForm.amount_usd || !createForm.concept}
          class="btn-primary flex-1"
        >
          {creating ? 'Enviando…' : 'Crear Solicitud'}
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- ═══════════════════════════════════════════════════════════════
     MODAL — Autorizar
════════════════════════════════════════════════════════════════ -->
{#if showAuthorizeModal && selectedPayout}
  <div class="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 space-y-4">
      <div class="flex items-center gap-2">
        <ShieldCheck size={20} class="text-green-600" />
        <h3 class="font-semibold text-gray-800">Autorizar Pago #{selectedPayout.id}</h3>
      </div>

      <div class="bg-gray-50 rounded-lg p-4 text-sm space-y-2">
        <div class="flex justify-between">
          <span class="text-gray-500">Proveedor</span>
          <span class="font-medium">{selectedPayout.provider_name}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">Monto</span>
          <span class="font-bold text-lg text-green-700">{fmt(selectedPayout.amount_usd)}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">Método</span>
          <span class="uppercase font-semibold">{selectedPayout.payment_method}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">Concepto</span>
          <span>{selectedPayout.concept}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">Cuenta destino</span>
          <span class="font-mono text-xs">{selectedPayout.provider_account}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">Creado por</span>
          <span>{selectedPayout.created_by}</span>
        </div>
      </div>

      <div class="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800 flex gap-2">
        <AlertCircle size={16} class="shrink-0 mt-0.5" />
        <span><strong>Este pago se ejecutará inmediatamente en Mercury</strong> al autorizar. No es reversible.</span>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Nota de autorización <span class="text-gray-400">(opcional)</span></label>
        <textarea bind:value={authorizeNote} rows="2" class="input w-full resize-none" placeholder="Ej: Verificado con factura #INV-2026-001" />
      </div>

      <div class="flex gap-3 pt-2">
        <button on:click={() => { showAuthorizeModal = false; selectedPayout = null; }} class="btn-secondary flex-1">
          Cancelar
        </button>
        <button
          on:click={handleAuthorize}
          disabled={authorizing}
          class="flex-1 py-2 rounded-lg font-medium text-white bg-green-600 hover:bg-green-700 transition"
        >
          {authorizing ? 'Autorizando…' : '✓ Autorizar y Ejecutar'}
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- ═══════════════════════════════════════════════════════════════
     MODAL — Rechazar
════════════════════════════════════════════════════════════════ -->
{#if showRejectModal && selectedPayout}
  <div class="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 space-y-4">
      <div class="flex items-center gap-2">
        <Ban size={20} class="text-red-500" />
        <h3 class="font-semibold text-gray-800">Rechazar Solicitud #{selectedPayout.id}</h3>
      </div>

      <div class="bg-gray-50 rounded-lg p-3 text-sm">
        <div class="flex justify-between">
          <span class="text-gray-500">Proveedor</span>
          <span class="font-medium">{selectedPayout.provider_name}</span>
        </div>
        <div class="flex justify-between mt-1">
          <span class="text-gray-500">Monto</span>
          <span class="font-bold">{fmt(selectedPayout.amount_usd)}</span>
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Motivo del rechazo *</label>
        <textarea bind:value={rejectReason} rows="3" class="input w-full resize-none" placeholder="Explica por qué se rechaza esta solicitud…" />
      </div>

      <div class="flex gap-3 pt-2">
        <button on:click={() => { showRejectModal = false; selectedPayout = null; }} class="btn-secondary flex-1">Cancelar</button>
        <button
          on:click={handleReject}
          disabled={rejecting || !rejectReason.trim()}
          class="flex-1 py-2 rounded-lg font-medium text-white bg-red-600 hover:bg-red-700 transition"
        >
          {rejecting ? 'Rechazando…' : 'Rechazar Solicitud'}
        </button>
      </div>
    </div>
  </div>
{/if}
