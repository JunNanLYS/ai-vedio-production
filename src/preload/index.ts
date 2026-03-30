import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

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

const api = {
  getBackendPort: (): Promise<number | null> => ipcRenderer.invoke('get-backend-port'),

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

  openDirectory: (path: string): Promise<void> => ipcRenderer.invoke('open-directory', path),

  openFile: (path: string): Promise<void> => ipcRenderer.invoke('open-file', path),

  selectDirectory: (): Promise<string | null> => ipcRenderer.invoke('select-directory'),

  windowMinimize: (): void => ipcRenderer.send('window-minimize'),
  windowMaximize: (): Promise<boolean> => ipcRenderer.invoke('window-maximize'),
  windowClose: (): void => ipcRenderer.send('window-close'),
  windowIsMaximized: (): Promise<boolean> => ipcRenderer.invoke('window-is-maximized'),

  checkForUpdates: (silent: boolean = false): Promise<void> => 
    ipcRenderer.invoke('check-for-updates', silent),
  downloadUpdate: (): Promise<void> => ipcRenderer.invoke('download-update'),
  quitAndInstall: (): Promise<void> => ipcRenderer.invoke('quit-and-install'),
  getUpdateInfo: (): Promise<UpdateInfo> => ipcRenderer.invoke('get-update-info'),
  getAppVersion: (): Promise<string> => ipcRenderer.invoke('get-app-version'),

  onUpdateAvailable: (callback: (info: UpdateInfo) => void) => {
    ipcRenderer.on('update-available', (_event, info) => callback(info))
  },
  onUpdateNotAvailable: (callback: () => void) => {
    ipcRenderer.on('update-not-available', () => callback())
  },
  onUpdateProgress: (callback: (progress: DownloadProgress) => void) => {
    ipcRenderer.on('update-progress', (_event, progress) => callback(progress))
  },
  onUpdateDownloaded: (callback: () => void) => {
    ipcRenderer.on('update-downloaded', () => callback())
  },
  onUpdateError: (callback: (error: string) => void) => {
    ipcRenderer.on('update-error', (_event, error) => callback(error))
  },

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
