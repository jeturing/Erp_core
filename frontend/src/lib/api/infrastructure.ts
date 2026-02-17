import api from './client';
import type {
  ClusterStatus,
  ClusterSummary,
  ContainerItem,
  ContainersListResponse,
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
};

export type { NodeSummary, ContainerItem, NodeMetrics, ContainerMetrics };

export default infrastructureApi;
