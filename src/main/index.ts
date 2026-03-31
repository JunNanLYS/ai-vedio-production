import { app, shell, BrowserWindow, ipcMain, dialog } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import { spawn, ChildProcess } from 'child_process'
import { autoUpdater } from 'electron-updater'
import icon from '../../resources/icon.png?asset'

// 后端端口号
let backendPort: number | null = null
// 后端进程实例
let backendProcess: ChildProcess | null = null
// 后端日志缓冲区（最多保留 1000 条）
const backendLogs: string[] = []
const MAX_LOGS = 1000
// 日志订阅的窗口集合
const logSubscribers = new Set<BrowserWindow>()
// 主窗口引用
let mainWindow: BrowserWindow | null = null
// 是否允许关闭窗口
let allowClose = false
// 更新信息
let updateInfo: {
  available: boolean
  version?: string
  releaseDate?: string
  releaseNotes?: string
  downloading: boolean
  progress: number
} = {
  available: false,
  downloading: false,
  progress: 0
}

/**
 * 添加日志并广播给订阅者
 */
function appendLog(type: 'stdout' | 'stderr', content: string): void {
  const timestamp = new Date().toISOString()
  const logLine = `[${timestamp}] [${type.toUpperCase()}] ${content.trim()}`

  // 添加到缓冲区
  backendLogs.push(logLine)
  if (backendLogs.length > MAX_LOGS) {
    backendLogs.shift()
  }

  // 广播给所有订阅者
  logSubscribers.forEach((win) => {
    if (!win.isDestroyed()) {
      win.webContents.send('backend-log', logLine)
    }
  })
}

/**
 * 启动 Python 后端子进程
 */
function startBackend(): void {
  const isDev = is.dev

  if (isDev) {
    // 开发环境：使用 uv run python main.py
    // __dirname = out/main，需要向上两级到达项目根目录
    const projectRoot = join(__dirname, '../..')
    console.log('[Backend] 项目根目录:', projectRoot)

    backendProcess = spawn('uv', ['run', 'python', 'main.py'], {
      cwd: projectRoot,
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: true
    })
  } else {
    // 生产环境：使用 Nuitka 打包后的可执行文件
    const resourcesPath = process.resourcesPath

    // Windows: ai-video-backend.exe
    // macOS/Linux: ai-video-backend
    const backendExeName =
      process.platform === 'win32' ? 'ai-video-backend.exe' : 'ai-video-backend'

    // 检查 backend 目录下的可执行文件
    const backendPath = join(resourcesPath, 'backend', backendExeName)

    // 数据库存储在用户数据目录，覆盖安装时不会被删除
    const dbPath = join(app.getPath('userData'), 'ai_video_production.db')
    console.log('[Backend] 数据库路径:', dbPath)

    console.log('[Backend] 生产环境后端路径:', backendPath)

    backendProcess = spawn(backendPath, [], {
      cwd: join(resourcesPath, 'backend'),
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: false,
      env: {
        ...process.env,
        DATABASE_URL: `sqlite:///${dbPath}`
      }
    })
  }

  // 处理标准输出，解析端口号
  backendProcess.stdout?.on('data', (data: Buffer) => {
    const output = data.toString()
    console.log('[Backend stdout]:', output)
    appendLog('stdout', output)

    // 解析 SERVER_PORT:{port} 格式的输出
    const portMatch = output.match(/SERVER_PORT:(\d+)/)
    if (portMatch) {
      backendPort = parseInt(portMatch[1], 10)
      console.log(`[Backend] 服务已启动，端口: ${backendPort}`)
    }
  })

  // 处理错误输出
  backendProcess.stderr?.on('data', (data: Buffer) => {
    const output = data.toString()
    console.error('[Backend stderr]:', output)
    appendLog('stderr', output)
  })

  // 处理进程退出
  backendProcess.on('close', (code) => {
    const message = `后端进程已退出，退出码: ${code}`
    console.log(`[Backend] ${message}`)
    appendLog('stderr', message)
    backendProcess = null
    backendPort = null
  })

  // 处理进程错误
  backendProcess.on('error', (err) => {
    console.error('[Backend] 进程启动失败:', err)
    backendProcess = null
  })
}

/**
 * 停止 Python 后端子进程
 */
function stopBackend(): void {
  if (backendProcess) {
    console.log('[Backend] 正在停止后端进程...')
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', String(backendProcess.pid), '/f', '/t'])
    } else {
      backendProcess.kill('SIGTERM')
    }
    backendProcess = null
    backendPort = null
  }
}

function setupAutoUpdater(): void {
  autoUpdater.autoDownload = false
  autoUpdater.autoInstallOnAppQuit = true
  autoUpdater.forceDevUpdateConfig = true

  autoUpdater.on('checking-for-update', () => {
    console.log('[Updater] 正在检查更新...')
  })

  autoUpdater.on('update-available', (info) => {
    console.log('[Updater] 发现新版本:', info.version)
    updateInfo = {
      available: true,
      version: info.version,
      releaseDate: info.releaseDate,
      releaseNotes:
        typeof info.releaseNotes === 'string'
          ? info.releaseNotes
          : info.releaseNotes?.map((n) => n.note).join('\n'),
      downloading: false,
      progress: 0
    }
    mainWindow?.webContents.send('update-available', updateInfo)
  })

  autoUpdater.on('update-not-available', () => {
    console.log('[Updater] 当前已是最新版本')
    updateInfo = { available: false, downloading: false, progress: 0 }
    mainWindow?.webContents.send('update-not-available')
  })

  autoUpdater.on('download-progress', (progressInfo) => {
    console.log(`[Updater] 下载进度: ${progressInfo.percent.toFixed(1)}%`)
    updateInfo.progress = progressInfo.percent
    updateInfo.downloading = true
    mainWindow?.webContents.send('update-progress', {
      percent: progressInfo.percent,
      transferred: progressInfo.transferred,
      total: progressInfo.total,
      bytesPerSecond: progressInfo.bytesPerSecond
    })
  })

  autoUpdater.on('update-downloaded', () => {
    console.log('[Updater] 更新下载完成')
    updateInfo.downloading = false
    updateInfo.progress = 100
    mainWindow?.webContents.send('update-downloaded')
  })

  autoUpdater.on('error', (error) => {
    console.error('[Updater] 更新错误:', error)
    updateInfo.downloading = false
    mainWindow?.webContents.send('update-error', error.message)
  })
}

