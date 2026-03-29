import { api } from './api'
import type { Order, CreateOrderRequest } from '../types'

interface OrderListResponse {
  items: Order[]
  total: number
  page: number
  page_size: number
}

export const ordersService = {
  getAll: async (): Promise<Order[]> => {
    const response = await api.get<OrderListResponse>('/api/orders')
    return response.items
  },
  getRecent: () => api.get<Order[]>('/api/orders/recent'),
  create: (data: CreateOrderRequest) => api.post<Order>('/api/orders', data),
  update: (id: number, data: Partial<CreateOrderRequest>) =>
    api.put<Order>(`/api/orders/${id}`, data),
  delete: (id: number) => api.del<void>(`/api/orders/${id}`)
}
