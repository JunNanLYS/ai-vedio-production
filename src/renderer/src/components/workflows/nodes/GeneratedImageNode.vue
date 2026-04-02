<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import type { CanvasNode, GeneratedImageStatus, Project, SubCategory } from '@/types'
import { assetsService } from '@/services/assets'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'

interface Props {
  node: CanvasNode
  selected?: boolean
  scale?: number
}

const props = withDefaults(defineProps<Props>(), {
  scale: 1
})

const emit = defineEmits<{
  resize: [{ width: number; height: number; x?: number; y?: number }]
  update: [updates: Partial<CanvasNode>]
  convertToAsset: [assetId: number]
  contextmenu: [event: MouseEvent]
  mousedown: [event: MouseEvent]
}>()

const MIN_WIDTH = 160
const MIN_HEIGHT = 160

const status = computed<GeneratedImageStatus>(() => props.node.genStatus || 'pending')
const errorMessage = computed(() => props.node.genError || '生成失败')
const statusText = computed(() => props.node.genStatusText || '')

const nodeStyle = computed(() => ({
  left: `${props.node.x}px`,
  top: `${props.node.y}px`,
  width: `${props.node.width}px`,
  height: `${props.node.height}px`
}))

const statusConfig = computed(() => {
  switch (status.value) {
    case 'pending':
      return {
        bg: 'bg-zinc-50 dark:bg-zinc-900/20',
        border: 'border-zinc-300 dark:border-zinc-700',
        icon: 'clock',
        text: statusText.value || '等待中',
        textColor: 'text-zinc-500 dark:text-zinc-400'
      }
    case 'generating':
      return {
        bg: 'bg-blue-50 dark:bg-blue-900/20',
        border: 'border-blue-300 dark:border-blue-700',
        icon: 'loading',
        text: statusText.value || '生成中',
        textColor: 'text-blue-600 dark:text-blue-400'
      }
    case 'success':
      return {
        bg: 'bg-green-50 dark:bg-green-900/20',
        border: 'border-green-300 dark:border-green-700',
        icon: 'check',
        text: statusText.value || '已完成',
        textColor: 'text-green-600 dark:text-green-400'
      }
    case 'failed':
      return {
        bg: 'bg-red-50 dark:bg-red-900/20',
        border: 'border-red-300 dark:border-red-700',
        icon: 'error',
        text: statusText.value || '生成失败',
        textColor: 'text-red-600 dark:text-red-400'
      }
    default:
      return {
        bg: 'bg-zinc-50 dark:bg-zinc-900/20',
        border: 'border-zinc-300 dark:border-zinc-700',
        icon: 'clock',
        text: '未知状态',
        textColor: 'text-zinc-500 dark:text-zinc-400'
      }
  }
})

const showSaveDialog = ref(false)
const projects = ref<Project[]>([])
const subCategories = ref<SubCategory[]>([])
const selectedProjectId = ref<number | null>(null)
const selectedCategory = ref('image')
const selectedSubCategory = ref('')
const isSaving = ref(false)

const categoryOptions = [
  { value: 'image', label: '图片' },
  { value: 'prompt', label: '提示词' },
  { value: 'audio', label: '音频' },
  { value: 'video', label: '视频' },
  { value: 'document', label: '文档' }
]

const loadProjects = async () => {
  try {
    projects.value = await assetsService.getProjects()
    if (projects.value.length > 0) {
      const currentProject = await assetsService.getCurrentProject()
      selectedProjectId.value = currentProject.project?.id || projects.value[0].id
      await loadSubCategories()
    }
  } catch (error) {
    console.error('加载项目列表失败:', error)
  }
}

const loadSubCategories = async () => {
  if (!selectedProjectId.value) return
  try {
    const result = await assetsService.getSubCategories(selectedCategory.value)
    subCategories.value = result
    if (result.length > 0) {
      selectedSubCategory.value = result[0].name
    } else {
      selectedSubCategory.value = ''
    }
  } catch (error) {
    console.error('加载子分类失败:', error)
  }
}

