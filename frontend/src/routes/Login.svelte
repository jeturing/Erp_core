<script lang="ts">
  import { auth } from '../lib/stores';
  import { Button, Input, Spinner } from '../lib/components';
  import { onMount } from 'svelte';
  
  let username = '';
  let password = '';
  let isSubmitting = false;
  let error = '';
  
  // Redirect if already logged in
  onMount(() => {
    if ($auth.user) {
      window.location.hash = '#/dashboard';
    }
  });
  
  async function handleSubmit(e: Event) {
    e.preventDefault();
    error = '';
    isSubmitting = true;
    
    try {
      const success = await auth.login({ username, password });
      if (success) {
        window.location.hash = '#/dashboard';
      } else {
        error = $auth.error || 'Credenciales inválidas';
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error de conexión';
    } finally {
      isSubmitting = false;
    }
  }
</script>

<div class="min-h-screen flex">
  <!-- Left Panel - Branding -->
  <div class="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-900 via-primary-800 to-primary-900 p-12 flex-col justify-between">
    <div>
      <!-- Logo -->
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-accent-500 flex items-center justify-center">
          <span class="text-primary-900 font-bold text-xl">J</span>
        </div>
        <span class="text-2xl font-bold text-white">Jeturing</span>
      </div>
    </div>
    
    <div class="space-y-6">
      <h1 class="text-4xl font-bold text-white leading-tight">
        ERP Core
        <span class="block text-accent-400">Management Platform</span>
      </h1>
      <p class="text-lg text-primary-200 max-w-md">
        Gestiona tus tenants, suscripciones e infraestructura desde un único panel de control.
      </p>
      
      <!-- Features -->
      <div class="grid grid-cols-2 gap-4 pt-4">
        <div class="flex items-center gap-2 text-primary-200">
          <svg class="w-5 h-5 text-accent-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <span>Multi-tenant</span>
        </div>
        <div class="flex items-center gap-2 text-primary-200">
          <svg class="w-5 h-5 text-accent-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <span>Auto-provisioning</span>
        </div>
        <div class="flex items-center gap-2 text-primary-200">
          <svg class="w-5 h-5 text-accent-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <span>Stripe Integration</span>
        </div>
        <div class="flex items-center gap-2 text-primary-200">
          <svg class="w-5 h-5 text-accent-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <span>Proxmox Ready</span>
        </div>
      </div>
    </div>
    
    <p class="text-sm text-primary-400">
      © 2024 Jeturing Technologies. All rights reserved.
    </p>
  </div>
  
  <!-- Right Panel - Login Form -->
  <div class="w-full lg:w-1/2 flex items-center justify-center p-8 bg-surface-dark">
    <div class="w-full max-w-md space-y-8">
      <!-- Mobile Logo -->
      <div class="lg:hidden flex items-center justify-center gap-3 mb-8">
        <div class="w-10 h-10 rounded-lg bg-accent-500 flex items-center justify-center">
          <span class="text-primary-900 font-bold text-xl">J</span>
        </div>
        <span class="text-2xl font-bold text-white">Jeturing</span>
      </div>
      
      <div class="text-center lg:text-left">
        <h2 class="text-2xl font-bold text-white">Iniciar sesión</h2>
        <p class="mt-2 text-secondary-400">
          Ingresa tus credenciales para acceder al panel
        </p>
      </div>
      
      <form on:submit={handleSubmit} class="space-y-6">
        {#if error}
          <div class="p-4 rounded-lg bg-error/10 border border-error/20">
            <p class="text-sm text-error">{error}</p>
          </div>
        {/if}
        
        <Input
          label="Usuario"
          name="username"
          placeholder="admin"
          bind:value={username}
          required
          disabled={isSubmitting}
        />
        
        <Input
          label="Contraseña"
          type="password"
          name="password"
          placeholder="••••••••"
          bind:value={password}
          required
          disabled={isSubmitting}
        />
        
        <div class="flex items-center justify-between">
          <label class="flex items-center gap-2 cursor-pointer">
            <input 
              type="checkbox" 
              class="w-4 h-4 rounded border-surface-border bg-surface-highlight 
                     text-primary-500 focus:ring-primary-500/50"
            />
            <span class="text-sm text-secondary-400">Recordarme</span>
          </label>
          
          <a href="#/forgot-password" class="text-sm text-primary-400 hover:text-primary-300">
            ¿Olvidaste tu contraseña?
          </a>
        </div>
        
        <Button
          type="submit"
          variant="accent"
          size="lg"
          loading={isSubmitting}
          disabled={isSubmitting || !username || !password}
        >
          {isSubmitting ? 'Iniciando sesión...' : 'Iniciar sesión'}
        </Button>
      </form>
      
      <div class="pt-4 text-center">
        <p class="text-sm text-secondary-500">
          ¿Necesitas ayuda? 
          <a href="mailto:soporte@jeturing.net" class="text-primary-400 hover:text-primary-300">
            Contacta soporte
          </a>
        </p>
      </div>
    </div>
  </div>
</div>

<style>
  button[type="submit"] {
    width: 100%;
  }
</style>
