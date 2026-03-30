<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { CanvasNode } from '@/types'
import { assetsService } from '@/services/assets'
import UploadImageNode from './nodes/UploadImageNode.vue'
import GenerateImageNode from './nodes/GenerateImageNode.vue'
import TextAnnotationNode from './nodes/TextAnnotationNode.vue'

interface Props {
  node: CanvasNode
  selected?: boolean
  scale?: number
  referenceImages?: { nodeId: string; order: number; previewUrl?: string }[]
}

const props = withDefaults(defineProps<Props>(), {
  scale: 1
})

const emit = defineEmits<{
  resize: [{ width: number; height: number; x?: number; y?: number }]
  update: [updates: Partial<CanvasNode>]
  generate: []
}>()

const categoryColors: Record<string, string> = {
  prompt: 'bg-purple-100 dark:bg-purple-900/30 border-purple-300 dark:border-purple-700',
  image: 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700',
  audio: 'bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-700',
  video: 'bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700',
  document: 'bg-yellow-100 dark:bg-yellow-900/30 border-yellow-300 dark:border-yellow-700'
}

const iconColor: Record<string, string> = {
  prompt: 'text-purple-600 dark:text-purple-400',
  image: 'text-blue-600 dark:text-blue-400',
  audio: 'text-green-600 dark:text-green-400',
  video: 'text-red-600 dark:text-red-400',
  document: 'text-yellow-600 dark:text-yellow-400'
}

const MIN_WIDTH = 100
const MIN_HEIGHT = 80

const nodeStyle = computed(() => ({
  left: `${props.node.x}px`,
  top: `${props.node.y}px`,
  width: `${props.node.width}px`,
  height: `${props.node.height}px`
}))

const isImage = computed(() => {
  if (!props.node.fileType) return false
  const imageTypes = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp']
  return imageTypes.includes(props.node.fileType.toLowerCase())
})

const isVideo = computed(() => {
  if (!props.node.fileType) return false
  const videoTypes = ['mp4', 'webm', 'mov', 'avi', 'mkv']
  return videoTypes.includes(props.node.fileType.toLowerCase())
})

const previewUrl = ref<string>('')
const loading = ref(false)

const loadPreview = async () => {
  if (props.node.assetId && (isImage.value || isVideo.value)) {
    loading.value = true
    try {
      previewUrl.value = await assetsService.getPreviewUrl(props.node.assetId)
    } catch (error) {
      console.error('获取预览图失败:', error)
    } finally {
      loading.value = false
    }
  }
}

watch(() => props.node.assetId, loadPreview, { immediate: true })

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
  'n': 'ns-resize',
  's': 'ns-resize',
  'e': 'ew-resize',
  'w': 'ew-resize',
  'ne': 'nesw-resize',
  'sw': 'nesw-resize',
  'nw': 'nwse-resize',
  'se': 'nwse-resize'
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
  
  const { direction, startX, startY, startWidth, startHeight, startNodeX, startNodeY } = resizeState.value
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

const handleUpdate = (updates: Partial<CanvasNode>) => {
  emit('update', updates)
}
</script>

<template>
  <UploadImageNode
    v-if="node.type === 'upload-image'"
    :node="node"
    :selected="selected"
    :scale="scale"
    @resize="emit('resize', $event)"
    @update="handleUpdate"
  />
  <GenerateImageNode
    v-else-if="node.type === 'generate-image'"
    :node="node"
    :selected="selected"
    :scale="scale"
    :reference-images="referenceImages"
    @resize="emit('resize', $event)"
    @update="handleUpdate"
    @generate="emit('generate')"
  />
  <TextAnnotationNode
    v-else-if="node.type === 'text-annotation'"
    :node="node"
    :selected="selected"
    :scale="scale"
    @resize="emit('resize', $event)"
    @update="handleUpdate"
  />
  <div
    v-else
    class="absolute rounded-xl border-2 cursor-move transition-shadow duration-200 overflow-hidden group"
    :class="[
      categoryColors[node.category || 'document'] || 'bg-zinc-100 dark:bg-zinc-800 border-zinc-300 dark:border-zinc-700',
      selected ? 'ring-2 ring-blue-500 ring-offset-2 shadow-lg' : 'shadow-md hover:shadow-lg'
    ]"
    :style="nodeStyle"
  >
    <div class="flex flex-col h-full">
      <div class="flex items-center gap-2 px-3 py-2 border-b border-inherit bg-white/50 dark:bg-black/20">
        <div :class="iconColor[node.category || 'document'] || 'text-zinc-600 dark:text-zinc-400'">
          <svg
            v-if="node.category === 'prompt'"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M12 2L2 7L12 12L22 7L12 2Z" />
            <path d="M2 17L12 22L22 17" />
            <path d="M2 12L12 17L22 12" />
          </svg>
          <svg
            v-else-if="node.category === 'image'"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <path d="M21 15L16 10L5 21" />
          </svg>
          <svg
            v-else-if="node.category === 'audio'"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M9 18V5L21 3V16" />
            <circle cx="6" cy="18" r="3" />
            <circle cx="18" cy="16" r="3" />
          </svg>
          <svg
            v-else-if="node.category === 'video'"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <rect x="2" y="4" width="20" height="16" rx="2" />
            <polygon points="10,8 16,12 10,16" />
          </svg>
          <svg
            v-else
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M14 2H6C5 2 4 3 4 4V20C4 21 5 22 6 22H18C19 22 20 21 20 20V8L14 2Z" />
            <polyline points="14,2 14,8 20,8" />
          </svg>
        </div>
        <span class="text-sm font-medium text-zinc-700 dark:text-zinc-300 truncate flex-1">
          {{ node.name }}
        </span>
        <span v-if="node.fileType" class="text-xs text-zinc-400 dark:text-zinc-500 uppercase">
          .{{ node.fileType }}
        </span>
      </div>

      <div class="flex-1 flex items-center justify-center overflow-hidden bg-black/5 dark:bg-black/20">
        <div v-if="loading" class="flex items-center justify-center">
          <div
            class="w-6 h-6 border-2 border-zinc-200 dark:border-zinc-700 border-t-zinc-600 dark:border-t-zinc-300 rounded-full animate-spin"
          ></div>
        </div>
        <img
          v-else-if="isImage && previewUrl"
          :src="previewUrl"
          :alt="node.name"
          class="w-full h-full object-cover pointer-events-none"
          draggable="false"
          @error="($event.target as HTMLImageElement).style.display = 'none'"
        />
        <video
          v-else-if="isVideo && previewUrl"
          :src="previewUrl"
          class="w-full h-full object-cover"
          muted
        />
        <div
          v-else
          class="flex flex-col items-center justify-center gap-2 text-zinc-400 dark:text-zinc-600"
        >
          <svg
            v-if="node.category === 'prompt'"
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
          >
            <path d="M12 2L2 7L12 12L22 7L12 2Z" />
            <path d="M2 17L12 22L22 17" />
            <path d="M2 12L12 17L22 12" />
          </svg>
          <svg
            v-else-if="node.category === 'audio'"
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
          >
            <path d="M9 18V5L21 3V16" />
            <circle cx="6" cy="18" r="3" />
            <circle cx="18" cy="16" r="3" />
          </svg>
          <svg
            v-else
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
          >
            <path d="M14 2H6C5 2 4 3 4 4V20C4 21 5 22 6 22H18C19 22 20 21 20 20V8L14 2Z" />
            <polyline points="14,2 14,8 20,8" />
          </svg>
          <span v-if="node.fileType" class="text-xs">{{ node.fileType.toUpperCase() }}</span>
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
  </div>
</template>
