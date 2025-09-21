export interface AppError extends Error {
  type: 'validation' | 'network' | 'api' | 'file' | 'unknown'
  code?: string
  details?: any
  retryable?: boolean
}

export class ValidationError extends Error implements AppError {
  type = 'validation' as const
  retryable = false

  constructor(message: string, public field?: string) {
    super(message)
    this.name = 'ValidationError'
  }
}

export class NetworkError extends Error implements AppError {
  type = 'network' as const
  retryable = true

  constructor(message: string, public code?: string) {
    super(message)
    this.name = 'NetworkError'
  }
}

export class AppApiError extends Error implements AppError {
  type = 'api' as const

  constructor(
    message: string,
    public status: number,
    public retryable: boolean = false,
    public details?: any
  ) {
    super(message)
    this.name = 'AppApiError'
  }
}

export class FileError extends Error implements AppError {
  type = 'file' as const
  retryable = false

  constructor(message: string, public fileType?: string, public maxSize?: number) {
    super(message)
    this.name = 'FileError'
  }
}

// Error transformation utilities
export const transformApiError = (error: any): AppError => {
  // Network errors
  if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
    return new NetworkError('Request timeout. Please check your connection and try again.', error.code)
  }

  if (error.code === 'ERR_NETWORK' || !error.response) {
    return new NetworkError('Network error. Please check your connection.', error.code)
  }

  // API errors
  if (error.response) {
    const status = error.response.status
    const data = error.response.data
    const message = data?.detail || data?.message || error.message || 'An error occurred'
    const retryable = status >= 500 || status === 429

    return new AppApiError(message, status, retryable, data)
  }

  // Validation errors
  if (error.name === 'ValidationError') {
    return error
  }

  // Unknown errors
  return {
    name: 'UnknownError',
    message: error.message || 'An unknown error occurred',
    type: 'unknown' as const,
    retryable: false
  } as AppError
}

// File validation utilities
export const validateFileSize = (file: File, maxSizeBytes: number): void => {
  if (file.size > maxSizeBytes) {
    const maxSizeMB = Math.round(maxSizeBytes / (1024 * 1024))
    throw new FileError(
      `File size must be less than ${maxSizeMB}MB`,
      file.type,
      maxSizeBytes
    )
  }
}

export const validateFileType = (file: File, allowedTypes: string[]): void => {
  const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
  const mimeType = file.type.toLowerCase()

  const isValidExtension = allowedTypes.some(type =>
    type.toLowerCase() === fileExtension
  )

  const isValidMimeType = allowedTypes.some(type => {
    if (type === '.pdf') return mimeType === 'application/pdf'
    if (type === '.doc') return mimeType === 'application/msword'
    if (type === '.docx') return mimeType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    if (type === '.txt') return mimeType === 'text/plain'
    return false
  })

  if (!isValidExtension && !isValidMimeType) {
    throw new FileError(
      `File type not supported. Allowed types: ${allowedTypes.join(', ')}`,
      file.type
    )
  }
}

export const validateFile = (
  file: File,
  maxSizeBytes: number,
  allowedTypes: string[]
): void => {
  validateFileSize(file, maxSizeBytes)
  validateFileType(file, allowedTypes)
}

// LinkedIn URL validation
export const validateLinkedInUrl = (url: string): void => {
  if (!url) {
    throw new ValidationError('LinkedIn URL is required')
  }

  try {
    const urlObj = new URL(url)

    if (!urlObj.hostname.includes('linkedin.com')) {
      throw new ValidationError('Must be a LinkedIn profile URL')
    }

    if (!url.includes('/in/')) {
      throw new ValidationError('Must be a valid LinkedIn profile URL (should contain /in/)')
    }
  } catch (error) {
    if (error instanceof ValidationError) {
      throw error
    }
    throw new ValidationError('Must be a valid URL format')
  }
}

// Error message formatting
export const getErrorMessage = (error: any): string => {
  if (error instanceof Error) {
    return error.message
  }

  if (typeof error === 'string') {
    return error
  }

  if (error?.message) {
    return error.message
  }

  return 'An unknown error occurred'
}

export const getErrorType = (error: any): AppError['type'] => {
  if (error?.type) {
    return error.type
  }

  if (error instanceof ValidationError) return 'validation'
  if (error instanceof NetworkError) return 'network'
  if (error instanceof ApiError) return 'api'
  if (error instanceof FileError) return 'file'

  return 'unknown'
}

// User-friendly error messages
export const getUserFriendlyErrorMessage = (error: any): string => {
  const appError = transformApiError(error)

  switch (appError.type) {
    case 'validation':
      return appError.message

    case 'network':
      if (appError.message.includes('timeout')) {
        return 'Request timed out. Please check your internet connection and try again.'
      }
      return 'Unable to connect to the server. Please check your internet connection.'

    case 'api':
      if ((appError as AppApiError).status === 413) {
        return 'File is too large. Please choose a smaller file.'
      }
      if ((appError as AppApiError).status === 429) {
        return 'Too many requests. Please wait a moment and try again.'
      }
      if ((appError as AppApiError).status >= 500) {
        return 'Server error. Please try again later.'
      }
      return appError.message

    case 'file':
      return appError.message

    default:
      return 'An unexpected error occurred. Please try again.'
  }
}

// Retry logic
export const shouldRetry = (error: any, retryCount: number, maxRetries: number = 3): boolean => {
  if (retryCount >= maxRetries) return false

  const appError = transformApiError(error)
  return appError.retryable || false
}

export const getRetryDelay = (retryCount: number): number => {
  // Exponential backoff: 1s, 2s, 4s, 8s...
  return Math.min(1000 * Math.pow(2, retryCount), 10000)
}

// Error reporting (for production)
export const reportError = (error: any, context?: Record<string, any>): void => {
  if (process.env.NODE_ENV === 'development') {
    console.error('Error reported:', error, context)
    return
  }

  // In production, send to error reporting service
  // Example: Sentry, LogRocket, etc.
  try {
    // errorReportingService.captureException(error, { extra: context })
  } catch (reportingError) {
    console.error('Failed to report error:', reportingError)
  }
}