<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { settingsService, type KieConfig } from '@/services/settings'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
import { toast } from '@/components/ui/toast/use-toast'
import { Eye, EyeOff, Save, Trash2, Loader2, CheckCircle, XCircle, Key, Globe } from 'lucide-vue-next'

const apiToken = ref('')
const apiEndpoint = ref('https://api.kie.ai/api/v1/jobs/createTask')
const showToken = ref(false)
const isLoading = ref(false)
const isSaving = ref(false)
const isTesting = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)
const showDeleteDialog = ref(false)
const isConfigured = ref(false)

const loadConfig = async () => {
  isLoading.value = true
  try {
    const config: KieConfig = await settingsService.getKieConfig()
    apiToken.value = config.api_token || ''
    apiEndpoint.value = config.api_endpoint || 'https://api.kie.ai/api/v1/jobs/createTask'
    isConfigured.value = config.is_configured
  } catch (error) {
    console.error('加载配置失败:', error)
    toast({
      title: '加载失败',
      description: '无法加载 KIE API 配置',
      variant: 'destructive'
    })
  } finally {
    isLoading.value = false
  }
}

const handleSave = async () => {
  if (!apiToken.value.trim()) {
    toast({
      title: '保存失败',
      description: '请输入 API Token',
      variant: 'destructive'
    })
    return
  }

  isSaving.value = true
  try {
    await settingsService.saveKieConfig(apiToken.value.trim(), apiEndpoint.value.trim())
    isConfigured.value = true
    toast({
      title: '保存成功',
      description: 'KIE API 配置已保存'
    })
  } catch (error) {
    console.error('保存配置失败:', error)
    toast({
      title: '保存失败',
      description: '无法保存 KIE API 配置',
      variant: 'destructive'
    })
  } finally {
    isSaving.value = false
  }
}

const handleTest = async () => {
  if (!apiToken.value.trim()) {
    toast({
      title: '测试失败',
      description: '请先输入 API Token',
      variant: 'destructive'
    })
    return
  }

  isTesting.value = true
  testResult.value = null
  try {
    const result = await settingsService.testKieConfig()
    testResult.value = result
    if (result.success) {
      toast({
        title: '连接成功',
        description: 'KIE API 连接正常'
      })
    } else {
      toast({
        title: '连接失败',
        description: result.message,
        variant: 'destructive'
      })
    }
  } catch (error) {
    console.error('测试连接失败:', error)
    testResult.value = { success: false, message: '连接测试失败' }
    toast({
      title: '测试失败',
      description: '无法测试 KIE API 连接',
      variant: 'destructive'
    })
  } finally {
    isTesting.value = false
  }
}

