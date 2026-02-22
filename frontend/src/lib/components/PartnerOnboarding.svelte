<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { Lock, User, CreditCard, CheckCircle, ArrowRight, ArrowLeft, ExternalLink, Loader2, Eye } from 'lucide-svelte';
  import partnerPortalApi from '../api/partnerPortal';
  import type { PartnerOnboardingStatus, PartnerProfile } from '../types';

  export let onboardingStatus: PartnerOnboardingStatus;
  export let profile: PartnerProfile | null = null;

  const dispatch = createEventDispatcher();

  let loading = false;
  let error = '';
  let success = '';

  // viewStep = paso que se muestra en pantalla (puede ir hacia atrás para ver resumen)
  // currentStep = paso actual real (del servidor)
  $: currentStep = onboardingStatus.current_step;
  let viewStep: number = onboardingStatus.current_step;

  // Sync viewStep cuando currentStep avanza
  $: if (currentStep > viewStep) viewStep = currentStep;

  // Step 1: Password (datos guardados al completar para mostrar en resumen)
  let newPassword = '';
  let confirmPassword = '';
  let step1Saved = { done: currentStep > 1 };

  // Step 2: Profile
  let companyName = profile?.company_name || '';
  let legalName = profile?.legal_name || '';
  let taxId = profile?.tax_id || '';
  let contactName = profile?.contact_name || '';
  let phone = profile?.phone || '';
  let country = profile?.country || '';
  let address = profile?.address || '';

  // Snapshot del perfil guardado (para resumen read-only)
  let savedProfile: { company_name: string; contact_name: string; country: string } | null =
    currentStep > 2 && profile
      ? { company_name: profile.company_name, contact_name: profile.contact_name || '', country: profile.country || '' }
      : null;

  // Step 3: Stripe
  let stripeUrl = '';
  let verifying = false;

  const steps = [
    { step: 1, icon: Lock,        label: 'Credenciales' },
    { step: 2, icon: User,        label: 'Perfil'        },
    { step: 3, icon: CreditCard,  label: 'Stripe KYC'   },
    { step: 4, icon: CheckCircle, label: 'Completo'      },
  ];

  // ¿Está el paso visible en modo lectura (completado, navegando hacia atrás)?
  $: isReadOnly = viewStep < currentStep;

  function resetMessages() { error = ''; success = ''; }

  /** Navega al paso (solo si ya fue completado o es el actual) */
  function goToStep(s: number) {
    if (s > currentStep) return; // No se puede saltar adelante
    resetMessages();
    viewStep = s;
  }

  /** Retrocede al paso anterior en modo lectura */
  function goBack() {
    if (viewStep > 1) {
      resetMessages();
      viewStep -= 1;
    }
  }

  /** Avanza al paso actual (salir de modo lectura) */
  function goToCurrentStep() {
    resetMessages();
    viewStep = currentStep;
  }

  // ─── Paso 1: establecer contraseña ───────────────────────────────────────

  async function handleSetPassword() {
    resetMessages();
    if (newPassword.length < 8) { error = 'La contraseña debe tener al menos 8 caracteres'; return; }
    if (newPassword !== confirmPassword) { error = 'Las contraseñas no coinciden'; return; }
    loading = true;
    try {
      const result = await partnerPortalApi.setPassword(newPassword, confirmPassword);
      success = result.message;
      onboardingStatus.current_step = result.onboarding_step;
      onboardingStatus.steps[0].completed = true;
      onboardingStatus.steps[1].completed = result.onboarding_step >= 2;
      step1Saved = { done: true };
      newPassword = '';
      confirmPassword = '';
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error al cambiar la contraseña';
    } finally {
      loading = false;
    }
  }

  // ─── Paso 2: perfil ───────────────────────────────────────────────────────

  async function handleUpdateProfile() {
    resetMessages();
    if (!companyName.trim()) { error = 'El nombre de empresa es requerido'; return; }
    loading = true;
    try {
      const result = await partnerPortalApi.updateProfile({
        company_name: companyName,
        legal_name: legalName || null,
        tax_id: taxId || null,
        contact_name: contactName || null,
        phone: phone || null,
        country: country || null,
        address: address || null,
      });
      success = result.message;
      onboardingStatus.current_step = result.onboarding_step;
      onboardingStatus.steps[1].completed = true;
      onboardingStatus.steps[2].completed = result.onboarding_step >= 3;
      savedProfile = { company_name: companyName, contact_name: contactName, country: country };
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error al actualizar el perfil';
    } finally {
      loading = false;
    }
  }

  // ─── Paso 3: Stripe ───────────────────────────────────────────────────────

  async function handleStartStripe() {
    resetMessages();
    loading = true;
    try {
      const result = await partnerPortalApi.startStripe();
      if (result.onboarding_url) {
        stripeUrl = result.onboarding_url;
        window.open(result.onboarding_url, '_blank');
        success = 'Redirigiendo a Stripe para completar KYC...';
      } else {
        error = 'No se pudo generar el link de onboarding';
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error al crear cuenta Stripe';
    } finally {
      loading = false;
    }
  }

  async function handleVerifyStripe() {
    resetMessages();
    verifying = true;
    try {
      const result = await partnerPortalApi.verifyStripe();
      if (result.onboarding_complete) {
        success = '¡KYC completado! Tu cuenta Stripe está activa.';
        onboardingStatus.current_step = 4;
        onboardingStatus.steps[2].completed = true;
        onboardingStatus.steps[3].completed = true;
        onboardingStatus.stripe_onboarding_complete = true;
        onboardingStatus.stripe_charges_enabled = result.charges_enabled;
      } else {
        error = 'El KYC de Stripe aún no está completo. Revisa tu email o completa los pasos pendientes.';
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error al verificar Stripe';
    } finally {
      verifying = false;
    }
  }

  async function handleSkipStripe() {
    resetMessages();
    loading = true;
    try {
      await partnerPortalApi.skipStripe();
      onboardingStatus.current_step = 4;
      onboardingStatus.steps[3].completed = true;
      success = 'Onboarding completado. Podrás configurar Stripe después.';
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error';
    } finally {
      loading = false;
    }
  }

  function handleComplete() { dispatch('complete'); }
</script>

<div class="min-h-screen bg-[#F5F3EF] flex flex-col items-center justify-center p-6">
  <div class="w-full max-w-2xl">

    <!-- Header -->
    <div class="text-center mb-8">
      <div class="w-12 h-12 rounded bg-[#C05A3C] flex items-center justify-center mx-auto mb-4">
        <span class="text-white font-bold text-xl">S</span>
      </div>
      <h1 class="text-2xl font-bold text-[#1a1a1a] tracking-tight">Bienvenido al Portal de Partners</h1>
      <p class="text-sm text-gray-500 mt-1">Completa estos pasos para activar tu cuenta</p>
    </div>

    <!-- Stepper (clickeable en pasos completados) -->
    <div class="flex items-center justify-center gap-0 mb-8">
      {#each steps as s, i}
        <div class="flex items-center">
          <div class="flex flex-col items-center">
            <button
              class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all
                {currentStep > s.step
                  ? 'bg-[#4A7C59] text-white shadow-md cursor-pointer hover:bg-[#3d6a4b] ring-2 ring-offset-2 ring-transparent hover:ring-[#4A7C59]'
                  : currentStep === s.step
                    ? 'bg-[#C05A3C] text-white shadow-md cursor-default'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'}
                {viewStep === s.step && currentStep !== s.step ? 'ring-2 ring-offset-2 ring-[#4A7C59]' : ''}"
              on:click={() => goToStep(s.step)}
              disabled={s.step > currentStep}
              title={s.step < currentStep ? 'Ver paso completado' : s.step === currentStep ? 'Paso actual' : 'Paso bloqueado'}
            >
              {#if currentStep > s.step}
                <CheckCircle class="w-5 h-5" />
              {:else}
                <svelte:component this={s.icon} class="w-4 h-4" />
              {/if}
            </button>
            <span class="text-[10px] font-semibold uppercase tracking-wider mt-1.5
              {currentStep >= s.step ? 'text-[#1a1a1a]' : 'text-gray-400'}">
              {s.label}
            </span>
          </div>
          {#if i < steps.length - 1}
            <div class="w-12 h-0.5 mx-2 mt-[-16px]
              {currentStep > s.step ? 'bg-[#4A7C59]' : 'bg-gray-200'}"></div>
          {/if}
        </div>
      {/each}
    </div>

    <!-- Alerta modo lectura -->
    {#if isReadOnly}
      <div class="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm text-blue-700 mb-4">
        <Eye class="w-4 h-4 flex-shrink-0" />
        <span>Estás viendo un paso completado — <strong>solo lectura</strong>.</span>
        <button
          class="ml-auto text-[#C05A3C] font-semibold hover:underline text-xs whitespace-nowrap"
          on:click={goToCurrentStep}
        >
          Ir al paso actual →
        </button>
      </div>
    {/if}

    <!-- Mensajes -->
    {#if error}
      <div class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 mb-4">{error}</div>
    {/if}
    {#if success}
      <div class="rounded border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700 mb-4">{success}</div>
    {/if}

    <!-- Tarjeta del paso -->
    <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-8">

      <!-- ── PASO 1 ── -->
      {#if viewStep === 1}
        {#if isReadOnly}
          <!-- Paso 1 completado: vista read-only -->
          <div class="flex items-center gap-3 mb-4">
            <div class="w-8 h-8 rounded-full bg-[#4A7C59] flex items-center justify-center flex-shrink-0">
              <CheckCircle class="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 class="text-lg font-bold text-[#1a1a1a]">Credenciales establecidas</h2>
              <p class="text-xs text-[#4A7C59] font-semibold">✓ Paso completado</p>
            </div>
          </div>
          <div class="rounded-lg border border-gray-100 bg-gray-50 p-4">
            <p class="text-sm text-gray-600">
              Tu contraseña de acceso al portal ya está configurada.
              Por seguridad no se muestra aquí.
            </p>
            <p class="text-xs text-gray-400 mt-2">
              Puedes cambiar tu contraseña más adelante desde la configuración de perfil.
            </p>
          </div>
        {:else}
          <!-- Paso 1 activo: formulario -->
          <h2 class="text-lg font-bold text-[#1a1a1a] mb-1">Establece tu contraseña</h2>
          <p class="text-sm text-gray-500 mb-6">Crea una contraseña segura para acceder al portal</p>
          <div class="space-y-4">
            <div>
              <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1.5">
                Nueva Contraseña
              </label>
              <input
                type="password"
                bind:value={newPassword}
                class="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none"
                placeholder="Mínimo 8 caracteres"
              />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1.5">
                Confirmar Contraseña
              </label>
              <input
                type="password"
                bind:value={confirmPassword}
                class="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none"
                placeholder="Repetir contraseña"
              />
            </div>
            <button
              class="w-full bg-[#C05A3C] text-white font-semibold py-2.5 rounded-lg hover:bg-[#a94e33] transition-colors flex items-center justify-center gap-2 text-sm disabled:opacity-60"
              on:click={handleSetPassword}
              disabled={loading}
            >
              {#if loading}<Loader2 class="w-4 h-4 animate-spin" />{/if}
              Continuar
              <ArrowRight class="w-4 h-4" />
            </button>
          </div>
        {/if}

      <!-- ── PASO 2 ── -->
      {:else if viewStep === 2}
        {#if isReadOnly}
          <!-- Paso 2 completado: vista read-only -->
          <div class="flex items-center gap-3 mb-4">
            <div class="w-8 h-8 rounded-full bg-[#4A7C59] flex items-center justify-center flex-shrink-0">
              <CheckCircle class="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 class="text-lg font-bold text-[#1a1a1a]">Perfil completado</h2>
              <p class="text-xs text-[#4A7C59] font-semibold">✓ Paso completado</p>
            </div>
          </div>
          <div class="rounded-lg border border-gray-100 bg-gray-50 p-4 space-y-3">
            {#if savedProfile}
              <div class="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">Empresa</span>
                  <p class="text-[#1a1a1a] font-medium">{savedProfile.company_name || companyName || '—'}</p>
                </div>
                <div>
                  <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">Contacto</span>
                  <p class="text-[#1a1a1a]">{savedProfile.contact_name || contactName || '—'}</p>
                </div>
                <div>
                  <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">País</span>
                  <p class="text-[#1a1a1a]">{savedProfile.country || country || '—'}</p>
                </div>
              </div>
            {:else}
              <p class="text-sm text-gray-600">Perfil comercial guardado correctamente.</p>
            {/if}
          </div>
        {:else}
          <!-- Paso 2 activo: formulario -->
          <h2 class="text-lg font-bold text-[#1a1a1a] mb-1">Completa tu perfil comercial</h2>
          <p class="text-sm text-gray-500 mb-6">Esta información se usará para contratos y facturación</p>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="sm:col-span-2">
              <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1.5">Empresa *</label>
              <input type="text" bind:value={companyName}
                class="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1.5">Razón Social</label>
              <input type="text" bind:value={legalName}
                class="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1.5">RNC / Tax ID</label>
              <input type="text" bind:value={taxId}
                class="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1.5">Contacto</label>
              <input type="text" bind:value={contactName}
                class="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1.5">Teléfono</label>
              <input type="text" bind:value={phone}
                class="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1.5">País</label>
              <input type="text" bind:value={country}
                class="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1.5">Dirección</label>
              <input type="text" bind:value={address}
                class="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
            </div>
          </div>
          <div class="flex gap-3 mt-6">
            <button
              class="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 transition-colors px-4 py-2.5 border border-gray-200 rounded-lg"
              on:click={goBack}
            >
              <ArrowLeft class="w-4 h-4" /> Atrás
            </button>
            <button
              class="flex-1 bg-[#C05A3C] text-white font-semibold py-2.5 rounded-lg hover:bg-[#a94e33] transition-colors flex items-center justify-center gap-2 text-sm disabled:opacity-60"
              on:click={handleUpdateProfile}
              disabled={loading}
            >
              {#if loading}<Loader2 class="w-4 h-4 animate-spin" />{/if}
              Guardar y continuar
              <ArrowRight class="w-4 h-4" />
            </button>
          </div>
        {/if}

      <!-- ── PASO 3 ── -->
      {:else if viewStep === 3}
        {#if isReadOnly}
          <!-- Paso 3 completado: vista read-only -->
          <div class="flex items-center gap-3 mb-4">
            <div class="w-8 h-8 rounded-full bg-[#4A7C59] flex items-center justify-center flex-shrink-0">
              <CheckCircle class="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 class="text-lg font-bold text-[#1a1a1a]">Stripe KYC completado</h2>
              <p class="text-xs text-[#4A7C59] font-semibold">✓ Paso completado</p>
            </div>
          </div>
          <div class="rounded-lg border border-gray-100 bg-gray-50 p-4">
            {#if onboardingStatus.stripe_onboarding_complete}
              <p class="text-sm text-gray-600">
                ✅ Tu cuenta Stripe Connect está verificada y activa.
                Puedes recibir pagos automáticos.
              </p>
            {:else}
              <p class="text-sm text-amber-700">
                ⚠️ Stripe fue omitido. Puedes configurarlo desde el portal.
              </p>
            {/if}
          </div>
        {:else}
          <!-- Paso 3 activo: formulario -->
          <h2 class="text-lg font-bold text-[#1a1a1a] mb-1">Conecta tu cuenta Stripe</h2>
          <p class="text-sm text-gray-500 mb-6">
            Para recibir pagos y comisiones, necesitas completar la verificación KYC de Stripe Connect.
            Este paso asegura el split automático de ingresos 50/50.
          </p>
          <div class="space-y-4">
            {#if !stripeUrl}
              <div class="rounded-lg border border-blue-100 bg-blue-50 p-4">
                <p class="text-sm text-blue-800">
                  <strong>¿Qué es esto?</strong> Stripe Connect te permite recibir pagos directamente.
                  Cuando tus clientes paguen, el ingreso se divide automáticamente entre tu cuenta y Jeturing.
                </p>
              </div>
              <button
                class="w-full bg-[#635BFF] text-white font-semibold py-2.5 rounded-lg hover:bg-[#5851e0] transition-colors flex items-center justify-center gap-2 text-sm disabled:opacity-60"
                on:click={handleStartStripe}
                disabled={loading}
              >
                {#if loading}<Loader2 class="w-4 h-4 animate-spin" />{/if}
                <CreditCard class="w-4 h-4" />
                Conectar con Stripe
              </button>
            {:else}
              <div class="rounded-lg border border-amber-100 bg-amber-50 p-4">
                <p class="text-sm text-amber-800">
                  Se abrió una ventana de Stripe. Completa los pasos allí y luego vuelve aquí para verificar.
                </p>
                <a href={stripeUrl} target="_blank" rel="noreferrer"
                  class="text-sm text-[#635BFF] hover:underline flex items-center gap-1 mt-2">
                  <ExternalLink class="w-3 h-3" />
                  Abrir Stripe nuevamente
                </a>
              </div>
              <button
                class="w-full bg-[#4A7C59] text-white font-semibold py-2.5 rounded-lg hover:bg-[#3d6a4b] transition-colors flex items-center justify-center gap-2 text-sm disabled:opacity-60"
                on:click={handleVerifyStripe}
                disabled={verifying}
              >
                {#if verifying}<Loader2 class="w-4 h-4 animate-spin" />{/if}
                <CheckCircle class="w-4 h-4" />
                Verificar KYC completado
              </button>
            {/if}
            <div class="flex gap-3">
              <button
                class="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 transition-colors px-4 py-2 border border-gray-200 rounded-lg"
                on:click={goBack}
              >
                <ArrowLeft class="w-4 h-4" /> Atrás
              </button>
              <button
                class="flex-1 text-gray-500 text-sm hover:text-gray-700 transition-colors py-2"
                on:click={handleSkipStripe}
              >
                Saltar (configurar después)
              </button>
            </div>
          </div>
        {/if}

      <!-- ── PASO 4: Completo ── -->
      {:else}
        <div class="text-center py-6">
          <div class="w-16 h-16 rounded-full bg-[#4A7C59] flex items-center justify-center mx-auto mb-4">
            <CheckCircle class="w-8 h-8 text-white" />
          </div>
          <h2 class="text-xl font-bold text-[#1a1a1a] mb-2">¡Onboarding completado!</h2>
          <p class="text-sm text-gray-500 mb-6">
            Tu cuenta de partner está lista. Ya puedes gestionar leads, clientes y comisiones desde tu portal.
          </p>
          {#if !onboardingStatus.stripe_onboarding_complete}
            <div class="rounded-lg border border-amber-100 bg-amber-50 p-3 text-sm text-amber-700 mb-6">
              ⚠️ Recuerda completar la verificación de Stripe para recibir pagos automáticos.
            </div>
          {/if}
          <button
            class="bg-[#C05A3C] text-white font-semibold px-8 py-2.5 rounded-lg hover:bg-[#a94e33] transition-colors flex items-center justify-center gap-2 text-sm mx-auto"
            on:click={handleComplete}
          >
            Entrar al Portal
            <ArrowRight class="w-4 h-4" />
          </button>
        </div>
      {/if}

    </div>

    <!-- Botones de navegación inferior (cuando está en modo lectura y no es el paso 4) -->
    {#if isReadOnly && viewStep < 4}
      <div class="flex justify-between mt-4">
        <button
          class="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 transition-colors"
          on:click={goBack}
          disabled={viewStep <= 1}
        >
          {#if viewStep > 1}<ArrowLeft class="w-4 h-4" /> Paso anterior{/if}
        </button>
        <button
          class="flex items-center gap-1.5 text-sm text-[#C05A3C] hover:text-[#a94e33] font-semibold transition-colors"
          on:click={goToCurrentStep}
        >
          Ir al paso actual <ArrowRight class="w-4 h-4" />
        </button>
      </div>
    {/if}

  </div>
</div>
