import api from './client';
import type {
  ClusterStatus,
  ClusterSummary,
  ContainerItem,
  ContainersListResponse,
  NodeSummary,
  NodesListResponse,
} from '../types';

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

  async setMaintenance(nodeId: number, enable: boolean): Promise<{ message: string; status: string }> {
    return api.post(`/api/nodes/${nodeId}/maintenance?enable=${enable ? 'true' : 'false'}`);
  },
};

export type { NodeSummary, ContainerItem };

export default infrastructureApi;
