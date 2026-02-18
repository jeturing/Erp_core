<script lang="ts">
  import {
    Zap, Shield, ChartColumn, Globe, Headphones, Users,
    CircleCheck, ArrowRight, Star
  } from 'lucide-svelte';

  let email = '';

  function goToLogin() {
    window.location.hash = '#/login';
  }

  function handleCTA() {
    window.location.hash = '#/login';
  }

  const features = [
    {
      icon: Zap,
      title: 'Implementación Rápida',
      desc: 'Tu instancia Odoo lista en minutos. Sin configuraciones complicadas, sin infraestructura que gestionar.',
    },
    {
      icon: Shield,
      title: 'Seguridad Empresarial',
      desc: 'Backups automáticos, SSL incluido, y datos encriptados. Tu información siempre protegida.',
    },
    {
      icon: ChartColumn,
      title: 'Escalabilidad Total',
      desc: 'Crece sin límites. Desde startups hasta corporaciones, Sajet se adapta a tu ritmo.',
    },
    {
      icon: Globe,
      title: 'Dominio Personalizado',
      desc: 'Usa tu propio dominio. Accede a tu ERP desde miempresa.com con SSL automático.',
    },
    {
      icon: Headphones,
      title: 'Soporte 24/7',
      desc: 'Equipo experto disponible siempre. Resolvemos problemas antes de que los notes.',
    },
    {
      icon: Users,
      title: 'Multi-empresa',
      desc: 'Gestiona varias empresas desde una sola plataforma. Permisos granulares por usuario.',
    },
  ];

  const testimonials = [
    {
      name: 'Carlos Mendoza',
      role: 'CEO, TechVentures MX',
      text: 'Migramos nuestro ERP a Sajet y en 2 semanas ya estábamos operando al 100%. El soporte es excepcional.',
      stars: 5,
    },
    {
      name: 'Ana Rodríguez',
      role: 'CFO, Distribuidora Norte',
      text: 'La facturación electrónica integrada nos ahorró horas de trabajo manual. Totalmente recomendado.',
      stars: 5,
    },
    {
      name: 'Miguel Torres',
      role: 'CTO, Logística Express',
      text: 'Escalamos de 10 a 80 usuarios sin ningún problema. La plataforma nunca falla.',
      stars: 5,
    },
  ];

  const stats = [
    { value: '500+', label: 'Empresas' },
    { value: '99.9%', label: 'Uptime' },
    { value: '24/7', label: 'Soporte' },
    { value: '56+', label: 'Partners' },
  ];

  const navLinks = ['Características', 'Precios', 'Partners', 'Contacto'];
</script>

