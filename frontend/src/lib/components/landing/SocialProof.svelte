<script lang="ts">
  export let industries: string[] = [
    'Retail', 'Manufacturing', 'Services', 'Healthcare', 'Distribution', 'Consulting'
  ];
</script>

<section class="bg-cloud py-16 border-y border-border">
  <div class="max-w-6xl mx-auto px-6">
    <p class="text-center text-sm font-inter text-slate tracking-wide mb-8">
      Trusted by growing businesses in the US, Latin America and beyond
    </p>
    <div class="flex flex-wrap justify-center items-center gap-8">
      {#each industries as industry}
        <div class="flex items-center gap-2 text-slate/60">
          <div class="w-8 h-8 rounded-card-sm bg-primary-light flex items-center justify-center">
            <span class="text-xs font-jakarta font-bold text-primary">{industry[0]}</span>
          </div>
          <span class="text-sm font-inter font-medium text-slate">{industry}</span>
        </div>
      {/each}
    </div>
  </div>
</section>
