import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

// 自定义 API 供渲染进程使用
const api = {
  // 获取后端端口
  getBackendPort: (): Promise<number | null> => ipcRenderer.invoke('get-backend-port'),

  // 后端日志相关
  subscribeBackendLogs: (callback: (log: string) => void) => {
    const handler = (_event: unknown, log: string) => callback(log)
    ipcRenderer.on('backend-log', handler)
    ipcRenderer.send('subscribe-backend-logs')
    return () => {
      ipcRenderer.removeListener('backend-log', handler)
      ipcRenderer.send('unsubscribe-backend-logs')
    }
  },
  getBackendLogs: (): Promise<string[]> => ipcRenderer.invoke('get-backend-logs'),

  // 打开目录
  openDirectory: (path: string): Promise<void> => ipcRenderer.invoke('open-directory', path),

  // 打开文件
  openFile: (path: string): Promise<void> => ipcRenderer.invoke('open-file', path),

  // 选择目录
  selectDirectory: (): Promise<string | null> => ipcRenderer.invoke('select-directory'),

  // 窗口控制
  windowMinimize: (): void => ipcRenderer.send('window-minimize'),
  windowMaximize: (): Promise<boolean> => ipcRenderer.invoke('window-maximize'),
  windowClose: (): void => ipcRenderer.send('window-close'),
  windowIsMaximized: (): Promise<boolean> => ipcRenderer.invoke('window-is-maximized'),

  // 平台信息
  platform: process.platform
}

// Use `contextBridge` APIs to expose Electron APIs to
// renderer only if context isolation is enabled, otherwise
// just add to the DOM global.
if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error(error)
  }
} else {
  // @ts-ignore (define in dts)
  window.electron = electronAPI
  // @ts-ignore (define in dts)
  window.api = api
}
