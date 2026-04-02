<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import type { CanvasNode, CanvasConnection, Asset } from '@/types'
import CanvasNodeComponent from './CanvasNode.vue'
import { ContextMenu } from '@/components/ui/context-menu'

interface Props {
  nodes: CanvasNode[]
  connections: CanvasConnection[]
  initialViewport?: { x: number; y: number; scale: number }
}

const props = withDefaults(defineProps<Props>(), {
  initialViewport: () => ({ x: 0, y: 0, scale: 1 })
})

const emit = defineEmits<{
  nodeMove: [id: string, x: number, y: number]
  nodeResize: [id: string, width: number, height: number, x?: number, y?: number]
  nodeSelect: [id: string | null]
  nodeDelete: [id: string]
  nodesDelete: [ids: string[]]
  nodeUpdate: [id: string, updates: Partial<CanvasNode>]
  nodeCreate: [type: string, x: number, y: number]
  connectionCreate: [sourceId: string, targetId: string]
  connectionDelete: [id: string]
  assetDrop: [asset: Asset, x: number, y: number]
  nodeGenerate: [id: string]
  viewportChange: [viewport: { x: number; y: number; scale: number }]
  nodeConvertToAsset: [nodeId: string, assetId: number]
  nodeOpenFile: [node: CanvasNode]
  nodeOpenFolder: [node: CanvasNode]
  nodeDeleteWithConfirm: [node: CanvasNode]
  nodesPaste: [nodes: CanvasNode[], position: { x: number; y: number }]
}>()

const canvasRef = ref<HTMLDivElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)
const contextMenuRef = ref<InstanceType<typeof ContextMenu> | null>(null)

const viewport = ref({
  x: props.initialViewport.x,
  y: props.initialViewport.y,
  scale: props.initialViewport.scale
})

watch(
  () => props.initialViewport,
  (newViewport) => {
    viewport.value = { ...newViewport }
  },
  { deep: true }
)

const MIN_SCALE = 0.1
const MAX_SCALE = 3
const SCALE_STEP = 0.1

const emitViewportChange = () => {
  emit('viewportChange', { ...viewport.value })
}

const isPanning = ref(false)
const panStart = ref({ x: 0, y: 0 })
const selectedNodeId = ref<string | null>(null)
const selectedNodeIds = ref<Set<string>>(new Set())
const draggedNode = ref<{ id: string; offsetX: number; offsetY: number } | null>(null)
const selectedConnectionId = ref<string | null>(null)

const isConnecting = ref(false)
const connectingFrom = ref<string | null>(null)
const connectingLine = ref<{
  x1: number
  y1: number
  x2: number
  y2: number
  sourceOnRight: boolean
} | null>(null)

const isSelecting = ref(false)
const selectionBox = ref<{ startX: number; startY: number; endX: number; endY: number } | null>(
  null
)

const clipboard = ref<CanvasNode[]>([])
const mousePosition = ref({ x: 0, y: 0 })

const canvasTransform = computed(() => {
  return `translate(${viewport.value.x}px, ${viewport.value.y}px) scale(${viewport.value.scale})`
})

const gridBackground = computed(() => {
  const gridSize = 20 * viewport.value.scale
  const offsetX = viewport.value.x % gridSize
  const offsetY = viewport.value.y % gridSize
  return {
    backgroundPosition: `${offsetX}px ${offsetY}px`,
    backgroundSize: `${gridSize}px ${gridSize}px`
  }
})

const getBezierPath = (
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  sourceOnRight: boolean = true
): string => {
  const dx = Math.abs(x2 - x1)
  const controlOffset = Math.max(dx * 0.5, 50)

  if (sourceOnRight) {
    const cp1x = x1 + controlOffset
    const cp2x = x2 - controlOffset
    return `M ${x1} ${y1} C ${cp1x} ${y1}, ${cp2x} ${y2}, ${x2} ${y2}`
  } else {
    const cp1x = x1 - controlOffset
    const cp2x = x2 + controlOffset
    return `M ${x1} ${y1} C ${cp1x} ${y1}, ${cp2x} ${y2}, ${x2} ${y2}`
  }
}

