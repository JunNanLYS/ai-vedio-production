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
  category: 'prompt' | 'image' | 'audio' | 'video' | 'document'
  sub_category: string
  file_path: string
  file_type: string
  project_id: number | null
  created_at: string
}

export interface CreateAssetRequest {
  name: string
  category: 'prompt' | 'image' | 'audio' | 'video' | 'document'
  sub_category: string
  file_path: string
  file_type: string
  project_id?: number
}
