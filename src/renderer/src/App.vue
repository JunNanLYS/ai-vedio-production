<script setup lang="ts">
import { ref, onMounted } from 'vue'
import MainLayout from './components/layout/MainLayout.vue'
import { setBackendPort } from './services/api'
import { Button } from './components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from './components/ui/dialog'
import { Toaster } from './components/ui/toast'

interface UpdateInfo {
  available: boolean
  version?: string
  releaseDate?: string
  releaseNotes?: string
  downloading: boolean
  progress: number
}

const isReady = ref(false)
const error = ref<string | null>(null)
const showUpdateDialog = ref(false)
const updateInfo = ref<UpdateInfo | null>(null)

function handleRetry() {
  window.location.reload()
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

function handleUpdateAvailable(info: UpdateInfo) {
  updateInfo.value = info
  showUpdateDialog.value = true
}

function goToUpdate() {
  showUpdateDialog.value = false
  window.location.hash = '/update'
}

onMounted(async () => {
  try {
    const port = await window.api.getBackendPort()
    if (port) {
      setBackendPort(port)
      isReady.value = true
    } else {
      error.value = '后端服务启动失败'
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '未知错误'
  }

  window.api.onUpdateAvailable(handleUpdateAvailable)
})
</script>

<template>
  <div v-if="!isReady" class="loading-screen">
    <div class="loading-content">
      <div v-if="error" class="error-state">
        <div class="error-icon">⚠️</div>
        <p class="error-text">{{ error }}</p>
        <button @click="handleRetry" class="retry-btn">重试</button>
      </div>
      <div v-else class="loading-state">
        <div class="spinner"></div>
        <p class="loading-text">正在加载...</p>
      </div>
    </div>
  </div>
  <MainLayout v-else />

  <Toaster />

  <Dialog v-model:open="showUpdateDialog">
    <DialogContent class="sm:max-w-md rounded-2xl bg-white/95 dark:bg-zinc-900/95 backdrop-blur-xl">
      <DialogHeader>
        <DialogTitle class="text-xl">发现新版本</DialogTitle>
        <DialogDescription> 有新版本可供下载安装 </DialogDescription>
      </DialogHeader>

      <div class="flex items-center justify-between rounded-xl bg-zinc-100 dark:bg-zinc-800 p-4">
        <div>
          <p class="text-sm text-zinc-500 dark:text-zinc-400">新版本</p>
          <p class="text-xl font-bold text-violet-600 dark:text-violet-400">
            v{{ updateInfo?.version }}
          </p>
        </div>
        <div class="text-right">
          <p class="text-sm text-zinc-500 dark:text-zinc-400">发布日期</p>
          <p class="text-base font-medium text-zinc-900 dark:text-zinc-100">
            {{ formatDate(updateInfo?.releaseDate) }}
          </p>
        </div>
      </div>

      <DialogFooter class="gap-2 sm:gap-0">
        <Button variant="outline" class="rounded-xl" @click="showUpdateDialog = false">
          稍后提醒
        </Button>
        <Button
          class="rounded-xl bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700"
          @click="goToUpdate"
        >
          前往更新
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<style scoped>
.loading-screen {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #18181b 0%, #27272a 100%);
}

.loading-content {
  text-align: center;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  color: #a1a1aa;
  font-size: 14px;
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.error-icon {
  font-size: 48px;
}

.error-text {
  color: #ef4444;
  font-size: 14px;
}

.retry-btn {
  margin-top: 8px;
  padding: 8px 24px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: #2563eb;
}
</style>
