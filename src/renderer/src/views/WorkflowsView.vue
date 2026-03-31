<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useLocalStorage } from '@vueuse/core'
import { onBeforeRouteLeave } from 'vue-router'
import { workflowsService } from '@/services/workflows'
import { productsService } from '@/services/products'
import { ordersService } from '@/services/orders'
import { canvasService } from '@/services/canvas'
import { assetsService } from '@/services/assets'
import { imageGenerationService } from '@/services/imageGeneration'
import type {
  Workflow,
  Order,
  Product,
  OrderWorkflowResponse,
  CanvasNode,
  CanvasConnection,
  CanvasAsset,
  Asset,
  Project
} from '@/types'
import SegmentedControl from '@/components/workflows/SegmentedControl.vue'
import WorkflowList from '@/components/workflows/WorkflowList.vue'
import WorkflowEditDialog from '@/components/workflows/WorkflowEditDialog.vue'
import WorkflowTemplateSelector from '@/components/workflows/WorkflowTemplateSelector.vue'
import Timeline from '@/components/workflows/Timeline.vue'
import InfiniteCanvas from '@/components/workflows/InfiniteCanvas.vue'
import CanvasSidebar from '@/components/workflows/CanvasSidebar.vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { InputDialog, ConfirmDialog, NewCanvasDialog } from '@/components/ui/dialog'
import { toast } from '@/components/ui/toast/use-toast'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'

const SEGMENT_OPTIONS = ['工作流管理', '订单工作流', '画布']
const DEFAULT_STEPS = ['脚本', '配音', '剪辑', '渲染']

const currentSegment = ref(SEGMENT_OPTIONS[0])
const workflows = ref<Workflow[]>([])
const orders = ref<Order[]>([])
const selectedOrderId = ref<number | null>(null)
const orderWorkflow = ref<OrderWorkflowResponse | null>(null)
const loading = ref({
  workflows: false,
  orders: false,
  orderWorkflow: false
})

const editDialogOpen = ref(false)
const editingWorkflow = ref<Workflow | null>(null)

const inputDialogOpen = ref(false)
const inputDialogTitle = ref('')
const inputDialogLabel = ref('')
const inputDialogPlaceholder = ref('')
const inputDialogDefault = ref('')
const inputDialogCallback = ref<((value: string) => void) | null>(null)

const confirmDialogOpen = ref(false)
const confirmDialogTitle = ref('确认')
const confirmDialogMessage = ref('')
const confirmDialogVariant = ref<'default' | 'danger'>('default')
const confirmDialogCallback = ref<(() => void) | null>(null)

const newCanvasDialogOpen = ref(false)

interface CanvasState {
  nodes: CanvasNode[]
  connections: CanvasConnection[]
  viewport: { x: number; y: number; scale: number }
  canvasId: number | null
  canvasName: string | null
  projectId: number | null
  projectName: string | null
}

const savedCanvasState = useLocalStorage<CanvasState>('canvas-state', {
  nodes: [],
  connections: [],
  viewport: { x: 0, y: 0, scale: 1 },
  canvasId: null,
  canvasName: null,
  projectId: null,
  projectName: null
})

const canvasNodes = ref<CanvasNode[]>(savedCanvasState.value.nodes)
const canvasConnections = ref<CanvasConnection[]>(savedCanvasState.value.connections)
const assetDrawerOpen = ref(false)

const projects = ref<Project[]>([])
const defaultCanvasProject = ref<{ project_id: number | null; project_name: string | null }>({
  project_id: savedCanvasState.value.projectId,
  project_name: savedCanvasState.value.projectName
})
const currentCanvasName = ref<string | null>(savedCanvasState.value.canvasName)
const currentCanvasId = ref<number | null>(savedCanvasState.value.canvasId)
const canvasViewport = ref(savedCanvasState.value.viewport)
const canvasList = ref<CanvasAsset[]>([])
const canvasListLoading = ref(false)

const saveCanvasState = (): void => {
  savedCanvasState.value = {
    nodes: canvasNodes.value,
    connections: canvasConnections.value,
    viewport: canvasViewport.value,
    canvasId: currentCanvasId.value,
    canvasName: currentCanvasName.value,
    projectId: defaultCanvasProject.value.project_id,
    projectName: defaultCanvasProject.value.project_name
  }
}

watch(
  [
    canvasNodes,
    canvasConnections,
    canvasViewport,
    currentCanvasId,
    currentCanvasName,
    defaultCanvasProject
  ],
  saveCanvasState,
  { deep: true }
)

const allProducts = computed(() => {
  if (!orderWorkflow.value?.steps_with_products) return []
  return orderWorkflow.value.steps_with_products.flatMap((sp) => sp.products)
})

const hasWorkflow = computed(() => {
  return orderWorkflow.value !== null
})

const selectedOrderIdString = computed({
  get: () => selectedOrderId.value?.toString() ?? '',
  set: (value: string) => {
    selectedOrderId.value = value ? parseInt(value, 10) : null
  }
})

const fetchWorkflows = async (): Promise<void> => {
  loading.value.workflows = true
  try {
    workflows.value = await workflowsService.getAll()
  } catch (error) {
    console.error('获取工作流列表失败:', error)
  } finally {
    loading.value.workflows = false
  }
}

