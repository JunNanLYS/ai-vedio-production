<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { FolderOpen, Upload, AlertCircle, FolderSearch } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import CategoryTree from '@/components/assets/CategoryTree.vue'
import AssetList from '@/components/assets/AssetList.vue'
import UploadDialog from '@/components/assets/UploadDialog.vue'
import NewProjectDialog from '@/components/assets/NewProjectDialog.vue'
import LoadProjectDialog from '@/components/assets/LoadProjectDialog.vue'
import ProjectSelector from '@/components/assets/ProjectSelector.vue'
import { assetsService } from '@/services/assets'
import type { Asset, Project } from '@/types'

const assets = ref<Asset[]>([])
const projects = ref<Project[]>([])
const currentProject = ref<Project | null>(null)
const loading = ref(false)
const selectedCategory = ref<string | null>(null)
const selectedSubCategory = ref<string | null>(null)
const selectedAssetIds = ref<number[]>([])

const showUploadDialog = ref(false)
const showNewProjectDialog = ref(false)
const showLoadProjectDialog = ref(false)
const categoryTreeRef = ref<InstanceType<typeof CategoryTree> | null>(null)
const loadProjectDialogRef = ref<InstanceType<typeof LoadProjectDialog> | null>(null)

const filteredAssets = computed(() => {
  if (!selectedCategory.value) return assets.value
  return assets.value.filter((asset) => {
    if (asset.category !== selectedCategory.value) return false
    if (selectedSubCategory.value && asset.sub_category !== selectedSubCategory.value) return false
    return true
  })
})

const hasProject = computed(() => currentProject.value !== null)

const loadProjects = async (): Promise<void> => {
  try {
    const data = await assetsService.getProjects()
    projects.value = data
  } catch (error) {
    console.error('加载项目列表失败:', error)
    projects.value = []
  }
}

const loadCurrentProject = async (): Promise<void> => {
  try {
    const data = await assetsService.getCurrentProject()
    currentProject.value = data.project
  } catch (error) {
    console.error('获取当前项目失败:', error)
    currentProject.value = null
  }
}

const loadAssets = async (): Promise<void> => {
  if (!currentProject.value) {
    assets.value = []
    return
  }
  
  loading.value = true
  try {
    const data = await assetsService.getAll()
    assets.value = data
  } catch (error) {
    console.error('加载资产失败:', error)
    assets.value = []
  } finally {
    loading.value = false
  }
}

const handleProjectSelect = async (project: Project): Promise<void> => {
  try {
    await assetsService.switchProject(project.id)
    currentProject.value = project
    await loadAssets()
    categoryTreeRef.value?.loadSubCategories()
  } catch (error) {
    console.error('切换项目失败:', error)
  }
}

const handleProjectCreate = (): void => {
  showNewProjectDialog.value = true
}

const handleProjectLoad = (): void => {
  showLoadProjectDialog.value = true
}

const handleLoadProject = async (path: string): Promise<void> => {
  try {
    const result = await assetsService.loadProject(path)
    projects.value.unshift(result.project)
    currentProject.value = result.project
    showLoadProjectDialog.value = false
    await loadAssets()
    categoryTreeRef.value?.loadSubCategories()
    alert(`项目加载成功！共导入 ${result.loaded_assets} 个资产文件`)
  } catch (error: any) {
    console.error('加载项目失败:', error)
    if (error.detail) {
      loadProjectDialogRef.value?.setError(error.detail)
    }
  }
}

const handleProjectDelete = async (project: Project): Promise<void> => {
  if (!confirm(`确定要删除项目"${project.name}"吗？这将删除该项目的所有资产文件。`)) return
  
  try {
    await assetsService.deleteProject(project.id)
    projects.value = projects.value.filter(p => p.id !== project.id)
    
    if (currentProject.value?.id === project.id) {
      currentProject.value = null
      assets.value = []
      await loadCurrentProject()
      if (currentProject.value) {
        await loadAssets()
      }
    }
  } catch (error) {
    console.error('删除项目失败:', error)
  }
}

const handleCreateProject = async (name: string, path: string): Promise<void> => {
  try {
    const newProject = await assetsService.createProject(name, path)
    projects.value.unshift(newProject)
    currentProject.value = newProject
    showNewProjectDialog.value = false
    await loadAssets()
    categoryTreeRef.value?.loadSubCategories()
  } catch (error) {
    console.error('创建项目失败:', error)
  }
}

const handleCategorySelect = (category: string, subCategory?: string): void => {
  selectedCategory.value = category
  selectedSubCategory.value = subCategory || null
}

const handleAssetSelect = (id: number): void => {
  const index = selectedAssetIds.value.indexOf(id)
  if (index === -1) {
    selectedAssetIds.value.push(id)
  } else {
    selectedAssetIds.value.splice(index, 1)
  }
}

const handleAssetDelete = async (id: number): Promise<void> => {
  try {
    await assetsService.delete(id)
    assets.value = assets.value.filter((a) => a.id !== id)
    selectedAssetIds.value = selectedAssetIds.value.filter((assetId) => assetId !== id)
  } catch (error) {
    console.error('删除资产失败:', error)
  }
}

const handleAssetRename = (id: number, newName: string): void => {
  const asset = assets.value.find(a => a.id === id)
  if (asset) {
    const ext = asset.name.split('.').pop()
    asset.name = `${newName}.${ext}`
  }
}