const getConnectionPath = (connection: CanvasConnection): string | null => {
  const sourceNode = props.nodes.find((n) => n.id === connection.sourceId)
  const targetNode = props.nodes.find((n) => n.id === connection.targetId)

  if (!sourceNode || !targetNode) return null

  const x1 = sourceNode.x + sourceNode.width
  const y1 = sourceNode.y + sourceNode.height / 2
  const x2 = targetNode.x
  const y2 = targetNode.y + targetNode.height / 2

  return getBezierPath(x1, y1, x2, y2, true)
}

const getConnectionLabelPosition = (
  connection: CanvasConnection
): { x: number; y: number } | null => {
  const sourceNode = props.nodes.find((n) => n.id === connection.sourceId)
  const targetNode = props.nodes.find((n) => n.id === connection.targetId)

  if (!sourceNode || !targetNode) return null

  const x1 = sourceNode.x + sourceNode.width
  const y1 = sourceNode.y + sourceNode.height / 2
  const x2 = targetNode.x
  const y2 = targetNode.y + targetNode.height / 2

  const midX = (x1 + x2) / 2
  const midY = (y1 + y2) / 2

  return { x: midX, y: midY }
}

const contextMenuItems = [
  { label: '上传图片', icon: 'upload', action: () => {} },
  { label: '生成图片', icon: 'sparkles', action: () => {} },
  { label: '宫格图', icon: 'grid', action: () => {} },
  { label: '文本注释', icon: 'text', action: () => {} }
]

const contextMenuPosition = ref({ x: 0, y: 0 })

const findScrollableParent = (element: HTMLElement | null): HTMLElement | null => {
  if (!element || element === containerRef.value) return null
  
  const style = window.getComputedStyle(element)
  const overflowY = style.overflowY
  const overflow = style.overflow
  
  if ((overflowY === 'auto' || overflowY === 'scroll' || overflow === 'auto' || overflow === 'scroll') &&
      element.scrollHeight > element.clientHeight) {
    return element
  }
  
  return findScrollableParent(element.parentElement)
}

const canScroll = (element: HTMLElement, e: WheelEvent): boolean => {
  const style = window.getComputedStyle(element)
  const overflowY = style.overflowY
  const overflow = style.overflow
  
  if (overflowY !== 'auto' && overflowY !== 'scroll' && overflow !== 'auto' && overflow !== 'scroll') {
    return false
  }
  
  if (element.scrollHeight <= element.clientHeight) {
    return false
  }
  
  const atTop = element.scrollTop === 0
  const atBottom = element.scrollTop + element.clientHeight >= element.scrollHeight - 1
  
  if (e.deltaY < 0 && atTop) {
    return false
  }
  if (e.deltaY > 0 && atBottom) {
    return false
  }
  
  return true
}

const handleWheel = (e: WheelEvent) => {
  const target = e.target as HTMLElement
  const scrollableParent = findScrollableParent(target)
  
  if (scrollableParent && canScroll(scrollableParent, e)) {
    return
  }
  
  if (e.ctrlKey || e.metaKey) {
    e.preventDefault()
    const delta = e.deltaY > 0 ? -SCALE_STEP : SCALE_STEP
    const newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, viewport.value.scale + delta))

    if (containerRef.value) {
      const rect = containerRef.value.getBoundingClientRect()
      const mouseX = e.clientX - rect.left
      const mouseY = e.clientY - rect.top

      const scaleRatio = newScale / viewport.value.scale
      viewport.value.x = mouseX - (mouseX - viewport.value.x) * scaleRatio
      viewport.value.y = mouseY - (mouseY - viewport.value.y) * scaleRatio
    }

    viewport.value.scale = newScale
    emitViewportChange()
  } else {
    viewport.value.x -= e.deltaX
    viewport.value.y -= e.deltaY
    emitViewportChange()
  }
}