<div class="min-h-screen bg-[#020617] text-white font-sans">
  <!-- Navbar -->
  <nav class="fixed top-0 left-0 right-0 z-50 bg-[#020617]/90 backdrop-blur-sm border-b border-white/5">
    <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
      <!-- Logo -->
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded bg-[#16a34a] flex items-center justify-center">
          <span class="text-white font-bold text-sm">S</span>
        </div>
        <span class="text-white font-bold tracking-[0.08em] text-sm">SAJET</span>
      </div>

      <!-- Nav links -->
      <div class="hidden md:flex items-center gap-8">
        {#each navLinks as link}
          <button type="button" class="text-sm text-gray-400 hover:text-white transition-colors bg-transparent border-none cursor-pointer p-0">{link}</button>
        {/each}
      </div>

      <!-- CTA buttons -->
      <div class="flex items-center gap-3">
        <button
          class="text-sm text-gray-300 hover:text-white transition-colors px-3 py-1.5"
          on:click={goToLogin}
        >
          Iniciar Sesión
        </button>
        <button
          class="text-sm font-semibold bg-[#16a34a] hover:bg-[#15803d] text-white px-4 py-2 rounded-md transition-colors"
          on:click={handleCTA}
        >
          Comenzar Gratis
        </button>
      </div>
    </div>
  </nav>

  <!-- Hero Section -->
  <section class="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
    <!-- Background gradient -->
    <div class="absolute inset-0 bg-gradient-to-b from-[#020617] via-[#0a1628] to-[#020617] pointer-events-none"></div>
    <div class="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-[#16a34a]/5 blur-3xl pointer-events-none"></div>

    <div class="relative z-10 max-w-4xl mx-auto px-6 text-center">
      <!-- Badge -->
      <div class="inline-flex items-center gap-2 rounded-full border border-[#16a34a]/30 bg-[#16a34a]/10 px-4 py-1.5 mb-8">
        <div class="w-1.5 h-1.5 rounded-full bg-[#16a34a] animate-pulse"></div>
        <span class="text-xs font-semibold text-[#4ade80] tracking-[0.08em] uppercase">Plataforma ERP Cloud #1 en LATAM</span>
      </div>

      <!-- Headline -->
      <h1 class="text-5xl sm:text-6xl font-bold text-white leading-tight mb-6">
        Tu negocio en la nube<br />
        <span class="text-[#4ade80]">con poder ilimitado</span>
      </h1>

      <!-- Subtext -->
      <p class="text-lg text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
        Sajet ERP te da todo lo que necesitas para gestionar tu empresa: facturación, inventario, CRM,
        RRHH y más. En la nube, sin instalaciones, sin complicaciones.
      </p>

      <!-- CTA buttons -->
      <div class="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
        <button
          class="flex items-center gap-2 bg-[#16a34a] hover:bg-[#15803d] text-white font-semibold text-sm px-8 py-3.5 rounded-md transition-colors w-full sm:w-auto"
          on:click={handleCTA}
        >
          Empezar Ahora — Gratis
          <ArrowRight class="w-4 h-4" />
        </button>
        <button
          class="flex items-center gap-2 border border-white/10 text-gray-300 hover:text-white hover:border-white/30 font-medium text-sm px-8 py-3.5 rounded-md transition-colors w-full sm:w-auto"
          on:click={goToLogin}
        >
          Ver Demo
        </button>
      </div>

      <!-- Stats badges -->
      <div class="flex flex-wrap justify-center gap-4">
        {#each stats as stat}
          <div class="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-5 py-2">
            <span class="text-base font-bold text-white">{stat.value}</span>
            <span class="text-xs text-gray-400">{stat.label}</span>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- Features Section -->
  <section class="bg-[#020617] py-24">
    <div class="max-w-6xl mx-auto px-6">
      <div class="text-center mb-16">
        <span class="text-xs font-semibold tracking-[0.12em] text-[#4ade80] uppercase mb-3 block">Características</span>
        <h2 class="text-4xl font-bold text-white mb-4">Todo lo que tu empresa necesita</h2>
        <p class="text-gray-400 max-w-xl mx-auto">
          Una plataforma completa que crece contigo. Sin costos ocultos, sin limitaciones artificiales.
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {#each features as feature}
          <div class="rounded-xl border border-white/5 bg-white/[0.03] hover:bg-white/[0.06] hover:border-[#16a34a]/20 p-6 transition-all group">
            <div class="w-10 h-10 rounded-lg bg-[#16a34a]/10 flex items-center justify-center mb-4 group-hover:bg-[#16a34a]/20 transition-colors">
              <svelte:component this={feature.icon} class="w-5 h-5 text-[#4ade80]" />
            </div>
            <h3 class="text-base font-semibold text-white mb-2">{feature.title}</h3>
            <p class="text-sm text-gray-400 leading-relaxed">{feature.desc}</p>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- Testimonials Section -->
  <section class="bg-[#030d1f] py-24">
    <div class="max-w-6xl mx-auto px-6">
      <div class="text-center mb-16">
        <span class="text-xs font-semibold tracking-[0.12em] text-[#4ade80] uppercase mb-3 block">Testimonios</span>
        <h2 class="text-4xl font-bold text-white mb-4">Lo que dicen nuestros clientes</h2>
        <p class="text-gray-400 max-w-xl mx-auto">Más de 500 empresas confían en Sajet para gestionar su negocio.</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        {#each testimonials as t}
          <div class="rounded-xl border border-white/5 bg-white/[0.03] p-6 flex flex-col gap-4">
            <!-- Stars -->
            <div class="flex gap-1">
              {#each Array(t.stars) as _}
                <Star class="w-4 h-4 fill-[#fbbf24] text-[#fbbf24]" />
              {/each}
            </div>
            <!-- Text -->
            <p class="text-sm text-gray-300 leading-relaxed flex-1">"{t.text}"</p>
            <!-- Author -->
            <div class="flex items-center gap-3 pt-2 border-t border-white/5">
              <div class="w-8 h-8 rounded-full bg-[#16a34a]/20 flex items-center justify-center flex-shrink-0">
                <span class="text-xs font-bold text-[#4ade80]">{t.name[0]}</span>
              </div>
              <div>
                <p class="text-xs font-semibold text-white">{t.name}</p>
                <p class="text-[10px] text-gray-500">{t.role}</p>
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- CTA Section -->
  <section class="bg-[#020617] py-24">
    <div class="max-w-3xl mx-auto px-6 text-center">
      <h2 class="text-4xl font-bold text-white mb-4">¿Listo para transformar tu negocio?</h2>
      <p class="text-gray-400 mb-10">Únete a más de 500 empresas que ya usan Sajet ERP. Sin tarjeta de crédito.</p>

      <div class="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
        <input
          type="email"
          class="flex-1 bg-white/5 border border-white/10 text-white placeholder-gray-500 text-sm px-4 py-3 rounded-md focus:outline-none focus:border-[#16a34a]/50"
          placeholder="tu@empresa.com"
          bind:value={email}
        />
        <button
          class="bg-[#16a34a] hover:bg-[#15803d] text-white font-semibold text-sm px-6 py-3 rounded-md transition-colors whitespace-nowrap flex items-center gap-2 justify-center"
          on:click={handleCTA}
        >
          Comenzar Gratis
          <ArrowRight class="w-4 h-4" />
        </button>
      </div>

      <p class="text-xs text-gray-500 mt-4">
        Al registrarte, aceptas nuestros
        <a href="/terms" class="text-[#4ade80] hover:underline">Términos de Servicio</a>
        y
        <a href="/privacy" class="text-[#4ade80] hover:underline">Política de Privacidad</a>.
      </p>
    </div>
  </section>

  <!-- Footer -->
  <footer class="bg-[#010b18] border-t border-white/5 py-12">
    <div class="max-w-6xl mx-auto px-6">
      <div class="flex flex-col md:flex-row items-center justify-between gap-6 mb-8">
        <!-- Logo + tagline -->
        <div class="flex flex-col items-center md:items-start gap-2">
          <div class="flex items-center gap-2">
            <div class="w-7 h-7 rounded bg-[#16a34a] flex items-center justify-center">
              <span class="text-white font-bold text-xs">S</span>
            </div>
            <span class="text-white font-bold tracking-[0.08em] text-sm">SAJET</span>
          </div>
          <p class="text-xs text-gray-500">ERP Cloud para empresas latinoamericanas</p>
        </div>

        <!-- Nav links -->
        <div class="flex flex-wrap justify-center gap-6">
          {#each navLinks as link}
            <button type="button" class="text-xs text-gray-500 hover:text-gray-300 transition-colors bg-transparent border-none cursor-pointer p-0">{link}</button>
          {/each}
          <a href="/privacy" class="text-xs text-gray-500 hover:text-gray-300 transition-colors">Privacidad</a>
          <a href="/terms" class="text-xs text-gray-500 hover:text-gray-300 transition-colors">Términos</a>
        </div>

        <!-- Social -->
        <div class="flex items-center gap-4">
          <a href="https://twitter.com/sajet" target="_blank" rel="noopener noreferrer" class="text-gray-500 hover:text-white transition-colors text-xs">Twitter</a>
          <a href="https://linkedin.com/company/sajet" target="_blank" rel="noopener noreferrer" class="text-gray-500 hover:text-white transition-colors text-xs">LinkedIn</a>
          <a href="https://github.com/jeturing" target="_blank" rel="noopener noreferrer" class="text-gray-500 hover:text-white transition-colors text-xs">GitHub</a>
        </div>
      </div>

      <div class="border-t border-white/5 pt-6 text-center">
        <p class="text-xs text-gray-600">
          &copy; {new Date().getFullYear()} Sajet ERP. Todos los derechos reservados. Hecho con amor en USA.
        </p>
      </div>
    </div>
  </footer>
</div>
