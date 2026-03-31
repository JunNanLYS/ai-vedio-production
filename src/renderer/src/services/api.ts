let backendUrl: string | null = null

async function getBackendUrl(): Promise<string> {
  if (backendUrl) {
    return backendUrl
  }

  const port = await window.api.getBackendPort()
  if (!port) {
    throw new Error('无法获取后端端口')
  }

  backendUrl = `http://127.0.0.1:${port}`
  return backendUrl
}

function setBackendPort(port: number): void {
  backendUrl = `http://127.0.0.1:${port}`
}

function getBackendUrlSync(): string | null {
  return backendUrl
}

async function request<T>(endpoint: string, options?: RequestInit, retries = 2): Promise<T> {
  const url = await getBackendUrl()

  try {
    const response = await fetch(`${url}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers
      },
      ...options
    })

    if (!response.ok) {
      throw new Error(`请求失败: ${response.status}`)
    }

    return response.json()
  } catch (err) {
    if (retries > 0 && err instanceof TypeError) {
      console.warn('[API] 连接失败，重试中...')
      await new Promise((resolve) => setTimeout(resolve, 500))
      return request<T>(endpoint, options, retries - 1)
    }
    throw err
  }
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),
  post: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  put: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, { method: 'PUT', body: JSON.stringify(data) }),
  del: <T>(endpoint: string) => request<T>(endpoint, { method: 'DELETE' })
}

export { getBackendUrl, setBackendPort, getBackendUrlSync }
