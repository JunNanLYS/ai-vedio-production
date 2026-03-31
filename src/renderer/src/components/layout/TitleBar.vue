<script setup lang="ts">
import { ref, onMounted } from 'vue'

const isMaximized = ref(false)

onMounted(async () => {
  isMaximized.value = await window.api.windowIsMaximized()
})

const handleMinimize = () => {
  window.api.windowMinimize()
}

const handleMaximize = async () => {
  isMaximized.value = await window.api.windowMaximize()
}

const handleClose = () => {
  window.api.windowClose()
}
</script>

<template>
  <div
    class="h-10 flex items-center justify-center relative bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl border-b border-black/5 dark:border-white/5 select-none"
    style="-webkit-app-region: drag"
  >
    <span class="font-medium text-sm text-zinc-700 dark:text-zinc-200">AI 视频生产</span>
    <div class="absolute right-0 flex" style="-webkit-app-region: no-drag">
      <button
        @click="handleMinimize"
        class="w-11 h-10 flex items-center justify-center hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
        title="最小化"
      >
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <rect
            x="1"
            y="5.5"
            width="10"
            height="1"
            fill="currentColor"
            class="text-zinc-600 dark:text-zinc-300"
          />
        </svg>
      </button>
      <button
        @click="handleMaximize"
        class="w-11 h-10 flex items-center justify-center hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
        :title="isMaximized ? '还原' : '最大化'"
      >
        <svg
          v-if="!isMaximized"
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <rect
            x="1.5"
            y="1.5"
            width="9"
            height="9"
            stroke="currentColor"
            stroke-width="1"
            class="text-zinc-600 dark:text-zinc-300"
          />
        </svg>
        <svg
          v-else
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <rect
            x="3"
            y="0"
            width="9"
            height="9"
            stroke="currentColor"
            stroke-width="1"
            class="text-zinc-600 dark:text-zinc-300"
          />
          <rect
            x="0"
            y="3"
            width="9"
            height="9"
            stroke="currentColor"
            stroke-width="1"
            fill="currentColor"
            class="text-white dark:text-zinc-900"
          />
        </svg>
      </button>
      <button
        @click="handleClose"
        class="w-11 h-10 flex items-center justify-center hover:bg-red-500 transition-colors group"
        title="关闭"
      >
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M1 1L11 11M11 1L1 11"
            stroke="currentColor"
            stroke-width="1.2"
            class="text-zinc-600 dark:text-zinc-300 group-hover:text-white"
          />
        </svg>
      </button>
    </div>
  </div>
</template>
