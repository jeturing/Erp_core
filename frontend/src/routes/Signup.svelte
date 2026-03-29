<script lang="ts">
  import { onMount } from 'svelte';
  import {
    Loader2,
    ArrowLeft,
    CheckCircle,
    Building2,
    Calculator,
    Handshake,
    ShieldCheck,
    Zap,
    Star,
    ChevronDown,
    ChevronUp,
    ArrowRight,
    Clock,
    BadgeCheck,
    Lock,
  } from 'lucide-svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';

  type Mode = 'landing' | 'tenant' | 'partner' | 'accountant';
  let mode = $state<Mode>('landing');

  let tenantLoading = $state(false);
  let tenantError = $state('');
  let loadingPlans = $state(true);
  let plans = $state<any[]>([]);
  let tenantForm = $state({
    full_name: '',
    email: '',
    company_name: '',
    subdomain: '',
    plan: 'pro',
    user_count: 1,
    billing_period: 'monthly',
  });

  let partnerLoading = $state(false);
  let partnerSuccess = $state(false);
  let partnerError = $state('');
  let partnerForm = $state({
    company_name: '',
    contact_name: '',
    contact_email: '',
    phone: '',
    country: 'DO',
    password: '',
    password_confirm: '',
  });

  let openFaq = $state<number | null>(null);

  const faqs = [
    {
      q: 'Cuanto tarda en activarse mi cuenta?',
      a: 'Tu instancia Sajet se provisiona automaticamente en minutos una vez confirmado el pago. Recibiras un email con las credenciales.',
    },
    {
      q: 'Puedo cambiar de plan despues?',
      a: 'Si, puedes cambiar de plan en cualquier momento desde el portal de cliente. Los cambios aplican al siguiente ciclo de facturacion.',
    },
    {
      q: 'Que significa que el partner queda pendiente de validacion?',
      a: 'Al registrarte como partner, nuestro equipo revisa tu solicitud para confirmar que cumples los requisitos del programa. La validacion toma 24-48 horas habiles. No se activa ningun cobro hasta aprobar.',
    },
    {
      q: 'Como funciona la comision para partners?',
      a: 'Los partners certificados reciben el 50% de los ingresos netos de cada cliente referido, pagado mensualmente via Stripe Connect.',
    },
    {
      q: 'Puedo empezar sin saber que ruta elegir?',
      a: 'Si. La portada de alta te permite comparar empresa, firma contable y partner antes de entrar al formulario correcto.',
    },
  ];

  const benefits = [
    { icon: Zap, title: 'Activa en minutos', desc: 'Provisioning automatico. Tu Sajet listo en menos de 5 minutos.' },
    { icon: ShieldCheck, title: 'Datos seguros', desc: 'Base de datos aislada por tenant. Cumplimiento y operacion separada por cliente.' },
    { icon: CheckCircle, title: 'Flujos claros', desc: 'Cada tipo de usuario entra por su onboarding correcto desde el primer clic.' },
    { icon: Star, title: 'Soporte LATAM', desc: 'Acompanamiento comercial y tecnico en espanol para toda la region.' },
  ];

  const launchPaths: Array<{
    mode: Mode;
    icon: typeof Building2;
    kicker: string;
    title: string;
    desc: string;
    points: string[];
    featured?: boolean;
  }> = [
    {
      mode: 'tenant',
      icon: Building2,
      kicker: 'Cliente / Empresa',
      title: 'Abrir mi empresa en SAJET',
      desc: 'Crea tu instancia Sajet, elige plan y sal a produccion con dominio propio y checkout en Stripe.',
      points: ['Instancia dedicada', 'Dominio .sajet.us', 'Activacion inmediata'],
      featured: true,
    },
    {
      mode: 'accountant',
      icon: Calculator,
      kicker: 'Contador / Firma',
      title: 'Centralizar clientes contables',
      desc: 'Activa un workspace para tu firma y entra al modelo multi-cliente con un recorrido pensado para despachos.',
      points: ['Ruta multi-cliente', 'Branding de firma', 'Alta contable guiada'],
    },
    {
      mode: 'partner',
      icon: Handshake,
      kicker: 'Socio / Partner',
      title: 'Revender y cobrar comisiones',
      desc: 'Solicita acceso al programa de partners con portal, acuerdos, validacion y dispersion posterior por Stripe.',
      points: ['Comisiones recurrentes', 'White-label', 'Validacion del equipo SAJET'],
    },
  ];

  const activationSteps = [
    'Eliges la ruta correcta: empresa, firma contable o socio.',
    'Completas tus datos y definimos el espacio inicial.',
    'Stripe procesa el alta y SAJET prepara tu entorno operativo.',
  ];

  const tenantBenefits = [
    'ERP completo con ventas, compras, inventario, CRM y contabilidad.',
    'Tu subdominio .sajet.us se reserva desde el alta.',
    'Checkout con Stripe y aprovisionamiento inmediato despues del pago.',
  ];

  const accountantBenefits = [
    'Espacio preparado para operacion multi-cliente y trabajo contable continuo.',
    'Onboarding alineado a firma contable y acceso centralizado.',
    'La activacion usa la misma base de SAJET con copy y recorrido especifico para despacho.',
  ];

  function sanitizeSubdomain(v: string) {
    return v.toLowerCase().replace(/[^a-z0-9-]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
  }

  async function loadPlans() {
    try {
      const res = await fetch('/api/public/plans');
      const data = await res.json();
      plans = data.plans || [];
      if (plans.length > 0) {
        tenantForm.plan = plans.find((p: any) => p.name === 'pro')?.name || plans[0].name;
      }
    } catch {
      // silent
    } finally {
      loadingPlans = false;
    }
  }

  async function handleTenantSubmit(e: Event) {
    e.preventDefault();
    tenantError = '';
    tenantForm.subdomain = sanitizeSubdomain(tenantForm.subdomain);

    if (!tenantForm.full_name || !tenantForm.email || !tenantForm.company_name || !tenantForm.subdomain) {
      tenantError = 'Complete todos los campos obligatorios';
      return;
    }
    if (tenantForm.subdomain.length < 3) {
      tenantError = 'El subdominio debe tener al menos 3 caracteres';
      return;
    }

    tenantLoading = true;
    try {
      const res = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...tenantForm,
          is_accountant: mode === 'accountant',
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || 'Error al procesar registro');
      if (data?.checkout_url) {
        window.location.href = data.checkout_url;
        return;
      }
      throw new Error('No se recibio URL de checkout');
    } catch (err: any) {
      tenantError = err?.message || 'Error procesando registro';
    } finally {
      tenantLoading = false;
    }
  }

  async function handlePartnerSubmit(e: Event) {
    e.preventDefault();
    partnerError = '';
    if (!partnerForm.company_name || !partnerForm.contact_name || !partnerForm.contact_email || !partnerForm.password) {
      partnerError = 'Complete los campos obligatorios';
      return;
    }
    if (partnerForm.password.length < 8) {
      partnerError = 'La contrasena debe tener al menos 8 caracteres';
      return;
    }
    if (partnerForm.password !== partnerForm.password_confirm) {
      partnerError = 'Las contrasenas no coinciden';
      return;
    }

    partnerLoading = true;
    try {
      const res = await fetch('/api/public/partner-signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_name: partnerForm.company_name,
          contact_name: partnerForm.contact_name,
          contact_email: partnerForm.contact_email,
          phone: partnerForm.phone || undefined,
          country: partnerForm.country || undefined,
          password: partnerForm.password,
          billing_scenario: 'jeturing_collects',
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || 'Error al crear cuenta de partner');
      partnerSuccess = true;
    } catch (err: any) {
      partnerError = err?.message || 'Error al crear cuenta';
    } finally {
      partnerLoading = false;
    }
  }

  const isAccountantFlow = $derived(mode === 'accountant');
  const activeWorkspaceTitle = $derived(isAccountantFlow ? 'Crear espacio para tu firma contable' : 'Crear tu empresa en SAJET');
  const activeWorkspaceSubtitle = $derived(
    isAccountantFlow
    ? 'Este flujo prepara un workspace multi-cliente para tu firma y conserva el onboarding financiero dentro de SAJET.'
    : 'Completa los datos y continua al checkout seguro para provisionar tu instancia.'
  );
  const activeWorkspaceLabel = $derived(isAccountantFlow ? 'Firma contable *' : 'Empresa *');
  const activeSubmitLabel = $derived(isAccountantFlow ? 'Continuar con activacion contable' : 'Continuar a pago seguro');
  const activeSupportCopy = $derived(
    isAccountantFlow
    ? 'Stripe procesa el alta y SAJET deja tu workspace listo para operar clientes.'
    : 'Pago procesado de forma segura por Stripe sin guardar datos de tarjeta.'
  );
  const activeBenefits = $derived(isAccountantFlow ? accountantBenefits : tenantBenefits);
  const activeSubdomainPlaceholder = $derived(isAccountantFlow ? 'firma-contable' : 'miempresa');
  const activeNameLabel = $derived(isAccountantFlow ? 'Responsable principal *' : 'Nombre completo *');
  const activeUsersLabel = $derived(isAccountantFlow ? 'Miembros base' : 'Usuarios');
  const activeSubdomainLabel = $derived(isAccountantFlow ? 'Espacio / Subdominio *' : 'Subdominio *');

  onMount(async () => {
    try {
      const params = $page.url.searchParams;
      const m = params.get('mode');
      const role = params.get('role');
      if (m === 'partner') mode = 'partner';
      else if (m === 'tenant') mode = 'tenant';
      else if (m === 'accountant') mode = 'accountant';
      else if (role === 'accountant') mode = 'accountant';

      const plan = params.get('plan');
      const users = Number(params.get('users') || '1');
      const billing = params.get('billing');
      if (plan) tenantForm.plan = plan;
      if (users > 0) tenantForm.user_count = users;
      if (billing === 'annual' || billing === 'monthly') tenantForm.billing_period = billing;
    } catch {
      // no-op
    }
    await loadPlans();
  });
