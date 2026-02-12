<!-- Domains.svelte - Página de gestión de dominios personalizados -->
<script lang="ts">
    import { onMount } from 'svelte';
    import Layout from '../lib/components/Layout.svelte';
    import Card from '../lib/components/Card.svelte';
    import Button from '../lib/components/Button.svelte';
    import Badge from '../lib/components/Badge.svelte';
    import Input from '../lib/components/Input.svelte';
    import StatCard from '../lib/components/StatCard.svelte';
    import DataTable from '../lib/components/DataTable.svelte';
    import Modal from '../lib/components/Modal.svelte';
    import { domainsStore, domainStats, type CustomDomain } from '../lib/stores/domains';
    
    // Estado del modal
    let showCreateModal = false;
    let showDetailsModal = false;
    let showDeleteModal = false;
    let selectedDomain: CustomDomain | null = null;
    
    // Form de creación
    let newDomain = {
        external_domain: '',
        customer_id: 1,  // TODO: selector de cliente
        tenant_deployment_id: null as number | null
    };
    let createLoading = false;
    let createError = '';
    let createInstructions: any = null;
    
    // Configuración de la tabla
    const columns = [
        { key: 'external_domain', label: 'Dominio Externo', sortable: true },
        { key: 'sajet_full_domain', label: 'Subdominio Sajet', sortable: true },
        { 
            key: 'verification_status', 
            label: 'Estado', 
            type: 'badge' as const,
            badgeColors: {
                pending: 'yellow',
                verifying: 'blue',
                verified: 'green',
                failed: 'red',
                expired: 'gray'
            },
            sortable: true
        },
        { key: 'cloudflare_configured', label: 'Cloudflare', type: 'boolean' as const },
        { key: 'is_active', label: 'Activo', type: 'boolean' as const },
        { key: 'created_at', label: 'Creado', type: 'date' as const, sortable: true }
    ];
    
    const tableActions = [
        { 
            label: 'Ver', 
            onClick: (row: CustomDomain) => openDetails(row)
        },
        { 
            label: 'Verificar', 
            onClick: (row: CustomDomain) => verifyDomain(row)
        },
        { 
            label: 'Eliminar', 
            variant: 'danger',
            onClick: (row: CustomDomain) => confirmDelete(row)
        }
    ];
    
    // Cargar dominios al montar
    onMount(() => {
        domainsStore.load();
    });
    
    // Handlers
    async function handleCreate() {
        createLoading = true;
        createError = '';
        createInstructions = null;
        
        try {
            const result = await domainsStore.create(newDomain);
            createInstructions = result.instructions;
            
            // No cerrar modal, mostrar instrucciones
            newDomain = { external_domain: '', customer_id: 1, tenant_deployment_id: null };
        } catch (error: any) {
            createError = error.message || 'Error creando dominio';
        } finally {
            createLoading = false;
        }
    }
    
    function openDetails(domain: CustomDomain) {
        selectedDomain = domain;
        showDetailsModal = true;
    }
    
    async function verifyDomain(domain: CustomDomain) {
        try {
            const result = await domainsStore.verify(domain.id);
            alert(result.message);
        } catch (error: any) {
            alert('Error: ' + (error.message || 'No se pudo verificar'));
        }
    }
    
    async function configureCloudflare(domain: CustomDomain) {
        try {
            const result = await domainsStore.configureCloudflare(domain.id);
            alert(result.message);
            await domainsStore.load();
        } catch (error: any) {
            alert('Error: ' + (error.message || 'No se pudo configurar'));
        }
    }
    
    async function toggleActive(domain: CustomDomain) {
        try {
            if (domain.is_active) {
                await domainsStore.deactivate(domain.id);
            } else {
                await domainsStore.activate(domain.id);
            }
        } catch (error: any) {
            alert('Error: ' + (error.message || 'No se pudo cambiar estado'));
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
            selectedDomain = null;
        } catch (error: any) {
            alert('Error: ' + (error.message || 'No se pudo eliminar'));
        }
    }
    
    function closeCreateModal() {
        showCreateModal = false;
        createError = '';
        createInstructions = null;
        newDomain = { external_domain: '', customer_id: 1, tenant_deployment_id: null };
    }
    
    // Reactive
    $: stats = $domainStats;