const handleMouseDown = (e: MouseEvent) => {
  if (e.button === 1 || (e.button === 0 && e.altKey)) {
    isPanning.value = true
    panStart.value = { x: e.clientX - viewport.value.x, y: e.clientY - viewport.value.y }
    e.preventDefault()
  } else if (e.button === 0) {
    const target = e.target as HTMLElement
    const isOnNode = target.closest('.pointer-events-auto') !== null
    const isOnZoomControl = target.closest('.absolute.bottom-4') !== null

    if (!isOnNode && !isOnZoomControl) {
      selectedNodeId.value = null
      selectedNodeIds.value.clear()
      selectedConnectionId.value = null
      emit('nodeSelect', null)
      cancelConnecting()

      if (containerRef.value) {
        const rect = containerRef.value.getBoundingClientRect()
        const x = (e.clientX - rect.left - viewport.value.x) / viewport.value.scale
        const y = (e.clientY - rect.top - viewport.value.y) / viewport.value.scale
        isSelecting.value = true
        selectionBox.value = { startX: x, startY: y, endX: x, endY: y }
      }
    }
  }
}

const handleContextMenu = (e: MouseEvent) => {
  if (e.target === canvasRef.value || e.target === containerRef.value) {
    e.preventDefault()

    if (containerRef.value) {
      const rect = containerRef.value.getBoundingClientRect()
      const x = (e.clientX - rect.left - viewport.value.x) / viewport.value.scale
      const y = (e.clientY - rect.top - viewport.value.y) / viewport.value.scale
      contextMenuPosition.value = { x, y }

      contextMenuItems[0].action = () =>
        emit('nodeCreate', 'upload-image', contextMenuPosition.value.x, contextMenuPosition.value.y)
      contextMenuItems[1].action = () =>
        emit(
          'nodeCreate',
          'generate-image',
          contextMenuPosition.value.x,
          contextMenuPosition.value.y
        )
      contextMenuItems[2].action = () =>
        emit(
          'nodeCreate',
          'grid-image',
          contextMenuPosition.value.x,
          contextMenuPosition.value.y
        )
      contextMenuItems[3].action = () =>
        emit(
          'nodeCreate',
          'text-annotation',
          contextMenuPosition.value.x,
          contextMenuPosition.value.y
        )

      contextMenuRef.value?.show(e.clientX, e.clientY)
    }
  }
}

const handleMouseMove = (e: MouseEvent) => {
  if (containerRef.value) {
    const rect = containerRef.value.getBoundingClientRect()
    mousePosition.value = {
      x: (e.clientX - rect.left - viewport.value.x) / viewport.value.scale,
      y: (e.clientY - rect.top - viewport.value.y) / viewport.value.scale
    }
  }

  if (isPanning.value) {
    viewport.value.x = e.clientX - panStart.value.x
    viewport.value.y = e.clientY - panStart.value.y
    emitViewportChange()
  } else if (isSelecting.value && selectionBox.value && containerRef.value) {
    const rect = containerRef.value.getBoundingClientRect()
    const x = (e.clientX - rect.left - viewport.value.x) / viewport.value.scale
    const y = (e.clientY - rect.top - viewport.value.y) / viewport.value.scale
    selectionBox.value.endX = x
    selectionBox.value.endY = y
  } else if (draggedNode.value) {
    const node = props.nodes.find((n) => n.id === draggedNode.value!.id)
    if (node) {
      const newX = (e.clientX - viewport.value.x - draggedNode.value.offsetX) / viewport.value.scale
      const newY = (e.clientY - viewport.value.y - draggedNode.value.offsetY) / viewport.value.scale
      const deltaX = newX - node.x
      const deltaY = newY - node.y

      if (selectedNodeIds.value.size > 1 && selectedNodeIds.value.has(draggedNode.value.id)) {
        selectedNodeIds.value.forEach((id) => {
          if (id !== draggedNode.value!.id) {
            const n = props.nodes.find((n) => n.id === id)
            if (n) {
              emit('nodeMove', id, n.x + deltaX, n.y + deltaY)
            }
          }
        })
      }
      emit('nodeMove', draggedNode.value.id, newX, newY)
    }
  } else if (isConnecting.value && connectingFrom.value && containerRef.value) {
    const fromNode = props.nodes.find((n) => n.id === connectingFrom.value)
    if (fromNode) {
      const rect = containerRef.value.getBoundingClientRect()
      const mouseX = (e.clientX - rect.left - viewport.value.x) / viewport.value.scale
      const mouseY = (e.clientY - rect.top - viewport.value.y) / viewport.value.scale

      connectingLine.value = {
        x1: fromNode.x + fromNode.width,
        y1: fromNode.y + fromNode.height / 2,
        x2: mouseX,
        y2: mouseY,
        sourceOnRight: true
      }
    }
  }
}

