import { api, getBackendUrl } from './api'
import type { Asset, CreateAssetRequest, Project, SubCategory } from '../types'

export const assetsService = {
  getAll: (category?: string) =>
    api.get<Asset[]>(`/api/assets${category ? `?category=${category}` : ''}`),
  getById: (id: number) => api.get<Asset>(`/api/assets/${id}`),
  create: (data: CreateAssetRequest) => api.post<Asset>('/api/assets', data),
  upload: async (file: File, category: string, subCategory: string) => {
    const baseUrl = await getBackendUrl()
    const formData = new FormData()
    formData.append('file', file)
    formData.append('category', category)
    formData.append('sub_category', subCategory)
    const response = await fetch(`${baseUrl}/api/assets/upload`, {
      method: 'POST',
      body: formData
    })
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || '上传失败')
    }
    return response.json()
  },
  delete: (id: number) => api.del(`/api/assets/${id}`),
  rename: (id: number, newName: string) =>
    api.put<Asset>(`/api/assets/${id}/rename`, { new_name: newName }),
  getFilePath: (id: number) => api.get<{ path: string }>(`/api/assets/${id}/path`),
  getContent: (id: number) =>
    api.get<{ content: string; name: string }>(`/api/assets/${id}/content`),
  getPreviewUrl: async (id: number): Promise<string> => {
    const baseUrl = await getBackendUrl()
    return `${baseUrl}/api/assets/${id}/preview`
  },

  getProjects: () => api.get<Project[]>('/api/projects'),
  createProject: (name: string, path?: string) =>
    api.post<Project>('/api/projects', { project_name: name, project_path: path }),
  loadProject: (path: string) =>
    api.post<{ message: string; project: Project; loaded_assets: number }>('/api/projects/load', {
      project_path: path
    }),
  getCurrentProject: () => api.get<{ project: Project | null }>('/api/projects/current'),
  switchProject: (projectId: number) =>
    api.post<{ message: string; project: Project }>(`/api/projects/switch/${projectId}`, {}),
  deleteProject: (projectId: number) => api.del(`/api/projects/${projectId}`),
  getProjectPath: () => api.get<{ path: string }>('/api/projects/path'),

  getSubCategories: (category?: string) =>
    api.get<SubCategory[]>(`/api/subcategories${category ? `?category=${category}` : ''}`),
  createSubCategory: (category: string, name: string) =>
    api.post<SubCategory>('/api/subcategories', { category, name }),
  deleteSubCategory: (id: number) => api.del(`/api/subcategories/${id}`),

  moveAsset: (assetId: number, targetProjectId: number, targetCategory: string, targetSubCategory: string) =>
    api.post<Asset>(`/api/assets/${assetId}/move`, {
      target_project_id: targetProjectId,
      target_category: targetCategory,
      target_sub_category: targetSubCategory
    })
}