</script>

<Layout>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex justify-between items-center">
            <div>
                <h1 class="text-2xl font-bold text-gray-900">Dominios Personalizados</h1>
                <p class="text-gray-600 mt-1">
                    Gestiona los dominios personalizados de tus clientes
                </p>
            </div>
            <Button on:click={() => showCreateModal = true}>
                + Nuevo Dominio
            </Button>
        </div>
        
        <!-- Stats -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard 
                title="Total Dominios" 
                value={stats.total} 
                icon="🌐"
            />
            <StatCard 
                title="Activos" 
                value={stats.active} 
                icon="✅"
                trend="up"
            />
            <StatCard 
                title="Pendientes" 
                value={stats.pending} 
                icon="⏳"
            />
            <StatCard 
                title="Verificados" 
                value={stats.verified} 
                icon="🔒"
            />
        </div>
        
        <!-- Tabla de dominios -->
        <Card>
            <DataTable 
                {columns}
                data={$domainsStore.items}
                loading={$domainsStore.loading}
                emptyMessage="No hay dominios registrados"
                actions={tableActions}
            />
        </Card>
    </div>
</Layout>

<!-- Modal: Crear Dominio -->
<Modal 
    bind:isOpen={showCreateModal}
    title="Registrar Nuevo Dominio"
    confirmText={createInstructions ? 'Cerrar' : 'Registrar'}
    on:close={closeCreateModal}
    on:confirm={createInstructions ? closeCreateModal : handleCreate}
    loading={createLoading}
    size="lg"
