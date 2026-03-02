<script lang="ts">
  import { ArrowLeft, LifeBuoy } from 'lucide-svelte';

  function goToLogin() {
    window.location.hash = '#/login';
  }

  function goToSignup() {
    window.location.hash = '#/signup';
  }
</script>

<div class="min-h-screen bg-bg-page p-6">
  <div class="max-w-2xl mx-auto space-y-6">
    <button class="btn-secondary px-3 py-2 text-sm inline-flex items-center gap-2" on:click={goToLogin}>
      <ArrowLeft size={14} /> Volver a login
    </button>

    <div class="card p-6 sm:p-8 space-y-5">
      <h1 class="text-2xl font-bold text-text-primary">Recuperar acceso</h1>
      <p class="text-sm text-gray-600">
        Selecciona tu tipo de cuenta y te guiamos con el flujo correcto de recuperación.
      </p>

      <div class="grid sm:grid-cols-3 gap-3">
        <a class="border border-border-light rounded-md p-4 hover:border-[#003B73] transition-colors" href="mailto:soporte@sajet.us?subject=Recuperar%20acceso%20Tenant&body=Email%20de%20la%20cuenta:%20">
          <p class="font-semibold text-sm text-text-primary mb-1">Tenant</p>
          <p class="text-xs text-gray-500">Restablecer contraseña de portal cliente.</p>
        </a>
        <a class="border border-border-light rounded-md p-4 hover:border-[#003B73] transition-colors" href="mailto:soporte@sajet.us?subject=Recuperar%20acceso%20Accountant&body=Email%20de%20la%20cuenta:%20">
          <p class="font-semibold text-sm text-text-primary mb-1">Accountant</p>
          <p class="text-xs text-gray-500">Recuperar acceso a cuentas multi-tenant.</p>
        </a>
        <a class="border border-border-light rounded-md p-4 hover:border-[#003B73] transition-colors" href="mailto:soporte@sajet.us?subject=Recuperar%20acceso%20Partner&body=Email%20de%20la%20cuenta:%20">
          <p class="font-semibold text-sm text-text-primary mb-1">Partner</p>
          <p class="text-xs text-gray-500">Recuperar acceso al portal de socios.</p>
        </a>
      </div>

      <div class="rounded border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700 flex items-center gap-2">
        <LifeBuoy size={14} />
        Soporte: <a class="underline" href="mailto:soporte@sajet.us">soporte@sajet.us</a>
      </div>

      <button class="btn-primary w-full py-3" on:click={goToSignup}>Crear cuenta nueva</button>
    </div>
  </div>
</div>
