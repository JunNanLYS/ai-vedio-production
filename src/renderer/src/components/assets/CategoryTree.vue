<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import {
  FileText,
  Image,
  Music,
  Video,
  ChevronRight,
  ChevronDown,
  Plus,
  Trash2,
  X,
  Check,
  FileSpreadsheet,
  Layout
} from 'lucide-vue-next'
import { cn } from '@/lib/utils'
import { assetsService } from '@/services/assets'
import type { SubCategory } from '@/types'

interface Category {
  id: string
  name: string
  icon: typeof FileText
}

const props = defineProps<{
  selectedCategory: string | null
  selectedSubCategory: string | null
}>()

const emit = defineEmits<{
  (e: 'select', category: string, subCategory?: string): void
}>()

const categories: Category[] = [
  { id: 'prompt', name: 'Prompt', icon: FileText },
  { id: 'image', name: '图片', icon: Image },
  { id: 'audio', name: '声音', icon: Music },
  { id: 'video', name: '视频', icon: Video },
  { id: 'document', name: '文档', icon: FileSpreadsheet },
  { id: 'canvas', name: '画布', icon: Layout }
]

const subCategories = ref<SubCategory[]>([])
const expandedCategories = ref<Set<string>>(new Set())
const newSubCategoryName = ref('')
const addingToCategory = ref<string | null>(null)
const deletingId = ref<number | null>(null)
const newSubCategoryInputRef = ref<HTMLInputElement | null>(null)

const getSubCategoriesByCategory = (categoryId: string): SubCategory[] => {
  return subCategories.value.filter((sub) => sub.category === categoryId)
}

const loadSubCategories = async (): Promise<void> => {
  try {
    const data = await assetsService.getSubCategories()
    subCategories.value = data
  } catch (error) {
    console.error('加载子分类失败:', error)
  }
}

const toggleCategory = (categoryId: string): void => {
  if (expandedCategories.value.has(categoryId)) {
    expandedCategories.value.delete(categoryId)
  } else {
    expandedCategories.value.add(categoryId)
  }
}

const handleCategoryClick = (category: Category): void => {
  emit('select', category.id)
  toggleCategory(category.id)
}

const handleSubCategoryClick = (categoryId: string, subCategory: SubCategory): void => {
  emit('select', categoryId, subCategory.name)
}

const startAddingSubCategory = (categoryId: string): void => {
  addingToCategory.value = categoryId
  newSubCategoryName.value = ''
  nextTick(() => {
    newSubCategoryInputRef.value?.focus()
  })
}

const cancelAddingSubCategory = (): void => {
  addingToCategory.value = null
  newSubCategoryName.value = ''
}

const confirmAddSubCategory = async (): Promise<void> => {
  if (!addingToCategory.value || !newSubCategoryName.value.trim()) return

  try {
    const newSubCategory = await assetsService.createSubCategory(
      addingToCategory.value,
      newSubCategoryName.value.trim()
    )
    subCategories.value.push(newSubCategory)
    cancelAddingSubCategory()
  } catch (error) {
    console.error('创建子分类失败:', error)
  }
}

const handleDeleteSubCategory = async (subCategory: SubCategory, event: Event): Promise<void> => {
  event.stopPropagation()

  if (!confirm(`确定要删除子分类"${subCategory.name}"吗？`)) return

  deletingId.value = subCategory.id
  try {
    await assetsService.deleteSubCategory(subCategory.id)
    subCategories.value = subCategories.value.filter((s) => s.id !== subCategory.id)
    if (addingToCategory.value) {
      addingToCategory.value = null
      newSubCategoryName.value = ''
    }
  } catch (error) {
    console.error('删除子分类失败:', error)
  } finally {
    deletingId.value = null
  }
}

const isSelected = (categoryId: string, subCategoryName?: string): boolean => {
  if (subCategoryName) {
    return props.selectedCategory === categoryId && props.selectedSubCategory === subCategoryName
  }
  return props.selectedCategory === categoryId && !props.selectedSubCategory
}

onMounted(() => {
  loadSubCategories()
})

defineExpose({ loadSubCategories })
</script>

<template>
  <div class="category-tree h-full overflow-auto py-4">
    <div class="space-y-1 px-2">
      <div v-for="category in categories" :key="category.id" class="category-group">
        <div
          @click="handleCategoryClick(category)"
          :class="
            cn(
              'flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer transition-all duration-200',
              'hover:bg-zinc-900/5 dark:hover:bg-white/5',
              isSelected(category.id) && 'bg-zinc-900/5 dark:bg-white/10'
            )
          "
        >
          <component
            :is="category.icon"
            :size="18"
            :stroke-width="1.5"
            class="text-zinc-500 dark:text-zinc-400"
          />
          <span class="flex-1 text-sm font-medium text-zinc-700 dark:text-zinc-300">
            {{ category.name }}
          </span>
          <button
            @click.stop="startAddingSubCategory(category.id)"
            class="p-1 rounded-lg hover:bg-zinc-200/50 dark:hover:bg-zinc-700/50 transition-colors"
          >
            <Plus :size="14" class="text-zinc-400" />
          </button>
          <component
            :is="expandedCategories.has(category.id) ? ChevronDown : ChevronRight"
            :size="16"
            class="text-zinc-400"
          />
        </div>

        <div
          v-if="expandedCategories.has(category.id)"
          class="ml-6 mt-1 space-y-0.5 overflow-hidden"
        >
          <div
            v-for="subCategory in getSubCategoriesByCategory(category.id)"
            :key="subCategory.id"
            @click="handleSubCategoryClick(category.id, subCategory)"
            :class="
              cn(
                'group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all duration-200',
                'hover:bg-zinc-900/5 dark:hover:bg-white/5',
                isSelected(category.id, subCategory.name) && 'bg-zinc-900/5 dark:bg-white/10'
              )
            "
          >
            <span class="flex-1 text-sm text-zinc-600 dark:text-zinc-400 truncate">
              {{ subCategory.name }}
            </span>
            <button
              @click="handleDeleteSubCategory(subCategory, $event)"
              :disabled="deletingId === subCategory.id"
              class="p-1 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors opacity-0 group-hover:opacity-100 disabled:opacity-50 shrink-0"
            >
              <Trash2 :size="12" class="text-red-400" />
            </button>
          </div>

          <div v-if="addingToCategory === category.id" class="flex items-center gap-1 px-2 py-2">
            <input
              ref="newSubCategoryInputRef"
              v-model="newSubCategoryName"
              type="text"
              placeholder="输入名称"
              class="min-w-0 flex-1 h-7 px-2 text-sm rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 focus:outline-none focus:ring-1 focus:ring-zinc-400"
              @keyup.enter="confirmAddSubCategory"
              @keyup.esc="cancelAddingSubCategory"
            />
            <button
              @click="confirmAddSubCategory"
              :disabled="!newSubCategoryName.trim()"
              class="p-1.5 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors disabled:opacity-50 shrink-0"
            >
              <Check :size="14" class="text-green-500" />
            </button>
            <button
              @click="cancelAddingSubCategory"
              class="p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors shrink-0"
            >
              <X :size="14" class="text-red-400" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.category-tree::-webkit-scrollbar {
  width: 4px;
}

.category-tree::-webkit-scrollbar-track {
  background: transparent;
}

.category-tree::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 2px;
}

.dark .category-tree::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
}
</style>
