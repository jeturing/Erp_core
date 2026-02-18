<script lang="ts">
  import {
    LayoutDashboard, Users, Globe, Server, CreditCard,
    Settings, LogOut, Menu, X, FileText, Route, Shield,
    ExternalLink, Package, UserCheck, Handshake, Target,
    Percent, FileSpreadsheet, Boxes, UsersRound, Receipt,
    Scale, GitCompareArrows, ClipboardList, ShieldCheck, Palette,
    ShoppingBag,
  } from 'lucide-svelte';
  import { auth } from '../stores';

  export let currentRoute: string = 'dashboard';

  let mobileOpen = false;

  type NavItem = { id: string; label: string; icon: any; href: string };

  const navItems: NavItem[] = [
    { id: 'dashboard',      label: 'Dashboard',      icon: LayoutDashboard, href: '#/dashboard' },
    { id: 'tenants',        label: 'Tenants',         icon: Users,           href: '#/tenants' },
    { id: 'domains',        label: 'Domains',         icon: Globe,           href: '#/domains' },
    { id: 'infrastructure', label: 'Infrastructure',  icon: Server,          href: '#/infrastructure' },
    { id: 'billing',        label: 'Billing',         icon: CreditCard,      href: '#/billing' },
    { id: 'plans',          label: 'Planes',          icon: Package,         href: '#/plans' },
    { id: 'clients',        label: 'Clientes',        icon: UserCheck,       href: '#/clients' },
    { id: 'partners',       label: 'Partners',        icon: Handshake,       href: '#/partners' },
    { id: 'leads',          label: 'Leads',           icon: Target,          href: '#/leads' },
    { id: 'commissions',    label: 'Comisiones',      icon: Percent,         href: '#/commissions' },
    { id: 'quotations',     label: 'Cotizaciones',    icon: FileSpreadsheet, href: '#/quotations' },
    { id: 'catalog',        label: 'Catálogo',        icon: ShoppingBag,     href: '#/catalog' },    { id: 'blueprints',      label: 'Blueprints',       icon: Boxes,           href: '#/blueprints' },
    { id: 'seats',           label: 'Seats',            icon: UsersRound,      href: '#/seats' },
    { id: 'invoices',        label: 'Facturas',         icon: Receipt,         href: '#/invoices' },
    { id: 'settlements',     label: 'Liquidaciones',    icon: Scale,           href: '#/settlements' },
    { id: 'reconciliation',  label: 'Conciliación',     icon: GitCompareArrows, href: '#/reconciliation' },
    { id: 'workorders',      label: 'Work Orders',      icon: ClipboardList,   href: '#/workorders' },
    { id: 'audit',           label: 'Auditoría',        icon: ShieldCheck,     href: '#/audit' },
    { id: 'branding',        label: 'Branding',         icon: Palette,         href: '#/branding' },    { id: 'settings',       label: 'Settings',        icon: Settings,        href: '#/settings' },
    { id: 'logs',           label: 'Logs',            icon: FileText,        href: '#/logs' },
    { id: 'tunnels',        label: 'Tunnels',         icon: Route,           href: '#/tunnels' },
    { id: 'roles',          label: 'Roles',           icon: Shield,          href: '#/roles' },
    { id: 'portal',         label: 'Portal Tenant',   icon: ExternalLink,    href: '#/portal' },
  ];

  function handleLogout() {
    auth.logout();
    window.location.hash = '#/login';
  }
</script>

<div class="min-h-screen flex bg-bg-page">
  {#if mobileOpen}
    <button
      type="button"
      class="fixed inset-0 bg-black/50 z-40 lg:hidden cursor-default"
      on:click={() => (mobileOpen = false)}
      aria-label="Cerrar menú"
    ></button>
  {/if}

  <!-- Sidebar -->
  <aside class={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-charcoal flex flex-col transition-transform duration-300 ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
    <!-- Logo -->
    <div class="flex items-center gap-3 px-6 py-6 border-b border-border-dark">
      <div class="w-8 h-8 bg-terracotta flex items-center justify-center flex-shrink-0">
        <span class="text-text-light font-bold font-sans text-sm">S</span>
      </div>
      <span class="font-sans font-bold text-text-light tracking-wide text-sm uppercase">Sajet ERP</span>
    </div>

    <!-- Nav -->
    <nav class="flex-1 px-6 pt-2 overflow-y-auto">
      {#each navItems as item}
        <a
          href={item.href}
          class={currentRoute === item.id ? 'sidebar-link-active' : 'sidebar-link'}
          on:click={() => (mobileOpen = false)}
        >
          <svelte:component this={item.icon} size={18} />
          <span>{item.label}</span>
        </a>
      {/each}
    </nav>

    <!-- User -->
    <div class="px-6 py-5 border-t border-border-dark">
      <div class="flex items-center justify-between gap-3">
        <div class="flex items-center gap-3 min-w-0">
          <div class="w-8 h-8 rounded-full bg-dark-subtle flex items-center justify-center flex-shrink-0">
            <span class="text-gray-400 font-sans font-semibold text-xs">
              {$auth.user?.username?.charAt(0).toUpperCase() || 'U'}
            </span>
          </div>
          <div class="min-w-0">
            <p class="text-sm font-semibold font-sans text-text-light truncate">{$auth.user?.username || 'Admin'}</p>
            <p class="text-[11px] text-gray-500 truncate font-body">{$auth.user?.email || ''}</p>
          </div>
        </div>
        <button type="button" class="p-1.5 text-gray-500 hover:text-error transition-colors flex-shrink-0" on:click={handleLogout} title="Cerrar sesión" aria-label="Cerrar sesión">
          <LogOut size={16} />
        </button>
      </div>
    </div>
  </aside>

  <!-- Main content -->
  <div class="flex-1 flex flex-col min-w-0">
    <!-- Header -->
    <header class="h-16 bg-charcoal border-b border-border-dark flex items-center px-6 gap-4">
      <button type="button" class="lg:hidden p-2 text-gray-400 hover:text-text-light" on:click={() => (mobileOpen = !mobileOpen)} aria-label="Menú">
        {#if mobileOpen}<X size={22} />{:else}<Menu size={22} />{/if}
      </button>

      <span class="hidden lg:block text-[11px] font-semibold uppercase tracking-widest text-gray-500 font-sans">
        {navItems.find(n => n.id === currentRoute)?.label ?? currentRoute}
      </span>

      <div class="ml-auto flex items-center gap-4">
        <a href="/docs" target="_blank" rel="noreferrer" class="hidden sm:block text-[11px] uppercase tracking-widest text-gray-500 hover:text-text-light font-sans transition-colors">
          API Docs
        </a>
        <a href="#/portal" class="btn-accent btn-sm">Portal</a>
      </div>
    </header>

    <main class="flex-1 overflow-auto bg-bg-page">
      <slot />
    </main>
  </div>
</div>
