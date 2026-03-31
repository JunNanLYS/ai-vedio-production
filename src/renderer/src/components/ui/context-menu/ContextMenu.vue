<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

interface MenuItem {
  label: string
  icon?: string
  action: () => void
  divider?: boolean
  disabled?: boolean
  tooltip?: string
}

const props = defineProps<{
  items: MenuItem[]
}>()

const visible = ref(false)
const position = ref({ x: 0, y: 0 })

const show = (x: number, y: number) => {
  position.value = { x, y }
  visible.value = true
}

const hide = () => {
  visible.value = false
}

const handleItemClick = (item: MenuItem) => {
  if (!item.disabled) {
    item.action()
    hide()
  }
}

const handleClickOutside = () => {
  if (visible.value) {
    hide()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

defineExpose({ show, hide })
</script>

<template>
  <Teleport to="body">
    <Transition name="context-menu">
      <div
        v-if="visible"
        class="fixed z-50 min-w-[160px] bg-white dark:bg-zinc-800 rounded-xl shadow-xl border border-zinc-200 dark:border-zinc-700 py-1 overflow-hidden"
        :style="{ left: `${position.x}px`, top: `${position.y}px` }"
        @click.stop
      >
        <template v-for="(item, index) in items" :key="index">
          <div v-if="item.divider" class="h-px bg-zinc-200 dark:bg-zinc-700 my-1"></div>
          <button
            v-else
            class="w-full flex items-center gap-2 px-3 py-2 text-sm text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-700 transition-colors text-left"
            :class="{
              'opacity-50 cursor-not-allowed': item.disabled,
              'hover:bg-zinc-100 dark:hover:bg-zinc-700': !item.disabled
            }"
            :title="item.tooltip"
            @click="handleItemClick(item)"
          >
            <svg
              v-if="item.icon"
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path v-if="item.icon === 'upload'" d="M8 10V3M5 6L8 3L11 6M3 10V13H13V10" />
              <path
                v-else-if="item.icon === 'image'"
                d="M2 4C2 2.89543 2.89543 2 4 2H12C13.1046 2 14 2.89543 14 4V12C14 13.1046 13.1046 14 12 14H4C2.89543 14 2 13.1046 2 12V4ZM5 6.5C5 7.32843 5.67157 8 6.5 8C7.32843 8 8 7.32843 8 6.5C8 5.67157 7.32843 5 6.5 5C5.67157 5 5 5.67157 5 6.5ZM14 10L11 7L5 13H12C13.1046 13 14 12.1046 14 11V10Z"
              />
              <path
                v-else-if="item.icon === 'sparkles'"
                d="M8 1L9.5 5.5L14 7L9.5 8.5L8 13L6.5 8.5L2 7L6.5 5.5L8 1Z"
              />
              <path v-else-if="item.icon === 'text'" d="M3 3H13M8 3V13M5 13H11" />
              <path
                v-else-if="item.icon === 'folder'"
                d="M2 4C2 2.89543 2.89543 2 4 2H6L8 4H12C13.1046 4 14 4.89543 14 6V12C14 13.1046 13.1046 14 12 14H4C2.89543 14 2 13.1046 2 12V4Z"
              />
              <path
                v-else-if="item.icon === 'file'"
                d="M4 2C2.89543 2 2 2.89543 2 4V12C2 13.1046 2.89543 14 4 14H12C13.1046 14 14 13.1046 14 12V6L10 2H4ZM10 2.5L13.5 6H10V2.5Z"
              />
              <path
                v-else-if="item.icon === 'trash'"
                d="M5 4H3V6H4V12C4 13.1046 4.89543 14 6 14H10C11.1046 14 12 13.1046 12 12V6H13V4H5ZM6 6H10V12H6V6ZM7 2H9V4H7V2Z"
              />
            </svg>
            <span>{{ item.label }}</span>
          </button>
        </template>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.context-menu-enter-active,
.context-menu-leave-active {
  transition: all 0.15s ease;
}

.context-menu-enter-from,
.context-menu-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

.context-menu-enter-to,
.context-menu-leave-from {
  opacity: 1;
  transform: scale(1);
}
</style>
