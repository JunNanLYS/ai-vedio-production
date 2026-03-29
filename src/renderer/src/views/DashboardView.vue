<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { TrendingUp, TrendingDown, Loader2 } from 'lucide-vue-next'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { dashboardService } from '@/services/dashboard'
import { ordersService } from '@/services/orders'
import type { DashboardStats, Order } from '@/types'

// 数据状态
const stats = ref<DashboardStats | null>(null)
const recentOrders = ref<Order[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

// 获取数据
const fetchData = async () => {
  try {
    loading.value = true
    error.value = null
    const [statsData, ordersData] = await Promise.all([
      dashboardService.getStats(),
      ordersService.getRecent()
    ])
    stats.value = statsData
    recentOrders.value = ordersData
  } catch (e) {
    error.value = '加载数据失败，请稍后重试'
    console.error('Failed to fetch dashboard data:', e)
  } finally {
    loading.value = false
  }
}

// 格式化金额
const formatCurrency = (amount: number) => {
  return `¥${amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

// 获取趋势图标
const getTrendIcon = (trend: number) => {
  return trend >= 0 ? TrendingUp : TrendingDown
}

// 获取趋势颜色
const getTrendColor = (trend: number) => {
  return trend >= 0 ? 'text-emerald-500' : 'text-rose-500'
}

// 获取进度条颜色
const getProgressColor = (progress: number) => {
  if (progress < 30) return 'bg-amber-400'
  if (progress < 70) return 'bg-sky-400'
  return 'bg-emerald-400'
}

// 状态标签配置
const statusConfig = computed(() => ({
  pending: {
    label: '待处理',
    class: 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400'
  },
  in_progress: {
    label: '进行中',
    class: 'bg-sky-100 text-sky-600 dark:bg-sky-900/30 dark:text-sky-400'
  },
  completed: {
    label: '已完成',
    class: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400'
  },
  cancelled: {
    label: '已取消',
    class: 'bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400'
  }
}))

// 获取状态配置
const getStatusConfig = (status: Order['status']) => {
  return statusConfig.value[status] || statusConfig.value.pending
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div
      v-motion
      :initial="{ opacity: 0, y: -20 }"
      :enter="{ opacity: 1, y: 0, transition: { type: 'spring', stiffness: 200, damping: 20 } }"
    >
      <h1 class="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">仪表盘</h1>
      <p class="text-zinc-500 dark:text-zinc-400 mt-1">查看业务概览和最近订单</p>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <Loader2 class="w-8 h-8 animate-spin text-zinc-400" />
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="text-center py-20">
      <p class="text-rose-500">{{ error }}</p>
      <button
        @click="fetchData"
        class="mt-4 px-4 py-2 text-sm bg-zinc-100 dark:bg-zinc-800 rounded-lg hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
      >
        重试
      </button>
    </div>

    <!-- 主内容 -->
    <template v-else>
      <!-- 统计卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- 月收入卡片 -->
        <Card
          v-motion
          :initial="{ opacity: 0, y: 20 }"
          :enter="{
            opacity: 1,
            y: 0,
            transition: { type: 'spring', stiffness: 200, damping: 20, delay: 100 }
          }"
          class="backdrop-blur-xl bg-white/70 dark:bg-zinc-900/70 border-zinc-200/50 dark:border-zinc-800/50 rounded-3xl shadow-xl shadow-black/5 hover:shadow-2xl hover:shadow-black/10 transition-all duration-300"
        >
          <CardHeader class="pb-2">
            <CardTitle class="text-sm font-medium text-zinc-500 dark:text-zinc-400">
              月收入
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div class="flex items-end justify-between">
              <div class="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
                {{ stats ? formatCurrency(stats.monthly_income) : '¥0.00' }}
              </div>
              <div
                v-if="stats"
                :class="[
                  'flex items-center gap-1 text-sm font-medium',
                  getTrendColor(stats.income_trend)
                ]"
              >
                <component :is="getTrendIcon(stats.income_trend)" class="w-4 h-4" />
                <span>{{ Math.abs(stats.income_trend) }}%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- 月利润卡片 -->
        <Card
          v-motion
          :initial="{ opacity: 0, y: 20 }"
          :enter="{
            opacity: 1,
            y: 0,
            transition: { type: 'spring', stiffness: 200, damping: 20, delay: 200 }
          }"
          class="backdrop-blur-xl bg-white/70 dark:bg-zinc-900/70 border-zinc-200/50 dark:border-zinc-800/50 rounded-3xl shadow-xl shadow-black/5 hover:shadow-2xl hover:shadow-black/10 transition-all duration-300"
        >
          <CardHeader class="pb-2">
            <CardTitle class="text-sm font-medium text-zinc-500 dark:text-zinc-400">
              月利润
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div class="flex items-end justify-between">
              <div class="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
                {{ stats ? formatCurrency(stats.monthly_profit) : '¥0.00' }}
              </div>
              <div
                v-if="stats"
                :class="[
                  'flex items-center gap-1 text-sm font-medium',
                  getTrendColor(stats.profit_trend)
                ]"
              >
                <component :is="getTrendIcon(stats.profit_trend)" class="w-4 h-4" />
                <span>{{ Math.abs(stats.profit_trend) }}%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- 最近订单 -->
      <Card
        v-motion
        :initial="{ opacity: 0, y: 20 }"
        :enter="{
          opacity: 1,
          y: 0,
          transition: { type: 'spring', stiffness: 200, damping: 20, delay: 300 }
        }"
        class="backdrop-blur-xl bg-white/70 dark:bg-zinc-900/70 border-zinc-200/50 dark:border-zinc-800/50 rounded-3xl shadow-xl shadow-black/5"
      >
        <CardHeader>
          <CardTitle class="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            最近订单
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div
            v-if="recentOrders.length === 0"
            class="text-center py-10 text-zinc-500 dark:text-zinc-400"
          >
            暂无订单数据
          </div>
          <div v-else class="space-y-4">
            <div
              v-for="(order, index) in recentOrders"
              :key="order.id"
              v-motion
              :initial="{ opacity: 0, x: -20 }"
              :enter="{
                opacity: 1,
                x: 0,
                transition: {
                  type: 'spring',
                  stiffness: 200,
                  damping: 20,
                  delay: 400 + index * 100
                }
              }"
              class="flex items-center gap-4 p-4 rounded-2xl bg-zinc-50/50 dark:bg-zinc-800/50 hover:bg-zinc-100/50 dark:hover:bg-zinc-700/50 transition-colors"
            >
              <!-- 公司名 -->
              <div class="flex-1 min-w-0">
                <p class="font-medium text-zinc-900 dark:text-zinc-100 truncate">
                  {{ order.company_name }}
                </p>
              </div>

              <!-- 进度条 -->
              <div class="w-32 flex items-center gap-2">
                <div class="flex-1 h-2 bg-zinc-200 dark:bg-zinc-700 rounded-full overflow-hidden">
                  <div
                    :class="[
                      'h-full rounded-full transition-all duration-500',
                      getProgressColor(order.progress)
                    ]"
                    :style="{ width: `${order.progress}%` }"
                  />
                </div>
                <span class="text-xs text-zinc-500 dark:text-zinc-400 w-8 text-right">
                  {{ order.progress }}%
                </span>
              </div>

              <!-- 金额 -->
              <div class="w-28 text-right">
                <p class="font-medium text-zinc-900 dark:text-zinc-100">
                  {{ formatCurrency(order.income) }}
                </p>
              </div>

              <!-- 状态标签 -->
              <div class="w-20 text-right">
                <span
                  :class="[
                    'inline-flex items-center justify-center px-2.5 py-1 rounded-full text-xs font-medium',
                    getStatusConfig(order.status).class
                  ]"
                >
                  {{ getStatusConfig(order.status).label }}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </template>
  </div>
</template>
