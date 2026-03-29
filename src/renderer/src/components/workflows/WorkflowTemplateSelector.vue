<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Workflow } from '@/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

interface Props {
  workflows: Workflow[]
  loading?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  apply: [workflowId: number]
}>()

const selectedId = ref<number | null>(null)

watch(
  () => props.workflows,
  (newWorkflows) => {
    if (newWorkflows.length > 0 && !selectedId.value) {
      selectedId.value = newWorkflows[0].id
    }
  },
  { immediate: true }
)

const handleApply = () => {
  if (selectedId.value) {
    emit('apply', selectedId.value)
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="text-center py-4">
      <p class="text-zinc-500 dark:text-zinc-400 mb-4">该订单暂无工作流，请选择一个模板应用</p>
    </div>

    <div
      v-if="loading"
      class="flex flex-col items-center justify-center py-8 gap-4"
    >
      <div
        class="w-8 h-8 border-2 border-zinc-200 dark:border-zinc-700 border-t-zinc-900 dark:border-t-white rounded-full animate-spin"
      ></div>
      <span class="text-zinc-500 dark:text-zinc-400">加载模板...</span>
    </div>

    <div v-else-if="workflows.length === 0" class="text-center py-8 text-zinc-500 dark:text-zinc-400">
      暂无可用模板，请先创建工作流模板
    </div>

    <div v-else class="space-y-3">
      <Card
        v-for="workflow in workflows"
        :key="workflow.id"
        :class="[
          'cursor-pointer transition-all duration-200 rounded-2xl border-2',
          selectedId === workflow.id
            ? 'border-zinc-900 dark:border-white bg-zinc-50 dark:bg-zinc-800/50'
            : 'border-transparent bg-white/70 dark:bg-zinc-900/70 hover:border-zinc-300 dark:hover:border-zinc-700'
        ]"
        @click="selectedId = workflow.id"
      >
        <CardContent class="p-4">
          <div class="flex items-center justify-between mb-2">
            <h4 class="font-semibold text-zinc-900 dark:text-zinc-100">{{ workflow.name }}</h4>
            <div
              v-if="selectedId === workflow.id"
              class="w-5 h-5 rounded-full bg-zinc-900 dark:bg-white flex items-center justify-center"
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M2 6L5 9L10 3" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="dark:stroke-zinc-900"/>
              </svg>
            </div>
          </div>
          <div class="flex items-center flex-wrap gap-1.5">
            <span
              v-for="(step, index) in workflow.steps"
              :key="index"
              class="px-2 py-0.5 bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 rounded-md text-xs"
            >
              {{ step }}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>

    <div v-if="workflows.length > 0" class="flex justify-center pt-4">
      <Button
        class="rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100"
        :disabled="!selectedId"
        @click="handleApply"
      >
        应用模板
      </Button>
    </div>
  </div>
</template>