const handleMouseUp = () => {
  if (isSelecting.value && selectionBox.value) {
    const minX = Math.min(selectionBox.value.startX, selectionBox.value.endX)
    const maxX = Math.max(selectionBox.value.startX, selectionBox.value.endX)
    const minY = Math.min(selectionBox.value.startY, selectionBox.value.endY)
    const maxY = Math.max(selectionBox.value.startY, selectionBox.value.endY)

    selectedNodeIds.value.clear()
    props.nodes.forEach((node) => {
      const nodeRight = node.x + node.width
      const nodeBottom = node.y + node.height

      if (node.x < maxX && nodeRight > minX && node.y < maxY && nodeBottom > minY) {
        selectedNodeIds.value.add(node.id)
      }
    })

    if (selectedNodeIds.value.size === 1) {
      const id = Array.from(selectedNodeIds.value)[0]
      selectedNodeId.value = id
      emit('nodeSelect', id)
    } else {
      selectedNodeId.value = null
      emit('nodeSelect', null)
    }

    isSelecting.value = false
    selectionBox.value = null
  }

  isPanning.value = false
  draggedNode.value = null
}

const handleNodeMouseDown = (e: MouseEvent, nodeId: string) => {
  if (e.button !== 0) return

  const node = props.nodes.find((n) => n.id === nodeId)
  if (!node) return

  selectedNodeId.value = nodeId
  emit('nodeSelect', nodeId)

  const nodeX = node.x * viewport.value.scale + viewport.value.x
  const nodeY = node.y * viewport.value.scale + viewport.value.y

  draggedNode.value = {
    id: nodeId,
    offsetX: e.clientX - nodeX,
    offsetY: e.clientY - nodeY
  }

  e.stopPropagation()
}

const handleNodeResize = (
  id: string,
  data: { width: number; height: number; x?: number; y?: number }
) => {
  emit('nodeResize', id, data.width, data.height, data.x, data.y)
}

const handleNodeUpdate = (id: string, updates: Partial<CanvasNode>) => {
  emit('nodeUpdate', id, updates)
}

const handleNodeDeleteWithConfirm = (id: string) => {
  const node = props.nodes.find((n) => n.id === id)
  if (node) {
    emit('nodeDeleteWithConfirm', node)
  }
}

const startConnecting = (nodeId: string) => {
  isConnecting.value = true
  connectingFrom.value = nodeId
}

const cancelConnecting = () => {
  isConnecting.value = false
  connectingFrom.value = null
  connectingLine.value = null
}

