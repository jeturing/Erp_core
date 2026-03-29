import api from './client';
import type {
  ClusterStatus,
  ClusterSummary,
  ContainerItem,
  ContainersListResponse,
  NodeCreatePayload,
  NodeSummary,
  NodesListResponse,
} from '../types';

export interface ContainerMetrics {
  vmid: number;
  hostname: string;
  status: string;
  ip_address: string;
  cpu_cores: number;
  cpu_used?: number;
  ram_mb: number;
  ram_used?: number;
  disk_gb: number;
  disk_used?: number;
}

export interface NodeMetrics {
  id: number;
  hostname: string;
  status: string;
  cpu_total: number;
  cpu_used: number;
  ram_total: number;
  ram_used: number;
  disk_total: number;
  disk_used: number;
}

export const infrastructureApi = {
  async getNodes(): Promise<NodesListResponse> {
    return api.get<NodesListResponse>('/api/nodes');
  },

  async createNode(payload: NodeCreatePayload): Promise<{ message: string; id: number; name: string }> {
    return api.post('/api/nodes', payload);
  },

  async getClusterStatus(): Promise<ClusterStatus> {
    return api.get<ClusterStatus>('/api/nodes/status');
  },

  async getClusterSummary(): Promise<ClusterSummary> {
    return api.get<ClusterSummary>('/api/nodes/metrics/summary');
  },

  async getContainers(): Promise<ContainersListResponse> {
    return api.get<ContainersListResponse>('/api/nodes/containers/all');
  },

  async getNodeMetrics(nodeId: number): Promise<NodeMetrics> {
    return api.get<NodeMetrics>(`/api/nodes/${nodeId}/metrics`);
  },

  async getContainerMetrics(vmid: number): Promise<ContainerMetrics> {
    return api.get<ContainerMetrics>(`/api/proxmox/metrics/${vmid}`);
  },

  async getAllContainerMetrics(): Promise<ContainerMetrics[]> {
    return api.get<ContainerMetrics[]>('/api/proxmox/containers/metrics');
  },

  async setMaintenance(nodeId: number, enable: boolean): Promise<{ message: string; status: string }> {
    return api.post(`/api/nodes/${nodeId}/maintenance?enable=${enable ? 'true' : 'false'}`);
  },

  /**
   * Devuelve nodos elegibles para recibir una migración.
   * Filtra: can_host_tenants=true, status=online, y excluye el nodo indicado.
   */
  async getEligibleMigrationTargets(excludeNodeId?: number): Promise<NodeSummary[]> {
    const res = await api.get<NodesListResponse>('/api/nodes');
    return res.items.filter(
      (n) =>
        n.can_host_tenants &&
        n.status === 'online' &&
        (excludeNodeId == null || n.id !== excludeNodeId),
    );
  },
};

export type { NodeSummary, ContainerItem };

export default infrastructureApi;