const fetchOrders = async (): Promise<void> => {
  loading.value.orders = true
  try {
    orders.value = await ordersService.getAll()
    if (orders.value.length > 0 && !selectedOrderId.value) {
      selectedOrderId.value = orders.value[0].id
      await fetchOrderWorkflow()
    }
  } catch (error) {
    console.error('获取订单列表失败:', error)
  } finally {
    loading.value.orders = false
  }
}

const fetchOrderWorkflow = async (): Promise<void> => {
  if (!selectedOrderId.value) return

  loading.value.orderWorkflow = true
  try {
    orderWorkflow.value = await workflowsService.getOrderWorkflow(selectedOrderId.value)
  } catch (error) {
    console.error('获取订单工作流失败:', error)
    orderWorkflow.value = null
  } finally {
    loading.value.orderWorkflow = false
  }
}

const showInputDialog = (
  title: string,
  options: {
    label?: string
    placeholder?: string
    defaultValue?: string
  },
  callback: (value: string) => void
): void => {
  inputDialogTitle.value = title
  inputDialogLabel.value = options.label || ''
  inputDialogPlaceholder.value = options.placeholder || ''
  inputDialogDefault.value = options.defaultValue || ''
  inputDialogCallback.value = callback
  inputDialogOpen.value = true
}

const showConfirmDialog = (
  title: string,
  message: string,
  callback: () => void,
  variant: 'default' | 'danger' = 'default'
): void => {
  confirmDialogTitle.value = title
  confirmDialogMessage.value = message
  confirmDialogVariant.value = variant
  confirmDialogCallback.value = callback
  confirmDialogOpen.value = true
}

const handleInputDialogConfirm = (value: string): void => {
  if (inputDialogCallback.value) {
    inputDialogCallback.value(value)
    inputDialogCallback.value = null
  }
}

const handleConfirmDialogConfirm = (): void => {
  if (confirmDialogCallback.value) {
    confirmDialogCallback.value()
    confirmDialogCallback.value = null
  }
}

const handleCreateWorkflow = async (): Promise<void> => {
  showInputDialog(
    '创建工作流',
    {
      label: '工作流名称',
      placeholder: '请输入工作流名称',
      defaultValue: '新工作流'
    },
    async (name: string) => {
      if (!name.trim()) return
      try {
        await workflowsService.create({
          name: name.trim(),
          description: '',
          steps: DEFAULT_STEPS
        })
        await fetchWorkflows()
      } catch (error) {
        console.error('创建工作流失败:', error)
      }
    }
  )
}

const handleEditWorkflow = (workflow: Workflow): void => {
  editingWorkflow.value = workflow
  editDialogOpen.value = true
}

const handleSaveWorkflow = async (
  id: number,
  data: { name: string; steps: string[] }
): Promise<void> => {
  try {
    await workflowsService.update(id, data)
    await fetchWorkflows()
  } catch (error) {
    console.error('更新工作流失败:', error)
  }
}

const handleDeleteWorkflow = async (id: number): Promise<void> => {
  showConfirmDialog(
    '删除工作流',
    '确定要删除此工作流吗？此操作不可撤销。',
    async () => {
      try {
        await workflowsService.delete(id)
        await fetchWorkflows()
      } catch (error) {
        console.error('删除工作流失败:', error)
      }
    },
    'danger'
  )
}

const handleAddProduct = async (): Promise<void> => {
  if (!selectedOrderId.value) return

  showInputDialog(
    '添加产品',
    {
      label: '产品名称',
      placeholder: '请输入产品名称'
    },
    async (name: string) => {
      if (!name.trim()) return
      try {
        await workflowsService.addProduct(selectedOrderId.value!, { name: name.trim() })
        await fetchOrderWorkflow()
      } catch (error) {
        console.error('添加产品失败:', error)
      }
    }
  )
}

const handleProductClick = (product: Product): void => {
  console.log('查看产品详情:', product)
}

const updateProductStep = (productId: number, newStep: number, newStatus: string): void => {
  if (!orderWorkflow.value?.steps_with_products) return

  for (const stepProducts of orderWorkflow.value.steps_with_products) {
    const productIndex = stepProducts.products.findIndex((p) => p.id === productId)
    if (productIndex !== -1) {
      const product = stepProducts.products.splice(productIndex, 1)[0]
      product.current_step = newStep
      product.status = newStatus

      const targetStep = orderWorkflow.value.steps_with_products.find(
        (sp) => sp.step_index === newStep
      )
      if (targetStep) {
        targetStep.products.push(product)
      }
      break
    }
  }
}

const handleProductMovePrev = async (product: Product): Promise<void> => {
  try {
    const result = await productsService.move(product.id, 'prev')
    updateProductStep(product.id, result.current_step, result.status)
  } catch (error) {
    console.error('移动产品失败:', error)
    toast({ title: '移动产品失败', variant: 'destructive' })
  }
}

const handleProductMoveNext = async (product: Product): Promise<void> => {
  try {
    const result = await productsService.move(product.id, 'next')
    updateProductStep(product.id, result.current_step, result.status)
  } catch (error) {
    console.error('移动产品失败:', error)
    toast({ title: '移动产品失败', variant: 'destructive' })
  }
}

const handleOrderChange = (): void => {
  fetchOrderWorkflow()
}

