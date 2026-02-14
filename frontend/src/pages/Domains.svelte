<script lang="ts">
  import { onMount } from 'svelte';
  import { Globe, CheckCircle2, Clock3, ShieldCheck } from 'lucide-svelte';
  import { Badge, Button, Card, Input, Modal, StatCard } from '../lib/components';
  import { domainStats, domainsStore, type CustomDomain } from '../lib/stores/domains';

  let showCreateModal = false;
  let showDetailsModal = false;
  let showDeleteModal = false;
  let selectedDomain: CustomDomain | null = null;

  let search = '';
  let feedback = '';
  let feedbackError = false;

  let createLoading = false;
  let createError = '';
  let createInstructions: {
    step1: string;
    record_type: string;
    record_name: string;
    record_value: string;
    step2: string;
  } | null = null;

  let createForm = {
    external_domain: '',
    customer_id: 1,
  };

  onMount(() => {
    domainsStore.load();
  });

  function clearFeedback() {
    feedback = '';
    feedbackError = false;
  }

  function statusBadge(status: string) {
    if (status === 'verified') return 'success';
    if (status === 'pending' || status === 'verifying') return 'warning';
    if (status === 'failed' || status === 'expired') return 'error';
    return 'secondary';
  }

  async function handleCreate() {
    createError = '';
    createLoading = true;
    try {
      const payload = {
        external_domain: createForm.external_domain.trim(),
        customer_id: Number(createForm.customer_id),
      };
      const result = await domainsStore.create(payload);
      createInstructions = result.instructions || null;
      feedback = 'Dominio registrado correctamente.';
      feedbackError = false;
      await domainsStore.load();
    } catch (error) {
      createError = error instanceof Error ? error.message : 'No se pudo crear dominio';
    } finally {
      createLoading = false;
    }
  }

  function openDetails(domain: CustomDomain) {
    selectedDomain = domain;
    showDetailsModal = true;
  }

  async function verifyDomain(domain: CustomDomain) {
    clearFeedback();
    try {
      const result = await domainsStore.verify(domain.id);
      feedback = result.message || 'Dominio verificado';
      feedbackError = !result.success;
      await domainsStore.load();
    } catch (error) {
      feedback = error instanceof Error ? error.message : 'No se pudo verificar dominio';
      feedbackError = true;
    }
  }

  async function configureCloudflare(domain: CustomDomain) {
    clearFeedback();
    try {
      const result = await domainsStore.configureCloudflare(domain.id);
      feedback = result.message || 'Cloudflare configurado';
      feedbackError = !result.success;
      await domainsStore.load();
      await domainsStore.get(domain.id);
    } catch (error) {
      feedback = error instanceof Error ? error.message : 'No se pudo configurar Cloudflare';
      feedbackError = true;
    }
  }

  async function toggleActive(domain: CustomDomain) {
    clearFeedback();
    try {
      if (domain.is_active) {
        await domainsStore.deactivate(domain.id);
        feedback = 'Dominio desactivado';
      } else {
        await domainsStore.activate(domain.id);
        feedback = 'Dominio activado';
      }
      feedbackError = false;
      await domainsStore.load();
      await domainsStore.get(domain.id);
    } catch (error) {
      feedback = error instanceof Error ? error.message : 'No se pudo cambiar estado';
      feedbackError = true;
    }
  }

  function confirmDelete(domain: CustomDomain) {
    selectedDomain = domain;
    showDeleteModal = true;
  }

  async function handleDelete() {
    if (!selectedDomain) return;
    try {
      await domainsStore.delete(selectedDomain.id);
      showDeleteModal = false;
      feedback = 'Dominio eliminado correctamente';
      feedbackError = false;
      selectedDomain = null;
    } catch (error) {
      feedback = error instanceof Error ? error.message : 'No se pudo eliminar dominio';
      feedbackError = true;
    }
  }

  function closeCreateModal() {
    showCreateModal = false;
    createError = '';
    createInstructions = null;
    createForm = {
      external_domain: '',
      customer_id: 1,
    };
  }

  $: stats = $domainStats;
  $: filteredDomains = $domainsStore.items.filter((domain) => {
    const text = `${domain.external_domain} ${domain.sajet_full_domain}`.toLowerCase();
    return text.includes(search.toLowerCase().trim());
  });
