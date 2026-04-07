<script lang="ts">
  import { onMount } from 'svelte';
  import { onboardingConfigApi } from '../lib/api/onboardingConfig';
  import type { OnboardingConfig, OnboardingStep, PortalMenuItem } from '../lib/api/onboardingConfig';
  import { toasts } from '../lib/stores';
  import {
    Settings, Save, Plus, Trash2, Eye, EyeOff, Globe, Menu,
    List, FileText, ToggleLeft, ToggleRight, ChevronUp, ChevronDown,
    Loader2, RefreshCw, Check, X,
  } from 'lucide-svelte';

  let config: OnboardingConfig | null = null;
  let loading = true;
  let saving = false;
  let activeTab: 'welcome' | 'steps' | 'plans' | 'menu' | 'account' | 'ecf' = 'welcome';

  const TABS = [
    { key: 'welcome', label: 'Bienvenida', icon: FileText },
    { key: 'steps',   label: 'Pasos',      icon: List },
    { key: 'plans',   label: 'Planes',     icon: Globe },
    { key: 'menu',    label: 'Menú Portal',icon: Menu },
    { key: 'account', label: 'Cuenta',     icon: Settings },
    { key: 'ecf',     label: 'Fiscal (RD)',icon: FileText },
  ] as const;

  const STEP_KEYS = [
    { key: 'password', label: 'Contraseña', defaultRequired: true },
    { key: 'profile',  label: 'Perfil',     defaultRequired: true },
    { key: 'ecf',      label: 'Fiscal (RD)',defaultRequired: false },
    { key: 'confirm',  label: 'Confirmación',defaultRequired: true },
  ];

  const MENU_ICONS = ['LayoutDashboard','CreditCard','Globe','MessageSquare','Settings','FileText','BarChart2','Users'];
  const ECF_COUNTRIES = ['DO','MX','CO','PE','CL','AR','EC','GT','CR','PA'];

  async function loadConfig() {
    loading = true;
    try {
      config = await onboardingConfigApi.get('default');
      // Ensure arrays exist
      if (!config.steps_config || !config.steps_config.length) {
        config.steps_config = STEP_KEYS.map((s, i) => ({
          step: i, key: s.key, label: s.label,
          required: s.defaultRequired, visible: true, condition: null,
        }));
      }
      if (!config.portal_menu || !config.portal_menu.length) {
        config.portal_menu = defaultMenu();
      }
    } catch (e: any) {
      toasts.error(e.message || 'Error cargando configuración');
    } finally {
      loading = false;
    }
  }

  function defaultMenu(): PortalMenuItem[] {
    return [
      { key:'dashboard', label:'Dashboard',  icon:'LayoutDashboard', visible:true, order:0 },
      { key:'billing',   label:'Facturación',icon:'CreditCard',       visible:true, order:1 },
      { key:'domains',   label:'Dominios',   icon:'Globe',            visible:true, order:2 },
      { key:'support',   label:'Soporte',    icon:'MessageSquare',    visible:true, order:3 },
      { key:'settings',  label:'Configuración',icon:'Settings',       visible:true, order:4 },
    ];
  }

  async function save() {
    if (!config) return;
    saving = true;
    try {
      const res = await onboardingConfigApi.update('default', {
        welcome_title:    config.welcome_title,
        welcome_subtitle: config.welcome_subtitle,
        steps_config:     config.steps_config,
        visible_plans:    config.visible_plans,
        portal_menu:      config.portal_menu,
        allow_plan_change:  config.allow_plan_change,
        allow_cancel:       config.allow_cancel,
        allow_email_change: config.allow_email_change,
        show_invoices:      config.show_invoices,
        show_usage:         config.show_usage,
        ecf_countries:      config.ecf_countries,
      });
      config = res.config;
      toasts.success('Configuración guardada');
    } catch (e: any) {
      toasts.error(e.message || 'Error guardando');
    } finally {
      saving = false;
    }
  }

  // ── Steps helpers ────────────────────────────────────────
  function moveStep(index: number, dir: -1 | 1) {
    if (!config) return;
    const arr = [...config.steps_config];
    const target = index + dir;
    if (target < 0 || target >= arr.length) return;
    [arr[index], arr[target]] = [arr[target], arr[index]];
    arr.forEach((s, i) => (s.step = i));
    config.steps_config = arr;
  }

  function toggleStepCondition(step: OnboardingStep) {
    if (step.condition) {
      step.condition = null;
    } else {
      step.condition = { country_in: ['DO'] };
    }
    config = config; // trigger reactivity
  }

  // ── Menu helpers ─────────────────────────────────────────
  function addMenuItem() {
    if (!config) return;
    config.portal_menu = [...config.portal_menu, {
      key: `item_${Date.now()}`, label: 'Nueva sección',
      icon: 'FileText', visible: true, order: config.portal_menu.length,
    }];
  }

  function removeMenuItem(i: number) {
    if (!config) return;
    config.portal_menu = config.portal_menu.filter((_, idx) => idx !== i);
    config.portal_menu.forEach((m, idx) => (m.order = idx));
  }

  function moveMenuItem(i: number, dir: -1 | 1) {
    if (!config) return;
    const arr = [...config.portal_menu];
    const t = i + dir;
    if (t < 0 || t >= arr.length) return;
    [arr[i], arr[t]] = [arr[t], arr[i]];
    arr.forEach((m, idx) => (m.order = idx));
    config.portal_menu = arr;
  }

  // ── Plan helpers ─────────────────────────────────────────
  function togglePlan(name: string) {
    if (!config) return;
    if (config.visible_plans.includes(name)) {
      config.visible_plans = config.visible_plans.filter(p => p !== name);
    } else {
      config.visible_plans = [...config.visible_plans, name];
    }
  }

  // ── ECF helpers ─────────────────────────────────────────
  function toggleEcfCountry(code: string) {
    if (!config) return;
    if (config.ecf_countries.includes(code)) {
      config.ecf_countries = config.ecf_countries.filter(c => c !== code);
    } else {
      config.ecf_countries = [...config.ecf_countries, code];
    }
  }

  onMount(loadConfig);