const handleApplyTemplate = async (workflowId: number): Promise<void> => {
  if (!selectedOrderId.value) return

  try {
    await workflowsService.applyToOrder(selectedOrderId.value, workflowId)
    await fetchOrderWorkflow()
  } catch (error) {
    console.error('应用模板失败:', error)
    toast({ title: '应用模板失败', variant: 'destructive' })
  }
}

const generateNodeId = (): string => {
  return `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

const handleAssetDrop = async (asset: Asset, x: number, y: number): Promise<void> => {
  const nodeWidth = 200
  const nodeHeight = 150

  const newNode: CanvasNode = {
    id: generateNodeId(),
    type: 'asset',
    assetId: asset.id,
    x: x - nodeWidth / 2,
    y: y - nodeHeight / 2,
    width: nodeWidth,
    height: nodeHeight,
    name: asset.name,
    category: asset.category,
    fileType: asset.file_type,
    filePath: asset.file_path
  }

  canvasNodes.value.push(newNode)

  if (asset.category === 'image') {
    try {
      const { assetsService } = await import('@/services/assets')
      const previewUrl = await assetsService.getPreviewUrl(asset.id)
      const node = canvasNodes.value.find((n) => n.id === newNode.id)
      if (node) {
        node.localImagePath = previewUrl
      }
    } catch (error) {
      console.error('获取预览图失败:', error)
    }
  }
}

const handleNodeCreate = (type: string, x: number, y: number): void => {
  const nodeConfigs: Record<string, { width: number; height: number; name: string }> = {
    'upload-image': { width: 200, height: 150, name: '上传图片' },
    'generate-image': { width: 320, height: 420, name: '生成图片' },
    'text-annotation': { width: 200, height: 120, name: '文本注释' }
  }

  const config = nodeConfigs[type] || { width: 200, height: 150, name: '节点' }

  const newNode: CanvasNode = {
    id: generateNodeId(),
    type: type as CanvasNode['type'],
    x: x - config.width / 2,
    y: y - config.height / 2,
    width: config.width,
    height: config.height,
    name: config.name
  }

  canvasNodes.value.push(newNode)
}

const handleNodeUpdate = (id: string, updates: Partial<CanvasNode>): void => {
  const node = canvasNodes.value.find((n) => n.id === id)
  if (node) {
    Object.assign(node, updates)
  }
}

const handleConnectionCreate = (sourceId: string, targetId: string): void => {
  const MAX_REFERENCE_IMAGES = 14
  const MAX_FILE_SIZE = 30 * 1024 * 1024

  const existingConnections = canvasConnections.value.filter(
    (c) => c.targetId === targetId && c.type === 'reference'
  )

  if (existingConnections.length >= MAX_REFERENCE_IMAGES) {
    toast({
      title: '参考图片已达上限',
      description: `最多只能添加${MAX_REFERENCE_IMAGES}张参考图片`,
      variant: 'destructive'
    })
    return
  }

  const sourceNode = canvasNodes.value.find((n) => n.id === sourceId)
  if (sourceNode?.fileSize) {
    const totalSize =
      existingConnections.reduce((sum, c) => {
        const node = canvasNodes.value.find((n) => n.id === c.sourceId)
        return sum + (node?.fileSize || 0)
      }, 0) + sourceNode.fileSize

    if (totalSize > MAX_FILE_SIZE) {
      toast({
        title: '参考图片总大小超出限制',
        description: '参考图片总大小不能超过30MB',
        variant: 'destructive'
      })
      return
    }
  }

  const maxOrder = existingConnections.reduce((max, c) => Math.max(max, c.order || 0), 0)

  const newConnection: CanvasConnection = {
    id: `conn-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    sourceId,
    targetId,
    type: 'reference',
    order: maxOrder + 1
  }

  canvasConnections.value.push(newConnection)
}

const handleConnectionDelete = (id: string): void => {
  canvasConnections.value = canvasConnections.value.filter((c) => c.id !== id)
}

const handleNodeMove = (id: string, x: number, y: number): void => {
  const node = canvasNodes.value.find((n) => n.id === id)
  if (node) {
    node.x = x
    node.y = y
  }
}

const handleNodeResize = (
  id: string,
  width: number,
  height: number,
  x?: number,
  y?: number
): void => {
  const node = canvasNodes.value.find((n) => n.id === id)
  if (node) {
    node.width = width
    node.height = height
    if (x !== undefined) node.x = x
    if (y !== undefined) node.y = y
  }
}

const handleNodeDelete = (id: string): void => {
  canvasNodes.value = canvasNodes.value.filter((n) => n.id !== id)
  canvasConnections.value = canvasConnections.value.filter(
    (c) => c.sourceId !== id && c.targetId !== id
  )
}

const handleNodeDeleteWithConfirm = (node: CanvasNode): void => {
  const getNodeName = (n: CanvasNode): string => {
    if (n.name) return n.name
    switch (n.type) {
      case 'upload-image':
        return '上传图片'
      case 'generate-image':
        return '生成图片'
      case 'generated-image':
        return '生成结果'
      case 'text-annotation':
        return '文本注释'
      default:
        return '节点'
    }
  }
  
  const nodeName = getNodeName(node)
  
  showConfirmDialog(
    '删除节点',
    `确定要删除节点"${nodeName}"吗？`,
    () => {
      handleNodeDelete(node.id)
      toast({
        title: '删除成功',
        description: `节点"${nodeName}"已删除`
      })
    },
    'danger'
  )
}

