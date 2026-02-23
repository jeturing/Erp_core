import { mount } from 'svelte'
import './app.css'
import { initializeI18n } from './lib/i18n'

// Initialize i18n BEFORE mounting — ensures locale is set before first render
initializeI18n()

import App from './App.svelte'

const app = mount(App, {
  target: document.getElementById('app')!,
})

export default app
