import api from './client'

const BASE = '/api/v1/webhooks/admin/email-packages'

export interface PostalEmailPackage {
  id: number
  name: string
  description?: string | null
  price_monthly: number
  email_quota_monthly: number
  email_burst_limit_60m: number
  email_overage_price: number
  is_active: boolean
  sort_order: number
}

export interface TenantEmailOverviewItem {
  customer_id: number
  company_name: string
  subdomain: string
  email: string
  partner_id: number | null
  plan: string | null
  subscription_id: number | null
  billing_mode: string | null
  active_email_profile: {
    addon_id: number
    catalog_item_id: number
    name: string
    quantity: number
    unit_price_monthly: number
    starts_at?: string | null
  } | null
  effective_limits: {
    max_emails_monthly: number
    email_rate_per_minute: number
    email_rate_per_hour: number
    email_rate_per_day: number
  }
  pending_addon_invoices: {
    count: number
    total: number
    currency: string
  }
}

export const postalAdminApi = {
  async listPackages(includeInactive = true): Promise<{ items: PostalEmailPackage[]; total: number }> {
    return api.get(`${BASE}?include_inactive=${includeInactive ? 'true' : 'false'}`)
  },

  async createPackage(payload: {
    name: string
    description?: string
    price_monthly: number
    email_quota_monthly: number
    email_burst_limit_60m: number
    email_overage_price: number
    sort_order?: number
  }): Promise<{ message: string; item: PostalEmailPackage }> {
    return api.post(BASE, payload)
  },

  async updatePackage(
    itemId: number,
    payload: {
      name: string
      description?: string
      price_monthly: number
      email_quota_monthly: number
      email_burst_limit_60m: number
      email_overage_price: number
      sort_order?: number
    },
  ): Promise<{ message: string; item: PostalEmailPackage }> {
    return api.put(`${BASE}/${itemId}`, payload)
  },

  async deactivatePackage(itemId: number): Promise<{ message: string }> {
    return api.delete(`${BASE}/${itemId}`)
  },

  async reactivatePackage(itemId: number): Promise<{ message: string; item: PostalEmailPackage }> {
    return api.put(`${BASE}/${itemId}/reactivate`)
  },

  async getTenantOverview(search = '', limit = 100, offset = 0): Promise<{
    items: TenantEmailOverviewItem[]
    total: number
    limit: number
    offset: number
    packages: PostalEmailPackage[]
  }> {
    const params = new URLSearchParams()
    if (search.trim()) params.set('search', search.trim())
    params.set('limit', String(limit))
    params.set('offset', String(offset))
    return api.get(`${BASE}/tenant-overview?${params.toString()}`)
  },

  async assignPackage(payload: {
    customer_id: number
    catalog_item_id: number
    quantity?: number
    charge_now?: boolean
    notes?: string
  }): Promise<any> {
    return api.post(`${BASE}/assign`, payload)
  },

  async updateTenantSubscriptionQuantity(addonId: number, quantity: number): Promise<{ message: string; addon_id: number; quantity: number }> {
    return api.put(`${BASE}/tenant-subscriptions/${addonId}?quantity=${encodeURIComponent(String(quantity))}`)
  },

  async deactivateTenantSubscription(addonId: number): Promise<{ message: string; addon_id: number }> {
    return api.delete(`${BASE}/tenant-subscriptions/${addonId}`)
  },

    async bulkAssignFree(catalogItemId: number): Promise<{ message: string; assigned: number; skipped: number; errors: number }> {
      return api.post(`${BASE}/bulk-assign-free`, { catalog_item_id: catalogItemId })
    },
}
