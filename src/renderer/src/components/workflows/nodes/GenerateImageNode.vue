<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type {
  CanvasNode,
  Asset,
  ImageGenModel,
  ImageAspectRatio,
  ImageResolution,
  ImageOutputFormat
} from '@/types'
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
  referenceImages?: { nodeId: string; order: number; previewUrl?: string; fileSize?: number }[]
}

const props = withDefaults(defineProps<Props>(), {
  scale: 1
})

const emit = defineEmits<{
  resize: [{ width: number; height: number; x?: number; y?: number }]
  update: [updates: Partial<CanvasNode>]
  generate: []
  contextmenu: [event: MouseEvent]
  mousedown: [event: MouseEvent]
}>()

const MIN_WIDTH = 280
const MIN_HEIGHT = 320
const MAX_PROMPT_LENGTH = 20000
const MAX_REFERENCE_IMAGES = 14
const MAX_FILE_SIZE = 30 * 1024 * 1024

const MODEL_OPTIONS: { value: ImageGenModel; label: string }[] = [
  { value: 'nano-banana-2', label: 'Nano Banana 2' },
  { value: 'nano-banana-pro', label: 'Nano Banana Pro' }
]

const ASPECT_RATIO_OPTIONS: { value: ImageAspectRatio; label: string }[] = [
  { value: 'auto', label: '自动' },
  { value: '1:1', label: '1:1' },
  { value: '1:4', label: '1:4' },
  { value: '1:8', label: '1:8' },
  { value: '2:3', label: '2:3' },
  { value: '3:2', label: '3:2' },
  { value: '3:4', label: '3:4' },
  { value: '4:1', label: '4:1' },
  { value: '4:3', label: '4:3' },
  { value: '4:5', label: '4:5' },
  { value: '5:4', label: '5:4' },
  { value: '8:1', label: '8:1' },
  { value: '9:16', label: '9:16' },
  { value: '16:9', label: '16:9' },
  { value: '21:9', label: '21:9' }
]

const RESOLUTION_OPTIONS: { value: ImageResolution; label: string }[] = [
  { value: '1k', label: '1K' },
  { value: '2k', label: '2K' },
  { value: '4k', label: '4K' }
]

const OUTPUT_FORMAT_OPTIONS: { value: ImageOutputFormat; label: string }[] = [
  { value: 'png', label: 'PNG' },
  { value: 'jpg', label: 'JPG' }
]

const promptTemplates = ref<Asset[]>([])
const showTemplatePicker = ref(false)
const loadingTemplates = ref(false)
const showLimitWarning = ref(false)
const limitWarningMessage = ref('')

const currentModel = computed<ImageGenModel>({
  get: () => props.node.genModel || 'nano-banana-2',
  set: (value) => emit('update', { genModel: value })
})

const currentAspectRatio = computed<ImageAspectRatio>({
  get: () => props.node.aspectRatio || 'auto',
  set: (value) => emit('update', { aspectRatio: value })
})

const currentResolution = computed<ImageResolution>({
  get: () => props.node.resolution || '2k',
  set: (value) => emit('update', { resolution: value })
})

const currentOutputFormat = computed<ImageOutputFormat>({
  get: () => props.node.outputFormat || 'png',
  set: (value) => emit('update', { outputFormat: value })
})

const promptLength = computed(() => (props.node.prompt || '').length)
const isPromptOverLimit = computed(() => promptLength.value > MAX_PROMPT_LENGTH)

const nodeStyle = computed(() => ({
  left: `${props.node.x}px`,
  top: `${props.node.y}px`,
  width: `${props.node.width}px`,
  height: `${props.node.height}px`
}))

const referenceImageCount = computed(() => props.referenceImages?.length || 0)
const totalReferenceSize = computed(() => {
  if (!props.referenceImages) return 0
  return props.referenceImages.reduce((sum, img) => sum + (img.fileSize || 0), 0)
})

const fetchPromptTemplates = async () => {
  loadingTemplates.value = true
  try {
    const templates = await assetsService.getAll('prompt')
    promptTemplates.value = templates
  } catch (error) {
    console.error('获取提示词模板失败:', error)
  } finally {
    loadingTemplates.value = false
  }
}

const getTemplateContent = async (template: Asset) => {
  try {
    const result = await assetsService.getContent(template.id)
    emit('update', { prompt: result.content })
    showTemplatePicker.value = false
  } catch (error) {
    console.error('获取模板内容失败:', error)
  }
}

const handlePromptInput = (event: Event) => {
  const value = (event.target as HTMLTextAreaElement).value
  emit('update', { prompt: value })
}