const handleUpload = async (file: File, category: string, subCategoryName: string): Promise<void> => {
  const tempId = `temp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  
  const tempAsset: Asset = {
    id: -1,
    name: file.name,
    category: category as 'prompt' | 'image' | 'audio' | 'video' | 'document',
    sub_category: subCategoryName,
    file_path: '',
    file_type: file.name.split('.').pop() || '',
    project_id: currentProject.value?.id || null,
    created_at: new Date().toISOString(),
    uploading: true,
    tempId: tempId
  }
  
  assets.value.unshift(tempAsset)
  showUploadDialog.value = false
  
  try {
    const uploadResult = await assetsService.upload(file, category, subCategoryName)
    
    const newAsset = await assetsService.create({
      name: file.name,
      category: category as 'prompt' | 'image' | 'audio' | 'video' | 'document',
      sub_category: subCategoryName,
      file_path: uploadResult.file_path,
      file_type: file.name.split('.').pop() || ''
    })
    
    const tempIndex = assets.value.findIndex(a => a.tempId === tempId)
    if (tempIndex !== -1) {
      assets.value[tempIndex] = newAsset
    }
    
    categoryTreeRef.value?.loadSubCategories()
  } catch (error) {
    console.error('上传资产失败:', error)
    assets.value = assets.value.filter(a => a.tempId !== tempId)
  }
}

const handleOpenDirectory = async (): Promise<void> => {
  if (currentProject.value?.path) {
    try {
      await window.api.openDirectory(currentProject.value.path)
    } catch (error) {
      console.error('打开目录失败:', error)
    }
  }
}

onMounted(async () => {
  await loadProjects()
  await loadCurrentProject()
  await loadAssets()
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <div>
          <h1 class="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">资产管理</h1>
          <p class="text-zinc-500 dark:text-zinc-400 mt-1">
            {{ currentProject ? `当前项目: ${currentProject.name}` : '请选择或创建一个项目' }}
          </p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <ProjectSelector
          :projects="projects"
          :current-project="currentProject"
          @select="handleProjectSelect"
          @create="handleProjectCreate"
          @delete="handleProjectDelete"
        />
        <Button
          variant="outline"
          size="sm"
          @click="handleProjectLoad"
          class="rounded-xl gap-2"
        >
          <FolderSearch :size="16" />
          加载项目
        </Button>
        <Button
          variant="outline"
          size="sm"
          @click="handleOpenDirectory"
          :disabled="!currentProject"
          class="rounded-xl gap-2"
        >
          <FolderOpen :size="16" />
          打开目录
        </Button>
      </div>
    </div>

    <div v-if="!hasProject" class="flex items-center justify-center min-h-[calc(100vh-280px)]">
      <Card class="w-full max-w-md backdrop-blur-xl bg-white/70 dark:bg-zinc-900/70 border-zinc-200/50 dark:border-zinc-800/50 rounded-2xl shadow-xl shadow-black/5">
        <CardContent class="p-8 text-center">
          <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center">
            <AlertCircle :size="32" class="text-zinc-400" />
          </div>
          <h3 class="text-lg font-medium text-zinc-800 dark:text-zinc-200 mb-2">暂无选中项目</h3>
          <p class="text-sm text-zinc-500 dark:text-zinc-400 mb-6">
            请选择一个现有项目或创建新项目来管理资产
          </p>
          <Button
            @click="showNewProjectDialog = true"
            class="rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100"
          >
            创建新项目
          </Button>
          <Button
            variant="outline"
            @click="handleProjectLoad"
            class="rounded-xl gap-2"
          >
            <FolderSearch :size="16" />
            加载项目
          </Button>
        </CardContent>
      </Card>
    </div>

    <div v-else class="flex gap-6 min-h-[calc(100vh-220px)]">
      <Card class="w-56 shrink-0 backdrop-blur-xl bg-white/70 dark:bg-zinc-900/70 border-zinc-200/50 dark:border-zinc-800/50 rounded-2xl shadow-xl shadow-black/5">
        <CardContent class="p-4">
          <CategoryTree
            ref="categoryTreeRef"
            :selected-category="selectedCategory"
            :selected-sub-category="selectedSubCategory"
            @select="handleCategorySelect"
          />
        </CardContent>
      </Card>

      <Card class="flex-1 backdrop-blur-xl bg-white/70 dark:bg-zinc-900/70 border-zinc-200/50 dark:border-zinc-800/50 rounded-2xl shadow-xl shadow-black/5 flex flex-col">
        <CardContent class="p-0 flex-1 flex flex-col">
          <div class="flex-1 overflow-auto">
            <AssetList
              :assets="filteredAssets"
              :selected-ids="selectedAssetIds"
              :loading="loading"
              :current-category="selectedCategory"
              :current-sub-category="selectedSubCategory"
              @select="handleAssetSelect"
              @delete="handleAssetDelete"
              @rename="handleAssetRename"
              @upload="handleUpload"
            />
          </div>
          <div class="p-4 border-t border-zinc-200/50 dark:border-zinc-800/50">
            <Button
              @click="showUploadDialog = true"
              class="rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 gap-2"
            >
              <Upload :size="16" />
              上传资产
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>

    <UploadDialog
      :visible="showUploadDialog"
      @close="showUploadDialog = false"
      @upload="handleUpload"
    />

    <NewProjectDialog
      :visible="showNewProjectDialog"
      @close="showNewProjectDialog = false"
      @create="handleCreateProject"
    />

    <LoadProjectDialog
      ref="loadProjectDialogRef"
      :visible="showLoadProjectDialog"
      @close="showLoadProjectDialog = false"
      @load="handleLoadProject"
    />
  </div>
</template>
