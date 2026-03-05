<script lang="ts">
  import { onMount } from 'svelte';
  import { MessageCircle, Plus, Edit3, Trash2, Globe, Star, Check, X } from 'lucide-svelte';
  import { api } from '../lib/api/client';
  import type { Testimonial } from '../lib/types';

  let testimonials: Testimonial[] = $state([]);
  let loading = $state(true);
  let error = $state('');

  // Modal state
  let showModal = $state(false);
  let editingId: number | null = $state(null);
  let saving = $state(false);
  let selectedLocale = $state('en');

  // Form
  let form = $state({
    name: '',
    role: '',
    company: '',
    text: '',
    avatar_url: '',
    locale: 'en',
    featured: false,
    sort_order: 0,
  });

  async function loadTestimonials() {
    loading = true;
    error = '';
    try {
      const data = await api.get<{ items: Testimonial[]; total: number }>(
        `/api/admin/testimonials?locale=${selectedLocale}`
      );
      testimonials = data.items ?? [];
    } catch (e: any) {
      error = e.message || 'Error cargando testimonios';
      console.error(e);
    } finally {
      loading = false;
    }
  }

  function openCreate() {
    editingId = null;
    form = {
      name: '',
      role: '',
      company: '',
      text: '',
      avatar_url: '',
      locale: selectedLocale,
      featured: false,
      sort_order: testimonials.length + 1,
    };
    showModal = true;
  }

  function openEdit(testimonial: Testimonial) {
    editingId = testimonial.id;
    form = {
      name: testimonial.name,
      role: testimonial.role,
      company: testimonial.company,
      text: testimonial.text,
      avatar_url: testimonial.avatar_url || '',
      locale: testimonial.locale,
      featured: testimonial.featured || false,
      sort_order: testimonial.sort_order || 0,
    };
    showModal = true;
  }

  async function saveTestimonial() {
    if (!form.name.trim() || !form.text.trim()) {
      alert('Nombre y texto son requeridos');
      return;
    }

    saving = true;
    try {
      if (editingId) {
        await api.put(`/api/admin/testimonials/${editingId}`, form);
      } else {
        await api.post('/api/admin/testimonials', form);
      }
      showModal = false;
      await loadTestimonials();
    } catch (e: any) {
      alert(e.message || 'Error guardando testimonio');
    } finally {
      saving = false;
    }
  }

  async function deleteTestimonial(id: number) {
    if (!confirm('¿Eliminar este testimonio?')) return;
    try {
      await api.delete(`/api/admin/testimonials/${id}`);
      await loadTestimonials();
    } catch (e: any) {
      alert(e.message || 'Error eliminando testimonio');
    }
  }

  async function toggleFeatured(id: number, featured: boolean) {
    try {
      await api.patch(`/api/admin/testimonials/${id}`, { featured: !featured });
      await loadTestimonials();
    } catch (e: any) {
      alert(e.message || 'Error actualizando testimonio');
    }
  }

  onMount(() => {
    loadTestimonials();
  });

  $effect(() => {
    selectedLocale;
    loadTestimonials();
  });
</script>

<div class="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8">
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <MessageCircle class="w-8 h-8 text-amber-600" />
          <h1 class="text-3xl font-bold text-gray-900">Testimonios</h1>
        </div>
        <button
          onclick={() => openCreate()}
          class="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition"
        >
          <Plus class="w-5 h-5" />
          Nuevo Testimonio
        </button>
      </div>

      <!-- Filters -->
      <div class="flex items-center gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Idioma</label>
          <select
            bind:value={selectedLocale}
            class="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
          >
            <option value="en">English (en)</option>
            <option value="es">Español (es)</option>
          </select>
        </div>
        <div class="text-sm text-gray-600 mt-6">
          {testimonials.length} testimonios
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
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
        </div>
      </div>
    {:else if testimonials.length === 0}
      <div class="text-center py-12">
        <MessageCircle class="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p class="text-gray-600">No hay testimonios para este idioma</p>
      </div>
    {:else}
      <!-- Table -->
      <div class="bg-white rounded-lg shadow overflow-hidden">
        <table class="w-full">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-6 py-3 text-left text-sm font-semibold text-gray-900">Nombre</th>
              <th class="px-6 py-3 text-left text-sm font-semibold text-gray-900">Rol</th>
              <th class="px-6 py-3 text-left text-sm font-semibold text-gray-900">Empresa</th>
              <th class="px-6 py-3 text-left text-sm font-semibold text-gray-900">Texto</th>
              <th class="px-6 py-3 text-center text-sm font-semibold text-gray-900">Destacado</th>
              <th class="px-6 py-3 text-center text-sm font-semibold text-gray-900">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            {#each testimonials as testimonial (testimonial.id)}
              <tr class="hover:bg-gray-50 transition">
                <td class="px-6 py-4 text-sm font-medium text-gray-900">{testimonial.name}</td>
                <td class="px-6 py-4 text-sm text-gray-600">{testimonial.role}</td>
                <td class="px-6 py-4 text-sm text-gray-600">{testimonial.company}</td>
                <td class="px-6 py-4 text-sm text-gray-600 max-w-xs truncate">
                  {testimonial.text}
                </td>
                <td class="px-6 py-4 text-center">
                  <button
                    onclick={() => toggleFeatured(testimonial.id, testimonial.featured || false)}
                    class="inline-flex items-center gap-1 px-2 py-1 rounded transition {testimonial.featured
                      ? 'bg-amber-100 text-amber-700'
                      : 'bg-gray-100 text-gray-600'}"
                  >
                    {#if testimonial.featured}
                      <Star class="w-4 h-4 fill-current" />
                      Sí
                    {:else}
                      <X class="w-4 h-4" />
                      No
                    {/if}
                  </button>
                </td>
                <td class="px-6 py-4 text-center flex items-center justify-center gap-2">
                  <button
                    onclick={() => openEdit(testimonial)}
                    class="p-2 hover:bg-blue-100 text-blue-600 rounded transition"
                    title="Editar"
                  >
                    <Edit3 class="w-4 h-4" />
                  </button>
                  <button
                    onclick={() => deleteTestimonial(testimonial.id)}
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
    {/if}
  </div>

  <!-- Modal -->
  {#if showModal}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 class="text-xl font-bold text-gray-900">
            {editingId ? 'Editar Testimonio' : 'Nuevo Testimonio'}
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
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
            <input
              type="text"
              bind:value={form.name}
              placeholder="Nombre del cliente"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            />
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Rol</label>
              <input
                type="text"
                bind:value={form.role}
                placeholder="CEO, Contador, etc."
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Empresa</label>
              <input
                type="text"
                bind:value={form.company}
                placeholder="Nombre de la empresa"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Texto del Testimonio *</label>
            <textarea
              bind:value={form.text}
              placeholder="Lo que el cliente dijo..."
              rows="4"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">URL Avatar</label>
            <input
              type="url"
              bind:value={form.avatar_url}
              placeholder="https://..."
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            />
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Idioma</label>
              <select
                bind:value={form.locale}
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              >
                <option value="en">English (en)</option>
                <option value="es">Español (es)</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Orden</label>
              <input
                type="number"
                bind:value={form.sort_order}
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              />
            </div>
          </div>

          <label class="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              bind:checked={form.featured}
              class="w-4 h-4 accent-amber-600"
            />
            <span class="text-sm text-gray-700">Mostrar en página principal</span>
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
            onclick={() => saveTestimonial()}
            disabled={saving}
            class="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 transition"
          >
            {saving ? 'Guardando...' : 'Guardar'}
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>
