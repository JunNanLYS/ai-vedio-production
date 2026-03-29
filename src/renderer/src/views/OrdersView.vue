<script setup lang="ts">
import type { Order, CreateOrderRequest } from '@/types'
import { ref, onMounted } from 'vue'
import { ordersService } from '@/services/orders'
import OrderTable from '@/components/orders/OrderTable.vue'
import OrderDialog from '@/components/orders/OrderDialog.vue'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog'

const orders = ref<Order[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const dialogOpen = ref(false)
const editingOrder = ref<Order | null>(null)

const deleteDialogOpen = ref(false)
const deletingOrderId = ref<number | null>(null)

const loadOrders = async (): Promise<void> => {
  loading.value = true
  error.value = null

  try {
    orders.value = await ordersService.getAll()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载订单失败'
    console.error('加载订单失败:', err)
  } finally {
    loading.value = false
  }
}

const handleCreate = (): void => {
  editingOrder.value = null
  dialogOpen.value = true
}

const handleEdit = (order: Order): void => {
  editingOrder.value = order
  dialogOpen.value = true
}

const handleSubmit = async (data: CreateOrderRequest): Promise<void> => {
  try {
    if (editingOrder.value) {
      await ordersService.update(editingOrder.value.id, data)
    } else {
      await ordersService.create(data)
    }

    dialogOpen.value = false
    editingOrder.value = null

    await loadOrders()
  } catch (err) {
    console.error('保存订单失败:', err)
    error.value = err instanceof Error ? err.message : '保存订单失败'
  }
}

const handleDelete = (id: number): void => {
  deletingOrderId.value = id
  deleteDialogOpen.value = true
}

const confirmDelete = async (): Promise<void> => {
  if (!deletingOrderId.value) return

  try {
    await ordersService.delete(deletingOrderId.value)
    deleteDialogOpen.value = false
    deletingOrderId.value = null

    await loadOrders()
  } catch (err) {
    console.error('删除订单失败:', err)
    error.value = err instanceof Error ? err.message : '删除订单失败'
  }
}

onMounted(() => {
  loadOrders()
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">订单管理</h1>
        <p class="text-zinc-500 dark:text-zinc-400 mt-1">管理所有订单信息</p>
      </div>
      <Button
        class="rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 gap-2"
        @click="handleCreate"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M8 3V13M3 8H13" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
        </svg>
        新建订单
      </Button>
    </div>

    <div
      v-if="error"
      class="flex items-center gap-3 px-4 py-3 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 rounded-xl text-rose-600 dark:text-rose-400"
    >
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="8" stroke="currentColor" stroke-width="1.5" />
        <path
          d="M10 6V10M10 13V13.5"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
        />
      </svg>
      <span>{{ error }}</span>
    </div>

    <OrderTable :orders="orders" :loading="loading" @edit="handleEdit" @delete="handleDelete" />

    <OrderDialog v-model:open="dialogOpen" :order="editingOrder" @submit="handleSubmit" />

    <Dialog v-model:open="deleteDialogOpen">
      <DialogContent class="max-w-md rounded-2xl">
        <DialogHeader>
          <DialogTitle>确认删除</DialogTitle>
          <DialogDescription>确定要删除这个订单吗？此操作无法撤销。</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="deleteDialogOpen = false">取消</Button>
          <Button variant="destructive" @click="confirmDelete">删除</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
