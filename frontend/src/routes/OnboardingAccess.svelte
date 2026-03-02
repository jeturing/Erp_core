<script lang="ts">
  function goToLogin() {
    window.location.hash = '#/login?next=customer-onboarding';
  }

  function goToHome() {
    window.location.hash = '#/';
  }
</script>

<div class="min-h-screen bg-bg-page flex items-center justify-center p-6">
  <div class="w-full max-w-2xl bg-white border border-border-light rounded-lg p-8 shadow-soft">
    <h1 class="text-2xl font-bold text-text-primary mb-3">Completa tu Onboarding</h1>
    <p class="text-sm text-gray-600 mb-6">
      Para continuar con la configuración de tu empresa debes iniciar sesión con tu cuenta de cliente.
    </p>

    <div class="grid gap-4 sm:grid-cols-2">
      <button class="btn-primary py-3" on:click={goToLogin}>
        Ir a iniciar sesión
      </button>
      <button class="btn-secondary py-3" on:click={goToHome}>
        Volver al inicio
      </button>
    </div>

    <div class="mt-6 text-xs text-gray-500">
      Después de autenticarte, el sistema te llevará automáticamente al paso pendiente del onboarding.
    </div>
  </div>
</div>
