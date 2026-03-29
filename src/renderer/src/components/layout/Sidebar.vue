<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { LayoutDashboard, FileText, GitBranch, FolderOpen, Wifi } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

interface NavItem {
  name: string
  path: string
  icon: typeof LayoutDashboard
  label: string
}

const navItems: NavItem[] = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard, label: '仪表盘' },
  { name: 'Orders', path: '/orders', icon: FileText, label: '订单管理' },
  { name: 'Workflows', path: '/workflows', icon: GitBranch, label: '工作流' },
  { name: 'Assets', path: '/assets', icon: FolderOpen, label: '资产管理' },
  { name: 'Connection', path: '/connection', icon: Wifi, label: '连通测试' }
]

const isActive = (path: string): boolean => {
  return route.path === path
}

const handleNavigate = (path: string): void => {
  router.push(path)
}
</script>

<template>
  <aside
    class="w-60 h-full bg-white/70 dark:bg-zinc-900/70 backdrop-blur-xl border-r border-black/5 dark:border-white/5 flex flex-col py-6"
  >
    <nav class="flex-1 px-3 space-y-1">
      <button
        v-for="item in navItems"
        :key="item.path"
        @click="handleNavigate(item.path)"
        v-motion
        :initial="{ scale: 1 }"
        :hovered="{ scale: 1.02 }"
        :tapped="{ scale: 0.96 }"
        :transition="{ type: 'spring', stiffness: 400, damping: 25 }"
        :class="[
          'w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all duration-200',
          isActive(item.path)
            ? 'bg-zinc-900/5 dark:bg-white/10 text-zinc-900 dark:text-white font-medium'
            : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-900/5 dark:hover:bg-white/5'
        ]"
      >
        <component
          :is="item.icon"
          :size="20"
          :stroke-width="1.5"
          :class="[
            'transition-colors',
            isActive(item.path)
              ? 'text-zinc-900 dark:text-white'
              : 'text-zinc-500 dark:text-zinc-500'
          ]"
        />
        <span class="text-sm">{{ item.label }}</span>
      </button>
    </nav>
  </aside>
</template>