async function checkForUpdates(silent: boolean = false): Promise<void> {
  try {
    await autoUpdater.checkForUpdates()
  } catch (error) {
    console.error('[Updater] 检查更新失败:', error)
    if (!silent) {
      mainWindow?.webContents.send('update-error', '检查更新失败')
    }
  }
}

async function downloadUpdate(): Promise<void> {
  if (updateInfo.available && !updateInfo.downloading) {
    try {
      updateInfo.downloading = true
      await autoUpdater.downloadUpdate()
    } catch (error) {
      console.error('[Updater] 下载更新失败:', error)
      updateInfo.downloading = false
      mainWindow?.webContents.send('update-error', '下载更新失败')
    }
  }
}

function quitAndInstall(): void {
  autoUpdater.quitAndInstall(false, true)
}

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    show: false,
    autoHideMenuBar: true,
    frame: false,
    ...(process.platform === 'darwin' ? { titleBarStyle: 'hiddenInset' } : {}),
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      webSecurity: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow?.show()
  })

  mainWindow.on('close', (event) => {
    if (!allowClose) {
      event.preventDefault()
      mainWindow?.webContents.send('prepare-close')
    }
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// IPC handler: 获取后端端口号（等待后端就绪）
ipcMain.handle('get-backend-port', async () => {
  // 等待后端就绪，最多等待 30 秒
  const timeout = 30000
  const startTime = Date.now()

  while (!backendPort && Date.now() - startTime < timeout) {
    await new Promise((resolve) => setTimeout(resolve, 100))
  }

  return backendPort
})

// IPC handler: 订阅后端日志
ipcMain.on('subscribe-backend-logs', (event) => {
  const win = BrowserWindow.fromWebContents(event.sender)
  if (win) {
    logSubscribers.add(win)
    // 发送历史日志
    backendLogs.forEach((log) => {
      win.webContents.send('backend-log', log)
    })
  }
})

// IPC handler: 取消订阅后端日志
ipcMain.on('unsubscribe-backend-logs', (event) => {
  const win = BrowserWindow.fromWebContents(event.sender)
  if (win) {
    logSubscribers.delete(win)
  }
})

// IPC handler: 获取历史日志
ipcMain.handle('get-backend-logs', () => {
  return [...backendLogs]
})

// IPC handler: 打开目录
ipcMain.handle('open-directory', async (_, path: string) => {
  await shell.openPath(path)
})

// IPC handler: 打开文件
ipcMain.handle('open-file', async (_, path: string) => {
  await shell.openPath(path)
})

// IPC handler: 选择目录
ipcMain.handle('select-directory', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openDirectory', 'createDirectory'],
    title: '选择项目保存位置'
  })
  if (result.canceled || result.filePaths.length === 0) {
    return null
  }
  return result.filePaths[0]
})

// IPC handler: 窗口最小化
ipcMain.on('window-minimize', (event) => {
  const win = BrowserWindow.fromWebContents(event.sender)
  win?.minimize()
})

// IPC handler: 窗口最大化/还原
ipcMain.handle('window-maximize', (event) => {
  const win = BrowserWindow.fromWebContents(event.sender)
  if (win) {
    if (win.isMaximized()) {
      win.unmaximize()
      return false
    } else {
      win.maximize()
      return true
    }
  }
  return false
})

// IPC handler: 窗口关闭
ipcMain.on('window-close', (event) => {
  const win = BrowserWindow.fromWebContents(event.sender)
  if (win) {
    win.webContents.send('prepare-close')
  }
})

// IPC handler: 允许关闭窗口
ipcMain.on('allow-close', () => {
  allowClose = true
  mainWindow?.close()
})

// IPC handler: 获取窗口最大化状态
ipcMain.handle('window-is-maximized', (event) => {
  const win = BrowserWindow.fromWebContents(event.sender)
  return win?.isMaximized() ?? false
})

// IPC handler: 检查更新
ipcMain.handle('check-for-updates', async (_, silent: boolean = false) => {
  await checkForUpdates(silent)
})

// IPC handler: 下载更新
ipcMain.handle('download-update', async () => {
  await downloadUpdate()
})

// IPC handler: 安装更新
ipcMain.handle('quit-and-install', () => {
  quitAndInstall()
})

// IPC handler: 获取更新信息
ipcMain.handle('get-update-info', () => {
  return updateInfo
})

// IPC handler: 获取应用版本
ipcMain.handle('get-app-version', () => {
  return app.getVersion()
})

// Electron 完成初始化并准备创建浏览器窗口时调用此方法
// 某些 API 只能在此事件发生后才能使用
app.whenReady().then(() => {
  electronApp.setAppUserModelId('com.electron')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  setupAutoUpdater()

  startBackend()

  createWindow()

  setTimeout(() => {
    checkForUpdates(true)
  }, 3000)

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  stopBackend()

  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  stopBackend()
})
