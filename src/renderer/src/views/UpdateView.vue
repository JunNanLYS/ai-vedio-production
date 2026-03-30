<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'

interface UpdateInfo {
  available: boolean
  version?: string
  releaseDate?: string
  releaseNotes?: string
  downloading: boolean
  progress: number
}

interface DownloadProgress {
  percent: number
  transferred: number
  total: number
  bytesPerSecond: number
}

const currentVersion = ref<string>('')
const checking = ref(false)
const updateInfo = ref<UpdateInfo | null>(null)
const downloadProgress = ref<DownloadProgress | null>(null)
const downloading = ref(false)
const downloaded = ref(false)
const errorMessage = ref<string>('')
const showUpdateDialog = ref(false)

const formattedProgress = computed(() => {
  if (!downloadProgress.value) return { percent: '0%', speed: '', transferred: '', total: '' }
  const p = downloadProgress.value
  return {
    percent: `${p.percent.toFixed(1)}%`,
    speed: formatBytes(p.bytesPerSecond) + '/s',
    transferred: formatBytes(p.transferred),
    total: formatBytes(p.total)
  }
})

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
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

async function checkForUpdates() {
  checking.value = true
  errorMessage.value = ''
  updateInfo.value = null
  downloaded.value = false
  downloadProgress.value = null

  try {
    await window.api.checkForUpdates()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '检查更新失败'
  } finally {
    checking.value = false
  }
}

async function downloadUpdate() {
  downloading.value = true
  errorMessage.value = ''

  try {
    await window.api.downloadUpdate()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '下载更新失败'
    downloading.value = false
  }
}

function installUpdate() {
  window.api.quitAndInstall()
}

function handleUpdateAvailable(info: UpdateInfo) {
  updateInfo.value = info
  showUpdateDialog.value = true
}

function handleUpdateNotAvailable() {
  updateInfo.value = { available: false, downloading: false, progress: 0 }
}

function handleUpdateProgress(progress: DownloadProgress) {
  downloadProgress.value = progress
}

function handleUpdateDownloaded() {
  downloading.value = false
  downloaded.value = true
}

function handleUpdateError(error: string) {
  errorMessage.value = error
  downloading.value = false
}

onMounted(async () => {
  currentVersion.value = await window.api.getAppVersion()

  window.api.onUpdateAvailable(handleUpdateAvailable)
  window.api.onUpdateNotAvailable(handleUpdateNotAvailable)
  window.api.onUpdateProgress(handleUpdateProgress)
  window.api.onUpdateDownloaded(handleUpdateDownloaded)
  window.api.onUpdateError(handleUpdateError)
})

