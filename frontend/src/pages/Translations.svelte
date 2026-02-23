<script lang="ts">
  import { onMount } from 'svelte';
  import { Languages, Plus, Edit3, Trash2, Check, X, Download, Upload, Search } from 'lucide-svelte';
  import { api } from '../lib/api/client';

  interface Translation {
    id: number;
    key: string;
    locale: string;
    value: string;
    context?: string;
    is_approved: boolean;
    approved_by?: string;
    created_at: string;
    updated_at: string;
  }

  let translations: Translation[] = $state([]);
  let loading = $state(true);
  let error = $state('');

  // Modal state
  let showModal = $state(false);
  let editingId: number | null = $state(null);
  let saving = $state(false);
  let selectedLocale = $state('en');
  let selectedContext = $state('');
  let searchQuery = $state('');

  // Form
  let form = $state({
    key: '',
    locale: 'en',
    value: '',
    context: '',
    is_approved: true,
  });

  // Computed
  let filteredTranslations = $state<Translation[]>([]);

  function applyFilters() {
    filteredTranslations = translations.filter((t) => {
      const matchLocale = !selectedLocale || t.locale === selectedLocale;
      const matchContext = !selectedContext || t.context === selectedContext;
      const matchSearch =
        !searchQuery ||
        t.key.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.value.toLowerCase().includes(searchQuery.toLowerCase());
      return matchLocale && matchContext && matchSearch;
    });
  }

  async function loadTranslations() {
    loading = true;
    error = '';
    try {
      let url = '/api/admin/translations';
      const params = new URLSearchParams();
      if (selectedLocale) params.append('locale', selectedLocale);
      if (selectedContext) params.append('context', selectedContext);
      if (params.toString()) url += '?' + params.toString();

      const data = await api.get<{ items: Translation[]; total: number }>(url);
      translations = data.items ?? [];
      applyFilters();
    } catch (e: any) {
      error = e.message || 'Error cargando traducciones';
      console.error(e);
    } finally {
      loading = false;
    }
  }

  function openCreate() {
    editingId = null;
    form = {
      key: '',
      locale: selectedLocale,
      value: '',
      context: selectedContext,
      is_approved: true,
    };
    showModal = true;
  }

  function openEdit(translation: Translation) {
    editingId = translation.id;
    form = {
      key: translation.key,
      locale: translation.locale,
      value: translation.value,
      context: translation.context || '',
      is_approved: translation.is_approved,
    };
    showModal = true;
  }

  async function saveTranslation() {
    if (!form.key.trim() || !form.value.trim()) {
      alert('Key y Value son requeridos');
      return;
    }

    saving = true;
    try {
      if (editingId) {
        await api.put(`/api/admin/translations/${editingId}`, form);
      } else {
        await api.post('/api/admin/translations', form);
      }
      showModal = false;
      await loadTranslations();
    } catch (e: any) {
      alert(e.message || 'Error guardando traducción');
    } finally {
      saving = false;
    }
  }

  async function deleteTranslation(id: number) {
    if (!confirm('¿Eliminar esta traducción?')) return;
    try {
      await api.delete(`/api/admin/translations/${id}`);
      await loadTranslations();
    } catch (e: any) {
      alert(e.message || 'Error eliminando traducción');
    }
  }

  async function toggleApproval(id: number, approved: boolean) {
    try {
      await api.patch(`/api/admin/translations/${id}`, { is_approved: !approved });
      await loadTranslations();
    } catch (e: any) {
      alert(e.message || 'Error actualizando aprobación');
    }
  }

  async function exportCSV() {
    const csv = [
      ['Key', 'Locale', 'Value', 'Context', 'Approved'].join(','),
      ...filteredTranslations.map((t) =>
        [t.key, t.locale, `"${t.value.replace(/"/g, '""')}"`, t.context || '', t.is_approved ? 'Yes' : 'No'].join(',')
      ),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `translations-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  }

  onMount(() => {
    loadTranslations();
  });

  $effect(() => {
    selectedLocale || selectedContext || searchQuery;
    applyFilters();
  });
</script>

<div class="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8">
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <Languages class="w-8 h-8 text-purple-600" />
          <h1 class="text-3xl font-bold text-gray-900">Traducciones Dinámicas</h1>
        </div>
        <div class="flex items-center gap-2">
          <button
            onclick={() => exportCSV()}
            class="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
          >
            <Download class="w-5 h-5" />
            Exportar CSV
          </button>
          <button
            onclick={() => openCreate()}
            class="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
          >
            <Plus class="w-5 h-5" />
            Nueva Traducción
          </button>
        </div>
      </div>

      <!-- Filters -->
      <div class="flex items-end gap-4 flex-wrap">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Idioma</label>
          <select
            bind:value={selectedLocale}
            class="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value="">Todos</option>
            <option value="en">English (en)</option>
            <option value="es">Español (es)</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Contexto</label>
          <select
            bind:value={selectedContext}
            class="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value="">Todos</option>
            <option value="landing">Landing</option>
            <option value="seo">SEO</option>
            <option value="pricing">Pricing</option>
            <option value="footer">Footer</option>
            <option value="email">Email</option>
          </select>
        </div>
        <div class="flex-1 min-w-64">
          <label class="block text-sm font-medium text-gray-700 mb-1">Búsqueda</label>
          <div class="relative">
            <Search class="absolute left-3 top-2.5 w-5 h-5 text-gray-400" />
            <input
              type="text"
              bind:value={searchQuery}
              placeholder="Buscar por key o valor..."
              class="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
        </div>
        <div class="text-sm text-gray-600">
          {filteredTranslations.length} resultados
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
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
        </div>
      </div>
    {:else if filteredTranslations.length === 0}
      <div class="text-center py-12">
        <Languages class="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p class="text-gray-600">No hay traducciones que coincidan con los filtros</p>
      </div>
    {:else}
      <!-- Table -->
      <div class="bg-white rounded-lg shadow overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50 border-b border-gray-200">
              <tr>
                <th class="px-6 py-3 text-left text-sm font-semibold text-gray-900">Key</th>
                <th class="px-6 py-3 text-left text-sm font-semibold text-gray-900">Idioma</th>
                <th class="px-6 py-3 text-left text-sm font-semibold text-gray-900">Valor</th>
                <th class="px-6 py-3 text-left text-sm font-semibold text-gray-900">Contexto</th>
                <th class="px-6 py-3 text-center text-sm font-semibold text-gray-900">Aprobado</th>
                <th class="px-6 py-3 text-center text-sm font-semibold text-gray-900">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              {#each filteredTranslations as translation (translation.id)}
                <tr class="hover:bg-gray-50 transition">
                  <td class="px-6 py-4 text-sm font-medium text-gray-900 font-mono">{translation.key}</td>
                  <td class="px-6 py-4 text-sm text-gray-600">
                    {translation.locale === 'en' ? '🇺🇸 English' : '🇲🇽 Español'}
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-600 max-w-xs truncate">{translation.value}</td>
                  <td class="px-6 py-4 text-sm text-gray-600">
                    {#if translation.context}
                      <span class="inline-block px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                        {translation.context}
                      </span>
                    {:else}
                      <span class="text-gray-400">—</span>
                    {/if}
                  </td>
                  <td class="px-6 py-4 text-center">
                    <button
                      onclick={() => toggleApproval(translation.id, translation.is_approved)}
                      class="inline-flex items-center gap-1 px-2 py-1 rounded transition {translation.is_approved
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-600'}"
                    >
                      {#if translation.is_approved}
                        <Check class="w-4 h-4" />
                        Sí
                      {:else}
                        <X class="w-4 h-4" />
                        No
                      {/if}
                    </button>
                  </td>
                  <td class="px-6 py-4 text-center flex items-center justify-center gap-2">
                    <button
                      onclick={() => openEdit(translation)}
                      class="p-2 hover:bg-blue-100 text-blue-600 rounded transition"
                      title="Editar"
                    >
                      <Edit3 class="w-4 h-4" />
                    </button>
                    <button
                      onclick={() => deleteTranslation(translation.id)}
                      class="p-2 hover:bg-red-100 text-red-600 rounded transition"
                      title="Eliminar"
                    >
                      <Trash2 class="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    {/if}
  </div>

  <!-- Modal -->
  {#if showModal}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 class="text-xl font-bold text-gray-900">
            {editingId ? 'Editar Traducción' : 'Nueva Traducción'}
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

        <div class="p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Key *</label>
              <input
                type="text"
                bind:value={form.key}
                placeholder="hero.title, footer.copyright..."
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono text-sm"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Idioma</label>
              <select
                bind:value={form.locale}
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="en">English (en)</option>
                <option value="es">Español (es)</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Valor *</label>
            <textarea
              bind:value={form.value}
              placeholder="Texto traducido..."
              rows="4"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Contexto (opcional)</label>
            <select
              bind:value={form.context}
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="">Sin contexto</option>
              <option value="landing">Landing</option>
              <option value="seo">SEO</option>
              <option value="pricing">Pricing</option>
              <option value="footer">Footer</option>
              <option value="email">Email</option>
            </select>
          </div>

          <label class="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              bind:checked={form.is_approved}
              class="w-4 h-4 accent-purple-600"
            />
            <span class="text-sm text-gray-700">Aprobado</span>
          </label>
        </div>

        <div class="border-t border-gray-200 px-6 py-4 flex justify-end gap-2">
          <button
            onclick={() => {
              showModal = false;
            }}
            class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            Cancelar
          </button>
          <button
            onclick={() => saveTranslation()}
            disabled={saving}
            class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition"
          >
            {saving ? 'Guardando...' : 'Guardar'}
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>