const showWarning = (message: string) => {
  limitWarningMessage.value = message
  showLimitWarning.value = true
  setTimeout(() => {
    showLimitWarning.value = false
  }, 3000)
}

const handleGenerate = () => {
  if ((props.node as any).isGenerating) return

  if (isPromptOverLimit.value) {
    showWarning(`提示词超出限制（${promptLength.value}/${MAX_PROMPT_LENGTH}字符）`)
    return
  }

  if (referenceImageCount.value > MAX_REFERENCE_IMAGES) {
    showWarning(`参考图片超出限制（最多${MAX_REFERENCE_IMAGES}张）`)
    return
  }

  if (totalReferenceSize.value > MAX_FILE_SIZE) {
    showWarning(`参考图片总大小超出限制（最大30MB）`)
    return
  }

  if (!props.node.prompt || !props.node.prompt.trim()) {
    showWarning('请输入提示词')
    return
  }

  emit('generate')
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
  fetchPromptTemplates()
})
</script>

<template>
  <div
    class="absolute rounded-xl border-2 cursor-move transition-shadow duration-200 overflow-visible pointer-events-auto group"
    :class="[
      'bg-purple-50 dark:bg-purple-900/20 border-purple-300 dark:border-purple-700',
      selected ? 'ring-2 ring-blue-500 ring-offset-2 shadow-lg' : 'shadow-md hover:shadow-lg'
    ]"
    :style="nodeStyle"
    @contextmenu="emit('contextmenu', $event)"
    @mousedown="emit('mousedown', $event)"
  >
    <div class="flex flex-col h-full">
      <div
        class="flex items-center gap-2 px-3 py-2 border-b border-purple-200 dark:border-purple-800 bg-white/50 dark:bg-black/20"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          class="text-purple-600 dark:text-purple-400"
        >
          <path d="M8 1L9.5 5.5L14 7L9.5 8.5L8 13L6.5 8.5L2 7L6.5 5.5L8 1Z" />
        </svg>
        <span class="text-sm font-medium text-zinc-700 dark:text-zinc-300 truncate flex-1">
          生成图片
        </span>
      </div>

      <div class="flex-1 flex flex-col overflow-hidden bg-black/5 dark:bg-black/20 p-2 gap-2">
        <!-- 模型选择 -->
        <div class="flex items-center gap-2">
          <span class="text-xs text-zinc-500 dark:text-zinc-400 shrink-0">模型</span>
          <Select v-model="currentModel">
            <SelectTrigger class="h-7 text-xs flex-1">
              <SelectValue placeholder="选择模型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem v-for="option in MODEL_OPTIONS" :key="option.value" :value="option.value">
                {{ option.label }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <!-- Prompt输入 -->
        <div class="flex-1 relative">
          <textarea
            :value="node.prompt || ''"
            placeholder="输入提示词..."
            class="w-full h-full text-sm bg-white dark:bg-zinc-800 border rounded-lg p-2 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 select-text"
            :class="
              isPromptOverLimit
                ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                : 'border-zinc-200 dark:border-zinc-700'
            "
            @input="handlePromptInput"
            @mousedown.stop
            @wheel.stop
          ></textarea>
          <div
            class="absolute bottom-1 right-1 text-[10px] px-1 rounded"
            :class="
              isPromptOverLimit
                ? 'text-red-500 bg-red-100 dark:bg-red-900/50'
                : 'text-zinc-400 bg-zinc-100 dark:bg-zinc-800'
            "
          >
            {{ promptLength }}/{{ MAX_PROMPT_LENGTH }}
          </div>
        </div>

        <!-- 参考图片预览 -->
        <div v-if="referenceImages && referenceImages.length > 0" class="flex gap-1 flex-wrap">
          <div
            v-for="ref in referenceImages"
            :key="ref.nodeId"
            class="relative w-10 h-10 rounded border border-purple-300 dark:border-purple-700 overflow-hidden bg-white dark:bg-zinc-800 transition-transform duration-200 hover:scale-125 hover:z-10 hover:shadow-lg cursor-pointer"
          >
            <img
              v-if="ref.previewUrl"
              :src="ref.previewUrl"
              class="w-full h-full object-cover pointer-events-none"
              draggable="false"
            />
            <span
              class="absolute bottom-0 right-0 bg-purple-500 text-white text-[10px] px-1 rounded-tl"
            >
              图{{ ref.order }}
            </span>
          </div>
          <div
            v-if="referenceImages.length >= MAX_REFERENCE_IMAGES"
            class="w-10 h-10 rounded border-2 border-dashed border-amber-400 dark:border-amber-600 flex items-center justify-center text-amber-500 text-[10px]"
          >
            已满
          </div>
        </div>

        <!-- 配置选项行 -->
        <div class="flex gap-2">
          <!-- 图片比例 -->
          <div class="flex-1">
            <Select v-model="currentAspectRatio">
              <SelectTrigger class="h-7 text-xs w-full">
                <SelectValue placeholder="比例" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="option in ASPECT_RATIO_OPTIONS"
                  :key="option.value"
                  :value="option.value"
                >
                  {{ option.label }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <!-- 分辨率 -->
          <div class="flex-1">
            <Select v-model="currentResolution">
              <SelectTrigger class="h-7 text-xs w-full">
                <SelectValue placeholder="分辨率" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="option in RESOLUTION_OPTIONS"
                  :key="option.value"
                  :value="option.value"
                >
                  {{ option.label }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <!-- 输出格式 -->
          <div class="flex-1">
            <Select v-model="currentOutputFormat">
              <SelectTrigger class="h-7 text-xs w-full">
                <SelectValue placeholder="格式" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="option in OUTPUT_FORMAT_OPTIONS"
                  :key="option.value"
                  :value="option.value"
                >
                  {{ option.label }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <!-- 模板和生成按钮 -->
        <div class="flex gap-2">
          <div class="relative flex-1">
            <button
              class="w-full text-xs bg-zinc-100 dark:bg-zinc-700 hover:bg-zinc-200 dark:hover:bg-zinc-600 text-zinc-700 dark:text-zinc-300 rounded-lg py-1.5 px-2 transition-colors flex items-center justify-center gap-1 border border-zinc-200 dark:border-zinc-600"
              @click="showTemplatePicker = !showTemplatePicker"
            >
              <svg
                width="12"
                height="12"
                viewBox="0 0 16 16"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path d="M3 4h10M3 8h10M3 12h6" />
              </svg>
              模板
            </button>

            <Transition name="dropdown">
              <div
                v-if="showTemplatePicker"
                class="absolute bottom-full left-0 mb-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg shadow-xl max-h-60 overflow-y-auto z-50 min-w-[220px]"
                @mousedown.stop
                @wheel.stop
              >
                <div v-if="loadingTemplates" class="p-3 text-center text-sm text-zinc-500">
                  加载中...
                </div>
                <template v-else-if="promptTemplates.length > 0">
                  <button
                    v-for="template in promptTemplates"
                    :key="template.id"
                    class="w-full text-left text-sm px-3 py-2 hover:bg-zinc-100 dark:hover:bg-zinc-700 whitespace-nowrap overflow-hidden text-ellipsis"
                    @click="getTemplateContent(template)"
                  >
                    {{ template.name }}
                  </button>
                </template>
                <div v-else class="p-3 text-center text-sm text-zinc-500">暂无模板</div>
              </div>
            </Transition>
          </div>

          <button
            class="flex-1 text-xs bg-purple-500 hover:bg-purple-600 disabled:bg-purple-300 dark:disabled:bg-purple-800 text-white rounded-lg py-1.5 px-2 transition-colors flex items-center justify-center gap-1"
            :disabled="(node as any).isGenerating || isPromptOverLimit"
            @click="handleGenerate"
          >
            <svg
              v-if="(node as any).isGenerating"
              width="12"
              height="12"
              viewBox="0 0 16 16"
              fill="none"
              class="animate-spin"
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
              v-else
              width="12"
              height="12"
              viewBox="0 0 16 16"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path d="M8 2v12M2 8h12" />
            </svg>
            {{ (node as any).isGenerating ? '生成中...' : '生成' }}
          </button>
        </div>

        <!-- 警告提示 -->
        <Transition name="fade">
          <div
            v-if="showLimitWarning"
            class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-red-500 text-white text-xs px-3 py-2 rounded-lg shadow-lg z-50"
          >
            {{ limitWarningMessage }}
          </div>
        </Transition>
      </div>
    </div>

    <div
      class="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-purple-500 hover:bg-purple-600 text-white flex items-center justify-center transition-colors shadow-sm cursor-pointer opacity-0 group-hover:opacity-100"
      title="输出连接点"
    >
      <svg
        width="10"
        height="10"
        viewBox="0 0 10 10"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
      >
        <circle cx="5" cy="5" r="2" />
      </svg>
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
  </div>
</template>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

.dropdown-enter-to,
.dropdown-leave-from {
  opacity: 1;
  transform: translateY(0);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
