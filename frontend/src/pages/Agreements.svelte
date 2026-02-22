<script lang="ts">
  import { onMount } from 'svelte';
  import { FileText, Plus, Edit, Trash2, Download, Eye, Save, X, ChevronDown } from 'lucide-svelte';
  import { agreementsApi } from '../lib/api';
  import { toasts } from '../lib/stores';
  import type { AgreementTemplate, SignedAgreement } from '../lib/types';

  let templates: AgreementTemplate[] = [];
  let signedAgreements: SignedAgreement[] = [];
  let loading = $state(true);
  let activeTab = $state<'templates' | 'signed'>('templates');

  // ── Filters ──
  let filterType = $state('');
  let filterTarget = $state('');

  // ── Template editor ──
  let editing = $state(false);
  let editingTemplate = $state<Partial<AgreementTemplate> | null>(null);
  let previewing = $state(false);
  let saving = $state(false);

  const typeLabels: Record<string, string> = {
    nda: 'NDA',
    service_agreement: 'Acuerdo de Servicio',
    terms_of_service: 'Términos de Servicio',
    privacy_policy: 'Política de Privacidad',
  };

  const targetLabels: Record<string, string> = {
    partner: 'Partner',
    customer: 'Cliente',
    both: 'Ambos',
  };

  async function loadTemplates() {
    loading = true;
    try {
      const params: Record<string, any> = {};
      if (filterType) params.agreement_type = filterType;
      if (filterTarget) params.target = filterTarget;
      const res = await agreementsApi.listTemplates(params);
      templates = res.items;
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error cargando plantillas');
    } finally {
      loading = false;
    }
  }

  async function loadSigned() {
    loading = true;
    try {
      const res = await agreementsApi.listSigned();
      signedAgreements = res.items;
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error cargando acuerdos firmados');
    } finally {
      loading = false;
    }
  }

  function openCreate() {
    editingTemplate = {
      agreement_type: 'nda',
      target: 'partner',
      title: '',
      version: '1.0',
      html_content: '<h1>Título del Acuerdo</h1>\n<p>Contenido del acuerdo...</p>\n<p>Firmante: {{signer_name}}</p>\n<p>Fecha: {{date}}</p>',
      is_active: true,
      is_required: true,
    };
    editing = true;
    previewing = false;
  }

  function openEdit(t: AgreementTemplate) {
    editingTemplate = { ...t };
    editing = true;
    previewing = false;
  }

  function cancelEdit() {
    editing = false;
    editingTemplate = null;
    previewing = false;
  }

  async function saveTemplate() {
    if (!editingTemplate) return;
    saving = true;
    try {
      if (editingTemplate.id) {
        await agreementsApi.updateTemplate(editingTemplate.id, editingTemplate);
        toasts.success('Plantilla actualizada');
      } else {
        await agreementsApi.createTemplate(editingTemplate);
        toasts.success('Plantilla creada');
      }
      cancelEdit();
      await loadTemplates();
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error guardando');
    } finally {
      saving = false;
    }
  }

  async function deleteTemplate(id: number) {
    if (!confirm('¿Eliminar esta plantilla?')) return;
    try {
      await agreementsApi.deleteTemplate(id);
      toasts.success('Plantilla eliminada');
      await loadTemplates();
    } catch (err) {
      toasts.error(err instanceof Error ? err.message : 'Error eliminando');
    }
  }

  function switchTab(tab: 'templates' | 'signed') {
    activeTab = tab;
    if (tab === 'templates') loadTemplates();
    else loadSigned();
  }

  onMount(() => {
    loadTemplates();
  });
</script>

