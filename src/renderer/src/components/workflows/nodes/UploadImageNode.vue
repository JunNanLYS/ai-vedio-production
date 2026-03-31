<script setup lang="ts">
import { ref, computed } from 'vue'
import type { CanvasNode } from '@/types'

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
  contextmenu: [event: MouseEvent]
  mousedown: [event: MouseEvent]
}>()

const MIN_WIDTH = 120
const MIN_HEIGHT = 100

const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)

const nodeStyle = computed(() => ({
  left: `${props.node.x}px`,
  top: `${props.node.y}px`,
  width: `${props.node.width}px`,
  height: `${props.node.height}px`
}))

const handleFileSelect = (e: Event) => {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file && file.type.startsWith('image/')) {
    const reader = new FileReader()
    reader.onload = (event) => {
      emit('update', {
        localImagePath: event.target?.result as string,
        name: file.name,
        fileType: file.name.split('.').pop()?.toLowerCase() || 'png',
        fileSize: file.size
      })
    }
    reader.readAsDataURL(file)
  }
  input.value = ''
}

const handleDrop = (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = false
  const file = e.dataTransfer?.files[0]
  if (file && file.type.startsWith('image/')) {
    const reader = new FileReader()
    reader.onload = (event) => {
      emit('update', {
        localImagePath: event.target?.result as string,
        name: file.name,
        fileType: file.name.split('.').pop()?.toLowerCase() || 'png',
        fileSize: file.size
      })
    }
    reader.readAsDataURL(file)
  }
}

const handleDragOver = (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = true
}

const handleDragLeave = () => {
  isDragging.value = false
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
</script>

<template>
  <div
    class="absolute rounded-xl border-2 cursor-move transition-shadow duration-200 overflow-hidden pointer-events-auto group"
    :class="[
      'bg-orange-50 dark:bg-orange-900/20 border-orange-300 dark:border-orange-700',
      selected ? 'ring-2 ring-blue-500 ring-offset-2 shadow-lg' : 'shadow-md hover:shadow-lg',
      isDragging ? 'border-orange-500 dark:border-orange-500' : ''
    ]"
    :style="nodeStyle"
    @contextmenu="emit('contextmenu', $event)"
    @mousedown="emit('mousedown', $event)"
  >
    <div class="flex flex-col h-full">
      <div
        class="flex items-center gap-2 px-3 py-2 border-b border-orange-200 dark:border-orange-800 bg-white/50 dark:bg-black/20"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          class="text-orange-600 dark:text-orange-400"
        >
          <path d="M8 10V3M5 6L8 3L11 6M3 10V13H13V10" />
        </svg>
        <span class="text-sm font-medium text-zinc-700 dark:text-zinc-300 truncate flex-1">
          {{ node.name || '上传图片' }}
        </span>
        <span v-if="node.fileType" class="text-xs text-zinc-400 dark:text-zinc-500 uppercase">
          .{{ node.fileType }}
        </span>
      </div>

      <div
        class="flex-1 flex items-center justify-center overflow-hidden bg-black/5 dark:bg-black/20 relative"
        @drop="handleDrop"
        @dragover="handleDragOver"
        @dragleave="handleDragLeave"
        @click="fileInputRef?.click()"
      >
        <input
          ref="fileInputRef"
          type="file"
          accept="image/*"
          class="hidden"
          @change="handleFileSelect"
        />

        <img
          v-if="node.localImagePath"
          :src="node.localImagePath"
          :alt="node.name"
          class="w-full h-full object-cover pointer-events-none"
          draggable="false"
        />

        <div
          v-else
          class="flex flex-col items-center justify-center gap-2 text-zinc-400 dark:text-zinc-600 cursor-pointer hover:text-zinc-500 dark:hover:text-zinc-500 transition-colors"
          :class="{ 'text-orange-500 dark:text-orange-400': isDragging }"
        >
          <svg
            width="32"
            height="32"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
          >
            <path d="M8 10V3M5 6L8 3L11 6M3 10V13H13V10" />
          </svg>
          <span class="text-xs">点击或拖拽上传图片</span>
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
