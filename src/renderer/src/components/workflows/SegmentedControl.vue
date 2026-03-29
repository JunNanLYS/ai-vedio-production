<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'

interface Props {
  options: string[]
  modelValue: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const containerRef = ref<HTMLElement | null>(null)
const optionRefs = ref<Map<string, HTMLElement>>(new Map())
const indicatorStyle = ref({
  width: '0px',
  transform: 'translateX(0px)'
})

const updateIndicator = async () => {
  await nextTick()
  const activeOption = optionRefs.value.get(props.modelValue)
  const container = containerRef.value
  
  if (activeOption && container) {
    const containerRect = container.getBoundingClientRect()
    const optionRect = activeOption.getBoundingClientRect()
    
    const offsetLeft = optionRect.left - containerRect.left
    
    indicatorStyle.value = {
      width: `${optionRect.width}px`,
      transform: `translateX(${offsetLeft}px)`
    }
  }
}

const selectOption = (option: string) => {
  emit('update:modelValue', option)
}

const setOptionRef = (option: string, el: any) => {
  if (el) {
    optionRefs.value.set(option, el)
  }
}

onMounted(() => {
  updateIndicator()
})

watch(() => props.modelValue, () => {
  updateIndicator()
})

watch(() => props.options, () => {
  updateIndicator()
}, { deep: true })
</script>

<template>
  <div class="flex justify-center p-1">
    <div
      ref="containerRef"
      class="relative inline-flex bg-zinc-100/80 dark:bg-zinc-800/80 backdrop-blur-xl rounded-xl p-1 gap-1"
    >
      <div
        class="absolute top-1 h-[calc(100%-8px)] bg-white dark:bg-zinc-700 rounded-lg shadow-sm transition-all duration-300 ease-out"
        :style="{
          width: indicatorStyle.width,
          transform: indicatorStyle.transform
        }"
      />
      <button
        v-for="option in options"
        :key="option"
        :ref="(el) => setOptionRef(option, el)"
        :class="[
          'relative z-10 px-5 py-2 rounded-lg text-sm font-medium transition-colors duration-200',
          modelValue === option
            ? 'text-zinc-900 dark:text-zinc-100'
            : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-300'
        ]"
        @click="selectOption(option)"
      >
        {{ option }}
      </button>
    </div>
  </div>
</template>
