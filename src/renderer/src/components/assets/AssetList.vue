<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import {
  FileText,
  Image,
  Music,
  Video,
  File,
  Trash2,
  Pencil,
  ExternalLink,
  Check,
  X,
  Upload,
  FileSpreadsheet,
  Copy
} from 'lucide-vue-next'
import { cn } from '@/lib/utils'
import { assetsService } from '@/services/assets'
import type { Asset } from '@/types'

const props = defineProps<{
  assets: Asset[]
  selectedIds: number[]
  loading?: boolean
  currentCategory?: string | null
  currentSubCategory?: string | null
}>()

const emit = defineEmits<{
  (e: 'select', id: number): void
  (e: 'delete', id: number): void
  (e: 'rename', id: number, newName: string): void
  (e: 'upload', file: File, category: string, subCategoryName: string): void
}>()

const previewUrls = ref<Map<number, string>>(new Map())
const loadedAssetIds = ref<Set<number>>(new Set())
const renamingId = ref<number | null>(null)
const newName = ref('')
const isDragging = ref(false)
const subCategories = ref<{ id: number; name: string; category: string }[]>([])
const cardRefs = ref<Map<number, HTMLElement | null>>(new Map())
let observer: IntersectionObserver | null = null

const fileExtensionToCategory: Record<string, string> = {
  txt: 'prompt',
  md: 'prompt',
  json: 'prompt',
  jpg: 'image',
  jpeg: 'image',
  png: 'image',
  gif: 'image',
  webp: 'image',
  bmp: 'image',
  svg: 'image',
  mp3: 'audio',
  wav: 'audio',
  ogg: 'audio',
  flac: 'audio',
  aac: 'audio',
  m4a: 'audio',
  mp4: 'video',
  avi: 'video',
  mov: 'video',
  mkv: 'video',
  webm: 'video',
  flv: 'video',
  wmv: 'video',
  ppt: 'document',
  pptx: 'document',
  doc: 'document',
  docx: 'document',
  pdf: 'document'
}

const getCategoryFromFile = (file: File): string => {
  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  return fileExtensionToCategory[ext] || 'prompt'
}

const getFileIcon = (_fileType: string, category: string): typeof File => {
  if (category === 'prompt') return FileText
  if (category === 'image') return Image
  if (category === 'audio') return Music
  if (category === 'video') return Video
  if (category === 'document') return FileSpreadsheet
  return File
}

const getFileTypeLabel = (fileType: string): string => {
  return fileType.toUpperCase()
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const handleCardClick = (asset: Asset): void => {
  emit('select', asset.id)
}

const handleDelete = (id: number, event: Event): void => {
  event.stopPropagation()
  emit('delete', id)
}

const handleOpen = async (asset: Asset, event: Event): Promise<void> => {
  event.stopPropagation()
  try {
    const result = await assetsService.getFilePath(asset.id)
    await window.api.openFile(result.path)
  } catch (error) {
    console.error('打开文件失败:', error)
  }
}

const handleCopyContent = async (asset: Asset, event: Event): Promise<void> => {
  event.stopPropagation()
  try {
    const result = await assetsService.getContent(asset.id)
    await navigator.clipboard.writeText(result.content)
  } catch (error) {
    console.error('复制内容失败:', error)
  }
}

const startRename = (asset: Asset, event: Event): void => {
  event.stopPropagation()
  renamingId.value = asset.id
  const nameWithoutExt = asset.name.replace(/\.[^/.]+$/, '')
  newName.value = nameWithoutExt
}

const cancelRename = (): void => {
  renamingId.value = null
  newName.value = ''
}

const confirmRename = async (asset: Asset): Promise<void> => {
  if (!newName.value.trim() || newName.value === asset.name.replace(/\.[^/.]+$/, '')) {
    cancelRename()
    return
  }

  try {
    await assetsService.rename(asset.id, newName.value.trim())
    emit('rename', asset.id, newName.value.trim())
  } catch (error) {
    console.error('重命名失败:', error)
  } finally {
    cancelRename()
  }
}

const isSelected = (id: number): boolean => {
  return props.selectedIds.includes(id)
}

const loadPreviewUrl = async (asset: Asset): Promise<void> => {
  if (
    (asset.category === 'image' || asset.category === 'video') &&
    !previewUrls.value.has(asset.id) &&
    !loadedAssetIds.value.has(asset.id)
  ) {
    loadedAssetIds.value.add(asset.id)
    try {
      const url = await assetsService.getPreviewUrl(asset.id)
      previewUrls.value.set(asset.id, url)
    } catch (error) {
      console.error('加载预览失败:', error)
      loadedAssetIds.value.delete(asset.id)
    }
  }
}

const handlePreviewError = (assetId: number): void => {
  previewUrls.value.delete(assetId)
}

const initObserver = (): void => {
  if (observer) return

  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const target = entry.target as HTMLElement
          const assetId = Number(target.dataset.assetId)
          const asset = props.assets.find((a) => a.id === assetId)
          if (asset) {
            loadPreviewUrl(asset)
          }
          observer?.unobserve(entry.target)
        }
      })
    },
    {
      rootMargin: '100px'
    }
  )
}

