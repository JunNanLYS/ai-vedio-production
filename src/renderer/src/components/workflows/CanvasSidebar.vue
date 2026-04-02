<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Asset, SubCategory, Project } from '@/types'
import { assetsService } from '@/services/assets'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'

const assets = ref<Asset[]>([])
const subCategories = ref<SubCategory[]>([])
const projects = ref<Project[]>([])
const currentProject = ref<Project | null>(null)
const loading = ref(false)
const searchQuery = ref('')
const expandedCategories = ref<Set<string>>(new Set(['prompt', 'image']))
const previewUrls = ref<Map<number, string>>(new Map())

const categories = [
  { key: 'prompt', label: '提示词', icon: 'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z' },
  { key: 'image', label: '图片', icon: 'M19 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2zM8.5 10a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3zM21 15l-5-5L5 21' },
  { key: 'audio', label: '音频', icon: 'M9 18V5l12-2v13M9 18c0 1.66-1.34 3-3 3s-3-1.34-3-3 1.34-3 3-3 3 1.34 3 3zM21 16c0 1.66-1.34 3-3 3s-3-1.34-3-3 1.34-3 3-3 3 1.34 3 3z' },
  { key: 'video', label: '视频', icon: 'M23 7l-7 5 7 5V7zM14 5H3a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2z' },
  { key: 'document', label: '文档', icon: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zM14 2v6h6M16 13H8M16 17H8M10 9H8' }
]

const filteredAssets = computed(() => {
  if (!searchQuery.value) return assets.value
  const query = searchQuery.value.toLowerCase()
  return assets.value.filter(
    (a) => a.name.toLowerCase().includes(query) || a.sub_category.toLowerCase().includes(query)
  )
})

const groupedAssets = computed(() => {
  const groups: Record<string, Asset[]> = {}
  categories.forEach((cat) => {
    groups[cat.key] = filteredAssets.value.filter((a) => a.category === cat.key)
  })
  return groups
})

const fetchProjects = async (): Promise<void> => {
  try {
    projects.value = await assetsService.getProjects()
  } catch (error) {
    console.error('获取项目列表失败:', error)
  }
}

const fetchCurrentProject = async (): Promise<void> => {
  try {
    const result = await assetsService.getCurrentProject()
    currentProject.value = result.project
  } catch (error) {
    console.error('获取当前项目失败:', error)
  }
}

const handleProjectSwitch = async (projectId: unknown): Promise<void> => {
  if (!projectId) return
  try {
    await assetsService.switchProject(parseInt(String(projectId), 10))
    await fetchCurrentProject()
    await fetchData()
  } catch (error) {
    console.error('切换项目失败:', error)
  }
}

const fetchData = async (): Promise<void> => {
  loading.value = true
  try {
    const projectData = await assetsService.getCurrentProject()
    if (projectData.project) {
      currentProject.value = projectData.project
      const [assetsData, subCategoriesData] = await Promise.all([
        assetsService.getAll(),
        assetsService.getSubCategories()
      ])
      assets.value = assetsData
      subCategories.value = subCategoriesData

      const imageAssets = assetsData.filter(
        (a) =>
          a.category === 'image' &&
          ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'].includes(a.file_type.toLowerCase())
      )
      const urlPromises = imageAssets.map(async (asset) => {
        try {
          const url = await assetsService.getPreviewUrl(asset.id)
          return { id: asset.id, url }
        } catch {
          return { id: asset.id, url: '' }
        }
      })
      const urls = await Promise.all(urlPromises)
      urls.forEach(({ id, url }) => {
        if (url) {
          previewUrls.value.set(id, url)
        }
      })
    }
  } catch (error) {
    console.error('获取资产数据失败:', error)
  } finally {
    loading.value = false
  }
}

const toggleCategory = (categoryKey: string): void => {
  if (expandedCategories.value.has(categoryKey)) {
    expandedCategories.value.delete(categoryKey)
  } else {
    expandedCategories.value.add(categoryKey)
  }
}

const handleDragStart = (e: DragEvent, asset: Asset): void => {
  if (e.dataTransfer) {
    e.dataTransfer.setData('application/json', JSON.stringify(asset))
    e.dataTransfer.effectAllowed = 'copy'
  }
}

const isImage = (fileType: string): boolean => {
  const imageTypes = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp']
  return imageTypes.includes(fileType.toLowerCase())
}

const getPreviewUrl = (assetId: number): string => {
  return previewUrls.value.get(assetId) || ''
}

onMounted(() => {
  fetchProjects()
  fetchData()
})
</script>

<template>
  <div
    class="w-64 h-full flex flex-col bg-white dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800"
  >
    <div class="p-4 border-b border-zinc-200 dark:border-zinc-800">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-semibold text-zinc-900 dark:text-zinc-100">资产库</h3>
      </div>

      <Select
        v-if="projects.length > 0"
        :model-value="currentProject?.id.toString()"
        @update:model-value="handleProjectSwitch"
      >
        <SelectTrigger class="h-8 text-sm mb-3">
          <SelectValue placeholder="选择项目" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem v-for="project in projects" :key="project.id" :value="project.id.toString()">
            {{ project.name }}
          </SelectItem>
        </SelectContent>
      </Select>

      <Input v-model="searchQuery" placeholder="搜索资产..." class="h-8 text-sm" />
    </div>

    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div
        class="w-6 h-6 border-2 border-zinc-200 dark:border-zinc-700 border-t-zinc-600 dark:border-t-zinc-300 rounded-full animate-spin"
      ></div>
    </div>

    <div v-else class="flex-1 overflow-y-auto">
      <div
        v-for="category in categories"
        :key="category.key"
        class="border-b border-zinc-100 dark:border-zinc-800 last:border-b-0"
      >
        <button
          class="w-full flex items-center gap-2 px-4 py-3 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors"
          @click="toggleCategory(category.key)"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            class="text-zinc-500"
          >
            <path :d="category.icon" />
          </svg>
          <span class="text-sm font-medium text-zinc-700 dark:text-zinc-300 flex-1 text-left">
            {{ category.label }}
          </span>
          <span class="text-xs text-zinc-400 dark:text-zinc-500 mr-2">
            {{ groupedAssets[category.key]?.length || 0 }}
          </span>
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
            class="text-zinc-400 transition-transform"
            :class="{ 'rotate-180': expandedCategories.has(category.key) }"
          >
            <path d="M3 4.5L6 7.5L9 4.5" />
          </svg>
        </button>

        <div v-if="expandedCategories.has(category.key)" class="px-2 pb-2">
          <div
            v-for="asset in groupedAssets[category.key]"
            :key="asset.id"
            draggable="true"
            class="flex items-center gap-2 p-2 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 cursor-grab active:cursor-grabbing transition-colors group"
            @dragstart="handleDragStart($event, asset)"
          >
            <div
              class="w-10 h-10 rounded-lg overflow-hidden bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center flex-shrink-0"
            >
              <img
                v-if="isImage(asset.file_type) && getPreviewUrl(asset.id)"
                :src="getPreviewUrl(asset.id)"
                :alt="asset.name"
                class="w-full h-full object-cover"
                @error="($event.target as HTMLImageElement).style.display = 'none'"
              />
              <svg
                v-else
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
                class="text-zinc-400"
              >
                <path
                  v-if="asset.category === 'prompt'"
                  d="M12 2L2 7L12 12L22 7L12 2Z M2 17L12 22L22 17 M2 12L12 17L22 12"
                />
                <path
                  v-else-if="asset.category === 'image'"
                  d="M4 4H20V16H4V4Z M4 16L8 12L12 16L16 10L20 14V16H4V16Z"
                />
                <path
                  v-else-if="asset.category === 'audio'"
                  d="M9 18V5L21 3V16 M9 18C9 19.6569 7.65685 21 6 21C4.34315 21 3 19.6569 3 18C3 16.3431 4.34315 15 6 15C7.65685 15 9 16.3431 9 18Z M21 16C21 17.6569 19.6569 19 18 19C16.3431 19 15 17.6569 15 16C15 14.3431 16.3431 13 18 13C19.6569 13 21 14.3431 21 16Z"
                />
                <path
                  v-else-if="asset.category === 'video'"
                  d="M4 4H20V16H4V4Z M10 8L16 12L10 16V8Z"
                />
                <path v-else d="M6 2H14L20 8V22H6V2Z M14 2V8H20" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-zinc-700 dark:text-zinc-300 truncate">{{ asset.name }}</p>
              <p class="text-xs text-zinc-400 dark:text-zinc-500">{{ asset.sub_category }}</p>
            </div>
            <svg
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              class="text-zinc-300 dark:text-zinc-600 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <path d="M3 7H11M7 3V11" />
            </svg>
          </div>

          <div
            v-if="!groupedAssets[category.key]?.length"
            class="py-4 text-center text-sm text-zinc-400 dark:text-zinc-600"
          >
            暂无资产
          </div>
        </div>
      </div>

      <div v-if="assets.length === 0 && !loading" class="py-8 text-center">
        <div class="text-zinc-300 dark:text-zinc-700 mb-2">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none" class="mx-auto">
            <rect
              x="8"
              y="8"
              width="32"
              height="32"
              rx="8"
              stroke="currentColor"
              stroke-width="2"
              stroke-dasharray="4 2"
            />
            <path
              d="M16 24H32M24 16V32"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
            />
          </svg>
        </div>
        <p class="text-sm text-zinc-400 dark:text-zinc-600">暂无资产</p>
        <p class="text-xs text-zinc-300 dark:text-zinc-700 mt-1">请先在资产页面上传资产</p>
      </div>
    </div>
  </div>
</template>
