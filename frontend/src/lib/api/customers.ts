// Backward compatible wrapper: legacy "customers" now maps to tenants APIs.
import { tenantsApi } from './tenants';

export const customersApi = {
  list: tenantsApi.list,
  create: tenantsApi.create,
  delete: tenantsApi.delete,
  changePassword: tenantsApi.changePassword,
  suspend: tenantsApi.suspend,
};

export default customersApi;