const finishConnecting = (targetId: string) => {
  if (connectingFrom.value && connectingFrom.value !== targetId) {
    const sourceNode = props.nodes.find((n) => n.id === connectingFrom.value)
    const targetNode = props.nodes.find((n) => n.id === targetId)

    if (sourceNode && targetNode) {
      const canConnect =
        ((sourceNode.type === 'upload-image' ||
          (sourceNode.type === 'asset' && sourceNode.category === 'image') ||
          sourceNode.type === 'generated-image') &&
          (targetNode.type === 'generate-image' || targetNode.type === 'grid-image')) ||
        ((sourceNode.type === 'generate-image' || sourceNode.type === 'grid-image') && targetNode.type === 'generated-image')

      if (canConnect) {
        emit('connectionCreate', connectingFrom.value, targetId)
      }
    }
  }
  cancelConnecting()
}

const handleKeyDown = (e: KeyboardEvent) => {
  const activeElement = document.activeElement
  const isInputFocused =
    activeElement &&
    (activeElement.tagName === 'INPUT' ||
      activeElement.tagName === 'TEXTAREA' ||
      (activeElement as HTMLElement).isContentEditable)

  if (isInputFocused) return

  if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
    e.preventDefault()
    if (selectedNodeIds.value.size > 0) {
      const nodesToCopy = props.nodes.filter((n) => selectedNodeIds.value.has(n.id))
      clipboard.value = JSON.parse(JSON.stringify(nodesToCopy))
    } else if (selectedNodeId.value) {
      const nodeToCopy = props.nodes.find((n) => n.id === selectedNodeId.value)
      if (nodeToCopy) {
        clipboard.value = [JSON.parse(JSON.stringify(nodeToCopy))]
      }
    }
    return
  }

  if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
    e.preventDefault()
    if (clipboard.value.length > 0) {
      const nodesToPaste = JSON.parse(JSON.stringify(clipboard.value))
      emit('nodesPaste', nodesToPaste, { ...mousePosition.value })
    }
    return
  }

  if (e.key === 'Delete' || e.key === 'Backspace') {
    if (selectedConnectionId.value) {
      emit('connectionDelete', selectedConnectionId.value)
      selectedConnectionId.value = null
    } else if (selectedNodeIds.value.size > 1) {
      emit('nodesDelete', Array.from(selectedNodeIds.value))
      selectedNodeIds.value.clear()
      selectedNodeId.value = null
    } else if (selectedNodeId.value) {
      emit('nodeDelete', selectedNodeId.value)
      selectedNodeId.value = null
    }
  }

  if (e.key === 'Enter') {
    if (selectedConnectionId.value) {
      emit('connectionDelete', selectedConnectionId.value)
      selectedConnectionId.value = null
    }
  }

  if (e.key === 'Escape') {
    cancelConnecting()
    selectedNodeIds.value.clear()
    selectedConnectionId.value = null
  }

  if (e.key === '0' && (e.ctrlKey || e.metaKey)) {
    e.preventDefault()
    resetViewport()
  }
}

const resetViewport = () => {
  viewport.value = { x: 0, y: 0, scale: 1 }
  emitViewportChange()
}

const handleDragOver = (e: DragEvent) => {
  e.preventDefault()
  e.dataTransfer!.dropEffect = 'copy'
}

const handleDrop = (e: DragEvent) => {
  e.preventDefault()

  const assetData = e.dataTransfer?.getData('application/json')
  if (!assetData) return

  try {
    const asset = JSON.parse(assetData) as Asset

    if (containerRef.value) {
      const rect = containerRef.value.getBoundingClientRect()
      const x = (e.clientX - rect.left - viewport.value.x) / viewport.value.scale
      const y = (e.clientY - rect.top - viewport.value.y) / viewport.value.scale

      emit('assetDrop', asset, x, y)
    }
  } catch (error) {
    console.error('解析拖拽数据失败:', error)
  }
}

const zoomIn = () => {
  viewport.value.scale = Math.min(MAX_SCALE, viewport.value.scale + SCALE_STEP)
  emitViewportChange()
}

