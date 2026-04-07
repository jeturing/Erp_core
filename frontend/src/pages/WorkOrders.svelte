<script lang="ts">
  import { onMount } from 'svelte';
  import { workOrdersApi } from '../lib/api/workOrders';
  import { billingApi } from '../lib/api/billing';
  import { blueprintsApi } from '../lib/api/blueprints';
  import type { WorkOrderItem, ModuleDetail } from '../lib/types';

  let orders: WorkOrderItem[] = [];
  let total = 0;
  let loading = true;
  let selectedOrder: WorkOrderItem | null = null;
  let loadingDetail = false;
  let filterStatus = '';
  let toast = '';
  let toastType: 'success' | 'error' = 'success';

  // Panel de aprobación de módulos
  let approvalMode = false;
  let approvedSet = new Set<string>();
  let rejectedSet = new Set<string>();
  let approvalNotes = '';
  let savingApproval = false;

  // Datos para dropdowns
  let customers: Array<{id: number, name: string, email?: string}> = [];
  let blueprintPackages: Array<{id: number, name: string, display_name?: string}> = [];
  let customerSearch = '';

  // Modal nueva WO
  let showCreate = false;
  let newWO = { customer_id: 0, description: '', work_type: 'provision', blueprint_package_id: 0, selected_modules: '' };
  let creating = false;

  $: filteredCustomers = customers.filter(c => {
    const q = customerSearch.toLowerCase();
    return !q || c.name.toLowerCase().includes(q) || (c.email || '').toLowerCase().includes(q);
  });

  const STATUS_LABELS: Record<string, string> = {
    requested: 'Solicitada', approved: 'Aprobada', in_progress: 'En Progreso',
    completed: 'Completada', rejected: 'Rechazada', cancelled: 'Cancelada',
  };
  const STATUS_COLORS: Record<string, string> = {
    requested: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    approved: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    in_progress: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    completed: 'bg-green-500/20 text-green-400 border-green-500/30',
    rejected: 'bg-red-500/20 text-red-400 border-red-500/30',
    cancelled: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  };

  function showToast(msg: string, type: 'success' | 'error' = 'success') {
    toast = msg; toastType = type;
    setTimeout(() => toast = '', 4000);
  }

  async function load() {
    loading = true;
    try {
      const res = await workOrdersApi.list({ status: filterStatus || undefined, limit: 100 });
      orders = res.items; total = res.total;
    } catch { showToast('Error cargando órdenes', 'error'); }
    finally { loading = false; }
  }

  async function loadFormData() {
    try {
      const [custRes, pkgRes] = await Promise.all([
        billingApi.getCustomers().catch(() => ({ items: [] })),
        blueprintsApi.getPackages().catch(() => ({ items: [] })),
      ]);
      customers = ((custRes as any)?.items ?? custRes ?? []).map((c: any) => ({
        id: c.id, name: c.company_name || c.name || `Cliente #${c.id}`, email: c.email
      }));
      blueprintPackages = ((pkgRes as any)?.items ?? pkgRes ?? []).map((p: any) => ({
        id: p.id, name: p.name, display_name: p.display_name
      }));
    } catch { /* silencioso */ }
  }

  async function openDetail(wo: WorkOrderItem) {
    loadingDetail = true; selectedOrder = wo; approvalMode = false;
    try {
      selectedOrder = await workOrdersApi.get(wo.id);
    } catch { }
    loadingDetail = false;
    // Pre-seleccionar todos como aprobados para el panel de revisión
    if (selectedOrder?.selected_modules) {
      approvedSet = new Set(selectedOrder.approved_modules ?? selectedOrder.selected_modules);
      rejectedSet = new Set(selectedOrder.rejected_modules ?? []);
    }
  }

  function enterApprovalMode() {
    if (!selectedOrder?.selected_modules?.length) return;
    approvalMode = true;
    approvedSet = new Set(selectedOrder.approved_modules ?? selectedOrder.selected_modules ?? []);
    rejectedSet = new Set(selectedOrder.rejected_modules ?? []);
  }

  function toggleModule(tn: string) {
    if (approvedSet.has(tn)) { approvedSet.delete(tn); approvedSet = new Set(approvedSet); rejectedSet.add(tn); rejectedSet = new Set(rejectedSet); }
    else { rejectedSet.delete(tn); rejectedSet = new Set(rejectedSet); approvedSet.add(tn); approvedSet = new Set(approvedSet); }
  }

  async function saveApproval() {
    if (!selectedOrder) return;
    savingApproval = true;
    try {
      await workOrdersApi.approveModules(selectedOrder.id, {
        approved_modules: [...approvedSet],
        rejected_modules: [...rejectedSet],
        notes: approvalNotes || undefined,
      });
      showToast('Módulos guardados ✅');
      approvalMode = false; approvalNotes = '';
      selectedOrder = await workOrdersApi.get(selectedOrder.id);
    } catch { showToast('Error guardando revisión', 'error'); }
    savingApproval = false;
  }

  async function transition(status: string) {
    if (!selectedOrder) return;
    const confirmMsg = status === 'completed'
      ? '¿Completar la orden? Se enviará email con credenciales al cliente.' : '';
    if (confirmMsg && !confirm(confirmMsg)) return;
    try {
      const res = await workOrdersApi.updateStatus(selectedOrder.id, { status });
      showToast(`Orden → ${STATUS_LABELS[status] ?? status} ✅`);
      selectedOrder = res.work_order;
      orders = orders.map(o => o.id === selectedOrder!.id ? selectedOrder! : o);
    } catch (e: any) {
      showToast(e?.message ?? 'Error al cambiar estado', 'error');
    }
  }

  async function createWO() {
    if (!newWO.customer_id || newWO.customer_id <= 0 || !newWO.description) { showToast('Cliente y descripción son requeridos', 'error'); return; }
    creating = true;
    try {
      const payload: any = {
        customer_id: newWO.customer_id,
        description: newWO.description,
        work_type: newWO.work_type,
      };
      if (newWO.blueprint_package_id) payload.blueprint_package_id = newWO.blueprint_package_id;
      if (newWO.selected_modules) payload.selected_modules = newWO.selected_modules.split(',').map((s: string) => s.trim()).filter(Boolean);
      await workOrdersApi.create(payload);
      showToast('Work Order creada ✅');
      showCreate = false;
      newWO = { customer_id: 0, description: '', work_type: 'provision', blueprint_package_id: 0, selected_modules: '' };
      customerSearch = '';
      await load();
    } catch { showToast('Error creando work order', 'error'); }
    creating = false;
  }

  function formatDate(d: string | null) {
    if (!d) return '—';
    return new Date(d).toLocaleString('es-MX', { dateStyle: 'short', timeStyle: 'short' });
  }

  function groupByCategory(modules: ModuleDetail[]) {
    const groups: Record<string, ModuleDetail[]> = {};
    for (const m of modules) {
      const cat = m.category ?? 'General';
      if (!groups[cat]) groups[cat] = [];
      groups[cat].push(m);
    }
    return groups;
  }

  onMount(load);
