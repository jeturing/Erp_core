/**
 * Stripe Sync API — Sincronización Stripe → BD
 */
import { api } from './client';

export interface SyncResult {
  success: boolean;
  synced_at?: string;
  customers?: {
    linked: number;
    already_linked: number;
    not_found: number;
    details: any[];
  };
  subscriptions?: {
    linked: number;
    created: number;
    updated: number;
    skipped: number;
    errors: any[];
    details: any[];
  };
  invoices?: {
    imported: number;
    updated: number;
    skipped_existing: number;
    skipped_no_match: number;
    errors: any[];
    details: any[];
  };
}

export interface SyncStatus {
  last_sync: string | null;
  last_result: SyncResult | null;
  database: {
    customers: {
      total: number;
      stripe_linked: number;
      admin_accounts: number;
      unlinked: number;
    };
    subscriptions: {
      active: number;
      stripe_linked: number;
      unlinked: number;
    };
    invoices: {
      total: number;
      from_stripe: number;
      manual: number;
    };
  };
}

export const stripeSyncApi = {
  /** Full sync: customers + subscriptions + invoices */
  fullSync: (monthsBack = 3): Promise<SyncResult> =>
    api.post(`/api/stripe-sync/full?months_back=${monthsBack}`),

  /** Solo sincronizar suscripciones */
  syncSubscriptions: (): Promise<SyncResult> =>
    api.post('/api/stripe-sync/subscriptions'),

  /** Solo importar facturas */
  syncInvoices: (monthsBack = 3): Promise<SyncResult> =>
    api.post(`/api/stripe-sync/invoices?months_back=${monthsBack}`),

  /** Solo vincular stripe_customer_id */
  syncCustomers: (): Promise<SyncResult> =>
    api.post('/api/stripe-sync/customers'),

  /** Estado de la última sincronización */
  getStatus: (): Promise<SyncStatus> =>
    api.get('/api/stripe-sync/status'),
};

export default stripeSyncApi;
