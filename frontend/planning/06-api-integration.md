# API Integration Specification

## Overview
This document defines the API integration layer, HTTP client configuration, and communication patterns with the FastAPI backend that orchestrates the Coral Protocol multi-agent pipeline.

## API Architecture

### Base Configuration

```typescript
// src/services/api.ts
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'

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
```

### HTTP Client Setup

```typescript
class ApiClient {
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
          window.location.href = '/login'
        }
        return Promise.reject(this.transformError(error))
      }
    )
  }

  private transformError(error: any): ApiError {
    return {
      type: error.response?.status >= 500 ? 'server' : 'client',
      status: error.response?.status || 0,
      message: error.response?.data?.detail || error.message,
      details: error.response?.data
    }
  }
}
```

## API Endpoints

### Research Endpoints

```typescript
interface ResearchRequest {
  linkedinUrl: string
  cvFile: File
  jobDescription?: string
  jobDescriptionFile?: File
}

interface ResearchResponse {
  researchId: string
  status: 'initiated' | 'processing' | 'completed' | 'failed'
  estimatedDuration?: number
}

class ResearchApi {
  constructor(private client: ApiClient) {}

  // Submit research request with file uploads
  async submitResearch(data: ResearchRequest): Promise<ResearchResponse> {
    const formData = new FormData()
    formData.append('linkedin_url', data.linkedinUrl)
    formData.append('cv_file', data.cvFile)

    if (data.jobDescription) {
      formData.append('job_description', data.jobDescription)
    }
    if (data.jobDescriptionFile) {
      formData.append('job_description_file', data.jobDescriptionFile)
    }

    const response = await this.client.post('/api/research', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000, // Extended timeout for file uploads
    })

    return response.data
  }

  // Get research status
  async getResearchStatus(researchId: string): Promise<ProcessingState> {
    const response = await this.client.get(`/api/research/${researchId}/status`)
    return response.data
  }

  // Get research results
  async getResearchResults(researchId: string): Promise<MatchEvaluationResults> {
    const response = await this.client.get(`/api/research/${researchId}/results`)
    return response.data
  }

  // Cancel research
  async cancelResearch(researchId: string): Promise<void> {
    await this.client.post(`/api/research/${researchId}/cancel`)
  }
}
```

### File Upload Endpoints

```typescript
interface FileUploadResponse {
  fileId: string
  filename: string
  size: number
  contentType: string
  url: string
}

class FileApi {
  constructor(private client: ApiClient) {}

  // Upload CV file separately (if needed)
  async uploadCV(file: File): Promise<FileUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await this.client.post('/api/upload/cv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / (progressEvent.total || 1)
        )
        // Emit upload progress event
        this.onUploadProgress?.(percentCompleted)
      }
    })

    return response.data
  }

  // Upload job description file
  async uploadJobDescription(file: File): Promise<FileUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await this.client.post('/api/upload/job-description', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    return response.data
  }

  onUploadProgress?: (progress: number) => void
}
```

## Real-time Communication

### WebSocket Integration

```typescript
interface WebSocketManager {
  connect(researchId: string): void
  disconnect(): void
  onMessage(callback: (message: WebSocketMessage) => void): void
  onError(callback: (error: Event) => void): void
  onClose(callback: (event: CloseEvent) => void): void
}

class ResearchWebSocket implements WebSocketManager {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 1000

  connect(researchId: string): void {
    const wsUrl = `${WS_BASE_URL}/ws/research/${researchId}`

    try {
      this.ws = new WebSocket(wsUrl)
      this.setupEventHandlers()
    } catch (error) {
      console.error('WebSocket connection failed:', error)
      this.fallbackToPolling(researchId)
    }
  }

  private setupEventHandlers(): void {
    if (!this.ws) return

    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
    }

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        this.messageCallback?.(message)
      } catch (error) {
        console.error('Invalid WebSocket message:', error)
      }
    }

    this.ws.onclose = (event) => {
      if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
        setTimeout(() => {
          this.reconnectAttempts++
          this.connect(this.currentResearchId)
        }, this.reconnectInterval * Math.pow(2, this.reconnectAttempts))
      }
      this.closeCallback?.(event)
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      this.errorCallback?.(error)
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  onMessage(callback: (message: WebSocketMessage) => void): void {
    this.messageCallback = callback
  }

  onError(callback: (error: Event) => void): void {
    this.errorCallback = callback
  }

  onClose(callback: (event: CloseEvent) => void): void {
    this.closeCallback = callback
  }

  private messageCallback?: (message: WebSocketMessage) => void
  private errorCallback?: (error: Event) => void
  private closeCallback?: (event: CloseEvent) => void
  private currentResearchId: string = ''

  private fallbackToPolling(researchId: string): void {
    // Implement polling fallback
    console.log('Falling back to polling for research updates')
  }
}
```

## Error Handling

### Error Types and Handling

```typescript
interface ApiError {
  type: 'network' | 'client' | 'server' | 'timeout' | 'validation'
  status: number
  message: string
  details?: any
}

class ErrorHandler {
  static handle(error: ApiError): string {
    switch (error.type) {
      case 'network':
        return 'Network connection failed. Please check your internet connection.'
      case 'timeout':
        return 'Request timed out. Please try again.'
      case 'validation':
        return error.message || 'Invalid data provided.'
      case 'server':
        return 'Server error. Please try again later.'
      default:
        return 'An unexpected error occurred. Please try again.'
    }
  }

  static isRetryable(error: ApiError): boolean {
    return ['network', 'timeout', 'server'].includes(error.type) &&
           error.status !== 429 // Rate limited
  }
}
```

