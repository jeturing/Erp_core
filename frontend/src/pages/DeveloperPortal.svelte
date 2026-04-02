<script lang="ts">
  /**
   * DeveloperPortal.svelte — Developer Portal Dashboard
   *
   * Multi-stage agreement flow (Uber-style):
   * App Created → Organization Linked → Agreements (Generate→Pending→View→Review→Signed)
   * → Sandbox Access → Verification → Verified
   */
  import { onMount } from 'svelte';
  import {
    Plus, Loader2, CheckCircle, Circle, Clock, Eye, FileSignature,
    Building2, Shield, Rocket, XCircle, ExternalLink, ChevronRight,
    AlertTriangle, FileText, Trash2, Send
  } from 'lucide-svelte';
  import { developerPortalApi } from '../lib/api';
  import SignaturePanel from '../lib/components/SignaturePanel.svelte';
  import type {
    DeveloperAppSummary,
    DeveloperAgreementFlow,
    DeveloperAgreementFlowItem,
    AgreementFlowStatus,
  } from '../lib/types';

  let apps: DeveloperAppSummary[] = [];
  let selectedApp: DeveloperAppSummary | null = null;
  let selectedFlow: DeveloperAgreementFlow | null = null;
  let loading = true;
  let error = '';
  let success = '';

  // Create app modal
  let showCreateModal = false;
  let newAppName = '';
  let newAppDescription = '';
  let newAppApiSuite = 'eats_marketplace';
  let creating = false;

  // Link org modal
  let showLinkOrgModal = false;
  let orgName = '';
  let linking = false;

  // Signing state
  let signing = false;
  let signingFlowId: number | null = null;

  // Review state
  let reviewing = false;
  let rejectReason = '';

  // Admin check (from Layout context or store)
  let isAdmin = false;
  // We'll detect from the app data

  onMount(async () => {
    await loadApps();
  });

  async function loadApps() {
    loading = true;
    error = '';
    try {
      const res = await developerPortalApi.listApps();
      apps = res.items;
    } catch (e: any) {
      error = e.message || 'Error al cargar apps';
    } finally {
      loading = false;
    }
  }

  async function loadApp(id: number) {
    try {
      selectedApp = await developerPortalApi.getApp(id);
    } catch (e: any) {
      error = e.message || 'Error al cargar app';
    }
  }

  async function createApp() {
    if (!newAppName.trim()) return;
    creating = true;
    error = '';
    try {
      const res = await developerPortalApi.createApp({
        name: newAppName.trim(),
        description: newAppDescription.trim(),
        api_suite: newAppApiSuite,
      });
      apps = [res.app, ...apps];
      selectedApp = res.app;
      showCreateModal = false;
      newAppName = '';
      newAppDescription = '';
      success = 'App creada exitosamente';
      setTimeout(() => success = '', 3000);
    } catch (e: any) {
      error = e.message || 'Error al crear app';
    } finally {
      creating = false;
    }
  }

  async function linkOrganization() {
    if (!selectedApp || !orgName.trim()) return;
    linking = true;
    error = '';
    try {
      const res = await developerPortalApi.linkOrganization(selectedApp.id, orgName.trim());
      selectedApp = res.app;
      // Update in list
      apps = apps.map(a => a.id === selectedApp!.id ? selectedApp! : a);
      showLinkOrgModal = false;
      orgName = '';
      success = 'Organización vinculada';
      setTimeout(() => success = '', 3000);
    } catch (e: any) {
      error = e.message || 'Error al vincular organización';
    } finally {
      linking = false;
    }
  }

  async function viewAgreement(flowItem: DeveloperAgreementFlowItem) {
    error = '';
    try {
      // Load full flow with HTML content
      selectedFlow = await developerPortalApi.getFlow(flowItem.id);

      // Mark as viewed if pending
      if (flowItem.status === 'pending') {
        await developerPortalApi.markViewed(flowItem.id);
        selectedFlow.status = 'viewed';
        // Reload app to get updated statuses
        if (selectedApp) {
          selectedApp = await developerPortalApi.getApp(selectedApp.id);
          apps = apps.map(a => a.id === selectedApp!.id ? selectedApp! : a);
        }
      }
    } catch (e: any) {
      error = e.message || 'Error al cargar acuerdo';
    }
  }

  async function handleSign(e: CustomEvent<{ signer_name: string; signature_data: string }>) {
    if (!selectedFlow) return;
    signing = true;
    error = '';
    try {
      await developerPortalApi.signFlow(selectedFlow.id, {
        signer_name: e.detail.signer_name,
        signature_data: e.detail.signature_data,
      });
      selectedFlow.status = 'in_review';
      success = 'Acuerdo firmado. Pendiente de revisión.';
      setTimeout(() => success = '', 4000);

      // Reload app
      if (selectedApp) {
        selectedApp = await developerPortalApi.getApp(selectedApp.id);
        apps = apps.map(a => a.id === selectedApp!.id ? selectedApp! : a);
      }
      selectedFlow = null;
    } catch (e: any) {
      error = e.message || 'Error al firmar';
    } finally {
      signing = false;
    }
  }

  async function reviewFlow(flowId: number, action: 'approve' | 'reject') {
    reviewing = true;
    error = '';
    try {
      await developerPortalApi.reviewFlow(flowId, {
        action,
        reason: action === 'reject' ? rejectReason : undefined,
      });
      success = action === 'approve' ? 'Acuerdo aprobado' : 'Acuerdo rechazado';
      setTimeout(() => success = '', 3000);
      rejectReason = '';

      // Reload app
      if (selectedApp) {
        selectedApp = await developerPortalApi.getApp(selectedApp.id);
        apps = apps.map(a => a.id === selectedApp!.id ? selectedApp! : a);
      }
    } catch (e: any) {
      error = e.message || 'Error al revisar';
    } finally {
      reviewing = false;
    }
  }

  async function requestProduction() {
    if (!selectedApp) return;
    error = '';
    try {
      await developerPortalApi.requestProduction(selectedApp.id);
      selectedApp = await developerPortalApi.getApp(selectedApp.id);
      apps = apps.map(a => a.id === selectedApp!.id ? selectedApp! : a);
      success = 'Solicitud de producción enviada';
      setTimeout(() => success = '', 3000);
    } catch (e: any) {
      error = e.message || 'Error al solicitar producción';
    }
  }

  // ── UI Helpers ──

  const flowStatusConfig: Record<AgreementFlowStatus, { icon: any; color: string; label: string; bg: string }> = {
    generated:  { icon: Circle,         color: 'text-gray-400',  label: 'Generado',     bg: 'bg-gray-100' },
    pending:    { icon: Clock,          color: 'text-amber-500', label: 'Pendiente',    bg: 'bg-amber-50' },
    viewed:     { icon: Eye,            color: 'text-blue-500',  label: 'Visto',        bg: 'bg-blue-50' },
    in_review:  { icon: FileSignature,  color: 'text-purple-500',label: 'En Revisión',  bg: 'bg-purple-50' },
    signed:     { icon: CheckCircle,    color: 'text-green-600', label: 'Firmado',      bg: 'bg-green-50' },
    rejected:   { icon: XCircle,        color: 'text-red-500',   label: 'Rechazado',    bg: 'bg-red-50' },
  };

  const appProgressSteps = [
    { key: 'app_created',            label: 'App Creada',                icon: Plus },
    { key: 'org_linked',             label: 'Organización Vinculada',    icon: Building2 },
    { key: 'agreements_signed',      label: 'Acuerdos Firmados',         icon: FileSignature },
    { key: 'sandbox_access',         label: 'Acceso Sandbox',            icon: Shield },
    { key: 'verification_requested', label: 'Verificación Solicitada',   icon: Send },
    { key: 'verified',               label: 'Verificado',                icon: Rocket },
  ];

  function getAppStatusLabel(status: string): string {
    const labels: Record<string, string> = {
      created: 'Creada',
      org_linked: 'Org. Vinculada',
      agreements_pending: 'Acuerdos Pendientes',
      sandbox_granted: 'Sandbox Activo',
      verification_requested: 'Verificación Solicitada',
      verified: 'Verificada',
      rejected: 'Rechazada',
    };
    return labels[status] || status;
  }

  function getAppModeBadge(mode: string): { label: string; class: string } {
    if (mode === 'production') return { label: 'PROD APP', class: 'bg-green-100 text-green-700 border-green-200' };
    return { label: 'TEST APP', class: 'bg-amber-100 text-amber-700 border-amber-200' };
  }
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-xl font-bold text-[#1a1a1a]">Portal de Desarrollo</h1>
      <p class="text-sm text-gray-500 mt-0.5">Gestiona tus aplicaciones y acuerdos del Developer Portal</p>
    </div>
    <button
      class="inline-flex items-center gap-2 bg-[#003B73] text-white text-sm font-semibold px-4 py-2.5 rounded-lg hover:bg-[#002a54] transition-colors"
      on:click={() => showCreateModal = true}
    >
      <Plus class="w-4 h-4" />
      Crear Aplicación
    </button>
  </div>

  <!-- Messages -->
  {#if error}
    <div class="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700 flex items-center gap-2">
      <AlertTriangle class="w-4 h-4 flex-shrink-0" />
      {error}
      <button class="ml-auto text-red-400 hover:text-red-600" on:click={() => error = ''}>✕</button>
    </div>
  {/if}
  {#if success}
    <div class="rounded-lg bg-green-50 border border-green-200 p-3 text-sm text-green-700 flex items-center gap-2">
      <CheckCircle class="w-4 h-4 flex-shrink-0" />
      {success}
    </div>
  {/if}

  {#if loading}
    <div class="flex items-center justify-center py-20">
      <Loader2 class="w-6 h-6 animate-spin text-[#003B73]" />
      <span class="ml-2 text-sm text-gray-500">Cargando aplicaciones...</span>
    </div>
  {:else if selectedFlow}
    <!-- ═══════════════════════════════════════ -->
    <!--  AGREEMENT VIEW + SIGNING              -->
    <!-- ═══════════════════════════════════════ -->
    <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            class="text-sm text-gray-500 hover:text-[#003B73]"
            on:click={() => selectedFlow = null}
          >
            ← Volver
          </button>
          <div class="h-4 w-px bg-gray-200"></div>
          <h2 class="text-base font-semibold text-[#1a1a1a]">
            {selectedFlow.template_title || 'Acuerdo'}
          </h2>
        </div>
        {#if flowStatusConfig[selectedFlow.status]}
          {@const cfg = flowStatusConfig[selectedFlow.status]}
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium {cfg.bg} {cfg.color}">
            <svelte:component this={cfg.icon} class="w-3.5 h-3.5" />
            {cfg.label}
          </span>
        {/if}
      </div>

      <div class="p-6 space-y-6">
        <!-- Document Preview -->
        <div class="border border-gray-200 rounded-lg p-6 bg-gray-50 max-h-96 overflow-y-auto prose prose-sm">
          {@html selectedFlow.html_content}
        </div>

        <!-- Signing Panel (only if viewed status) -->
        {#if selectedFlow.status === 'viewed'}
          <SignaturePanel
            documentTitle={selectedFlow.template_title || 'Acuerdo'}
            htmlPreview=""
            loading={signing}
            signed={false}
            on:sign={handleSign}
          />
        {:else if selectedFlow.status === 'in_review'}
          <div class="rounded-lg border border-purple-200 bg-purple-50 p-4 text-center">
            <FileSignature class="w-6 h-6 text-purple-500 mx-auto mb-2" />
            <p class="text-sm font-semibold text-purple-700">Firma enviada — En revisión</p>
            <p class="text-xs text-purple-500 mt-1">Un administrador revisará su firma y aprobará o rechazará el acuerdo.</p>
          </div>
        {:else if selectedFlow.status === 'signed'}
          <div class="rounded-lg border border-green-200 bg-green-50 p-4 text-center">
            <CheckCircle class="w-6 h-6 text-green-600 mx-auto mb-2" />
            <p class="text-sm font-semibold text-green-700">Acuerdo Firmado</p>
            {#if selectedFlow.signed_at}
              <p class="text-xs text-green-500 mt-1">Firmado el {new Date(selectedFlow.signed_at).toLocaleDateString('es-DO')}</p>
            {/if}
          </div>
        {:else if selectedFlow.status === 'rejected'}
          <div class="rounded-lg border border-red-200 bg-red-50 p-4 text-center">
            <XCircle class="w-6 h-6 text-red-500 mx-auto mb-2" />
            <p class="text-sm font-semibold text-red-700">Acuerdo Rechazado</p>
            {#if selectedFlow.rejection_reason}
              <p class="text-xs text-red-500 mt-1">Motivo: {selectedFlow.rejection_reason}</p>
            {/if}
          </div>
        {/if}
      </div>
    </div>

  {:else if selectedApp}
    <!-- ═══════════════════════════════════════ -->
    <!--  APP DETAIL VIEW                       -->
    <!-- ═══════════════════════════════════════ -->
    <div class="space-y-6">
      <!-- App Header -->
      <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div class="px-6 py-4 border-b border-gray-100">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <button
                class="text-sm text-gray-500 hover:text-[#003B73]"
                on:click={() => selectedApp = null}
              >
                ← Volver
              </button>
              <div class="h-4 w-px bg-gray-200"></div>
              <h2 class="text-lg font-bold text-[#1a1a1a]">{selectedApp.name}</h2>
              <span class="px-2 py-0.5 rounded text-xs font-semibold border {getAppModeBadge(selectedApp.app_mode).class}">{getAppModeBadge(selectedApp.app_mode).label}</span>
            </div>
            <div class="text-right text-xs text-gray-400">
              <p>API Suite: <span class="font-semibold text-gray-600">{selectedApp.api_suite}</span></p>
              {#if selectedApp.created_at}
                <p>Creada: {new Date(selectedApp.created_at).toLocaleDateString('es-DO')}</p>
              {/if}
            </div>
          </div>
        </div>

        <!-- Progress Timeline -->
        <div class="px-6 py-5">
          <div class="flex items-center justify-between">
            {#each appProgressSteps as step, i}
              {@const done = selectedApp.progress[step.key as keyof typeof selectedApp.progress]}
              <div class="flex flex-col items-center relative">
                <div class="w-10 h-10 rounded-full flex items-center justify-center {done ? 'bg-green-500 text-white' : 'bg-gray-100 text-gray-400'} transition-colors">
                  {#if done}
                    <CheckCircle class="w-5 h-5" />
                  {:else}
                    <svelte:component this={step.icon} class="w-5 h-5" />
                  {/if}
                </div>
                <span class="text-[10px] mt-1.5 text-center max-w-[90px] {done ? 'text-green-700 font-semibold' : 'text-gray-400'}">
                  {step.label}
                </span>
              </div>
              {#if i < appProgressSteps.length - 1}
                <div class="flex-1 h-0.5 mx-1 mt-[-16px] {done && selectedApp.progress[appProgressSteps[i+1].key as keyof typeof selectedApp.progress] ? 'bg-green-500' : (done ? 'bg-green-300' : 'bg-gray-200')}"></div>
              {/if}
            {/each}
          </div>
        </div>
      </div>

      <!-- Link Organization (if not linked yet) -->
      {#if !selectedApp.organization_linked}
        <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div class="flex items-start gap-4">
            <div class="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center text-blue-500">
              <Building2 class="w-5 h-5" />
            </div>
            <div class="flex-1">
              <h3 class="text-sm font-semibold text-[#1a1a1a]">Vincular Organización</h3>
              <p class="text-xs text-gray-500 mt-1">
                Vincula tu organización a esta app para iniciar el proceso de acuerdos legales.
              </p>
              <button
                class="mt-3 inline-flex items-center gap-1.5 bg-[#003B73] text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-[#002a54]"
                on:click={() => showLinkOrgModal = true}
              >
                <Building2 class="w-3.5 h-3.5" />
                Vincular Organización
              </button>
            </div>
          </div>
        </div>
      {/if}

      <!-- Agreements Section -->
      {#if selectedApp.agreements.length > 0}
        <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
          <div class="px-6 py-4 border-b border-gray-100">
            <h3 class="text-sm font-semibold text-[#1a1a1a]">Acuerdos Legales</h3>
            <p class="text-xs text-gray-500">
              {selectedApp.agreements_signed} de {selectedApp.agreements_total} firmados
            </p>
          </div>
          <div class="divide-y divide-gray-100">
            {#each selectedApp.agreements as agreement}
              {@const cfg = flowStatusConfig[agreement.status]}
              <div class="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
                <div class="flex items-center gap-4">
                  <!-- Status icon with line -->
                  <div class="flex flex-col items-center">
                    <div class="w-8 h-8 rounded-full flex items-center justify-center {cfg.bg} {cfg.color}">
                      <svelte:component this={cfg.icon} class="w-4 h-4" />
                    </div>
                  </div>
                  <div>
                    <div class="flex items-center gap-2">
                      <span class="text-sm font-medium text-[#1a1a1a]">
                        {agreement.template_title || 'Acuerdo'}
                      </span>
                      <span class="px-1.5 py-0.5 rounded text-[10px] font-medium {cfg.bg} {cfg.color}">
                        {cfg.label}
                      </span>
                    </div>
                    {#if agreement.status === 'signed' && agreement.signed_at}
                      <p class="text-xs text-gray-400 mt-0.5">
                        Firmado el {new Date(agreement.signed_at).toLocaleDateString('es-DO')}
                      </p>
                    {:else if agreement.status === 'rejected' && agreement.rejection_reason}
                      <p class="text-xs text-red-400 mt-0.5">
                        {agreement.rejection_reason}
                      </p>
                    {:else if agreement.status === 'viewed'}
                      <p class="text-xs text-blue-400 mt-0.5">
                        Listo para firmar. Haga clic para ver y firmar.
                      </p>
                    {:else if agreement.status === 'pending'}
                      <p class="text-xs text-amber-400 mt-0.5">
                        Haga clic para ver el acuerdo.
                      </p>
                    {/if}
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  {#if agreement.status === 'pending' || agreement.status === 'viewed'}
                    <button
                      class="inline-flex items-center gap-1 text-xs font-medium text-[#003B73] bg-[#003B73]/10 px-3 py-1.5 rounded-lg hover:bg-[#003B73]/20"
                      on:click={() => viewAgreement(agreement)}
                    >
                      {agreement.status === 'viewed' ? 'Ver y Firmar' : 'Ver Acuerdo'}
                      <ChevronRight class="w-3.5 h-3.5" />
                    </button>
                  {:else if agreement.status === 'in_review'}
                    <!-- Admin review buttons -->
                    <button
                      class="inline-flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 px-3 py-1.5 rounded-lg hover:bg-green-100"
                      on:click={() => reviewFlow(agreement.id, 'approve')}
                      disabled={reviewing}
                    >
                      <CheckCircle class="w-3.5 h-3.5" />
                      Aprobar
                    </button>
                    <button
                      class="inline-flex items-center gap-1 text-xs font-medium text-red-700 bg-red-50 px-3 py-1.5 rounded-lg hover:bg-red-100"
                      on:click={() => {
                        rejectReason = prompt('Motivo de rechazo:') || '';
                        if (rejectReason) reviewFlow(agreement.id, 'reject');
                      }}
                      disabled={reviewing}
                    >
                      <XCircle class="w-3.5 h-3.5" />
                      Rechazar
                    </button>
                  {:else if agreement.status === 'signed' || agreement.status === 'generated'}
                    <button
                      class="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600"
                      on:click={() => viewAgreement(agreement)}
                    >
                      <Eye class="w-3.5 h-3.5" />
                      Ver
                    </button>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Sandbox & Production Actions -->
      {#if selectedApp.sandbox_access && selectedApp.status === 'sandbox_granted'}
        <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div class="flex items-start gap-4">
            <div class="w-10 h-10 rounded-full bg-green-50 flex items-center justify-center text-green-600">
              <Shield class="w-5 h-5" />
            </div>
            <div class="flex-1">
              <h3 class="text-sm font-semibold text-[#1a1a1a]">Acceso Sandbox Concedido</h3>
              <p class="text-xs text-gray-500 mt-1">
                Ya puedes desarrollar y probar tu integración en el entorno sandbox.
                Cuando estés listo, solicita acceso a producción.
              </p>
              <button
                class="mt-3 inline-flex items-center gap-1.5 bg-[#003B73] text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-[#002a54]"
                on:click={requestProduction}
              >
                <Rocket class="w-3.5 h-3.5" />
                Solicitar Producción
              </button>
            </div>
          </div>
        </div>
      {:else if selectedApp.status === 'verification_requested'}
        <div class="bg-white rounded-xl border border-amber-200 shadow-sm p-6">
          <div class="flex items-start gap-4">
            <div class="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center text-amber-500">
              <Clock class="w-5 h-5" />
            </div>
            <div class="flex-1">
              <h3 class="text-sm font-semibold text-[#1a1a1a]">Verificación en Proceso</h3>
              <p class="text-xs text-gray-500 mt-1">
                Tu solicitud de producción está siendo revisada por el equipo de Sajet.
              </p>
            </div>
          </div>
        </div>
      {:else if selectedApp.status === 'verified'}
        <div class="bg-white rounded-xl border border-green-200 shadow-sm p-6">
          <div class="flex items-start gap-4">
            <div class="w-10 h-10 rounded-full bg-green-50 flex items-center justify-center text-green-600">
              <Rocket class="w-5 h-5" />
            </div>
            <div class="flex-1">
              <h3 class="text-sm font-semibold text-green-700">¡App Verificada para Producción!</h3>
              <p class="text-xs text-gray-500 mt-1">
                Tu aplicación está lista para funcionar en producción.
              </p>
            </div>
          </div>
        </div>
      {/if}
    </div>

  {:else}
    <!-- ═══════════════════════════════════════ -->
    <!--  APPS LIST                             -->
    <!-- ═══════════════════════════════════════ -->
    {#if apps.length === 0}
      <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-12 text-center">
        <div class="w-16 h-16 bg-[#003B73]/10 rounded-full flex items-center justify-center mx-auto mb-4">
          <FileText class="w-8 h-8 text-[#003B73]" />
        </div>
        <h3 class="text-base font-semibold text-[#1a1a1a]">No tienes aplicaciones</h3>
        <p class="text-sm text-gray-500 mt-1 max-w-md mx-auto">
          Crea tu primera aplicación en el Developer Portal para comenzar a integrar con las APIs de Sajet.
        </p>
        <button
          class="mt-4 inline-flex items-center gap-2 bg-[#003B73] text-white text-sm font-semibold px-4 py-2.5 rounded-lg hover:bg-[#002a54]"
          on:click={() => showCreateModal = true}
        >
          <Plus class="w-4 h-4" />
          Crear Primera Aplicación
        </button>
      </div>
    {:else}
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {#each apps as app}
          {@const badge = getAppModeBadge(app.app_mode)}
          <button
            class="bg-white rounded-xl border border-gray-200 shadow-sm p-5 text-left hover:border-[#003B73]/30 hover:shadow-md transition-all group"
            on:click={() => { selectedApp = app; }}
          >
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-lg bg-[#003B73]/10 flex items-center justify-center text-[#003B73]">
                  <FileText class="w-4 h-4" />
                </div>
                <div>
                  <h3 class="text-sm font-semibold text-[#1a1a1a] group-hover:text-[#003B73]">{app.name}</h3>
                </div>
              </div>
              <span class="px-1.5 py-0.5 rounded text-[10px] font-semibold border {badge.class}">{badge.label}</span>
            </div>

            <!-- Mini progress bar -->
            <div class="flex items-center gap-1 mb-3">
              {#each appProgressSteps as step}
                {@const done = app.progress[step.key as keyof typeof app.progress]}
                <div class="flex-1 h-1 rounded-full {done ? 'bg-green-500' : 'bg-gray-200'}"></div>
              {/each}
            </div>

            <div class="flex items-center justify-between text-xs text-gray-500">
              <span>{getAppStatusLabel(app.status)}</span>
              <span>{app.api_suite}</span>
            </div>

            {#if app.agreements_total > 0}
              <div class="mt-2 text-[10px] text-gray-400">
                Acuerdos: {app.agreements_signed}/{app.agreements_total}
              </div>
            {/if}
          </button>
        {/each}
      </div>
    {/if}
  {/if}
</div>

<!-- ═══════════════════════════════════════ -->
<!--  CREATE APP MODAL                     -->
<!-- ═══════════════════════════════════════ -->
{#if showCreateModal}
  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
  <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" role="dialog" tabindex="-1" on:click={() => showCreateModal = false} on:keydown={(e) => e.key === 'Escape' && (showCreateModal = false)}>
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="bg-white rounded-xl shadow-xl max-w-md w-full" role="presentation" on:click|stopPropagation on:keydown|stopPropagation>
      <div class="px-6 py-4 border-b border-gray-100">
        <h3 class="text-base font-semibold text-[#1a1a1a]">Crear Aplicación</h3>
      </div>
      <div class="p-6 space-y-4">
        <div>
          <label for="app-name" class="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1">
            Nombre de la Aplicación
          </label>
          <input
            id="app-name"
            type="text"
            bind:value={newAppName}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#003B73] focus:border-transparent outline-none"
            placeholder="Ej: Sajet Delivery"
            disabled={creating}
          />
        </div>
        <div>
          <label for="app-desc" class="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1">
            Descripción
          </label>
          <textarea
            id="app-desc"
            bind:value={newAppDescription}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#003B73] focus:border-transparent outline-none"
            placeholder="Describe tu aplicación..."
            rows="2"
            disabled={creating}
          ></textarea>
        </div>
        <div>
          <label for="app-suite" class="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1">
            API Suite
          </label>
          <select
            id="app-suite"
            bind:value={newAppApiSuite}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#003B73] focus:border-transparent outline-none bg-white"
            disabled={creating}
          >
            <option value="eats_marketplace">Eats Marketplace</option>
            <option value="delivery_api">Delivery API</option>
            <option value="erp_integration">ERP Integration</option>
            <option value="partner_api">Partner API</option>
          </select>
        </div>
      </div>
      <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
        <button
          class="text-sm text-gray-500 hover:text-gray-700 px-4 py-2"
          on:click={() => showCreateModal = false}
          disabled={creating}
        >
          Cancelar
        </button>
        <button
          class="inline-flex items-center gap-2 bg-[#003B73] text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-[#002a54] disabled:opacity-60"
          on:click={createApp}
          disabled={!newAppName.trim() || creating}
        >
          {#if creating}
            <Loader2 class="w-4 h-4 animate-spin" />
          {/if}
          Crear
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- ═══════════════════════════════════════ -->
<!--  LINK ORGANIZATION MODAL              -->
<!-- ═══════════════════════════════════════ -->
{#if showLinkOrgModal}
  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
  <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" role="dialog" tabindex="-1" on:click={() => showLinkOrgModal = false} on:keydown={(e) => e.key === 'Escape' && (showLinkOrgModal = false)}>
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="bg-white rounded-xl shadow-xl max-w-md w-full" role="presentation" on:click|stopPropagation on:keydown|stopPropagation>
      <div class="px-6 py-4 border-b border-gray-100">
        <h3 class="text-base font-semibold text-[#1a1a1a]">Vincular Organización</h3>
      </div>
      <div class="p-6">
        <label for="org-name" class="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1">
          Nombre de la Organización
        </label>
        <input
          id="org-name"
          type="text"
          bind:value={orgName}
          class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#003B73] focus:border-transparent outline-none"
          placeholder="Ej: Jeturing SRL"
          disabled={linking}
        />
        <p class="text-xs text-gray-400 mt-2">
          Al vincular tu organización, se generarán los acuerdos legales requeridos para usar las APIs.
        </p>
      </div>
      <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
        <button
          class="text-sm text-gray-500 hover:text-gray-700 px-4 py-2"
          on:click={() => showLinkOrgModal = false}
          disabled={linking}
        >
          Cancelar
        </button>
        <button
          class="inline-flex items-center gap-2 bg-[#003B73] text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-[#002a54] disabled:opacity-60"
          on:click={linkOrganization}
          disabled={!orgName.trim() || linking}
        >
          {#if linking}
            <Loader2 class="w-4 h-4 animate-spin" />
          {/if}
          Vincular
        </button>
      </div>
    </div>
  </div>
{/if}
