<script lang="ts">
  import { auth } from '../lib/stores';

  let email = $state('');
  let password = $state('');
  let showPassword = $state(false);
  let loading = $state(false);
  let error = $state('');
  let requiresTotp = $state(false);
  let requiresEmailVerify = $state(false);
  let totpCode = $state('');
  let emailVerifyCode = $state('');
  let storedEmail = $state('');
  let storedPassword = $state('');
  let storedTotpCode = $state('');
  let emailVerifyMessage = $state('');

  function getPostLoginRoute(): string {
    try {
      const hash = window.location.hash || '';
      const query = hash.split('?')[1] || '';
      const params = new URLSearchParams(query);
      const next = (params.get('next') || '').trim();
      if (!next) return 'dashboard';

      // Allow only simple internal hash routes
      const safe = next.replace(/^#\/?/, '').split('?')[0].split('/')[0];
      if (!safe) return 'dashboard';
      if (!/^[a-z0-9-]+$/i.test(safe)) return 'dashboard';
      return safe;
    } catch {
      return 'dashboard';
    }
  }

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

    if (result.requires_email_verify) {
      storedEmail = email;
      storedPassword = password;
      requiresEmailVerify = true;
      emailVerifyMessage = result.message || 'Código de verificación enviado a tu email';
      loading = false;
      return;
    }

    if (result.error) {
      error = result.error;
      loading = false;
      return;
    }

    if (result.success) {
      window.location.hash = `#/${getPostLoginRoute()}`;
    }

    loading = false;
  }

  async function handleTotp(e: Event) {
    e.preventDefault();
    loading = true;
    error = '';

    const result = await auth.loginWithTotp(storedEmail, storedPassword, totpCode);

    if (result.requires_email_verify) {
      storedTotpCode = totpCode;
      requiresEmailVerify = true;
      requiresTotp = false;
      emailVerifyMessage = result.message || 'Código de verificación enviado a tu email';
      loading = false;
      return;
    }

    if (result.error) {
      error = result.error;
      loading = false;
      return;
    }

    if (result.success) {
      window.location.hash = `#/${getPostLoginRoute()}`;
    }

    loading = false;
  }

  async function handleEmailVerify(e: Event) {
    e.preventDefault();
    loading = true;
    error = '';

    const result = await auth.loginWithEmailVerify(
      storedEmail,
      storedPassword,
      emailVerifyCode,
      storedTotpCode || undefined
    );

    if (result.error) {
      error = result.error;
      loading = false;
      return;
    }

    if (result.success) {
      window.location.hash = `#/${getPostLoginRoute()}`;
    }

    loading = false;
  }

  function resetToLogin() {
    requiresTotp = false;
    requiresEmailVerify = false;
    totpCode = '';
    emailVerifyCode = '';
    storedTotpCode = '';
    error = '';
    emailVerifyMessage = '';
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
          Controla tu empresa de una forma facil intuitiva y agil.
        </p>
      </div>
    </div>
    <div>
      <p class="text-gray-600 text-xs">© 2026 Jeturing inc. Todos los derechos reservados.</p>
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

      {#if !requiresTotp && !requiresEmailVerify}
        <h2 class="text-2xl font-bold text-text-primary mb-1">Iniciar Sesión</h2>
        <p class="text-sm text-gray-500 mb-8">Accede al panel de administración</p>

        <form onsubmit={handleLogin} class="space-y-5">
          <div>
            <label class="label" for="email">Usuario o Email</label>
            <input
              id="email"
              type="text"
              class="input w-full px-3 py-2"
              placeholder="correo@empresa.com"
              bind:value={email}
              required
              autocomplete="username"
            />
            <p class="text-[11px] text-gray-400 mt-1">
              {email.includes('@') ? 'Acceso como partner, empresa o admin' : 'Acceso administrativo'}
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

          <div class="flex items-center justify-between text-xs mt-3">
            <a href="#/signup" class="text-[#C05A3C] hover:underline">Crear cuenta</a>
            <a href="#/recover-account" class="text-[#C05A3C] hover:underline">Recuperar cuenta</a>
          </div>
        </form>
      {:else if requiresTotp}
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
              placeholder="000-000"
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
            onclick={resetToLogin}
          >
            Volver al inicio
          </button>
        </form>
      {:else if requiresEmailVerify}
        <!-- Email Verification Step (Steam-style) -->
        <div class="text-center mb-6">
          <div class="w-14 h-14 rounded-full bg-terracotta/10 flex items-center justify-center mx-auto mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-terracotta"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
          </div>
          <h2 class="text-2xl font-bold text-text-primary mb-1">Verificación de email</h2>
          <p class="text-sm text-gray-500">{emailVerifyMessage}</p>
        </div>

        <form onsubmit={handleEmailVerify} class="space-y-5">
          <div>
            <label class="label" for="emailCode">Código de verificación</label>
            <input
              id="emailCode"
              type="text"
              maxlength="6"
              class="input w-full px-3 py-3 text-center text-3xl tracking-[0.6em] font-mono uppercase"
              placeholder="AB3K9Z"
              bind:value={emailVerifyCode}
              required
              autocomplete="one-time-code"
            />
            <p class="text-[11px] text-gray-400 mt-2 text-center">
              Revisa tu bandeja de entrada. El código expira en 5 minutos.
            </p>
          </div>

          {#if error}
            <div class="bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
              {error}
            </div>
          {/if}

          <button
            type="submit"
            class="btn-primary w-full py-3"
            disabled={loading || emailVerifyCode.length !== 6}
          >
            {loading ? 'Verificando...' : 'Verificar código'}
          </button>

          <button
            type="button"
            class="btn-secondary w-full py-2"
            onclick={resetToLogin}
          >
            Volver al inicio
          </button>
        </form>
      {/if}
    </div>
  </div>
</div>
