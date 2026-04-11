<script lang="ts">
  import { onMount } from 'svelte'
  import { postalAdminApi } from '$lib/api'
  import { toasts } from '$lib/stores/toast'
  import type { PostalEmailPackage, TenantEmailOverviewItem } from '$lib/api'
  import { RefreshCw, Plus, Save, Trash2, Power, PowerOff, CreditCard } from 'lucide-svelte'

  let loading = true
  let saving = false
  let assigningCustomerId: number | null = null
  let search = ''

  let packages: PostalEmailPackage[] = []
  let tenants: TenantEmailOverviewItem[] = []

  let createForm = {
    name: '',
    description: '',
    price_monthly: 0,
    email_quota_monthly: 0,
    email_burst_limit_60m: 0,
    email_overage_price: 0.0002,
    sort_order: 0,
  }

  let assignSelection: Record<number, number> = {}
  let assignQty: Record<number, number> = {}
  let chargeNowDirect: Record<number, boolean> = {}

  function fmtMoney(v: number | null | undefined): string {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(v || 0))
  }

  function fmtInt(v: number | null | undefined): string {
    return new Intl.NumberFormat('es-DO').format(Number(v || 0))
  }

  async function loadData() {
    loading = true
    try {
      const res = await postalAdminApi.getTenantOverview(search, 200, 0)
      tenants = res.items || []
      packages = res.packages || []

      const defaultPkg = packages[0]?.id || 0
      const nextSelection: Record<number, number> = {}
      const nextQty: Record<number, number> = {}
      const nextChargeNow: Record<number, boolean> = {}

      for (const t of tenants) {
        nextSelection[t.customer_id] = t.active_email_profile?.catalog_item_id || defaultPkg
        nextQty[t.customer_id] = t.active_email_profile?.quantity || 1
        nextChargeNow[t.customer_id] = true
      }

      assignSelection = nextSelection
      assignQty = nextQty
      chargeNowDirect = nextChargeNow
    } catch (e: any) {
      toasts.error(e.message || 'Error cargando administración de correo')
    } finally {
      loading = false
    }
  }

  async function createPackage() {
    if (!createForm.name.trim()) {
      toasts.error('Nombre requerido')
      return
    }
    if (createForm.price_monthly <= 0 || createForm.email_quota_monthly <= 0) {
      toasts.error('Precio y cuota mensual deben ser mayores a 0')
      return
    }

    saving = true
    try {
      await postalAdminApi.createPackage({
        name: createForm.name,
        description: createForm.description,
        price_monthly: Number(createForm.price_monthly),
        email_quota_monthly: Number(createForm.email_quota_monthly),
        email_burst_limit_60m: Number(createForm.email_burst_limit_60m),
        email_overage_price: Number(createForm.email_overage_price),
        sort_order: Number(createForm.sort_order || 0),
      })
      toasts.success('Perfil de correo creado')
      createForm = {
        name: '',
        description: '',
        price_monthly: 0,
        email_quota_monthly: 0,
        email_burst_limit_60m: 0,
        email_overage_price: 0.0002,
        sort_order: 0,
      }
      await loadData()
    } catch (e: any) {
      toasts.error(e.message || 'No se pudo crear el perfil')
    } finally {
      saving = false
    }
  }

  async function togglePackage(pkg: PostalEmailPackage) {
    try {
      if (pkg.is_active) {
        await postalAdminApi.deactivatePackage(pkg.id)
        toasts.success('Perfil desactivado')
      } else {
        await postalAdminApi.reactivatePackage(pkg.id)
        toasts.success('Perfil reactivado')
      }
      await loadData()
    } catch (e: any) {
      toasts.error(e.message || 'No se pudo actualizar el perfil')
    }
  }

  async function assignProfile(tenant: TenantEmailOverviewItem) {
    const packageId = Number(assignSelection[tenant.customer_id] || 0)
    const qty = Math.max(1, Number(assignQty[tenant.customer_id] || 1))
    if (!packageId) {
      toasts.error('Selecciona un perfil de correo')
      return
    }

    assigningCustomerId = tenant.customer_id
    try {
      const res = await postalAdminApi.assignPackage({
        customer_id: tenant.customer_id,
        catalog_item_id: packageId,
        quantity: qty,
        charge_now: !!chargeNowDirect[tenant.customer_id],
        notes: 'Asignación manual desde admin SAJET',
      })
      toasts.success(res.message || 'Perfil asignado')

      const checkoutUrl = res?.charge?.checkout_url
      if (checkoutUrl) {
        window.open(checkoutUrl, '_blank', 'noopener,noreferrer')
      }

      await loadData()
    } catch (e: any) {
      toasts.error(e.message || 'No se pudo asignar el perfil')
    } finally {
      assigningCustomerId = null
    }
  }

  async function updateQuantity(tenant: TenantEmailOverviewItem) {
    const addonId = tenant.active_email_profile?.addon_id
    if (!addonId) {
      toasts.error('El tenant no tiene perfil activo para actualizar')
      return
    }

    try {
      const qty = Math.max(1, Number(assignQty[tenant.customer_id] || 1))
      await postalAdminApi.updateTenantSubscriptionQuantity(addonId, qty)
      toasts.success('Cantidad actualizada')
      await loadData()
    } catch (e: any) {
      toasts.error(e.message || 'No se pudo actualizar la cantidad')
    }
  }

  async function removeProfile(tenant: TenantEmailOverviewItem) {
    const addonId = tenant.active_email_profile?.addon_id
    if (!addonId) {
      toasts.error('El tenant no tiene perfil activo')
      return
    }
    if (!confirm(`¿Desactivar perfil de correo para ${tenant.company_name}?`)) return

    try {
      await postalAdminApi.deactivateTenantSubscription(addonId)
      toasts.success('Perfil desactivado')
      await loadData()
    } catch (e: any) {
      toasts.error(e.message || 'No se pudo desactivar el perfil')
    }
  }

  onMount(loadData)
