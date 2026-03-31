<script setup lang="ts">
import type { Order, CreateOrderRequest, Workflow } from '@/types'
import { ref, computed, watch } from 'vue'
import { workflowsService } from '@/services/workflows'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'

type OrderStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled'

const STATUS_OPTIONS: { value: OrderStatus; label: string }[] = [
  { value: 'pending', label: '待处理' },
  { value: 'in_progress', label: '进行中' },
  { value: 'completed', label: '已完成' },
  { value: 'cancelled', label: '已取消' }
]

interface Props {
  open: boolean
  order?: Order | null
}

const props = withDefaults(defineProps<Props>(), {
  order: null
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  submit: [data: CreateOrderRequest & { status?: OrderStatus }]
}>()

const workflows = ref<Workflow[]>([])
const formData = ref<{
  company_name: string
  video_count: number
  unit_price: number
  income?: number
  profit?: number
  workflow_id?: number
  status: OrderStatus
}>({
  company_name: '',
  video_count: 1,
  unit_price: 0,
  income: undefined,
  profit: undefined,
  workflow_id: undefined,
  status: 'pending'
})

const errors = ref<Record<string, string>>({})

const isEditMode = computed(() => !!props.order)

const dialogTitle = computed(() => (isEditMode.value ? '编辑订单' : '新建订单'))

const fetchWorkflows = async () => {
  try {
    workflows.value = await workflowsService.getAll()
  } catch (error) {
    console.error('获取工作流列表失败:', error)
  }
}

watch(
  () => props.order,
  (newOrder) => {
    if (newOrder) {
      formData.value = {
        company_name: newOrder.company_name,
        video_count: newOrder.video_count,
        unit_price: newOrder.unit_price,
        income: newOrder.income,
        profit: newOrder.profit,
        workflow_id: undefined,
        status: newOrder.status
      }
    } else {
      resetForm()
    }
  },
  { immediate: true }
)

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen && !isEditMode.value) {
      fetchWorkflows()
    }
  }
)

const resetForm = (): void => {
  formData.value = {
    company_name: '',
    video_count: 1,
    unit_price: 0,
    income: undefined,
    profit: undefined,
    workflow_id: undefined,
    status: 'pending'
  }
  errors.value = {}
}

const validateForm = (): boolean => {
  errors.value = {}

  if (!formData.value.company_name.trim()) {
    errors.value.company_name = '请输入公司名'
  }

  if (formData.value.video_count < 1) {
    errors.value.video_count = '视频数量必须大于0'
  }

  if (formData.value.unit_price < 0) {
    errors.value.unit_price = '单价不能为负数'
  }

  return Object.keys(errors.value).length === 0
}

const handleSubmit = (): void => {
  if (!validateForm()) return

  emit('submit', {
    company_name: formData.value.company_name.trim(),
    video_count: formData.value.video_count,
    unit_price: formData.value.unit_price,
    income: formData.value.income,
    profit: formData.value.profit,
    workflow_id: formData.value.workflow_id,
    status: formData.value.status
  })
}

const handleClose = (): void => {
  emit('update:open', false)
  setTimeout(resetForm, 200)
}

const selectedWorkflowIdString = computed({
  get: () => formData.value.workflow_id?.toString() ?? '',
  set: (value: string) => {
    formData.value.workflow_id = value ? parseInt(value, 10) : undefined
  }
})
</script>

<template>
  <Dialog :open="open" @update:open="handleClose">
    <DialogContent class="order-dialog">
      <DialogHeader>
        <DialogTitle>{{ dialogTitle }}</DialogTitle>
        <DialogDescription>
          {{ isEditMode ? '修改订单信息' : '填写订单信息以创建新订单' }}
        </DialogDescription>
      </DialogHeader>

      <form class="order-dialog__form" @submit.prevent="handleSubmit">
        <!-- 公司名 -->
        <div class="order-dialog__field">
          <label class="order-dialog__label">
            公司名 <span class="order-dialog__required">*</span>
          </label>
          <Input
            v-model="formData.company_name"
            placeholder="请输入公司名"
            :class="{ 'order-dialog__input--error': errors.company_name }"
          />
          <span v-if="errors.company_name" class="order-dialog__error">
            {{ errors.company_name }}
          </span>
        </div>

        <!-- 工作流选择（仅新建时显示） -->
        <div v-if="!isEditMode" class="order-dialog__field">
          <label class="order-dialog__label">关联工作流（可选）</label>
          <Select v-model="selectedWorkflowIdString">
            <SelectTrigger class="rounded-xl">
              <SelectValue placeholder="选择工作流模板" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem
                v-for="workflow in workflows"
                :key="workflow.id"
                :value="workflow.id.toString()"
              >
                {{ workflow.name }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <!-- 状态选择（仅编辑时显示） -->
        <div v-if="isEditMode" class="order-dialog__field">
          <label class="order-dialog__label">订单状态</label>
          <Select v-model="formData.status">
            <SelectTrigger class="rounded-xl">
              <SelectValue placeholder="选择状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem
                v-for="option in STATUS_OPTIONS"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <!-- 视频数量 -->
        <div class="order-dialog__field">
          <label class="order-dialog__label">视频数量</label>
          <Input
            v-model.number="formData.video_count"
            type="number"
            min="1"
            placeholder="请输入视频数量"
            :class="{ 'order-dialog__input--error': errors.video_count }"
          />
          <span v-if="errors.video_count" class="order-dialog__error">
            {{ errors.video_count }}
          </span>
        </div>

        <!-- 单价 -->
        <div class="order-dialog__field">
          <label class="order-dialog__label">单价（元）</label>
          <Input
            v-model.number="formData.unit_price"
            type="number"
            min="0"
            step="0.01"
            placeholder="请输入单价"
            :class="{ 'order-dialog__input--error': errors.unit_price }"
          />
          <span v-if="errors.unit_price" class="order-dialog__error">
            {{ errors.unit_price }}
          </span>
        </div>

        <!-- 收入 -->
        <div class="order-dialog__field">
          <label class="order-dialog__label">收入（元，可选）</label>
          <Input
            v-model.number="formData.income"
            type="number"
            min="0"
            step="0.01"
            placeholder="请输入收入"
          />
        </div>

        <!-- 利润 -->
        <div class="order-dialog__field">
          <label class="order-dialog__label">利润（元，可选）</label>
          <Input
            v-model.number="formData.profit"
            type="number"
            step="0.01"
            placeholder="请输入利润"
          />
        </div>
      </form>

      <DialogFooter>
        <Button type="button" variant="outline" @click="handleClose"> 取消 </Button>
        <Button type="submit" @click="handleSubmit">
          {{ isEditMode ? '保存' : '创建' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<style scoped>
.order-dialog {
  max-width: 480px;
  border-radius: 16px;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.order-dialog__form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin: 20px 0;
}

.order-dialog__field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.order-dialog__label {
  font-size: 14px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.7);
}

.order-dialog__required {
  color: #ef4444;
  margin-left: 2px;
}

.order-dialog__input--error {
  border-color: #ef4444;
}

.order-dialog__error {
  font-size: 12px;
  color: #ef4444;
}

/* 暗色主题 */
:global(.dark) .order-dialog__label {
  color: rgba(255, 255, 255, 0.7);
}
</style>
