<script lang="ts">
  import { onMount } from 'svelte';
  import { FileText, Plus, Edit3, Trash2, Code, Check, X } from 'lucide-svelte';
  import { api } from '../lib/api/client';

  interface LandingSection {
    id: number;
    section_key: string;
    locale: string;
    title: string;
    content: string;
    meta_description: string;
    meta_keywords: string;
    og_title: string;
    og_description: string;
    og_image_url: string;
    structured_data: Record<string, any>;
    created_at: string;
    updated_at: string;
  }

  let sections: LandingSection[] = $state([]);
  let loading = $state(true);
  let error = $state('');

  // Modal state
  let showModal = $state(false);
  let editingId: number | null = $state(null);
  let saving = $state(false);
  let selectedLocale = $state('en');
  let expandedSections: Set<number> = $state(new Set());

  // Form
  let form = $state({
    section_key: '',
    locale: 'en',
    title: '',
    content: '',
    meta_description: '',
    meta_keywords: '',
    og_title: '',
    og_description: '',
    og_image_url: '',
    structured_data: '{}',
  });

  async function loadSections() {
    loading = true;
    error = '';
    try {
      const data = await api.get<{ items: LandingSection[]; total: number }>(
        `/api/admin/landing-sections?locale=${selectedLocale}`
      );
      sections = data.items ?? [];
    } catch (e: any) {
      error = e.message || 'Error cargando secciones';
      console.error(e);
    } finally {
      loading = false;
    }
  }

  function openCreate() {
    editingId = null;
    form = {
      section_key: '',
      locale: selectedLocale,
      title: '',
      content: '',
      meta_description: '',
      meta_keywords: '',
      og_title: '',
      og_description: '',
      og_image_url: '',
      structured_data: '{}',
    };
    showModal = true;
  }

  function openEdit(section: LandingSection) {
    editingId = section.id;
    form = {
      section_key: section.section_key,
      locale: section.locale,
      title: section.title,
      content: section.content,
      meta_description: section.meta_description || '',
      meta_keywords: section.meta_keywords || '',
      og_title: section.og_title || '',
      og_description: section.og_description || '',
      og_image_url: section.og_image_url || '',
      structured_data: JSON.stringify(section.structured_data || {}, null, 2),
    };
    showModal = true;
  }

  async function saveSection() {
    if (!form.section_key.trim() || !form.title.trim()) {
      alert('Section Key y Title son requeridos');
      return;
    }

    saving = true;
    try {
      const payload = {
        ...form,
        structured_data: form.structured_data ? JSON.parse(form.structured_data) : {},
      };

      if (editingId) {
        await api.put(`/api/admin/landing-sections/${editingId}`, payload);
      } else {
        await api.post('/api/admin/landing-sections', payload);
      }
      showModal = false;
      await loadSections();
    } catch (e: any) {
      alert(e.message || 'Error guardando sección');
    } finally {
      saving = false;
    }
  }

  async function deleteSection(id: number) {
    if (!confirm('¿Eliminar esta sección? (esto afectará a la página)')) return;
    try {
      await api.delete(`/api/admin/landing-sections/${id}`);
      await loadSections();
    } catch (e: any) {
      alert(e.message || 'Error eliminando sección');
    }
  }

  function toggleExpanded(id: number) {
    if (expandedSections.has(id)) {
      expandedSections.delete(id);
    } else {
      expandedSections.add(id);
    }
    expandedSections = expandedSections;
  }

  onMount(() => {
    loadSections();
  });

  $effect(() => {
    selectedLocale;
    loadSections();
  });
</script>

