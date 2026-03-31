import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { title: '仪表盘' }
  },
  {
    path: '/orders',
    name: 'Orders',
    component: () => import('../views/OrdersView.vue'),
    meta: { title: '订单管理' }
  },
  {
    path: '/workflows',
    name: 'Workflows',
    component: () => import('../views/WorkflowsView.vue'),
    meta: { title: '工作流' }
  },
  {
    path: '/assets',
    name: 'Assets',
    component: () => import('../views/AssetsView.vue'),
    meta: { title: '资产管理' }
  },
  {
    path: '/connection',
    name: 'Connection',
    component: () => import('../views/ConnectionView.vue'),
    meta: { title: '连通测试' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { title: '设置' }
  },
  {
    path: '/update',
    name: 'Update',
    component: () => import('../views/UpdateView.vue'),
    meta: { title: '软件更新' }
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