const observeCard = (assetId: number, el: HTMLElement | null): void => {
  if (!el || !observer) return
  el.dataset.assetId = String(assetId)
  observer.observe(el)
}

const setupCardRef = (assetId: number) => (el: any): void => {
  const element = el as HTMLElement | null
  if (element) {
    cardRefs.value.set(assetId, element)
    nextTick(() => {
      observeCard(assetId, element)
    })
  } else {
    const oldEl = cardRefs.value.get(assetId)
    if (oldEl && observer) {
      observer.unobserve(oldEl)
    }
    cardRefs.value.delete(assetId)
  }
}

const handleDragOver = async (event: DragEvent): Promise<void> => {
  event.preventDefault()
  isDragging.value = true
}

const handleDragLeave = (event: DragEvent): void => {
  event.preventDefault()
  if (event.currentTarget === event.target) {
    isDragging.value = false
  }
}

const handleDrop = async (event: DragEvent): Promise<void> => {
  event.preventDefault()
  isDragging.value = false

  if (!event.dataTransfer?.files || event.dataTransfer.files.length === 0) return

  const files = Array.from(event.dataTransfer.files)

  let category = props.currentCategory
  let subCategoryName = props.currentSubCategory || ''

  if (!category) {
    const detectedCategories = new Set<string>()
    files.forEach((file) => {
      detectedCategories.add(getCategoryFromFile(file))
    })

    if (detectedCategories.size === 1) {
      category = Array.from(detectedCategories)[0]
    } else {
      category = getCategoryFromFile(files[0])
    }
  }

  if (!subCategoryName) {
    try {
      const data = await assetsService.getSubCategories(category)
      subCategories.value = data

      if (data.length > 0) {
        subCategoryName = data[0].name
      } else {
        subCategoryName = '默认'
      }
    } catch (error) {
      console.error('加载子分类失败:', error)
      subCategoryName = '默认'
    }
  }

  for (const file of files) {
    emit('upload', file, category, subCategoryName)
  }
}

onMounted(() => {
  initObserver()
})

onUnmounted(() => {
  if (observer) {
    observer.disconnect()
    observer = null
  }
})
</script>

