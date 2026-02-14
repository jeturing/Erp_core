<script lang="ts">
  import { auth } from '../lib/stores';
  import { Button, Input, Spinner } from '../lib/components';
  import { onMount } from 'svelte';
  
  let username = '';
  let password = '';
  let isSubmitting = false;
  let error = '';
  
  onMount(() => {
    if ($auth.user) {
      redirectByRole($auth.user.role);
    }
  });
  
  function redirectByRole(role: string) {
    console.log('[Login] Redirecting to:', role === 'admin' ? '/dashboard' : '/portal');
    if (role === 'admin') {
      window.location.hash = '#/dashboard';
    } else {
      window.location.hash = '#/portal';
    }
  }
  
  async function handleSubmit(e: Event) {
    e.preventDefault();
    console.log('[Login] Submit clicked:', username);
    error = '';
    isSubmitting = true;
    
    try {
      console.log('[Login] Fetching...');
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: username, password: password }),
        credentials: 'include'
      });
      
      console.log('[Login] Response:', response.status);
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Credenciales inválidas');
      }
      
      const data = await response.json();
      console.log('[Login] Success:', data);
      
      // IMPORTANTE: Inicializar el store de auth ANTES del redirect
      // Esto asegura que App.svelte reconozca al usuario como autenticado
      await auth.init();
      
      console.log('[Login] Auth initialized, redirecting based on role:', data.role);
      redirectByRole(data.role);
      
    } catch (err) {
      console.error('[Login] Error:', err);
      error = err instanceof Error ? err.message : 'Error de conexión';
    } finally {
      isSubmitting = false;
    }
  }
</script>

<div class="min-h-screen flex">
  <div class="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-900 via-primary-800 to-primary-900 p-12 flex-col justify-between">
    <div>
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-accent-500 flex items-center justify-center">
          <span class="text-primary-900 font-bold text-xl">J</span>
        </div>
        <span class="text-2xl font-bold text-white">Jeturing</span>
      </div>
    </div>
    <div class="space-y-6">
      <h1 class="text-4xl font-bold text-white leading-tight">Bienvenido a<span class="block text-accent-400">Jeturing</span></h1>
      <p class="text-lg text-primary-200 max-w-md">Gestiona tu negocio de forma inteligente.</p>
      <div class="grid grid-cols-2 gap-4 pt-4">
        <div class="flex items-center gap-2 text-primary-200"><svg class="w-5 h-5 text-accent-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg><span>Gestión empresarial</span></div>
        <div class="flex items-center gap-2 text-primary-200"><svg class="w-5 h-5 text-accent-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg><span>Facturación</span></div>
        <div class="flex items-center gap-2 text-primary-200"><svg class="w-5 h-5 text-accent-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg><span>Dominios</span></div>
        <div class="flex items-center gap-2 text-primary-200"><svg class="w-5 h-5 text-accent-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg><span>Soporte 24/7</span></div>
      </div>
    </div>
    <p class="text-sm text-primary-400">© 2026 Jeturing Technologies.</p>
  </div>
  
  <div class="w-full lg:w-1/2 flex items-center justify-center p-8 bg-surface-dark">
    <div class="w-full max-w-md space-y-8">
      <div class="lg:hidden flex items-center justify-center gap-3 mb-8">
        <div class="w-10 h-10 rounded-lg bg-accent-500 flex items-center justify-center"><span class="text-primary-900 font-bold text-xl">J</span></div>
        <span class="text-2xl font-bold text-white">Jeturing</span>
      </div>
      
      <div class="text-center lg:text-left">
        <h2 class="text-2xl font-bold text-white">Iniciar sesión</h2>
        <p class="mt-2 text-secondary-400">Ingresa tus credenciales</p>
      </div>
      
      <form on:submit={handleSubmit} class="space-y-6">
        {#if error}
          <div class="p-4 rounded-lg bg-error/10 border border-error/20"><p class="text-sm text-error">{error}</p></div>
        {/if}
        
        <Input label="Usuario o Email" name="username" type="text" placeholder="usuario o email" autocomplete="username" bind:value={username} required disabled={isSubmitting} />
        <Input label="Contraseña" type="password" name="password" placeholder="••••••••" autocomplete="current-password" bind:value={password} required disabled={isSubmitting} />
        
        <div class="flex items-center justify-between">
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" class="w-4 h-4 rounded border-surface-border bg-surface-highlight text-primary-500" />
            <span class="text-sm text-secondary-400">Recordarme</span>
          </label>
          <a href="#/forgot-password" class="text-sm text-primary-400 hover:text-primary-300">¿Olvidaste tu contraseña?</a>
        </div>
        
        <Button type="submit" variant="accent" size="lg" loading={isSubmitting} disabled={isSubmitting || !username || !password}>
          {isSubmitting ? 'Iniciando...' : 'Iniciar sesión'}
        </Button>
      </form>
      
      <div class="pt-4 text-center">
        <p class="text-sm text-secondary-500">¿Ayuda? <a href="mailto:soporte@jeturing.net" class="text-primary-400">Contacta soporte</a></p>
      </div>
    </div>
  </div>
</div>
