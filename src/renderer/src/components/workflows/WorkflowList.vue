<script setup lang="ts">
import type { Workflow } from '@/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

interface Props {
  workflows: Workflow[]
  loading?: boolean
}

defineProps<Props>()
const emit = defineEmits<{
  create: []
  edit: [workflow: Workflow]
  delete: [id: number]
}>()
</script>

<template>
  <div class="space-y-4">
    <div class="flex justify-end">
      <Button
        class="rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100 gap-2"
        @click="emit('create')"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M8 3V13M3 8H13" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
        </svg>
        新建工作流
      </Button>
    </div>

    <div v-if="loading" class="flex flex-col items-center justify-center py-16 gap-4">
      <div
        class="w-8 h-8 border-2 border-zinc-200 dark:border-zinc-700 border-t-zinc-900 dark:border-t-white rounded-full animate-spin"
      ></div>
      <span class="text-zinc-500 dark:text-zinc-400">加载中...</span>
    </div>

    <div
      v-else-if="workflows.length === 0"
      class="flex flex-col items-center justify-center py-16 gap-3"
    >
      <div class="text-zinc-300 dark:text-zinc-600">
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
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
      <span class="text-base font-medium text-zinc-500 dark:text-zinc-400">暂无工作流</span>
      <span class="text-sm text-zinc-400 dark:text-zinc-500">点击上方按钮创建第一个工作流</span>
    </div>

    <div v-else class="space-y-3">
      <Card
        v-for="workflow in workflows"
        :key="workflow.id"
        class="backdrop-blur-xl bg-white/70 dark:bg-zinc-900/70 border-zinc-200/50 dark:border-zinc-800/50 rounded-2xl shadow-lg shadow-black/5 hover:shadow-xl hover:shadow-black/10 transition-all duration-300"
      >
        <CardContent class="p-5">
          <div class="flex items-start justify-between mb-2">
            <h3 class="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
              {{ workflow.name }}
            </h3>
            <div class="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon-sm"
                class="opacity-40 hover:opacity-100 hover:text-blue-500 transition-opacity"
                title="编辑"
                @click="emit('edit', workflow)"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path
                    d="M11.5 2.5L13.5 4.5M2 14L2.5 11.5L10 4L12 6L4.5 13.5L2 14Z"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </Button>
              <Button
                variant="ghost"
                size="icon-sm"
                class="opacity-40 hover:opacity-100 hover:text-rose-500 transition-opacity"
                title="删除"
                @click="emit('delete', workflow.id)"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path
                    d="M4 4L12 12M12 4L4 12"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                  />
                </svg>
              </Button>
            </div>
          </div>

          <p v-if="workflow.description" class="text-sm text-zinc-500 dark:text-zinc-400 mb-4">
            {{ workflow.description }}
          </p>

          <div class="flex items-center flex-wrap gap-2">
            <template v-for="(step, index) in workflow.steps" :key="index">
              <span
                class="px-3 py-1.5 bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded-lg text-sm font-medium"
              >
                {{ step }}
              </span>
              <svg
                v-if="index < workflow.steps.length - 1"
                width="20"
                height="20"
                viewBox="0 0 20 20"
                fill="none"
                class="text-zinc-300 dark:text-zinc-600"
              >
                <path
                  d="M4 10H16M16 10L12 6M16 10L12 14"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </template>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
