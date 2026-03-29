import api from './client';
import type {
  MigrationStartResponse,
  MigrationStatusResponse,
  MigrationJobListResponse,
  MigrationState,
} from '../types';

/** Response genérica para operaciones dedicated service. */
export interface DedicatedServiceResponse {
  success: boolean;
  data: {
    subdomain?: string;
    http_port?: number;
    chat_port?: number;
    service_name?: string;
    overlay_path?: string;
    message?: string;
    [key: string]: unknown;
  };
  meta: { message?: string };
}

/** Stats de servicios dedicados en un nodo. */
export interface DedicatedStatsResponse {
  success: boolean;
  data: {
    node_id: number;
    total_slots: number;
    used_http_ports: number[];
    used_chat_ports: number[];
    available_slots: number;
    dedicated_deployments: number;
    shared_deployments: number;
  };
  meta: Record<string, unknown>;
}

export const migrationApi = {
  /** Inicia migración de un tenant a un nodo destino. */
  async startMigration(
    subdomain: string,
    targetNodeId: number,
    initiatedBy?: string,
    targetRuntimeMode?: 'shared_pool' | 'dedicated_service',
  ): Promise<MigrationStartResponse> {
    return api.post<MigrationStartResponse>(
      `/api/migration/${encodeURIComponent(subdomain)}/start`,
      {
        target_node_id: targetNodeId,
        ...(initiatedBy ? { initiated_by: initiatedBy } : {}),
        ...(targetRuntimeMode ? { target_runtime_mode: targetRuntimeMode } : {}),
      },
    );
  },

  /** Consulta estado de migración activa para un tenant. */
  async getMigrationStatus(subdomain: string): Promise<MigrationStatusResponse> {
    return api.get<MigrationStatusResponse>(
      `/api/migration/${encodeURIComponent(subdomain)}/status`,
    );
  },

  /** Cancela una migración en curso. */
  async cancelMigration(
    subdomain: string,
    reason?: string,
  ): Promise<MigrationStatusResponse> {
    return api.post<MigrationStatusResponse>(
      `/api/migration/${encodeURIComponent(subdomain)}/cancel`,
      reason ? { reason } : {},
    );
  },

  /** Lista jobs de migración con filtros opcionales. */
  async listJobs(params?: {
    state?: MigrationState | string;
    limit?: number;
    offset?: number;
  }): Promise<MigrationJobListResponse> {
    const qs = new URLSearchParams();
    if (params?.state) qs.set('state', params.state);
    if (params?.limit != null) qs.set('limit', String(params.limit));
    if (params?.offset != null) qs.set('offset', String(params.offset));
    const suffix = qs.toString() ? `?${qs.toString()}` : '';
    return api.get<MigrationJobListResponse>(`/api/migration/jobs${suffix}`);
  },

  /** Obtiene detalle de un job específico. */
  async getJob(jobId: string): Promise<MigrationStatusResponse> {
    return api.get<MigrationStatusResponse>(
      `/api/migration/jobs/${encodeURIComponent(jobId)}`,
    );
  },

  // ── Dedicated Service (Fase 3) ──────────────────────────────────

  /** Provisiona servicio dedicado para un tenant (ports + systemd + overlay). */
  async provisionDedicated(subdomain: string): Promise<DedicatedServiceResponse> {
    return api.post<DedicatedServiceResponse>(
      `/api/migration/${encodeURIComponent(subdomain)}/provision-dedicated`,
      {},
    );
  },

  /** Desmonta servicio dedicado — revierte a shared_pool. */
  async deprovisionDedicated(subdomain: string): Promise<DedicatedServiceResponse> {
    return api.post<DedicatedServiceResponse>(
      `/api/migration/${encodeURIComponent(subdomain)}/deprovision-dedicated`,
      {},
    );
  },

  /** Obtiene estadísticas de servicios dedicados del nodo del tenant. */
  async getDedicatedStats(subdomain: string): Promise<DedicatedStatsResponse> {
    return api.get<DedicatedStatsResponse>(
      `/api/migration/${encodeURIComponent(subdomain)}/dedicated-stats`,
    );
  },
};

export default migrationApi;