<div class="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8">
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <FileText class="w-8 h-8 text-blue-600" />
          <h1 class="text-3xl font-bold text-gray-900">Secciones Landing</h1>
        </div>
        <button
          onclick={() => openCreate()}
          class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          <Plus class="w-5 h-5" />
          Nueva Sección
        </button>
      </div>

      <!-- Filters -->
      <div class="flex items-center gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Idioma</label>
          <select
            bind:value={selectedLocale}
            class="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="en">English (en)</option>
            <option value="es">Español (es)</option>
          </select>
        </div>
        <div class="text-sm text-gray-600 mt-6">
          {sections.length} secciones
        </div>
      </div>
    </div>

    <!-- Error -->
    {#if error}
      <div class="mb-6 p-4 bg-red-50 text-red-700 rounded-lg">
        {error}
      </div>
    {/if}

    <!-- Loading -->
    {#if loading}
      <div class="text-center py-12">
        <div class="inline-block">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    {:else if sections.length === 0}
      <div class="text-center py-12">
        <FileText class="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p class="text-gray-600">No hay secciones para este idioma</p>
      </div>
    {:else}
      <!-- Cards -->
      <div class="grid gap-4">
        {#each sections as section (section.id)}
          <div class="bg-white rounded-lg shadow hover:shadow-md transition">
            <div class="p-6">
              <div class="flex items-start justify-between mb-4">
                <div>
                  <div class="inline-block px-2 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded mb-2">
                    {section.section_key}
                  </div>
                  <h3 class="text-lg font-bold text-gray-900">{section.title}</h3>
                  <p class="text-sm text-gray-600 mt-1">
                    Actualizado: {new Date(section.updated_at).toLocaleDateString('es-ES')}
                  </p>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    onclick={() => openEdit(section)}
                    class="p-2 hover:bg-blue-100 text-blue-600 rounded transition"
                    title="Editar"
                  >
                    <Edit3 class="w-4 h-4" />
                  </button>
                  <button
                    onclick={() => deleteSection(section.id)}
                    class="p-2 hover:bg-red-100 text-red-600 rounded transition"
                    title="Eliminar"
                  >
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              </div>

              {#if expandedSections.has(section.id)}
                <div class="space-y-4 pt-4 border-t border-gray-200">
                  <div>
                    <h4 class="text-sm font-semibold text-gray-700 mb-2">Contenido</h4>
                    <p class="text-sm text-gray-600 whitespace-pre-wrap">{section.content}</p>
                  </div>

                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <h4 class="text-sm font-semibold text-gray-700 mb-2">Meta Description</h4>
                      <p class="text-xs text-gray-600">{section.meta_description || '—'}</p>
                    </div>
                    <div>
                      <h4 class="text-sm font-semibold text-gray-700 mb-2">Meta Keywords</h4>
                      <p class="text-xs text-gray-600">{section.meta_keywords || '—'}</p>
                    </div>
                  </div>

                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <h4 class="text-sm font-semibold text-gray-700 mb-2">OG Title</h4>
                      <p class="text-xs text-gray-600">{section.og_title || '—'}</p>
                    </div>
                    <div>
                      <h4 class="text-sm font-semibold text-gray-700 mb-2">OG Description</h4>
                      <p class="text-xs text-gray-600">{section.og_description || '—'}</p>
                    </div>
                  </div>

                  {#if section.og_image_url}
                    <div>
                      <h4 class="text-sm font-semibold text-gray-700 mb-2">OG Image</h4>
                      <img
                        src={section.og_image_url}
                        alt="OG"
                        class="max-h-32 rounded border border-gray-200"
                      />
                    </div>
                  {/if}

                  {#if Object.keys(section.structured_data || {}).length > 0}
                    <div>
                      <h4 class="text-sm font-semibold text-gray-700 mb-2">Schema.org JSON-LD</h4>
                      <pre class="text-xs bg-gray-50 p-2 rounded border border-gray-200 overflow-auto max-h-32"
                        >{JSON.stringify(section.structured_data, null, 2)}</pre>
                    </div>
                  {/if}
                </div>
              {/if}

              <button
                onclick={() => toggleExpanded(section.id)}
                class="text-sm text-blue-600 hover:text-blue-700 mt-4"
              >
                {expandedSections.has(section.id) ? 'Ocultar detalles' : 'Ver detalles'}
              </button>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Modal -->
  {#if showModal}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div class="bg-white rounded-lg shadow-xl max-w-3xl w-full my-8">
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 class="text-xl font-bold text-gray-900">
            {editingId ? 'Editar Sección' : 'Nueva Sección'}
          </h2>
          <button
            onclick={() => {
              showModal = false;
            }}
            class="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>

        <div class="p-6 space-y-4 max-h-[calc(90vh-200px)] overflow-y-auto">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Section Key *</label>
              <input
                type="text"
                bind:value={form.section_key}
                placeholder="hero, features, pricing..."
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Idioma</label>
              <select
                bind:value={form.locale}
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="en">English (en)</option>
                <option value="es">Español (es)</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Título *</label>
            <input
              type="text"
              bind:value={form.title}
              placeholder="Título de la sección"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Contenido</label>
            <textarea
              bind:value={form.content}
              placeholder="Contenido HTML o texto"
              rows="6"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Meta Description (SEO)</label>
            <textarea
              bind:value={form.meta_description}
              rows="2"
              maxlength="160"
              placeholder="Descripción para buscadores (máx 160 caracteres)"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            ></textarea>
            <p class="text-xs text-gray-500 mt-1">{form.meta_description.length}/160</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Meta Keywords (SEO)</label>
            <input
              type="text"
              bind:value={form.meta_keywords}
              placeholder="palabra1, palabra2, palabra3"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>

          <div class="border-t border-gray-200 pt-4">
            <h3 class="font-semibold text-gray-900 mb-3">Open Graph (Redes Sociales)</h3>
            <div class="space-y-3">
              <input
                type="text"
                bind:value={form.og_title}
                placeholder="OG Title"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
              <textarea
                bind:value={form.og_description}
                placeholder="OG Description"
                rows="2"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              ></textarea>
              <input
                type="url"
                bind:value={form.og_image_url}
                placeholder="OG Image URL"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
            </div>
          </div>

          <div class="border-t border-gray-200 pt-4">
            <h3 class="font-semibold text-gray-900 mb-3">Structured Data (Schema.org JSON-LD)</h3>
            <textarea
              bind:value={form.structured_data}
              placeholder={'{}'}
              rows="6"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
            ></textarea>
          </div>
        </div>

        <div class="border-t border-gray-200 px-6 py-4 flex justify-end gap-2 sticky bottom-0 bg-white">
          <button
            onclick={() => {
              showModal = false;
            }}
            class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            Cancelar
          </button>
          <button
            onclick={() => saveSection()}
            disabled={saving}
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {saving ? 'Guardando...' : 'Guardar'}
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>