### Retry Logic

```typescript
class RetryableRequest {
  static async execute<T>(
    request: () => Promise<T>,
    maxAttempts = 3,
    delay = 1000
  ): Promise<T> {
    let lastError: ApiError

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await request()
      } catch (error) {
        lastError = error as ApiError

        if (!ErrorHandler.isRetryable(lastError) || attempt === maxAttempts) {
          throw lastError
        }

        await this.delay(delay * Math.pow(2, attempt - 1))
      }
    }

    throw lastError!
  }

  private static delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
}
```

## Request/Response Caching

### Cache Implementation

```typescript
interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number
}

class ApiCache {
  private cache = new Map<string, CacheEntry<any>>()

  set<T>(key: string, data: T, ttl = 300000): void { // 5 min default TTL
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    })
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key)

    if (!entry) return null

    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key)
      return null
    }

    return entry.data
  }

  clear(): void {
    this.cache.clear()
  }

  has(key: string): boolean {
    return this.get(key) !== null
  }
}
```

### Cached API Wrapper

```typescript
class CachedApiClient {
  constructor(
    private apiClient: ApiClient,
    private cache: ApiCache
  ) {}

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const cacheKey = `GET:${url}:${JSON.stringify(config?.params || {})}`

    // Try cache first
    const cached = this.cache.get<T>(cacheKey)
    if (cached) return cached

    // Make request and cache result
    const response = await this.apiClient.get<T>(url, config)
    this.cache.set(cacheKey, response.data)

    return response.data
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    // Clear related cache entries on mutations
    this.cache.clear()
    return this.apiClient.post<T>(url, data, config)
  }
}
```

## React Hooks for API Integration

### Research Hook

```typescript
const useResearch = () => {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)

  const submitResearch = useCallback(async (data: ResearchRequest) => {
    setIsLoading(true)
    setError(null)

    try {
      const result = await RetryableRequest.execute(
        () => researchApi.submitResearch(data)
      )
      return result
    } catch (err) {
      const apiError = err as ApiError
      setError(apiError)
      throw apiError
    } finally {
      setIsLoading(false)
    }
  }, [])

  const cancelResearch = useCallback(async (researchId: string) => {
    try {
      await researchApi.cancelResearch(researchId)
    } catch (err) {
      console.error('Failed to cancel research:', err)
    }
  }, [])

  return {
    submitResearch,
    cancelResearch,
    isLoading,
    error
  }
}
```

### File Upload Hook

```typescript
const useFileUpload = () => {
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)

  const uploadFile = useCallback(async (file: File, type: 'cv' | 'job-description') => {
    setIsUploading(true)
    setUploadProgress(0)

    try {
      fileApi.onUploadProgress = setUploadProgress

      const result = type === 'cv'
        ? await fileApi.uploadCV(file)
        : await fileApi.uploadJobDescription(file)

      return result
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
      fileApi.onUploadProgress = undefined
    }
  }, [])

  return {
    uploadFile,
    uploadProgress,
    isUploading
  }
}
```

### Real-time Updates Hook

```typescript
const useResearchUpdates = (researchId: string) => {
  const [processingState, setProcessingState] = useState<ProcessingState | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!researchId) return

    const wsManager = new ResearchWebSocket()

    wsManager.onMessage((message) => {
      switch (message.type) {
        case 'stage_update':
        case 'progress_update':
          setProcessingState(prev => ({
            ...prev,
            ...message.data
          }))
          break
        case 'completion':
          setProcessingState(prev => ({
            ...prev,
            status: 'completed',
            results: message.data.results
          }))
          break
        case 'error':
          setError(message.data.error || 'Unknown error occurred')
          break
      }
    })

    wsManager.onError((error) => {
      console.error('WebSocket error:', error)
      setError('Connection error. Falling back to polling.')
    })

    wsManager.connect(researchId)

    return () => {
      wsManager.disconnect()
    }
  }, [researchId])

  return { processingState, error }
}
```

## API Service Factory

```typescript
// src/services/index.ts
class ApiServiceFactory {
  private static instance: ApiServiceFactory
  private apiClient: ApiClient
  private cache: ApiCache

  private constructor() {
    this.apiClient = new ApiClient()
    this.cache = new ApiCache()
  }

  static getInstance(): ApiServiceFactory {
    if (!ApiServiceFactory.instance) {
      ApiServiceFactory.instance = new ApiServiceFactory()
    }
    return ApiServiceFactory.instance
  }

  getResearchApi(): ResearchApi {
    return new ResearchApi(this.apiClient)
  }

  getFileApi(): FileApi {
    return new FileApi(this.apiClient)
  }

  getCachedApiClient(): CachedApiClient {
    return new CachedApiClient(this.apiClient, this.cache)
  }
}

// Export singleton instances
export const apiFactory = ApiServiceFactory.getInstance()
export const researchApi = apiFactory.getResearchApi()
export const fileApi = apiFactory.getFileApi()
export const cachedApi = apiFactory.getCachedApiClient()
```

This specification provides a robust, type-safe, and feature-rich API integration layer that handles file uploads, real-time updates, error handling, caching, and provides convenient React hooks for UI integration.