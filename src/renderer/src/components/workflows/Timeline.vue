<script setup lang="ts">
import type { Product } from '@/types'
import ProductCard from './ProductCard.vue'

interface Props {
  steps: string[]
  products: Product[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  productClick: [product: Product]
  productMovePrev: [product: Product]
  productMoveNext: [product: Product]
}>()

const getProductsByStep = (stepIndex: number) => {
  return props.products.filter((p) => p.current_step === stepIndex)
}

const canMovePrev = (product: Product) => {
  return product.current_step > 0
}

const canMoveNext = (product: Product) => {
  return product.current_step < props.steps.length - 1
}
</script>

<template>
  <div class="space-y-6">
    <div v-for="(step, index) in steps" :key="index" class="relative">
      <div class="flex items-center gap-3 mb-4">
        <div
          class="w-8 h-8 rounded-full bg-zinc-900 dark:bg-white flex items-center justify-center text-white dark:text-zinc-900 text-sm font-semibold"
        >
          {{ index + 1 }}
        </div>
        <span class="text-base font-semibold text-zinc-900 dark:text-zinc-100">{{ step }}</span>
      </div>

      <div class="ml-4 pl-6 border-l-2 border-zinc-200 dark:border-zinc-800">
        <div v-if="getProductsByStep(index).length > 0" class="flex flex-wrap gap-2 py-3">
          <ProductCard
            v-for="product in getProductsByStep(index)"
            :key="product.id"
            :product="product"
            :can-move-prev="canMovePrev(product)"
            :can-move-next="canMoveNext(product)"
            :current-step-name="step"
            @click="emit('productClick', product)"
            @move-prev="emit('productMovePrev', product)"
            @move-next="emit('productMoveNext', product)"
          />
        </div>
        <div v-else class="py-4 text-sm text-zinc-400 dark:text-zinc-500">
          暂无产品
        </div>
      </div>

      <div v-if="index < steps.length - 1" class="flex justify-start pl-3 py-1">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" class="text-zinc-300 dark:text-zinc-600">
          <path
            d="M12 5V19M12 19L6 13M12 19L18 13"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </div>
    </div>
  </div>
</template>