</script>

{#if mode === 'landing'}
  <div class="min-h-screen bg-[#F5F3EF]">
    <nav class="sticky top-0 z-30 bg-[#F5F3EF]/95 backdrop-blur border-b border-[#D1CCC4]">
      <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between gap-6">
        <a href="/" class="flex items-center gap-2.5">
          <div class="w-7 h-7 bg-[#003B73] flex items-center justify-center">
            <span class="text-white font-bold text-xs">S</span>
          </div>
          <span class="font-bold text-[#1a1a1a] text-sm tracking-wide uppercase">Sajet ERP</span>
        </a>

        <div class="hidden md:flex items-center gap-6 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-500">
          <button type="button" class="hover:text-[#003B73] transition-colors" onclick={() => (mode = 'tenant')}>Clientes</button>
          <button type="button" class="hover:text-[#003B73] transition-colors" onclick={() => (mode = 'accountant')}>Contadores</button>
          <button type="button" class="hover:text-[#003B73] transition-colors" onclick={() => (mode = 'partner')}>Socios</button>
        </div>

        <div class="flex items-center gap-3">
          <a href="/login" class="text-sm text-gray-500 hover:text-[#1a1a1a] transition-colors hidden sm:block">Iniciar sesion</a>
          <button
            type="button"
            onclick={() => (mode = 'tenant')}
            class="bg-[#003B73] text-white text-xs font-bold uppercase tracking-widest px-5 py-2.5 hover:bg-[#002a55] transition-colors"
          >
            Crear empresa
          </button>
        </div>
      </div>
    </nav>

    <section class="max-w-6xl mx-auto px-6 pt-16 pb-16 grid lg:grid-cols-[1.2fr_0.8fr] gap-10 items-start">
      <div>
        <div class="inline-flex items-center gap-2 bg-[#003B73]/10 text-[#003B73] text-xs font-semibold uppercase tracking-widest px-4 py-2 mb-8">
          <Star size={12} /> ERP cloud multi-tenant para LATAM
        </div>
        <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-[#1a1a1a] leading-tight mb-6">
          Elige tu entrada a SAJET y
          <br />
          <span class="text-[#003B73]">arranca con una ruta clara.</span>
        </h1>
        <p class="text-lg text-gray-500 max-w-2xl mb-8 leading-relaxed">
          Empresas, firmas contables y socios no deberian caer en el mismo formulario sin contexto.
          Aqui eliges tu modalidad y continuas con un onboarding hecho para ese recorrido.
        </p>
        <div class="flex flex-col sm:flex-row gap-4 mb-6">
          <button
            type="button"
            onclick={() => (mode = 'tenant')}
            class="bg-[#003B73] text-white font-bold uppercase tracking-widest text-sm px-8 py-4 hover:bg-[#002a55] transition-colors inline-flex items-center justify-center gap-2"
          >
            Crear mi empresa <ArrowRight size={16} />
          </button>
          <button
            type="button"
            onclick={() => (mode = 'accountant')}
            class="border-2 border-[#003B73] text-[#003B73] font-bold uppercase tracking-widest text-sm px-8 py-4 hover:bg-[#003B73]/5 transition-colors inline-flex items-center justify-center gap-2"
          >
            <Calculator size={16} /> Soy contador
          </button>
        </div>
        <p class="text-xs text-gray-400">
          Checkout, activacion y dispersion financiera se alinean con tu modelo operativo.
        </p>
      </div>

      <div class="bg-[#1C1C1C] text-white p-8 lg:p-9">
        <p class="text-[11px] font-bold uppercase tracking-[0.24em] text-white/60 mb-4">Ruta guiada</p>
        <h2 class="text-2xl font-bold leading-tight mb-4">No es solo un alta: es el inicio del flujo correcto.</h2>
        <p class="text-sm text-white/70 leading-relaxed mb-6">
          SAJET usa una misma base operativa, pero cambia la experiencia segun si vas a crear una empresa,
          trabajar como firma contable o entrar como socio comercial.
        </p>
        <div class="space-y-4">
          {#each activationSteps as step, index}
            <div class="flex gap-3 items-start">
              <span class="w-7 h-7 bg-white/10 text-white text-[11px] font-bold flex items-center justify-center shrink-0">{index + 1}</span>
              <p class="text-sm text-white/80 leading-relaxed">{step}</p>
            </div>
          {/each}
        </div>
      </div>
    </section>

    <section class="max-w-6xl mx-auto px-6 pb-16">
      <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {#each benefits as b}
          <div class="bg-white border border-[#D1CCC4] p-6">
            <div class="w-10 h-10 bg-[#003B73]/10 flex items-center justify-center mb-4">
              <svelte:component this={b.icon} size={20} class="text-[#003B73]" />
            </div>
            <h3 class="font-bold text-sm text-[#1a1a1a] mb-1">{b.title}</h3>
            <p class="text-xs text-gray-500 leading-relaxed">{b.desc}</p>
          </div>
        {/each}
      </div>
    </section>

    <section class="max-w-6xl mx-auto px-6 pb-20">
      <h2 class="text-2xl font-bold text-center text-[#1a1a1a] mb-3">Como quieres empezar?</h2>
      <p class="text-center text-sm text-gray-500 mb-10">Elige el camino que mejor se adapta a tu caso</p>
      <div class="grid lg:grid-cols-3 gap-6">
        {#each launchPaths as path}
          <div class={`${path.featured ? 'bg-white border-2 border-[#003B73]' : 'bg-white border border-[#D1CCC4]'} p-8`}>
            <p class="text-[11px] font-bold uppercase tracking-[0.22em] text-gray-400 mb-4">{path.kicker}</p>
            <div class={`w-12 h-12 flex items-center justify-center mb-5 ${path.featured ? 'bg-[#003B73]/10' : 'bg-[#E8E4DC]'}`}>
              <svelte:component this={path.icon} size={24} class="text-[#003B73]" />
            </div>
            <h3 class="text-xl font-bold text-[#1a1a1a] mb-2">{path.title}</h3>
            <p class="text-sm text-gray-500 mb-5 leading-relaxed">{path.desc}</p>
            <ul class="space-y-2 mb-6">
              {#each path.points as item}
                <li class="flex items-center gap-2 text-sm text-[#1a1a1a]">
                  <CheckCircle size={14} class={`${path.featured ? 'text-[#003B73]' : 'text-gray-300'} shrink-0`} />
                  {item}
                </li>
              {/each}
            </ul>
            <button
              type="button"
              onclick={() => (mode = path.mode)}
              class={`w-full font-bold uppercase tracking-widest text-xs py-3.5 transition-colors ${path.featured ? 'bg-[#003B73] text-white hover:bg-[#002a55]' : 'border-2 border-[#003B73] text-[#003B73] hover:bg-[#003B73]/5'}`}
            >
              {path.mode === 'partner' ? 'Solicitar acceso' : 'Elegir esta ruta'}
            </button>
          </div>
        {/each}
      </div>
    </section>

    <section class="max-w-3xl mx-auto px-6 pb-20">
      <h2 class="text-2xl font-bold text-center text-[#1a1a1a] mb-10">Preguntas frecuentes</h2>
      <div class="space-y-2">
        {#each faqs as faq, i}
          <div class="bg-white border border-[#D1CCC4]">
            <button
              type="button"
              class="w-full flex items-center justify-between px-5 py-4 text-left gap-4"
              onclick={() => (openFaq = openFaq === i ? null : i)}
            >
              <span class="text-sm font-semibold text-[#1a1a1a]">{faq.q}</span>
              {#if openFaq === i}
                <ChevronUp size={16} class="text-gray-400 shrink-0" />
              {:else}
                <ChevronDown size={16} class="text-gray-400 shrink-0" />
              {/if}
            </button>
            {#if openFaq === i}
              <div class="px-5 pb-4 pt-3 text-sm text-gray-500 leading-relaxed border-t border-[#D1CCC4]">
                {faq.a}
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </section>

    <footer class="border-t border-[#D1CCC4] py-10">
      <div class="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <div class="w-6 h-6 bg-[#003B73] flex items-center justify-center">
            <span class="text-white font-bold text-[10px]">S</span>
          </div>
          <span class="text-xs text-gray-400 uppercase tracking-widest font-bold">Sajet ERP · Jeturing</span>
        </div>
        <div class="flex items-center gap-4 text-xs text-gray-400">
          <span class="flex items-center gap-1"><Lock size={11} /> SSL · Datos cifrados</span>
          <span class="flex items-center gap-1"><ShieldCheck size={11} /> Operacion separada por flujo</span>
          <a href="/login" class="hover:text-[#003B73] transition-colors">Iniciar sesion</a>
        </div>
      </div>
    </footer>
  </div>
{:else if mode === 'tenant' || mode === 'accountant'}
  <div class="min-h-screen bg-[#F5F3EF] p-6">
    <div class="max-w-6xl mx-auto space-y-5">
      <div class="flex items-center justify-between">
        <button
          type="button"
          class="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-[#1a1a1a] transition-colors"
          onclick={() => (mode = 'landing')}
        >
          <ArrowLeft size={14} /> Volver
        </button>
        <a href="/login" class="text-sm text-[#C05A3C] hover:underline">Ya tengo cuenta</a>
      </div>

      <div class="grid lg:grid-cols-[0.88fr_1.12fr] gap-8 items-start">
        <aside class="space-y-5">
          <div class="bg-[#1C1C1C] text-white p-8">
            <p class="text-[11px] font-bold uppercase tracking-[0.22em] text-white/60 mb-4">
              {isAccountantFlow ? 'Flujo contable' : 'Flujo empresa'}
            </p>
            <h1 class="text-3xl font-bold leading-tight mb-4">{activeWorkspaceTitle}</h1>
            <p class="text-sm text-white/75 leading-relaxed mb-6">{activeWorkspaceSubtitle}</p>
            <div class="space-y-3">
              {#each activeBenefits as benefit}
                <div class="flex items-start gap-3">
                  <CheckCircle size={16} class="text-white/80 shrink-0 mt-0.5" />
                  <p class="text-sm text-white/78 leading-relaxed">{benefit}</p>
                </div>
              {/each}
            </div>
          </div>

          <div class="bg-white border border-[#D1CCC4] p-6">
            <p class="text-[11px] font-bold uppercase tracking-[0.22em] text-gray-400 mb-4">Que pasa despues</p>
            <div class="space-y-3">
              {#each activationSteps as step, index}
                <div class="flex items-start gap-3">
                  <span class="w-6 h-6 bg-[#003B73] text-white text-[10px] font-bold flex items-center justify-center shrink-0">{index + 1}</span>
                  <p class="text-sm text-gray-600 leading-relaxed">{step}</p>
                </div>
              {/each}
            </div>
          </div>
        </aside>

        <div class="bg-white border border-[#D1CCC4] p-8">
          <div class="flex items-center gap-3 mb-5">
            <div class="w-10 h-10 bg-[#003B73]/10 flex items-center justify-center">
              {#if isAccountantFlow}
                <Calculator size={20} class="text-[#003B73]" />
              {:else}
                <Building2 size={20} class="text-[#003B73]" />
              {/if}
            </div>
            <div>
              <h1 class="text-xl font-bold text-[#1a1a1a]">{activeWorkspaceTitle}</h1>
              <p class="text-xs text-gray-500">{activeWorkspaceSubtitle}</p>
            </div>
          </div>

          <div class="grid sm:grid-cols-2 gap-3 mb-5">
            <button
              type="button"
              onclick={() => (mode = 'tenant')}
              class={`border px-4 py-3 text-sm font-bold uppercase tracking-[0.18em] transition-colors ${!isAccountantFlow ? 'bg-[#003B73] border-[#003B73] text-white' : 'border-[#D1CCC4] text-gray-500 hover:border-[#003B73] hover:text-[#003B73]'}`}
            >
              Empresa / Cliente
            </button>
            <button
              type="button"
              onclick={() => (mode = 'accountant')}
              class={`border px-4 py-3 text-sm font-bold uppercase tracking-[0.18em] transition-colors ${isAccountantFlow ? 'bg-[#003B73] border-[#003B73] text-white' : 'border-[#D1CCC4] text-gray-500 hover:border-[#003B73] hover:text-[#003B73]'}`}
            >
              Contador / Firma
            </button>
          </div>

          <div class="border-b border-[#D1CCC4] mb-5"></div>

          <form class="space-y-4" onsubmit={handleTenantSubmit}>
            <div class="grid sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-[11px] font-semibold uppercase tracking-widest text-gray-500 mb-1.5" for="full_name">{activeNameLabel}</label>
                <input
                  id="full_name"
                  class="w-full border border-[#D1CCC4] bg-[#F5F3EF] px-3 py-2.5 text-sm focus:outline-none focus:border-[#003B73]"
                  bind:value={tenantForm.full_name}
                  required
                />
              </div>
              <div>
                <label class="block text-[11px] font-semibold uppercase tracking-widest text-gray-500 mb-1.5" for="t_email">Email *</label>
                <input
                  id="t_email"
                  type="email"
                  class="w-full border border-[#D1CCC4] bg-[#F5F3EF] px-3 py-2.5 text-sm focus:outline-none focus:border-[#003B73]"
                  bind:value={tenantForm.email}
                  required
                />
              </div>
            </div>

            <div class="grid sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-[11px] font-semibold uppercase tracking-widest text-gray-500 mb-1.5" for="t_company">{activeWorkspaceLabel}</label>
                <input
                  id="t_company"
                  class="w-full border border-[#D1CCC4] bg-[#F5F3EF] px-3 py-2.5 text-sm focus:outline-none focus:border-[#003B73]"
                  bind:value={tenantForm.company_name}
                  required
                />
              </div>
              <div>
                <label class="block text-[11px] font-semibold uppercase tracking-widest text-gray-500 mb-1.5" for="t_sub">{activeSubdomainLabel}</label>
                <div class="flex">
                  <input
                    id="t_sub"
                    class="flex-1 border border-r-0 border-[#D1CCC4] bg-[#F5F3EF] px-3 py-2.5 text-sm focus:outline-none focus:border-[#003B73]"
                    bind:value={tenantForm.subdomain}
                    oninput={() => (tenantForm.subdomain = sanitizeSubdomain(tenantForm.subdomain))}
                    placeholder={activeSubdomainPlaceholder}
                    required
                  />
                  <span class="border border-[#D1CCC4] bg-[#E8E4DC] px-3 py-2.5 text-xs text-gray-500 whitespace-nowrap">.sajet.us</span>
                </div>
              </div>
            </div>

            <div class="grid sm:grid-cols-3 gap-4">
              <div>
                <label class="block text-[11px] font-semibold uppercase tracking-widest text-gray-500 mb-1.5" for="t_plan">Plan *</label>
                <select
                  id="t_plan"
                  class="w-full border border-[#D1CCC4] bg-[#F5F3EF] px-3 py-2.5 text-sm focus:outline-none focus:border-[#003B73]"
                  bind:value={tenantForm.plan}
                  disabled={loadingPlans}
                >
                  {#if loadingPlans}
                    <option>Cargando...</option>
                  {:else}
                    {#each plans as p}
                      <option value={p.name}>{p.display_name || p.name}</option>
                    {/each}
                  {/if}
                </select>
              </div>
              <div>
                <label class="block text-[11px] font-semibold uppercase tracking-widest text-gray-500 mb-1.5" for="t_users">{activeUsersLabel}</label>
                <input
                  id="t_users"
                  type="number"
                  min="1"
                  class="w-full border border-[#D1CCC4] bg-[#F5F3EF] px-3 py-2.5 text-sm focus:outline-none focus:border-[#003B73]"
                  bind:value={tenantForm.user_count}
                />
              </div>
              <div>
                <label class="block text-[11px] font-semibold uppercase tracking-widest text-gray-500 mb-1.5" for="t_billing">Periodo</label>
                <select
                  id="t_billing"
                  class="w-full border border-[#D1CCC4] bg-[#F5F3EF] px-3 py-2.5 text-sm focus:outline-none focus:border-[#003B73]"
                  bind:value={tenantForm.billing_period}
                >
                  <option value="monthly">Mensual</option>
                  <option value="annual">Anual (-15%)</option>
                </select>
              </div>
            </div>

            {#if tenantError}
              <div class="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{tenantError}</div>
            {/if}

            <div class="flex items-center gap-2 text-xs text-gray-400">
              <Lock size={11} /> {activeSupportCopy}
            </div>

            <button
              type="submit"
              disabled={tenantLoading || loadingPlans}
              class="w-full bg-[#003B73] text-white font-bold uppercase tracking-widest text-xs py-4 hover:bg-[#002a55] transition-colors disabled:opacity-50 inline-flex items-center justify-center gap-2"
            >
              {#if tenantLoading}
                <Loader2 size={14} class="animate-spin" />
              {/if}
              {activeSubmitLabel}
            </button>
          </form>
        </div>
      </div>

      <p class="text-center text-xs text-gray-400">
        Quieres ser partner?
        <button type="button" class="text-[#003B73] hover:underline font-semibold" onclick={() => (mode = 'partner')}>Ir al flujo de partner</button>
        ·
        Prefieres ver la propuesta para contadores?
        <a class="text-[#003B73] hover:underline font-semibold" href="/accountants">Explorar landing contable</a>
      </p>
    </div>
  </div>
{:else if mode === 'partner'}
  <div class="min-h-screen bg-[#F5F3EF] p-6">
    <div class="max-w-2xl mx-auto space-y-5">
      <div class="flex items-center justify-between">
        <button
          type="button"
          class="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-[#1a1a1a] transition-colors"
          onclick={() => (mode = 'landing')}
        >
          <ArrowLeft size={14} /> Volver
        </button>
        <a href="/login?next=partner-portal" class="text-sm text-[#C05A3C] hover:underline">Ya tengo cuenta</a>
      </div>

      {#if partnerSuccess}
        <div class="bg-white border border-[#D1CCC4] p-10 text-center">
          <div class="w-16 h-16 bg-amber-100 flex items-center justify-center mx-auto mb-5">
            <Clock size={32} class="text-amber-600" />
          </div>
          <h2 class="text-2xl font-bold text-[#1a1a1a] mb-3">Solicitud recibida</h2>
          <p class="text-sm text-gray-500 mb-2 max-w-md mx-auto leading-relaxed">
            Tu cuenta de partner ha sido creada con estado <strong class="text-amber-600">pendiente de validacion</strong>.
          </p>
          <p class="text-sm text-gray-500 mb-6 max-w-md mx-auto leading-relaxed">
            Nuestro equipo revisara tu solicitud y te notificara por email en <strong>24-48 horas habiles</strong>.
            Una vez validada, podras iniciar sesion y acceder al portal de partner.
          </p>
          <div class="border border-[#D1CCC4] bg-[#F5F3EF] p-5 mb-6 text-left max-w-sm mx-auto">
            <h4 class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-3">Que pasa ahora?</h4>
            <ol class="space-y-2">
              {#each [
                'Revisamos tu solicitud (24-48h habiles)',
                'Te enviamos email de confirmacion con instrucciones',
                'Accedes al portal de partner y completas onboarding',
                'Empiezas a gestionar clientes y cobrar comisiones',
              ] as step, i}
                <li class="flex items-start gap-2.5 text-xs text-gray-600">
                  <span class="w-5 h-5 bg-[#003B73] text-white text-[10px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">{i + 1}</span>
                  {step}
                </li>
              {/each}
            </ol>
          </div>
          <button
            type="button"
            onclick={() => goto('/login?next=partner-portal')}
            class="bg-[#003B73] text-white font-bold uppercase tracking-widest text-xs px-8 py-3.5 hover:bg-[#002a55] transition-colors inline-flex items-center gap-2"
          >
            Ir a iniciar sesion <ArrowRight size={14} />
          </button>
        </div>
      {:else}
        <div class="bg-white border border-[#D1CCC4] p-8">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 bg-[#00FF9F]/20 flex items-center justify-center">
              <Handshake size={20} class="text-[#003B73]" />
            </div>
            <div>
              <h1 class="text-xl font-bold text-[#1a1a1a]">Programa de Partners SAJET</h1>
              <p class="text-xs text-gray-500">50% de comision · gestion white-label · portal dedicado</p>
            </div>
          </div>

          <div class="bg-amber-50 border border-amber-200 px-4 py-3 flex items-start gap-2 mb-5">
            <BadgeCheck size={15} class="text-amber-600 mt-0.5 shrink-0" />
            <p class="text-xs text-amber-700 leading-relaxed">
              <strong>Cuenta sujeta a validacion</strong> — Al registrarte, tu cuenta queda en estado <em>pendiente</em>
              y no podras iniciar sesion hasta que nuestro equipo la apruebe (24-48h). No se activa ningun cobro.
            </p>
          </div>

          <div class="border-b border-[#D1CCC4] mb-5"></div>

          <form class="space-y-4" onsubmit={handlePartnerSubmit}>
            <div class="grid sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-[11px] font-semibold uppercase tracking-widest text-gray-500 mb-1.5" for="p_company">Empresa *</label>
                <input
                  id="p_company"
                  class="w-full border border-[#D1CCC4] bg-[#F5F3EF] px-3 py-2.5 text-sm focus:outline-none focus:border-[#003B73]"
                  bind:value={partnerForm.company_name}
                  required
                />
              </div>
              <div>
                <label class="block text-[11px] font-semibold uppercase tracking-widest text-gray-500 mb-1.5" for="p_name">Nombre de contacto *</label>
                <input
                  id="p_name"
                  class="w-full border border-[#D1CCC4] bg-[#F5F3EF] px-3 py-2.5 text-sm focus:outline-none focus:border-[#003B73]"
                  bind:value={partnerForm.contact_name}
                  required
                />
              </div>
            </div>

            <div class="grid sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-[11px] font-semibold uppercase tracking-widest text-gray-500 mb-1.5" for="p_email">Email *</label>
                <input
                  id="p_email"
                  type="email"
                  class="w-full border border-[#D1CCC4] bg-[#F5F3EF] px-3 py-2.5 text-sm focus:outline-none focus:border-[#003B73]"
                  bind:value={partnerForm.contact_email}
                  required
                />
              </div>
              <div>
                <label class="block text-[11px] font-semibold uppercase tracking-widest text-gray-500 mb-1.5" for="p_phone">Telefono</label>
                <input
                  id="p_phone"
                  class="w-full border border-[#D1CCC4] bg-[#F5F3EF] px-3 py-2.5 text-sm focus:outline-none focus:border-[#003B73]"
                  bind:value={partnerForm.phone}
                />
              </div>
            </div>

            <div>
              <label class="block text-[11px] font-semibold uppercase tracking-widest text-gray-500 mb-1.5" for="p_country">Pais</label>
              <select
                id="p_country"
                class="w-full border border-[#D1CCC4] bg-[#F5F3EF] px-3 py-2.5 text-sm focus:outline-none focus:border-[#003B73]"
                bind:value={partnerForm.country}
              >
                <option value="DO">Republica Dominicana</option>
                <option value="US">Estados Unidos</option>
                <option value="MX">Mexico</option>
                <option value="CO">Colombia</option>
                <option value="ES">Espana</option>
                <option value="PA">Panama</option>
                <option value="CL">Chile</option>
                <option value="AR">Argentina</option>
                <option value="PE">Peru</option>
              </select>
            </div>

            <div class="grid sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-[11px] font-semibold uppercase tracking-widest text-gray-500 mb-1.5" for="p_pass">Contrasena *</label>
                <input
                  id="p_pass"
                  type="password"
                  autocomplete="new-password"
                  minlength="8"
                  required
                  class="w-full border border-[#D1CCC4] bg-[#F5F3EF] px-3 py-2.5 text-sm focus:outline-none focus:border-[#003B73]"
                  bind:value={partnerForm.password}
                />
              </div>
              <div>
                <label class="block text-[11px] font-semibold uppercase tracking-widest text-gray-500 mb-1.5" for="p_pass2">Confirmar contrasena *</label>
                <input
                  id="p_pass2"
                  type="password"
                  autocomplete="new-password"
                  minlength="8"
                  required
                  class="w-full border border-[#D1CCC4] bg-[#F5F3EF] px-3 py-2.5 text-sm focus:outline-none focus:border-[#003B73]"
                  bind:value={partnerForm.password_confirm}
                />
              </div>
            </div>

            {#if partnerError}
              <div class="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{partnerError}</div>
            {/if}

            <button
              type="submit"
              disabled={partnerLoading}
              class="w-full bg-[#003B73] text-white font-bold uppercase tracking-widest text-xs py-4 hover:bg-[#002a55] transition-colors disabled:opacity-50 inline-flex items-center justify-center gap-2"
            >
              {#if partnerLoading}
                <Loader2 size={14} class="animate-spin" />
              {/if}
              Enviar solicitud de partner
            </button>

            <p class="text-center text-xs text-gray-400">
              Al registrarte aceptas los terminos del Programa de Partners de Jeturing / SAJET.
            </p>
          </form>
        </div>

        <p class="text-center text-xs text-gray-400">
          Buscas crear tu propia cuenta?
          <button type="button" class="text-[#003B73] hover:underline font-semibold" onclick={() => (mode = 'tenant')}>Ir al flujo empresa</button>
        </p>
      {/if}
    </div>
  </div>
{/if}
