import { api } from './api'
import type { CanvasAsset, SaveCanvasRequest } from '../types'

export const canvasService = {
  getAll: (projectId?: number) =>
    api.get<CanvasAsset[]>(`/api/canvas${projectId ? `?project_id=${projectId}` : ''}`),

  get: (id: number) => api.get<CanvasAsset>(`/api/canvas/${id}`),

  save: (data: SaveCanvasRequest) => api.post<CanvasAsset>('/api/canvas', data),

  update: (id: number, data: Partial<SaveCanvasRequest>) =>
    api.put<CanvasAsset>(`/api/canvas/${id}`, data),

  delete: (id: number) => api.del(`/api/canvas/${id}`),

  getDefaultProject: () =>
    api.get<{ project_id: number | null; project_name: string | null }>(
      '/api/canvas/default-project'
    ),

  setDefaultProject: (projectId: number) =>
    api.post<{ message: string; project_id: number; project_name: string }>(
      `/api/canvas/set-default-project/${projectId}`,
      {}
    )
}
