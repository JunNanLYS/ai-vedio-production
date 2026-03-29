<script setup lang="ts">
import { ref } from 'vue'
import { ChevronDown, Folder, Check, Plus, Trash2 } from 'lucide-vue-next'
import { cn } from '@/lib/utils'
import type { Project } from '@/types'

const props = defineProps<{
  projects: Project[]
  currentProject: Project | null
}>()

const emit = defineEmits<{
  (e: 'select', project: Project): void
  (e: 'create'): void
  (e: 'delete', project: Project): void
}>()

const isOpen = ref(false)

const handleSelect = (project: Project): void => {
  emit('select', project)
  isOpen.value = false
}

const handleCreate = (): void => {
  emit('create')
  isOpen.value = false
}

const handleDelete = (project: Project, event: Event): void => {
  event.stopPropagation()
  emit('delete', project)
}
</script>

<template>
  <div class="relative">
    <button
      @click="isOpen = !isOpen"
      :class="
        cn(
          'flex items-center gap-2 px-3 py-2 rounded-xl transition-all duration-200',
          'bg-white/70 dark:bg-zinc-800/70 border border-zinc-200/50 dark:border-zinc-700/50',
          'hover:bg-zinc-50 dark:hover:bg-zinc-700/50',
          'min-w-[200px]'
        )
      "
    >
      <Folder :size="16" class="text-zinc-500" />
      <span class="flex-1 text-left text-sm font-medium text-zinc-700 dark:text-zinc-300 truncate">
        {{ currentProject?.name || '选择项目' }}
      </span>
      <ChevronDown
        :size="16"
        :class="cn('text-zinc-400 transition-transform duration-200', isOpen && 'rotate-180')"
      />
    </button>

    <Transition name="dropdown">
      <div
        v-if="isOpen"
        class="absolute top-full left-0 mt-2 w-full min-w-[200px] bg-white/95 dark:bg-zinc-800/95 backdrop-blur-xl rounded-xl border border-zinc-200/50 dark:border-zinc-700/50 shadow-xl shadow-black/5 z-50 overflow-hidden"
      >
        <div class="max-h-64 overflow-auto">
          <button
            v-for="project in projects"
            :key="project.id"
            @click="handleSelect(project)"
            :class="
              cn(
                'w-full flex items-center gap-2 px-3 py-2.5 text-left transition-colors',
                'hover:bg-zinc-100/50 dark:hover:bg-zinc-700/50',
                currentProject?.id === project.id && 'bg-zinc-100/50 dark:bg-zinc-700/50'
              )
            "
          >
            <Folder :size="14" class="text-zinc-400 shrink-0" />
            <span class="flex-1 text-sm text-zinc-700 dark:text-zinc-300 truncate">
              {{ project.name }}
            </span>
            <Check
              v-if="currentProject?.id === project.id"
              :size="14"
              class="text-green-500 shrink-0"
            />
            <button
              @click="handleDelete(project, $event)"
              class="p-1 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors shrink-0"
            >
              <Trash2 :size="12" class="text-red-400" />
            </button>
          </button>
        </div>

        <div class="border-t border-zinc-200/50 dark:border-zinc-700/50">
          <button
            @click="handleCreate"
            class="w-full flex items-center gap-2 px-3 py-2.5 text-left hover:bg-zinc-100/50 dark:hover:bg-zinc-700/50 transition-colors"
          >
            <Plus :size="14" class="text-zinc-400" />
            <span class="text-sm text-zinc-600 dark:text-zinc-400">新建项目</span>
          </button>
        </div>
      </div>
    </Transition>

    <div
      v-if="isOpen"
      class="fixed inset-0 z-40"
      @click="isOpen = false"
    />
  </div>
</template>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