</script>

<div class="p-6 lg:p-8 space-y-6">
  <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold text-white">Domains</h1>
      <p class="text-secondary-400 mt-1">Gestion de dominios personalizados y estado de verificacion DNS</p>
    </div>
    <Button on:click={() => (showCreateModal = true)}>+ Nuevo dominio</Button>
  </div>

  {#if feedback}
    <div class={`rounded-lg border px-4 py-3 text-sm ${feedbackError ? 'bg-error/10 border-error/30 text-error' : 'bg-success/10 border-success/30 text-success'}`}>
      {feedback}
    </div>
  {/if}

  <Card>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
      <StatCard value={stats.total} label="Total" icon={Globe} iconBg="bg-primary-500/10" iconColor="text-primary-300" />
      <StatCard value={stats.active} label="Activos" icon={CheckCircle2} iconBg="bg-success/10" iconColor="text-success" />
      <StatCard value={stats.pending} label="Pendientes" icon={Clock3} iconBg="bg-warning/10" iconColor="text-warning" />
      <StatCard value={stats.verified} label="Verificados" icon={ShieldCheck} iconBg="bg-accent-500/10" iconColor="text-accent-500" />
      <Input label="Buscar" placeholder="dominio o subdominio" bind:value={search} />
    </div>
  </Card>

  <Card title="Listado de dominios" subtitle="/api/domains" padding="none">
    <div class="overflow-x-auto">
      <table class="table">
        <thead>
          <tr>
            <th>Dominio externo</th>
            <th>Subdominio Sajet</th>
            <th>Estado</th>
            <th>Cloudflare</th>
            <th>Activo</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#if $domainsStore.loading}
            <tr>
              <td colspan="6" class="py-8 text-center text-secondary-500">Cargando...</td>
            </tr>
          {:else}
            {#each filteredDomains as domain}
              <tr>
                <td>
                  <p class="text-white font-medium">{domain.external_domain}</p>
                  <p class="text-xs text-secondary-500">ID cliente: {domain.customer_id}</p>
                </td>
                <td class="font-mono text-xs text-secondary-300">{domain.sajet_full_domain}</td>
                <td><Badge variant={statusBadge(domain.verification_status)}>{domain.verification_status}</Badge></td>
                <td><Badge variant={domain.cloudflare_configured ? 'success' : 'secondary'}>{domain.cloudflare_configured ? 'si' : 'no'}</Badge></td>
                <td><Badge variant={domain.is_active ? 'success' : 'secondary'}>{domain.is_active ? 'si' : 'no'}</Badge></td>
                <td>
                  <div class="flex flex-wrap gap-2">
                    <Button size="sm" variant="secondary" on:click={() => openDetails(domain)}>Ver</Button>
                    <Button size="sm" variant="secondary" on:click={() => verifyDomain(domain)}>Verificar</Button>
                    <Button size="sm" variant="danger" on:click={() => confirmDelete(domain)}>Eliminar</Button>
                  </div>
                </td>
              </tr>
            {:else}
              <tr>
                <td colspan="6" class="py-8 text-center text-secondary-500">No hay dominios registrados</td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
  </Card>
</div>

<Modal
  bind:isOpen={showCreateModal}
  title="Registrar nuevo dominio"
  confirmText={createInstructions ? 'Cerrar' : 'Registrar'}
  on:close={closeCreateModal}
  on:confirm={createInstructions ? closeCreateModal : handleCreate}
  loading={createLoading}
  size="lg"
>
  {#if createInstructions}
    <div class="space-y-4">
      <div class="bg-success/10 border border-success/30 rounded-lg p-4 text-success text-sm">
        Dominio registrado. Complete la configuracion DNS para validar.
      </div>

      <div class="rounded-lg border border-surface-border bg-surface-highlight p-4 text-sm text-secondary-200 space-y-2">
        <p>{createInstructions.step1}</p>
        <div class="font-mono text-xs rounded bg-surface-dark p-3">
          <p>Tipo: {createInstructions.record_type}</p>
          <p>Nombre: {createInstructions.record_name}</p>
          <p>Valor: {createInstructions.record_value}</p>
        </div>
        <p>{createInstructions.step2}</p>
      </div>
    </div>
  {:else}
    <div class="space-y-4">
      {#if createError}
        <div class="rounded-lg border border-error/30 bg-error/10 px-3 py-2 text-sm text-error">{createError}</div>
      {/if}

      <Input label="Dominio externo" placeholder="www.miempresa.com" bind:value={createForm.external_domain} required />
      <Input label="ID cliente" type="number" bind:value={createForm.customer_id} required />
    </div>
  {/if}
</Modal>

<Modal
  bind:isOpen={showDetailsModal}
  title="Detalles del dominio"
  showFooter={false}
  size="lg"
  on:close={() => {
    showDetailsModal = false;
    selectedDomain = null;
  }}
>
  {#if selectedDomain}
    <div class="space-y-4 text-sm">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <p class="text-secondary-500 uppercase text-xs">Dominio externo</p>
          <p class="font-mono text-primary-300 font-semibold">{selectedDomain.external_domain}</p>
        </div>
        <div>
          <p class="text-secondary-500 uppercase text-xs">Subdominio Sajet</p>
          <p class="font-mono text-secondary-200">{selectedDomain.sajet_full_domain}</p>
        </div>
      </div>

      <div class="flex flex-wrap gap-3">
        <Badge variant={statusBadge(selectedDomain.verification_status)}>{selectedDomain.verification_status}</Badge>
        <Badge variant={selectedDomain.cloudflare_configured ? 'success' : 'secondary'}>
          Cloudflare {selectedDomain.cloudflare_configured ? 'ok' : 'pendiente'}
        </Badge>
        <Badge variant={selectedDomain.is_active ? 'success' : 'secondary'}>
          {selectedDomain.is_active ? 'Activo' : 'Inactivo'}
        </Badge>
      </div>

      <div class="rounded-lg bg-surface-highlight border border-surface-border p-4">
        <p class="text-secondary-500 mb-1">Destino</p>
        <p class="font-mono text-secondary-200">http://{selectedDomain.target_node_ip}:{selectedDomain.target_port}</p>
      </div>

      {#if selectedDomain.verification_status !== 'verified'}
        <div class="rounded-lg bg-info/10 border border-info/30 p-4">
          <p class="text-info text-sm font-medium mb-2">Configuracion DNS esperada</p>
          <p class="font-mono text-xs text-secondary-200">CNAME {selectedDomain.external_domain} -> {selectedDomain.sajet_full_domain}</p>
        </div>
      {/if}

        <div class="flex flex-wrap gap-2 pt-2">
        {#if !selectedDomain.cloudflare_configured}
          <Button variant="secondary" on:click={() => configureCloudflare(selectedDomain!)}>Configurar Cloudflare</Button>
        {/if}
        {#if selectedDomain.verification_status !== 'verified'}
          <Button variant="primary" on:click={() => verifyDomain(selectedDomain!)}>Verificar DNS</Button>
        {/if}
        <Button variant={selectedDomain.is_active ? 'ghost' : 'primary'} on:click={() => toggleActive(selectedDomain!)}>
          {selectedDomain.is_active ? 'Desactivar' : 'Activar'}
        </Button>
      </div>
    </div>
  {/if}
</Modal>

<Modal
  bind:isOpen={showDeleteModal}
  title="Eliminar dominio"
  confirmText="Eliminar"
  confirmVariant="danger"
  on:close={() => {
    showDeleteModal = false;
    selectedDomain = null;
  }}
  on:confirm={handleDelete}
>
  {#if selectedDomain}
    <div class="space-y-3 text-sm text-secondary-300">
      <p>Se eliminara el dominio <strong class="text-error">{selectedDomain.external_domain}</strong> y su configuracion asociada.</p>
      <p class="text-secondary-500">Esta accion no se puede deshacer.</p>
    </div>
  {/if}
</Modal>