>
    {#if createInstructions}
        <!-- Instrucciones de configuración -->
        <div class="space-y-4">
            <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                <p class="text-green-800 font-medium">✅ Dominio registrado correctamente</p>
            </div>
            
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 class="font-semibold text-blue-900 mb-2">📋 Configuración DNS Requerida</h4>
                <p class="text-blue-800 text-sm mb-3">{createInstructions.step1}</p>
                
                <div class="bg-white rounded p-3 font-mono text-sm">
                    <div class="grid grid-cols-3 gap-2">
                        <div>
                            <span class="text-gray-500">Tipo:</span>
                            <span class="font-bold">{createInstructions.record_type}</span>
                        </div>
                        <div>
                            <span class="text-gray-500">Nombre:</span>
                            <span class="font-bold">{createInstructions.record_name}</span>
                        </div>
                        <div>
                            <span class="text-gray-500">Valor:</span>
                            <span class="font-bold text-primary">{createInstructions.record_value}</span>
                        </div>
                    </div>
                </div>
                
                <p class="text-blue-700 text-sm mt-3">{createInstructions.step2}</p>
            </div>
        </div>
    {:else}
        <!-- Formulario de creación -->
        <div class="space-y-4">
            {#if createError}
                <div class="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p class="text-red-800 text-sm">{createError}</p>
                </div>
            {/if}
            
            <Input 
                label="Dominio del Cliente"
                placeholder="www.mi-empresa.com"
                bind:value={newDomain.external_domain}
                hint="El dominio completo que el cliente quiere usar"
            />
            
            <Input 
                label="ID del Cliente"
                type="number"
                bind:value={newDomain.customer_id}
                hint="ID del cliente propietario del dominio"
            />
            
            <div class="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
                <p class="font-medium text-gray-900 mb-2">¿Cómo funciona?</p>
                <ol class="list-decimal list-inside space-y-1">
                    <li>Registras el dominio del cliente aquí</li>
                    <li>El sistema genera un subdominio en sajet.us</li>
                    <li>El cliente configura un CNAME apuntando a ese subdominio</li>
                    <li>Verificas y activas el dominio</li>
                </ol>
            </div>
        </div>
    {/if}
</Modal>

<!-- Modal: Detalles del Dominio -->
<Modal 
    bind:isOpen={showDetailsModal}
    title="Detalles del Dominio"
    showFooter={false}
    size="lg"
    on:close={() => { showDetailsModal = false; selectedDomain = null; }}
>
    {#if selectedDomain}
        <div class="space-y-4">
            <!-- Info principal -->
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="text-xs text-gray-500 uppercase">Dominio Externo</label>
                    <p class="font-mono font-bold text-primary">{selectedDomain.external_domain}</p>
                </div>
                <div>
                    <label class="text-xs text-gray-500 uppercase">Subdominio Sajet</label>
                    <p class="font-mono">{selectedDomain.sajet_full_domain}</p>
                </div>
            </div>
            
            <!-- Estados -->
            <div class="flex gap-4 flex-wrap">
                <div class="flex items-center gap-2">
                    <span class="text-gray-500">Verificación:</span>
                    <Badge variant={
                        selectedDomain.verification_status === 'verified' ? 'green' :
                        selectedDomain.verification_status === 'pending' ? 'yellow' :
                        selectedDomain.verification_status === 'failed' ? 'red' : 'gray'
                    }>
                        {selectedDomain.verification_status}
                    </Badge>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-gray-500">Cloudflare:</span>
                    <Badge variant={selectedDomain.cloudflare_configured ? 'green' : 'gray'}>
                        {selectedDomain.cloudflare_configured ? 'Configurado' : 'Pendiente'}
                    </Badge>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-gray-500">Estado:</span>
                    <Badge variant={selectedDomain.is_active ? 'green' : 'red'}>
                        {selectedDomain.is_active ? 'Activo' : 'Inactivo'}
                    </Badge>
                </div>
            </div>
            
            <!-- Configuración de destino -->
            <div class="bg-gray-50 rounded-lg p-4">
                <h4 class="font-medium text-gray-900 mb-2">Destino</h4>
                <p class="font-mono text-sm">
                    http://{selectedDomain.target_node_ip}:{selectedDomain.target_port}
                </p>
            </div>
            
            <!-- Instrucciones DNS -->
            {#if selectedDomain.verification_status !== 'verified'}
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 class="font-medium text-blue-900 mb-2">Configuración DNS Requerida</h4>
                    <div class="bg-white rounded p-3 font-mono text-sm">
                        <p><span class="text-gray-500">Tipo:</span> CNAME</p>
                        <p><span class="text-gray-500">Nombre:</span> {selectedDomain.external_domain}</p>
                        <p><span class="text-gray-500">Valor:</span> {selectedDomain.sajet_full_domain}</p>
                    </div>
                </div>
            {/if}
            
            <!-- Acciones -->
            <div class="flex gap-2 pt-4 border-t">
                {#if !selectedDomain.cloudflare_configured}
                    <Button variant="secondary" on:click={() => configureCloudflare(selectedDomain)}>
                        Configurar Cloudflare
                    </Button>
                {/if}
                
                {#if selectedDomain.verification_status !== 'verified'}
                    <Button variant="primary" on:click={() => verifyDomain(selectedDomain)}>
                        Verificar DNS
                    </Button>
                {/if}
                
                <Button 
                    variant={selectedDomain.is_active ? 'ghost' : 'success'}
                    on:click={() => toggleActive(selectedDomain)}
                >
                    {selectedDomain.is_active ? 'Desactivar' : 'Activar'}
                </Button>
            </div>
        </div>
    {/if}
</Modal>

<!-- Modal: Confirmar Eliminación -->
<Modal 
    bind:isOpen={showDeleteModal}
    title="Eliminar Dominio"
    confirmText="Eliminar"
    confirmVariant="danger"
    on:close={() => { showDeleteModal = false; selectedDomain = null; }}
    on:confirm={handleDelete}
>
    {#if selectedDomain}
        <div class="text-center">
            <div class="text-5xl mb-4">⚠️</div>
            <p class="text-gray-700">
                ¿Estás seguro de que deseas eliminar el dominio<br>
                <strong class="text-red-600">{selectedDomain.external_domain}</strong>?
            </p>
            <p class="text-gray-500 text-sm mt-2">
                Esta acción también eliminará la configuración de Cloudflare asociada.
            </p>
        </div>
    {/if}
</Modal>

<style>
    .text-primary {
        color: var(--color-primary, #003B73);
    }
</style>
