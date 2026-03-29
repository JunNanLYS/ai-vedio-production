<script setup lang="ts">
import { ref, computed } from 'vue'
import { X, FolderPlus, Loader2, FolderOpen } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'create', name: string, path: string): void
}>()

const projectName = ref('')
const projectPath = ref('')
const isCreating = ref(false)
const errorMessage = ref('')

const isValid = computed(() => {
  return projectName.value.trim().length > 0 && !isCreating.value
})

const handleSelectPath = async (): Promise<void> => {
  const selectedPath = await window.api.selectDirectory()
  if (selectedPath) {
    projectPath.value = selectedPath
  }
}

const handleCreate = async (): Promise<void> => {
  if (!isValid.value) return

  const name = projectName.value.trim()

  if (name.length < 2) {
    errorMessage.value = '项目名称至少需要2个字符'
    return
  }

  if (/[\\/:*?"<>|]/.test(name)) {
    errorMessage.value = '项目名称不能包含特殊字符 \\ / : * ? " < > |'
    return
  }

  errorMessage.value = ''
  isCreating.value = true

  emit('create', name, projectPath.value)

  setTimeout(() => {
    isCreating.value = false
    handleClose()
  }, 500)
}

const handleClose = (): void => {
  projectName.value = ''
  projectPath.value = ''
  errorMessage.value = ''
  isCreating.value = false
  emit('close')
}
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
                <FolderPlus :size="16" class="text-zinc-600 dark:text-zinc-400" />
              </div>
              <h2 class="text-lg font-semibold text-zinc-800 dark:text-zinc-200">新建项目</h2>
            </div>
            <button
              @click="handleClose"
              class="p-2 rounded-xl hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            >
              <X :size="18" class="text-zinc-500" />
            </button>
          </div>

          <div class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                项目名称
              </label>
              <Input
                v-model="projectName"
                placeholder="输入项目名称..."
                :disabled="isCreating"
                class="rounded-xl"
                @keyup.enter="handleCreate"
              />
              <p v-if="errorMessage" class="text-xs text-red-500 mt-1.5">
                {{ errorMessage }}
              </p>
            </div>

            <div>
              <label class="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                保存位置
              </label>
              <div class="flex gap-2">
                <Input
                  v-model="projectPath"
                  placeholder="点击右侧按钮选择目录..."
                  :disabled="isCreating"
                  readonly
                  class="rounded-xl flex-1 bg-zinc-50 dark:bg-zinc-800"
                />
                <Button
                  variant="outline"
                  size="icon"
                  @click="handleSelectPath"
                  :disabled="isCreating"
                  class="rounded-xl shrink-0"
                >
                  <FolderOpen :size="16" />
                </Button>
              </div>
              <p class="text-xs text-zinc-400 mt-1.5">
                {{ projectPath || '未选择则使用默认位置' }}
              </p>
            </div>

            <p class="text-xs text-zinc-400">
              将创建包含 Prompt、图片、声音、视频 等子目录的项目文件夹
            </p>
          </div>

          <div class="flex justify-end gap-3 px-6 py-4 border-t border-black/5 dark:border-white/5">
            <Button variant="ghost" @click="handleClose" :disabled="isCreating" class="rounded-xl">
              取消
            </Button>
            <Button
              :disabled="!isValid"
              @click="handleCreate"
              class="rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100"
            >
              <Loader2 v-if="isCreating" :size="16" class="animate-spin mr-2" />
              {{ isCreating ? '创建中...' : '创建' }}
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
