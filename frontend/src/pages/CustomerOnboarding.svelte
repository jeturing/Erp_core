<script lang="ts">
  import { onMount } from 'svelte';
  import { customerOnboardingApi } from '../lib/api/customerOnboarding';
  import { onboardingConfigApi } from '../lib/api/onboardingConfig';
  import { agreementsApi } from '../lib/api';
  import type { OnboardingStatus } from '../lib/api/customerOnboarding';
  import type { OnboardingConfig, OnboardingStep } from '../lib/api/onboardingConfig';
  import type { Plan, AgreementTemplate } from '../lib/types';
  import { toasts, isAuthenticated } from '../lib/stores';
  import { goto } from '$app/navigation';
  import { api } from '../lib/api';
  import {
    CheckCircle, User, Building2, Globe, Phone, Mail, Lock,
    FileText, ArrowRight, ArrowLeft, Loader2, AlertTriangle,
    Shield, CreditCard, PartyPopper, ChevronRight, Eye, EyeOff,
  } from 'lucide-svelte';
  import SignaturePanel from '../lib/components/SignaturePanel.svelte';

  let status: OnboardingStatus | null = null;
  let onboardingConfig: OnboardingConfig | null = null;
  let loading = true;
  let saving = false;
  let currentStep = 0;
  let loadError = '';

  // Derived: steps visible and filtered by country condition
  let visibleSteps: OnboardingStep[] = [];

  // Step 0: Password
  let password = '';
  let passwordConfirm = '';
  let showPassword = false;
  let passwordError = '';

  // Step 1: Profile
  let profileForm = {
    full_name: '',
    company_name: '',
    phone: '',
    country: '',
  };

  // Step 2: e-CF (RD only)
  let ecfForm = {
    requires_ecf: true,
    ecf_rnc: '',
    ecf_business_name: '',
    ecf_establishment_type: 'persona_juridica',
    ecf_ncf_series: 'B01',
    ecf_environment: 'test_ecf',
  };

  // Step 3 — Plan pricing + TOS
  let plans: Plan[] = [];
  let selectedPlan = '';
  let plansLoading = false;
  let customerTOS: AgreementTemplate[] = [];
  let tosSignedIds: Set<number> = new Set();
  let tosSigningId: number | null = null;

  const countries = [
    { code: 'DO', name: 'República Dominicana 🇩🇴' },
    { code: 'US', name: 'Estados Unidos 🇺🇸' },
    { code: 'PR', name: 'Puerto Rico 🇵🇷' },
    { code: 'CO', name: 'Colombia 🇨🇴' },
    { code: 'MX', name: 'México 🇲🇽' },
    { code: 'PA', name: 'Panamá 🇵🇦' },
    { code: 'CR', name: 'Costa Rica 🇨🇷' },
    { code: 'GT', name: 'Guatemala 🇬🇹' },
    { code: 'EC', name: 'Ecuador 🇪🇨' },
    { code: 'PE', name: 'Perú 🇵🇪' },
    { code: 'CL', name: 'Chile 🇨🇱' },
    { code: 'AR', name: 'Argentina 🇦🇷' },
    { code: 'ES', name: 'España 🇪🇸' },
    { code: 'OTHER', name: 'Otro' },
  ];

  const establishmentTypes = [
    { value: 'persona_juridica', label: 'Persona Jurídica (empresa/sociedad)' },
    { value: 'persona_fisica', label: 'Persona Física (individual/profesional)' },
    { value: 'zona_franca', label: 'Zona Franca' },
  ];

  const ncfSeries = [
    { value: 'B01', label: 'B01 — Crédito Fiscal (facturas a empresas)' },
    { value: 'B02', label: 'B02 — Consumidor Final' },
    { value: 'B14', label: 'B14 — Régimen Especial (zonas francas, diplomáticos)' },
    { value: 'B15', label: 'B15 — Gubernamental' },
    { value: 'E31', label: 'E31 — e-CF Crédito Fiscal' },
    { value: 'E32', label: 'E32 — e-CF Consumidor Final' },
    { value: 'E33', label: 'E33 — e-CF Nota de Débito' },
    { value: 'E34', label: 'E34 — e-CF Nota de Crédito' },
  ];

  const stepLabels = [
    { icon: Lock, label: 'Contraseña' },
    { icon: User, label: 'Perfil' },
    { icon: FileText, label: 'Fiscal (RD)' },
    { icon: CreditCard, label: 'Pago' },
    { icon: CheckCircle, label: 'Completado' },
  ];

  async function loadStatus() {
    loading = true;
    loadError = '';
    try {
      // Guard: if not authenticated, redirect to login
      if (!$isAuthenticated) {
        goto('/login');
        return;
      }

      // Load both in parallel
      const [s, cfg] = await Promise.all([
        customerOnboardingApi.getStatus(),
        onboardingConfigApi.getActive(),
      ]);
      status = s;
      onboardingConfig = cfg;
      currentStep = s.onboarding_step;

      // Build visibleSteps from config, filtered by country condition
      visibleSteps = (cfg.steps_config || []).filter(step => {
        if (!step.visible) return false;
        if (step.condition?.country_in && profileForm.country) {
          return step.condition.country_in.includes(profileForm.country);
        }
        if (step.condition?.country_in && step.key === 'ecf') {
          // Show ecf step by default if condition present; filter when country known
          return true;
        }
        return true;
      });

      // Pre-fill profile form
      profileForm.full_name = s.full_name || '';
      profileForm.company_name = s.company_name || '';
      profileForm.phone = s.phone || '';
      profileForm.country = s.country || '';
      // Pre-fill e-CF if available
      if (s.ecf_rnc) ecfForm.ecf_rnc = s.ecf_rnc;
      if (s.ecf_business_name) ecfForm.ecf_business_name = s.ecf_business_name;
      if (s.ecf_establishment_type) ecfForm.ecf_establishment_type = s.ecf_establishment_type;
      if (s.ecf_ncf_series) ecfForm.ecf_ncf_series = s.ecf_ncf_series;
      if (s.ecf_environment) ecfForm.ecf_environment = s.ecf_environment;
    } catch (e: any) {
      const msg = e.message || '';
      // Session expired or not authenticated — redirect to login
      if (msg.includes('expirada') || msg.includes('401') || msg.includes('No autenticado')) {
        toasts.error('Su sesión ha expirado. Por favor, inicie sesión nuevamente.');
        goto('/login');
        return;
      }
      loadError = msg || 'Error cargando el estado del onboarding';
      toasts.error(loadError);
    } finally {
      loading = false;
    }
  }

  // Recompute visible steps when country changes
  $: if (onboardingConfig && profileForm.country) {
    const ecfCountries = onboardingConfig.ecf_countries || ['DO'];
    visibleSteps = (onboardingConfig.steps_config || []).filter(step => {
      if (!step.visible) return false;
      if (step.key === 'ecf') {
        return ecfCountries.includes(profileForm.country);
      }
      if (step.condition?.country_in) {
        return step.condition.country_in.includes(profileForm.country);
      }
      return true;
    });
  }

  // Get step key by currentStep index in the visible list
  $: currentStepKey = visibleSteps[currentStep]?.key ?? 'password';

  // Step 0: Set password
  async function handleSetPassword() {
    passwordError = '';
    if (password.length < 8) {
      passwordError = 'La contraseña debe tener al menos 8 caracteres';
      return;
    }
    if (password !== passwordConfirm) {
      passwordError = 'Las contraseñas no coinciden';
      return;
    }
    saving = true;
    try {
      const res = await customerOnboardingApi.setPassword(password, passwordConfirm);
      currentStep = res.onboarding_step;
      toasts.success('Contraseña establecida');
    } catch (e: any) {
      passwordError = e.message;
    } finally {
      saving = false;
    }
  }

  // Step 1: Update profile
  async function handleUpdateProfile() {
    if (!profileForm.full_name || !profileForm.company_name || !profileForm.country) {
      toasts.error('Nombre, empresa y país son obligatorios');
      return;
    }
    saving = true;
    try {
      const res = await customerOnboardingApi.updateProfile(profileForm);
      currentStep = res.onboarding_step;
      // Refresh status to get is_dominican flag
      await loadStatus();
      currentStep = status!.onboarding_step;
      if (res.is_dominican) {
        toasts.success('Perfil guardado — Complete los datos fiscales para RD');
      } else {
        toasts.success('Perfil completado');
      }
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      saving = false;
    }
  }

  // Step 2: Submit e-CF
  async function handleSubmitECF() {
    if (!ecfForm.ecf_rnc || !ecfForm.ecf_business_name) {
      toasts.error('RNC y Razón Social son obligatorios');
      return;
    }
    saving = true;
    try {
      const res = await customerOnboardingApi.submitECFQuestionnaire(ecfForm);
      currentStep = res.onboarding_step;
      toasts.success('Datos fiscales e-CF registrados');
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      saving = false;
    }
  }

  async function handleSkipECF() {
    saving = true;
    try {
      const res = await customerOnboardingApi.skipECF();
      currentStep = res.onboarding_step;
      toasts.success('Paso e-CF omitido');
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      saving = false;
    }
  }

  // Step 3→4: Complete
  async function handleComplete() {
    saving = true;
    try {
      const res = await customerOnboardingApi.completeOnboarding();
      currentStep = res.onboarding_step;
      toasts.success('¡Onboarding completado!');
    } catch (e: any) {
      toasts.error(e.message);
    } finally {
      saving = false;
    }
  }

  // Determine effective steps: use dynamic config when loaded, fallback to old static logic
  $: isDominican = profileForm.country === 'DO';
  $: effectiveSteps = visibleSteps.length > 0
    ? visibleSteps
    : (isDominican ? stepLabels : stepLabels.filter((_, i) => i !== 2));

  // Map currentStep to visible step index
  $: visibleStep = visibleSteps.length > 0
    ? currentStep
    : isDominican
      ? currentStep
      : currentStep >= 3 ? currentStep - 1 : currentStep;

  // Load available plans
  async function loadPlans() {
    plansLoading = true;
    try {
      const res = await api.get<{ items: Plan[]; total: number }>('/api/admin/plans?active_only=true');
      plans = (res.items || []).sort((a, b) => a.sort_order - b.sort_order);
      if (status?.plan) selectedPlan = status.plan;
      else if (plans.length > 0) selectedPlan = plans[0].name;
    } catch { /* plans not available, show fallback */ }
    plansLoading = false;
  }

  // Load customer TOS
  async function loadCustomerTOS() {
    try {
      const res = await agreementsApi.getRequired('customer');
      customerTOS = res.items || [];
    } catch { customerTOS = []; }
  }

  // Sign TOS
  async function handleSignTOS(event: CustomEvent<{ signer_name: string; signature_data: string }>, templateId: number) {
    tosSigningId = templateId;
    try {
      await agreementsApi.sign({
        template_id: templateId,
        signer_name: event.detail.signer_name,
        signature_data: event.detail.signature_data,
      });
      tosSignedIds = new Set([...tosSignedIds, templateId]);
      toasts.success('Acuerdo firmado');
    } catch (e: any) {
      toasts.error(e.message || 'Error al firmar');
    } finally {
      tosSigningId = null;
    }
  }

  function formatRNC(value: string): string {
    const clean = value.replace(/[^0-9]/g, '');
    if (clean.length === 9) {
      return `${clean.slice(0, 3)}-${clean.slice(3, 8)}-${clean.slice(8)}`;
    }
    if (clean.length === 11) {
      return `${clean.slice(0, 3)}-${clean.slice(3, 10)}-${clean.slice(10)}`;
    }
    return clean;
  }

  onMount(() => {
    loadStatus();
    loadPlans();
    loadCustomerTOS();
  });
