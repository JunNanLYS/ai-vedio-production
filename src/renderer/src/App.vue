<script setup lang="ts">
import { ref, onMounted } from 'vue'
import MainLayout from './components/layout/MainLayout.vue'
import { setBackendPort } from './services/api'

const isReady = ref(false)
const error = ref<string | null>(null)

function handleRetry() {
  window.location.reload()
}

onMounted(async () => {
  try {
    const port = await window.api.getBackendPort()
    if (port) {
      setBackendPort(port)
      isReady.value = true
    } else {
      error.value = '后端服务启动失败'
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '未知错误'
  }
})
</script>

<template>
  <div v-if="!isReady" class="loading-screen">
    <div class="loading-content">
      <div v-if="error" class="error-state">
        <div class="error-icon">⚠️</div>
        <p class="error-text">{{ error }}</p>
        <button @click="handleRetry" class="retry-btn">
          重试
        </button>
      </div>
      <div v-else class="loading-state">
        <div class="spinner"></div>
        <p class="loading-text">正在加载...</p>
      </div>
    </div>
  </div>
  <MainLayout v-else />
</template>

<style scoped>
.loading-screen {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #18181b 0%, #27272a 100%);
}

.loading-content {
  text-align: center;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  color: #a1a1aa;
  font-size: 14px;
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.error-icon {
  font-size: 48px;
}

.error-text {
  color: #ef4444;
  font-size: 14px;
}

.retry-btn {
  margin-top: 8px;
  padding: 8px 24px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: #2563eb;
}
</style>