const zoomOut = () => {
  viewport.value.scale = Math.max(MIN_SCALE, viewport.value.scale - SCALE_STEP)
  emitViewportChange()
}

const fitToNodes = () => {
  if (props.nodes.length === 0) {
    resetViewport()
    return
  }

  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity

  props.nodes.forEach((node) => {
    minX = Math.min(minX, node.x)
    minY = Math.min(minY, node.y)
    maxX = Math.max(maxX, node.x + node.width)
    maxY = Math.max(maxY, node.y + node.height)
  })

  const padding = 50
  const contentWidth = maxX - minX + padding * 2
  const contentHeight = maxY - minY + padding * 2

  if (containerRef.value) {
    const containerWidth = containerRef.value.clientWidth
    const containerHeight = containerRef.value.clientHeight

    const scaleX = containerWidth / contentWidth
    const scaleY = containerHeight / contentHeight
    const scale = Math.min(scaleX, scaleY, 1)

    viewport.value.scale = scale
    viewport.value.x = (containerWidth - contentWidth * scale) / 2 - minX * scale + padding * scale
    viewport.value.y =
      (containerHeight - contentHeight * scale) / 2 - minY * scale + padding * scale
    emitViewportChange()
  }
}

const getReferenceImages = (nodeId: string) => {
  const node = props.nodes.find((n) => n.id === nodeId)
  if (!node || (node.type !== 'generate-image' && node.type !== 'grid-image')) return undefined

  const connections = props.connections.filter((c) => c.targetId === nodeId)
  return connections.map((c, index) => {
    const sourceNode = props.nodes.find((n) => n.id === c.sourceId)
    let previewUrl: string | undefined
    let fileSize: number | undefined

    if (sourceNode) {
      if (sourceNode.localImagePath) {
        previewUrl = sourceNode.localImagePath
      } else if (sourceNode.filePath) {
        previewUrl = `asset:///${sourceNode.filePath}`
      }
      fileSize = sourceNode.fileSize
    }

    return {
      nodeId: c.sourceId,
      order: c.order || index + 1,
      previewUrl,
      fileSize
    }
  })
}

const handleConnectionClick = (e: MouseEvent, connectionId: string) => {
  e.stopPropagation()
  selectedConnectionId.value = connectionId
  selectedNodeId.value = null
  selectedNodeIds.value.clear()
  emit('nodeSelect', null)
}

const selectionBoxStyle = computed(() => {
  if (!selectionBox.value) return null

  const minX = Math.min(selectionBox.value.startX, selectionBox.value.endX)
  const maxX = Math.max(selectionBox.value.startX, selectionBox.value.endX)
  const minY = Math.min(selectionBox.value.startY, selectionBox.value.endY)
  const maxY = Math.max(selectionBox.value.startY, selectionBox.value.endY)

  return {
    left: `${minX}px`,
    top: `${minY}px`,
    width: `${maxX - minX}px`,
    height: `${maxY - minY}px`
  }
})

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})

defineExpose({
  resetViewport,
  zoomIn,
  zoomOut,
  fitToNodes,
  startConnecting,
  cancelConnecting
})
</script>

