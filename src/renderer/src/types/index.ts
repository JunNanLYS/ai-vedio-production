// 订单类型
export interface Order {
  id: number
  company_name: string
  progress: number
  video_count: number
  unit_price: number
  income: number
  profit: number
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  created_at: string
  updated_at: string
}

export interface CreateOrderRequest {
  company_name: string
  video_count: number
  unit_price: number
  income?: number
  profit?: number
  workflow_id?: number
  status?: 'pending' | 'in_progress' | 'completed' | 'cancelled'
}

// 仪表盘统计
export interface DashboardStats {
  monthly_income: number
  monthly_profit: number
  income_trend: number
  profit_trend: number
  total_orders: number
  completed_orders: number
}

// 工作流
export interface Workflow {
  id: number
  name: string
  description: string
  order_id: number | null
  steps: string[]
  created_at: string
}

export interface CreateWorkflowRequest {
  name: string
  description: string
  steps: string[]
  order_id?: number
}

export interface UpdateWorkflowRequest {
  name?: string
  description?: string
  steps?: string[]
}

// 产品
export interface Product {
  id: number
  order_id: number
  name: string
  current_step: number
  status: string
  created_at: string
}

export interface CreateProductRequest {
  name: string
}

export interface StepProducts {
  step_name: string
  step_index: number
  products: Product[]
}

export interface OrderWorkflowResponse {
  workflow: Workflow
  steps_with_products: StepProducts[]
}

// 项目
export interface Project {
  id: number
  name: string
  path: string
  created_at: string
}

// 子分类
export interface SubCategory {
  id: number
  category: string
  name: string
  project_id: number | null
  created_at: string
}

// 资产
export interface Asset {
  id: number
  name: string
  category: 'prompt' | 'image' | 'audio' | 'video' | 'document' | 'canvas'
  sub_category: string
  file_path: string
  file_type: string
  project_id: number | null
  created_at: string
  uploading?: boolean
  tempId?: string
}

export interface CreateAssetRequest {
  name: string
  category: 'prompt' | 'image' | 'audio' | 'video' | 'document' | 'canvas'
  sub_category: string
  file_path: string
  file_type: string
  project_id?: number
}

// 画布节点类型
export type CanvasNodeType = 'asset' | 'upload-image' | 'generate-image' | 'text-annotation'

// 图片生成模型类型
export type ImageGenModel = 'nano-banana-2' | 'nano-banana-pro'

// 图片比例类型
export type ImageAspectRatio =
  | 'auto'
  | '1:1'
  | '1:4'
  | '1:8'
  | '2:3'
  | '3:2'
  | '3:4'
  | '4:1'
  | '4:3'
  | '4:5'
  | '5:4'
  | '8:1'
  | '9:16'
  | '16:9'
  | '21:9'

// 分辨率类型
export type ImageResolution = '1k' | '2k' | '4k'

// 输出格式类型
export type ImageOutputFormat = 'png' | 'jpg'

// 画布节点
export interface CanvasNode {
  id: string
  type: CanvasNodeType
  assetId?: number
  x: number
  y: number
  width: number
  height: number
  name: string
  category?: 'prompt' | 'image' | 'audio' | 'video' | 'document' | 'canvas'
  fileType?: string
  filePath?: string
  localImagePath?: string
  prompt?: string
  text?: string
  referenceImages?: { nodeId: string; order: number }[]
  fileSize?: number
  // 生成图片配置
  genModel?: ImageGenModel
  aspectRatio?: ImageAspectRatio
  resolution?: ImageResolution
  outputFormat?: ImageOutputFormat
}

// 画布连接
export interface CanvasConnection {
  id: string
  sourceId: string
  targetId: string
  type?: 'reference' | 'default'
  order?: number
}

// 画布状态
export interface CanvasState {
  nodes: CanvasNode[]
  connections: CanvasConnection[]
  viewport: {
    x: number
    y: number
    scale: number
  }
}

// 画布资产
export interface CanvasAsset {
  id: number
  name: string
  nodes: CanvasNode[]
  connections: CanvasConnection[]
  viewport: { x: number; y: number; scale: number }
  project_id: number | null
  asset_id: number | null
  created_at: string
  updated_at: string
}

export interface SaveCanvasRequest {
  name: string
  nodes: CanvasNode[]
  connections: CanvasConnection[]
  viewport: { x: number; y: number; scale: number }
  project_id?: number
  asset_id?: number
}