const handleNodeOpenFile = async (node: CanvasNode): Promise<void> => {
  try {
    let absolutePath: string | undefined
    
    if (node.assetId) {
      const result = await assetsService.getFilePath(node.assetId)
      absolutePath = result.path
    } else if (node.filePath) {
      const isAbsolute = node.filePath.startsWith('/') || /^[A-Za-z]:/.test(node.filePath)
      if (isAbsolute) {
        absolutePath = node.filePath
      } else {
        const project = await assetsService.getCurrentProject()
        if (project.project) {
          absolutePath = `${project.project.path}/${node.filePath}`.replace(/\\/g, '/')
        }
      }
    }
    
    if (!absolutePath) {
      throw new Error('文件路径不存在')
    }
    
    await window.api.openFile(absolutePath)
  } catch (error: any) {
    console.error('打开文件失败:', error)
    toast({
      title: '打开文件失败',
      description: error.message || '未知错误',
      variant: 'destructive'
    })
  }
}

const handleNodeOpenFolder = async (node: CanvasNode): Promise<void> => {
  try {
    let absolutePath: string | undefined
    
    if (node.assetId) {
      const result = await assetsService.getFilePath(node.assetId)
      absolutePath = result.path
    } else if (node.filePath) {
      const isAbsolute = node.filePath.startsWith('/') || /^[A-Za-z]:/.test(node.filePath)
      if (isAbsolute) {
        absolutePath = node.filePath
      } else {
        const project = await assetsService.getCurrentProject()
        if (project.project) {
          absolutePath = `${project.project.path}/${node.filePath}`.replace(/\\/g, '/')
        }
      }
    }
    
    if (!absolutePath) {
      throw new Error('文件路径不存在')
    }
    
    const path = absolutePath.replace(/\\/g, '/')
    const lastSlashIndex = path.lastIndexOf('/')
    const dirPath = lastSlashIndex >= 0 ? path.substring(0, lastSlashIndex) : '.'
    
    await window.api.openDirectory(dirPath)
    
    toast({
      title: '打开目录成功',
      description: `已打开文件所在目录`
    })
  } catch (error: any) {
    console.error('打开目录失败:', error)
    toast({
      title: '打开目录失败',
      description: error.message || '未知错误',
      variant: 'destructive'
    })
  }
}

const handleNodesDelete = (ids: string[]): void => {
  canvasNodes.value = canvasNodes.value.filter((n) => !ids.includes(n.id))
  canvasConnections.value = canvasConnections.value.filter(
    (c) => !ids.includes(c.sourceId) && !ids.includes(c.targetId)
  )
}

