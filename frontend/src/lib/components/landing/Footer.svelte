<script lang="ts">
  import { t } from 'svelte-i18n';
  import { Linkedin, Youtube } from 'lucide-svelte';

  const year = new Date().getFullYear();

  const columns = [
    {
      title: $t('footer.product'),
      links: [
        { label: $t('footer.features'), href: '#features' },
        { label: $t('footer.pricing'), href: '#pricing' },
        { label: $t('footer.modules'), href: '#features' },
        { label: $t('footer.integrations'), href: '#faq' },
        { label: $t('footer.api_docs'), href: '/docs' },
      ],
    },
    {
      title: $t('footer.company'),
      links: [
        { label: $t('footer.about'), href: '#/about' },
        { label: $t('nav.partners'), href: '#partners' },
        { label: $t('nav.for_accountants'), href: '#/accountants' },
        { label: $t('footer.contact'), href: 'https://wa.me/4012001999' },
      ],
    },
    {
      title: $t('footer.legal'),
      links: [
        { label: $t('footer.privacy'), href: '#/privacy' },
        { label: $t('footer.terms'), href: '#/terms' },
        { label: $t('footer.data_processing'), href: '#/data-processing' },
        { label: $t('footer.security'), href: '#/security' },
        { label: $t('footer.sla'), href: '#/sla' },
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
          <!-- LinkedIn -->
          <a href="https://www.linkedin.com/in/jhonatancarvajal/" target="_blank" rel="noopener" class="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-slate-400 hover:bg-primary hover:text-white transition-all" aria-label="LinkedIn">
            <Linkedin class="w-4 h-4" />
          </a>
          <!-- WhatsApp -->
          <a href="https://wa.me/4012001999" target="_blank" rel="noopener" class="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-slate-400 hover:bg-emerald-500 hover:text-white transition-all" aria-label="WhatsApp">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>
              <path d="M12 0C5.373 0 0 5.373 0 12c0 2.123.558 4.115 1.535 5.836L.057 23.944l6.264-1.449A11.94 11.94 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.818a9.818 9.818 0 01-5.013-1.373l-.359-.214-3.724.861.882-3.624-.234-.373A9.818 9.818 0 012.182 12C2.182 6.567 6.567 2.182 12 2.182S21.818 6.567 21.818 12 17.433 21.818 12 21.818z"/>
            </svg>
          </a>
          <!-- YouTube -->
          <a href="https://youtube.com/@sajet" target="_blank" rel="noopener" class="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-slate-400 hover:bg-red-600 hover:text-white transition-all" aria-label="YouTube">
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
                <a
                  href={link.href}
                  class="text-sm font-inter text-slate-400 hover:text-white transition-colors"
                  {...link.href.startsWith('http') ? { target: '_blank', rel: 'noopener noreferrer' } : {}}
                >
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
