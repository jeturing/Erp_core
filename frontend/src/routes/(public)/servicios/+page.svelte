<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';

  // ── Tipos ──────────────────────────────────────────────
  interface CatalogItem {
    id: number;
    name: string;
    description: string | null;
    unit: string;
    price_monthly: number;
    price_max: number | null;
    is_addon: boolean;
    service_code: string | null;
    metadata_json: Record<string, unknown>;
  }

  interface CatalogData {
    categories: Record<string, CatalogItem[]>;
    total: number;
  }

  // ── Estado ────────────────────────────────────────────
  let catalog = $state<CatalogData | null>(null);
  let loading = $state(true);
  let error   = $state('');

  // Etiquetas legibles para categorías
  const CATEGORY_LABELS: Record<string, string> = {
    saas_platform:   'Plataforma SaaS',
    saas_support:    'Soporte',
    core_financiero: 'Core Financiero',
    vciso:           'vCISO',
    soc:             'SOC / SIEM',
    cloud_devops:    'Cloud & DevOps',
    payments_pos:    'Pagos & POS',
    email_service:   'Servicio de Correo',
  };

  const CATEGORY_ICONS: Record<string, string> = {
    saas_platform:   '🏢',
    saas_support:    '🛠️',
    core_financiero: '💰',
    vciso:           '🔐',
    soc:             '🛡️',
    cloud_devops:    '☁️',
    payments_pos:    '💳',
    email_service:   '✉️',
  };

  // ── Lógica ────────────────────────────────────────────
  onMount(async () => {
    try {
      const data = await api.get<CatalogData>('/api/public/catalog');
      catalog = data;
    } catch (e: unknown) {
      error = 'No se pudo cargar el catálogo. Por favor, intenta más tarde.';
      console.error(e);
    } finally {
      loading = false;
    }
  });

  function formatPrice(price: number): string {
    return new Intl.NumberFormat('es-DO', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(price);
  }

  function getEmailMeta(item: CatalogItem) {
    const m = item.metadata_json;
    return {
      quota:    (m.email_quota_monthly as number)  ?? 0,
      burst:    (m.email_burst_limit_60m as number) ?? 500,
      overage:  (m.email_overage_price as number)   ?? 0.0002,
    };
  }
</script>

<svelte:head>
  <title>Catálogo de Servicios — SAJET</title>
  <meta name="description" content="Explora todos los servicios y addons disponibles en la plataforma SAJET: correo, soporte, finanzas, ciberseguridad y más." />
</svelte:head>

<!-- ── Hero ──────────────────────────────────────────── -->
<section class="bg-[#003B73] text-white py-16 px-4 text-center">
  <h1 class="text-4xl font-bold font-inter mb-3">Catálogo de Servicios</h1>
  <p class="text-lg text-blue-200 max-w-2xl mx-auto font-inter">
    Todos los productos y addons disponibles para ampliar tu plataforma SAJET.
    Precios en USD por mes.
  </p>
</section>

<!-- ── Contenido ─────────────────────────────────────── -->
<main class="max-w-6xl mx-auto px-4 py-12">

  {#if loading}
    <div class="flex justify-center items-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-4 border-[#00FF9F] border-t-transparent"></div>
    </div>

  {:else if error}
    <div class="text-center py-20">
      <p class="text-red-400 text-lg">{error}</p>
    </div>

  {:else if catalog}
    {#each Object.entries(catalog.categories) as [catKey, items]}
      {@const label = CATEGORY_LABELS[catKey] ?? catKey.replace(/_/g, ' ')}
      {@const icon  = CATEGORY_ICONS[catKey] ?? '📦'}

      <section class="mb-14">
        <div class="flex items-center gap-3 mb-6 border-b border-slate-700 pb-3">
          <span class="text-2xl">{icon}</span>
          <h2 class="text-2xl font-bold text-white font-inter">{label}</h2>
          <span class="ml-auto text-sm text-slate-400">{items.length} plan{items.length !== 1 ? 'es' : ''}</span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {#each items as item (item.id)}
            <article
              class="bg-slate-800 border border-slate-700 rounded-2xl p-6 flex flex-col
                     hover:border-[#00FF9F]/50 transition-colors duration-200"
            >
              <!-- Cabecera -->
              <div class="flex items-start justify-between mb-3">
                <h3 class="text-lg font-semibold text-white font-inter leading-tight">{item.name}</h3>
                {#if item.is_addon}
                  <span class="ml-2 shrink-0 text-xs bg-[#00FF9F]/10 text-[#00FF9F] border border-[#00FF9F]/30 px-2 py-0.5 rounded-full">
                    addon
                  </span>
                {/if}
              </div>

              {#if item.description}
                <p class="text-slate-400 text-sm mb-4 flex-1 font-inter">{item.description}</p>
              {:else}
                <div class="flex-1"></div>
              {/if}

              <!-- Email package — detalles extra -->
              {#if item.service_code === 'postal_email_package'}
                {@const meta = getEmailMeta(item)}
                <ul class="text-sm text-slate-300 mb-4 space-y-1">
                  <li class="flex items-center gap-2">
                    <span class="text-[#00FF9F]">✓</span>
                    <span>{meta.quota.toLocaleString()} correos / mes incluidos</span>
                  </li>
                  <li class="flex items-center gap-2">
                    <span class="text-[#00FF9F]">✓</span>
                    <span>Límite por hora: {meta.burst.toLocaleString()} correos</span>
                  </li>
                  <li class="flex items-center gap-2">
                    <span class="text-slate-500">+</span>
                    <span class="text-slate-400">
                      Excedente: ${(meta.overage * 1000).toFixed(2)} / 1 000 correos
                    </span>
                  </li>
                </ul>
              {/if}

              <!-- Precio -->
              <div class="mt-auto pt-4 border-t border-slate-700 flex items-baseline gap-2">
                <span class="text-2xl font-bold text-white font-inter">
                  {formatPrice(item.price_monthly)}
                </span>
                <span class="text-slate-400 text-sm">/ {item.unit ?? 'mes'}</span>
                {#if item.price_max && item.price_max > item.price_monthly}
                  <span class="text-slate-500 text-xs">hasta {formatPrice(item.price_max)}</span>
                {/if}
              </div>
            </article>
          {/each}
        </div>
      </section>
    {/each}

    <!-- CTA final -->
    <div class="text-center mt-16 py-10 border border-slate-700 rounded-2xl bg-slate-800/50">
      <h3 class="text-2xl font-bold text-white font-inter mb-3">
        ¿Listo para empezar?
      </h3>
      <p class="text-slate-400 mb-6 font-inter">
        Regístrate gratis y activa los servicios que necesitas desde tu panel.
      </p>
      <div class="flex justify-center gap-4 flex-wrap">
        <a
          href="/signup"
          class="bg-[#00FF9F] text-[#003B73] font-bold py-3 px-8 rounded-xl
                 hover:bg-[#00e88f] transition-colors font-inter"
        >
          Crear cuenta gratis
        </a>
        <a
          href="/partner-signup"
          class="border border-[#00FF9F] text-[#00FF9F] font-bold py-3 px-8 rounded-xl
                 hover:bg-[#00FF9F]/10 transition-colors font-inter"
        >
          Ser partner
        </a>
      </div>
    </div>
  {/if}
</main>

<style>
  :global(body) {
    background-color: #0f172a;
    color: #f8fafc;
  }
</style>
