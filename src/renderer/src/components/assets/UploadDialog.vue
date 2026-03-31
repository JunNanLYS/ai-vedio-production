<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { X, Upload, Check, ChevronDown } from 'lucide-vue-next'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { assetsService } from '@/services/assets'
import type { SubCategory } from '@/types'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'upload', file: File, category: string, subCategoryName: string): void
}>()

const categories = [
  { id: 'prompt', name: 'Prompt' },
  { id: 'image', name: '图片' },
  { id: 'audio', name: '声音' },
  { id: 'video', name: '视频' },
  { id: 'document', name: '文档' }
]

const selectedFile = ref<File | null>(null)
const selectedCategory = ref<string>('')
const selectedSubCategory = ref<string>('')
const subCategories = ref<SubCategory[]>([])
const isDragging = ref(false)
const uploadProgress = ref(0)
const isUploading = ref(false)
const isCategoryOpen = ref(false)
const isSubCategoryOpen = ref(false)

const availableSubCategories = computed(() => {
  return subCategories.value.filter((sub) => sub.category === selectedCategory.value)
})

watch(selectedCategory, async (newCategory) => {
  selectedSubCategory.value = ''
  if (newCategory) {
    try {
      const data = await assetsService.getSubCategories(newCategory)
      subCategories.value = data
    } catch (error) {
      console.error('加载子分类失败:', error)
      subCategories.value = []
    }
  } else {
    subCategories.value = []
  }
})

const handleFileSelect = (event: Event): void => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0] as File
  }
}

const handleDrop = (event: DragEvent): void => {
  event.preventDefault()
  isDragging.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
    selectedFile.value = event.dataTransfer.files[0]
  }
}

const handleDragOver = (event: DragEvent): void => {
  event.preventDefault()
  isDragging.value = true
}

const handleDragLeave = (): void => {
  isDragging.value = false
}

const handleUpload = async (): Promise<void> => {
  if (!selectedFile.value || !selectedCategory.value || !selectedSubCategory.value) return

  isUploading.value = true
  uploadProgress.value = 0

  const progressInterval = setInterval(() => {
    uploadProgress.value += 10
    if (uploadProgress.value >= 100) {
      clearInterval(progressInterval)
    }
  }, 100)

  const subCategoryName = getSubCategoryName(selectedSubCategory.value)
  emit('upload', selectedFile.value, selectedCategory.value, subCategoryName)

  setTimeout(() => {
    isUploading.value = false
    uploadProgress.value = 0
    handleClose()
  }, 1000)
}

const handleClose = (): void => {
  selectedFile.value = null
  selectedCategory.value = ''
  selectedSubCategory.value = ''
  subCategories.value = []
  emit('close')
}

const canUpload = computed(() => {
  return selectedFile.value && selectedCategory.value && selectedSubCategory.value
})

const getCategoryName = (id: string): string => {
  return categories.find((c) => c.id === id)?.name || id
}

