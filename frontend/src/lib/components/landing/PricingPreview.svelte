<script lang="ts">
  import { t } from 'svelte-i18n';
  import { Check, Sparkles, Zap } from 'lucide-svelte';
  import { goto } from '$app/navigation';
  import { metaEvents } from '$lib/meta';

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

  $: priceKey = `${userCount}|${annual}|${displayPlans.map((p) => p.name).join(',')}`;
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
    // Track InitiateCheckout event
    const planPrice = (plan.base_price || 0) + (plan.price_per_user || 0) * (userCount || 1);
    metaEvents.initiateCheckout(plan.id || plan.name, plan.display_name || plan.name, planPrice);
    
    const params = new URLSearchParams({
      mode: 'tenant',
      plan: plan.id || plan.name,
      users: String(userCount),
      billing: annual ? 'annual' : 'monthly',
      ...(partnerCode ? { partner: partnerCode } : {}),
    });
    goto(`/signup?${params.toString()}`);
  }
</script>

<section id="pricing" style="background:#f5f5f7; padding:clamp(80px,10vw,140px) 24px;">
  <div class="max-w-6xl mx-auto px-6">
    <div class="text-center mb-12">
      <span style="display:inline-flex;align-items:center;gap:6px;border-radius:4px;background:rgba(0,59,115,0.08);color:#003B73;font-size:12px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;padding:5px 14px;margin-bottom:16px;">
        {$t('pricing.title')}
      </span>
      <h2 style="font-family:'Plus Jakarta Sans','Inter',system-ui;font-size:clamp(1.8rem,4.5vw,2.8rem);font-weight:700;letter-spacing:-0.035em;line-height:1.08;color:#061b31;margin:0 0 16px;">
        {$t('pricing.headline')}
      </h2>
      <p style="font-size:17px;font-weight:300;color:#64748d;max-width:480px;margin:0 auto;">
        {$t('pricing.subtitle')}
      </p>
    </div>

      <!-- Controls -->
      <div class="flex flex-col sm:flex-row items-center justify-center gap-6 mb-12">
        <!-- Billing toggle -->
        <div style="display:flex;align-items:center;gap:4px;background:#ffffff;border:1px solid #e5edf5;border-radius:8px;padding:4px;box-shadow:rgba(50,50,93,0.12) 0px 4px 12px -4px,rgba(0,0,0,0.06) 0px 2px 6px -2px;">
          <button
            style="font-size:13px;font-weight:500;padding:6px 16px;border-radius:6px;border:none;cursor:pointer;transition:all 0.2s;background:{!annual?'#003B73':'transparent'};color:{!annual?'#ffffff':'#64748d'};"
            on:click={() => annual = false}
          >
            {$t('pricing.monthly')}
          </button>
          <button
            style="font-size:13px;font-weight:500;padding:6px 16px;border-radius:6px;border:none;cursor:pointer;transition:all 0.2s;background:{annual?'#003B73':'transparent'};color:{annual?'#ffffff':'#64748d'};"
            on:click={() => annual = true}
          >
            {$t('pricing.annual')} <span style="font-size:11px;color:#00a36e;font-weight:600;margin-left:4px;">{$t('pricing.save')}</span>
          </button>
        </div>

      <!-- User count selector -->
      <div style="display:flex;align-items:center;gap:10px;background:#ffffff;border:1px solid #e5edf5;border-radius:8px;padding:8px 16px;box-shadow:rgba(50,50,93,0.12) 0px 4px 12px -4px,rgba(0,0,0,0.06) 0px 2px 6px -2px;">
        <span style="font-size:13px;color:#64748d;">{$t('pricing.users')}:</span>
        <button
          style="width:28px;height:28px;border-radius:50%;background:#f0f7ff;color:#003B73;font-weight:700;font-size:18px;display:flex;align-items:center;justify-content:center;border:none;cursor:pointer;transition:background 0.2s;"
          on:click={() => userCount = Math.max(1, userCount - 1)}
          disabled={userCount <= 1}
          aria-label="Reducir usuarios"
        >−</button>
        <span style="width:32px;text-align:center;font-size:14px;font-weight:700;color:#061b31;font-variant-numeric:tabular-nums;">{userCount}</span>
        <button
          style="width:28px;height:28px;border-radius:50%;background:#f0f7ff;color:#003B73;font-weight:700;font-size:18px;display:flex;align-items:center;justify-content:center;border:none;cursor:pointer;transition:background 0.2s;"
          on:click={() => userCount += 1}
          aria-label="Aumentar usuarios"
        >+</button>
      </div>
    </div>

    <!-- Plan Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
      {#each displayPlans as plan}
        <div style="
          position:relative; border-radius:8px; background:#ffffff;
          border:{plan.is_highlighted?'2px solid #003B73':'1px solid #e5edf5'};
          padding:{plan.is_highlighted?'28px 28px':'24px 24px'}; display:flex; flex-direction:column;
          box-shadow:{plan.is_highlighted?'rgba(50,50,93,0.35) 0px 30px 60px -12px, rgba(0,0,0,0.2) 0px 18px 36px -18px':'rgba(50,50,93,0.18) 0px 20px 40px -20px, rgba(0,0,0,0.08) 0px 10px 24px -12px'};
          transform:{plan.is_highlighted?'translateY(-4px)':'none'};
        ">
          {#if plan.is_highlighted}
            <div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%);">
              <span style="display:inline-flex;align-items:center;gap:4px;background:#003B73;color:#00FF9F;font-size:11px;font-weight:600;padding:4px 12px;border-radius:4px;letter-spacing:0.04em;text-transform:uppercase;">
                <Sparkles class="w-3 h-3" />
                {$t('pricing.most_popular')}
              </span>
            </div>
          {/if}

          <h3 style="font-size:16px;font-weight:700;color:#061b31;margin:0 0 4px;letter-spacing:-0.02em;">{plan.display_name || plan.name}</h3>

          <!-- Total price -->
          <div style="display:flex;align-items:baseline;gap:4px;margin-bottom:8px;">
            {#if pricingLoading}
              <span style="font-size:2rem;font-weight:700;color:#64748d;">…</span>
            {:else}
              <span style="font-size:2.5rem;font-weight:800;color:#061b31;letter-spacing:-0.04em;font-variant-numeric:tabular-nums;">
                {displayTotal(plan)}
              </span>
              <span style="font-size:13px;color:#64748d;">/mes</span>
            {/if}
          </div>

          <!-- Price breakdown -->
          <div style="font-size:11px;color:#64748d;margin-bottom:12px;background:#f8fafc;border-radius:6px;padding:10px 12px;line-height:1.8;border:1px solid #e5edf5;">
            <p style="font-weight:600;color:#273951;margin:0;">Base: ${plan.base_price}/mes</p>
            <p style="margin:0;">+${plan.price_per_user}/usuario adicional</p>
            <p style="margin:0;color:#94a3b8;">{plan.included_users} usuario{plan.included_users > 1 ? 's' : ''} incluido{plan.included_users > 1 ? 's' : ''} · Hasta {maxUsersLabel(plan)}</p>
            {#if !pricingLoading && extraUsersLine(plan)}
              <p style="color:#003B73;font-weight:500;margin:4px 0 0;padding-top:4px;border-top:1px solid #e5edf5;">{extraUsersLine(plan)}</p>
            {/if}
            {#if annual}
              <p style="color:#00a36e;font-weight:500;margin:4px 0 0;padding-top:4px;border-top:1px solid #e5edf5;">{plan.annual_discount_percent}% descuento anual</p>
            {/if}
          </div>

          <!-- Specs chips -->
          <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px;">
            {#each [
              `💾 ${storageLabel(plan.max_storage_mb)}`,
              '🔒 Backups ∞',
              `⚡ ${apiLabel(plan)}`,
              `💬 ${supportLabel(plan)}`
            ] as chip}
              <span style="font-size:11px;font-weight:500;background:#f0f7ff;color:#273951;border-radius:4px;padding:3px 8px;border:1px solid #e5edf5;">{chip}</span>
            {/each}
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
            style="
              width:100%; text-align:center; font-size:14px; font-weight:600; padding:12px 24px;
              border-radius:6px; cursor:pointer; transition:all 0.2s; margin-top:auto;
              background:{plan.is_highlighted?'#003B73':'transparent'};
              color:{plan.is_highlighted?'#00FF9F':'#003B73'};
              border:{plan.is_highlighted?'none':'2px solid #003B73'};
              box-shadow:{plan.is_highlighted?'rgba(50,50,93,0.25) 0px 6px 16px -4px':'none'};
            "
            on:mouseenter={e => {
              if (plan.is_highlighted) { e.currentTarget.style.background='#004d99'; e.currentTarget.style.boxShadow='rgba(50,50,93,0.35) 0px 10px 24px -4px'; }
              else { e.currentTarget.style.background='#003B73'; e.currentTarget.style.color='#00FF9F'; }
            }}
            on:mouseleave={e => {
              if (plan.is_highlighted) { e.currentTarget.style.background='#003B73'; e.currentTarget.style.boxShadow='rgba(50,50,93,0.25) 0px 6px 16px -4px'; }
              else { e.currentTarget.style.background='transparent'; e.currentTarget.style.color='#003B73'; }
            }}
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
            href="mailto:ventas@sajet.us?subject=Consulta%20integracion%20FEL%20-%20SAJET"
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
