<!-- Stripe dark brand footer: #1c1e54 background -->
<footer style="
  background: #020e1f;
  border-top: 1px solid rgba(0,255,159,0.08);
  padding: 64px 24px 40px;
">
  <div style="max-width:1080px; margin:0 auto;">
    <!-- Main grid -->
    <div style="display:grid; grid-template-columns:2fr 1fr 1fr 1fr; gap:48px; margin-bottom:56px;">

      <!-- Brand column -->
      <div>
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:20px;">
          <div style="
            width:32px; height:32px; background:linear-gradient(135deg,#003B73,#00569e);
            border-radius:6px; display:flex; align-items:center; justify-content:center;
            box-shadow:0 0 0 1px rgba(0,255,159,0.2);
          ">
            <span style="color:#00FF9F; font-weight:800; font-size:14px; font-family:'Plus Jakarta Sans',system-ui;">S</span>
          </div>
          <span style="font-family:'Plus Jakarta Sans',system-ui; font-weight:700; font-size:17px; color:#f0f4ff; letter-spacing:-0.02em;">SAJET</span>
        </div>
        <p style="font-size:14px; line-height:1.65; color:#7a8fa6; font-weight:300; max-width:260px; margin:0 0 24px;">
          ERP multi-tenant para empresas que exigen confiabilidad, escala y control real de sus datos.
        </p>
        <div style="display:flex; gap:16px;">
          {#each ['segrd.com', 'jeturing.com'] as link}
            <a href="https://{link}" target="_blank" rel="noopener"
              style="font-size:12px; color:#7a8fa6; text-decoration:none; transition:color 0.2s;"
              on:mouseenter={e=>e.currentTarget.style.color='#00FF9F'}
              on:mouseleave={e=>e.currentTarget.style.color='#7a8fa6'}
            >{link}</a>
          {/each}
        </div>
      </div>

      <!-- Links columns -->
      {#each [
        { title:'Producto', links:['Características', 'Precios', 'Seguridad', 'API', 'Changelog'] },
        { title:'Empresa', links:['Nosotros', 'Blog', 'Careers', 'Prensa', 'Contacto'] },
        { title:'Legal', links:['Privacidad', 'Términos', 'SLA', 'Cookies', 'GDPR'] },
      ] as col}
        <div>
          <h4 style="font-size:11px; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:#f0f4ff; margin:0 0 20px;">{col.title}</h4>
          <ul style="list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:12px;">
            {#each col.links as link}
              <li>
                <a href="#" style="font-size:13px; color:#7a8fa6; text-decoration:none; transition:color 0.2s; font-weight:300;"
                  on:mouseenter={e=>e.currentTarget.style.color='#c8d3e8'}
                  on:mouseleave={e=>e.currentTarget.style.color='#7a8fa6'}
                >{link}</a>
              </li>
            {/each}
          </ul>
        </div>
      {/each}
    </div>

    <!-- Bottom bar -->
    <div style="
      display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px;
      padding-top:32px; border-top:1px solid rgba(255,255,255,0.06);
    ">
      <p style="font-size:12px; color:#7a8fa6; margin:0; font-weight:300;">
        © {new Date().getFullYear()} Jeturing. Todos los derechos reservados.
      </p>
      <div style="display:flex; align-items:center; gap:6px;">
        <div style="width:6px; height:6px; border-radius:50%; background:#00FF9F; box-shadow:0 0 6px rgba(0,255,159,0.6);"></div>
        <span style="font-size:12px; color:#7a8fa6; font-weight:300;">Todos los sistemas operativos</span>
      </div>
    </div>
  </div>
</footer>