<template>
  <div
    class="asset-list h-full overflow-auto relative"
    @dragover="handleDragOver"
    @dragleave="handleDragLeave"
    @drop="handleDrop"
  >
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-zinc-200 border-t-zinc-600" />
    </div>

    <div
      v-else-if="assets.length === 0"
      class="flex flex-col items-center justify-center h-64 text-zinc-400"
    >
      <File :size="48" :stroke-width="1" class="mb-4 opacity-50" />
      <p class="text-sm">暂无资产</p>
      <p class="text-xs mt-1">拖拽文件到此处或点击上传按钮添加资产</p>
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 p-4">
      <div
        v-for="asset in assets"
        :key="asset.id"
        :ref="setupCardRef(asset.id)"
        @click="handleCardClick(asset)"
        :class="
          cn(
            'group relative bg-white/70 dark:bg-zinc-800/50 backdrop-blur-xl rounded-2xl p-5 cursor-pointer',
            'border border-black/5 dark:border-white/5',
            'shadow-xl shadow-black/5 dark:shadow-black/20',
            'transition-transform transition-shadow duration-300 hover:scale-[1.02] hover:shadow-2xl',
            isSelected(asset.id) && 'ring-2 ring-zinc-900/20 dark:ring-white/20'
          )
        "
      >
        <div class="flex flex-col items-center">
          <div
            :class="
              cn(
                'w-24 h-24 rounded-2xl flex items-center justify-center mb-4 overflow-hidden',
                'bg-gradient-to-br from-zinc-100 to-zinc-50 dark:from-zinc-700 dark:to-zinc-800',
                'shadow-inner'
              )
            "
          >
            <div
              v-if="asset.uploading"
              class="w-full h-full flex items-center justify-center bg-zinc-100 dark:bg-zinc-800"
            >
              <div class="relative">
                <div
                  class="animate-spin rounded-full h-10 w-10 border-2 border-zinc-200 dark:border-zinc-600 border-t-zinc-600 dark:border-t-zinc-300"
                />
              </div>
            </div>
            <img
              v-else-if="
                (asset.category === 'image' || asset.category === 'video') &&
                previewUrls.get(asset.id)
              "
              :src="previewUrls.get(asset.id)"
              :alt="asset.name"
              class="w-full h-full object-cover"
              @error="handlePreviewError(asset.id)"
            />
            <component
              v-else
              :is="getFileIcon(asset.file_type, asset.category)"
              :size="40"
              :stroke-width="1.5"
              class="text-zinc-600 dark:text-zinc-300"
            />
          </div>

          <div v-if="renamingId === asset.id" class="w-full mb-1">
            <div class="flex items-center gap-1">
              <input
                v-model="newName"
                type="text"
                class="min-w-0 flex-1 h-8 px-2 text-sm rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 focus:outline-none focus:ring-1 focus:ring-zinc-400"
                @click.stop
                @keyup.enter="confirmRename(asset)"
                @keyup.esc="cancelRename"
              />
              <button
                @click.stop="confirmRename(asset)"
                class="p-1.5 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors shrink-0"
              >
                <Check :size="14" class="text-green-500" />
              </button>
              <button
                @click.stop="cancelRename"
                class="p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors shrink-0"
              >
                <X :size="14" class="text-red-400" />
              </button>
            </div>
          </div>
          <h3
            v-else
            class="text-base font-medium text-zinc-800 dark:text-zinc-200 text-center truncate w-full mb-2"
          >
            {{ asset.name }}
          </h3>

          <div class="flex items-center gap-2 text-xs text-zinc-400">
            <span class="px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-700">
              {{ getFileTypeLabel(asset.file_type) }}
            </span>
            <span
              v-if="asset.uploading"
              class="px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-500"
            >
              上传中...
            </span>
          </div>

          <p class="text-xs text-zinc-400 mt-2">
            {{ formatDate(asset.created_at) }}
          </p>
        </div>

        <div
          v-if="!asset.uploading"
          :class="
            cn(
              'absolute top-2 right-2 flex gap-1',
              'opacity-0 group-hover:opacity-100 transition-opacity'
            )
          "
        >
          <button
            v-if="asset.category === 'prompt'"
            @click="handleCopyContent(asset, $event)"
            :class="
              cn(
                'p-1.5 rounded-lg',
                'bg-green-50 dark:bg-green-900/30 text-green-500',
                'hover:bg-green-100 dark:hover:bg-green-900/50'
              )
            "
            title="复制内容"
          >
            <Copy :size="14" />
          </button>
          <button
            @click="handleOpen(asset, $event)"
            :class="
              cn(
                'p-1.5 rounded-lg',
                'bg-blue-50 dark:bg-blue-900/30 text-blue-500',
                'hover:bg-blue-100 dark:hover:bg-blue-900/50'
              )
            "
            title="打开文件"
          >
            <ExternalLink :size="14" />
          </button>
          <button
            @click="startRename(asset, $event)"
            :class="
              cn(
                'p-1.5 rounded-lg',
                'bg-zinc-50 dark:bg-zinc-700/50 text-zinc-500',
                'hover:bg-zinc-100 dark:hover:bg-zinc-700'
              )
            "
            title="重命名"
          >
            <Pencil :size="14" />
          </button>
          <button
            @click="handleDelete(asset.id, $event)"
            :class="
              cn(
                'p-1.5 rounded-lg',
                'bg-red-50 dark:bg-red-900/30 text-red-500',
                'hover:bg-red-100 dark:hover:bg-red-900/50'
              )
            "
            title="删除"
          >
            <Trash2 :size="14" />
          </button>
        </div>
      </div>
    </div>

    <Transition name="fade">
      <div
        v-if="isDragging"
        class="absolute inset-0 z-10 flex items-center justify-center bg-zinc-50/90 dark:bg-zinc-900/90 backdrop-blur-sm rounded-2xl"
      >
        <div class="text-center">
          <div
            class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-zinc-200 dark:bg-zinc-700 flex items-center justify-center"
          >
            <Upload :size="32" class="text-zinc-500 dark:text-zinc-400" />
          </div>
          <p class="text-sm font-medium text-zinc-700 dark:text-zinc-300">释放以上传文件</p>
          <p class="text-xs text-zinc-400 mt-1">将根据当前分类自动归类</p>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.asset-list::-webkit-scrollbar {
  width: 6px;
}

.asset-list::-webkit-scrollbar-track {
  background: transparent;
}

.asset-list::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.dark .asset-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
