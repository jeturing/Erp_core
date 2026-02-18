<script lang="ts">
  import { auth } from '../lib/stores';

  let email = $state('');
  let password = $state('');
  let showPassword = $state(false);
  let loading = $state(false);
  let error = $state('');
  let requiresTotp = $state(false);
  let totpCode = $state('');
  let storedEmail = $state('');
  let storedPassword = $state('');

  async function handleLogin(e: Event) {
    e.preventDefault();
    loading = true;
    error = '';

    const result = await auth.login(email, password);

    if (result.requires_totp) {
      storedEmail = email;
      storedPassword = password;
      requiresTotp = true;
      loading = false;
      return;
    }

    if (result.error) {
      error = result.error;
      loading = false;
      return;
    }

    if (result.success) {
      window.location.hash = '#/dashboard';
    }

    loading = false;
  }

  async function handleTotp(e: Event) {
    e.preventDefault();
    loading = true;
    error = '';

    const result = await auth.loginWithTotp(storedEmail, storedPassword, totpCode);

    if (result.error) {
      error = result.error;
      loading = false;
      return;
    }

    if (result.success) {
      window.location.hash = '#/dashboard';
    }

    loading = false;
  }
</script>

<div class="min-h-screen flex">
  <!-- Left Panel -->
  <div class="hidden lg:flex lg:w-1/2 bg-charcoal flex-col justify-between p-12">
    <div>
      <div class="flex items-center gap-3 mb-16">
        <div class="w-10 h-10 bg-terracotta flex items-center justify-center">
          <span class="text-white font-bold text-xl">S</span>
        </div>
        <span class="text-white font-bold text-lg tracking-widest uppercase">SAJET ERP</span>
      </div>
      <div class="mt-16">
        <p class="text-gray-400 text-xs uppercase tracking-[0.15em] mb-6">Plataforma Empresarial</p>
        <h2 class="text-white text-4xl font-bold leading-tight mb-8">
          Gestión inteligente<br />para tu empresa.
        </h2>
        <p class="text-gray-500 text-sm leading-relaxed max-w-sm">
          Controla tenants, infraestructura, dominios y facturación desde un solo panel administrativo unificado.
        </p>
      </div>
    </div>
    <div>
      <p class="text-gray-600 text-xs">© 2026 Sajet. Todos los derechos reservados.</p>
    </div>
  </div>

  <!-- Right Panel -->
  <div class="w-full lg:w-1/2 bg-bg-page flex items-center justify-center p-8">
    <div class="w-full max-w-sm">
      <!-- Mobile logo -->
      <div class="flex lg:hidden items-center gap-3 mb-10">
        <div class="w-9 h-9 bg-terracotta flex items-center justify-center">
          <span class="text-white font-bold text-lg">S</span>
        </div>
        <span class="font-bold text-base tracking-widest uppercase text-text-primary">SAJET ERP</span>
      </div>

      {#if !requiresTotp}
        <h2 class="text-2xl font-bold text-text-primary mb-1">Iniciar Sesión</h2>
        <p class="text-sm text-gray-500 mb-8">Accede al panel de administración</p>

        <form onsubmit={handleLogin} class="space-y-5">
          <div>
            <label class="label" for="email">Usuario o Email</label>
            <input
              id="email"
              type="text"
              class="input w-full px-3 py-2"
              placeholder="admin o correo@empresa.com"
              bind:value={email}
              required
              autocomplete="username"
            />
            <p class="text-[11px] text-gray-400 mt-1">
              {email.includes('@') ? 'Acceso como partner o empresa' : 'Acceso administrativo'}
            </p>
          </div>

          <div>
            <label class="label" for="password">Contraseña</label>
            <div class="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                class="input w-full px-3 py-2 pr-10"
                placeholder="••••••••"
                bind:value={password}
                required
                autocomplete="current-password"
              />
              <button
                type="button"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                onclick={() => showPassword = !showPassword}
                aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
              >
                {#if showPassword}
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                {:else}
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                {/if}
              </button>
            </div>
          </div>

          {#if error}
            <div class="bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
              {error}
            </div>
          {/if}

          <button
            type="submit"
            class="btn-primary w-full py-3 mt-2 disabled:opacity-60"
            disabled={loading}
          >
            {loading ? 'Iniciando...' : 'Ingresar'}
          </button>
        </form>
      {:else}
        <!-- TOTP Step -->
        <h2 class="text-2xl font-bold text-text-primary mb-1">Verificación en dos pasos</h2>
        <p class="text-sm text-gray-500 mb-8">Ingresa el código de 6 dígitos de tu aplicación autenticadora</p>

        <form onsubmit={handleTotp} class="space-y-5">
          <div>
            <label class="label" for="totp">Código TOTP</label>
            <input
              id="totp"
              type="text"
              inputmode="numeric"
              pattern="[0-9]{6}"
              maxlength="6"
              class="input w-full px-3 py-2 text-center text-2xl tracking-[0.5em] font-mono"
              placeholder="000000"
              bind:value={totpCode}
              required
              autocomplete="one-time-code"
            />
          </div>

          {#if error}
            <div class="bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
              {error}
            </div>
          {/if}

          <button
            type="submit"
            class="btn-primary w-full py-3"
            disabled={loading || totpCode.length !== 6}
          >
            {loading ? 'Verificando...' : 'Verificar'}
          </button>

          <button
            type="button"
            class="btn-secondary w-full py-2"
            onclick={() => { requiresTotp = false; totpCode = ''; error = ''; }}
          >
            Volver al inicio
          </button>
        </form>
      {/if}
    </div>
  </div>
</div>