onUnmounted(() => {
})
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">软件更新</h1>
      <p class="text-zinc-500 dark:text-zinc-400 mt-1">检查并安装软件更新</p>
    </div>

    <Card
      class="backdrop-blur-xl bg-white/70 dark:bg-zinc-900/70 border-zinc-200/50 dark:border-zinc-800/50 rounded-3xl shadow-xl shadow-black/5"
    >
      <CardHeader>
        <CardTitle class="text-lg">当前版本</CardTitle>
        <CardDescription>您正在使用的软件版本</CardDescription>
      </CardHeader>
      <CardContent>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div
              class="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 shadow-lg shadow-violet-500/30"
            >
              <svg class="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
                />
              </svg>
            </div>
            <div>
              <p class="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
                v{{ currentVersion }}
              </p>
              <p class="text-sm text-zinc-500 dark:text-zinc-400">AI 视频生产工具</p>
            </div>
          </div>
          <Button
            :disabled="checking || downloading"
            class="h-12 px-6 rounded-xl font-medium"
            @click="checkForUpdates"
          >
            <svg
              v-if="checking"
              class="mr-2 h-5 w-5 animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
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
            <span>{{ checking ? '检查中...' : '检查更新' }}</span>
          </Button>
        </div>
      </CardContent>
    </Card>

    <Card
      v-if="updateInfo && !updateInfo.available"
      class="backdrop-blur-xl bg-white/70 dark:bg-zinc-900/70 border-zinc-200/50 dark:border-zinc-800/50 rounded-3xl shadow-xl shadow-black/5"
    >
      <CardContent class="p-6">
        <div class="flex items-center gap-4">
          <div
            class="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100 dark:bg-emerald-900/30"
          >
            <svg
              class="h-6 w-6 text-emerald-600 dark:text-emerald-400"
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
            <p class="text-lg font-semibold text-zinc-900 dark:text-zinc-100">已是最新版本</p>
            <p class="text-sm text-zinc-500 dark:text-zinc-400">
              您当前使用的 v{{ currentVersion }} 是最新版本
            </p>
          </div>
        </div>
      </CardContent>
    </Card>

    <Card
      v-if="errorMessage"
      class="backdrop-blur-xl bg-white/70 dark:bg-zinc-900/70 border-zinc-200/50 dark:border-zinc-800/50 rounded-3xl shadow-xl shadow-black/5"
    >
      <CardContent class="p-6">
        <div class="flex items-center gap-4">
          <div
            class="flex h-12 w-12 items-center justify-center rounded-xl bg-rose-100 dark:bg-rose-900/30"
          >
            <svg
              class="h-6 w-6 text-rose-600 dark:text-rose-400"
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
            <p class="text-lg font-semibold text-rose-600 dark:text-rose-400">更新出错</p>
            <p class="text-sm text-zinc-500 dark:text-zinc-400">{{ errorMessage }}</p>
          </div>
        </div>
      </CardContent>
    </Card>

    <Dialog v-model:open="showUpdateDialog">
      <DialogContent
        class="sm:max-w-lg rounded-2xl bg-white/95 dark:bg-zinc-900/95 backdrop-blur-xl"
      >
        <DialogHeader>
          <DialogTitle class="text-xl">发现新版本</DialogTitle>
          <DialogDescription class="text-base">
            有新版本可供下载安装
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-4 py-4">
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

          <div v-if="updateInfo?.releaseNotes" class="space-y-2">
            <p class="text-sm font-medium text-zinc-700 dark:text-zinc-300">更新内容</p>
            <div
              class="max-h-40 overflow-y-auto rounded-xl bg-zinc-50 dark:bg-zinc-800/50 p-4 text-sm text-zinc-600 dark:text-zinc-400 whitespace-pre-wrap"
            >
              {{ updateInfo.releaseNotes }}
            </div>
          </div>

          <div v-if="downloading || downloaded" class="space-y-2">
            <div class="flex items-center justify-between text-sm">
              <span class="text-zinc-500 dark:text-zinc-400">下载进度</span>
              <span class="font-medium text-zinc-900 dark:text-zinc-100">
                {{ formattedProgress.percent }}
              </span>
            </div>
            <div class="h-2 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
              <div
                class="h-full rounded-full bg-gradient-to-r from-violet-500 to-purple-600 transition-all duration-300"
                :style="{ width: `${downloadProgress?.percent || 0}%` }"
              />
            </div>
            <div
              v-if="downloadProgress"
              class="flex items-center justify-between text-xs text-zinc-500 dark:text-zinc-400"
            >
              <span>{{ formattedProgress.transferred }} / {{ formattedProgress.total }}</span>
              <span>{{ formattedProgress.speed }}</span>
            </div>
          </div>
        </div>

        <DialogFooter class="gap-2 sm:gap-0">
          <Button
            variant="outline"
            class="rounded-xl"
            @click="showUpdateDialog = false"
          >
            稍后提醒
          </Button>
          <Button
            v-if="!downloading && !downloaded"
            class="rounded-xl bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700"
            @click="downloadUpdate"
          >
            立即下载
          </Button>
          <Button
            v-else-if="downloaded"
            class="rounded-xl bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700"
            @click="installUpdate"
          >
            立即安装
          </Button>
          <Button
            v-else
            disabled
            class="rounded-xl"
          >
            下载中...
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
