import * as Sentry from '@sentry/svelte'
import { initializeI18n } from '$lib/i18n'

Sentry.init({
  dsn: 'https://25d1ed3d6874315596b334c4fee98a43@o4508162202009600.ingest.us.sentry.io/4510962513412096',
  sendDefaultPii: true,
})

// Initialize i18n BEFORE first render
initializeI18n()
