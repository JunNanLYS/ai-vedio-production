<script setup lang="ts">
import TitleBar from './TitleBar.vue'
import Sidebar from './Sidebar.vue'
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <div class="h-screen w-screen flex flex-col bg-zinc-50 dark:bg-zinc-950 overflow-hidden">
    <TitleBar />
    <div class="flex-1 flex overflow-hidden">
      <Sidebar />
      <main class="flex-1 overflow-auto p-6">
        <router-view v-slot="{ Component }">
          <Transition name="page" mode="out-in">
            <component :is="Component" :key="route.path" />
          </Transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<style scoped>
.page-enter-active,
.page-leave-active {
  transition: all 0.2s ease-out;
}

.page-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.page-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>
