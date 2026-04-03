<script lang="ts">
  import {
    LayoutDashboard, Users, Globe, Server, CreditCard, Key,
    Settings as SettingsIcon, LogOut, Menu, X, FileText, Route, Shield,
    ExternalLink, Package, UserCheck, Handshake, Target,
    Percent, FileSpreadsheet, Boxes, UsersRound, Receipt,
    Scale, GitCompareArrows, ClipboardList, ShieldCheck, Palette,
    ShoppingBag, ChevronDown, Sliders, Mail, BarChart2,
    Languages, MessageCircle, FileType, ArrowRightLeft,
    Moon, Sun, Activity, Zap, Rocket, Gauge
  } from 'lucide-svelte';
  import { auth } from '../stores';
  import { goto } from '$app/navigation';
  import { darkMode } from '../stores/darkMode';
  import { onMount } from 'svelte';

  onMount(() => darkMode.init());

  const { currentRoute = 'dashboard' }: { currentRoute?: string } = $props();

  let mobileOpen = $state(false);

  type NavItem = { id: string; label: string; icon: any; href: string };
  type NavGroup = { id: string; label: string; icon: any; children: NavItem[] };
  type NavEntry = NavItem | NavGroup;

  function isGroup(entry: NavEntry): entry is NavGroup {
    return 'children' in entry;
  }

  const navStructure: NavEntry[] = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },

    {
      id: 'grp-infra', label: 'Infraestructura', icon: Server,
      children: [
        { id: 'tenants',        label: 'Tenants',    icon: Users,  href: '/tenants' },
        { id: 'domains',        label: 'Dominios',   icon: Globe,  href: '/domains' },
        { id: 'infrastructure', label: 'Servidores', icon: Server, href: '/infrastructure' },
        { id: 'tunnels',        label: 'Tunnels',    icon: Route,  href: '/tunnels' },
        { id: 'migrations',     label: 'Migraciones', icon: ArrowRightLeft, href: '/migrations' },
      ],
    },

    {
      id: 'grp-comercial', label: 'Comercial', icon: Handshake,
      children: [
        { id: 'partners',   label: 'Partners',    icon: Handshake,       href: '/partners' },
        { id: 'leads',      label: 'Leads',        icon: Target,          href: '/leads' },
        { id: 'clients',    label: 'Clientes',     icon: UserCheck,       href: '/clients' },
        { id: 'quotations', label: 'Cotizaciones', icon: FileSpreadsheet, href: '/quotations' },
        { id: 'catalog',    label: 'Catálogo',     icon: ShoppingBag,     href: '/catalog' },
      ],
    },

    {
      id: 'grp-billing', label: 'Facturación', icon: CreditCard,
      children: [
        { id: 'billing',        label: 'Billing',       icon: CreditCard,       href: '/billing' },
        { id: 'plans',          label: 'Planes',        icon: Package,          href: '/plans' },
        { id: 'invoices',       label: 'Facturas',      icon: Receipt,          href: '/invoices' },
        { id: 'seats',          label: 'Seats',         icon: UsersRound,       href: '/seats' },
        { id: 'settlements',    label: 'Liquidaciones', icon: Scale,            href: '/settlements' },
        { id: 'reconciliation', label: 'Conciliación',  icon: GitCompareArrows,  href: '/reconciliation' },
        { id: 'dispersion',    label: 'Dispersión',    icon: ArrowRightLeft,    href: '/dispersion' },
        { id: 'quotas',         label: 'Quotas',         icon: Gauge,             href: '/quotas' },
        { id: 'plan-governance', label: 'Gobernanza',    icon: ShieldCheck,       href: '/plan-governance' },
      ],
    },

    {
      id: 'grp-ops', label: 'Operaciones', icon: ClipboardList,
      children: [
        { id: 'workorders',  label: 'Work Orders', icon: ClipboardList, href: '/workorders' },
        { id: 'blueprints',  label: 'Blueprints',  icon: Boxes,         href: '/blueprints' },
        { id: 'commissions', label: 'Comisiones',   icon: Percent,       href: '/commissions' },
        { id: 'branding',    label: 'Branding',     icon: Palette,       href: '/branding' },
      ],
    },

    {
      id: 'grp-analytics', label: 'Análisis', icon: BarChart2,
      children: [
        { id: 'reports',        label: 'Reportes',        icon: BarChart2, href: '/reports' },
        { id: 'communications', label: 'Comunicaciones',  icon: Mail,      href: '/communications' },
      ],
    },

    {
      id: 'grp-landing', label: 'Landing / i18n', icon: Languages,
      children: [
        { id: 'testimonials',     label: 'Testimonios',      icon: MessageCircle, href: '/testimonials' },
        { id: 'landing-sections', label: 'Secciones Landing', icon: FileType,      href: '/landing-sections' },
        { id: 'translations',     label: 'Traducciones',      icon: Languages,     href: '/translations' },
      ],
    },

    {
      id: 'grp-security', label: 'Seguridad', icon: Shield,
      children: [
        { id: 'session-monitoring', label: 'DSAM Monitor', icon: Activity, href: '/session-monitoring' },
      ],
    },

    {
      id: 'grp-admin', label: 'Administración', icon: SettingsIcon,
      children: [
        { id: 'settings',          label: 'Settings',          icon: SettingsIcon, href: '/settings' },
        { id: 'onboarding-config', label: 'Config. Onboarding',icon: Sliders,      href: '/onboarding-config' },
        { id: 'neural-users',      label: 'Neural Users ✨',    icon: Zap,          href: '/neural-users' },
        { id: 'roles',             label: 'Roles',              icon: Shield,       href: '/roles' },
        { id: 'admin-users',       label: 'Usuarios Admin',     icon: UsersRound,   href: '/admin-users' },
        { id: 'agreements',        label: 'Acuerdos',           icon: FileText,     href: '/agreements' },
        { id: 'developer-portal',  label: 'Developer Portal',   icon: Rocket,       href: '/developer-portal' },
        { id: 'api-keys',          label: 'API Keys',           icon: Key,          href: '/api-keys' },
        { id: 'stripe-connect',    label: 'Stripe Connect',     icon: CreditCard,   href: '/stripe-connect' },
        { id: 'audit',             label: 'Auditoría',          icon: ShieldCheck,  href: '/audit' },
        { id: 'logs',              label: 'Logs',               icon: FileText,     href: '/logs' },
        { id: 'portal',            label: 'Portal Tenant',      icon: ExternalLink, href: '/portal' },
      ],
    },
  ];

  // Flat list for header breadcrumb
  const allNavItems: NavItem[] = navStructure.flatMap(e => isGroup(e) ? e.children : [e]);

  // Which group owns a route
  function findGroupForRoute(route: string): string | null {
    for (const entry of navStructure) {
      if (isGroup(entry) && entry.children.some(c => c.id === route)) return entry.id;
    }
    return null;
  }

  // Expanded groups — persisted in localStorage
  let expandedGroups = $state<Set<string>>(new Set());

  function initExpandedGroups() {
    try {
      const saved = localStorage.getItem('sidebar_expanded');
      if (saved) expandedGroups = new Set(JSON.parse(saved));
    } catch { /* ignore */ }
    const activeGroup = findGroupForRoute(currentRoute);
    if (activeGroup) expandedGroups.add(activeGroup);
    expandedGroups = new Set(expandedGroups);
  }

  initExpandedGroups();

  $effect(() => {
    const grp = findGroupForRoute(currentRoute);
    if (grp && !expandedGroups.has(grp)) {
      expandedGroups.add(grp);
      expandedGroups = new Set(expandedGroups);
    }
  });

  function toggleGroup(groupId: string) {
    if (expandedGroups.has(groupId)) expandedGroups.delete(groupId);
    else expandedGroups.add(groupId);
    expandedGroups = new Set(expandedGroups);
    try { localStorage.setItem('sidebar_expanded', JSON.stringify([...expandedGroups])); } catch { /* */ }
  }

  function groupHasActive(group: NavGroup): boolean {
    return group.children.some(c => c.id === currentRoute);
  }

  function handleLogout() {
    auth.logout();
    goto('/login');
  }
