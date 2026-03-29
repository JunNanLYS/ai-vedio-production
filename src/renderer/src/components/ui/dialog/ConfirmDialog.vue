<script setup lang="ts">
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

interface Props {
  open: boolean
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  variant?: 'default' | 'danger'
}

withDefaults(defineProps<Props>(), {
  title: '确认',
  confirmText: '确定',
  cancelText: '取消',
  variant: 'default'
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  confirm: []
  cancel: []
}>()

const handleConfirm = () => {
  emit('confirm')
  emit('update:open', false)
}

const handleCancel = () => {
  emit('cancel')
  emit('update:open', false)
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
        <DialogDescription class="text-sm text-zinc-500 dark:text-zinc-400">
          {{ message }}
        </DialogDescription>
      </DialogHeader>

      <DialogFooter class="gap-2">
        <Button
          variant="outline"
          class="rounded-xl border-zinc-200 dark:border-zinc-700"
          @click="handleCancel"
        >
          {{ cancelText }}
        </Button>
        <Button
          v-if="variant === 'danger'"
          class="rounded-xl bg-red-500 hover:bg-red-600 text-white"
          @click="handleConfirm"
        >
          {{ confirmText }}
        </Button>
        <Button
          v-else
          class="rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-100"
          @click="handleConfirm"
        >
          {{ confirmText }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
