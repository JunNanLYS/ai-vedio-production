import { api } from './api'
import type { Product } from '../types'

export interface MoveProductRequest {
  direction: 'next' | 'prev'
}

export const productsService = {
  move: (productId: number, direction: 'next' | 'prev') =>
    api.post<Product>(`/api/products/${productId}/move`, { direction })
}
