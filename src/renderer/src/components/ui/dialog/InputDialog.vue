<script setup lang="ts">
import { ref, watch } from 'vue'
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
  open: boolean
  title?: string
  label?: string
  placeholder?: string
  defaultValue?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '请输入',
  label: '',
  placeholder: '',
  defaultValue: ''
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  confirm: [value: string]
  cancel: []
}>()

const inputValue = ref('')

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      inputValue.value = props.defaultValue
    }
  }
)

const handleConfirm = () => {
  emit('confirm', inputValue.value)
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
          {{ title }}
        </DialogTitle>
      </DialogHeader>

      <div class="py-4">
        <label v-if="label" class="text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2 block">
          {{ label }}
        </label>
        <Input
          v-model="inputValue"
          :placeholder="placeholder"
          class="bg-zinc-50 dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700"
          @keyup="handleKeyup"
        />
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
          @click="handleConfirm"
        >
          确定
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