const handleProjectChange = async () => {
  await loadSubCategories()
}

const handleCategoryChange = async () => {
  await loadSubCategories()
}

const openSaveDialog = () => {
  showSaveDialog.value = true
  loadProjects()
}

const handleCustomSave = async () => {
  if (!props.node.assetId) {
    return
  }

  if (!selectedProjectId.value) {
    return
  }

  isSaving.value = true
  try {
    const result = await assetsService.moveAsset(
      props.node.assetId,
      selectedProjectId.value,
      selectedCategory.value,
      selectedSubCategory.value
    )

    showSaveDialog.value = false

    emit('update', {
      category: result.category,
      sub_category: result.sub_category,
      filePath: result.file_path,
      fileType: result.file_type
    })

    emit('convertToAsset', result.id)
  } catch (error: any) {
    console.error('移动资产失败:', error)
  } finally {
    isSaving.value = false
  }
}

const resizeState = ref<{
  isResizing: boolean
  direction: string
  startX: number
  startY: number
  startWidth: number
  startHeight: number
  startNodeX: number
  startNodeY: number
} | null>(null)

const resizeCursors: Record<string, string> = {
  n: 'ns-resize',
  s: 'ns-resize',
  e: 'ew-resize',
  w: 'ew-resize',
  ne: 'nesw-resize',
  sw: 'nesw-resize',
  nw: 'nwse-resize',
  se: 'nwse-resize'
}

const getResizeCursor = (direction: string) => resizeCursors[direction] || 'default'

const handleResizeStart = (e: MouseEvent, direction: string) => {
  e.preventDefault()
  e.stopPropagation()

  resizeState.value = {
    isResizing: true,
    direction,
    startX: e.clientX,
    startY: e.clientY,
    startWidth: props.node.width,
    startHeight: props.node.height,
    startNodeX: props.node.x,
    startNodeY: props.node.y
  }

  document.addEventListener('mousemove', handleResizeMove)
  document.addEventListener('mouseup', handleResizeEnd)
}

const handleResizeMove = (e: MouseEvent) => {
  if (!resizeState.value) return

  const { direction, startX, startY, startWidth, startHeight, startNodeX, startNodeY } =
    resizeState.value
  const deltaX = (e.clientX - startX) / props.scale
  const deltaY = (e.clientY - startY) / props.scale

  let newWidth = startWidth
  let newHeight = startHeight
  let newNodeX: number | undefined
  let newNodeY: number | undefined

  if (direction.includes('e')) {
    newWidth = Math.max(MIN_WIDTH, startWidth + deltaX)
  }
  if (direction.includes('w')) {
    const potentialWidth = startWidth - deltaX
    if (potentialWidth >= MIN_WIDTH) {
      newWidth = potentialWidth
      newNodeX = startNodeX + deltaX
    } else {
      newWidth = MIN_WIDTH
      newNodeX = startNodeX + startWidth - MIN_WIDTH
    }
  }
  if (direction.includes('s')) {
    newHeight = Math.max(MIN_HEIGHT, startHeight + deltaY)
  }
  if (direction.includes('n')) {
    const potentialHeight = startHeight - deltaY
    if (potentialHeight >= MIN_HEIGHT) {
      newHeight = potentialHeight
      newNodeY = startNodeY + deltaY
    } else {
      newHeight = MIN_HEIGHT
      newNodeY = startNodeY + startHeight - MIN_HEIGHT
    }
  }

  emit('resize', { width: newWidth, height: newHeight, x: newNodeX, y: newNodeY })
}

const handleResizeEnd = () => {
  resizeState.value = null
  document.removeEventListener('mousemove', handleResizeMove)
  document.removeEventListener('mouseup', handleResizeEnd)
}

onMounted(() => {
  loadProjects()
})
</script>

