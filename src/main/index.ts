import { app, shell, BrowserWindow, ipcMain, dialog } from 'electron'
import { join } from 'path'
import { existsSync, appendFileSync, mkdirSync } from 'fs'
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
// 日志文件路径
let logFilePath: string | null = null
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
 * 获取日志目录路径（软件所在目录下的 logs 目录）
 */
function getLogDir(): string {
  let baseDir: string
  
  if (is.dev) {
    // 开发环境：使用项目根目录
    baseDir = join(__dirname, '../..')
  } else {
    // 生产环境：使用软件所在目录（resourcesPath 的父目录）
    baseDir = join(process.resourcesPath, '..')
  }
  
  const logDir = join(baseDir, 'logs')
  if (!existsSync(logDir)) {
    mkdirSync(logDir, { recursive: true })
  }
  return logDir
}

/**
 * 获取当前日期字符串 (YYYY-MM-DD)
 */
function getDateString(): string {
  const now = new Date()
  return now.toISOString().split('T')[0]
}

/**
 * 初始化日志文件
 */
function initLogFile(): void {
  const logDir = getLogDir()
  logFilePath = join(logDir, `backend-${getDateString()}.log`)
  console.log('[Log] 日志文件路径:', logFilePath)
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

  // 写入文件
  if (logFilePath) {
    try {
      appendFileSync(logFilePath, logLine + '\n', 'utf-8')
    } catch (err) {
      console.error('[Log] 写入日志文件失败:', err)
    }
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
  const logDir = getLogDir()

  if (isDev) {
    // 开发环境：使用 uv run python main.py
    // __dirname = out/main，需要向上两级到达项目根目录
    const projectRoot = join(__dirname, '../..')
    console.log('[Backend] 项目根目录:', projectRoot)

    backendProcess = spawn('uv', ['run', 'python', 'main.py'], {
      cwd: projectRoot,
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: true,
      env: {
        ...process.env,
        LOG_DIR: logDir
      }
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
    const backendDir = join(resourcesPath, 'backend')

    // 数据库存储在用户数据目录，覆盖安装时不会被删除
    const dbPath = join(app.getPath('userData'), 'ai_video_production.db')
    console.log('[Backend] 数据库路径:', dbPath)
    console.log('[Backend] 资源路径:', resourcesPath)
    console.log('[Backend] 后端目录:', backendDir)
    console.log('[Backend] 后端可执行文件路径:', backendPath)

    // 检查后端可执行文件是否存在
    if (!existsSync(backendPath)) {
      const errorMsg = `后端可执行文件不存在: ${backendPath}`
      console.error('[Backend]', errorMsg)
      appendLog('stderr', errorMsg)
      return
    }

    console.log('[Backend] 后端可执行文件存在，准备启动...')

    backendProcess = spawn(backendPath, [], {
      cwd: backendDir,
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: true,
      env: {
        ...process.env,
        DATABASE_URL: `sqlite+aiosqlite:///${dbPath}`,
        LOG_DIR: logDir
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
    const errorMsg = `后端进程启动失败: ${err.message}`
    console.error('[Backend]', errorMsg)
    appendLog('stderr', errorMsg)
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

// IPC handler: 获取日志目录路径
ipcMain.handle('get-log-dir', () => {
  return getLogDir()
})

// IPC handler: 打开日志目录
ipcMain.handle('open-log-dir', async () => {
  const logDir = getLogDir()
  await shell.openPath(logDir)
})

// Electron 完成初始化并准备创建浏览器窗口时调用此方法
// 某些 API 只能在此事件发生后才能使用
app.whenReady().then(() => {
  electronApp.setAppUserModelId('com.electron')

  // 初始化日志文件
  initLogFile()

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  setupAutoUpdater()

  startBackend()

  createWindow()

  mainWindow?.webContents.on('did-finish-load', () => {
    setTimeout(() => {
      setImmediate(() => {
        checkForUpdates(true)
      })
    }, 5000)
  })

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
