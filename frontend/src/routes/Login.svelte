<script lang="ts">
  import { auth } from '../lib/stores';
  import { Button, Input, Spinner } from '../lib/components';
  import { onMount } from 'svelte';
  import { api } from '../lib/api';
  
  let username = '';
  let password = '';
  let loginType: 'admin' | 'tenant' = 'tenant'; // Default a portal de cliente
  let isSubmitting = false;
  let error = '';
  
  // Redirect if already logged in
  onMount(() => {
    if ($auth.user) {
      redirectByRole($auth.user.role);
    }
  });
  
  function redirectByRole(role: string) {
    if (role === 'admin') {
      window.location.hash = '#/dashboard';
    } else {
      window.location.hash = '#/portal';
    }
  }
  
  async function handleSubmit(e: Event) {
    e.preventDefault();
    error = '';
    isSubmitting = true;
    
    try {
      // Llamar API directamente para controlar el rol
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: username,
          password: password,
          role: loginType
        }),
        credentials: 'include'
      });
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Credenciales inválidas');
      }
      
      const data = await response.json();
      
      // Leer el token de la cookie y guardarlo
      setTimeout(async () => {
        const match = document.cookie.match(/access_token=([^;]+)/);
        if (match) {
          api.setToken(match[1]);
        }
        
        // Inicializar auth store
        await auth.init();
        
        // Redirigir según el rol
        redirectByRole(data.role);
      }, 100);
      
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
        {#if loginType === 'admin'}
          ERP Core
          <span class="block text-accent-400">Management Platform</span>
        {:else}
          Portal de
          <span class="block text-accent-400">Cliente</span>
        {/if}
      </h1>
      <p class="text-lg text-primary-200 max-w-md">
        {#if loginType === 'admin'}
          Gestiona tus tenants, suscripciones e infraestructura desde un único panel de control.
        {:else}
          Accede a tus servicios, gestiona tus dominios y consulta tu facturación.
        {/if}
      </p>
      
      <!-- Features -->
      <div class="grid grid-cols-2 gap-4 pt-4">
        {#if loginType === 'admin'}
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
        {:else}
          <div class="flex items-center gap-2 text-primary-200">
            <svg class="w-5 h-5 text-accent-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <span>Dominios personalizados</span>
          </div>
          <div class="flex items-center gap-2 text-primary-200">
            <svg class="w-5 h-5 text-accent-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <span>SSL gratuito</span>
          </div>
          <div class="flex items-center gap-2 text-primary-200">
            <svg class="w-5 h-5 text-accent-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <span>Soporte 24/7</span>
          </div>
          <div class="flex items-center gap-2 text-primary-200">
            <svg class="w-5 h-5 text-accent-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <span>Odoo ERP incluido</span>
          </div>
        {/if}
      </div>
    </div>
    
    <p class="text-sm text-primary-400">
      © 2026 Jeturing Technologies. All rights reserved.
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
      
      <!-- Login Type Selector -->
      <div class="flex rounded-lg bg-surface-highlight p-1">
        <button
          type="button"
          class="flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all duration-200
                 {loginType === 'tenant' 
                   ? 'bg-accent-500 text-primary-900' 
                   : 'text-secondary-400 hover:text-white'}"
          on:click={() => loginType = 'tenant'}
        >
          Portal de Cliente
        </button>
        <button
          type="button"
          class="flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all duration-200
                 {loginType === 'admin' 
                   ? 'bg-accent-500 text-primary-900' 
                   : 'text-secondary-400 hover:text-white'}"
          on:click={() => loginType = 'admin'}
        >
          Administrador
        </button>
      </div>
      
      <div class="text-center lg:text-left">
        <h2 class="text-2xl font-bold text-white">Iniciar sesión</h2>
        <p class="mt-2 text-secondary-400">
          {#if loginType === 'admin'}
            Accede al panel de administración
          {:else}
            Accede a tu portal de cliente
          {/if}
        </p>
      </div>
      
      <form on:submit={handleSubmit} class="space-y-6">
        {#if error}
          <div class="p-4 rounded-lg bg-error/10 border border-error/20">
            <p class="text-sm text-error">{error}</p>
          </div>
        {/if}
        
        <Input
          label={loginType === 'admin' ? 'Usuario' : 'Email'}
          name="username"
          type={loginType === 'admin' ? 'text' : 'email'}
          placeholder={loginType === 'admin' ? 'admin' : 'tu@email.com'}
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
