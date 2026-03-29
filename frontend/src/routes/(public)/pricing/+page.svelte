<script lang="ts">
  import Landing from '$routes/Landing.svelte'
  import { onMount } from 'svelte'

  onMount(() => {
    // Scroll to pricing section after mount
    setTimeout(() => {
      const el = document.getElementById('pricing')
      if (el) el.scrollIntoView({ behavior: 'smooth' })
    }, 300)
  })
</script>

<Landing />
