<script lang="ts">
  import { t } from 'svelte-i18n';
  import { Linkedin, Twitter, Youtube } from 'lucide-svelte';

  const year = new Date().getFullYear();

  const columns = [
    {
      title: $t('footer.product'),
      links: [
        { label: $t('footer.features'), href: '#features' },
        { label: $t('footer.pricing'), href: '#pricing' },
        { label: $t('footer.modules'), href: '#features' },
        { label: $t('footer.integrations'), href: '#' },
        { label: $t('footer.api_docs'), href: '#' },
      ],
    },
    {
      title: $t('footer.company'),
      links: [
        { label: $t('footer.about'), href: '#' },
        { label: $t('nav.partners'), href: '#partners' },
        { label: $t('nav.for_accountants'), href: '#/accountants' },
        { label: $t('footer.blog'), href: '#' },
        { label: $t('footer.careers'), href: '#' },
      ],
    },
    {
      title: $t('footer.legal'),
      links: [
        { label: $t('footer.privacy'), href: '#' },
        { label: $t('footer.terms'), href: '#' },
        { label: $t('footer.data_processing'), href: '#' },
        { label: $t('footer.security'), href: '#' },
        { label: $t('footer.sla'), href: '#' },
      ],
    },
  ];
</script>

<footer class="bg-[#0F172A] pt-16 pb-8">
  <div class="max-w-6xl mx-auto px-6">
    <div class="grid grid-cols-2 md:grid-cols-4 gap-10 mb-14">
      <!-- Brand column -->
      <div class="col-span-2 md:col-span-1">
        <a href="#/" class="inline-block mb-4">
          <span class="text-xl font-jakarta font-extrabold text-white">
            Sajet<span class="text-secondary">.</span>us
          </span>
        </a>
        <p class="text-sm font-inter text-slate-400 leading-relaxed mb-6">
          {$t('footer.brand_description')}
        </p>
        <div class="flex items-center gap-3">
          <a href="https://linkedin.com" target="_blank" rel="noopener" class="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-slate-400 hover:bg-primary hover:text-white transition-all" aria-label="LinkedIn">
            <Linkedin class="w-4 h-4" />
          </a>
          <a href="https://x.com" target="_blank" rel="noopener" class="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-slate-400 hover:bg-primary hover:text-white transition-all" aria-label="X">
            <Twitter class="w-4 h-4" />
          </a>
          <a href="https://youtube.com" target="_blank" rel="noopener" class="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-slate-400 hover:bg-primary hover:text-white transition-all" aria-label="YouTube">
            <Youtube class="w-4 h-4" />
          </a>
        </div>
      </div>

      <!-- Link columns -->
      {#each columns as col}
        <div>
          <h4 class="text-sm font-jakarta font-semibold text-white mb-4">{col.title}</h4>
          <ul class="space-y-2.5">
            {#each col.links as link}
              <li>
                <a href={link.href} class="text-sm font-inter text-slate-400 hover:text-white transition-colors">
                  {link.label}
                </a>
              </li>
            {/each}
          </ul>
        </div>
      {/each}
    </div>

    <!-- Bottom bar -->
    <div class="border-t border-white/10 pt-6 flex flex-col md:flex-row items-center justify-between gap-3">
      <p class="text-xs font-inter text-slate-500">
        {$t('footer.copyright')}
      </p>
      <p class="text-xs font-inter text-slate-600">
        {$t('footer.powered_by')} {$t('footer.company_name')}
      </p>
    </div>
  </div>
</footer>
