import { api } from './api'
import type { Workflow, Product, CreateWorkflowRequest, UpdateWorkflowRequest, CreateProductRequest, OrderWorkflowResponse } from '../types'

export const workflowsService = {
  getAll: () => api.get<Workflow[]>('/api/workflows'),
  create: (data: CreateWorkflowRequest) => api.post<Workflow>('/api/workflows', data),
  update: (id: number, data: UpdateWorkflowRequest) => api.put<Workflow>(`/api/workflows/${id}`, data),
  delete: (id: number) => api.del<void>(`/api/workflows/${id}`),
  getOrderWorkflow: (orderId: number) =>
    api.get<OrderWorkflowResponse>(`/api/orders/${orderId}/workflow`),
  addProduct: (orderId: number, data: CreateProductRequest) =>
    api.post<Product>(`/api/orders/${orderId}/products`, data),
  applyToOrder: (orderId: number, workflowId: number) =>
    api.post<Workflow>(`/api/orders/${orderId}/apply-workflow/${workflowId}`, {})
}
