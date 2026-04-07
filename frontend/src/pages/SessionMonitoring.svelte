<!--
  DSAM — Dynamic Session & Anti-Theft Monitor
  Dashboard de monitoreo de sesiones, mapa geográfico, reglas de seguridad y playbook.
-->
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { dsamApi } from '$lib/api/dsam';
  import type {
    DashboardStats, SessionEntry, SecurityAction, SecurityRule,
    GeoPoint, LiveSession, TenantSessionConfig
  } from '$lib/api/dsam';
  import { toasts } from '$lib/stores/toast';
  import {
    Shield, Globe, Users, AlertTriangle, RefreshCw,
    MapPin, Lock, Unlock, Eye, Trash2, Plus, Play,
    Activity, Zap, Search, ChevronDown
  } from 'lucide-svelte';

  // ── State ──
  let activeTab = $state<'dashboard' | 'sessions' | 'geo' | 'rules' | 'playbook' | 'audit'>('dashboard');
  let loading = $state(false);
  let autoRefresh = $state(false);
  let refreshInterval: ReturnType<typeof setInterval> | null = null;

  // Dashboard
  let stats = $state<DashboardStats | null>(null);

  // Sessions
  let sessions = $state<SessionEntry[]>([]);
  let sessionsTotal = $state(0);
  let sessionsPage = $state(1);
  let sessionsTenantFilter = $state('');

  // Geo
  let livePositions = $state<LiveSession[]>([]);
  let heatmapData = $state<GeoPoint[]>([]);

  // Rules
  let rules = $state<SecurityRule[]>([]);
  let showRuleForm = $state(false);
  let newRuleType = $state('single_session');
  let newRuleTenant = $state('');
  let newRuleDesc = $state('');

  // Playbook (Security Actions)
  let actions = $state<SecurityAction[]>([]);
  let actionsTotal = $state(0);
  let actionsPage = $state(1);
  let actionsFilter = $state<'all' | 'unresolved' | 'critical'>('unresolved');

  // ── Data Loaders ──

  async function loadDashboard() {
    loading = true;
    try {
      const res = await dsamApi.getDashboard();
      if (res.success) stats = res.data;
    } catch (e: any) {
      toasts.error('Error cargando dashboard DSAM: ' + (e.message || e));
    }
    loading = false;
  }

  async function loadSessions() {
    loading = true;
    try {
      const res = await dsamApi.listSessions({
        tenant: sessionsTenantFilter || undefined,
        page: sessionsPage,
        limit: 50,
      });
      if (res.success) {
        sessions = res.data;
        sessionsTotal = res.meta.total || 0;
      }
    } catch (e: any) {
      toasts.error('Error cargando sesiones: ' + (e.message || e));
    }
    loading = false;
  }

  async function loadGeo() {
    loading = true;
    try {
      const [liveRes, heatRes] = await Promise.all([
        dsamApi.getGeoLive(),
        dsamApi.getGeoHeatmap(30),
      ]);
      if (liveRes.success) livePositions = liveRes.data;
      if (heatRes.success) heatmapData = heatRes.data;
    } catch (e: any) {
      toasts.error('Error cargando datos geo: ' + (e.message || e));
    }
    loading = false;
  }

  async function loadRules() {
    loading = true;
    try {
      const res = await dsamApi.listRules();
      if (res.success) rules = res.data;
    } catch (e: any) {
      toasts.error('Error cargando reglas: ' + (e.message || e));
    }
    loading = false;
  }

  async function loadActions() {
    loading = true;
    try {
      const params: any = { page: actionsPage, limit: 50 };
      if (actionsFilter === 'unresolved') params.resolved = false;
      if (actionsFilter === 'critical') { params.severity = 'critical'; params.resolved = false; }
      const res = await dsamApi.listActions(params);
      if (res.success) {
        actions = res.data;
        actionsTotal = res.meta.total || 0;
      }
    } catch (e: any) {
      toasts.error('Error cargando acciones: ' + (e.message || e));
    }
    loading = false;
  }

  // ── Actions ──

  async function syncNow() {
    try {
      const res = await dsamApi.syncSessions();
      if (res.success) {
        toasts.success(`Sync: ${res.data.scanned} escaneadas, ${res.data.created} nuevas, ${res.data.removed} eliminadas`);
        await loadDashboard();
      }
    } catch (e: any) {
      toasts.error('Error sync: ' + (e.message || e));
    }
  }

  async function runScan() {
    try {
      const res = await dsamApi.runScan();
      if (res.success) {
        toasts.success(`Scan: ${res.data.violations_found} violaciones, ${res.data.actions_taken} acciones`);
        await loadDashboard();
      }
    } catch (e: any) {
      toasts.error('Error scan: ' + (e.message || e));
    }
  }

  async function terminateSession(key: string) {
    if (!confirm('¿Terminar esta sesión? El usuario será desconectado inmediatamente.')) return;
    try {
      const res = await dsamApi.terminateSession(key, 'Admin termination');
      if (res.success) {
        toasts.success('Sesión terminada');
        await loadSessions();
      }
    } catch (e: any) {
      toasts.error('Error: ' + (e.message || e));
    }
  }

  async function lockAccount(tenant: string, login: string) {
    if (!confirm(`¿Bloquear cuenta ${login} en ${tenant}?`)) return;
    try {
      const res = await dsamApi.lockAccount(tenant, login, 'Security lock from DSAM');
      if (res.success) {
        toasts.success(`Cuenta ${login} bloqueada, ${res.data.sessions_terminated} sesiones terminadas`);
        await loadSessions();
      }
    } catch (e: any) {
      toasts.error('Error: ' + (e.message || e));
    }
  }

  async function createRule() {
    try {
      const res = await dsamApi.createRule({
        rule_type: newRuleType,
        tenant_db: newRuleTenant || null,
        description: newRuleDesc,
        config: {},
      });
      if (res.success) {
        toasts.success('Regla creada: #' + res.data.id);
        showRuleForm = false;
        newRuleType = 'single_session';
        newRuleTenant = '';
        newRuleDesc = '';
        await loadRules();
      }
    } catch (e: any) {
      toasts.error('Error creando regla: ' + (e.message || e));
    }
  }

  async function deleteRule(id: number) {
    if (!confirm('¿Eliminar regla #' + id + '?')) return;
    try {
      await dsamApi.deleteRule(id);
      toasts.success('Regla eliminada');
      await loadRules();
    } catch (e: any) {
      toasts.error('Error: ' + (e.message || e));
    }
  }

  async function resolveAction(id: number) {
    const note = prompt('Nota de resolución:');
    if (!note) return;
    try {
      await dsamApi.resolveAction(id, note);
      toasts.success('Acción resuelta');
      await loadActions();
      await loadDashboard();
    } catch (e: any) {
      toasts.error('Error: ' + (e.message || e));
    }
  }

  async function runAudit() {
    try {
      const res = await dsamApi.runSeatAudit();
      if (res.success) {
        toasts.success(`Auditoría: ${res.data.tenants_audited} tenants, ${res.data.tenants_over_limit} excedidos`);
      }
    } catch (e: any) {
      toasts.error('Error: ' + (e.message || e));
    }
  }

  // ── Tab change ──
  function switchTab(tab: typeof activeTab) {
    activeTab = tab;
    if (tab === 'dashboard') loadDashboard();
    else if (tab === 'sessions') loadSessions();
    else if (tab === 'geo') loadGeo();
    else if (tab === 'rules') loadRules();
    else if (tab === 'playbook') loadActions();
  }

  // ── Auto Refresh ──
  function toggleAutoRefresh() {
    autoRefresh = !autoRefresh;
    if (autoRefresh) {
      refreshInterval = setInterval(() => {
        if (activeTab === 'dashboard') loadDashboard();
        else if (activeTab === 'sessions') loadSessions();
        else if (activeTab === 'geo') loadGeo();
      }, 15000);
    } else if (refreshInterval) {
      clearInterval(refreshInterval);
      refreshInterval = null;
    }
  }

  // ── Severity helpers ──
  function severityColor(sev: string): string {
    switch (sev) {
      case 'critical': return 'badge-danger';
      case 'high': return 'badge-warning';
      case 'medium': return 'badge-neutral';
      default: return 'badge-success';
    }
  }

  function actionIcon(type: string): string {
    switch (type) {
      case 'session_terminated': return '🔌';
      case 'account_locked': return '🔒';
      case 'account_unlocked': return '🔓';
      case 'impossible_travel_detected': return '✈️';
      case 'concurrent_session_blocked': return '⚠️';
      case 'security_alert': return '🚨';
      default: return '📋';
    }
  }

  const ruleTypes = [
    { value: 'single_session', label: 'Sesión Única' },
    { value: 'max_sessions', label: 'Máx. Sesiones' },
    { value: 'geo_restriction', label: 'Restricción Geo' },
    { value: 'impossible_travel', label: 'Viaje Imposible' },
    { value: 'ip_whitelist', label: 'IP Whitelist' },
    { value: 'time_restriction', label: 'Restricción Horaria' },
  ];

  // ── Lifecycle ──
  onMount(() => loadDashboard());
  onDestroy(() => {
    if (refreshInterval) clearInterval(refreshInterval);
  });
