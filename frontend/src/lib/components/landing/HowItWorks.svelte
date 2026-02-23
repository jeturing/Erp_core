<script lang="ts">
  import { t } from 'svelte-i18n';
  import { UserPlus, Server, Mail, Rocket } from 'lucide-svelte';

  const steps = [
    { num: 1, icon: UserPlus, title: $t('how_it_works.step1_title'), desc: $t('how_it_works.step1_desc') },
    { num: 2, icon: Server,   title: $t('how_it_works.step2_title'), desc: $t('how_it_works.step2_desc') },
    { num: 3, icon: Mail,     title: $t('how_it_works.step3_title'), desc: $t('how_it_works.step3_desc') },
    { num: 4, icon: Rocket,   title: $t('how_it_works.step4_title'), desc: $t('how_it_works.step4_desc') },
  ];
</script>

<section id="how-it-works" class="bg-white py-24">
  <div class="max-w-5xl mx-auto px-6">
    <div class="text-center mb-16">
      <span class="inline-flex items-center gap-2 rounded-full bg-primary-light text-primary text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">
        {$t('how_it_works.title')}
      </span>
      <h2 class="text-4xl font-jakarta font-bold text-slate-dark mb-4">
        {$t('how_it_works.subtitle')}
      </h2>
    </div>

    <div class="relative">
      <!-- Línea conectora vertical (desktop) -->
      <div class="hidden md:block absolute left-1/2 top-8 bottom-8 w-px bg-gradient-to-b from-primary/30 via-primary/10 to-transparent -translate-x-1/2" aria-hidden="true"></div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-y-16">
        {#each steps as step, i}
          <div
            class="relative flex items-start gap-5 {i % 2 === 1 ? 'md:col-start-2' : 'md:col-start-1'}"
          >
            <!-- Número + ícono -->
            <div class="flex-shrink-0 relative">
              <div class="w-14 h-14 rounded-2xl bg-primary-light flex items-center justify-center shadow-soft">
                <svelte:component this={step.icon} class="w-6 h-6 text-primary" strokeWidth={1.5} />
              </div>
              <span class="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-primary text-white text-xs font-jakarta font-bold flex items-center justify-center shadow-md">
                {step.num}
              </span>
            </div>

            <!-- Texto -->
            <div>
              <h3 class="text-lg font-jakarta font-semibold text-slate-dark mb-1">{step.title}</h3>
              <p class="text-sm font-inter text-slate leading-relaxed">{step.desc}</p>
            </div>
          </div>
        {/each}
      </div>
    </div>

    <div class="text-center mt-16">
      <a href="#/customer-onboarding" class="inline-flex items-center gap-2 bg-primary hover:bg-navy text-white font-jakarta font-semibold text-sm px-6 py-3 rounded-btn shadow-soft hover:shadow-medium transition-all">
        {$t('how_it_works.cta')}
      </a>
    </div>
  </div>
</section>
