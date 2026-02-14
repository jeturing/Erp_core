<script lang="ts">
  import {
    LayoutDashboard,
    Users,
    Globe,
    Server,
    CreditCard,
    Settings,
    LogOut,
    ChevronLeft,
    Menu,
    Bell,
    Search,
    ExternalLink,
    FileText,
    Route,
    Shield,
  } from 'lucide-svelte';
  import { auth } from '../stores';

  export let currentRoute: string = 'dashboard';

  let sidebarCollapsed = false;
  let mobileMenuOpen = false;

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, href: '#/dashboard' },
    { id: 'tenants', label: 'Tenants', icon: Users, href: '#/tenants' },
    { id: 'domains', label: 'Domains', icon: Globe, href: '#/domains' },
    { id: 'infrastructure', label: 'Infrastructure', icon: Server, href: '#/infrastructure' },
    { id: 'billing', label: 'Billing', icon: CreditCard, href: '#/billing' },
    { id: 'settings', label: 'Settings', icon: Settings, href: '#/settings' },
    { id: 'logs', label: 'Logs', icon: FileText, href: '#/logs' },
    { id: 'tunnels', label: 'Tunnels', icon: Route, href: '#/tunnels' },
    { id: 'roles', label: 'Roles', icon: Shield, href: '#/roles' },
    { id: 'portal', label: 'Portal tenant', icon: ExternalLink, href: '#/portal' },
  ];

  function handleLogout() {
    auth.logout();
    window.location.hash = '#/login';
  }

  function toggleSidebar() {
    sidebarCollapsed = !sidebarCollapsed;
  }

  function closeMobileMenu() {
    mobileMenuOpen = false;
  }
</script>

<div class="min-h-screen flex bg-surface-dark">
  {#if mobileMenuOpen}
    <div
      class="fixed inset-0 bg-black/50 z-40 lg:hidden"
      on:click={closeMobileMenu}
      on:keydown={(event) => event.key === 'Escape' && closeMobileMenu()}
      role="button"
      tabindex="0"
      aria-label="Cerrar menu"
    ></div>
  {/if}

  <aside
    class={`
      fixed lg:static inset-y-0 left-0 z-50
      bg-surface-card border-r border-surface-border
      flex flex-col
      transition-all duration-300
      ${sidebarCollapsed ? 'w-20' : 'w-64'}
      ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
    `}
  >
    <div class="h-16 flex items-center justify-between px-4 border-b border-surface-border">
      <a href="#/dashboard" class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-lg bg-accent-500 flex items-center justify-center flex-shrink-0">
          <span class="text-primary-900 font-bold text-lg">J</span>
        </div>
        {#if !sidebarCollapsed}
          <span class="text-xl font-bold text-white">Jeturing</span>
        {/if}
      </a>

      <button
        type="button"
        class="hidden lg:flex p-1.5 rounded-lg text-secondary-400 hover:text-white hover:bg-surface-highlight transition-colors"
        on:click={toggleSidebar}
        aria-label={sidebarCollapsed ? 'Expandir sidebar' : 'Colapsar sidebar'}
      >
        <ChevronLeft size={20} class={`transition-transform ${sidebarCollapsed ? 'rotate-180' : ''}`} />
      </button>
    </div>

    <nav class="flex-1 py-4 px-3 overflow-y-auto">
      <ul class="space-y-1">
        {#each navItems as item}
          <li>
            <a
              href={item.href}
              class={currentRoute === item.id ? 'sidebar-link-active' : 'sidebar-link'}
              on:click={closeMobileMenu}
              title={sidebarCollapsed ? item.label : ''}
            >
              <svelte:component this={item.icon} size={20} />
              {#if !sidebarCollapsed}
                <span>{item.label}</span>
              {/if}
            </a>
          </li>
        {/each}
      </ul>

    </nav>

    <div class="p-3 border-t border-surface-border">
      <div class={`flex items-center ${sidebarCollapsed ? 'justify-center' : 'gap-3'}`}>
        <div class="w-9 h-9 rounded-full bg-primary-500/20 flex items-center justify-center flex-shrink-0">
          <span class="text-primary-300 font-medium text-sm">{$auth.user?.username?.charAt(0).toUpperCase() || 'U'}</span>
        </div>
        {#if !sidebarCollapsed}
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-white truncate">{$auth.user?.username || 'Usuario'}</p>
            <p class="text-xs text-secondary-500 truncate">{$auth.user?.email || 'sin-email'}</p>
          </div>
          <button
            type="button"
            class="p-1.5 rounded-lg text-secondary-400 hover:text-error hover:bg-error/10 transition-colors"
            on:click={handleLogout}
            title="Cerrar sesion"
            aria-label="Cerrar sesion"
          >
            <LogOut size={18} />
          </button>
        {/if}
      </div>
    </div>
  </aside>

  <div class="flex-1 flex flex-col min-w-0">
    <header class="h-16 bg-surface-card border-b border-surface-border flex items-center justify-between px-4 lg:px-6">
      <button
        type="button"
        class="lg:hidden p-2 rounded-lg text-secondary-400 hover:text-white hover:bg-surface-highlight transition-colors"
        on:click={() => (mobileMenuOpen = true)}
        aria-label="Abrir menu"
      >
        <Menu size={24} />
      </button>

      <div class="hidden sm:flex flex-1 max-w-md mx-4">
        <div class="relative w-full">
          <Search size={18} class="absolute left-3 top-1/2 -translate-y-1/2 text-secondary-500" />
          <input
            type="search"
            placeholder="Buscar tenants, dominios..."
            class="w-full pl-10 pr-4 py-2 bg-surface-highlight border border-surface-border rounded-lg
                   text-sm text-white placeholder-secondary-500
                   focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
          />
        </div>
      </div>

      <div class="flex items-center gap-3">
        <button
          type="button"
          class="relative p-2 rounded-lg text-secondary-400 hover:text-white hover:bg-surface-highlight transition-colors"
          aria-label="Notificaciones"
        >
          <Bell size={20} />
          <span class="absolute top-1.5 right-1.5 w-2 h-2 bg-accent-500 rounded-full"></span>
        </button>

        <div class="hidden sm:block h-6 w-px bg-surface-border"></div>

        <a href="/docs" target="_blank" rel="noreferrer" class="hidden sm:block text-sm text-secondary-400 hover:text-white transition-colors">
          API Docs
        </a>
      </div>
    </header>

    <main class="flex-1 overflow-auto">
      <slot />
    </main>
  </div>
</div>