<div class="p-6 space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="page-title flex items-center gap-2">
        <FileText class="w-6 h-6 text-terracotta" />
        Acuerdos y Contratos
      </h1>
      <p class="page-subtitle">Gestiona plantillas de NDA, TOS y acuerdos de servicio</p>
    </div>
    {#if activeTab === 'templates' && !editing}
      <button class="btn-primary flex items-center gap-2 text-sm" onclick={openCreate}>
        <Plus class="w-4 h-4" />
        Nueva Plantilla
      </button>
    {/if}
  </div>

  <!-- Tabs -->
  <div class="flex gap-1 border-b border-gray-200">
    <button
      class="px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px {activeTab === 'templates' ? 'border-terracotta text-terracotta' : 'border-transparent text-gray-500 hover:text-gray-700'}"
      onclick={() => switchTab('templates')}
    >
      Plantillas
    </button>
    <button
      class="px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px {activeTab === 'signed' ? 'border-terracotta text-terracotta' : 'border-transparent text-gray-500 hover:text-gray-700'}"
      onclick={() => switchTab('signed')}
    >
      Firmados
    </button>
  </div>

  {#if editing && editingTemplate}
    <!-- Template Editor -->
    <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
        <h2 class="font-semibold text-text-primary">
          {editingTemplate.id ? 'Editar Plantilla' : 'Nueva Plantilla'}
        </h2>
        <div class="flex gap-2">
          <button
            class="btn-secondary text-sm flex items-center gap-1.5"
            onclick={() => previewing = !previewing}
          >
            <Eye class="w-4 h-4" />
            {previewing ? 'Editar' : 'Vista Previa'}
          </button>
          <button class="btn-secondary text-sm flex items-center gap-1.5" onclick={cancelEdit}>
            <X class="w-4 h-4" /> Cancelar
          </button>
          <button
            class="btn-primary text-sm flex items-center gap-1.5"
            onclick={saveTemplate}
            disabled={saving}
          >
            <Save class="w-4 h-4" />
            {saving ? 'Guardando...' : 'Guardar'}
          </button>
        </div>
      </div>
      <div class="p-6 space-y-4">
        <!-- Meta fields -->
        <div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div>
            <label class="label">Título</label>
            <input
              type="text"
              class="input w-full px-3 py-2"
              bind:value={editingTemplate.title}
            />
          </div>
          <div>
            <label class="label">Tipo</label>
            <select class="input w-full px-3 py-2" bind:value={editingTemplate.agreement_type}>
              <option value="nda">NDA</option>
              <option value="service_agreement">Acuerdo de Servicio</option>
              <option value="terms_of_service">Términos de Servicio</option>
              <option value="privacy_policy">Política de Privacidad</option>
            </select>
          </div>
          <div>
            <label class="label">Destinatario</label>
            <select class="input w-full px-3 py-2" bind:value={editingTemplate.target}>
              <option value="partner">Partner</option>
              <option value="customer">Cliente</option>
              <option value="both">Ambos</option>
            </select>
          </div>
          <div>
            <label class="label">Versión</label>
            <input
              type="text"
              class="input w-full px-3 py-2"
              bind:value={editingTemplate.version}
            />
          </div>
        </div>
        <div class="flex gap-4">
          <label class="flex items-center gap-2 text-sm">
            <input type="checkbox" bind:checked={editingTemplate.is_active} class="rounded" />
            Activa
          </label>
          <label class="flex items-center gap-2 text-sm">
            <input type="checkbox" bind:checked={editingTemplate.is_required} class="rounded" />
            Obligatoria
          </label>
        </div>

        <!-- HTML Content / Preview -->
        {#if previewing}
          <div>
            <label class="label mb-2">Vista previa del documento</label>
            <div class="border border-gray-200 rounded-lg p-6 bg-white prose prose-sm max-w-none min-h-[400px]">
              {@html (editingTemplate.html_content || '')
                .replace(/\{\{signer_name\}\}/g, '<strong>[Nombre del firmante]</strong>')
                .replace(/\{\{date\}\}/g, new Date().toLocaleDateString('es-ES'))
                .replace(/\{\{company_name\}\}/g, '<strong>[Empresa]</strong>')
                .replace(/\{\{email\}\}/g, '<strong>[email@ejemplo.com]</strong>')}
            </div>
          </div>
        {:else}
          <div>
            <label class="label mb-2">
              Contenido HTML
              <span class="text-gray-400 font-normal text-xs ml-2">
                Variables: {'{{signer_name}}'}, {'{{date}}'}, {'{{company_name}}'}, {'{{email}}'}
              </span>
            </label>
            <textarea
              class="input w-full px-3 py-2 font-mono text-xs"
              rows="20"
              bind:value={editingTemplate.html_content}
            ></textarea>
          </div>
        {/if}
      </div>
    </div>
  {:else if activeTab === 'templates'}
    <!-- Filters -->
    <div class="flex gap-3 flex-wrap">
      <select class="input px-3 py-2 text-sm" bind:value={filterType} onchange={loadTemplates}>
        <option value="">Todos los tipos</option>
        <option value="nda">NDA</option>
        <option value="service_agreement">Acuerdo de Servicio</option>
        <option value="terms_of_service">Términos de Servicio</option>
        <option value="privacy_policy">Política de Privacidad</option>
      </select>
      <select class="input px-3 py-2 text-sm" bind:value={filterTarget} onchange={loadTemplates}>
        <option value="">Todos los destinatarios</option>
        <option value="partner">Partner</option>
        <option value="customer">Cliente</option>
        <option value="both">Ambos</option>
      </select>
    </div>

    <!-- Templates Table -->
    <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {#if loading}
        <div class="p-8 text-center text-gray-400">Cargando...</div>
      {:else if templates.length === 0}
        <div class="p-8 text-center text-gray-400">No hay plantillas registradas</div>
      {:else}
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50/50">
              <th class="text-left px-4 py-3 font-semibold text-gray-600">Título</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-600">Tipo</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-600">Destinatario</th>
              <th class="text-center px-4 py-3 font-semibold text-gray-600">Versión</th>
              <th class="text-center px-4 py-3 font-semibold text-gray-600">Estado</th>
              <th class="text-center px-4 py-3 font-semibold text-gray-600">Obligatoria</th>
              <th class="text-right px-4 py-3 font-semibold text-gray-600">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {#each templates as t}
              <tr class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                <td class="px-4 py-3 font-medium text-text-primary">{t.title}</td>
                <td class="px-4 py-3">
                  <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700">
                    {typeLabels[t.agreement_type] || t.agreement_type}
                  </span>
                </td>
                <td class="px-4 py-3 text-gray-600">{targetLabels[t.target] || t.target}</td>
                <td class="px-4 py-3 text-center text-gray-500">{t.version}</td>
                <td class="px-4 py-3 text-center">
                  <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium {t.is_active ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'}">
                    {t.is_active ? 'Activa' : 'Inactiva'}
                  </span>
                </td>
                <td class="px-4 py-3 text-center text-gray-500">{t.is_required ? 'Sí' : 'No'}</td>
                <td class="px-4 py-3 text-right">
                  <div class="flex items-center justify-end gap-1">
                    <button
                      class="p-1.5 text-gray-400 hover:text-terracotta rounded transition-colors"
                      onclick={() => openEdit(t)}
                      title="Editar"
                    >
                      <Edit class="w-4 h-4" />
                    </button>
                    <button
                      class="p-1.5 text-gray-400 hover:text-red-600 rounded transition-colors"
                      onclick={() => deleteTemplate(t.id)}
                      title="Eliminar"
                    >
                      <Trash2 class="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
    </div>
  {:else}
    <!-- Signed Agreements Table -->
    <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {#if loading}
        <div class="p-8 text-center text-gray-400">Cargando...</div>
      {:else if signedAgreements.length === 0}
        <div class="p-8 text-center text-gray-400">No hay acuerdos firmados</div>
      {:else}
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50/50">
              <th class="text-left px-4 py-3 font-semibold text-gray-600">Acuerdo</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-600">Tipo</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-600">Firmante</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-600">Fecha</th>
              <th class="text-center px-4 py-3 font-semibold text-gray-600">Hash</th>
              <th class="text-right px-4 py-3 font-semibold text-gray-600">PDF</th>
            </tr>
          </thead>
          <tbody>
            {#each signedAgreements as s}
              <tr class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                <td class="px-4 py-3 font-medium text-text-primary">{s.template_title || `#${s.template_id}`}</td>
                <td class="px-4 py-3">
                  <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700">
                    {typeLabels[s.template_type || ''] || s.template_type || '—'}
                  </span>
                </td>
                <td class="px-4 py-3 text-gray-600">{s.signer_name}</td>
                <td class="px-4 py-3 text-gray-500">
                  {s.signed_at ? new Date(s.signed_at).toLocaleDateString('es-ES') : '—'}
                </td>
                <td class="px-4 py-3 text-center">
                  <code class="text-[10px] text-gray-400 font-mono">{s.document_hash?.substring(0, 12)}…</code>
                </td>
                <td class="px-4 py-3 text-right">
                  {#if s.pdf_path}
                    <a
                      href={agreementsApi.getPdfUrl(s.id)}
                      target="_blank"
                      rel="noreferrer"
                      class="inline-flex items-center gap-1 text-terracotta hover:underline text-xs"
                    >
                      <Download class="w-3.5 h-3.5" />
                      PDF
                    </a>
                  {:else}
                    <span class="text-gray-300 text-xs">—</span>
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
    </div>
  {/if}
</div>
