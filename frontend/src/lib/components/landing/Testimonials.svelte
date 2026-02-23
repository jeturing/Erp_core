<script lang="ts">
  import { t } from 'svelte-i18n';
  import { Star } from 'lucide-svelte';

  export let testimonials: any[] = [];

  const fallback = [
    {
      name: $t('testimonials.t1_author'),
      role: '',
      company: $t('testimonials.t1_company'),
      text: $t('testimonials.t1_quote'),
      stars: 5,
      avatar_url: '',
    },
    {
      name: $t('testimonials.t2_author'),
      role: '',
      company: $t('testimonials.t2_company'),
      text: $t('testimonials.t2_quote'),
      stars: 5,
      avatar_url: '',
    },
    {
      name: $t('testimonials.t3_author'),
      role: '',
      company: $t('testimonials.t3_company'),
      text: $t('testimonials.t3_quote'),
      stars: 5,
      avatar_url: '',
    },
  ];

  $: displayTestimonials = testimonials.length > 0 ? testimonials : fallback;
</script>

<section id="testimonials" class="bg-white py-24">
  <div class="max-w-6xl mx-auto px-6">
    <div class="text-center mb-14">
      <span class="inline-flex items-center gap-2 rounded-full bg-primary-light text-primary text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">
        {$t('testimonials.title')}
      </span>
      <h2 class="text-4xl font-jakarta font-bold text-slate-dark mb-4">
        {$t('testimonials.subtitle')}
      </h2>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      {#each displayTestimonials as t}
        <div class="rounded-card-lg border border-border bg-cloud p-6 flex flex-col">
          <!-- Stars -->
          <div class="flex items-center gap-0.5 mb-4">
            {#each Array(t.stars || 5) as _}
              <Star class="w-4 h-4 text-amber-400 fill-amber-400" />
            {/each}
          </div>

          <!-- Quote -->
          <p class="text-sm font-inter text-slate-dark leading-relaxed flex-1 mb-6">
            "{t.text}"
          </p>

          <!-- Author -->
          <div class="flex items-center gap-3">
            {#if t.avatar_url}
              <img src={t.avatar_url} alt={t.name} class="w-10 h-10 rounded-full object-cover" />
            {:else}
              <div class="w-10 h-10 rounded-full bg-primary-light text-primary font-jakarta font-bold text-sm flex items-center justify-center">
                {t.name?.charAt(0) || '?'}
              </div>
            {/if}
            <div>
              <p class="text-sm font-jakarta font-semibold text-slate-dark">{t.name}</p>
              <p class="text-xs font-inter text-slate">{t.role}, {t.company}</p>
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>
</section>