</script>

<!-- ═══════════════════ TEMPLATE ═══════════════════ -->

<div class="dsam-container">
  <!-- Header -->
  <div class="dsam-header">
    <div>
      <h1 class="page-title">
        <Shield class="inline w-7 h-7 mr-2" style="color: #00FF9F" />
        DSAM — Session Monitor
      </h1>
      <p class="page-subtitle">Dynamic Session & Anti-Theft Monitor</p>
    </div>
    <div class="dsam-header-actions">
      <button class="btn-sm btn-accent" onclick={syncNow} title="Sync Redis → BD">
        <RefreshCw class="w-4 h-4" /> Sync
      </button>
      <button class="btn-sm btn-secondary" onclick={runScan} title="Ejecutar scan completo">
        <Play class="w-4 h-4" /> Scan
      </button>
      <button
        class="btn-sm"
        class:btn-accent={autoRefresh}
        class:btn-secondary={!autoRefresh}
        onclick={toggleAutoRefresh}
      >
        <Activity class="w-4 h-4" /> {autoRefresh ? 'Auto ON' : 'Auto OFF'}
      </button>
    </div>
  </div>

  <!-- Tabs -->
  <div class="dsam-tabs">
    {#each [
      { key: 'dashboard', label: 'Dashboard', icon: Zap },
      { key: 'sessions', label: 'Sesiones', icon: Users },
      { key: 'geo', label: 'Geo Mapa', icon: Globe },
      { key: 'rules', label: 'Reglas', icon: Shield },
      { key: 'playbook', label: 'Playbook', icon: AlertTriangle },
      { key: 'audit', label: 'Auditoría', icon: Search },
    ] as tab}
      {@const IconComp = tab.icon}
      <button
        class="dsam-tab"
        class:active={activeTab === tab.key}
        onclick={() => switchTab(tab.key as typeof activeTab)}
      >
        <IconComp class="w-4 h-4" />
        {tab.label}
      </button>
    {/each}
  </div>

  {#if loading}
    <div class="dsam-loading">
      <RefreshCw class="w-6 h-6 animate-spin" />
      <span>Cargando...</span>
    </div>
  {/if}

  <!-- ═══ DASHBOARD TAB ═══ -->
  {#if activeTab === 'dashboard' && stats}
    <div class="dsam-grid-4">
      <div class="stat-card">
        <div class="stat-value" style="color: #00FF9F">{stats.total_active}</div>
        <div class="stat-label">Sesiones Activas</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{stats.by_tenant.length}</div>
        <div class="stat-label">Tenants Conectados</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: {stats.critical_alerts > 0 ? '#ef4444' : '#00FF9F'}">
          {stats.critical_alerts}
        </div>
        <div class="stat-label">Alertas Críticas</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: {stats.unresolved_alerts > 0 ? '#f59e0b' : '#00FF9F'}">
          {stats.unresolved_alerts}
        </div>
        <div class="stat-label">Sin Resolver</div>
      </div>
    </div>

    <div class="dsam-grid-2">
      <!-- Por Tenant -->
      <div class="card">
        <h3 class="section-heading">Sesiones por Tenant</h3>
        {#if stats.by_tenant.length === 0}
          <p class="text-gray-500">Sin sesiones activas</p>
        {:else}
          <div class="dsam-table-wrap">
            <table class="dsam-table">
              <thead>
                <tr><th>Tenant</th><th class="text-right">Sesiones</th></tr>
              </thead>
              <tbody>
                {#each stats.by_tenant as t}
                  <tr>
                    <td><span class="font-mono text-sm">{t.tenant}</span></td>
                    <td class="text-right font-bold">{t.count}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>

      <!-- Por País -->
      <div class="card">
        <h3 class="section-heading">Sesiones por País</h3>
        {#if stats.by_country.length === 0}
          <p class="text-gray-500">Sin datos geográficos</p>
        {:else}
          <div class="dsam-table-wrap">
            <table class="dsam-table">
              <thead>
                <tr><th>País</th><th>Código</th><th class="text-right">Sesiones</th></tr>
              </thead>
              <tbody>
                {#each stats.by_country as c}
                  <tr>
                    <td>{c.country || 'Desconocido'}</td>
                    <td><span class="badge-neutral">{c.code || '??'}</span></td>
                    <td class="text-right font-bold">{c.count}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>
    </div>
  {/if}

  <!-- ═══ SESSIONS TAB ═══ -->
  {#if activeTab === 'sessions'}
    <div class="dsam-filter-bar">
      <input
        class="input"
        type="text"
        placeholder="Filtrar por tenant (ej: smarttoolsrd)"
        bind:value={sessionsTenantFilter}
        onkeydown={(e) => { if (e.key === 'Enter') loadSessions(); }}
      />
      <button class="btn-sm btn-accent" onclick={loadSessions}>
        <Search class="w-4 h-4" /> Buscar
      </button>
      <span class="text-sm text-gray-400">{sessionsTotal} sesiones</span>
    </div>

    <div class="card">
      <div class="dsam-table-wrap">
        <table class="dsam-table">
          <thead>
            <tr>
              <th>Tenant</th>
              <th>Usuario</th>
              <th>IP</th>
              <th>País / Ciudad</th>
              <th>Última Act.</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {#each sessions as s}
              <tr>
                <td><span class="font-mono text-sm">{s.tenant_db}</span></td>
                <td>{s.odoo_login || '—'}</td>
                <td><span class="font-mono text-xs">{s.ip_address}</span></td>
                <td>
                  {#if s.country}
                    <MapPin class="inline w-3 h-3" /> {s.country}
                    {#if s.city}, {s.city}{/if}
                  {:else}
                    <span class="text-gray-500">—</span>
                  {/if}
                </td>
                <td class="text-xs">{s.last_activity || '—'}</td>
                <td>
                  <button class="btn-sm btn-secondary" onclick={() => terminateSession(s.redis_key)} title="Terminar sesión">
                    <Zap class="w-3 h-3" />
                  </button>
                  {#if s.odoo_login}
                    <button class="btn-sm btn-secondary" onclick={() => lockAccount(s.tenant_db, s.odoo_login!)} title="Bloquear cuenta">
                      <Lock class="w-3 h-3" />
                    </button>
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      {#if sessionsTotal > 50}
        <div class="dsam-pagination">
          <button class="btn-sm btn-secondary" disabled={sessionsPage <= 1} onclick={() => { sessionsPage--; loadSessions(); }}>← Anterior</button>
          <span class="text-sm">Página {sessionsPage}</span>
          <button class="btn-sm btn-secondary" onclick={() => { sessionsPage++; loadSessions(); }}>Siguiente →</button>
        </div>
      {/if}
    </div>
  {/if}

  <!-- ═══ GEO TAB ═══ -->
  {#if activeTab === 'geo'}
    <div class="dsam-grid-2">
      <div class="card">
        <h3 class="section-heading"><Globe class="inline w-5 h-5" /> Sesiones en Vivo ({livePositions.length})</h3>
        <div class="dsam-table-wrap" style="max-height: 500px; overflow-y: auto;">
          <table class="dsam-table">
            <thead>
              <tr><th>Tenant</th><th>Usuario</th><th>País</th><th>Ciudad</th><th>IP</th></tr>
            </thead>
            <tbody>
              {#each livePositions as p}
                <tr>
                  <td class="font-mono text-sm">{p.tenant_db}</td>
                  <td>{p.odoo_login}</td>
                  <td>{p.country || '—'}</td>
                  <td>{p.city || '—'}</td>
                  <td class="font-mono text-xs">{p.ip}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <h3 class="section-heading"><MapPin class="inline w-5 h-5" /> Heatmap — Top Ubicaciones (30 días)</h3>
        <div class="dsam-table-wrap" style="max-height: 500px; overflow-y: auto;">
          <table class="dsam-table">
            <thead>
              <tr><th>País</th><th>Ciudad</th><th>Lat</th><th>Lon</th><th class="text-right">Accesos</th></tr>
            </thead>
            <tbody>
              {#each heatmapData as h}
                <tr>
                  <td>{h.country || '—'} ({h.country_code})</td>
                  <td>{h.city || '—'}</td>
                  <td class="text-xs">{h.lat?.toFixed(2)}</td>
                  <td class="text-xs">{h.lon?.toFixed(2)}</td>
                  <td class="text-right font-bold">{h.count}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  {/if}

  <!-- ═══ RULES TAB ═══ -->
  {#if activeTab === 'rules'}
    <div class="dsam-filter-bar">
      <button class="btn-sm btn-accent" onclick={() => showRuleForm = !showRuleForm}>
        <Plus class="w-4 h-4" /> Nueva Regla
      </button>
      <span class="text-sm text-gray-400">{rules.length} reglas configuradas</span>
    </div>

    {#if showRuleForm}
      <div class="card" style="border-left: 3px solid #00FF9F;">
        <h3 class="section-heading">Crear Regla de Seguridad</h3>
        <div class="dsam-form-grid">
          <div>
            <label class="text-sm font-medium">Tipo de Regla</label>
            <select class="input" bind:value={newRuleType}>
              {#each ruleTypes as rt}
                <option value={rt.value}>{rt.label}</option>
              {/each}
            </select>
          </div>
          <div>
            <label class="text-sm font-medium">Tenant (vacío = global)</label>
            <input class="input" type="text" bind:value={newRuleTenant} placeholder="ej: smarttoolsrd" />
          </div>
          <div style="grid-column: span 2;">
            <label class="text-sm font-medium">Descripción</label>
            <input class="input" type="text" bind:value={newRuleDesc} placeholder="Descripción de la regla" />
          </div>
        </div>
        <div class="mt-3 flex gap-2">
          <button class="btn-sm btn-accent" onclick={createRule}>Crear</button>
          <button class="btn-sm btn-secondary" onclick={() => showRuleForm = false}>Cancelar</button>
        </div>
      </div>
    {/if}

    <div class="card">
      <div class="dsam-table-wrap">
        <table class="dsam-table">
          <thead>
            <tr>
              <th>#</th><th>Tipo</th><th>Tenant</th><th>Estado</th><th>Descripción</th><th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {#each rules as r}
              <tr>
                <td>{r.id}</td>
                <td><span class="badge-neutral">{r.rule_type}</span></td>
                <td>{r.tenant_db || 'GLOBAL'}</td>
                <td>
                  {#if r.is_enabled}
                    <span class="badge-success">Activa</span>
                  {:else}
                    <span class="badge-warning">Inactiva</span>
                  {/if}
                </td>
                <td class="text-sm">{r.description || '—'}</td>
                <td>
                  <button class="btn-sm btn-secondary" onclick={() => deleteRule(r.id)} title="Eliminar">
                    <Trash2 class="w-3 h-3" />
                  </button>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {/if}

  <!-- ═══ PLAYBOOK TAB ═══ -->
  {#if activeTab === 'playbook'}
    <div class="dsam-filter-bar">
      {#each [
        { key: 'unresolved', label: 'Sin Resolver' },
        { key: 'critical', label: 'Críticas' },
        { key: 'all', label: 'Todas' },
      ] as f}
        <button
          class="btn-sm"
          class:btn-accent={actionsFilter === f.key}
          class:btn-secondary={actionsFilter !== f.key}
          onclick={() => { actionsFilter = f.key as typeof actionsFilter; loadActions(); }}
        >
          {f.label}
        </button>
      {/each}
      <span class="text-sm text-gray-400">{actionsTotal} acciones</span>
    </div>

    <div class="card">
      <div class="dsam-table-wrap">
        <table class="dsam-table">
          <thead>
            <tr>
              <th></th><th>Tipo</th><th>Severidad</th><th>Tenant</th><th>Usuario</th><th>IP</th><th>Fecha</th><th>Estado</th><th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {#each actions as a}
              <tr>
                <td>{actionIcon(a.action_type)}</td>
                <td class="text-sm">{a.action_type.replace(/_/g, ' ')}</td>
                <td><span class={severityColor(a.severity)}>{a.severity.toUpperCase()}</span></td>
                <td class="font-mono text-sm">{a.tenant_db}</td>
                <td>{a.odoo_login || '—'}</td>
                <td class="font-mono text-xs">{a.ip_address || '—'}</td>
                <td class="text-xs">{a.created_at || '—'}</td>
                <td>
                  {#if a.resolved}
                    <span class="badge-success">Resuelto</span>
                  {:else}
                    <span class="badge-warning">Pendiente</span>
                  {/if}
                </td>
                <td>
                  {#if !a.resolved}
                    <button class="btn-sm btn-accent" onclick={() => resolveAction(a.id)} title="Resolver">
                      ✓
                    </button>
                  {:else}
                    <span class="text-xs text-gray-500" title={a.resolution_note || ''}>
                      {a.resolved_by || ''}
                    </span>
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {/if}

  <!-- ═══ AUDIT TAB ═══ -->
  {#if activeTab === 'audit'}
    <div class="dsam-filter-bar">
      <button class="btn-sm btn-accent" onclick={runAudit}>
        <Play class="w-4 h-4" /> Ejecutar Auditoría de Seats
      </button>
    </div>

    <div class="card">
      <h3 class="section-heading">Reconciliación Seats vs Sesiones Activas</h3>
      <p class="text-sm text-gray-400 mb-4">
        Compara usuarios únicos activos en Redis contra seats comprados en la suscripción.
        Ejecuta la auditoría para obtener datos actualizados.
      </p>
    </div>
  {/if}
</div>

<!-- ═══════════════════ STYLES ═══════════════════ -->
<style>
  .dsam-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 1.5rem;
  }
  .dsam-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
    gap: 1rem;
  }
  .dsam-header-actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
  }
  .dsam-tabs {
    display: flex;
    gap: 0.25rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 1.5rem;
    overflow-x: auto;
  }
  .dsam-tab {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.6rem 1rem;
    border: none;
    background: transparent;
    color: rgba(255, 255, 255, 0.6);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    white-space: nowrap;
    font-size: 0.875rem;
    transition: all 0.15s;
  }
  .dsam-tab:hover {
    color: #fff;
    background: rgba(255, 255, 255, 0.04);
  }
  .dsam-tab.active {
    color: #00FF9F;
    border-bottom-color: #00FF9F;
  }
  .dsam-grid-4 {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
  }
  .dsam-grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }
  @media (max-width: 768px) {
    .dsam-grid-2 { grid-template-columns: 1fr; }
  }
  .dsam-filter-bar {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
  }
  .dsam-table-wrap {
    overflow-x: auto;
  }
  .dsam-table {
    width: 100%;
    border-collapse: collapse;
  }
  .dsam-table th, .dsam-table td {
    padding: 0.5rem 0.75rem;
    text-align: left;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  }
  .dsam-table th {
    font-size: 0.75rem;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.4);
    font-weight: 600;
  }
  .dsam-table tr:hover {
    background: rgba(255, 255, 255, 0.02);
  }
  .dsam-pagination {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 1rem 0;
  }
  .dsam-loading {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 2rem;
    color: rgba(255, 255, 255, 0.5);
  }
  .dsam-form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }
</style>
