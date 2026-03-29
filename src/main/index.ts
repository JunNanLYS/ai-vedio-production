import { app, shell, BrowserWindow, ipcMain, dialog } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import { spawn, ChildProcess } from 'child_process'
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
  logSubscribers.forEach(win => {
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
    const backendExeName = process.platform === 'win32' 
      ? 'ai-video-backend.exe' 
      : 'ai-video-backend'
    
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
    // Windows 使用 taskkill 强制结束进程树
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', String(backendProcess.pid), '/f', '/t'])
    } else {
      // macOS/Linux 使用 SIGTERM
      backendProcess.kill('SIGTERM')
    }
    backendProcess = null
    backendPort = null
  }
}

function createWindow(): void {
  // 创建浏览器窗口
  const mainWindow = new BrowserWindow({
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
      webSecurity: false  // 允许跨域请求
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // 基于 electron-vite cli 的 HMR
  // 开发环境加载远程 URL，生产环境加载本地 html 文件
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
    await new Promise(resolve => setTimeout(resolve, 100))
  }
  
  return backendPort
})

// IPC handler: 订阅后端日志
ipcMain.on('subscribe-backend-logs', (event) => {
  const win = BrowserWindow.fromWebContents(event.sender)
  if (win) {
    logSubscribers.add(win)
    // 发送历史日志
    backendLogs.forEach(log => {
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
  win?.close()
})

// IPC handler: 获取窗口最大化状态
ipcMain.handle('window-is-maximized', (event) => {
  const win = BrowserWindow.fromWebContents(event.sender)
  return win?.isMaximized() ?? false
})

// Electron 完成初始化并准备创建浏览器窗口时调用此方法
// 某些 API 只能在此事件发生后才能使用
app.whenReady().then(() => {
  // 为 Windows 设置应用用户模型 ID
  electronApp.setAppUserModelId('com.electron')

  // 开发环境默认通过 F12 打开或关闭 DevTools
  // 生产环境忽略 CommandOrControl + R
  // 参见 https://github.com/alex8088/electron-toolkit/tree/master/packages/utils
  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  // 启动 Python 后端
  startBackend()

  createWindow()

  app.on('activate', function () {
    // 在 macOS 上，当点击 dock 图标且没有其他窗口打开时，
    // 通常会在应用中重新创建一个窗口
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// 当所有窗口都关闭时退出应用，macOS 除外
// 在 macOS 上，应用及其菜单栏通常会保持活动状态，直到用户使用 Cmd + Q 明确退出
app.on('window-all-closed', () => {
  // 停止后端进程
  stopBackend()

  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// 应用退出前确保后端进程已停止
app.on('before-quit', () => {
  stopBackend()
})
