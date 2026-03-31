<script setup lang="ts">
import { cn } from '@/lib/utils'
import type { Product } from '@/types'

interface Props {
  product: Product
  canMovePrev?: boolean
  canMoveNext?: boolean
  currentStepName?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  click: [product: Product]
  movePrev: [product: Product]
  moveNext: [product: Product]
}>()

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return 'bg-green-500'
    case 'in_progress':
      return 'bg-blue-500'
    case 'pending':
      return 'bg-gray-400'
    default:
      return 'bg-gray-300'
  }
}

const getDisplayStatus = () => {
  if (props.currentStepName) {
    return props.currentStepName
  }
  switch (props.product.status) {
    case 'completed':
      return '已完成'
    case 'in_progress':
      return '进行中'
    case 'pending':
      return '待处理'
    default:
      return props.product.status
  }
}

const handleMovePrev = (e: Event) => {
  e.stopPropagation()
  emit('movePrev', props.product)
}

const handleMoveNext = (e: Event) => {
  e.stopPropagation()
  emit('moveNext', props.product)
}
</script>

<template>
  <div class="product-card" @click="emit('click', product)">
    <div class="product-card__content">
      <span class="product-card__name">{{ product.name }}</span>
      <div class="product-card__status">
        <span :class="cn('product-card__status-dot', getStatusColor(product.status))"></span>
        <span class="product-card__status-text">{{ getDisplayStatus() }}</span>
      </div>
    </div>
    <div class="product-card__actions">
      <button
        class="product-card__action-btn"
        :class="{ 'product-card__action-btn--disabled': !canMovePrev }"
        :disabled="!canMovePrev"
        title="上一步"
        @click="handleMovePrev"
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path
            d="M8 2L4 6L8 10"
            stroke="currentColor"
            stroke-width="1.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
      <button
        class="product-card__action-btn"
        :class="{ 'product-card__action-btn--disabled': !canMoveNext }"
        :disabled="!canMoveNext"
        title="下一步"
        @click="handleMoveNext"
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path
            d="M4 2L8 6L4 10"
            stroke="currentColor"
            stroke-width="1.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.product-card {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 12px;
  padding: 10px 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.product-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.product-card:active {
  transform: translateY(0);
}

.product-card__content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.product-card__name {
  font-size: 14px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
}

.product-card__status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.product-card__status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.product-card__status-text {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.5);
}

.product-card__actions {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-left: 4px;
}

.product-card__action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.5);
  transition: all 0.15s ease;
}

.product-card__action-btn:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.1);
  color: rgba(0, 0, 0, 0.8);
}

.product-card__action-btn--disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

:global(.dark) .product-card {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.1);
}

:global(.dark) .product-card__name {
  color: rgba(255, 255, 255, 0.9);
}

:global(.dark) .product-card__status-text {
  color: rgba(255, 255, 255, 0.5);
}

:global(.dark) .product-card__action-btn {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.5);
}

:global(.dark) .product-card__action-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.8);
}
</style>
