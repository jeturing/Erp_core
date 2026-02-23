<script lang="ts">
  import { t } from 'svelte-i18n';
  import { Check, Sparkles } from 'lucide-svelte';

  export let plans: any[] = [];
  export let partnerCode: string = '';

  let annual = false;
  let userCount = 1;

  const fallbackPlans = [
    {
      name: $t('pricing.starter_name'),
      description: $t('pricing.starter_desc'),
      monthly_price: 29,
      features: [$t('pricing.starter_users'), $t('pricing.starter_companies'), $t('pricing.starter_modules')],
      is_highlighted: false,
      trial_days: 14,
    },
    {
      name: $t('pricing.growth_name'),
      description: $t('pricing.growth_desc'),
      monthly_price: 79,
      features: [$t('pricing.growth_users'), $t('pricing.growth_companies'), $t('pricing.growth_modules')],
      is_highlighted: true,
      trial_days: 14,
    },
    {
      name: $t('pricing.enterprise_name'),
      description: $t('pricing.enterprise_desc'),
      monthly_price: 199,
      features: [$t('pricing.enterprise_users'), $t('pricing.enterprise_companies'), $t('pricing.enterprise_modules')],
      is_highlighted: false,
      trial_days: 14,
    },
  ];

  $: displayPlans = plans.length > 0 ? plans : fallbackPlans;

  function getPrice(plan: any): number {
    const base = plan.monthly_price || 0;
    const perUser = base * userCount;
    if (annual) {
      const discount = plan.annual_discount_percent || 20;
      return Math.round(perUser * (1 - discount / 100));
    }
    return perUser;
  }

  function goCheckout(plan: any) {
    const params = new URLSearchParams({
      plan: plan.id || plan.name,
      users: String(userCount),
      billing: annual ? 'annual' : 'monthly',
      ...(partnerCode ? { partner: partnerCode } : {}),
    });
    window.location.hash = `#/customer-onboarding?${params.toString()}`;
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

          <h3 class="text-lg font-jakarta font-bold text-slate-dark mb-1">{plan.name}</h3>

          <div class="flex items-baseline gap-1 mb-1">
            <span class="text-4xl font-jakarta font-extrabold text-slate-dark">${getPrice(plan)}</span>
            <span class="text-sm font-inter text-slate">/mo</span>
          </div>

          {#if userCount > 1}
            <p class="text-xs font-inter text-slate mb-4">{userCount} users × ${plan.monthly_price}{annual ? ' (−20%)' : ''}</p>
          {:else}
            <p class="text-xs font-inter text-slate mb-4">{$t('pricing.per_user_month')}</p>
          {/if}

          {#if plan.trial_days}
            <p class="text-xs font-inter text-primary font-medium mb-4">{plan.trial_days} {$t('common.free_trial_days')}</p>
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

    <p class="text-center text-xs font-inter text-slate mt-8">
      {$t('pricing.all_prices_usd')}
    </p>
    <p class="text-center text-xs font-inter text-slate-400 mt-2">
      {$t('pricing.billing_note')}
    </p>
  </div>
</section>
