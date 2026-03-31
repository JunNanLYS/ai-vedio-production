<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { getBackendUrl } from '@/services/api'
import BackendLogViewer from '@/components/backend/BackendLogViewer.vue'

type ConnectionStatus = 'idle' | 'checking' | 'connected' | 'disconnected'

const status = ref<ConnectionStatus>('idle')
const backendUrl = ref<string>('')
const responseTime = ref<number | null>(null)
const lastCheckTime = ref<Date | null>(null)
const errorMessage = ref<string>('')
const isTesting = ref(false)

const statusText = computed(() => {
  switch (status.value) {
    case 'idle':
      return '未测试'
    case 'checking':
      return '检测中...'
    case 'connected':
      return '已连接'
    case 'disconnected':
      return '未连接'
  }
})

const statusDescription = computed(() => {
  switch (status.value) {
    case 'idle':
      return '点击下方按钮测试连接'
    case 'checking':
      return '正在检测后端服务'
    case 'connected':
      return '后端运行正常'
    case 'disconnected':
      return '后端服务不可用'
  }
})

async function testConnection() {
  if (!backendUrl.value || isTesting.value) return

  isTesting.value = true
  status.value = 'checking'
  errorMessage.value = ''

  try {
    const startTime = Date.now()
    const response = await fetch(`${backendUrl.value}/status`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    responseTime.value = Date.now() - startTime
    lastCheckTime.value = new Date()

    if (response.ok) {
      status.value = 'connected'
    } else {
      status.value = 'disconnected'
      errorMessage.value = `HTTP ${response.status}: ${response.statusText}`
    }
  } catch (error) {
    status.value = 'disconnected'
    responseTime.value = null
    errorMessage.value = error instanceof Error ? error.message : '连接失败'
  } finally {
    isTesting.value = false
  }
}

onMounted(async () => {
  backendUrl.value = await getBackendUrl()
})
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">连通测试</h1>
      <p class="text-zinc-500 dark:text-zinc-400 mt-1">检测后端服务连接状态</p>
    </div>

    <Card
      class="backdrop-blur-xl bg-white/70 dark:bg-zinc-900/70 border-zinc-200/50 dark:border-zinc-800/50 rounded-3xl shadow-xl shadow-black/5"
    >
      <CardContent class="p-8">
        <div class="flex flex-col items-center">
          <div class="relative mb-6">
            <div
              v-if="status === 'connected'"
              class="absolute inset-0 animate-pulse rounded-full bg-emerald-400/30 blur-xl"
            />
            <div
              v-else-if="status === 'checking'"
              class="absolute inset-0 animate-pulse rounded-full bg-amber-400/30 blur-xl"
            />
            <div
              v-else-if="status === 'disconnected'"
              class="absolute inset-0 rounded-full bg-rose-400/20 blur-xl"
            />
            <div v-else class="absolute inset-0 rounded-full bg-zinc-400/20 blur-xl" />

            <div
              :class="[
                'relative h-24 w-24 rounded-full transition-all duration-500',
                'flex items-center justify-center shadow-lg',
                status === 'connected' && 'bg-emerald-500 shadow-emerald-500/30',
                status === 'checking' && 'bg-amber-500 shadow-amber-500/30',
                status === 'disconnected' && 'bg-rose-500 shadow-rose-500/30',
                status === 'idle' && 'bg-zinc-400 shadow-zinc-400/30'
              ]"
            >
              <svg
                v-if="status === 'checking'"
                class="h-10 w-10 text-white animate-spin"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>

              <svg
                v-else-if="status === 'connected'"
                class="h-10 w-10 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M5 13l4 4L19 7"
                />
              </svg>

              <svg
                v-else-if="status === 'disconnected'"
                class="h-10 w-10 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>

              <svg
                v-else
                class="h-10 w-10 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>

            <div
              v-if="status === 'connected'"
              class="absolute inset-0 animate-ping rounded-full bg-emerald-400/20"
            />
          </div>

          <div class="text-center">
            <h2 class="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
              {{ statusText }}
            </h2>
            <p class="mt-1 text-zinc-500 dark:text-zinc-400">
              {{ statusDescription }}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>

    <Card
      class="backdrop-blur-xl bg-white/70 dark:bg-zinc-900/70 border-zinc-200/50 dark:border-zinc-800/50 rounded-3xl shadow-xl shadow-black/5"
    >
      <CardContent class="p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-zinc-500 dark:text-zinc-400">后端地址</p>
            <p class="mt-1 font-mono text-lg text-zinc-900 dark:text-zinc-100">
              {{ backendUrl || '获取中...' }}
            </p>
          </div>
          <div
            class="flex h-12 w-12 items-center justify-center rounded-2xl bg-zinc-100 dark:bg-zinc-800"
          >
            <svg
              class="h-6 w-6 text-zinc-600 dark:text-zinc-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
              />
            </svg>
          </div>
        </div>
      </CardContent>
    </Card>

    <div class="flex justify-center">
      <Button
        :disabled="isTesting || !backendUrl"
        class="h-14 px-8 rounded-2xl text-base font-medium bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
        @click="testConnection"
      >
        <svg v-if="isTesting" class="mr-2 h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          />
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
        <span>{{ isTesting ? '测试中...' : '测试连接' }}</span>
      </Button>
    </div>

    <Card
      v-if="responseTime !== null || errorMessage"
      class="backdrop-blur-xl bg-white/70 dark:bg-zinc-900/70 border-zinc-200/50 dark:border-zinc-800/50 rounded-3xl shadow-xl shadow-black/5"
    >
      <CardContent class="p-6">
        <div class="space-y-4">
          <div v-if="responseTime !== null" class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div
                class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-100 dark:bg-emerald-900/30"
              >
                <svg
                  class="h-5 w-5 text-emerald-600 dark:text-emerald-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-zinc-500 dark:text-zinc-400">响应时间</p>
                <p class="font-mono text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  {{ responseTime }}ms
                </p>
              </div>
            </div>
            <span
              :class="[
                'rounded-full px-3 py-1 text-sm font-medium',
                responseTime < 100
                  ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                  : responseTime < 300
                    ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
                    : 'bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-400'
              ]"
            >
              {{ responseTime < 100 ? '极快' : responseTime < 300 ? '正常' : '较慢' }}
            </span>
          </div>

          <div v-if="status === 'connected'" class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div
                class="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-100 dark:bg-sky-900/30"
              >
                <svg
                  class="h-5 w-5 text-sky-600 dark:text-sky-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-zinc-500 dark:text-zinc-400">状态</p>
                <p class="text-lg font-semibold text-zinc-900 dark:text-zinc-100">OK</p>
              </div>
            </div>
            <span
              class="rounded-full bg-emerald-100 dark:bg-emerald-900/30 px-3 py-1 text-sm font-medium text-emerald-700 dark:text-emerald-400"
            >
              正常
            </span>
          </div>

          <div v-if="errorMessage" class="flex items-center gap-3">
            <div
              class="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-100 dark:bg-rose-900/30"
            >
              <svg
                class="h-5 w-5 text-rose-600 dark:text-rose-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div>
              <p class="text-sm font-medium text-zinc-500 dark:text-zinc-400">错误信息</p>
              <p class="text-lg font-semibold text-rose-600 dark:text-rose-400">
                {{ errorMessage }}
              </p>
            </div>
          </div>

          <div
            v-if="lastCheckTime"
            class="border-t border-zinc-200/50 dark:border-zinc-800/50 pt-4"
          >
            <p class="text-center text-sm text-zinc-400 dark:text-zinc-500">
              最后检测: {{ lastCheckTime.toLocaleTimeString('zh-CN') }}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>

    <BackendLogViewer />
  </div>
</template>