<template>
  <div
    ref="containerRef"
    class="relative w-full h-full overflow-hidden select-none"
    :class="['bg-zinc-50 dark:bg-zinc-900', 'bg-grid-pattern']"
    :style="gridBackground"
    @wheel="handleWheel"
    @mousedown="handleMouseDown"
    @mousemove="handleMouseMove"
    @mouseup="handleMouseUp"
    @mouseleave="handleMouseUp"
    @dragover="handleDragOver"
    @drop="handleDrop"
    @contextmenu="handleContextMenu"
  >
    <div
      ref="canvasRef"
      class="absolute top-0 left-0 w-full h-full pointer-events-none"
      :style="{ transform: canvasTransform, transformOrigin: '0 0' }"
    >
      <svg class="absolute" style="width: 50000px; height: 50000px; left: -20000px; top: -20000px; overflow: visible" viewBox="-20000 -20000 50000 50000">
        <g
          v-for="connection in connections"
          :key="connection.id"
          class="pointer-events-auto cursor-pointer"
        >
          <path
            v-if="getConnectionPath(connection)"
            :d="getConnectionPath(connection)!"
            fill="none"
            stroke="currentColor"
            :stroke-width="selectedConnectionId === connection.id ? 4 : 2"
            :class="[
              connection.type === 'reference'
                ? 'text-purple-400 dark:text-purple-600'
                : 'text-zinc-400 dark:text-zinc-600',
              selectedConnectionId === connection.id ? 'text-blue-500 dark:text-blue-400' : ''
            ]"
            @click="handleConnectionClick($event, connection.id)"
          />
          <g
            v-if="
              connection.type === 'reference' &&
              connection.order &&
              getConnectionLabelPosition(connection)
            "
          >
            <circle
              :cx="getConnectionLabelPosition(connection)!.x"
              :cy="getConnectionLabelPosition(connection)!.y"
              r="12"
              fill="currentColor"
              class="text-purple-500"
            />
            <text
              :x="getConnectionLabelPosition(connection)!.x"
              :y="getConnectionLabelPosition(connection)!.y + 4"
              text-anchor="middle"
              fill="white"
              font-size="11"
              font-weight="bold"
            >
              {{ connection.order }}
            </text>
          </g>
        </g>

        <path
          v-if="isConnecting && connectingLine"
          :d="
            getBezierPath(
              connectingLine.x1,
              connectingLine.y1,
              connectingLine.x2,
              connectingLine.y2,
              connectingLine.sourceOnRight
            )
          "
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-dasharray="5,5"
          class="text-purple-400"
        />
      </svg>

      <CanvasNodeComponent
        v-for="node in nodes"
        :key="node.id"
        :node="node"
        :selected="selectedNodeId === node.id || selectedNodeIds.has(node.id)"
        :scale="viewport.scale"
        :reference-images="getReferenceImages(node.id)"
        class="pointer-events-auto"
        @mousedown="handleNodeMouseDown($event, node.id)"
        @resize="handleNodeResize(node.id, $event)"
        @update="handleNodeUpdate(node.id, $event)"
        @generate="emit('nodeGenerate', node.id)"
        @convert-to-asset="emit('nodeConvertToAsset', node.id, $event)"
        @delete="handleNodeDeleteWithConfirm"
        @open-file="emit('nodeOpenFile', $event)"
        @open-folder="emit('nodeOpenFolder', $event)"
      />

      <div
        v-if="isSelecting && selectionBoxStyle"
        class="absolute border-2 border-blue-500 bg-blue-500/10 pointer-events-none"
        :style="selectionBoxStyle"
      ></div>

      <div
        v-for="node in nodes.filter(
          (n) => n.type === 'upload-image' || (n.type === 'asset' && n.category === 'image') || n.type === 'generate-image' || n.type === 'grid-image' || n.type === 'generated-image'
        )"
        :key="'connect-' + node.id"
        class="absolute pointer-events-auto"
        :style="{
          left: `${node.x + node.width - 8}px`,
          top: `${node.y + node.height / 2 - 8}px`
        }"
      >
        <button
          class="w-4 h-4 rounded-full text-white flex items-center justify-center transition-colors shadow-sm"
          :class="node.type === 'generate-image' || node.type === 'grid-image' || node.type === 'generated-image' ? 'bg-green-500 hover:bg-green-600' : 'bg-purple-500 hover:bg-purple-600'"
          @mousedown.stop
          @click.stop="startConnecting(node.id)"
        >
          <svg
            width="8"
            height="8"
            viewBox="0 0 8 8"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
          >
            <circle cx="4" cy="4" r="2" />
          </svg>
        </button>
      </div>

      <div
        v-for="node in nodes.filter((n) => n.type === 'generate-image' || n.type === 'grid-image')"
        :key="'target-' + node.id"
        class="absolute pointer-events-auto"
        :style="{
          left: `${node.x - 12}px`,
          top: `${node.y + node.height / 2 - 12}px`
        }"
        @click.stop="finishConnecting(node.id)"
      >
        <div
          class="w-6 h-6 rounded-full border-2 border-dashed flex items-center justify-center transition-colors"
          :class="
            isConnecting
              ? 'bg-purple-100 border-purple-500 dark:bg-purple-900/50'
              : 'border-zinc-300 dark:border-zinc-700'
          "
        >
          <svg
            width="10"
            height="10"
            viewBox="0 0 10 10"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
            class="text-zinc-400"
          >
            <path d="M5 2V8M2 5H8" />
          </svg>
        </div>
      </div>
    </div>

    <div
      class="absolute bottom-4 right-4 flex items-center gap-2 bg-white dark:bg-zinc-800 rounded-xl shadow-lg p-2"
    >
      <button
        class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-700 transition-colors"
        @click="zoomOut"
        title="缩小"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          class="text-zinc-600 dark:text-zinc-400"
        >
          <path d="M3 8H13" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
        </svg>
      </button>
      <span class="text-sm text-zinc-600 dark:text-zinc-400 min-w-[50px] text-center">
        {{ Math.round(viewport.scale * 100) }}%
      </span>
      <button
        class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-700 transition-colors"
        @click="zoomIn"
        title="放大"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          class="text-zinc-600 dark:text-zinc-400"
        >
          <path d="M8 3V13M3 8H13" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
        </svg>
      </button>
      <div class="w-px h-6 bg-zinc-200 dark:bg-zinc-700"></div>
      <button
        class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-700 transition-colors"
        @click="fitToNodes"
        title="适应画布"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          class="text-zinc-600 dark:text-zinc-400"
        >
          <path
            d="M2 5V2H5M11 2H14V5M14 11V14H11M5 14H2V11"
            stroke="currentColor"
            stroke-width="1.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
      <button
        class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-700 transition-colors"
        @click="resetViewport"
        title="重置视图"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          class="text-zinc-600 dark:text-zinc-400"
        >
          <circle cx="8" cy="8" r="5" stroke="currentColor" stroke-width="1.5" />
          <circle cx="8" cy="8" r="1" fill="currentColor" />
        </svg>
      </button>
    </div>

    <div
      v-if="nodes.length === 0"
      class="absolute inset-0 flex items-center justify-center pointer-events-none"
    >
      <div class="text-center">
        <div class="text-zinc-300 dark:text-zinc-700 mb-2">
          <svg width="64" height="64" viewBox="0 0 64 64" fill="none" class="mx-auto">
            <rect
              x="8"
              y="8"
              width="48"
              height="48"
              rx="8"
              stroke="currentColor"
              stroke-width="2"
              stroke-dasharray="4 2"
            />
            <path
              d="M24 32H40M32 24V40"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
            />
          </svg>
        </div>
        <p class="text-zinc-400 dark:text-zinc-600">右键画布创建节点</p>
        <p class="text-sm text-zinc-300 dark:text-zinc-700 mt-1">或从资产库拖拽资产到画布</p>
      </div>
    </div>

    <ContextMenu ref="contextMenuRef" :items="contextMenuItems" />
  </div>
</template>

<style scoped>
.bg-grid-pattern {
  background-image:
    linear-gradient(to right, var(--grid-color) 1px, transparent 1px),
    linear-gradient(to bottom, var(--grid-color) 1px, transparent 1px);
  --grid-color: theme('colors.zinc.200');
}

.dark .bg-grid-pattern {
  --grid-color: theme('colors.zinc.800');
}
</style>
