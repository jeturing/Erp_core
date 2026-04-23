<script lang="ts">
  import { onMount } from 'svelte'
  import { medprepApi } from '$lib/api/medprep'
  import type { MedSubStats, MedSubscription, MedSession, MedBank } from '$lib/api/medprep'
  import { toasts } from '$lib/stores/toast'
  import { formatDate } from '$lib/utils/formatters'
  import {
    Stethoscope, Users, TrendingUp, CreditCard, Wifi, RefreshCcw,
    Search, X, CheckCircle, XCircle, Clock, AlertTriangle,
    ChevronLeft, ChevronRight, BookOpen, Activity,
  } from 'lucide-svelte'

  // ── State ──
  let stats      = $state<MedSubStats | null>(null)
  let subs       = $state<MedSubscription[]>([])
  let sessions   = $state<MedSession[]>([])
  let banks      = $state<MedBank[]>([])
  let loading    = $state(true)
  let sessLoading = $state(false)
  let tab        = $state<'subs' | 'sessions' | 'banks'>('subs')
  let search     = $state('')
  let filterStatus  = $state('all')
  let filterBank    = $state('')
  let page       = $state(1)
  let totalPages = $state(1)
  let cancelingId = $state<number | null>(null)

  async function loadAll() {
    loading = true
    try {
      const [statsRes, subsRes, banksRes] = await Promise.all([
        medprepApi.stats(),
        medprepApi.subscriptions({ status: filterStatus, bank_slug: filterBank || undefined, search: search || undefined, page }),
        medprepApi.banks(),
      ])
      if (statsRes.success) stats = statsRes.data
      if (subsRes.success) {
        subs = subsRes.data
        totalPages = subsRes.meta?.pages ?? 1
      }
      if (banksRes.success) banks = banksRes.data
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error cargando datos MedPrep')
    } finally {
      loading = false
    }
  }

  async function loadSessions() {
    sessLoading = true
    try {
      const res = await medprepApi.sessions()
      if (res.success) sessions = res.data
    } catch (e: any) {
      toasts.error('Error cargando sesiones en vivo')
    } finally {
      sessLoading = false
    }
  }

  async function cancelSub(id: number, userName: string) {
    if (!confirm(`¿Cancelar suscripción de ${userName}? Esta acción es irreversible.`)) return
    cancelingId = id
    try {
      const res = await medprepApi.cancelSubscription(id)
      if (res.success) {
        toasts.success('Suscripción cancelada correctamente')
        await loadAll()
      }
    } catch (e: any) {
      toasts.error(e?.message ?? 'Error al cancelar')
    } finally {
      cancelingId = null
    }
  }

  function statusBadge(status: string, isActive: boolean) {
    if (isActive) return { label: 'Activa', class: 'bg-green-500/15 text-green-400 border-green-500/20' }
    if (status === 'canceled') return { label: 'Cancelada', class: 'bg-red-500/15 text-red-400 border-red-500/20' }
    if (status === 'past_due') return { label: 'Vencida', class: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/20' }
    return { label: status, class: 'bg-gray-500/15 text-gray-400 border-gray-500/20' }
  }

  $effect(() => {
    if (tab === 'sessions') loadSessions()
  })

  onMount(() => {
    loadAll()
  })
</script>

<svelte:head>
  <title>MedPrep — Estudiantes y Suscripciones</title>
</svelte:head>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 rounded-xl bg-emerald-500/10 flex items-center justify-center">
        <Stethoscope size={18} class="text-emerald-400" />
      </div>
      <div>
        <h1 class="text-xl font-semibold text-white">MedPrep</h1>
        <p class="text-xs text-gray-400">Gestión de estudiantes y suscripciones</p>
      </div>
    </div>
    <button onclick={loadAll} class="btn-ghost flex items-center gap-2 text-sm">
      <RefreshCcw size={14} />
      Actualizar
    </button>
  </div>

  <!-- Stats cards -->
  {#if stats}
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      {#each [
        { label: 'Estudiantes activos', value: stats.active_students, icon: Users, color: 'text-emerald-400' },
        { label: 'Suscripciones activas', value: stats.active, icon: CheckCircle, color: 'text-blue-400' },
        { label: 'ARR proyectado', value: `$${stats.arr_usd.toLocaleString()}`, icon: TrendingUp, color: 'text-yellow-400' },
        { label: 'Nuevas (30d)', value: stats.new_last_30d, icon: Activity, color: 'text-purple-400' },
      ] as card}
        <div class="card p-4">
          <div class="flex items-start justify-between mb-2">
            <p class="text-xs text-gray-400">{card.label}</p>
            <card.icon size={16} class={card.color} />
          </div>
          <p class="text-2xl font-bold text-white">{card.value}</p>
        </div>
      {/each}
    </div>

    <!-- Distribución por banco -->
    <div class="card p-4">
      <h3 class="text-sm font-medium text-gray-300 mb-3 flex items-center gap-2">
        <BookOpen size={14} />
        Suscripciones activas por banco
      </h3>
      <div class="flex flex-wrap gap-3">
        {#each stats.by_bank as b}
          <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-800/60 border border-gray-700">
            <span class="w-2 h-2 rounded-full" style="background:{b.color}"></span>
            <span class="text-sm text-gray-300">{b.name}</span>
            <span class="text-sm font-medium text-white">{b.active}</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Tabs -->
  <div class="flex gap-1 border-b border-gray-800">
    {#each [
      { id: 'subs', label: 'Suscripciones', icon: CreditCard },
      { id: 'sessions', label: 'Sesiones en vivo', icon: Wifi },
      { id: 'banks', label: 'Bancos', icon: BookOpen },
    ] as t}
      <button
        onclick={() => tab = t.id as any}
        class="flex items-center gap-2 px-4 py-2.5 text-sm border-b-2 transition-colors
               {tab === t.id ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-gray-400 hover:text-gray-300'}"
      >
        <t.icon size={14} />
        {t.label}
        {#if t.id === 'sessions' && sessions.length > 0}
          <span class="px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-xs">{sessions.length}</span>
        {/if}
      </button>
    {/each}
  </div>

  <!-- TAB: Suscripciones -->
  {#if tab === 'subs'}
    <!-- Filtros -->
    <div class="flex flex-wrap gap-3">
      <div class="relative flex-1 min-w-48">
        <Search size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Buscar por nombre o ID..."
          bind:value={search}
          oninput={() => { page = 1; loadAll() }}
          class="input pl-9 w-full"
        />
      </div>
      <select bind:value={filterStatus} onchange={() => { page = 1; loadAll() }} class="input">
        <option value="all">Todos los estados</option>
        <option value="active">Activas</option>
        <option value="canceled">Canceladas</option>
        <option value="past_due">Vencidas</option>
      </select>
      <select bind:value={filterBank} onchange={() => { page = 1; loadAll() }} class="input">
        <option value="">Todos los bancos</option>
        {#each banks as b}
          <option value={b.slug}>{b.name}</option>
        {/each}
      </select>
    </div>

    {#if loading}
      <div class="flex justify-center py-12">
        <div class="w-6 h-6 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin"></div>
      </div>
    {:else if subs.length === 0}
      <div class="card p-12 text-center text-gray-400 text-sm">
        No hay suscripciones que coincidan con los filtros.
      </div>
    {:else}
      <div class="card overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-800 text-xs text-gray-400">
              <th class="px-4 py-3 text-left">Estudiante</th>
              <th class="px-4 py-3 text-left">Banco</th>
              <th class="px-4 py-3 text-left">Estado</th>
              <th class="px-4 py-3 text-left">Vigencia</th>
              <th class="px-4 py-3 text-left">Precio</th>
              <th class="px-4 py-3 text-left">Creada</th>
              <th class="px-4 py-3 text-right">Acción</th>
            </tr>
          </thead>
          <tbody>
            {#each subs as sub}
              {@const badge = statusBadge(sub.status, sub.is_active)}
              <tr class="border-b border-gray-800/50 hover:bg-white/[0.02] transition-colors">
                <td class="px-4 py-3">
                  <div class="font-medium text-white">{sub.user.display_name || `User #${sub.user.sajet_user_id}`}</div>
                  <div class="text-xs text-gray-500">SAJET #{sub.user.sajet_user_id}</div>
                </td>
                <td class="px-4 py-3">
                  <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full shrink-0" style="background:{sub.bank.color}"></span>
                    {sub.bank.name}
                  </div>
                </td>
                <td class="px-4 py-3">
                  <span class="px-2 py-0.5 rounded-full border text-xs {badge.class}">{badge.label}</span>
                </td>
                <td class="px-4 py-3 text-gray-400 text-xs">
                  {#if sub.period_end}
                    {formatDate(sub.period_end)}
                  {:else}
                    —
                  {/if}
                </td>
                <td class="px-4 py-3">${sub.price.amount}/año</td>
                <td class="px-4 py-3 text-gray-400 text-xs">
                  {sub.created_at ? formatDate(sub.created_at) : '—'}
                </td>
                <td class="px-4 py-3 text-right">
                  {#if sub.is_active}
                    <button
                      onclick={() => cancelSub(sub.id, sub.user.display_name || `#${sub.user.sajet_user_id}`)}
                      disabled={cancelingId === sub.id}
                      class="px-2 py-1 rounded text-xs bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20 transition-colors disabled:opacity-50"
                    >
                      {cancelingId === sub.id ? '...' : 'Cancelar'}
                    </button>
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      <!-- Paginación -->
      {#if totalPages > 1}
        <div class="flex items-center justify-center gap-3 text-sm">
          <button
            onclick={() => { page = Math.max(1, page - 1); loadAll() }}
            disabled={page === 1}
            class="btn-ghost flex items-center gap-1 disabled:opacity-40"
          >
            <ChevronLeft size={14} /> Anterior
          </button>
          <span class="text-gray-400">Página {page} de {totalPages}</span>
          <button
            onclick={() => { page = Math.min(totalPages, page + 1); loadAll() }}
            disabled={page === totalPages}
            class="btn-ghost flex items-center gap-1 disabled:opacity-40"
          >
            Siguiente <ChevronRight size={14} />
          </button>
        </div>
      {/if}
    {/if}

  <!-- TAB: Sesiones en vivo -->
  {:else if tab === 'sessions'}
    <div class="flex items-center justify-between mb-4">
      <p class="text-sm text-gray-400">
        Sesiones MedPrep activas en Redis (TTL 1h desde último login)
      </p>
      <button onclick={loadSessions} class="btn-ghost flex items-center gap-2 text-sm">
        <RefreshCcw size={13} />
        Actualizar
      </button>
    </div>

    {#if sessLoading}
      <div class="flex justify-center py-12">
        <div class="w-6 h-6 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin"></div>
      </div>
    {:else if sessions.length === 0}
      <div class="card p-12 text-center">
        <Wifi size={32} class="text-gray-600 mx-auto mb-3" />
        <p class="text-gray-400 text-sm">No hay sesiones MedPrep activas en este momento.</p>
      </div>
    {:else}
      <div class="card overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-800 text-xs text-gray-400">
              <th class="px-4 py-3 text-left">Usuario (SAJET ID)</th>
              <th class="px-4 py-3 text-left">Email</th>
              <th class="px-4 py-3 text-left">Rol</th>
              <th class="px-4 py-3 text-left">IP</th>
              <th class="px-4 py-3 text-left">Login</th>
            </tr>
          </thead>
          <tbody>
            {#each sessions as sess}
              <tr class="border-b border-gray-800/50 hover:bg-white/[0.02]">
                <td class="px-4 py-3">
                  <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    SAJET #{sess.sajet_user_id}
                  </div>
                </td>
                <td class="px-4 py-3 text-gray-300">{sess.email}</td>
                <td class="px-4 py-3">
                  <span class="px-2 py-0.5 rounded-full text-xs
                    {sess.role === 'admin' ? 'bg-purple-500/15 text-purple-400' : 'bg-blue-500/15 text-blue-400'}">
                    {sess.role}
                  </span>
                </td>
                <td class="px-4 py-3 text-gray-400 font-mono text-xs">{sess.ip}</td>
                <td class="px-4 py-3 text-gray-400 text-xs">
                  {sess.login_at ? new Date(sess.login_at).toLocaleString('es-DO') : '—'}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}

  <!-- TAB: Bancos -->
  {:else if tab === 'banks'}
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      {#each banks as bank}
        <div class="card p-4 flex items-center gap-4">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0" style="background:{bank.color}22">
            <BookOpen size={18} style="color:{bank.color}" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="font-medium text-white">{bank.name}</div>
            <div class="text-xs text-gray-400 mt-0.5">
              {bank.question_count.toLocaleString()} preguntas ·
              {bank.flashcard_count.toLocaleString()} flashcards
            </div>
            {#if bank.stripe_price_id}
              <div class="text-xs text-gray-500 font-mono mt-0.5 truncate">{bank.stripe_price_id}</div>
            {/if}
          </div>
          <div class="text-right shrink-0">
            <div class="text-lg font-bold text-white">{bank.active_subscriptions}</div>
            <div class="text-xs text-gray-400">activos</div>
            <div class="text-xs text-emerald-400 mt-0.5">${bank.price_usd}/año</div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
