import { mount } from 'svelte'
import './app.css'
import { initializeI18n } from './lib/i18n'
import * as Sentry from '@sentry/svelte'

Sentry.init({
  dsn: 'https://25d1ed3d6874315596b334c4fee98a43@o4508162202009600.ingest.us.sentry.io/4510962513412096',
  // Setting this option to true will send default PII data to Sentry.
  // For example, automatic IP address collection on events
  sendDefaultPii: true,
})

// Initialize i18n BEFORE mounting — ensures locale is set before first render
initializeI18n()

import App from './App.svelte'

const app = mount(App, {
  target: document.getElementById('app')!,
})

export default app
