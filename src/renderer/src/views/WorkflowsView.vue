<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { workflowsService } from '@/services/workflows'
import { productsService } from '@/services/products'
import { ordersService } from '@/services/orders'
import type { Workflow, Order, Product, OrderWorkflowResponse } from '@/types'
import SegmentedControl from '@/components/workflows/SegmentedControl.vue'
import WorkflowList from '@/components/workflows/WorkflowList.vue'
import WorkflowEditDialog from '@/components/workflows/WorkflowEditDialog.vue'
import WorkflowTemplateSelector from '@/components/workflows/WorkflowTemplateSelector.vue'
import Timeline from '@/components/workflows/Timeline.vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { InputDialog, ConfirmDialog } from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'

const SEGMENT_OPTIONS = ['工作流管理', '订单工作流']
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

const fetchWorkflows = async () => {
  loading.value.workflows = true
  try {
    workflows.value = await workflowsService.getAll()
  } catch (error) {
    console.error('获取工作流列表失败:', error)
  } finally {
    loading.value.workflows = false
  }
}

const fetchOrders = async () => {
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

const fetchOrderWorkflow = async () => {
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
) => {
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
) => {
  confirmDialogTitle.value = title
  confirmDialogMessage.value = message
  confirmDialogVariant.value = variant
  confirmDialogCallback.value = callback
  confirmDialogOpen.value = true
}

const handleInputDialogConfirm = (value: string) => {
  if (inputDialogCallback.value) {
    inputDialogCallback.value(value)
    inputDialogCallback.value = null
  }
}

const handleConfirmDialogConfirm = () => {
  if (confirmDialogCallback.value) {
    confirmDialogCallback.value()
    confirmDialogCallback.value = null
  }
}

const handleCreateWorkflow = async () => {
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

const handleEditWorkflow = (workflow: Workflow) => {
  editingWorkflow.value = workflow
  editDialogOpen.value = true
}

const handleSaveWorkflow = async (id: number, data: { name: string; steps: string[] }) => {
  try {
    await workflowsService.update(id, data)
    await fetchWorkflows()
  } catch (error) {
    console.error('更新工作流失败:', error)
  }
}

const handleDeleteWorkflow = async (id: number) => {
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

const handleAddProduct = async () => {
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

const handleProductClick = (product: Product) => {
  console.log('查看产品详情:', product)
}

const updateProductStep = (productId: number, newStep: number, newStatus: string) => {
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

const handleProductMovePrev = async (product: Product) => {
  try {
    const result = await productsService.move(product.id, 'prev')
    updateProductStep(product.id, result.current_step, result.status)
  } catch (error) {
    console.error('移动产品失败:', error)
    alert('移动产品失败')
  }
}

const handleProductMoveNext = async (product: Product) => {
  try {
    const result = await productsService.move(product.id, 'next')
    updateProductStep(product.id, result.current_step, result.status)
  } catch (error) {
    console.error('移动产品失败:', error)
    alert('移动产品失败')
  }
}

const handleOrderChange = () => {
  fetchOrderWorkflow()
}

const handleApplyTemplate = async (workflowId: number) => {
  if (!selectedOrderId.value) return

  try {
    await workflowsService.applyToOrder(selectedOrderId.value, workflowId)
    await fetchOrderWorkflow()
  } catch (error) {
    console.error('应用模板失败:', error)
    alert('应用模板失败')
  }
}

onMounted(() => {
  fetchWorkflows()
  fetchOrders()
})
</script>

<template>
  <div class="space-y-6">
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
        <div class="flex items-center justify-between mb-6 pb-4 border-b border-zinc-200/50 dark:border-zinc-800/50">
          <div class="flex items-center gap-3">
            <label class="text-sm font-medium text-zinc-600 dark:text-zinc-400">选择订单:</label>
            <Select v-model="selectedOrderIdString" @update:model-value="handleOrderChange">
              <SelectTrigger class="w-[200px] rounded-xl">
                <SelectValue placeholder="请选择订单" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem v-for="order in orders" :key="order.id" :value="order.id.toString()">
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

        <div v-if="loading.orderWorkflow" class="flex flex-col items-center justify-center py-16 gap-4">
          <div
            class="w-8 h-8 border-2 border-zinc-200 dark:border-zinc-700 border-t-zinc-900 dark:border-t-white rounded-full animate-spin"
          ></div>
          <span class="text-zinc-500 dark:text-zinc-400">加载中...</span>
        </div>

        <div v-else-if="!selectedOrderId" class="text-center py-16 text-zinc-500 dark:text-zinc-400">
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
  </div>
</template>