</script>

<div class="min-h-screen bg-bg-page p-4 sm:p-8">
  <div class="max-w-3xl mx-auto space-y-8">
    <!-- Header -->
    <div class="text-center">
      <h1 class="text-3xl font-bold text-text-light mb-2">
        {onboardingConfig?.welcome_title ?? 'Bienvenido a Sajet'}
      </h1>
      <p class="text-gray-400">
        {onboardingConfig?.welcome_subtitle ?? 'Complete su configuración para comenzar a usar la plataforma'}
      </p>
    </div>

    {#if loading}
      <div class="flex items-center justify-center py-20">
        <Loader2 size={32} class="animate-spin text-terracotta" />
      </div>
    {:else if !status}
      <div class="card p-8 text-center space-y-4">
        <AlertTriangle size={48} class="mx-auto text-amber-400 mb-4" />
        <p class="text-gray-400">{loadError || 'No se pudo cargar el estado del onboarding.'}</p>
        <div class="flex justify-center gap-3">
          <button class="btn-accent px-4 py-2 text-sm" on:click={loadStatus}>Reintentar</button>
          <a href="/login" class="btn-secondary px-4 py-2 text-sm">Iniciar Sesión</a>
        </div>
      </div>
    {:else if currentStep >= 4}
      <!-- ═══ COMPLETED STATE ═══ -->
      <div class="card p-10 text-center border border-emerald-500/30 space-y-4">
        <PartyPopper size={64} class="mx-auto text-emerald-400" />
        <h2 class="text-2xl font-bold text-emerald-400">¡Onboarding Completado!</h2>
        <p class="text-gray-400">Su cuenta está lista. Ya puede acceder a todos los servicios de la plataforma.</p>
        <div class="pt-4">
          <a href="/dashboard" class="btn-accent inline-flex items-center gap-2 px-6 py-3">
            Ir al Dashboard <ChevronRight size={16} />
          </a>
        </div>
      </div>
    {:else}
      <!-- ═══ PROGRESS STEPPER ═══ -->
      <div class="flex items-center justify-center gap-1 sm:gap-3">
        {#each effectiveSteps as step, i}
          <div class="flex items-center gap-1 sm:gap-2">
            <div class="flex flex-col items-center gap-1">
              <div class={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold transition-all
                ${i < visibleStep ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50' :
                  i === visibleStep ? 'bg-terracotta/20 text-terracotta border-2 border-terracotta scale-110' :
                  'bg-bg-card text-gray-500 border border-border-dark'}`}>
                {#if i < visibleStep}
                  <CheckCircle size={18} />
                {:else}
                  {@const StepIcon = (step as any).icon}
                  <StepIcon size={16} />
                {/if}
              </div>
              <span class="text-[10px] font-medium {i === visibleStep ? 'text-terracotta' : 'text-gray-500'} hidden sm:block">
                {step.label}
              </span>
            </div>
            {#if i < effectiveSteps.length - 1}
              <div class="w-6 sm:w-10 h-px {i < visibleStep ? 'bg-emerald-500/50' : 'bg-border-dark'} mt-[-18px] sm:mt-[-16px]"></div>
            {/if}
          </div>
        {/each}
      </div>

      <!-- ═══ STEP 0: PASSWORD ═══ -->
      {#if currentStep === 0}
        <div class="card p-6 sm:p-8 border border-border-dark space-y-6">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-terracotta/10 flex items-center justify-center">
              <Lock size={20} class="text-terracotta" />
            </div>
            <div>
              <h2 class="text-lg font-bold text-text-light">Establezca su contraseña</h2>
              <p class="text-xs text-gray-500">Cree una contraseña segura para su cuenta</p>
            </div>
          </div>

          {#if passwordError}
            <div class="rounded border border-red-500/30 bg-red-900/20 px-4 py-3 text-sm text-red-300">{passwordError}</div>
          {/if}

          <div class="space-y-4">
            <div>
              <label class="label">Nueva contraseña</label>
              <div class="relative">
                {#if showPassword}
                  <input type="text" bind:value={password} class="input w-full pr-10 font-mono" placeholder="Mínimo 8 caracteres" />
                {:else}
                  <input type="password" bind:value={password} class="input w-full pr-10 font-mono" placeholder="Mínimo 8 caracteres" />
                {/if}
                <button class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-200" type="button"
                  on:click={() => showPassword = !showPassword}>
                  {#if showPassword}<EyeOff size={16} />{:else}<Eye size={16} />{/if}
                </button>
              </div>
            </div>
            <div>
              <label class="label">Confirmar contraseña</label>
              <input type="password" bind:value={passwordConfirm} class="input w-full font-mono" placeholder="Repita la contraseña" />
            </div>
          </div>

          <div class="flex justify-end">
            <button class="btn-accent flex items-center gap-2" on:click={handleSetPassword} disabled={saving}>
              {#if saving}<Loader2 size={14} class="animate-spin" />{/if}
              Continuar <ArrowRight size={16} />
            </button>
          </div>
        </div>
      {/if}

      <!-- ═══ STEP 1: PROFILE ═══ -->
      {#if currentStep === 1}
        <div class="card p-6 sm:p-8 border border-border-dark space-y-6">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <User size={20} class="text-blue-400" />
            </div>
            <div>
              <h2 class="text-lg font-bold text-text-light">Complete su perfil</h2>
              <p class="text-xs text-gray-500">Información básica de su empresa</p>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="label">Nombre completo *</label>
              <div class="relative">
                <User size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                <input type="text" bind:value={profileForm.full_name} class="input w-full pl-9" placeholder="Juan Pérez" />
              </div>
            </div>
            <div>
              <label class="label">Empresa *</label>
              <div class="relative">
                <Building2 size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                <input type="text" bind:value={profileForm.company_name} class="input w-full pl-9" placeholder="Mi Empresa SRL" />
              </div>
            </div>
            <div>
              <label class="label">Teléfono</label>
              <div class="relative">
                <Phone size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                <input type="text" bind:value={profileForm.phone} class="input w-full pl-9" placeholder="+1 (809) 555-1234" />
              </div>
            </div>
            <div>
              <label class="label">País *</label>
              <div class="relative">
                <Globe size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                <select bind:value={profileForm.country} class="input w-full pl-9">
                  <option value="">Seleccione un país...</option>
                  {#each countries as c}
                    <option value={c.code}>{c.name}</option>
                  {/each}
                </select>
              </div>
            </div>
          </div>

          {#if profileForm.country === 'DO'}
            <div class="rounded border border-amber-500/30 bg-amber-900/10 px-4 py-3 text-sm text-amber-300 flex items-start gap-2">
              <AlertTriangle size={16} class="mt-0.5 flex-shrink-0" />
              <div>
                <strong>República Dominicana detectada.</strong> En el siguiente paso deberá completar el cuestionario de factura electrónica (e-CF) requerido por la DGII, o puede indicar que no necesita e-CF.
              </div>
            </div>
          {/if}

          <div class="flex justify-between">
            <button class="btn-secondary flex items-center gap-2" on:click={() => currentStep = 0}>
              <ArrowLeft size={16} /> Atrás
            </button>
            <button class="btn-accent flex items-center gap-2" on:click={handleUpdateProfile} disabled={saving}>
              {#if saving}<Loader2 size={14} class="animate-spin" />{/if}
              Continuar <ArrowRight size={16} />
            </button>
          </div>
        </div>
      {/if}

      <!-- ═══ STEP 2: e-CF QUESTIONNAIRE (RD ONLY) ═══ -->
      {#if currentStep === 2}
        <div class="card p-6 sm:p-8 border border-amber-500/30 space-y-6">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
              <FileText size={20} class="text-amber-400" />
            </div>
            <div>
              <h2 class="text-lg font-bold text-text-light">Factura Electrónica — DGII</h2>
              <p class="text-xs text-gray-500">Datos fiscales para comprobantes electrónicos (e-CF) en República Dominicana</p>
            </div>
          </div>

          <div class="rounded border border-blue-500/30 bg-blue-900/10 px-4 py-3 text-sm text-blue-300">
            <strong>¿Qué es e-CF?</strong> Los Comprobantes Fiscales Electrónicos son documentos tributarios digitales
            autorizados por la DGII. Si su empresa emite facturas en RD, necesita esta configuración para cumplir
            con la normativa vigente (Norma General 05-2019).
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="label">RNC / Cédula *</label>
              <input type="text" bind:value={ecfForm.ecf_rnc} class="input w-full font-mono"
                placeholder="101-12345-6 o 001-1234567-8" maxlength="13" />
              <p class="text-[10px] text-gray-500 mt-1">RNC (9 dígitos) o Cédula (11 dígitos) — solo números</p>
              {#if ecfForm.ecf_rnc}
                <p class="text-xs text-emerald-400 mt-1">Formateado: {formatRNC(ecfForm.ecf_rnc)}</p>
              {/if}
            </div>
            <div>
              <label class="label">Razón Social (nombre fiscal) *</label>
              <input type="text" bind:value={ecfForm.ecf_business_name} class="input w-full"
                placeholder="Nombre exacto según DGII" />
            </div>
            <div>
              <label class="label">Tipo de Contribuyente *</label>
              <select bind:value={ecfForm.ecf_establishment_type} class="input w-full">
                {#each establishmentTypes as t}
                  <option value={t.value}>{t.label}</option>
                {/each}
              </select>
            </div>
            <div>
              <label class="label">Serie NCF principal</label>
              <select bind:value={ecfForm.ecf_ncf_series} class="input w-full">
                {#each ncfSeries as s}
                  <option value={s.value}>{s.label}</option>
                {/each}
              </select>
              <p class="text-[10px] text-gray-500 mt-1">Serie de comprobante que usará con más frecuencia</p>
            </div>
            <div class="md:col-span-2">
              <label class="label">Ambiente</label>
              <div class="flex gap-4">
                <label class="flex items-center gap-2 cursor-pointer text-sm">
                  <input type="radio" bind:group={ecfForm.ecf_environment} value="test_ecf" class="accent-terracotta" />
                  <span class="text-gray-300">Pruebas (Test e-CF)</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer text-sm">
                  <input type="radio" bind:group={ecfForm.ecf_environment} value="production" class="accent-terracotta" />
                  <span class="text-gray-300">Producción</span>
                </label>
              </div>
              <p class="text-[10px] text-gray-500 mt-1">Recomendamos iniciar en pruebas y migrar a producción cuando esté listo</p>
            </div>
          </div>

          <div class="flex justify-between gap-3 flex-wrap">
            <button class="btn-secondary flex items-center gap-2" on:click={() => currentStep = 1}>
              <ArrowLeft size={16} /> Atrás
            </button>
            <div class="flex gap-3">
              <button class="text-sm text-gray-500 hover:text-gray-300 underline" on:click={handleSkipECF} disabled={saving}>
                No necesito e-CF por ahora
              </button>
              <button class="btn-accent flex items-center gap-2" on:click={handleSubmitECF} disabled={saving}>
                {#if saving}<Loader2 size={14} class="animate-spin" />{/if}
                Guardar y Continuar <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </div>
      {/if}

      <!-- ═══ STEP 3: PLAN SELECTION + TOS + CONFIRMATION ═══ -->
      {#if currentStep === 3}
        <div class="card p-6 sm:p-8 border border-border-dark space-y-6">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
              <CreditCard size={20} class="text-emerald-400" />
            </div>
            <div>
              <h2 class="text-lg font-bold text-text-light">Plan y Confirmación</h2>
              <p class="text-xs text-gray-500">Seleccione su plan y revise sus datos</p>
            </div>
          </div>

          <!-- Plan pricing cards -->
          {#if plans.length > 0}
            <div>
              <h3 class="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-3">Seleccione su plan</h3>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {#each plans as plan}
                  <button
                    class="relative rounded-xl border-2 p-5 text-left transition-all
                      {selectedPlan === plan.name ? 'border-terracotta bg-terracotta/5 shadow-lg' : 'border-border-dark hover:border-gray-500 bg-bg-page'}"
                    on:click={() => selectedPlan = plan.name}
                  >
                    {#if selectedPlan === plan.name}
                      <div class="absolute top-2 right-2 w-5 h-5 rounded-full bg-terracotta flex items-center justify-center">
                        <CheckCircle size={12} class="text-white" />
                      </div>
                    {/if}
                    <h4 class="font-bold text-text-light text-base mb-1">{plan.display_name}</h4>
                    <div class="flex items-baseline gap-1 mb-3">
                      <span class="text-2xl font-bold text-terracotta">${plan.base_price}</span>
                      <span class="text-xs text-gray-500">/{plan.currency === 'usd' ? 'mo' : plan.currency}</span>
                    </div>
                    <ul class="space-y-1.5 text-xs text-gray-400">
                      <li class="flex items-center gap-1.5">
                        <CheckCircle size={10} class="text-emerald-400 flex-shrink-0" />
                        {plan.included_users} usuario{plan.included_users > 1 ? 's' : ''} incluido{plan.included_users > 1 ? 's' : ''}
                      </li>
                      {#if plan.price_per_user > 0}
                        <li class="flex items-center gap-1.5">
                          <CheckCircle size={10} class="text-emerald-400 flex-shrink-0" />
                          +${plan.price_per_user}/usuario extra
                        </li>
                      {/if}
                      <li class="flex items-center gap-1.5">
                        <CheckCircle size={10} class="text-emerald-400 flex-shrink-0" />
                        {plan.max_users === 999 ? 'Usuarios ilimitados' : `Hasta ${plan.max_users} usuarios`}
                      </li>
                      {#each (plan.features || []).slice(0, 3) as feat}
                        <li class="flex items-center gap-1.5">
                          <CheckCircle size={10} class="text-emerald-400 flex-shrink-0" />
                          {feat}
                        </li>
                      {/each}
                    </ul>
                  </button>
                {/each}
              </div>
            </div>
          {/if}

          <!-- Customer TOS -->
          {#if customerTOS.length > 0}
            <div>
              <h3 class="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-3">Términos y Condiciones</h3>
              <div class="space-y-4">
                {#each customerTOS as tos (tos.id)}
                  <div class="border border-border-dark rounded-lg p-4">
                    <SignaturePanel
                      documentTitle={tos.title}
                      htmlPreview={tos.html_content}
                      loading={tosSigningId === tos.id}
                      signed={tosSignedIds.has(tos.id)}
                      on:sign={(e) => handleSignTOS(e, tos.id)}
                    />
                  </div>
                {/each}
              </div>
            </div>
          {/if}

          <!-- Summary card -->
          <div class="bg-bg-page rounded-lg border border-border-dark p-4 space-y-3">
            <h3 class="text-xs font-semibold uppercase tracking-widest text-gray-500">Resumen de Configuración</h3>
            <div class="grid grid-cols-2 gap-2 text-sm">
              <div class="text-gray-500">Nombre:</div>
              <div class="text-text-light">{status?.full_name || profileForm.full_name}</div>
              <div class="text-gray-500">Empresa:</div>
              <div class="text-text-light">{status?.company_name || profileForm.company_name}</div>
              <div class="text-gray-500">Email:</div>
              <div class="text-text-light">{status?.email}</div>
              <div class="text-gray-500">País:</div>
              <div class="text-text-light">{countries.find(c => c.code === (status?.country || profileForm.country))?.name || status?.country}</div>
              <div class="text-gray-500">Plan:</div>
              <div class="text-text-light font-semibold capitalize">{status?.plan || 'Basic'}</div>
              {#if status?.requires_ecf}
                <div class="text-gray-500">e-CF:</div>
                <div class="text-emerald-400 flex items-center gap-1"><Shield size={12} /> Activo — RNC {status.ecf_rnc}</div>
                <div class="text-gray-500">Razón Social:</div>
                <div class="text-text-light">{status.ecf_business_name}</div>
                <div class="text-gray-500">Ambiente:</div>
                <div class="text-text-light">{status.ecf_environment === 'production' ? 'Producción' : 'Pruebas'}</div>
              {/if}
              {#if status?.partner_id}
                <div class="text-gray-500">Referido por:</div>
                <div class="text-blue-400">Partner #{status.partner_id}</div>
              {/if}
            </div>
          </div>

          <div class="flex justify-between">
            <button class="btn-secondary flex items-center gap-2" on:click={() => {
              if (status?.is_dominican) currentStep = 2;
              else currentStep = 1;
            }}>
              <ArrowLeft size={16} /> Atrás
            </button>
            <button class="btn-accent flex items-center gap-2 px-6" on:click={handleComplete} disabled={saving}>
              {#if saving}<Loader2 size={14} class="animate-spin" />{/if}
              <PartyPopper size={16} /> Completar Onboarding
            </button>
          </div>
        </div>
      {/if}
    {/if}
  </div>
</div>
