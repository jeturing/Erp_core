<script lang="ts">
  import { t } from 'svelte-i18n';
  import { Check, Sparkles, Zap } from 'lucide-svelte';

  export let plans: any[] = [];
  export let partnerCode: string = '';

  let annual = false;
  let userCount = 1;

  let pricingByPlan: Record<string, any> = {};
  let pricingLoading = false;
  let pricingError = '';
  let lastPriceKey = '';

  // Map backend fields to frontend-expected shape
  function normalizePlan(p: any): any {
    return {
      ...p,
      name: p.name,
      display_name: p.display_name || p.name,
      base_price: p.base_price ?? p.monthly_price ?? 0,
      price_per_user: p.price_per_user ?? 0,
      included_users: p.included_users ?? 1,
      max_users: p.max_users ?? 0,
      trial_days: p.trial_days ?? 14,
      annual_discount_percent: p.annual_discount_percent ?? 20,
    };
  }

  $: displayPlans = plans.length > 0 ? plans.map(normalizePlan) : [];

  async function updatePrices() {
    if (displayPlans.length === 0) {
      pricingByPlan = {};
      return;
    }

    pricingLoading = true;
    pricingError = '';
    try {
      const results = await Promise.all(
        displayPlans.map(async (plan) => {
          const res = await fetch('/api/public/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              plan_name: plan.name,
              user_count: userCount,
              billing_period: annual ? 'annual' : 'monthly',
              partner_code: partnerCode || null,
            }),
          });

          if (!res.ok) {
            throw new Error(`Pricing error for ${plan.name}`);
          }
          return res.json();
        })
      );

      const next: Record<string, any> = {};
      results.forEach((result) => {
        next[result.plan_name] = result;
      });
      pricingByPlan = next;
    } catch (err) {
      console.error('[Pricing] Failed to calculate pricing', err);
      pricingError = $t('pricing.error');
      pricingByPlan = {};
    } finally {
      pricingLoading = false;
    }
  }

  $: priceKey = `${userCount}|${annual}|${partnerCode}|${displayPlans.map((p) => p.name).join(',')}`;
  $: if (displayPlans.length > 0 && priceKey !== lastPriceKey) {
    lastPriceKey = priceKey;
    updatePrices();
  }

  function displayTotal(plan: any): string {
    const data = pricingByPlan[plan.name];
    if (!data) return '—';
    const total = annual ? data.annual.monthly_equivalent : data.monthly.total;
    return `$${Math.round(total)}`;
  }

  function extraUsersLine(plan: any): string {
    const data = pricingByPlan[plan.name];
    if (!data || !data.extra_users || data.extra_users === 0) return '';
    return `${plan.included_users} incluido${plan.included_users > 1 ? 's' : ''} + ${data.extra_users} × $${plan.price_per_user} extra`;
  }

  function maxUsersLabel(plan: any): string {
    if (!plan.max_users || plan.max_users === 0) return '∞';
    return `máx ${plan.max_users}`;
  }

  function storageLabel(mb: number): string {
    if (!mb || mb === 0) return '∞';
    if (mb >= 1024) return `${mb / 1024} GB`;
    return `${mb} MB`;
  }

  function apiLabel(plan: any): string {
    if (plan.name === 'pro') return 'API lectura';
    return 'API completa';
  }

  function supportLabel(plan: any): string {
    if (plan.name === 'basic') return 'Email';
    if (plan.name === 'pro') return 'Prioritario';
    return '24/7';
  }

  function goCheckout(plan: any) {
    const params = new URLSearchParams({
      plan: plan.id || plan.name,
      users: String(userCount),
      billing: annual ? 'annual' : 'monthly',
      ...(partnerCode ? { partner: partnerCode } : {}),
    });
    window.location.hash = `#/signup?${params.toString()}`;
  }
</script>

