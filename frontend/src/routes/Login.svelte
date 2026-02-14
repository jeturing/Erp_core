<script lang="ts">
  import { onMount } from 'svelte';
  import { auth } from '../lib/stores';
  import { Button, Input } from '../lib/components';

  let username = '';
  let password = '';
  let totpCode = '';
  let requiresTotp = false;
  let isSubmitting = false;
  let localError = '';

  function redirectByRole(role: string) {
    if (role === 'tenant') {
      window.location.hash = '#/portal';
      return;
    }
    window.location.hash = '#/dashboard';
  }

  onMount(() => {
    if ($auth.user) {
      redirectByRole($auth.user.role);
    }
  });

  async function handleSubmit(event: Event) {
    event.preventDefault();
    localError = '';
    isSubmitting = true;

    try {
      const result = await auth.login({
        username,
        password,
        totp_code: requiresTotp ? totpCode : undefined,
      });

      if (result.requiresTotp) {
        requiresTotp = true;
        localError = '';
        return;
      }

      if (!result.success) {
        localError = result.error || $auth.error || 'Credenciales invalidas';
        return;
      }

      requiresTotp = false;
      totpCode = '';
      if ($auth.user) {
        redirectByRole($auth.user.role);
      }
    } finally {
      isSubmitting = false;
    }
  }
</script>

<div class="min-h-screen flex">
  <div class="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-900 via-primary-800 to-primary-900 p-12 flex-col justify-between">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-lg bg-accent-500 flex items-center justify-center">
        <span class="text-primary-900 font-bold text-xl">J</span>
      </div>
      <span class="text-2xl font-bold text-white">Jeturing</span>
    </div>

    <div class="space-y-6">
      <h1 class="text-4xl font-bold text-white leading-tight">
        Acceso unificado
        <span class="block text-accent-400">Admin y Tenant</span>
      </h1>
      <p class="text-lg text-primary-200 max-w-md">Usa usuario admin o email tenant para autenticarte en la SPA.</p>
    </div>

    <p class="text-sm text-primary-400">© 2026 Jeturing Technologies</p>
  </div>

  <div class="w-full lg:w-1/2 flex items-center justify-center p-8 bg-surface-dark">
    <div class="w-full max-w-md space-y-8">
      <div class="lg:hidden flex items-center justify-center gap-3 mb-8">
        <div class="w-10 h-10 rounded-lg bg-accent-500 flex items-center justify-center">
          <span class="text-primary-900 font-bold text-xl">J</span>
        </div>
        <span class="text-2xl font-bold text-white">Jeturing</span>
      </div>

      <div class="text-center lg:text-left">
        <h2 class="text-2xl font-bold text-white">Iniciar sesion</h2>
        <p class="mt-2 text-secondary-400">
          {requiresTotp ? 'Ingresa tu codigo 2FA para completar el acceso' : 'Credenciales administradas por `/api/auth/login`'}
        </p>
      </div>

      <form on:submit={handleSubmit} class="space-y-6">
        {#if localError || $auth.error}
          <div class="p-4 rounded-lg bg-error/10 border border-error/20">
            <p class="text-sm text-error">{localError || $auth.error}</p>
          </div>
        {/if}

        <Input
          label="Usuario o email"
          name="username"
          type="text"
          placeholder="admin o cliente@dominio.com"
          autocomplete="username"
          bind:value={username}
          required
          disabled={isSubmitting}
        />

        <Input
          label="Contrasena"
          type="password"
          name="password"
          placeholder="••••••••"
          autocomplete="current-password"
          bind:value={password}
          required
          disabled={isSubmitting}
        />

        {#if requiresTotp}
          <Input
            label="Codigo 2FA"
            name="totp_code"
            type="text"
            placeholder="123456"
            autocomplete="one-time-code"
            bind:value={totpCode}
            required
            disabled={isSubmitting}
          />
        {/if}

        <Button
          type="submit"
          variant="accent"
          size="lg"
          loading={isSubmitting}
          disabled={isSubmitting || !username || !password || (requiresTotp && !totpCode)}
        >
          {#if isSubmitting}
            Verificando...
          {:else if requiresTotp}
            Verificar 2FA
          {:else}
            Iniciar sesion
          {/if}
        </Button>
      </form>

      <div class="pt-4 text-center">
        <p class="text-sm text-secondary-500">
          Soporte:
          <a href="mailto:soporte@jeturing.net" class="text-primary-400 hover:text-primary-300">soporte@jeturing.net</a>
        </p>
      </div>
    </div>
  </div>
</div>
