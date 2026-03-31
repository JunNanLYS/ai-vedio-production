<script setup lang="ts">
import { ref, computed } from 'vue'
import { X, FolderSearch, Loader2, FolderOpen, AlertCircle } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'load', path: string): void
}>()

const projectPath = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

const isValid = computed(() => {
  return projectPath.value.trim().length > 0 && !isLoading.value
})

const handleSelectPath = async (): Promise<void> => {
  const selectedPath = await window.api.selectDirectory()
  if (selectedPath) {
    projectPath.value = selectedPath
    errorMessage.value = ''
  }
}

const handleLoad = async (): Promise<void> => {
  if (!isValid.value) return

  const path = projectPath.value.trim()
  errorMessage.value = ''
  isLoading.value = true

  emit('load', path)

  setTimeout(() => {
    isLoading.value = false
    handleClose()
  }, 500)
}

const handleClose = (): void => {
  projectPath.value = ''
  errorMessage.value = ''
  isLoading.value = false
  emit('close')
}

defineExpose({
  setError: (message: string) => {
    errorMessage.value = message
    isLoading.value = false
  },
  resetLoading: () => {
    isLoading.value = false
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/30 backdrop-blur-sm" @click="handleClose" />

        <div
          class="relative w-full max-w-md bg-white/90 dark:bg-zinc-900/90 backdrop-blur-xl rounded-3xl shadow-2xl border border-black/5 dark:border-white/5 overflow-hidden"
        >
          <div
            class="flex items-center justify-between px-6 py-4 border-b border-black/5 dark:border-white/5"
          >
            <div class="flex items-center gap-3">
              <div
                class="w-8 h-8 rounded-xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center"
              >
                <FolderSearch :size="16" class="text-zinc-600 dark:text-zinc-400" />
              </div>
              <h2 class="text-lg font-semibold text-zinc-800 dark:text-zinc-200">加载资产项目</h2>
            </div>
            <button
              @click="handleClose"
              class="p-2 rounded-xl hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            >
              <X :size="18" class="text-zinc-500" />
            </button>
          </div>

          <div class="p-6 space-y-4">
            <div class="flex items-center gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-xl">
              <AlertCircle :size="16" class="text-amber-600 dark:text-amber-400 shrink-0" />
              <p class="text-xs text-amber-700 dark:text-amber-300">
                加载功能用于导入已有的资产项目目录，会自动扫描目录中的文件并建立索引
              </p>
            </div>

            <div>
              <label class="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                项目目录
              </label>
              <div class="flex gap-2">
                <Input
                  v-model="projectPath"
                  placeholder="选择要加载的项目目录..."
                  :disabled="isLoading"
                  readonly
                  class="rounded-xl flex-1 bg-zinc-50 dark:bg-zinc-800"
                />
                <Button
                  variant="outline"
                  size="icon"
                  @click="handleSelectPath"
                  :disabled="isLoading"
                  class="rounded-xl shrink-0"
                >
                  <FolderOpen :size="16" />
                </Button>
              </div>
              <p v-if="errorMessage" class="text-xs text-red-500 mt-1.5">
                {{ errorMessage }}
              </p>
            </div>

            <p class="text-xs text-zinc-400">目录应包含 prompts、images、audios、videos 等子目录</p>
          </div>

          <div class="flex justify-end gap-3 px-6 py-4 border-t border-black/5 dark:border-white/5">
            <Button variant="ghost" @click="handleClose" :disabled="isLoading" class="rounded-xl">
              取消
            </Button>
            <Button
              :disabled="!isValid"
              @click="handleLoad"
              class="rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100"
            >
              <Loader2 v-if="isLoading" :size="16" class="animate-spin mr-2" />
              {{ isLoading ? '加载中...' : '加载' }}
            </Button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
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
</style>