</script>

<!-- ══════════════════════════════════════════════════════════ -->
<!--  PAGE HEADER                                              -->
<!-- ══════════════════════════════════════════════════════════ -->
<div class="p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto">
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
    <div>
      <h1 class="text-2xl font-bold text-white flex items-center gap-2">
        <Settings class="w-6 h-6 text-blue-400" />
        Configuración de Onboarding
      </h1>
      <p class="text-slate-400 text-sm mt-1">
        Personaliza pasos, planes, menú del portal y textos de bienvenida.
      </p>
    </div>
    <div class="flex gap-2">
      <button
        on:click={loadConfig}
        disabled={loading}
        class="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm transition"
      >
        <RefreshCw class="w-4 h-4 {loading ? 'animate-spin' : ''}" />
        Recargar
      </button>
      <button
        on:click={save}
        disabled={saving || loading}
        class="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition disabled:opacity-50"
      >
        {#if saving}
          <Loader2 class="w-4 h-4 animate-spin" />
        {:else}
          <Save class="w-4 h-4" />
        {/if}
        Guardar cambios
      </button>
    </div>
  </div>

  {#if loading}
    <div class="flex justify-center py-20">
      <Loader2 class="w-10 h-10 text-blue-400 animate-spin" />
    </div>
  {:else if config}
    <!-- ── TABS ── -->
    <div class="flex flex-wrap gap-1 mb-6 bg-slate-800/50 p-1 rounded-xl">
      {#each TABS as tab}
          {@const TabIcon = tab.icon as any}
        <button
          on:click={() => activeTab = tab.key}
          class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition
            {activeTab === tab.key
              ? 'bg-blue-600 text-white shadow'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700'}"
        >
          <TabIcon class="w-4 h-4" />
          {tab.label}
        </button>
      {/each}
    </div>

    <!-- ══════════════════════════════════════════════════════ -->
    <!--  TAB: BIENVENIDA                                       -->
    <!-- ══════════════════════════════════════════════════════ -->
    {#if activeTab === 'welcome'}
      <div class="space-y-5">
        <div class="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h2 class="text-lg font-semibold text-white mb-4">Textos de Bienvenida</h2>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-slate-300 mb-1">Título principal</label>
              <input
                type="text"
                bind:value={config.welcome_title}
                placeholder="¡Bienvenido a Sajet ERP!"
                class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2
                       text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-300 mb-1">Subtítulo</label>
              <textarea
                bind:value={config.welcome_subtitle}
                rows="3"
                placeholder="Configure su cuenta para comenzar."
                class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2
                       text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              ></textarea>
            </div>
          </div>
        </div>

        <!-- Live preview -->
        <div class="bg-gradient-to-br from-blue-900/40 to-slate-900 rounded-xl p-8 border border-blue-700/30 text-center">
          <p class="text-xs text-slate-500 uppercase tracking-wider mb-4">Vista previa</p>
          <h3 class="text-2xl font-bold text-white mb-2">{config.welcome_title || '—'}</h3>
          <p class="text-slate-300">{config.welcome_subtitle || '—'}</p>
        </div>
      </div>

    <!-- ══════════════════════════════════════════════════════ -->
    <!--  TAB: PASOS                                            -->
    <!-- ══════════════════════════════════════════════════════ -->
    {:else if activeTab === 'steps'}
      <div class="bg-slate-800 rounded-xl border border-slate-700 divide-y divide-slate-700">
        {#each config.steps_config as step, i}
          <div class="p-4 flex flex-col sm:flex-row sm:items-start gap-4">
            <!-- Order buttons -->
            <div class="flex sm:flex-col gap-1 pt-1">
              <button
                on:click={() => moveStep(i, -1)}
                disabled={i === 0}
                class="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-700 disabled:opacity-30 transition"
              ><ChevronUp class="w-4 h-4" /></button>
              <button
                on:click={() => moveStep(i, 1)}
                disabled={i === config.steps_config.length - 1}
                class="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-700 disabled:opacity-30 transition"
              ><ChevronDown class="w-4 h-4" /></button>
            </div>

            <!-- Step number badge -->
            <div class="w-8 h-8 rounded-full bg-blue-700 flex items-center justify-center text-white text-sm font-bold shrink-0">
              {i + 1}
            </div>

            <!-- Content -->
            <div class="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs text-slate-400 mb-1">Etiqueta del paso</label>
                <input
                  type="text"
                  bind:value={step.label}
                  class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-1.5
                         text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label class="block text-xs text-slate-400 mb-1">Clave interna</label>
                <input
                  type="text"
                  value={step.key}
                  disabled
                  class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5
                         text-slate-500 text-sm cursor-not-allowed"
                />
              </div>
            </div>

            <!-- Toggles -->
            <div class="flex flex-col gap-2 min-w-[140px]">
              <label class="flex items-center justify-between gap-2 text-sm cursor-pointer">
                <span class="text-slate-300">Visible</span>
                <button
                  on:click={() => { step.visible = !step.visible; config = config; }}
                  class="transition {step.visible ? 'text-green-400' : 'text-slate-600'}"
                >
                  {#if step.visible}
                    <ToggleRight class="w-6 h-6" />
                  {:else}
                    <ToggleLeft class="w-6 h-6" />
                  {/if}
                </button>
              </label>
              <label class="flex items-center justify-between gap-2 text-sm cursor-pointer">
                <span class="text-slate-300">Requerido</span>
                <button
                  on:click={() => { step.required = !step.required; config = config; }}
                  class="transition {step.required ? 'text-blue-400' : 'text-slate-600'}"
                  disabled={step.key === 'password'}
                >
                  {#if step.required}
                    <ToggleRight class="w-6 h-6" />
                  {:else}
                    <ToggleLeft class="w-6 h-6" />
                  {/if}
                </button>
              </label>
              <label class="flex items-center justify-between gap-2 text-sm cursor-pointer">
                <span class="text-slate-300">Solo países</span>
                <button
                  on:click={() => toggleStepCondition(step)}
                  class="transition {step.condition ? 'text-amber-400' : 'text-slate-600'}"
                >
                  {#if step.condition}
                    <ToggleRight class="w-6 h-6" />
                  {:else}
                    <ToggleLeft class="w-6 h-6" />
                  {/if}
                </button>
              </label>

              {#if step.condition}
                <input
                  type="text"
                  placeholder="DO,MX,CO"
                  value={(step.condition.country_in || []).join(',')}
                  on:input={(e) => {
                    const val = (e.target as HTMLInputElement).value;
                    step.condition = { country_in: val.split(',').map(c => c.trim().toUpperCase()).filter(Boolean) };
                    config = config;
                  }}
                  class="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1
                         text-white text-xs focus:outline-none focus:ring-1 focus:ring-amber-500"
                />
              {/if}
            </div>
          </div>
        {/each}
      </div>

    <!-- ══════════════════════════════════════════════════════ -->
    <!--  TAB: PLANES                                           -->
    <!-- ══════════════════════════════════════════════════════ -->
    {:else if activeTab === 'plans'}
      <div class="space-y-4">
        <p class="text-slate-400 text-sm">
          Selecciona qué planes son visibles en el onboarding y portal del cliente.
          Los detalles de cada plan (precio, features) se gestionan en la sección <strong class="text-white">Planes</strong>.
        </p>
        {#if config.available_plans && config.available_plans.length}
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {#each config.available_plans as plan}
              {@const active = config.visible_plans.includes(plan.name)}
              <button
                on:click={() => togglePlan(plan.name)}
                class="relative p-4 rounded-xl border text-left transition
                  {active
                    ? 'border-blue-500 bg-blue-900/30'
                    : 'border-slate-700 bg-slate-800 hover:border-slate-500'}"
              >
                {#if active}
                  <span class="absolute top-3 right-3 bg-blue-500 rounded-full p-0.5">
                    <Check class="w-3 h-3 text-white" />
                  </span>
                {/if}
                <p class="font-semibold text-white">{plan.display_name}</p>
                <p class="text-sm text-slate-400">${plan.base_price}/mes base</p>
                <p class="text-xs text-slate-500 mt-1 font-mono">{plan.name}</p>
              </button>
            {/each}
          </div>
        {:else}
          <p class="text-slate-500 text-sm">No hay planes disponibles. Crea planes en la sección Planes.</p>
        {/if}

        {#if config.plans_detail && config.plans_detail.length}
          <div class="mt-4">
            <h3 class="text-sm font-semibold text-slate-300 mb-3">Detalle de planes visibles</h3>
            <div class="overflow-x-auto">
              <table class="w-full text-sm text-left">
                <thead class="text-xs text-slate-400 uppercase bg-slate-800">
                  <tr>
                    <th class="px-4 py-2">Plan</th>
                    <th class="px-4 py-2">Precio base</th>
                    <th class="px-4 py-2">+Usuario</th>
                    <th class="px-4 py-2">Usuarios inc.</th>
                    <th class="px-4 py-2">Features</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-700">
                  {#each config.plans_detail as pd}
                    <tr class="bg-slate-800/50 hover:bg-slate-800">
                      <td class="px-4 py-2 font-medium text-white">{pd.display_name}</td>
                      <td class="px-4 py-2 text-green-400">${pd.base_price}</td>
                      <td class="px-4 py-2 text-slate-300">${pd.price_per_user}</td>
                      <td class="px-4 py-2 text-slate-300">{pd.included_users}</td>
                      <td class="px-4 py-2">
                        <div class="flex flex-wrap gap-1">
                          {#each pd.features.slice(0, 3) as feat}
                            <span class="px-1.5 py-0.5 bg-slate-700 rounded text-slate-300 text-xs">{feat}</span>
                          {/each}
                          {#if pd.features.length > 3}
                            <span class="text-slate-500 text-xs">+{pd.features.length - 3}</span>
                          {/if}
                        </div>
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </div>
        {/if}
      </div>

    <!-- ══════════════════════════════════════════════════════ -->
    <!--  TAB: MENÚ PORTAL                                      -->
    <!-- ══════════════════════════════════════════════════════ -->
    {:else if activeTab === 'menu'}
      <div class="space-y-4">
        <div class="flex justify-between items-center">
          <p class="text-slate-400 text-sm">Configura qué secciones aparecen en el portal del cliente.</p>
          <button
            on:click={addMenuItem}
            class="flex items-center gap-1.5 px-3 py-1.5 bg-green-700 hover:bg-green-600 text-white rounded-lg text-sm transition"
          >
            <Plus class="w-4 h-4" /> Agregar sección
          </button>
        </div>

        <div class="bg-slate-800 rounded-xl border border-slate-700 divide-y divide-slate-700">
          {#each config.portal_menu as item, i}
            <div class="p-4 flex flex-col sm:flex-row sm:items-center gap-4">
              <!-- Order -->
              <div class="flex sm:flex-col gap-1">
                <button on:click={() => moveMenuItem(i, -1)} disabled={i === 0}
                  class="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-700 disabled:opacity-30 transition">
                  <ChevronUp class="w-4 h-4" />
                </button>
                <button on:click={() => moveMenuItem(i, 1)} disabled={i === config.portal_menu.length - 1}
                  class="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-700 disabled:opacity-30 transition">
                  <ChevronDown class="w-4 h-4" />
                </button>
              </div>

              <div class="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label class="block text-xs text-slate-400 mb-1">Etiqueta</label>
                  <input type="text" bind:value={item.label}
                    class="w-full bg-slate-700 border border-slate-600 rounded px-3 py-1.5
                           text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
                <div>
                  <label class="block text-xs text-slate-400 mb-1">Clave</label>
                  <input type="text" bind:value={item.key}
                    class="w-full bg-slate-700 border border-slate-600 rounded px-3 py-1.5
                           text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
                <div>
                  <label class="block text-xs text-slate-400 mb-1">Ícono (Lucide)</label>
                  <select bind:value={item.icon}
                    class="w-full bg-slate-700 border border-slate-600 rounded px-3 py-1.5
                           text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    {#each MENU_ICONS as ico}
                      <option value={ico}>{ico}</option>
                    {/each}
                  </select>
                </div>
              </div>

              <!-- Visible toggle + delete -->
              <div class="flex items-center gap-3">
                <button on:click={() => { item.visible = !item.visible; config = config; }}
                  class="transition {item.visible ? 'text-green-400' : 'text-slate-600'}">
                  {#if item.visible}
                    <Eye class="w-5 h-5" />
                  {:else}
                    <EyeOff class="w-5 h-5" />
                  {/if}
                </button>
                <button on:click={() => removeMenuItem(i)}
                  class="text-red-400 hover:text-red-300 transition p-1 rounded hover:bg-red-900/30">
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </div>
          {/each}
        </div>

        {#if config.portal_menu.length === 0}
          <div class="text-center py-10 text-slate-500">
            No hay ítems en el menú. Agrega al menos uno.
          </div>
        {/if}
      </div>

    <!-- ══════════════════════════════════════════════════════ -->
    <!--  TAB: CUENTA                                           -->
    <!-- ══════════════════════════════════════════════════════ -->
    {:else if activeTab === 'account'}
      <div class="bg-slate-800 rounded-xl border border-slate-700 p-6 space-y-5">
        <h2 class="text-lg font-semibold text-white">Gestión de Cuenta del Cliente</h2>
        <p class="text-slate-400 text-sm">Controla qué acciones pueden realizar los clientes desde su portal.</p>

        {#each [
          { key: 'allow_plan_change',  label: 'Cambiar de plan',     desc: 'El cliente puede solicitar un upgrade/downgrade' },
          { key: 'allow_cancel',       label: 'Cancelar suscripción', desc: 'El cliente puede iniciar la cancelación' },
          { key: 'allow_email_change', label: 'Cambiar e-mail',       desc: 'El cliente puede actualizar su correo de acceso' },
          { key: 'show_invoices',      label: 'Ver facturas',          desc: 'Mostrar historial de facturas' },
          { key: 'show_usage',         label: 'Ver uso de recursos',   desc: 'Mostrar métricas de uso (almacenamiento, usuarios)' },
        ] as opt}
          <div class="flex items-center justify-between py-3 border-b border-slate-700 last:border-0">
            <div>
              <p class="text-white font-medium">{opt.label}</p>
              <p class="text-slate-400 text-sm">{opt.desc}</p>
            </div>
            <button
              on:click={() => { (config as any)[opt.key] = !(config as any)[opt.key]; config = config; }}
              class="transition {(config as any)[opt.key] ? 'text-green-400' : 'text-slate-500'}"
            >
              {#if (config as any)[opt.key]}
                <ToggleRight class="w-8 h-8" />
              {:else}
                <ToggleLeft class="w-8 h-8" />
              {/if}
            </button>
          </div>
        {/each}
      </div>

    <!-- ══════════════════════════════════════════════════════ -->
    <!--  TAB: FISCAL (RD e-CF)                                 -->
    <!-- ══════════════════════════════════════════════════════ -->
    {:else if activeTab === 'ecf'}
      <div class="space-y-5">
        <div class="bg-slate-800 rounded-xl border border-slate-700 p-6">
          <h2 class="text-lg font-semibold text-white mb-2">Países que activan e-CF</h2>
          <p class="text-slate-400 text-sm mb-4">
            Los clientes de estos países verán el paso de configuración fiscal electrónica durante el onboarding.
          </p>
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
            {#each ECF_COUNTRIES as code}
              {@const active = config.ecf_countries.includes(code)}
              <button
                on:click={() => toggleEcfCountry(code)}
                class="flex items-center gap-2 px-3 py-2 rounded-lg border text-sm transition
                  {active
                    ? 'border-blue-500 bg-blue-900/30 text-white'
                    : 'border-slate-700 bg-slate-700/50 text-slate-400 hover:border-slate-500'}"
              >
                {#if active}
                  <Check class="w-4 h-4 text-blue-400 shrink-0" />
                {:else}
                  <X class="w-4 h-4 text-slate-600 shrink-0" />
                {/if}
                {code}
              </button>
            {/each}
          </div>
        </div>

        <div class="bg-amber-900/20 border border-amber-700/40 rounded-xl p-4 text-sm text-amber-300">
          <strong>Nota:</strong> Actualmente la integración e-CF solo está disponible para República Dominicana (DO)
          con la DGII. Si activas otros países, el paso aparecerá pero deberás integrar su sistema fiscal.
        </div>
      </div>
    {/if}

    <!-- ── Bottom save bar ── -->
    <div class="mt-8 flex justify-end">
      <button
        on:click={save}
        disabled={saving}
        class="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500
               text-white font-medium transition disabled:opacity-50"
      >
        {#if saving}
          <Loader2 class="w-4 h-4 animate-spin" />
          Guardando…
        {:else}
          <Save class="w-4 h-4" />
          Guardar configuración
        {/if}
      </button>
    </div>
  {:else}
    <div class="text-center py-20 text-slate-500">No se pudo cargar la configuración.</div>
  {/if}
</div>