<template>
  <div
    class="absolute rounded-xl border-2 cursor-move transition-shadow duration-200 overflow-visible pointer-events-auto group"
    :class="[
      statusConfig.bg,
      statusConfig.border,
      selected ? 'ring-2 ring-blue-500 ring-offset-2 shadow-lg' : 'shadow-md hover:shadow-lg'
    ]"
    :style="nodeStyle"
    @contextmenu="emit('contextmenu', $event)"
    @mousedown="emit('mousedown', $event)"
  >
    <div class="flex flex-col h-full">
      <div
        class="flex items-center gap-2 px-3 py-2 border-b border-inherit bg-white/50 dark:bg-black/20"
      >
        <svg
          v-if="status === 'generating'"
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          class="animate-spin"
          :class="statusConfig.textColor"
        >
          <circle
            cx="8"
            cy="8"
            r="6"
            stroke="currentColor"
            stroke-width="2"
            stroke-dasharray="30"
            stroke-dashoffset="10"
          />
        </svg>
        <svg
          v-else-if="status === 'success'"
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          :class="statusConfig.textColor"
        >
          <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" />
          <path d="M5 8L7 10L11 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <svg
          v-else-if="status === 'failed'"
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          :class="statusConfig.textColor"
        >
          <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" />
          <path d="M6 6L10 10M10 6L6 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
        </svg>
        <svg
          v-else
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          :class="statusConfig.textColor"
        >
          <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" />
          <path d="M8 5V8L10 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
        </svg>
        <span class="text-sm font-medium text-zinc-700 dark:text-zinc-300 truncate flex-1">
          {{ statusConfig.text }}
        </span>
        <button
          v-if="status === 'success' && node.assetId"
          class="text-xs px-2 py-0.5 rounded bg-blue-500 hover:bg-blue-600 text-white transition-colors opacity-0 group-hover:opacity-100"
          title="自定义保存位置"
          @click.stop="openSaveDialog"
        >
          自定义保存
        </button>
      </div>

      <div class="flex-1 flex items-center justify-center overflow-hidden bg-black/5 dark:bg-black/20 relative">
        <img
          v-if="status === 'success' && node.localImagePath"
          :src="node.localImagePath"
          class="w-full h-full object-cover pointer-events-none"
          draggable="false"
        />
        
        <div v-else-if="status === 'generating'" class="flex flex-col items-center justify-center gap-4">
          <div class="relative w-16 h-16">
            <div class="absolute inset-0 rounded-full border-4 border-blue-200 dark:border-blue-800"></div>
            <div 
              class="absolute inset-0 rounded-full border-4 border-blue-500 dark:border-blue-400 border-t-transparent animate-spin"
            ></div>
            <div class="absolute inset-2 rounded-full bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" class="text-blue-500 dark:text-blue-400">
                <path d="M10 2L12 6L16 7L13 10L14 14L10 12L6 14L7 10L4 7L8 6L10 2Z" fill="currentColor" />
              </svg>
            </div>
          </div>
          <div class="flex flex-col items-center gap-1">
            <span class="text-sm font-medium text-blue-600 dark:text-blue-400">AI 正在创作...</span>
            <div class="flex gap-1">
              <span class="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style="animation-delay: 0ms;"></span>
              <span class="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style="animation-delay: 150ms;"></span>
              <span class="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style="animation-delay: 300ms;"></span>
            </div>
          </div>
        </div>

        <div v-else-if="status === 'failed'" class="flex flex-col items-center justify-center gap-3 p-4 text-center">
          <div class="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/50 flex items-center justify-center">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" class="text-red-500 dark:text-red-400">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" />
              <path d="M8 8L16 16M16 8L8 16" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
            </svg>
          </div>
          <span class="text-sm text-red-600 dark:text-red-400 font-medium">生成失败</span>
          <span class="text-xs text-red-500 dark:text-red-500 max-w-[140px] truncate" :title="errorMessage">
            {{ errorMessage }}
          </span>
        </div>

        <div v-else class="flex flex-col items-center justify-center gap-3">
          <div class="w-12 h-12 rounded-full bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" class="text-zinc-400 dark:text-zinc-500">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" />
              <path d="M12 6V12L16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
            </svg>
          </div>
          <span class="text-sm text-zinc-500 dark:text-zinc-400">等待生成</span>
        </div>
      </div>
    </div>

    <template v-if="selected">
      <div
        v-for="direction in ['n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw']"
        :key="direction"
        class="absolute bg-blue-500 opacity-0 hover:opacity-100 transition-opacity"
        :class="{
          'top-0 left-2 right-2 h-1 cursor-ns-resize': direction === 'n',
          'bottom-0 left-2 right-2 h-1 cursor-ns-resize': direction === 's',
          'right-0 top-2 bottom-2 w-1 cursor-ew-resize': direction === 'e',
          'left-0 top-2 bottom-2 w-1 cursor-ew-resize': direction === 'w',
          'top-0 right-0 w-3 h-3 cursor-nesw-resize': direction === 'ne',
          'bottom-0 left-0 w-3 h-3 cursor-nesw-resize': direction === 'sw',
          'top-0 left-0 w-3 h-3 cursor-nwse-resize': direction === 'nw',
          'bottom-0 right-0 w-3 h-3 cursor-nwse-resize': direction === 'se'
        }"
        :style="{ cursor: getResizeCursor(direction) }"
        @mousedown="handleResizeStart($event, direction)"
      ></div>
    </template>

    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showSaveDialog"
          class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm"
          @click.self="showSaveDialog = false"
        >
          <div
            class="bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl w-[400px] max-h-[80vh] overflow-hidden"
            @click.stop
          >
            <div class="px-6 py-4 border-b border-zinc-200 dark:border-zinc-800">
              <h3 class="text-lg font-semibold text-zinc-900 dark:text-zinc-100">自定义保存位置</h3>
              <p class="text-sm text-zinc-500 dark:text-zinc-400 mt-1">选择图片保存的项目和分类</p>
            </div>

            <div class="p-6 space-y-4">
              <div class="space-y-2">
                <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">资产项目</label>
                <Select v-model="selectedProjectId" @update:model-value="handleProjectChange">
                  <SelectTrigger>
                    <SelectValue placeholder="选择项目" />
                  </SelectTrigger>
                  <SelectContent class="z-[10000]">
                    <SelectItem
                      v-for="project in projects"
                      :key="project.id"
                      :value="project.id"
                    >
                      {{ project.name }}
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div class="space-y-2">
                <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">大分类</label>
                <Select v-model="selectedCategory" @update:model-value="handleCategoryChange">
                  <SelectTrigger>
                    <SelectValue placeholder="选择分类" />
                  </SelectTrigger>
                  <SelectContent class="z-[10000]">
                    <SelectItem
                      v-for="cat in categoryOptions"
                      :key="cat.value"
                      :value="cat.value"
                    >
                      {{ cat.label }}
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div class="space-y-2">
                <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">小分类</label>
                <Select v-model="selectedSubCategory">
                  <SelectTrigger>
                    <SelectValue placeholder="选择子分类（可选）" />
                  </SelectTrigger>
                  <SelectContent class="z-[10000]">
                    <SelectItem value="">无</SelectItem>
                    <SelectItem
                      v-for="sub in subCategories"
                      :key="sub.id"
                      :value="sub.name"
                    >
                      {{ sub.name }}
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div class="px-6 py-4 border-t border-zinc-200 dark:border-zinc-800 flex justify-end gap-3">
              <button
                class="px-4 py-2 text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition-colors"
                @click="showSaveDialog = false"
              >
                取消
              </button>
              <button
                class="px-4 py-2 text-sm font-medium text-white bg-blue-500 hover:bg-blue-600 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="isSaving || !selectedProjectId"
                @click="handleCustomSave"
              >
                {{ isSaving ? '保存中...' : '确认保存' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
@keyframes bounce {
  0%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-6px);
  }
}

.animate-bounce {
  animation: bounce 1s infinite ease-in-out;
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
