<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import type { Project } from '@/types'

interface Props {
  open: boolean
  projects: Project[]
  defaultProjectId: number | null
  defaultProjectName: string | null
  canvasName?: string | null
  isUpdate?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  canvasName: null,
  isUpdate: false
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  confirm: [projectId: number, canvasName: string]
  cancel: []
}>()

const selectedProjectId = ref<string>('')
const canvasNameInput = ref('')

const hasProjects = computed(() => props.projects.length > 0)

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      if (props.defaultProjectId) {
        selectedProjectId.value = props.defaultProjectId.toString()
      } else if (props.projects.length > 0) {
        selectedProjectId.value = props.projects[0].id.toString()
      } else {
        selectedProjectId.value = ''
      }
      canvasNameInput.value = props.canvasName || ''
    }
  }
)

const handleConfirm = () => {
  if (!selectedProjectId.value || !canvasNameInput.value.trim()) return
  emit('confirm', parseInt(selectedProjectId.value, 10), canvasNameInput.value.trim())
  emit('update:open', false)
}

const handleCancel = () => {
  emit('cancel')
  emit('update:open', false)
}

const handleKeyup = (event: KeyboardEvent) => {
  if (event.key === 'Enter') {
    handleConfirm()
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent
      class="backdrop-blur-xl bg-white/90 dark:bg-zinc-900/90 border-zinc-200/50 dark:border-zinc-800/50 rounded-2xl max-w-sm"
    >
      <DialogHeader>
        <DialogTitle class="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          {{ isUpdate ? '更新画布' : '保存画布' }}
        </DialogTitle>
      </DialogHeader>

      <div class="py-4 space-y-4">
        <div class="space-y-2">
          <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">保存到项目</label>
          <Select v-model="selectedProjectId">
            <SelectTrigger class="bg-zinc-50 dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700">
              <SelectValue placeholder="请选择项目" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem
                v-for="project in projects"
                :key="project.id"
                :value="project.id.toString()"
              >
                {{ project.name }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div class="space-y-2">
          <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">画布名称</label>
          <Input
            v-model="canvasNameInput"
            placeholder="请输入画布名称"
            class="bg-zinc-50 dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700"
            @keyup="handleKeyup"
          />
        </div>
      </div>

      <DialogFooter class="gap-2">
        <Button
          variant="outline"
          class="rounded-xl border-zinc-200 dark:border-zinc-700"
          @click="handleCancel"
        >
          取消
        </Button>
        <Button
          class="rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100"
          :disabled="!selectedProjectId || !canvasNameInput.trim()"
          @click="handleConfirm"
        >
          {{ isUpdate ? '更新' : '保存' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
