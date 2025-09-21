import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'
import type { ApiError } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface ApiConfig {
  baseURL: string
  timeout: number
  headers: Record<string, string>
}

const defaultConfig: ApiConfig = {
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
}

export class ApiClient {
  private client: AxiosInstance

  constructor(config: ApiConfig = defaultConfig) {
    this.client = axios.create(config)
    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth headers if available
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        // Add request ID for tracking
        config.headers['X-Request-ID'] = crypto.randomUUID()

        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        // Handle common errors
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token')
          // Only redirect to login if we're not already there
          if (!window.location.pathname.includes('/login')) {
            window.location.href = '/login'
          }
        }
        return Promise.reject(this.transformError(error))
      }
    )
  }

  private transformError(error: any): ApiError {
    // Handle different error types
    if (error.code === 'ECONNABORTED') {
      return {
        type: 'timeout',
        status: 408,
        message: 'Request timeout. Please try again.',
        details: { code: error.code }
      }
    }

    if (!error.response) {
      return {
        type: 'network',
        status: 0,
        message: 'Network error. Please check your connection.',
        details: { code: error.code }
      }
    }

    const status = error.response.status
    const responseData = error.response.data

    return {
      type: status >= 500 ? 'server' : status >= 400 ? 'client' : 'network',
      status,
      message: responseData?.detail || responseData?.message || error.message || 'An error occurred',
      details: responseData
    }
  }

  // Generic HTTP methods
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get(url, config)
    return response.data
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post(url, data, config)
    return response.data
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put(url, data, config)
    return response.data
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete(url, config)
    return response.data
  }

  async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch(url, data, config)
    return response.data
  }

  // File upload with progress
  async uploadFile<T>(
    url: string,
    file: File,
    fieldName: string = 'file',
    onProgress?: (progress: number) => void,
    additionalData?: Record<string, string>
  ): Promise<T> {
    const formData = new FormData()
    formData.append(fieldName, file)

    // Add additional form fields
    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, value)
      })
    }

    const response = await this.client.post(url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000, // Extended timeout for file uploads
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          onProgress(percentCompleted)
        }
      }
    })

    return response.data
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.get('/health')
  }
}

// Create default instance
export const apiClient = new ApiClient()