const getSubCategoryName = (id: string): string => {
  return subCategories.value.find((s) => s.id.toString() === id)?.name || id
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
            <h2 class="text-lg font-semibold text-zinc-800 dark:text-zinc-200">上传资产</h2>
            <button
              @click="handleClose"
              class="p-2 rounded-xl hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            >
              <X :size="18" class="text-zinc-500" />
            </button>
          </div>

          <div class="p-6 space-y-4">
            <div
              @drop="handleDrop"
              @dragover="handleDragOver"
              @dragleave="handleDragLeave"
              :class="
                cn(
                  'relative border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-300',
                  isDragging
                    ? 'border-zinc-400 bg-zinc-50 dark:bg-zinc-800'
                    : 'border-zinc-200 dark:border-zinc-700',
                  selectedFile &&
                    'border-zinc-300 dark:border-zinc-600 bg-zinc-50/50 dark:bg-zinc-800/50'
                )
              "
            >
              <input
                type="file"
                @change="handleFileSelect"
                class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />

              <div v-if="!selectedFile" class="space-y-3">
                <div
                  class="w-12 h-12 mx-auto rounded-2xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center"
                >
                  <Upload :size="24" class="text-zinc-400" />
                </div>
                <div>
                  <p class="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                    拖拽文件到此处或点击选择
                  </p>
                  <p class="text-xs text-zinc-400 mt-1">支持所有文件类型</p>
                </div>
              </div>

              <div v-else class="space-y-2">
                <div
                  class="w-12 h-12 mx-auto rounded-2xl bg-green-100 dark:bg-green-900/30 flex items-center justify-center"
                >
                  <Check :size="24" class="text-green-500" />
                </div>
                <p class="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                  {{ selectedFile.name }}
                </p>
                <p class="text-xs text-zinc-400">{{ (selectedFile.size / 1024).toFixed(1) }} KB</p>
              </div>
            </div>

            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                  分类
                </label>
                <div class="relative">
                  <button
                    @click="isCategoryOpen = !isCategoryOpen"
                    :class="
                      cn(
                        'w-full h-10 px-3 rounded-xl border border-zinc-200 dark:border-zinc-700',
                        'bg-white dark:bg-zinc-800 text-sm text-left flex items-center justify-between',
                        'hover:border-zinc-300 dark:hover:border-zinc-600 transition-colors',
                        'focus:outline-none focus:ring-2 focus:ring-zinc-900/10 dark:focus:ring-white/10'
                      )
                    "
                  >
                    <span
                      :class="
                        selectedCategory ? 'text-zinc-700 dark:text-zinc-300' : 'text-zinc-400'
                      "
                    >
                      {{ selectedCategory ? getCategoryName(selectedCategory) : '选择分类' }}
                    </span>
                    <ChevronDown :size="16" class="text-zinc-400" />
                  </button>

                  <Transition name="dropdown">
                    <div
                      v-if="isCategoryOpen"
                      class="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-zinc-800 rounded-xl border border-zinc-200 dark:border-zinc-700 shadow-lg z-10 overflow-hidden"
                    >
                      <button
                        v-for="category in categories"
                        :key="category.id"
                        @click="
                          (selectedCategory = category.id), (isCategoryOpen = false)
                        "
                        :class="
                          cn(
                            'w-full px-3 py-2.5 text-left text-sm hover:bg-zinc-50 dark:hover:bg-zinc-700/50 transition-colors',
                            selectedCategory === category.id &&
                              'bg-zinc-50 dark:bg-zinc-700/50 text-zinc-900 dark:text-white'
                          )
                        "
                      >
                        {{ category.name }}
                      </button>
                    </div>
                  </Transition>
                </div>
                <div
                  v-if="isCategoryOpen"
                  class="fixed inset-0 z-0"
                  @click="isCategoryOpen = false"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                  子分类
                </label>
                <div class="relative">
                  <button
                    @click="isSubCategoryOpen = !isSubCategoryOpen"
                    :disabled="!selectedCategory"
                    :class="
                      cn(
                        'w-full h-10 px-3 rounded-xl border border-zinc-200 dark:border-zinc-700',
                        'bg-white dark:bg-zinc-800 text-sm text-left flex items-center justify-between',
                        'hover:border-zinc-300 dark:hover:border-zinc-600 transition-colors',
                        'focus:outline-none focus:ring-2 focus:ring-zinc-900/10 dark:focus:ring-white/10',
                        'disabled:opacity-50 disabled:cursor-not-allowed'
                      )
                    "
                  >
                    <span
                      :class="
                        selectedSubCategory ? 'text-zinc-700 dark:text-zinc-300' : 'text-zinc-400'
                      "
                    >
                      {{
                        selectedSubCategory ? getSubCategoryName(selectedSubCategory) : '选择子分类'
                      }}
                    </span>
                    <ChevronDown :size="16" class="text-zinc-400" />
                  </button>

                  <Transition name="dropdown">
                    <div
                      v-if="isSubCategoryOpen && availableSubCategories.length > 0"
                      class="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-zinc-800 rounded-xl border border-zinc-200 dark:border-zinc-700 shadow-lg z-10 overflow-hidden max-h-48 overflow-auto"
                    >
                      <button
                        v-for="sub in availableSubCategories"
                        :key="sub.id"
                        @click="
                          (selectedSubCategory = sub.id.toString()), (isSubCategoryOpen = false)
                        "
                        :class="
                          cn(
                            'w-full px-3 py-2.5 text-left text-sm hover:bg-zinc-50 dark:hover:bg-zinc-700/50 transition-colors',
                            selectedSubCategory === sub.id.toString() &&
                              'bg-zinc-50 dark:bg-zinc-700/50 text-zinc-900 dark:text-white'
                          )
                        "
                      >
                        {{ sub.name }}
                      </button>
                    </div>
                  </Transition>
                </div>
                <div
                  v-if="isSubCategoryOpen"
                  class="fixed inset-0 z-0"
                  @click="isSubCategoryOpen = false"
                />
              </div>
            </div>

            <div v-if="isUploading" class="space-y-2">
              <div class="h-2 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
                <div
                  class="h-full bg-zinc-800 dark:bg-zinc-200 transition-all duration-300"
                  :style="{ width: `${uploadProgress}%` }"
                />
              </div>
              <p class="text-xs text-center text-zinc-500">上传中... {{ uploadProgress }}%</p>
            </div>
          </div>

          <div class="flex justify-end gap-3 px-6 py-4 border-t border-black/5 dark:border-white/5">
            <Button variant="ghost" @click="handleClose" class="rounded-xl"> 取消 </Button>
            <Button
              :disabled="!canUpload || isUploading"
              @click="handleUpload"
              class="rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100"
            >
              上传
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

.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
