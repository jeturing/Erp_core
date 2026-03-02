<script lang="ts">
  import { onMount } from 'svelte';
  import { Loader2, ArrowLeft, CheckCircle } from 'lucide-svelte';

  let role = 'tenant';
  let loadingPlans = true;
  let submitting = false;
  let error = '';

  let plans = [];

  let form = {
    full_name: '',
    email: '',
    company_name: '',
    subdomain: '',
    plan: 'pro',
    user_count: 1,
    billing_period: 'monthly',
  };

  function sanitizeSubdomain(value) {
    return value
      .toLowerCase()
      .replace(/[^a-z0-9-]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
  }

  async function loadPlans() {
    loadingPlans = true;
    try {
      const res = await fetch('/api/public/plans');
      if (!res.ok) throw new Error('No se pudieron cargar los planes');
      const data = await res.json();
      plans = data.plans || [];
      if (plans.length > 0) {
        form.plan = plans.find((p) => p.name === 'pro')?.name || plans[0].name;
      }
    } catch (e) {
      error = e?.message || 'Error cargando planes';
    } finally {
      loadingPlans = false;
    }
  }

  function setRole(next) {
    role = next;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    error = '';

    form.subdomain = sanitizeSubdomain(form.subdomain);

    if (!form.full_name || !form.email || !form.company_name || !form.subdomain || !form.plan) {
      error = 'Complete todos los campos obligatorios';
      return;
    }

    if (form.subdomain.length < 3) {
      error = 'El subdominio debe tener al menos 3 caracteres';
      return;
    }

    submitting = true;
    try {
      const response = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          is_accountant: role === 'accountant',
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.detail || 'No se pudo crear la cuenta');
      }

      if (data?.checkout_url) {
        window.location.href = data.checkout_url;
        return;
      }

      throw new Error('No se recibió URL de checkout');
    } catch (e) {
      error = e?.message || 'Error procesando registro';
    } finally {
      submitting = false;
    }
  }

  function goToLogin() {
    window.location.hash = '#/login';
  }

  function goToHome() {
    window.location.hash = '#/';
  }

  onMount(async () => {
    // Parse hash query params, e.g. #/signup?plan=pro&users=5&billing=annual&role=accountant
    try {
      const hash = window.location.hash || '';
      const query = hash.split('?')[1] || '';
      const params = new URLSearchParams(query);

      const roleParam = (params.get('role') || '').toLowerCase();
      if (roleParam === 'accountant') role = 'accountant';

      const plan = params.get('plan');
      const users = Number(params.get('users') || '1');
      const billing = params.get('billing');
      if (plan) form.plan = plan;
      if (users > 0) form.user_count = users;
      if (billing === 'annual' || billing === 'monthly') form.billing_period = billing;
    } catch {
      // ignore query parse errors
    }

    await loadPlans();
  });
</script>

<div class="min-h-screen bg-bg-page p-6">
  <div class="max-w-3xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
      <button class="btn-secondary px-3 py-2 text-sm inline-flex items-center gap-2" on:click={goToHome}>
        <ArrowLeft size={14} /> Volver al inicio
      </button>
      <button class="text-sm text-[#C05A3C] hover:underline" on:click={goToLogin}>Ya tengo cuenta</button>
    </div>

    <div class="card p-6 sm:p-8">
      <h1 class="text-2xl font-bold text-text-primary mb-2">Crear cuenta SAJET</h1>
      <p class="text-sm text-gray-500 mb-6">Selecciona tu flujo de registro y completa tus datos.</p>

      <div class="grid grid-cols-2 gap-3 mb-3">
        <button
          class={`py-2.5 rounded-md border text-sm font-semibold ${role === 'tenant' ? 'bg-[#003B73] text-white border-[#003B73]' : 'border-border-light text-text-secondary'}`}
          on:click={() => setRole('tenant')}
        >
          Tenant
        </button>
        <button
          class={`py-2.5 rounded-md border text-sm font-semibold ${role === 'accountant' ? 'bg-[#003B73] text-white border-[#003B73]' : 'border-border-light text-text-secondary'}`}
          on:click={() => setRole('accountant')}
        >
          Accountant
        </button>
      </div>
      <a href="#/partner-signup" class="text-xs text-[#C05A3C] hover:underline inline-block mb-3">¿Quieres registrarte como Partner? Ir al flujo Partner</a>

      <form class="space-y-4" on:submit={handleSubmit}>
        <div class="grid sm:grid-cols-2 gap-4">
          <div>
            <label class="label" for="full_name">Nombre completo *</label>
            <input id="full_name" class="input w-full" bind:value={form.full_name} required />
          </div>
          <div>
            <label class="label" for="email">Email *</label>
            <input id="email" type="email" class="input w-full" bind:value={form.email} required />
          </div>
        </div>

        <div class="grid sm:grid-cols-2 gap-4">
          <div>
            <label class="label" for="company_name">Empresa *</label>
            <input id="company_name" class="input w-full" bind:value={form.company_name} required />
          </div>
          <div>
            <label class="label" for="subdomain">Subdominio *</label>
            <input id="subdomain" class="input w-full" bind:value={form.subdomain} on:input={() => (form.subdomain = sanitizeSubdomain(form.subdomain))} placeholder="miempresa" required />
          </div>
        </div>

        <div class="grid sm:grid-cols-3 gap-4">
          <div>
            <label class="label" for="plan">Plan *</label>
            <select id="plan" class="input w-full" bind:value={form.plan} disabled={loadingPlans}>
              {#if loadingPlans}
                <option>Cargando planes...</option>
              {:else}
                {#each plans as p}
                  <option value={p.name}>{p.display_name || p.name}</option>
                {/each}
              {/if}
            </select>
          </div>
          <div>
            <label class="label" for="user_count">Usuarios</label>
            <input id="user_count" type="number" min="1" class="input w-full" bind:value={form.user_count} />
          </div>
          <div>
            <label class="label" for="billing_period">Periodo</label>
            <select id="billing_period" class="input w-full" bind:value={form.billing_period}>
              <option value="monthly">Mensual</option>
              <option value="annual">Anual</option>
            </select>
          </div>
        </div>

        {#if role === 'accountant'}
          <div class="rounded border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700 flex items-center gap-2">
            <CheckCircle size={14} />
            El registro se creará con perfil Accountant para gestionar múltiples clientes.
          </div>
        {/if}

        {#if error}
          <div class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
        {/if}

        <button class="btn-primary w-full py-3 inline-flex items-center justify-center gap-2" type="submit" disabled={submitting || loadingPlans}>
          {#if submitting}<Loader2 size={14} class="animate-spin" />{/if}
          Continuar a pago seguro
        </button>
      </form>
    </div>
  </div>
</div>