const handleDelete = async () => {
  try {
    await settingsService.deleteKieConfig()
    apiToken.value = ''
    isConfigured.value = false
    testResult.value = null
    showDeleteDialog.value = false
    toast({
      title: '删除成功',
      description: 'KIE API 配置已删除'
    })
  } catch (error) {
    console.error('删除配置失败:', error)
    toast({
      title: '删除失败',
      description: '无法删除 KIE API 配置',
      variant: 'destructive'
    })
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-zinc-900 dark:text-zinc-100">设置</h1>
        <p class="text-zinc-500 dark:text-zinc-400 mt-1">配置 KIE API 以使用图片生成功能</p>
      </div>
      <div
        v-if="isConfigured"
        class="flex items-center gap-2 px-3 py-1.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full text-sm"
      >
        <CheckCircle class="w-4 h-4" />
        已配置
      </div>
      <div
        v-else
        class="flex items-center gap-2 px-3 py-1.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded-full text-sm"
      >
        <XCircle class="w-4 h-4" />
        未配置
      </div>
    </div>

    <Card class="bg-white/70 dark:bg-zinc-900/70 backdrop-blur-xl border-zinc-200 dark:border-zinc-800">
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <Key class="w-5 h-5 text-violet-500" />
          KIE API 配置
        </CardTitle>
        <CardDescription>
          配置 KIE API Token 以使用 Nano Banana 图片生成功能。API Token 将安全存储在本地数据库中。
        </CardDescription>
      </CardHeader>
      <CardContent class="space-y-6">
        <div v-if="isLoading" class="flex items-center justify-center py-8">
          <Loader2 class="w-6 h-6 animate-spin text-violet-500" />
          <span class="ml-2 text-zinc-500">加载配置中...</span>
        </div>

        <template v-else>
          <div class="space-y-2">
            <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">
              API Token <span class="text-red-500">*</span>
            </label>
            <div class="relative">
              <Input
                v-model="apiToken"
                :type="showToken ? 'text' : 'password'"
                placeholder="输入您的 KIE API Token"
                class="pr-10"
              />
              <button
                type="button"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300"
                @click="showToken = !showToken"
              >
                <Eye v-if="!showToken" class="w-4 h-4" />
                <EyeOff v-else class="w-4 h-4" />
              </button>
            </div>
            <p class="text-xs text-zinc-500 dark:text-zinc-400">
              从 KIE 平台获取您的 API Token
            </p>
          </div>

          <div class="space-y-2">
            <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-2">
              <Globe class="w-4 h-4" />
              API 端点
            </label>
            <Input
              v-model="apiEndpoint"
              placeholder="https://api.kie.ai/api/v1/jobs/createTask"
            />
            <p class="text-xs text-zinc-500 dark:text-zinc-400">
              默认端点通常无需修改
            </p>
          </div>

          <div
            v-if="testResult"
            class="flex items-center gap-2 p-3 rounded-lg"
            :class="
              testResult.success
                ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
            "
          >
            <CheckCircle v-if="testResult.success" class="w-4 h-4" />
            <XCircle v-else class="w-4 h-4" />
            <span class="text-sm">{{ testResult.message }}</span>
          </div>

          <div class="flex items-center gap-3 pt-4 border-t border-zinc-200 dark:border-zinc-800">
            <Button
              class="flex-1 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700"
              :disabled="isSaving || !apiToken.trim()"
              @click="handleSave"
            >
              <Loader2 v-if="isSaving" class="w-4 h-4 mr-2 animate-spin" />
              <Save v-else class="w-4 h-4 mr-2" />
              {{ isSaving ? '保存中...' : '保存配置' }}
            </Button>

            <Button
              variant="outline"
              :disabled="isTesting || !apiToken.trim()"
              @click="handleTest"
            >
              <Loader2 v-if="isTesting" class="w-4 h-4 mr-2 animate-spin" />
              <span v-else>测试连接</span>
            </Button>

            <Button
              v-if="isConfigured"
              variant="destructive"
              @click="showDeleteDialog = true"
            >
              <Trash2 class="w-4 h-4" />
            </Button>
          </div>
        </template>
      </CardContent>
    </Card>

    <Card class="bg-white/70 dark:bg-zinc-900/70 backdrop-blur-xl border-zinc-200 dark:border-zinc-800">
      <CardHeader>
        <CardTitle>使用说明</CardTitle>
      </CardHeader>
      <CardContent class="space-y-4 text-sm text-zinc-600 dark:text-zinc-400">
        <div class="space-y-2">
          <h4 class="font-medium text-zinc-900 dark:text-zinc-100">1. 获取 API Token</h4>
          <p>访问 KIE 平台并获取您的 API Token。</p>
        </div>
        <div class="space-y-2">
          <h4 class="font-medium text-zinc-900 dark:text-zinc-100">2. 配置 Token</h4>
          <p>将 API Token 粘贴到上方输入框中，点击保存。</p>
        </div>
        <div class="space-y-2">
          <h4 class="font-medium text-zinc-900 dark:text-zinc-100">3. 开始使用</h4>
          <p>在工作流画布中添加"生成图片"节点，输入提示词即可生成图片。</p>
        </div>
        <div class="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
          <p class="text-amber-700 dark:text-amber-400">
            <strong>注意：</strong>API Token 存储在本地数据库中，不会上传到服务器。请妥善保管您的 Token。
          </p>
        </div>
      </CardContent>
    </Card>

    <Dialog v-model:open="showDeleteDialog">
      <DialogContent class="sm:max-w-md rounded-2xl bg-white/95 dark:bg-zinc-900/95 backdrop-blur-xl">
        <DialogHeader>
          <DialogTitle>确认删除</DialogTitle>
          <DialogDescription>
            确定要删除 KIE API 配置吗？删除后将无法使用图片生成功能。
          </DialogDescription>
        </DialogHeader>
        <DialogFooter class="gap-2 sm:gap-0">
          <Button variant="outline" class="rounded-xl" @click="showDeleteDialog = false">
            取消
          </Button>
          <Button variant="destructive" class="rounded-xl" @click="handleDelete">
            删除
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
