# Sentry SDK en Svelte (Erp_core)

## Estado

✅ Dependencia instalada en `frontend`:

- `@sentry/svelte`

✅ Inicialización aplicada en el entrypoint:

- [frontend/src/main.ts](frontend/src/main.ts)

## Configuración aplicada

```ts
import * as Sentry from '@sentry/svelte'

Sentry.init({
  dsn: 'https://25d1ed3d6874315596b334c4fee98a43@o4508162202009600.ingest.us.sentry.io/4510962513412096',
  sendDefaultPii: true,
})
```

## Verificación recomendada

Agregar temporalmente en cualquier componente Svelte:

```svelte
<button type="button" onclick="{() => {throw new Error('This is your first error!')}}">
  Break the world
</button>
```

Luego validar que el evento llegue a Sentry en Issues.

## Nota

Para producción, se recomienda mover el DSN a variable de entorno (`VITE_SENTRY_DSN`) y mantener `sendDefaultPii` alineado a política de privacidad/compliance.
