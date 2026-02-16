<script lang="ts">
  import { onMount } from 'svelte';
  import { auth } from '../lib/stores';
  import { Eye, EyeOff } from 'lucide-svelte';
  import { api } from '../lib/api';

  let username = '';
  let password = '';
  let totpCode = '';
  let showPassword = false;
  let step: 'credentials' | 'totp' = 'credentials';
  let userRole: 'admin' | 'partner' | 'tenant' = 'admin';

  const roles = [
    { id: 'admin',   label: 'Admin' },
    { id: 'partner', label: 'Partner' },
    { id: 'tenant',  label: 'Empresa' },
  ] as const;

  async function handleSubmit() {
    if (step === 'credentials') {
      const result = await auth.login(username, password);
      if (result?.requires_totp) {
        step = 'totp';
      }
    } else {
      // TOTP verify
      try {
        await api.post('/api/auth/totp/verify', { code: totpCode, username });
        await auth.init();
      } catch {
        auth.setError('Código TOTP inválido');
      }
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') handleSubmit();
  }

  onMount(() => {
    username = '';
    password = '';
  });
</script>

<div class="min-h-screen flex bg-bg-page">
  <!-- Left panel – charcoal -->
  <div class="hidden lg:flex w-[600px] flex-shrink-0 bg-charcoal flex-col justify-between px-14 py-16">
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 bg-terracotta flex items-center justify-center">
        <span class="text-text-light font-bold font-sans text-sm">S</span>
      </div>
      <span class="font-sans font-bold text-text-light tracking-wide text-sm uppercase">Sajet ERP</span>
      <span class="ml-2 text-gray-500 font-body text-xs">Enterprise Resource Planning</span>
    </div>

    <div>
      <h1 class="font-sans font-bold text-text-light text-5xl leading-tight">
        Gestiona tu negocio<br />desde un solo lugar.
      </h1>
      <p class="mt-6 text-gray-500 font-body text-base max-w-sm">
        Plataforma multi-tenant para distribuidores, gestores y empresas que buscan escalar con tecnología.
      </p>
    </div>

    <p class="text-gray-600 font-body text-xs">© {new Date().getFullYear()} Sajet ERP. Todos los derechos reservados.</p>
  </div>

  <!-- Right panel -->
  <div class="flex-1 flex items-center justify-center px-8 py-16 bg-bg-page">
    <div class="w-full max-w-sm">
      {#if step === 'credentials'}
        <h2 class="font-sans font-bold text-text-primary text-2xl mb-1">Iniciar Sesión</h2>
        <p class="text-gray-500 font-body text-sm mb-8">Ingresa tus credenciales para acceder al sistema.</p>

        <!-- Fields -->
        <div class="space-y-5">
          <div>
            <label class="label" for="login-user">Correo o usuario</label>
            <input
              id="login-user"
              type="text"
              class="input"
              placeholder="usuario@empresa.com"
              bind:value={username}
              on:keydown={handleKeydown}
              autocomplete="username"
            />
          </div>
          <div>
            <div class="flex items-center justify-between mb-1.5">
              <label class="label !mb-0" for="login-pass">Contraseña</label>
              <a href="#/forgot-password" class="text-[11px] text-terracotta font-sans hover:underline">¿Olvidaste tu contraseña?</a>
            </div>
            <div class="relative">
              <input
                id="login-pass"
                type={showPassword ? 'text' : 'password'}
                class="input pr-11"
                placeholder="••••••••"
                bind:value={password}
                on:keydown={handleKeydown}
                autocomplete="current-password"
              />
              <button
                type="button"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-text-secondary"
                on:click={() => (showPassword = !showPassword)}
                tabindex="-1"
              >
                {#if showPassword}<EyeOff size={16} />{:else}<Eye size={16} />{/if}
              </button>
            </div>
          </div>
        </div>

        {#if $auth.error}
          <p class="mt-4 text-sm text-error font-body">{$auth.error}</p>
        {/if}

        <button
          type="button"
          class="btn-primary w-full mt-6 py-3"
          on:click={handleSubmit}
          disabled={$auth.isLoading}
        >
          {$auth.isLoading ? 'Ingresando...' : 'INGRESAR AL SISTEMA'}
        </button>

        <!-- Role selector -->
        <div class="mt-8">
          <p class="text-[11px] uppercase tracking-widest text-gray-500 font-sans mb-3 text-center">Tipo de acceso</p>
          <div class="flex gap-2 justify-center">
            {#each roles as r}
              <button
                type="button"
                class={`px-4 py-2 text-[10px] font-semibold uppercase tracking-widest font-sans border transition-colors ${
                  userRole === r.id
                    ? 'bg-charcoal text-text-light border-charcoal'
                    : 'bg-transparent text-gray-500 border-border-light hover:border-charcoal'
                }`}
                on:click={() => (userRole = r.id)}
              >
                {r.label}
              </button>
            {/each}
          </div>
        </div>

      {:else}
        <!-- TOTP Step -->
        <h2 class="font-sans font-bold text-text-primary text-2xl mb-1">Verificación 2FA</h2>
        <p class="text-gray-500 font-body text-sm mb-8">Ingresa el código de tu aplicación autenticadora.</p>

        <div>
          <label class="label" for="totp-code">Código TOTP (6 dígitos)</label>
          <input
            id="totp-code"
            type="text"
            inputmode="numeric"
            maxlength="6"
            class="input text-center text-xl tracking-[0.3em] font-mono"
            placeholder="000000"
            bind:value={totpCode}
            on:keydown={handleKeydown}
            autofocus
          />
        </div>

        {#if $auth.error}
          <p class="mt-4 text-sm text-error font-body">{$auth.error}</p>
        {/if}

        <button type="button" class="btn-primary w-full mt-6 py-3" on:click={handleSubmit} disabled={$auth.isLoading}>
          {$auth.isLoading ? 'Verificando...' : 'VERIFICAR CÓDIGO'}
        </button>

        <button type="button" class="btn-ghost w-full mt-3" on:click={() => { step = 'credentials'; auth.clearError?.(); }}>
          Volver al inicio de sesión
        </button>
      {/if}
    </div>
  </div>
</div>
