<script lang="ts">
  import { Loader2 } from 'lucide-svelte';
  import { goto } from '$app/navigation';

  let loading = false;
  let success = false;
  let error = '';

  let form = {
    company_name: '',
    contact_name: '',
    contact_email: '',
    phone: '',
    country: 'DO',
    password: '',
    password_confirm: '',
  };

  async function handleSubmit(event: Event) {
    event.preventDefault();
    error = '';

    if (!form.company_name || !form.contact_name || !form.contact_email || !form.password) {
      error = 'Complete los campos obligatorios';
      return;
    }
    if (form.password.length < 8) {
      error = 'La contraseña debe tener al menos 8 caracteres';
      return;
    }
    if (form.password !== form.password_confirm) {
      error = 'Las contraseñas no coinciden';
      return;
    }

    loading = true;
    try {
      const response = await fetch('/api/public/partner-signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_name: form.company_name,
          contact_name: form.contact_name,
          contact_email: form.contact_email,
          phone: form.phone || undefined,
          country: form.country || undefined,
          password: form.password,
          billing_scenario: 'jeturing_collects',
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.detail || 'No se pudo crear la cuenta de partner');
      }

      success = true;
    } catch (e: any) {
      error = e?.message || 'Error al crear cuenta';
    } finally {
      loading = false;
    }
  }

  function goToLogin() {
    goto('/login?next=partner-portal');
  }

  function goToPartnersSection() {
    goto('/partners');
  }
</script>

<div class="min-h-screen bg-bg-page flex items-center justify-center p-6">
  <div class="w-full max-w-2xl bg-white border border-border-light rounded-lg p-8 shadow-soft">
    <h1 class="text-2xl font-bold text-text-primary mb-3">Programa de Socios SAJET</h1>
    <p class="text-sm text-gray-600 mb-6">Crea tu cuenta de socio para gestionar leads, comisiones y clientes.</p>

    {#if success}
      <div class="rounded border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700 mb-4">
        Cuenta creada correctamente. Ahora inicia sesión para completar tu onboarding de partner.
      </div>
      <div class="grid gap-4 sm:grid-cols-2">
        <button class="btn-primary py-3" on:click={goToLogin}>Ir a iniciar sesión</button>
        <button class="btn-secondary py-3" on:click={goToPartnersSection}>Ver beneficios para socios</button>
      </div>
    {:else}
      <form class="space-y-4" on:submit={handleSubmit}>
        <div class="grid sm:grid-cols-2 gap-4">
          <div>
            <label class="label" for="company_name">Empresa *</label>
            <input id="company_name" class="input w-full" bind:value={form.company_name} required />
          </div>
          <div>
            <label class="label" for="contact_name">Nombre de contacto *</label>
            <input id="contact_name" class="input w-full" bind:value={form.contact_name} required />
          </div>
        </div>

        <div class="grid sm:grid-cols-2 gap-4">
          <div>
            <label class="label" for="contact_email">Email *</label>
            <input id="contact_email" type="email" class="input w-full" bind:value={form.contact_email} required />
          </div>
          <div>
            <label class="label" for="phone">Teléfono</label>
            <input id="phone" class="input w-full" bind:value={form.phone} />
          </div>
        </div>

        <div>
          <label class="label" for="country">País</label>
          <input id="country" class="input w-full" bind:value={form.country} />
        </div>

        <div class="grid sm:grid-cols-2 gap-4">
          <div>
            <label class="label" for="password">Contraseña *</label>
            <input id="password" type="password" class="input w-full" bind:value={form.password} minlength="8" required />
          </div>
          <div>
            <label class="label" for="password_confirm">Confirmar contraseña *</label>
            <input id="password_confirm" type="password" class="input w-full" bind:value={form.password_confirm} minlength="8" required />
          </div>
        </div>

        {#if error}
          <div class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
        {/if}

        <div class="grid gap-4 sm:grid-cols-2">
          <button class="btn-primary py-3 inline-flex items-center justify-center gap-2" type="submit" disabled={loading}>
            {#if loading}<Loader2 size={14} class="animate-spin" />{/if}
            Crear cuenta partner
          </button>
          <button class="btn-secondary py-3" type="button" on:click={goToLogin}>Ya tengo cuenta</button>
        </div>
      </form>
    {/if}

    <div class="mt-6 text-xs text-gray-500">Si ya recibiste invitación, inicia sesión con tu email y completa onboarding.</div>
  </div>
</div>
