<script lang="ts">
  import { onMount } from 'svelte';
  
  let isMenuOpen = false;
  let activeSection = 'hero';
  let scrollY = 0;
  
  const plans = [
    {
      name: 'Basic',
      price: '29',
      description: 'Perfecto para pequeñas empresas',
      features: [
        'Sajet ERP completo',
        '1 dominio personalizado',
        '5 GB almacenamiento',
        'Soporte por email',
        'Backups diarios',
        'SSL gratuito'
      ],
      highlighted: false,
      cta: 'Comenzar Gratis'
    },
    {
      name: 'Pro',
      price: '79',
      description: 'Para empresas en crecimiento',
      features: [
        'Todo de Basic +',
        '5 dominios personalizados',
        '25 GB almacenamiento',
        'Soporte prioritario 24/7',
        'Backups cada 6 horas',
        'Recursos dedicados',
        'API acceso completo',
        'Integraciones avanzadas'
      ],
      highlighted: true,
      cta: 'Elegir Pro'
    },
    {
      name: 'Enterprise',
      price: '199',
      description: 'Soluciones a medida',
      features: [
        'Todo de Pro +',
        'Dominios ilimitados',
        '100 GB almacenamiento',
        'Gerente de cuenta dedicado',
        'SLA 99.9% garantizado',
        'Servidor dedicado',
        'Personalización completa',
        'Onboarding personalizado'
      ],
      highlighted: false,
      cta: 'Contactar Ventas'
    }
  ];
  
  const features = [
    {
      icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4',
      title: 'Sajet ERP Completo',
      description: 'Accede a todos los módulos: ventas, compras, inventario, contabilidad, CRM y más.'
    },
    {
      icon: 'M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9',
      title: 'Dominios Personalizados',
      description: 'Usa tu propio dominio con SSL gratuito y configuración automática de DNS.'
    },
    {
      icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
      title: 'Seguridad Empresarial',
      description: 'Autenticación 2FA, backups automáticos, encriptación de datos y cumplimiento GDPR.'
    },
    {
      icon: 'M13 10V3L4 14h7v7l9-11h-7z',
      title: 'Alto Rendimiento',
      description: 'Infraestructura optimizada con CDN global para tiempos de carga ultrarrápidos.'
    },
    {
      icon: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4',
      title: 'Backups Automáticos',
      description: 'Tus datos siempre seguros con backups automáticos y restauración en un clic.'
    },
    {
      icon: 'M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z',
      title: 'Soporte 24/7',
      description: 'Equipo de expertos disponible para ayudarte cuando lo necesites.'
    }
  ];
  
  const testimonials = [
    {
      quote: 'Jeturing nos permitió digitalizar toda nuestra operación en semanas. El soporte es excepcional.',
      author: 'María García',
      role: 'CEO, TechStart Solutions',
      avatar: 'MG'
    },
    {
      quote: 'La mejor inversión que hemos hecho. El ERP es potente y la plataforma muy estable.',
      author: 'Carlos Rodríguez',
      role: 'Director de Operaciones, LogiPro',
      avatar: 'CR'
    },
    {
      quote: 'Migramos desde otro proveedor y la diferencia es abismal. Totalmente recomendado.',
      author: 'Ana Martínez',
      role: 'Gerente General, Comercial AM',
      avatar: 'AM'
    }
  ];
  
  const stats = [
    { value: '500+', label: 'Empresas activas' },
    { value: '99.9%', label: 'Uptime garantizado' },
    { value: '24/7', label: 'Soporte disponible' },
    { value: '50+', label: 'Países alcanzados' }
  ];
  
  onMount(() => {
    const handleScroll = () => {
      scrollY = window.scrollY;
      
      // Update active section based on scroll position
      const sections = ['hero', 'features', 'pricing', 'testimonials', 'contact'];
      for (const section of sections) {
        const el = document.getElementById(section);
        if (el) {
          const rect = el.getBoundingClientRect();
          if (rect.top <= 100 && rect.bottom >= 100) {
            activeSection = section;
            break;
          }
        }
      }
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  });
  
  function scrollToSection(sectionId: string) {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
    isMenuOpen = false;
  }
</script>

<svelte:head>
  <title>Jeturing ERP - Gestión Empresarial en la Nube</title>
  <meta name="description" content="Plataforma ERP empresarial en la nube. Gestiona tu negocio desde cualquier lugar con dominios personalizados y soporte 24/7." />
</svelte:head>

<div class="min-h-screen bg-slate-950 text-white">
  <!-- Navigation -->
  <nav class="fixed top-0 left-0 right-0 z-50 transition-all duration-300 {scrollY > 50 ? 'bg-slate-900/95 backdrop-blur-md shadow-lg' : 'bg-transparent'}">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16 md:h-20">
        <!-- Logo -->
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-500/25">
            <span class="text-slate-900 font-bold text-xl">J</span>
          </div>
          <span class="text-xl font-bold">Jeturing</span>
        </div>
        
        <!-- Desktop Navigation -->
        <div class="hidden md:flex items-center gap-8">
          <button on:click={() => scrollToSection('features')} 
                  class="text-sm font-medium transition-colors {activeSection === 'features' ? 'text-emerald-400' : 'text-slate-300 hover:text-white'}">
            Características
          </button>
          <button on:click={() => scrollToSection('pricing')} 
                  class="text-sm font-medium transition-colors {activeSection === 'pricing' ? 'text-emerald-400' : 'text-slate-300 hover:text-white'}">
            Precios
          </button>
          <button on:click={() => scrollToSection('testimonials')} 
                  class="text-sm font-medium transition-colors {activeSection === 'testimonials' ? 'text-emerald-400' : 'text-slate-300 hover:text-white'}">
            Testimonios
          </button>
          <button on:click={() => scrollToSection('contact')} 
                  class="text-sm font-medium transition-colors {activeSection === 'contact' ? 'text-emerald-400' : 'text-slate-300 hover:text-white'}">
            Contacto
          </button>
        </div>
        
        <!-- CTA Buttons -->
        <div class="hidden md:flex items-center gap-4">
          <a href="#/login" class="text-sm font-medium text-slate-300 hover:text-white transition-colors">
            Iniciar Sesión
          </a>
          <a href="#/login" class="px-5 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-900 font-semibold rounded-lg transition-all shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40">
            Prueba Gratis
          </a>
        </div>
        
        <!-- Mobile Menu Button -->
        <button on:click={() => isMenuOpen = !isMenuOpen} class="md:hidden p-2 text-slate-300 hover:text-white">
          <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {#if isMenuOpen}
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            {:else}
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            {/if}
          </svg>
        </button>
      </div>
    </div>
    
    <!-- Mobile Menu -->
    {#if isMenuOpen}
      <div class="md:hidden bg-slate-900/95 backdrop-blur-md border-t border-slate-800">
        <div class="px-4 py-4 space-y-3">
          <button on:click={() => scrollToSection('features')} class="block w-full text-left px-4 py-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg">
            Características
          </button>
          <button on:click={() => scrollToSection('pricing')} class="block w-full text-left px-4 py-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg">
            Precios
          </button>
          <button on:click={() => scrollToSection('testimonials')} class="block w-full text-left px-4 py-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg">
            Testimonios
          </button>
          <button on:click={() => scrollToSection('contact')} class="block w-full text-left px-4 py-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg">
            Contacto
          </button>
          <hr class="border-slate-800" />
          <a href="#/login" class="block px-4 py-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg">
            Iniciar Sesión
          </a>
          <a href="#/login" class="block px-4 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-900 font-semibold text-center rounded-lg">
            Prueba Gratis
          </a>
        </div>
      </div>
    {/if}
  </nav>
  
  <!-- Hero Section -->
  <section id="hero" class="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
    <!-- Background -->
    <div class="absolute inset-0 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950"></div>
    <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiMyMDI5M2EiIGZpbGwtb3BhY2l0eT0iMC40Ij48cGF0aCBkPSJNMzYgMzRoLTJWMGgydjM0em0tNCAwSDI4VjBoNHYzNHptLTYgMGgtNFYwaDR2MzR6bS02IDBoLTRWMGg0djM0em0tNiAwSDh2LTJoNnYyem0wLTRIOHYtMmg2djJ6bS0xMCAwaC00di0yaDR2MnptMCAyaC00djJoNHYtMnptMTYgMGgtNHYyaDR2LTJ6bTQgMGgtMnYyaDJ2LTJ6bTQgMGgtMnYyaDJ2LTJ6bTQtMmgtMnYyaDJ2LTJ6bTQtMmgtMnYyaDJ2LTJ6bTQtMmgtMnYyaDJ2LTJ6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-30"></div>
    
    <!-- Gradient Orbs -->
    <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-emerald-500/20 rounded-full blur-3xl animate-pulse"></div>
    <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-teal-500/20 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
    
    <div class="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
      <!-- Badge -->
      <div class="inline-flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-full mb-8">
        <span class="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
        <span class="text-sm text-slate-300">+500 empresas ya confían en nosotros</span>
      </div>
      
      <!-- Headline -->
      <h1 class="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold leading-tight mb-6">
        <span class="bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
          Tu negocio en la nube
        </span>
        <br />
        <span class="bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-400 bg-clip-text text-transparent">
          con poder ilimitado
        </span>
      </h1>
      
      <!-- Subheadline -->
      <p class="text-lg sm:text-xl text-slate-400 max-w-3xl mx-auto mb-10">
        Gestiona ventas, inventario, contabilidad y más con Sajet ERP. 
        Despliega en minutos con tu propio dominio y soporte experto 24/7.
      </p>
      
      <!-- CTA Buttons -->
      <div class="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
        <a href="#/login" class="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-900 font-bold text-lg rounded-xl transition-all shadow-2xl shadow-emerald-500/25 hover:shadow-emerald-500/40 hover:scale-105">
          Comenzar Gratis
        </a>
        <button on:click={() => scrollToSection('features')} class="w-full sm:w-auto px-8 py-4 bg-slate-800/50 hover:bg-slate-800 border border-slate-700 text-white font-semibold text-lg rounded-xl transition-all flex items-center justify-center gap-2">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Ver Demo
        </button>
      </div>
      
      <!-- Stats -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto">
        {#each stats as stat}
          <div class="text-center">
            <div class="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent mb-1">
              {stat.value}
            </div>
            <div class="text-sm text-slate-500">{stat.label}</div>
          </div>
        {/each}
      </div>
    </div>
    
    <!-- Scroll Indicator -->
    <div class="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
      <svg class="w-6 h-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
      </svg>
    </div>
  </section>
  
  <!-- Features Section -->
  <section id="features" class="py-24 relative">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Section Header -->
      <div class="text-center mb-16">
        <span class="inline-block px-4 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-emerald-400 text-sm font-medium mb-4">
          Características
        </span>
        <h2 class="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
          Todo lo que tu empresa necesita
        </h2>
        <p class="text-lg text-slate-400 max-w-2xl mx-auto">
          Una plataforma completa para gestionar cada aspecto de tu negocio
        </p>
      </div>
      
      <!-- Features Grid -->
      <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
        {#each features as feature, i}
          <div class="group relative bg-slate-900/50 hover:bg-slate-800/50 border border-slate-800 hover:border-emerald-500/30 rounded-2xl p-8 transition-all duration-300 hover:-translate-y-1">
            <!-- Icon -->
            <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border border-emerald-500/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg class="w-7 h-7 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d={feature.icon} />
              </svg>
            </div>
            
            <!-- Content -->
            <h3 class="text-xl font-semibold mb-3 group-hover:text-emerald-400 transition-colors">
              {feature.title}
            </h3>
            <p class="text-slate-400 leading-relaxed">
              {feature.description}
            </p>
            
            <!-- Hover Gradient -->
            <div class="absolute inset-0 rounded-2xl bg-gradient-to-br from-emerald-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
          </div>
        {/each}
      </div>
    </div>
  </section>
  
  <!-- Pricing Section -->
  <section id="pricing" class="py-24 relative bg-slate-900/50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Section Header -->
      <div class="text-center mb-16">
        <span class="inline-block px-4 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-emerald-400 text-sm font-medium mb-4">
          Precios
        </span>
        <h2 class="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
          Planes para cada etapa
        </h2>
        <p class="text-lg text-slate-400 max-w-2xl mx-auto">
          Sin costos ocultos. Cancela cuando quieras. Prueba gratis por 14 días.
        </p>
      </div>
      
      <!-- Pricing Cards -->
      <div class="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
        {#each plans as plan, i}
          <div class="relative {plan.highlighted ? 'md:-mt-4 md:mb-4' : ''}">
            {#if plan.highlighted}
              <div class="absolute -top-4 left-0 right-0 flex justify-center">
                <span class="px-4 py-1 bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-900 text-sm font-semibold rounded-full">
                  Más Popular
                </span>
              </div>
            {/if}
            
            <div class="h-full bg-slate-900 border {plan.highlighted ? 'border-emerald-500/50 shadow-xl shadow-emerald-500/10' : 'border-slate-800'} rounded-2xl p-8 {plan.highlighted ? 'ring-2 ring-emerald-500/20' : ''}">
              <div class="text-center mb-8">
                <h3 class="text-xl font-semibold mb-2">{plan.name}</h3>
                <p class="text-slate-400 text-sm mb-4">{plan.description}</p>
                <div class="flex items-baseline justify-center gap-1">
                  <span class="text-4xl font-bold">${plan.price}</span>
                  <span class="text-slate-400">/mes</span>
                </div>
              </div>
              
              <ul class="space-y-4 mb-8">
                {#each plan.features as feature}
                  <li class="flex items-start gap-3">
                    <svg class="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                    <span class="text-slate-300">{feature}</span>
                  </li>
                {/each}
              </ul>
              
              <a href="#/login" 
                 class="block w-full py-3 text-center font-semibold rounded-xl transition-all
                        {plan.highlighted 
                          ? 'bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-900 shadow-lg shadow-emerald-500/25' 
                          : 'bg-slate-800 hover:bg-slate-700 text-white border border-slate-700'}">
                {plan.cta}
              </a>
            </div>
          </div>
        {/each}
      </div>
      
      <!-- Enterprise CTA -->
      <div class="mt-16 text-center">
        <p class="text-slate-400 mb-4">
          ¿Necesitas una solución personalizada para tu empresa?
        </p>
        <a href="mailto:enterprise@jeturing.net" class="inline-flex items-center gap-2 text-emerald-400 hover:text-emerald-300 font-medium">
          Habla con nuestro equipo de ventas
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
          </svg>
        </a>
      </div>
    </div>
  </section>
  
  <!-- Testimonials Section -->
  <section id="testimonials" class="py-24 relative">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Section Header -->
      <div class="text-center mb-16">
        <span class="inline-block px-4 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-emerald-400 text-sm font-medium mb-4">
          Testimonios
        </span>
        <h2 class="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
          Lo que dicen nuestros clientes
        </h2>
        <p class="text-lg text-slate-400 max-w-2xl mx-auto">
          Empresas reales obteniendo resultados reales
        </p>
      </div>
      
      <!-- Testimonials Grid -->
      <div class="grid md:grid-cols-3 gap-8">
        {#each testimonials as testimonial}
          <div class="bg-slate-900/50 border border-slate-800 rounded-2xl p-8 hover:border-slate-700 transition-colors">
            <!-- Quote -->
            <svg class="w-10 h-10 text-emerald-500/30 mb-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z" />
            </svg>
            
            <p class="text-lg text-slate-300 mb-6 leading-relaxed">
              "{testimonial.quote}"
            </p>
            
            <!-- Author -->
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-slate-900 font-bold">
                {testimonial.avatar}
              </div>
              <div>
                <div class="font-semibold">{testimonial.author}</div>
                <div class="text-sm text-slate-400">{testimonial.role}</div>
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  </section>
  
  <!-- Contact/CTA Section -->
  <section id="contact" class="py-24 relative overflow-hidden">
    <!-- Background -->
    <div class="absolute inset-0 bg-gradient-to-br from-emerald-900/20 via-slate-900 to-teal-900/20"></div>
    
    <div class="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
      <h2 class="text-3xl sm:text-4xl md:text-5xl font-bold mb-6">
        ¿Listo para transformar tu negocio?
      </h2>
      <p class="text-lg text-slate-400 mb-10 max-w-2xl mx-auto">
        Únete a más de 500 empresas que ya confían en Jeturing para gestionar sus operaciones. 
        Comienza tu prueba gratuita de 14 días hoy.
      </p>
      
      <!-- CTA Form -->
      <div class="max-w-md mx-auto">
        <form class="flex flex-col sm:flex-row gap-4">
          <input 
            type="email" 
            placeholder="tu@email.com"
            class="flex-1 px-5 py-4 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
          />
          <button type="submit" class="px-8 py-4 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-900 font-bold rounded-xl transition-all shadow-lg shadow-emerald-500/25 whitespace-nowrap">
            Comenzar Gratis
          </button>
        </form>
        <p class="text-sm text-slate-500 mt-4">
          Sin tarjeta de crédito requerida • Cancela en cualquier momento
        </p>
      </div>
      
      <!-- Contact Info -->
      <div class="mt-16 flex flex-col sm:flex-row items-center justify-center gap-8 text-slate-400">
        <a href="mailto:info@jeturing.net" class="flex items-center gap-2 hover:text-emerald-400 transition-colors">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          info@jeturing.net
        </a>
        <a href="tel:+34900000000" class="flex items-center gap-2 hover:text-emerald-400 transition-colors">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
          </svg>
          +34 900 000 000
        </a>
      </div>
    </div>
  </section>
  
  <!-- Footer -->
  <footer class="bg-slate-950 border-t border-slate-800 py-12">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
        <!-- Brand -->
        <div class="col-span-2 md:col-span-1">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center">
              <span class="text-slate-900 font-bold text-xl">J</span>
            </div>
            <span class="text-xl font-bold">Jeturing</span>
          </div>
          <p class="text-slate-400 text-sm">
            Plataforma ERP empresarial para empresas modernas.
          </p>
        </div>
        
        <!-- Links -->
        <div>
          <h4 class="font-semibold mb-4">Producto</h4>
          <ul class="space-y-2 text-sm text-slate-400">
            <li><a href="#features" class="hover:text-emerald-400 transition-colors">Características</a></li>
            <li><a href="#pricing" class="hover:text-emerald-400 transition-colors">Precios</a></li>
            <li><a href="#" class="hover:text-emerald-400 transition-colors">Integraciones</a></li>
            <li><a href="#" class="hover:text-emerald-400 transition-colors">API</a></li>
          </ul>
        </div>
        
        <div>
          <h4 class="font-semibold mb-4">Empresa</h4>
          <ul class="space-y-2 text-sm text-slate-400">
            <li><a href="#" class="hover:text-emerald-400 transition-colors">Sobre nosotros</a></li>
            <li><a href="#" class="hover:text-emerald-400 transition-colors">Blog</a></li>
            <li><a href="#" class="hover:text-emerald-400 transition-colors">Carreras</a></li>
            <li><a href="#contact" class="hover:text-emerald-400 transition-colors">Contacto</a></li>
          </ul>
        </div>
        
        <div>
          <h4 class="font-semibold mb-4">Legal</h4>
          <ul class="space-y-2 text-sm text-slate-400">
            <li><a href="#" class="hover:text-emerald-400 transition-colors">Privacidad</a></li>
            <li><a href="#" class="hover:text-emerald-400 transition-colors">Términos</a></li>
            <li><a href="#" class="hover:text-emerald-400 transition-colors">Cookies</a></li>
            <li><a href="#" class="hover:text-emerald-400 transition-colors">GDPR</a></li>
          </ul>
        </div>
      </div>
      
      <!-- Bottom -->
      <div class="flex flex-col md:flex-row items-center justify-between pt-8 border-t border-slate-800">
        <p class="text-sm text-slate-500">
          © 2026 Jeturing Technologies. Todos los derechos reservados.
        </p>
        
        <!-- Social Links -->
        <div class="flex items-center gap-4 mt-4 md:mt-0">
          <a href="#" class="w-10 h-10 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors">
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"/>
            </svg>
          </a>
          <a href="#" class="w-10 h-10 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors">
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
            </svg>
          </a>
          <a href="#" class="w-10 h-10 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors">
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
          </a>
        </div>
      </div>
    </div>
  </footer>
</div>

<style>
  :global(html) {
    scroll-behavior: smooth;
  }
</style>
