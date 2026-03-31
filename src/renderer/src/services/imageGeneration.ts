import { api } from './api'

export interface ImageGenerationRequest {
  prompt: string
  model: string
  aspect_ratio: string
  resolution: string
  output_format: string
  image_input: string[]
}

export interface ImageGenerationResponse {
  task_id: string
  message: string
}

export interface TaskStatusResponse {
  task_id: string
  status: string
  result_urls: string[]
  error_message: string
  progress: number
}

export interface DownloadResponse {
  asset_id: number
  file_path: string
  file_name: string
}

export interface UploadImageResponse {
  file_url: string
  file_name: string
  file_size: number
}

export const imageGenerationService = {
  createTask: (request: ImageGenerationRequest) =>
    api.post<ImageGenerationResponse>('/api/image-generation/create', request),
  
  getStatus: (taskId: string) =>
    api.get<TaskStatusResponse>(`/api/image-generation/status/${taskId}`),
  
  downloadImage: (imageUrl: string, projectId?: number) =>
    api.post<DownloadResponse>('/api/image-generation/download', { 
      image_url: imageUrl,
      project_id: projectId || 0
    }),
  
  uploadImage: (filePath: string, assetId?: number) =>
    api.post<UploadImageResponse>('/api/image-generation/upload', { 
      file_path: filePath || "",
      asset_id: assetId || 0
    })
}
