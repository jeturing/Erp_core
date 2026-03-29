<script lang="ts">
  import PartnerLanding from '$routes/PartnerLanding.svelte'
  import { page } from '$app/stores'

  const slug = $derived($page.params.slug)
</script>
<PartnerLanding code={slug} />
