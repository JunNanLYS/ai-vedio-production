<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const logs = ref<string[]>([])
const isExpanded = ref(false)
const autoScroll = ref(true)
const logContainer = ref<HTMLElement | null>(null)
let unsubscribe: (() => void) | null = null

const filteredLogs = computed(() => {
  return logs.value.slice(-500)
})

const logCount = computed(() => logs.value.length)

function formatLog(log: string): { type: string; content: string; timestamp: string } {
  const stdoutMatch = log.match(/\[([^\]]+)\] \[STDOUT\] (.+)/)
  const stderrMatch = log.match(/\[([^\]]+)\] \[STDERR\] (.+)/)
  
  if (stdoutMatch) {
    return { type: 'stdout', timestamp: stdoutMatch[1], content: stdoutMatch[2] }
  } else if (stderrMatch) {
    return { type: 'stderr', timestamp: stderrMatch[1], content: stderrMatch[2] }
  }
  
  return { type: 'unknown', timestamp: '', content: log }
}

function getLogClass(type: string): string {
  switch (type) {
    case 'stdout':
      return 'text-emerald-600 dark:text-emerald-400'
    case 'stderr':
      return 'text-rose-600 dark:text-rose-400'
    default:
      return 'text-zinc-600 dark:text-zinc-400'
  }
}

function scrollToBottom(): void {
  if (autoScroll.value && logContainer.value) {
    nextTick(() => {
      logContainer.value!.scrollTop = logContainer.value!.scrollHeight
    })
  }
}

function toggleAutoScroll(): void {
  autoScroll.value = !autoScroll.value
}

function clearLogs(): void {
  logs.value = []
}

function toggleExpand(): void {
  isExpanded.value = !isExpanded.value
}

onMounted(async () => {
  const historyLogs = await window.api.getBackendLogs()
  logs.value = historyLogs
  scrollToBottom()
  
  unsubscribe = window.api.subscribeBackendLogs((log: string) => {
    logs.value.push(log)
    if (logs.value.length > 1000) {
      logs.value.shift()
    }
    scrollToBottom()
  })
})

onUnmounted(() => {
  if (unsubscribe) {
    unsubscribe()
  }
})
</script>

<template>
  <Card
    class="backdrop-blur-xl bg-white/70 dark:bg-zinc-900/70 border-zinc-200/50 dark:border-zinc-800/50 rounded-3xl shadow-xl shadow-black/5"
  >
    <CardHeader class="pb-3">
      <div class="flex items-center justify-between">
        <CardTitle class="text-lg flex items-center gap-2">
          <svg
            class="h-5 w-5 text-zinc-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          后端日志
          <span class="text-sm font-normal text-zinc-400">({{ logCount }} 条)</span>
        </CardTitle>
        <div class="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            class="h-8 px-2"
            :class="{ 'bg-emerald-100 dark:bg-emerald-900/30': autoScroll }"
            @click="toggleAutoScroll"
          >
            <svg
              class="h-4 w-4"
              :class="autoScroll ? 'text-emerald-600 dark:text-emerald-400' : 'text-zinc-400'"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 14l-7 7m0 0l-7-7m7 7V3"
              />
            </svg>
          </Button>
          <Button variant="ghost" size="sm" class="h-8 px-2" @click="clearLogs">
            <svg class="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </Button>
          <Button variant="ghost" size="sm" class="h-8 px-2" @click="toggleExpand">
            <svg
              class="h-4 w-4 text-zinc-400 transition-transform"
              :class="{ 'rotate-180': isExpanded }"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </Button>
        </div>
      </div>
    </CardHeader>
    <CardContent v-show="isExpanded" class="pt-0">
      <div
        ref="logContainer"
        class="h-64 overflow-y-auto rounded-xl bg-zinc-900 dark:bg-zinc-950 p-3 font-mono text-xs"
      >
        <div v-if="filteredLogs.length === 0" class="text-zinc-500 text-center py-4">
          暂无日志
        </div>
        <div
          v-for="(log, index) in filteredLogs"
          :key="index"
          class="py-0.5 hover:bg-zinc-800/50 px-1 rounded"
        >
          <span :class="getLogClass(formatLog(log).type)">
            {{ log }}
          </span>
        </div>
      </div>
    </CardContent>
  </Card>
</template>