</script>

<div class="p-6 lg:p-8 space-y-6">
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
    <div>
      <h1 class="page-title">Perfiles de Correo por Tenant</h1>
      <p class="page-subtitle mt-1">CRUD de planes de correo, asignación por tenant y control de cobro inmediato para clientes directos.</p>
    </div>
    <button class="btn btn-secondary btn-sm" on:click={loadData} disabled={loading}>
      <RefreshCw size={13} class={loading ? 'animate-spin' : ''} />
      Actualizar
    </button>
  </div>

  <div class="card">
    <div class="flex items-center gap-2 mb-4">
      <Plus size={16} />
      <h2 class="section-heading">Crear perfil de correo</h2>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-3">
      <input class="input" placeholder="Nombre" bind:value={createForm.name} />
      <input class="input" placeholder="Descripción" bind:value={createForm.description} />
      <input class="input" type="number" min="0" step="0.01" placeholder="Precio mensual" bind:value={createForm.price_monthly} />
      <input class="input" type="number" min="0" step="1" placeholder="Cuota mensual" bind:value={createForm.email_quota_monthly} />
      <input class="input" type="number" min="0" step="1" placeholder="Burst 60m" bind:value={createForm.email_burst_limit_60m} />
      <input class="input" type="number" min="0" step="0.0001" placeholder="Sobreuso" bind:value={createForm.email_overage_price} />
    </div>
    <div class="mt-3">
      <button class="btn-accent btn-sm" on:click={createPackage} disabled={saving}>
        <Save size={14} />
        Crear perfil
      </button>
    </div>

    <div class="mt-5 overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="text-left text-gray-500 border-b border-border-light">
            <th class="py-2">Perfil</th>
            <th class="py-2">Precio</th>
            <th class="py-2">Cuota</th>
            <th class="py-2">Burst 60m</th>
            <th class="py-2">Estado</th>
            <th class="py-2 text-right">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#each packages as pkg}
            <tr class="border-b border-border-light/60">
              <td class="py-2">
                <div class="font-semibold text-text-primary">{pkg.name}</div>
                <div class="text-xs text-gray-500">{pkg.description || '—'}</div>
              </td>
              <td class="py-2">{fmtMoney(pkg.price_monthly)}</td>
              <td class="py-2">{fmtInt(pkg.email_quota_monthly)}</td>
              <td class="py-2">{fmtInt(pkg.email_burst_limit_60m)}</td>
              <td class="py-2">
                <span class={pkg.is_active ? 'badge badge-success' : 'badge badge-neutral'}>{pkg.is_active ? 'activo' : 'inactivo'}</span>
              </td>
              <td class="py-2 text-right">
                <button class="btn btn-secondary btn-xs" on:click={() => togglePackage(pkg)}>
                  {#if pkg.is_active}
                    <PowerOff size={12} /> Desactivar
                  {:else}
                    <Power size={12} /> Reactivar
                  {/if}
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <div class="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between mb-4">
      <h2 class="section-heading">Asignación por tenant + cobros</h2>
      <input class="input w-full sm:w-80" placeholder="Buscar por empresa, subdominio o email" bind:value={search} on:keydown={(e) => e.key === 'Enter' && loadData()} />
    </div>

    <div class="overflow-x-auto">
      <table class="w-full text-sm min-w-[1200px]">
        <thead>
          <tr class="text-left text-gray-500 border-b border-border-light">
            <th class="py-2">Tenant</th>
            <th class="py-2">Perfil activo</th>
            <th class="py-2">Límites efectivos</th>
            <th class="py-2">Pendiente facturar</th>
            <th class="py-2">Asignar perfil</th>
            <th class="py-2 text-right">CRUD</th>
          </tr>
        </thead>
        <tbody>
          {#if loading}
            <tr><td colspan="6" class="py-8 text-center text-gray-500">Cargando...</td></tr>
          {:else if tenants.length === 0}
            <tr><td colspan="6" class="py-8 text-center text-gray-500">Sin resultados</td></tr>
          {:else}
            {#each tenants as tenant}
              <tr class="border-b border-border-light/60 align-top">
                <td class="py-3">
                  <div class="font-semibold text-text-primary">{tenant.company_name}</div>
                  <div class="text-xs text-gray-500">{tenant.subdomain}.sajet.us</div>
                  <div class="text-xs text-gray-500">{tenant.email}</div>
                  <div class="mt-1 text-[11px] text-gray-500">{tenant.partner_id ? `Partner #${tenant.partner_id}` : 'Cliente directo'}</div>
                </td>

                <td class="py-3">
                  {#if tenant.active_email_profile}
                    <div class="font-semibold">{tenant.active_email_profile.name}</div>
                    <div class="text-xs text-gray-500">x {tenant.active_email_profile.quantity} · {fmtMoney(tenant.active_email_profile.unit_price_monthly)}/mes</div>
                  {:else}
                    <span class="text-xs text-gray-500">Sin perfil activo</span>
                  {/if}
                </td>

                <td class="py-3 text-xs">
                  <div>Mes: <b>{fmtInt(tenant.effective_limits.max_emails_monthly)}</b></div>
                  <div>Min: <b>{fmtInt(tenant.effective_limits.email_rate_per_minute)}</b></div>
                  <div>Hora: <b>{fmtInt(tenant.effective_limits.email_rate_per_hour)}</b></div>
                  <div>Día: <b>{fmtInt(tenant.effective_limits.email_rate_per_day)}</b></div>
                </td>

                <td class="py-3">
                  <div class="font-semibold">{fmtMoney(tenant.pending_addon_invoices.total)}</div>
                  <div class="text-xs text-gray-500">{tenant.pending_addon_invoices.count} facturas</div>
                </td>

                <td class="py-3">
                  <div class="space-y-2">
                    <select class="input" bind:value={assignSelection[tenant.customer_id]}>
                      {#each packages.filter((p) => p.is_active) as pkg}
                        <option value={pkg.id}>{pkg.name} · {fmtMoney(pkg.price_monthly)}</option>
                      {/each}
                    </select>
                    <div class="flex items-center gap-2">
                      <input class="input w-20" type="number" min="1" bind:value={assignQty[tenant.customer_id]} />
                      <label class="text-xs text-gray-600 inline-flex items-center gap-1">
                        <input type="checkbox" bind:checked={chargeNowDirect[tenant.customer_id]} disabled={!!tenant.partner_id} />
                        Cobrar ahora (directo)
                      </label>
                    </div>
                    <button class="btn-accent btn-xs" on:click={() => assignProfile(tenant)} disabled={assigningCustomerId === tenant.customer_id}>
                      {#if assigningCustomerId === tenant.customer_id}
                        <RefreshCw size={12} class="animate-spin" />
                      {:else}
                        <CreditCard size={12} />
                      {/if}
                      Asignar perfil
                    </button>
                  </div>
                </td>

                <td class="py-3 text-right">
                  <div class="flex gap-2 justify-end">
                    <button class="btn btn-secondary btn-xs" on:click={() => updateQuantity(tenant)} disabled={!tenant.active_email_profile}>
                      <Save size={12} /> Cantidad
                    </button>
                    <button class="btn btn-danger btn-xs" on:click={() => removeProfile(tenant)} disabled={!tenant.active_email_profile}>
                      <Trash2 size={12} /> Quitar
                    </button>
                  </div>
                </td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
  </div>
</div>
