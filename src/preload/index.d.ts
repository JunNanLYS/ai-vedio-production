import { ElectronAPI } from '@electron-toolkit/preload'

interface UpdateInfo {
  available: boolean
  version?: string
  releaseDate?: string
  releaseNotes?: string
  downloading: boolean
  progress: number
}

interface DownloadProgress {
  percent: number
  transferred: number
  total: number
  bytesPerSecond: number
}

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
      checkForUpdates: (silent?: boolean) => Promise<void>
      downloadUpdate: () => Promise<void>
      quitAndInstall: () => Promise<void>
      getUpdateInfo: () => Promise<UpdateInfo>
      getAppVersion: () => Promise<string>
      onUpdateAvailable: (callback: (info: UpdateInfo) => void) => void
      onUpdateNotAvailable: (callback: () => void) => void
      onUpdateProgress: (callback: (progress: DownloadProgress) => void) => void
      onUpdateDownloaded: (callback: () => void) => void
      onUpdateError: (callback: (error: string) => void) => void
      platform: NodeJS.Platform
    }
  }
}