</script>

<!-- Toast -->
{#if toast}
  <div class="fixed top-4 right-4 z-50 px-5 py-3 rounded-lg shadow-xl font-medium text-sm
    {toastType === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}">
    {toast}
  </div>
{/if}

<div class="flex h-full gap-4">
  <!-- ─── Lista ───────────────────────────────────────────────── -->
  <div class="flex-1 flex flex-col gap-4 min-w-0">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-white">Órdenes de Trabajo</h1>
        <p class="text-sm text-gray-400 mt-0.5">{total} órdenes en total</p>
      </div>
      <button on:click={() => { showCreate = !showCreate; if (showCreate) loadFormData(); }}
        class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors">
        + Nueva Orden
      </button>
    </div>

    <!-- Filtros -->
    <div class="flex gap-2">
      {#each ['', 'requested', 'approved', 'in_progress', 'completed', 'rejected'] as s}
        <button on:click={() => { filterStatus = s; load(); }}
          class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border
            {filterStatus === s ? 'bg-red-600 text-white border-red-600' : 'border-gray-700 text-gray-400 hover:text-white hover:border-gray-500'}">
          {s === '' ? 'Todas' : STATUS_LABELS[s] ?? s}
        </button>
      {/each}
    </div>

    <!-- Tabla -->
    {#if loading}
      <div class="text-center py-16 text-gray-400">Cargando...</div>
    {:else if orders.length === 0}
      <div class="text-center py-16 text-gray-400">No hay órdenes{filterStatus ? ' con ese estado' : ''}.</div>
    {:else}
      <div class="flex-1 overflow-auto rounded-xl border border-gray-700">
        <table class="w-full text-sm">
          <thead class="bg-gray-800/80 sticky top-0">
            <tr>
              {#each ['Orden', 'Tipo', 'Blueprint', 'Estado', 'Módulos', 'Fecha'] as h}
                <th class="px-4 py-3 text-left text-xs text-gray-400 font-medium">{h}</th>
              {/each}
            </tr>
          </thead>
          <tbody>
            {#each orders as wo}
              <tr on:click={() => openDetail(wo)}
                class="border-t border-gray-700/50 hover:bg-gray-700/30 cursor-pointer transition-colors
                  {selectedOrder?.id === wo.id ? 'bg-gray-700/40' : ''}">
                <td class="px-4 py-3 font-mono text-xs text-gray-300">{wo.order_number}</td>
                <td class="px-4 py-3 text-gray-300">{wo.work_type}</td>
                <td class="px-4 py-3 text-gray-400 text-xs">{wo.blueprint_package_id ? `#${wo.blueprint_package_id}` : '—'}</td>
                <td class="px-4 py-3">
                  <span class="px-2 py-0.5 rounded-full border text-xs {STATUS_COLORS[wo.status] ?? ''}">
                    {STATUS_LABELS[wo.status] ?? wo.status}
                  </span>
                </td>
                <td class="px-4 py-3 text-gray-400 text-xs">
                  {#if wo.selected_modules}
                    <span class="text-blue-400">{wo.selected_modules.length} sel.</span>
                    {#if wo.approved_modules}
                      / <span class="text-green-400">{wo.approved_modules.length} apr.</span>
                    {/if}
                  {:else}—{/if}
                </td>
                <td class="px-4 py-3 text-gray-400 text-xs">{formatDate(wo.created_at)}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}

    <!-- Modal Nueva WO -->
    {#if showCreate}
      <div class="bg-gray-800 border border-gray-700 rounded-xl p-5 space-y-3">
        <h3 class="font-semibold text-white">Nueva Orden de Trabajo</h3>
        <div class="grid grid-cols-2 gap-3">
          <!-- Cliente con búsqueda -->
          <div class="col-span-2 md:col-span-1">
            <label class="text-xs text-gray-400 block mb-1">Cliente *</label>
            <input bind:value={customerSearch} placeholder="Buscar cliente..."
              class="w-full bg-gray-700 border border-gray-600 rounded-t-lg px-3 py-2 text-sm text-white" />
            {#if customerSearch && filteredCustomers.length > 0}
              <div class="border border-t-0 border-gray-600 rounded-b-lg bg-gray-800 max-h-36 overflow-y-auto">
                {#each filteredCustomers.slice(0, 8) as c}
                  <button type="button" class="w-full text-left px-3 py-2 text-sm hover:bg-gray-700 transition-colors
                    {newWO.customer_id === c.id ? 'bg-red-900/30 text-red-300' : 'text-white'}"
                    on:click={() => { newWO.customer_id = c.id; customerSearch = c.name; }}>
                    <span class="font-medium">{c.name}</span>
                    {#if c.email}<span class="text-gray-400 text-xs ml-2">{c.email}</span>{/if}
                  </button>
                {/each}
              </div>
            {:else if customerSearch && filteredCustomers.length === 0}
              <div class="border border-t-0 border-gray-600 rounded-b-lg bg-gray-800 px-3 py-2 text-xs text-gray-500">
                Sin resultados
              </div>
            {/if}
            {#if newWO.customer_id}
              <div class="text-[10px] text-green-400 mt-1">✓ Cliente ID: {newWO.customer_id}</div>
            {/if}
          </div>
          <!-- Tipo -->
          <div>
            <label class="text-xs text-gray-400 block mb-1">Tipo</label>
            <select bind:value={newWO.work_type} class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white">
              {#each [['provision','Provisión'],['module_install','Instalar Módulos'],['migration','Migración'],['configuration','Configuración'],['support','Soporte']] as [v,l]}
                <option value={v}>{l}</option>
              {/each}
            </select>
          </div>
          <!-- Blueprint -->
          <div class="col-span-2 md:col-span-1">
            <label class="text-xs text-gray-400 block mb-1">Blueprint / Paquete</label>
            <select bind:value={newWO.blueprint_package_id} class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white">
              <option value={0}>Sin paquete</option>
              {#each blueprintPackages as p}
                <option value={p.id}>{p.display_name || p.name}</option>
              {/each}
            </select>
          </div>
          <!-- Módulos extra -->
          <div>
            <label class="text-xs text-gray-400 block mb-1">Módulos extra (opcional)</label>
            <input bind:value={newWO.selected_modules} placeholder="crm_dashboard, pos"
              class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white" />
          </div>
        </div>
        <div>
          <label class="text-xs text-gray-400 block mb-1">Descripción *</label>
          <textarea bind:value={newWO.description} rows={2} placeholder="Descripción de la orden..."
            class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white resize-none"></textarea>
        </div>
        <div class="flex gap-2 justify-end">
          <button on:click={() => showCreate = false} class="px-4 py-2 text-sm text-gray-400 hover:text-white">Cancelar</button>
          <button on:click={createWO} disabled={creating}
            class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm disabled:opacity-50">
            {creating ? 'Creando...' : 'Crear Orden'}
          </button>
        </div>
      </div>
    {/if}
  </div>

  <!-- ─── Panel de detalle ─────────────────────────────────────── -->
  {#if selectedOrder}
    <div class="w-[480px] flex-shrink-0 bg-gray-800 border border-gray-700 rounded-xl p-5 overflow-y-auto flex flex-col gap-4">
      {#if loadingDetail}
        <div class="text-center py-8 text-gray-400">Cargando detalle...</div>
      {:else}
        <!-- Header detalle -->
        <div class="flex items-start justify-between">
          <div>
            <div class="font-mono text-sm text-gray-400">{selectedOrder.order_number}</div>
            <div class="font-semibold text-white mt-0.5">{selectedOrder.work_type}</div>
            {#if selectedOrder.customer_name}
              <div class="text-sm text-gray-400">{selectedOrder.customer_name}
                {#if selectedOrder.customer_subdomain}
                  <span class="text-xs text-blue-400 ml-1">{selectedOrder.customer_subdomain}.sajet.us</span>
                {/if}
              </div>
            {/if}
          </div>
          <div class="flex flex-col items-end gap-2">
            <span class="px-2.5 py-1 rounded-full border text-xs {STATUS_COLORS[selectedOrder.status] ?? ''}">
              {STATUS_LABELS[selectedOrder.status] ?? selectedOrder.status}
            </span>
            <button on:click={() => selectedOrder = null} class="text-gray-500 hover:text-white text-xs">✕ cerrar</button>
          </div>
        </div>

        <!-- Descripción -->
        <p class="text-sm text-gray-300 bg-gray-700/40 rounded-lg p-3">{selectedOrder.description}</p>

        <!-- Blueprint -->
        {#if selectedOrder.blueprint_name}
          <div class="text-sm">
            <span class="text-gray-400">Blueprint: </span>
            <span class="text-blue-400 font-medium">{selectedOrder.blueprint_name}</span>
          </div>
        {/if}

        <!-- Panel de Módulos -->
        {#if selectedOrder.selected_modules && selectedOrder.selected_modules.length > 0}
          <div class="border border-gray-700 rounded-xl overflow-hidden">
            <div class="bg-gray-700/50 px-4 py-3 flex items-center justify-between">
              <span class="text-sm font-medium text-white">
                Módulos Seleccionados ({selectedOrder.selected_modules.length})
              </span>
              {#if !approvalMode && selectedOrder.status === 'requested' || selectedOrder.status === 'approved'}
                <button on:click={enterApprovalMode}
                  class="text-xs text-yellow-400 hover:text-yellow-300 border border-yellow-500/30 px-2 py-1 rounded">
                  ✏️ Revisar módulos
                </button>
              {/if}
            </div>

            {#if !approvalMode}
              <!-- Vista de sólo lectura -->
              <div class="p-3 space-y-1 max-h-64 overflow-y-auto">
                {#if selectedOrder.selected_modules_detail}
                  {@const groups = groupByCategory(selectedOrder.selected_modules_detail)}
                  {#each Object.entries(groups) as [cat, mods]}
                    <div class="mb-2">
                      <div class="text-xs text-gray-500 uppercase tracking-wide mb-1">{cat}</div>
                      {#each mods as mod}
                        <div class="flex items-center gap-2 py-0.5">
                          {#if mod.approved}
                            <span class="w-4 h-4 rounded-full bg-green-500/20 border border-green-500/40 flex items-center justify-center text-green-400 text-xs">✓</span>
                          {:else if mod.rejected}
                            <span class="w-4 h-4 rounded-full bg-red-500/20 border border-red-500/40 flex items-center justify-center text-red-400 text-xs">✕</span>
                          {:else}
                            <span class="w-4 h-4 rounded-full bg-gray-600 border border-gray-500"></span>
                          {/if}
                          <span class="text-sm text-gray-300">{mod.display_name}</span>
                        </div>
                      {/each}
                    </div>
                  {/each}
                {:else}
                  {#each selectedOrder.selected_modules as tn}
                    <div class="text-sm text-gray-300 py-0.5">• {tn}</div>
                  {/each}
                {/if}
              </div>
            {:else}
              <!-- Modo aprobación con checkboxes -->
              <div class="p-3 space-y-1 max-h-72 overflow-y-auto">
                <p class="text-xs text-yellow-400 mb-2">☑ Marcado = Aprobado &nbsp; ☐ Sin marcar = Rechazado</p>
                {#if selectedOrder.selected_modules_detail}
                  {@const groups = groupByCategory(selectedOrder.selected_modules_detail)}
                  {#each Object.entries(groups) as [cat, mods]}
                    <div class="mb-2">
                      <div class="text-xs text-gray-500 uppercase tracking-wide mb-1">{cat}</div>
                      {#each mods as mod}
                        <label class="flex items-center gap-2 py-1 cursor-pointer hover:bg-gray-700/30 rounded px-1">
                          <input type="checkbox"
                            checked={approvedSet.has(mod.technical_name)}
                            on:change={() => toggleModule(mod.technical_name)}
                            class="w-4 h-4 rounded border-gray-500 accent-green-500" />
                          <span class="text-sm {approvedSet.has(mod.technical_name) ? 'text-white' : 'text-gray-500 line-through'}">
                            {mod.display_name}
                          </span>
                        </label>
                      {/each}
                    </div>
                  {/each}
                {:else}
                  {#each selectedOrder.selected_modules as tn}
                    <label class="flex items-center gap-2 py-1 cursor-pointer">
                      <input type="checkbox"
                        checked={approvedSet.has(tn)}
                        on:change={() => toggleModule(tn)}
                        class="w-4 h-4 rounded accent-green-500" />
                      <span class="text-sm {approvedSet.has(tn) ? 'text-white' : 'text-gray-500 line-through'}">{tn}</span>
                    </label>
                  {/each}
                {/if}
              </div>
              <div class="p-3 border-t border-gray-700 space-y-2">
                <div class="flex gap-2 text-xs text-gray-400">
                  <span class="text-green-400 font-medium">{approvedSet.size} aprobados</span>
                  <span>•</span>
                  <span class="text-red-400 font-medium">{rejectedSet.size} rechazados</span>
                </div>
                <textarea bind:value={approvalNotes} placeholder="Notas de revisión (opcional)..." rows={2}
                  class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm text-white resize-none"></textarea>
                <div class="flex gap-2">
                  <button on:click={() => { approvalMode = false; approvalNotes = ''; }}
                    class="flex-1 px-3 py-2 text-sm text-gray-400 hover:text-white border border-gray-600 rounded-lg">
                    Cancelar
                  </button>
                  <button on:click={saveApproval} disabled={savingApproval}
                    class="flex-1 px-3 py-2 text-sm bg-green-600 hover:bg-green-700 text-white rounded-lg disabled:opacity-50">
                    {savingApproval ? 'Guardando...' : '💾 Guardar revisión'}
                  </button>
                </div>
              </div>
            {/if}
          </div>
        {/if}

        <!-- Credenciales (solo si completada) -->
        {#if selectedOrder.status === 'completed' && selectedOrder.tenant_admin_email}
          <div class="bg-gray-700/40 border border-gray-600 rounded-xl p-3 space-y-1.5">
            <div class="text-xs font-semibold text-gray-300 mb-2">🔑 Credenciales generadas</div>
            <div class="text-xs"><span class="text-gray-400">Admin:</span> <code class="text-white">{selectedOrder.tenant_admin_email}</code></div>
            {#if selectedOrder.tenant_user_email}
              <div class="text-xs"><span class="text-gray-400">Usuario:</span> <code class="text-white">{selectedOrder.tenant_user_email}</code></div>
            {/if}
          </div>
        {/if}

        <!-- Timeline -->
        <div class="text-xs text-gray-500 space-y-0.5">
          {#if selectedOrder.requested_at}<div>📋 Solicitada: {formatDate(selectedOrder.requested_at)} por {selectedOrder.requested_by ?? '—'}</div>{/if}
          {#if selectedOrder.approved_at}<div>✅ Aprobada: {formatDate(selectedOrder.approved_at)} por {selectedOrder.approved_by ?? '—'}</div>{/if}
          {#if selectedOrder.completed_at}<div>🏁 Completada: {formatDate(selectedOrder.completed_at)} por {selectedOrder.completed_by ?? '—'}</div>{/if}
        </div>

        <!-- Notas -->
        {#if selectedOrder.notes}
          <div class="bg-gray-700/30 rounded-lg p-3">
            <div class="text-xs text-gray-400 mb-1 font-medium">Notas</div>
            <pre class="text-xs text-gray-300 whitespace-pre-wrap font-sans">{selectedOrder.notes}</pre>
          </div>
        {/if}

        <!-- Botones de transición -->
        <div class="flex flex-wrap gap-2 pt-2 border-t border-gray-700">
          {#if selectedOrder.status === 'requested'}
            <button on:click={() => transition('approved')}
              class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-medium">
              ✅ Aprobar
            </button>
            <button on:click={() => transition('rejected')}
              class="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-medium">
              ✕ Rechazar
            </button>
          {/if}
          {#if selectedOrder.status === 'approved'}
            <button on:click={() => transition('in_progress')}
              class="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-medium">
              ▶ Iniciar
            </button>
            <button on:click={() => transition('cancelled')}
              class="px-3 py-1.5 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-xs font-medium">
              Cancelar
            </button>
          {/if}
          {#if selectedOrder.status === 'in_progress'}
            <button on:click={() => transition('completed')}
              class="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded-lg text-xs font-medium">
              🏁 Completar + Enviar Email
            </button>
            <button on:click={() => transition('cancelled')}
              class="px-3 py-1.5 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-xs font-medium">
              Cancelar
            </button>
          {/if}
        </div>
      {/if}
    </div>
  {/if}
</div>
