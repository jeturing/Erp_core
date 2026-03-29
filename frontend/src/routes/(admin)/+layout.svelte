<script lang="ts">
  import Layout from '$lib/components/Layout.svelte'
  import { page } from '$app/stores'

  let { children } = $props()

  // Extract the route name from the current path for Layout's currentRoute prop
  const currentRoute = $derived($page.url.pathname.replace(/^\//, '') || 'dashboard')
</script>

<Layout {currentRoute}>
  {@render children()}
</Layout>