const handleNodeGenerate = async (id: string): Promise<void> => {
  const node = canvasNodes.value.find((n) => n.id === id)
  if (!node || node.type !== 'generate-image') {
    return
  }

  if (!node.prompt || !node.prompt.trim()) {
    toast({
      title: '请输入提示词',
      description: '生成图片需要输入提示词',
      variant: 'destructive'
    })
    return
  }

  const referenceConnections = canvasConnections.value.filter(
    (c) => c.targetId === id && c.type === 'reference'
  )

  const imageInput: string[] = []
  for (const conn of referenceConnections) {
    const sourceNode = canvasNodes.value.find((n) => n.id === conn.sourceId)
    if (sourceNode?.assetId) {
      try {
        toast({
          title: '上传参考图片',
          description: '正在上传原图到服务器...'
        })
        const uploadResult = await imageGenerationService.uploadImage('', sourceNode.assetId)
        imageInput.push(uploadResult.file_url)
        toast({
          title: '参考图片上传成功',
          description: `已上传: ${uploadResult.file_name}`
        })
      } catch (error: any) {
        toast({
          title: '上传参考图片失败',
          description: error.response?.data?.detail || error.message || '未知错误',
          variant: 'destructive'
        })
        return
      }
    }
  }

  const generatingNode = canvasNodes.value.find((n) => n.id === id)
  if (generatingNode) {
    ;(generatingNode as any).isGenerating = true
  }

  const placeholderNodeId = generateNodeId()
  const placeholderNode: CanvasNode = {
    id: placeholderNodeId,
    type: 'generated-image',
    x: node.x + node.width + 60,
    y: node.y,
    width: 200,
    height: 200,
    name: '生成结果',
    genStatus: 'generating',
    sourceNodeId: id
  }
  canvasNodes.value.push(placeholderNode)

  const placeholderConnection: CanvasConnection = {
    id: `conn-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    sourceId: id,
    targetId: placeholderNodeId,
    type: 'default'
  }
  canvasConnections.value.push(placeholderConnection)

  try {
    const createResult = await imageGenerationService.createTask({
      prompt: node.prompt,
      model: node.genModel || 'nano-banana-2',
      aspect_ratio: node.aspectRatio || 'auto',
      resolution: node.resolution || '2k',
      output_format: node.outputFormat || 'png',
      image_input: imageInput
    })

    const taskId = createResult.task_id

    const placeholderNodeToUpdate = canvasNodes.value.find((n) => n.id === placeholderNodeId)
    if (placeholderNodeToUpdate) {
      placeholderNodeToUpdate.genTaskId = taskId
    }

    toast({
      title: '任务已创建',
      description: `任务ID: ${taskId}`
    })

    const maxDuration = 10 * 60 * 1000
    const startTime = Date.now()
    let pollCount = 0
    const pollInterval = 10000

    while (Date.now() - startTime < maxDuration) {
      await new Promise((resolve) => setTimeout(resolve, pollInterval))
      pollCount++

      const status = await imageGenerationService.getStatus(taskId)

      if (status.status === 'success' && status.result_urls.length > 0) {
        toast({
          title: '图片生成成功',
          description: `正在下载 ${status.result_urls.length} 张图片...`
        })

        const sourceGenNode = canvasNodes.value.find((n) => n.id === id)
        if (sourceGenNode) {
          ;(sourceGenNode as any).isGenerating = false
        }

        const firstPlaceholder = canvasNodes.value.find((n) => n.id === placeholderNodeId)
        const projectId = defaultCanvasProject.value.project_id || undefined
        
        for (let i = 0; i < status.result_urls.length; i++) {
          const resultUrl = status.result_urls[i]
          const downloadResult = await imageGenerationService.downloadImage(resultUrl, projectId)
          const previewUrl = await assetsService.getPreviewUrl(downloadResult.asset_id)

          if (i === 0 && firstPlaceholder) {
            firstPlaceholder.genStatus = 'success'
            firstPlaceholder.localImagePath = previewUrl
            firstPlaceholder.assetId = downloadResult.asset_id
            firstPlaceholder.filePath = downloadResult.file_path
          } else {
            const newResultNodeId = generateNodeId()
            const newResultNode: CanvasNode = {
              id: newResultNodeId,
              type: 'generated-image',
              x: node.x + node.width + 60 + i * 220,
              y: node.y + 220,
              width: 200,
              height: 200,
              name: `生成结果 ${i + 1}`,
              genStatus: 'success',
              sourceNodeId: id,
              localImagePath: previewUrl,
              assetId: downloadResult.asset_id,
              filePath: downloadResult.file_path
            }
            canvasNodes.value.push(newResultNode)

            const newConnection: CanvasConnection = {
              id: `conn-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              sourceId: id,
              targetId: newResultNodeId,
              type: 'default'
            }
            canvasConnections.value.push(newConnection)
          }
        }

        toast({
          title: '图片已保存',
          description: `已保存 ${status.result_urls.length} 张图片到资产库`
        })
        return
      }

      if (status.status === 'fail') {
        throw new Error(status.error_message || '生成失败')
      }

      if (pollCount % 10 === 0) {
        const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000)
        const statusText = status.status === 'waiting' ? '等待中' :
                          status.status === 'queuing' ? '排队中' :
                          status.status === 'generating' ? '生成中' : status.status
        toast({
          title: `任务${statusText}`,
          description: `已等待 ${elapsedSeconds} 秒`
        })
      }
    }

    throw new Error('生成超时（超过10分钟）')
  } catch (error: any) {
    console.error('生成图片失败:', error)

    const sourceGenNode = canvasNodes.value.find((n) => n.id === id)
    if (sourceGenNode) {
      ;(sourceGenNode as any).isGenerating = false
    }

    const failedPlaceholder = canvasNodes.value.find((n) => n.id === placeholderNodeId)
    if (failedPlaceholder) {
      failedPlaceholder.genStatus = 'failed'
      failedPlaceholder.genError = error.message || '未知错误'
    }

    toast({
      title: '生成失败',
      description: error.message || '未知错误',
      variant: 'destructive'
    })
  }
}

const handleNodeConvertToAsset = async (nodeId: string, assetId: number): Promise<void> => {
  const node = canvasNodes.value.find((n) => n.id === nodeId)
  if (!node) return

  try {
    const asset = await assetsService.getById(assetId)
    const previewUrl = await assetsService.getPreviewUrl(assetId)

    canvasNodes.value = canvasNodes.value.map((n) => {
      if (n.id === nodeId) {
        return {
          id: nodeId,
          type: 'asset' as const,
          x: n.x,
          y: n.y,
          width: n.width,
          height: n.height,
          assetId: asset.id,
          name: asset.name,
          category: asset.category,
          sub_category: asset.sub_category,
          filePath: asset.file_path,
          fileType: asset.file_type,
          localImagePath: previewUrl
        } as CanvasNode
      }
      return n
    })

    toast({
      title: '保存成功',
      description: '图片已保存到新位置，节点已转换为资产节点'
    })
  } catch (error: any) {
    console.error('转换节点失败:', error)
    toast({
      title: '转换失败',
      description: error.message || '未知错误',
      variant: 'destructive'
    })
  }
}

const handleClearCanvas = (): void => {
  showConfirmDialog(
    '清空画布',
    '确定要清空画布吗？所有节点将被删除。',
    () => {
      canvasNodes.value = []
      canvasConnections.value = []
      canvasViewport.value = { x: 0, y: 0, scale: 1 }
    },
    'danger'
  )
}

