<script>
  import { onMount } from 'svelte';
  import { Copy, Check, Mail, X } from 'lucide-svelte';

  let { 
    isOpen = false,
    credentials = null,
    onDismiss = () => {},
    onSendEmail = async () => {},
  } = $props();

  let copied = $state('');
  let sending = $state(false);
  let autoCloseTimer = null;
  let showSendEmailCheckbox = $state(false);
  let sendEmailNow = $state(false);

  onMount(() => {
    if (isOpen && credentials) {
      // Auto-dismiss después de 8 segundos si el usuario no interactúa
      autoCloseTimer = setTimeout(() => {
        if (!sendEmailNow && !sending) {
          onDismiss();
        }
      }, 8000);

      // Si no ha habido clic, mostrar checkbox para enviar email
      setTimeout(() => {
        showSendEmailCheckbox = true;
      }, 2000);
    }

    return () => {
      if (autoCloseTimer) clearTimeout(autoCloseTimer);
    };
  });

  function copyToClipboard(text, field) {
    navigator.clipboard.writeText(text);
    copied = field;
    setTimeout(() => {
      copied = '';
    }, 2000);
  }

  async function handleSendEmail() {
    sending = true;
    try {
      await onSendEmail(false); // false = send immediately
      sendEmailNow = true;
      // Auto-dismiss después de enviar
      setTimeout(() => {
        onDismiss();
      }, 2000);
    } catch (error) {
      console.error('Error enviando email:', error);
    } finally {
      sending = false;
    }
  }

  function handleDismiss() {
    if (autoCloseTimer) clearTimeout(autoCloseTimer);
    onDismiss();
  }

  const tenantUrl = credentials?.tenant_url || (credentials ? `https://${credentials.subdomain}.sajet.us` : '');
</script>

{#if isOpen && credentials}
<!-- Backdrop -->
<div class="fixed inset-0 bg-black/60 z-[9999] flex items-center justify-center p-4" role="dialog">
  <!-- Modal -->
  <div class="bg-charcoal rounded-xl border border-border-dark w-full max-w-md shadow-2xl animate-in fade-in scale-95 duration-200">
    <!-- Header -->
    <div class="flex items-center justify-between p-6 border-b border-border-dark">
      <h2 class="text-lg font-semibold text-text-light flex items-center gap-2">
        ✓ Cliente Creado
      </h2>
      <button
        on:click={handleDismiss}
        class="text-gray-400 hover:text-text-light transition-colors p-1"
        aria-label="Cerrar"
      >
        <X size={20} />
      </button>
    </div>

    <!-- Body -->
    <div class="p-6 space-y-5">
      <!-- Company info -->
      <div class="bg-gray-700/30 rounded-lg p-4">
        <div class="text-xs text-gray-400 uppercase tracking-widest mb-2">Información del Tenant</div>
        <div class="text-text-light font-medium mb-1">{credentials.company_name}</div>
        <div class="text-sm text-gray-400 font-mono break-all">{credentials.subdomain}.sajet.us</div>
      </div>

      <!-- Credentials -->
      <div class="space-y-3">
        <div class="text-xs text-gray-400 uppercase tracking-widest">Credenciales de Acceso</div>

        <!-- Usuario -->
        <div class="bg-dark-subtle rounded-lg p-4 border border-border-dark">
          <label class="text-xs text-gray-500 block mb-2">Nombre de Usuario</label>
          <div class="flex items-center gap-2">
            <code class="text-text-light font-mono text-sm flex-1 break-all">{credentials.admin_login}</code>
            <button
              on:click={() => copyToClipboard(credentials.admin_login, 'user')}
              class="p-2 hover:bg-gray-600 rounded transition-colors text-gray-400 hover:text-text-light"
              title="Copiar usuario"
              disabled={sending}
            >
              {#if copied === 'user'}
                <Check size={16} class="text-green-400" />
              {:else}
                <Copy size={16} />
              {/if}
            </button>
          </div>
        </div>

        <!-- Contraseña -->
        <div class="bg-dark-subtle rounded-lg p-4 border border-border-dark">
          <label class="text-xs text-gray-500 block mb-2">Contraseña Temporal</label>
          <div class="flex items-center gap-2">
            <code class="text-text-light font-mono text-sm flex-1 break-all">{credentials.admin_password}</code>
            <button
              on:click={() => copyToClipboard(credentials.admin_password, 'pass')}
              class="p-2 hover:bg-gray-600 rounded transition-colors text-gray-400 hover:text-text-light"
              title="Copiar contraseña"
              disabled={sending}
            >
              {#if copied === 'pass'}
                <Check size={16} class="text-green-400" />
              {:else}
                <Copy size={16} />
              {/if}
            </button>
          </div>
          <div class="text-xs text-yellow-400/70 mt-2">
            ⚠ Cambia esta contraseña después de tu primer acceso
          </div>
        </div>

        <!-- URL -->
        <div class="bg-dark-subtle rounded-lg p-4 border border-border-dark">
          <label class="text-xs text-gray-500 block mb-2">URL de Acceso</label>
          <div class="flex items-center gap-2">
            <code class="text-blue-400 font-mono text-sm flex-1 break-all">{tenantUrl}</code>
            <button
              on:click={() => copyToClipboard(tenantUrl, 'url')}
              class="p-2 hover:bg-gray-600 rounded transition-colors text-gray-400 hover:text-text-light"
              title="Copiar URL"
              disabled={sending}
            >
              {#if copied === 'url'}
                <Check size={16} class="text-green-400" />
              {:else}
                <Copy size={16} />
              {/if}
            </button>
          </div>
        </div>
      </div>

      <!-- Info message -->
      <div class="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 text-sm text-blue-300">
        <div class="font-medium mb-1">Próximos pasos:</div>
        <ul class="text-xs space-y-1">
          <li>✓ Copia las credenciales arriba</li>
          <li>✓ Accede a la URL con usuario y contraseña</li>
          <li>✓ Cambia tu contraseña inmediatamente</li>
        </ul>
      </div>

      <!-- Send email option (appears after 2 seconds) -->
      {#if showSendEmailCheckbox}
        <div class="border-t border-border-dark pt-4">
          <div class="text-xs text-gray-400 mb-3">¿Deseas recibir las credenciales por email también?</div>
          <button
            on:click={handleSendEmail}
            disabled={sending}
            class="w-full btn-accent flex items-center justify-center gap-2"
          >
            <Mail size={16} />
            {sending ? 'Enviando...' : 'Enviar Credenciales por Email'}
          </button>
        </div>
      {/if}

      <!-- Auto-close info -->
      <div class="text-xs text-gray-500 text-center">
        {#if sendEmailNow}
          <span class="text-green-400">✓ Email enviado. Cerrando...</span>
        {:else}
          <span>Este modal se cerrará automáticamente en 8 segundos</span>
        {/if}
      </div>
    </div>

    <!-- Footer -->
    <div class="border-t border-border-dark p-4 flex gap-2">
      <button
        on:click={handleDismiss}
        disabled={sending}
        class="flex-1 btn-secondary"
      >
        Cerrar
      </button>
      {#if !sendEmailNow && showSendEmailCheckbox}
        <button
          on:click={handleSendEmail}
          disabled={sending}
          class="flex-1 btn-accent flex items-center justify-center gap-2"
        >
          <Mail size={14} />
          {sending ? 'Enviando...' : 'Email'}
        </button>
      {/if}
    </div>
  </div>
</div>
{/if}