<section id="pricing" class="bg-gradient-subtle py-24">
  <div class="max-w-6xl mx-auto px-6">
    <div class="text-center mb-12">
      <span class="inline-flex items-center gap-2 rounded-full bg-primary-light text-primary text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">
        {$t('pricing.title')}
      </span>
      <h2 class="text-4xl font-jakarta font-bold text-slate-dark mb-4 whitespace-pre-line">
        {$t('pricing.headline')}
      </h2>
      <p class="text-base font-inter text-slate max-w-lg mx-auto">
        {$t('pricing.subtitle')}
      </p>
    </div>

    <!-- Controls -->
    <div class="flex flex-col sm:flex-row items-center justify-center gap-6 mb-12">
      <!-- Billing toggle -->
      <div class="flex items-center gap-3 bg-white rounded-full border border-border px-1.5 py-1 shadow-soft">
        <button
          class="text-sm font-inter font-medium px-4 py-1.5 rounded-full transition-all {!annual ? 'bg-primary text-white shadow-sm' : 'text-slate hover:text-slate-dark'}"
          on:click={() => annual = false}
        >
          {$t('pricing.monthly')}
        </button>
        <button
          class="text-sm font-inter font-medium px-4 py-1.5 rounded-full transition-all {annual ? 'bg-primary text-white shadow-sm' : 'text-slate hover:text-slate-dark'}"
          on:click={() => annual = true}
        >
          {$t('pricing.annual')} <span class="text-xs text-emerald-600 font-semibold ml-1">{$t('pricing.save')}</span>
        </button>
      </div>

      <!-- User count selector -->
      <div class="flex items-center gap-3 bg-white rounded-full border border-border px-4 py-2 shadow-soft">
        <label class="text-sm font-inter text-slate">{$t('pricing.users')}:</label>
        <button
          class="w-7 h-7 rounded-full bg-cloud text-slate-dark font-bold text-lg flex items-center justify-center hover:bg-primary-light transition-colors disabled:opacity-40"
          on:click={() => userCount = Math.max(1, userCount - 1)}
          disabled={userCount <= 1}
        >−</button>
        <span class="w-8 text-center text-sm font-jakarta font-bold text-slate-dark">{userCount}</span>
        <button
          class="w-7 h-7 rounded-full bg-cloud text-slate-dark font-bold text-lg flex items-center justify-center hover:bg-primary-light transition-colors"
          on:click={() => userCount += 1}
        >+</button>
      </div>
    </div>

    <!-- Plan Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
      {#each displayPlans as plan}
        <div class="relative rounded-card-lg border bg-white p-6 flex flex-col {plan.is_highlighted ? 'border-primary shadow-elevated ring-2 ring-primary/20' : 'border-border shadow-soft'}">
          {#if plan.is_highlighted}
            <div class="absolute -top-3 left-1/2 -translate-x-1/2">
              <span class="inline-flex items-center gap-1 bg-primary text-white text-xs font-inter font-semibold px-3 py-1 rounded-full shadow-md">
                <Sparkles class="w-3 h-3" />
                {$t('pricing.most_popular')}
              </span>
            </div>
          {/if}

          <h3 class="text-lg font-jakarta font-bold text-slate-dark mb-1">{plan.display_name || plan.name}</h3>

          <!-- Total price -->
          <div class="flex items-baseline gap-1 mb-2">
            {#if pricingLoading}
              <span class="text-3xl font-jakarta font-bold text-slate animate-pulse">…</span>
            {:else}
              <span class="text-4xl font-jakarta font-extrabold text-slate-dark">
                {displayTotal(plan)}
              </span>
              <span class="text-sm font-inter text-slate">/mes</span>
            {/if}
          </div>

          <!-- Price breakdown -->
          <div class="text-xs font-inter text-slate mb-3 bg-cloud rounded-lg px-3 py-2 space-y-0.5">
            <p class="font-semibold text-slate-dark">Base: ${plan.base_price}/mes</p>
            <p>+${plan.price_per_user}/usuario adicional</p>
            <p class="text-slate-400">{plan.included_users} usuario{plan.included_users > 1 ? 's' : ''} incluido{plan.included_users > 1 ? 's' : ''} · Hasta {maxUsersLabel(plan)}</p>
            {#if !pricingLoading && extraUsersLine(plan)}
              <p class="text-primary font-medium pt-1 border-t border-border">{extraUsersLine(plan)}</p>
            {/if}
            {#if annual}
              <p class="text-emerald-600 font-medium pt-1 border-t border-border">{plan.annual_discount_percent}% descuento anual</p>
            {/if}
          </div>

          <!-- Specs chips -->
          <div class="flex flex-wrap gap-1.5 mb-4">
            <span class="inline-flex items-center gap-1 text-[11px] font-inter font-medium bg-cloud text-slate-dark rounded-full px-2.5 py-1">
              💾 {storageLabel(plan.max_storage_mb)}
            </span>
            <span class="inline-flex items-center gap-1 text-[11px] font-inter font-medium bg-cloud text-slate-dark rounded-full px-2.5 py-1">
              🔒 Backups ∞
            </span>
            <span class="inline-flex items-center gap-1 text-[11px] font-inter font-medium bg-cloud text-slate-dark rounded-full px-2.5 py-1">
              ⚡ {apiLabel(plan)}
            </span>
            <span class="inline-flex items-center gap-1 text-[11px] font-inter font-medium bg-cloud text-slate-dark rounded-full px-2.5 py-1">
              💬 {supportLabel(plan)}
            </span>
          </div>

          <!-- Trial badge -->
          <p class="text-xs font-inter text-primary font-semibold mb-4">
            ✓ {plan.trial_days} días de prueba gratis · Sin tarjeta
          </p>

          <ul class="space-y-2.5 mb-6 flex-1">
            {#each plan.features || [] as feat}
              <li class="flex items-start gap-2 text-sm font-inter text-slate-dark">
                <Check class="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" strokeWidth={2.5} />
                <span>{feat}</span>
              </li>
            {/each}
          </ul>

          <button
            on:click={() => goCheckout(plan)}
            class="w-full text-center text-sm font-jakarta font-semibold py-2.5 rounded-btn transition-all {plan.is_highlighted
              ? 'bg-primary hover:bg-navy text-white shadow-soft hover:shadow-medium'
              : 'border border-primary text-primary hover:bg-primary hover:text-white'}"
          >
            {$t('pricing.start_trial')}
          </button>
        </div>
      {/each}
    </div>

    {#if pricingError}
      <p class="text-center text-xs font-inter text-rose-600 mt-8">
        {pricingError}
      </p>
    {/if}
    <p class="text-center text-xs font-inter text-slate mt-8">
      {$t('pricing.all_prices_usd')}
    </p>
    <p class="text-center text-xs font-inter text-slate-400 mt-2">
      {$t('pricing.billing_note')}
    </p>

    <!-- FEL / e-CF notice -->
    <div class="mt-10 rounded-card-lg border border-amber-200 bg-amber-50 p-5 flex gap-4 items-start">
      <div class="flex-shrink-0 w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center">
        <Zap class="w-5 h-5 text-amber-600" />
      </div>
      <div class="flex-1">
        <p class="text-sm font-jakarta font-bold text-amber-900 mb-1">
          ⚡ ¿Necesitas facturación electrónica DGII (e-CF)?
        </p>
        <p class="text-sm font-inter text-amber-800 leading-relaxed mb-2">
          Todos los planes incluyen integración nativa con <strong>República FEL</strong>, proveedor certificado ante la DGII.
          El módulo e-CF se activa sobre cualquier plan — el costo del timbre fiscal depende de tu volumen de documentos
          y se factura directamente por el PAC. <strong>Nos encargamos de toda la implementación técnica sin costo adicional.</strong>
        </p>
        <div class="flex flex-wrap gap-3">
          <a
            href="#/contact?subject=fel"
            class="inline-flex items-center gap-1 text-xs font-inter font-semibold text-amber-700 hover:text-amber-900 transition-colors"
          >
            Consultar integración FEL →
          </a>
          <span class="text-xs font-inter text-amber-600">·</span>
          <a
            href="https://republicafel.com"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center gap-1 text-xs font-inter font-semibold text-amber-700 hover:text-amber-900 transition-colors"
          >
            Ver tarifas República FEL ↗
          </a>
        </div>
      </div>
    </div>
  </div>
</section>