const checkPendingGeneratingNodes = async (): Promise<void> => {
  const generatingNodes = canvasNodes.value.filter(
    (n) => n.type === 'generated-image' && n.genStatus === 'generating' && n.genTaskId
  )

  if (generatingNodes.length === 0) return

  toast({
    title: '检查未完成的生成任务',
    description: `发现 ${generatingNodes.length} 个正在生成的节点，正在检查状态...`
  })

  for (const node of generatingNodes) {
    if (!node.genTaskId) continue

    try {
      const status = await imageGenerationService.getStatus(node.genTaskId)

      if (status.status === 'success' && status.result_urls.length > 0) {
        toast({
          title: '图片生成成功',
          description: `正在下载 ${status.result_urls.length} 张图片...`
        })

        const projectId = defaultCanvasProject.value.project_id || undefined

        for (let i = 0; i < status.result_urls.length; i++) {
          const resultUrl = status.result_urls[i]
          const downloadResult = await imageGenerationService.downloadImage(resultUrl, projectId)
          const previewUrl = await assetsService.getPreviewUrl(downloadResult.asset_id)

          if (i === 0) {
            node.genStatus = 'success'
            node.genTaskId = undefined
            node.localImagePath = previewUrl
            node.assetId = downloadResult.asset_id
            node.filePath = downloadResult.file_path
          } else {
            const newNodeId = `gen-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
            const newNode: CanvasNode = {
              id: newNodeId,
              type: 'generated-image',
              x: node.x + i * 220,
              y: node.y + 220,
              width: 200,
              height: 200,
              name: `生成结果 ${i + 1}`,
              genStatus: 'success',
              sourceNodeId: node.sourceNodeId,
              localImagePath: previewUrl,
              assetId: downloadResult.asset_id,
              filePath: downloadResult.file_path
            }
            canvasNodes.value.push(newNode)
          }
        }

        toast({
          title: '图片已保存',
          description: `已保存 ${status.result_urls.length} 张图片到资产库`
        })
      } else if (status.status === 'fail') {
        node.genStatus = 'failed'
        node.genTaskId = undefined
        node.genError = status.error_message || '生成失败'

        toast({
          title: '生成任务失败',
          description: status.error_message || '生成失败',
          variant: 'destructive'
        })
      } else {
        const statusText =
          status.status === 'waiting'
            ? '等待中'
            : status.status === 'queuing'
              ? '排队中'
              : status.status === 'generating'
                ? '生成中'
                : status.status

        toast({
          title: '任务仍在进行中',
          description: `节点 "${node.name}" 状态: ${statusText}，请稍后刷新查看`
        })
      }
    } catch (error: any) {
      console.error(`检查任务状态失败 (${node.genTaskId}):`, error)
      node.genStatus = 'failed'
      node.genTaskId = undefined
      node.genError = error.message || '检查状态失败'

      toast({
        title: '检查任务状态失败',
        description: error.message || '未知错误',
        variant: 'destructive'
      })
    }
  }
}

const loadProjects = async (): Promise<void> => {
  try {
    projects.value = await assetsService.getProjects()
  } catch (error) {
    console.error('加载项目列表失败:', error)
  }
}

const loadDefaultCanvasProject = async (): Promise<void> => {
  try {
    defaultCanvasProject.value = await canvasService.getDefaultProject()
  } catch (error) {
    console.error('加载默认画布项目失败:', error)
  }
}

const loadCanvasList = async (projectId?: number): Promise<void> => {
  const effectiveProjectId = projectId ?? defaultCanvasProject.value.project_id
  if (!effectiveProjectId) {
    console.warn('loadCanvasList: 没有 project_id，跳过加载')
    return
  }

  canvasListLoading.value = true
  try {
    canvasList.value = await canvasService.getAll(effectiveProjectId)
    console.log('loadCanvasList: 加载成功，画布数量:', canvasList.value.length)
  } catch (error) {
    console.error('加载画布列表失败:', error)
    canvasList.value = []
  } finally {
    canvasListLoading.value = false
  }
}

const autoSaveCanvas = async (): Promise<boolean> => {
  if (!currentCanvasId.value || !currentCanvasName.value) {
    return false
  }
  
  if (canvasNodes.value.length === 0 && canvasConnections.value.length === 0) {
    return false
  }

  try {
    await canvasService.update(currentCanvasId.value, {
      name: currentCanvasName.value,
      nodes: canvasNodes.value,
      connections: canvasConnections.value,
      viewport: canvasViewport.value
    })
    console.log('自动保存画布成功:', currentCanvasName.value)
    return true
  } catch (error) {
    console.error('自动保存画布失败:', error)
    return false
  }
}

const handleLoadCanvas = async (canvasIdOrAction: unknown): Promise<void> => {
  if (!canvasIdOrAction) return

  const actionStr = String(canvasIdOrAction)
  if (actionStr === '__new__') {
    await autoSaveCanvas()
    handleNewCanvas()
    return
  }

  const canvasId = parseInt(actionStr, 10)
  if (isNaN(canvasId)) return

  if (canvasId !== currentCanvasId.value) {
    await autoSaveCanvas()
  }

  try {
    const canvas = await canvasService.get(canvasId)
    canvasNodes.value = canvas.nodes || []
    canvasConnections.value = canvas.connections || []
    canvasViewport.value = canvas.viewport || { x: 0, y: 0, scale: 1 }
    currentCanvasName.value = canvas.name
    currentCanvasId.value = canvas.id

    await checkPendingGeneratingNodes()
  } catch (error) {
    console.error('加载画布失败:', error)
    toast({ title: '加载画布失败', variant: 'destructive' })
  }
}

const handleNewCanvas = (): void => {
  if (projects.value.length === 0) {
    toast({
      title: '请先创建一个项目',
      description: '需要先创建资产项目才能创建画布',
      variant: 'destructive'
    })
    return
  }
  newCanvasDialogOpen.value = true
}

const handleNewCanvasConfirm = async (projectId: number, name: string): Promise<void> => {
  try {
    await canvasService.setDefaultProject(projectId)
    defaultCanvasProject.value = {
      project_id: projectId,
      project_name: projects.value.find((p) => p.id === projectId)?.name || ''
    }

    const data = {
      name: name,
      nodes: [],
      connections: [],
      viewport: { x: 0, y: 0, scale: 1 },
      project_id: projectId
    }

    const result = await canvasService.save(data)
    
    canvasNodes.value = []
    canvasConnections.value = []
    canvasViewport.value = { x: 0, y: 0, scale: 1 }
    currentCanvasId.value = result.id
    currentCanvasName.value = name
    
    await loadCanvasList(projectId)
    toast({
      title: '画布创建成功',
      description: `画布"${name}"已创建`
    })
  } catch (error) {
    console.error('创建画布失败:', error)
    toast({
      title: '创建画布失败',
      variant: 'destructive'
    })
  }
}

const handleNodeSelect = (id: string | null): void => {
  console.log('选中节点:', id)
}

const handleViewportChange = (viewport: { x: number; y: number; scale: number }): void => {
  canvasViewport.value = viewport
}

watch(
  () => defaultCanvasProject.value.project_id,
  (projectId) => {
    if (projectId) {
      loadCanvasList()
    }
  }
)

watch(currentSegment, async (newSegment, oldSegment) => {
  if (oldSegment === '画布' && newSegment !== '画布') {
    await autoSaveCanvas()
  }
})

onBeforeRouteLeave(async () => {
  if (currentSegment.value === '画布') {
    await autoSaveCanvas()
  }
})

const handleBeforeUnload = async (): Promise<void> => {
  await autoSaveCanvas()
}

const isSavingOnClose = ref(false)

const handlePrepareClose = async (): Promise<void> => {
  if (currentSegment.value === '画布' && currentCanvasId.value) {
    isSavingOnClose.value = true
    await autoSaveCanvas()
    isSavingOnClose.value = false
  }
  window.api.allowClose()
}

onMounted(async () => {
  window.addEventListener('beforeunload', handleBeforeUnload)
  window.api.onPrepareClose(handlePrepareClose)
  fetchWorkflows()
  fetchOrders()
  await loadProjects()
  await loadDefaultCanvasProject()
  
  if (savedCanvasState.value.projectId) {
    await loadCanvasList(savedCanvasState.value.projectId)
  }
  
  if (savedCanvasState.value.canvasId && canvasNodes.value.length > 0) {
    await checkPendingGeneratingNodes()
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
})
</script>

<template>
  <div class="h-full flex flex-col overflow-hidden">
    <Transition name="fade-slide" mode="out-in">
      <div v-if="currentSegment !== '画布'" key="workflow" class="h-full flex flex-col">
        <div class="space-y-6 p-6">
          <div class="flex flex-col items-center gap-4">
            <h1 class="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">工作流</h1>
            <SegmentedControl v-model="currentSegment" :options="SEGMENT_OPTIONS" />
          </div>

          <div v-if="currentSegment === '工作流管理'">
            <WorkflowList
              :workflows="workflows"
              :loading="loading.workflows"
              @create="handleCreateWorkflow"
              @edit="handleEditWorkflow"
              @delete="handleDeleteWorkflow"
            />
          </div>

          <Card
            v-else
            class="backdrop-blur-xl bg-white/70 dark:bg-zinc-900/70 border-zinc-200/50 dark:border-zinc-800/50 rounded-3xl shadow-xl shadow-black/5"
          >
            <CardContent class="p-6">
              <div
                class="flex items-center justify-between mb-6 pb-4 border-b border-zinc-200/50 dark:border-zinc-800/50"
              >
                <div class="flex items-center gap-3">
                  <label class="text-sm font-medium text-zinc-600 dark:text-zinc-400"
                    >选择订单:</label
                  >
                  <Select v-model="selectedOrderIdString" @update:model-value="handleOrderChange">
                    <SelectTrigger class="w-[200px] rounded-xl">
                      <SelectValue placeholder="请选择订单" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem
                        v-for="order in orders"
                        :key="order.id"
                        :value="order.id.toString()"
                      >
                        {{ order.company_name }}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  v-if="hasWorkflow"
                  class="rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 gap-2"
                  @click="handleAddProduct"
                >
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path
                      d="M8 3V13M3 8H13"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                    />
                  </svg>
                  添加产品
                </Button>
              </div>

              <div
                v-if="loading.orderWorkflow"
                class="flex flex-col items-center justify-center py-16 gap-4"
              >
                <div
                  class="w-8 h-8 border-2 border-zinc-200 dark:border-zinc-700 border-t-zinc-900 dark:border-t-white rounded-full animate-spin"
                ></div>
                <span class="text-zinc-500 dark:text-zinc-400">加载中...</span>
              </div>

              <div
                v-else-if="!selectedOrderId"
                class="text-center py-16 text-zinc-500 dark:text-zinc-400"
              >
                请选择一个订单查看工作流
              </div>

              <template v-else-if="hasWorkflow && orderWorkflow">
                <Timeline
                  :steps="orderWorkflow.workflow.steps"
                  :products="allProducts"
                  @product-click="handleProductClick"
                  @product-move-prev="handleProductMovePrev"
                  @product-move-next="handleProductMoveNext"
                />
              </template>

              <div v-else class="py-8">
                <WorkflowTemplateSelector
                  :workflows="workflows"
                  :loading="loading.workflows"
                  @apply="handleApplyTemplate"
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <div v-else key="canvas" class="h-full flex flex-col">
        <div
          class="flex items-center justify-between px-6 py-4 border-b border-zinc-200 dark:border-zinc-800"
        >
          <div class="flex items-center gap-4">
            <h1 class="text-xl font-semibold text-zinc-900 dark:text-zinc-100">画布</h1>
            <Select @update:model-value="handleLoadCanvas">
              <SelectTrigger class="w-[180px] rounded-xl">
                <SelectValue :placeholder="currentCanvasName || '选择画布'" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__new__">+ 新建画布</SelectItem>
                <SelectItem
                  v-for="canvas in canvasList"
                  :key="canvas.id"
                  :value="canvas.id.toString()"
                >
                  {{ canvas.name }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <SegmentedControl v-model="currentSegment" :options="SEGMENT_OPTIONS" />
          <div class="flex items-center gap-2">
            <span
              v-if="defaultCanvasProject.project_name"
              class="text-xs text-zinc-400 dark:text-zinc-500"
            >
              ({{ defaultCanvasProject.project_name }})
            </span>
            <Button variant="outline" size="sm" class="rounded-xl gap-2" @click="assetDrawerOpen = !assetDrawerOpen">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <rect
                  x="2"
                  y="2"
                  width="12"
                  height="12"
                  rx="2"
                  stroke="currentColor"
                  stroke-width="1.5"
                />
                <path d="M6 2V14M10 2V14" stroke="currentColor" stroke-width="1.5" />
              </svg>
              资产库
            </Button>
            <span class="text-sm text-zinc-500 dark:text-zinc-400">
              {{ canvasNodes.length }} 个节点
            </span>
            <Button
              v-if="canvasNodes.length > 0"
              variant="outline"
              size="sm"
              class="rounded-xl"
              @click="handleClearCanvas"
            >
              清空画布
            </Button>
          </div>
        </div>

        <div class="flex-1 relative overflow-hidden">
          <Transition name="drawer">
            <div v-if="assetDrawerOpen" class="absolute top-0 left-0 h-full z-10 shadow-2xl">
              <CanvasSidebar />
            </div>
          </Transition>
          <InfiniteCanvas
            :nodes="canvasNodes"
            :connections="canvasConnections"
            :initial-viewport="canvasViewport"
            @node-move="handleNodeMove"
            @node-resize="handleNodeResize"
            @node-delete="handleNodeDelete"
            @nodes-delete="handleNodesDelete"
            @node-update="handleNodeUpdate"
            @node-create="handleNodeCreate"
            @node-select="handleNodeSelect"
            @connection-create="handleConnectionCreate"
            @connection-delete="handleConnectionDelete"
            @asset-drop="handleAssetDrop"
            @node-generate="handleNodeGenerate"
            @viewport-change="handleViewportChange"
            @node-convert-to-asset="handleNodeConvertToAsset"
            @node-delete-with-confirm="handleNodeDeleteWithConfirm"
            @node-open-file="handleNodeOpenFile"
            @node-open-folder="handleNodeOpenFolder"
          />
        </div>
      </div>
    </Transition>

    <WorkflowEditDialog
      v-model:open="editDialogOpen"
      :workflow="editingWorkflow"
      @save="handleSaveWorkflow"
    />

    <InputDialog
      v-model:open="inputDialogOpen"
      :title="inputDialogTitle"
      :label="inputDialogLabel"
      :placeholder="inputDialogPlaceholder"
      :default-value="inputDialogDefault"
      @confirm="handleInputDialogConfirm"
    />

    <ConfirmDialog
      v-model:open="confirmDialogOpen"
      :title="confirmDialogTitle"
      :message="confirmDialogMessage"
      :variant="confirmDialogVariant"
      @confirm="handleConfirmDialogConfirm"
    />

    <NewCanvasDialog
      v-model:open="newCanvasDialogOpen"
      :projects="projects"
      :default-project-id="defaultCanvasProject.project_id"
      @confirm="handleNewCanvasConfirm"
    />

    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="isSavingOnClose"
          class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm"
        >
          <div
            class="flex flex-col items-center gap-4 px-8 py-6 bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl"
          >
            <div
              class="w-10 h-10 border-3 border-zinc-200 dark:border-zinc-700 border-t-zinc-900 dark:border-t-white rounded-full animate-spin"
            ></div>
            <span class="text-lg font-medium text-zinc-900 dark:text-zinc-100">正在保存数据...</span>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.fade-slide-enter-to,
.fade-slide-leave-from {
  opacity: 1;
  transform: translateX(0);
}

.drawer-enter-active,
.drawer-leave-active {
  transition: all 0.3s ease;
}

.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
  transform: translateX(-100%);
}

.drawer-enter-to,
.drawer-leave-from {
  opacity: 1;
  transform: translateX(0);
}
</style>
