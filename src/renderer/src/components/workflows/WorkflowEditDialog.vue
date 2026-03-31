<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Workflow } from '@/types'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface Props {
  workflow: Workflow | null
  open: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:open': [value: boolean]
  save: [id: number, data: { name: string; steps: string[] }]
}>()

const workflowName = ref('')
const steps = ref<string[]>([])
const newStepName = ref('')

watch(
  () => props.workflow,
  (newWorkflow) => {
    if (newWorkflow) {
      workflowName.value = newWorkflow.name
      steps.value = [...newWorkflow.steps]
    }
  },
  { immediate: true }
)

const addStep = () => {
  if (newStepName.value.trim()) {
    steps.value.push(newStepName.value.trim())
    newStepName.value = ''
  }
}

const removeStep = (index: number) => {
  steps.value.splice(index, 1)
}

const moveStepUp = (index: number) => {
  if (index > 0) {
    const temp = steps.value[index]
    steps.value[index] = steps.value[index - 1]
    steps.value[index - 1] = temp
  }
}

const moveStepDown = (index: number) => {
  if (index < steps.value.length - 1) {
    const temp = steps.value[index]
    steps.value[index] = steps.value[index + 1]
    steps.value[index + 1] = temp
  }
}

const handleSave = () => {
  if (props.workflow && workflowName.value.trim()) {
    emit('save', props.workflow.id, {
      name: workflowName.value.trim(),
      steps: steps.value
    })
    emit('update:open', false)
  }
}

const handleClose = () => {
  emit('update:open', false)
}
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent
      class="backdrop-blur-xl bg-white/90 dark:bg-zinc-900/90 border-zinc-200/50 dark:border-zinc-800/50 rounded-2xl max-w-md"
    >
      <DialogHeader>
        <DialogTitle class="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          编辑工作流
        </DialogTitle>
      </DialogHeader>

      <div class="space-y-4 py-4">
        <div class="space-y-2">
          <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">工作流名称</label>
          <Input
            v-model="workflowName"
            placeholder="输入工作流名称"
            class="bg-zinc-50 dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700"
          />
        </div>

        <div class="space-y-2">
          <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">步骤列表</label>
          <div class="space-y-2 max-h-60 overflow-y-auto">
            <div
              v-for="(_step, index) in steps"
              :key="index"
              class="flex items-center gap-2 p-2 bg-zinc-50 dark:bg-zinc-800 rounded-xl"
            >
              <span
                class="w-6 h-6 flex items-center justify-center bg-zinc-200 dark:bg-zinc-700 rounded-full text-xs font-medium text-zinc-600 dark:text-zinc-400"
              >
                {{ index + 1 }}
              </span>
              <input
                v-model="steps[index]"
                class="flex-1 bg-transparent border-none outline-none text-sm text-zinc-900 dark:text-zinc-100"
              />
              <div class="flex items-center gap-1">
                <button
                  class="p-1 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-lg transition-colors disabled:opacity-30"
                  :disabled="index === 0"
                  @click="moveStepUp(index)"
                >
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path
                      d="M7 11V3M7 3L3 7M7 3L11 7"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </button>
                <button
                  class="p-1 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-lg transition-colors disabled:opacity-30"
                  :disabled="index === steps.length - 1"
                  @click="moveStepDown(index)"
                >
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path
                      d="M7 3V11M7 11L3 7M7 11L11 7"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </button>
                <button
                  class="p-1 hover:bg-rose-100 dark:hover:bg-rose-900/30 text-rose-500 rounded-lg transition-colors"
                  @click="removeStep(index)"
                >
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path
                      d="M3 3L11 11M11 3L3 11"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="round"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="flex gap-2">
          <Input
            v-model="newStepName"
            placeholder="新步骤名称"
            class="flex-1 bg-zinc-50 dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700"
            @keyup.enter="addStep"
          />
          <Button
            variant="outline"
            class="rounded-xl border-zinc-200 dark:border-zinc-700"
            @click="addStep"
          >
            添加
          </Button>
        </div>
      </div>

      <DialogFooter class="gap-2">
        <Button
          variant="outline"
          class="rounded-xl border-zinc-200 dark:border-zinc-700"
          @click="handleClose"
        >
          取消
        </Button>
        <Button
          class="rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100"
          @click="handleSave"
        >
          保存
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