</script>

<div class="min-h-screen flex bg-bg-page">
  {#if mobileOpen}
    <button
      type="button"
      class="fixed inset-0 bg-black/50 z-40 lg:hidden cursor-default"
      onclick={() => (mobileOpen = false)}
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
    <nav class="flex-1 px-3 pt-2 overflow-y-auto sidebar-nav">
      {#each navStructure as entry}
        {#if isGroup(entry)}
          <!-- Group header -->
          <button
            type="button"
            class="sidebar-group-toggle {groupHasActive(entry) ? 'sidebar-group-active' : ''}"
            onclick={() => toggleGroup(entry.id)}
            aria-expanded={expandedGroups.has(entry.id)}
          >
            <div class="flex items-center gap-2.5 min-w-0">
              <svelte:component this={entry.icon} size={16} class="shrink-0 opacity-60" />
              <span class="truncate">{entry.label}</span>
            </div>
            <div class="flex items-center gap-1.5">
              {#if !expandedGroups.has(entry.id)}
                <span class="sidebar-group-badge">{entry.children.length}</span>
              {/if}
              <ChevronDown
                size={14}
                class="shrink-0 transition-transform duration-200 {expandedGroups.has(entry.id) ? 'rotate-180' : ''}"
              />
            </div>
          </button>

          <!-- Group children -->
          {#if expandedGroups.has(entry.id)}
            <div class="sidebar-group-children">
              {#each entry.children as item}
                <a
                  href={item.href}
                  class={currentRoute === item.id ? 'sidebar-child-active' : 'sidebar-child'}
                  onclick={() => (mobileOpen = false)}
                >
                  <svelte:component this={item.icon} size={15} />
                  <span>{item.label}</span>
                </a>
              {/each}
            </div>
          {/if}
        {:else}
          <!-- Direct link (Dashboard) -->
          <a
            href={entry.href}
            class="sidebar-direct-link {currentRoute === entry.id ? 'sidebar-direct-active' : ''}"
            onclick={() => (mobileOpen = false)}
          >
            <svelte:component this={entry.icon} size={18} />
            <span>{entry.label}</span>
          </a>
        {/if}
      {/each}
    </nav>

    <!-- User -->
    <div class="px-4 py-4 border-t border-border-dark">
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
        <button type="button" class="p-1.5 text-gray-500 hover:text-error transition-colors flex-shrink-0" onclick={handleLogout} title="Cerrar sesión" aria-label="Cerrar sesión">
          <LogOut size={16} />
        </button>
      </div>
    </div>
  </aside>

  <!-- Main content -->
  <div class="flex-1 flex flex-col min-w-0">
    <!-- Header -->
    <header class="h-16 bg-charcoal border-b border-border-dark flex items-center px-6 gap-4">
      <button type="button" class="lg:hidden p-2 text-gray-400 hover:text-text-light" onclick={() => (mobileOpen = !mobileOpen)} aria-label="Menú">
        {#if mobileOpen}<X size={22} />{:else}<Menu size={22} />{/if}
      </button>

      <span class="hidden lg:block text-[11px] font-semibold uppercase tracking-widest text-gray-500 font-sans">
        {allNavItems.find(n => n.id === currentRoute)?.label ?? currentRoute}
      </span>

      <div class="ml-auto flex items-center gap-4">
        <a href="/docs" target="_blank" rel="noreferrer" class="hidden sm:block text-[11px] uppercase tracking-widest text-gray-500 hover:text-text-light font-sans transition-colors">
          API Docs
        </a>
        <!-- Dark mode toggle -->
        <button
          type="button"
          onclick={() => darkMode.toggle()}
          class="p-2 rounded-md text-gray-400 hover:text-text-light hover:bg-white/10 transition-colors"
          title={$darkMode ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
          aria-label="Toggle dark mode"
        >
          {#if $darkMode}
            <Sun size={16} />
          {:else}
            <Moon size={16} />
          {/if}
        </button>
        <a href="/portal" class="btn-accent btn-sm">Portal</a>
      </div>
    </header>

    <main class="flex-1 overflow-auto bg-bg-page">
      <slot />
    </main>
  </div>
</div>

<style>
  .sidebar-nav::-webkit-scrollbar { width: 4px; }
  .sidebar-nav::-webkit-scrollbar-track { background: transparent; }
  .sidebar-nav::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }

  .sidebar-direct-link {
    display: flex; align-items: center; gap: 0.625rem;
    padding: 0.5rem 0.75rem; margin-bottom: 0.25rem; border-radius: 0.375rem;
    font-size: 0.8125rem; font-weight: 500; color: #9ca3af;
    transition: all 150ms; text-decoration: none;
  }
  .sidebar-direct-link:hover { color: #e5e7eb; background: rgba(255,255,255,0.05); }
  .sidebar-direct-active {
    color: #f5f5f5 !important; background: rgba(192,90,60,0.2) !important;
    border-left: 3px solid #C05A3C;
  }

  .sidebar-group-toggle {
    display: flex; align-items: center; justify-content: space-between;
    width: 100%; padding: 0.4375rem 0.75rem; margin-top: 0.5rem; margin-bottom: 0.125rem;
    border-radius: 0.375rem; font-size: 0.6875rem; font-weight: 700;
    letter-spacing: 0.05em; text-transform: uppercase; color: #6b7280;
    transition: all 150ms; border: none; background: transparent;
    cursor: pointer; text-align: left;
  }
  .sidebar-group-toggle:hover { color: #9ca3af; background: rgba(255,255,255,0.03); }
  .sidebar-group-active { color: #d1d5db !important; }

  .sidebar-group-badge {
    font-size: 0.625rem; font-weight: 600;
    min-width: 1.125rem; height: 1.125rem;
    display: inline-flex; align-items: center; justify-content: center;
    border-radius: 9999px; background: rgba(255,255,255,0.08); color: #6b7280;
  }

  .sidebar-group-children {
    padding-left: 0.5rem; margin-bottom: 0.25rem;
    border-left: 1px solid rgba(255,255,255,0.06); margin-left: 1.25rem;
  }

  .sidebar-child {
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.375rem 0.625rem; border-radius: 0.375rem;
    font-size: 0.8125rem; color: #9ca3af;
    transition: all 150ms; text-decoration: none;
  }
  .sidebar-child:hover { color: #e5e7eb; background: rgba(255,255,255,0.05); }
  .sidebar-child-active {
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.375rem 0.625rem; border-radius: 0.375rem;
    font-size: 0.8125rem; font-weight: 600; color: #f5f5f5;
    background: rgba(192,90,60,0.15); text-decoration: none;
  }
</style>
