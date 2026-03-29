<script setup lang="ts">
import type { Order } from '@/types'
import { Button } from '@/components/ui/button'

interface Props {
  orders: Order[]
  loading?: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  edit: [order: Order]
  delete: [id: number]
}>()

// 获取进度条颜色
const getProgressColor = (progress: number): string => {
  if (progress < 30) return 'bg-red-400'
  if (progress < 70) return 'bg-yellow-400'
  return 'bg-green-400'
}

// 获取状态标签样式
const getStatusClass = (status: Order['status']): string => {
  const classes: Record<Order['status'], string> = {
    pending: 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400',
    in_progress: 'bg-sky-100 text-sky-600 dark:bg-sky-900/30 dark:text-sky-400',
    completed: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400',
    cancelled: 'bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400'
  }
  return classes[status]
}

// 获取状态文本
const getStatusText = (status: Order['status']): string => {
  const texts: Record<Order['status'], string> = {
    pending: '待处理',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return texts[status]
}

// 格式化日期
const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 格式化金额
const formatMoney = (amount: number): string => {
  return `¥${amount.toFixed(2)}`
}
</script>

<template>
  <div class="order-table">
    <!-- 加载状态 -->
    <div v-if="loading" class="order-table__loading">
      <div class="order-table__loading-spinner"></div>
      <span>加载中...</span>
    </div>

    <!-- 空状态 -->
    <div v-else-if="orders.length === 0" class="order-table__empty">
      <div class="order-table__empty-icon">
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
          <rect
            x="8"
            y="8"
            width="32"
            height="32"
            rx="8"
            stroke="currentColor"
            stroke-width="2"
            stroke-dasharray="4 2"
          />
          <path
            d="M16 24H32M24 16V32"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
          />
        </svg>
      </div>
      <span class="order-table__empty-text">暂无订单</span>
      <span class="order-table__empty-hint">点击右上角按钮创建第一个订单</span>
    </div>

    <!-- 表格 -->
    <div v-else class="order-table__container">
      <table class="order-table__table">
        <thead>
          <tr>
            <th>公司名</th>
            <th>完成进度</th>
            <th>视频数量</th>
            <th>单价</th>
            <th>收入</th>
            <th>利润</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="order in orders" :key="order.id">
            <td class="order-table__company">{{ order.company_name }}</td>
            <td>
              <div class="order-table__progress">
                <div class="order-table__progress-bar">
                  <div
                    class="order-table__progress-fill"
                    :class="getProgressColor(order.progress)"
                    :style="{ width: `${order.progress}%` }"
                  ></div>
                </div>
                <span class="order-table__progress-text">{{ order.progress }}%</span>
              </div>
            </td>
            <td>{{ order.video_count }}</td>
            <td>{{ formatMoney(order.unit_price) }}</td>
            <td>{{ formatMoney(order.income) }}</td>
            <td>{{ formatMoney(order.profit) }}</td>
            <td>
              <span
                :class="[
                  'inline-flex items-center justify-center px-2.5 py-1 rounded-full text-xs font-medium',
                  getStatusClass(order.status)
                ]"
              >
                {{ getStatusText(order.status) }}
              </span>
            </td>
            <td class="order-table__date">{{ formatDate(order.created_at) }}</td>
            <td>
              <div class="order-table__actions">
                <Button
                  variant="ghost"
                  size="icon-sm"
                  class="order-table__action-btn"
                  @click="emit('edit', order)"
                >
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path
                      d="M11.5 2.5L13.5 4.5M2 14H4L12.5 5.5C12.8 5.2 12.8 4.8 12.5 4.5L11.5 3.5C11.2 3.2 10.8 3.2 10.5 3.5L2 12V14Z"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </Button>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  class="order-table__action-btn order-table__action-btn--danger"
                  @click="emit('delete', order.id)"
                >
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path
                      d="M3 4H13M5.5 4V3C5.5 2.4 6 2 6.5 2H9.5C10 2 10.5 2.4 10.5 3V4M6 7V11M10 7V11M4 4L4.5 12.5C4.5 13.3 5.2 14 6 14H10C10.8 14 11.5 13.3 11.5 12.5L12 4"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </Button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.order-table {
  width: 100%;
}

.order-table__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 16px;
  color: rgba(0, 0, 0, 0.4);
}

.order-table__loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.order-table__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 12px;
}

.order-table__empty-icon {
  color: rgba(0, 0, 0, 0.15);
}

.order-table__empty-text {
  font-size: 16px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.5);
}

.order-table__empty-hint {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.35);
}

.order-table__container {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 24px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.order-table__table {
  width: 100%;
  border-collapse: collapse;
}

.order-table__table thead {
  background: rgba(0, 0, 0, 0.02);
}

.order-table__table th {
  padding: 16px 20px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.order-table__table td {
  padding: 16px 20px;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.8);
  border-bottom: 1px solid rgba(0, 0, 0, 0.03);
}

.order-table__table tbody tr {
  transition: background 0.2s ease;
}

.order-table__table tbody tr:hover {
  background: rgba(102, 126, 234, 0.04);
}

.order-table__company {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.9);
}

.order-table__progress {
  display: flex;
  align-items: center;
  gap: 12px;
}

.order-table__progress-bar {
  flex: 1;
  height: 6px;
  background: rgba(0, 0, 0, 0.06);
  border-radius: 3px;
  overflow: hidden;
  min-width: 80px;
}

.order-table__progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.order-table__progress-text {
  font-size: 13px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.6);
  min-width: 40px;
}

.order-table__date {
  font-size: 13px;
  color: rgba(0, 0, 0, 0.5);
}

.order-table__actions {
  display: flex;
  gap: 4px;
}

.order-table__action-btn {
  opacity: 0.4;
  transition: opacity 0.2s ease;
}

.order-table__action-btn:hover {
  opacity: 1;
}

.order-table__action-btn--danger:hover {
  color: #ef4444;
}

/* 暗色主题 */
:global(.dark) .order-table__loading,
:global(.dark) .order-table__empty-icon {
  color: rgba(255, 255, 255, 0.4);
}

:global(.dark) .order-table__empty-text {
  color: rgba(255, 255, 255, 0.5);
}

:global(.dark) .order-table__empty-hint {
  color: rgba(255, 255, 255, 0.35);
}

:global(.dark) .order-table__container {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.08);
}

:global(.dark) .order-table__table thead {
  background: rgba(255, 255, 255, 0.02);
}

:global(.dark) .order-table__table th {
  color: rgba(255, 255, 255, 0.5);
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

:global(.dark) .order-table__table td {
  color: rgba(255, 255, 255, 0.8);
  border-bottom-color: rgba(255, 255, 255, 0.05);
}

:global(.dark) .order-table__table tbody tr:hover {
  background: rgba(102, 126, 234, 0.08);
}

:global(.dark) .order-table__company {
  color: rgba(255, 255, 255, 0.95);
}

:global(.dark) .order-table__progress-bar {
  background: rgba(255, 255, 255, 0.1);
}

:global(.dark) .order-table__progress-text {
  color: rgba(255, 255, 255, 0.6);
}

:global(.dark) .order-table__date {
  color: rgba(255, 255, 255, 0.5);
}

/* 响应式 */
@media (max-width: 1200px) {
  .order-table__container {
    overflow-x: auto;
  }

  .order-table__table {
    min-width: 900px;
  }
}
</style>
