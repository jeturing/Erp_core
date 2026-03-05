<script lang="ts">
  import { t } from 'svelte-i18n';
  import { Check, Sparkles } from 'lucide-svelte';

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

          <div class="flex items-baseline gap-1 mb-1">
            {#if pricingLoading}
              <span class="text-3xl font-jakarta font-bold text-slate">…</span>
            {:else if pricingByPlan[plan.name]}
              <span class="text-4xl font-jakarta font-extrabold text-slate-dark">
                ${annual
                  ? pricingByPlan[plan.name].annual.monthly_equivalent
                  : pricingByPlan[plan.name].monthly.total}
              </span>
              <span class="text-sm font-inter text-slate">{$t('pricing.per_month')}</span>
            {:else}
              <span class="text-3xl font-jakarta font-bold text-slate">—</span>
            {/if}
          </div>

          <div class="text-xs font-inter text-slate mb-4 space-y-1">
            <p>{$t('pricing.base_label')}: ${plan.base_price}{$t('pricing.per_month')}</p>
            <p>{$t('pricing.per_user_additional', { price: plan.price_per_user })}</p>
            <p>{$t('pricing.included_users', { count: plan.included_users })}</p>
            {#if annual}
              <p class="text-emerald-600">{$t('pricing.annual_note', { discount: plan.annual_discount_percent || 20 })}</p>
            {/if}
          </div>

          {#if plan.trial_days}
            <p class="text-xs font-inter text-primary font-medium mb-4">
              {$t('common.free_trial_days', { days: plan.trial_days })}
            </p>
          {/if}

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
  </div>
</section>
