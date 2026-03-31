import { api } from './api'

export interface KieConfig {
  api_token: string
  api_endpoint: string
  is_configured: boolean
}

export interface TestResult {
  success: boolean
  message: string
}

export const settingsService = {
  getKieConfig: () => api.get<KieConfig>('/api/settings/kie'),
  saveKieConfig: (apiToken: string, apiEndpoint?: string) =>
    api.post<{ message: string }>('/api/settings/kie', {
      api_token: apiToken,
      api_endpoint: apiEndpoint || 'https://api.kie.ai/api/v1/jobs/createTask'
    }),
  deleteKieConfig: () => api.del<{ message: string }>('/api/settings/kie'),
  testKieConfig: () => api.post<TestResult>('/api/settings/kie/test', {})
}
