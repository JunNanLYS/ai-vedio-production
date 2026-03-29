import { ElectronAPI } from '@electron-toolkit/preload'

declare global {
  interface Window {
    electron: ElectronAPI
    api: {
      getBackendPort: () => Promise<number | null>
      subscribeBackendLogs: (callback: (log: string) => void) => () => void
      getBackendLogs: () => Promise<string[]>
      openDirectory: (path: string) => Promise<void>
      openFile: (path: string) => Promise<void>
      selectDirectory: () => Promise<string | null>
      windowMinimize: () => void
      windowMaximize: () => Promise<boolean>
      windowClose: () => void
      windowIsMaximized: () => Promise<boolean>
      platform: NodeJS.Platform
    }
  }
}
