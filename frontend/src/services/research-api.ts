import { apiClient } from './api-client'
import type { ResearchFormData, ResearchResponse, ResearchStatus, MatchEvaluationResults } from '@/types'
import type { ProcessingState } from '@/components/processing'

export interface ResearchRequest {
  linkedinUrl: string
  cvFile: File
  jobDescription?: string
  jobDescriptionFile?: File
}

export interface ResearchStatusResponse {
  research_id: string
  status: 'initiated' | 'processing' | 'completed' | 'failed'
  message?: string
  current_stage?: string
  overall_progress?: number
  estimated_time_remaining?: number
  stages?: any[]
  error?: string
}

export class ResearchApi {
  // Submit research request with file uploads
  async submitResearch(
    data: ResearchFormData,
    onProgress?: (progress: number) => void
  ): Promise<ResearchResponse> {
    const formData = new FormData()

    // Add form fields
    formData.append('linkedin_url', data.linkedinUrl)
    formData.append('cv_file', data.cvFile!)

    // Handle job description - either text or file
    if (data.useJobDescriptionFile && data.jobDescriptionFile) {
      formData.append('job_description_file', data.jobDescriptionFile)
    } else if (data.jobDescription) {
      formData.append('job_description', data.jobDescription)
    }

    const response = await apiClient.post<ResearchResponse>('/api/research', formData, {
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

    return response
  }

  // Get research status
  async getResearchStatus(researchId: string): Promise<ResearchStatusResponse> {
    return apiClient.get<ResearchStatusResponse>(`/api/research/${researchId}/status`)
  }

  // Get research results
  async getResearchResults(researchId: string): Promise<MatchEvaluationResults> {
    return apiClient.get<MatchEvaluationResults>(`/api/research/${researchId}/results`)
  }

  // Cancel research
  async cancelResearch(researchId: string): Promise<void> {
    await apiClient.post(`/api/research/${researchId}/cancel`)
  }

  // List user's research history (if implemented)
  async getResearchHistory(limit = 10, offset = 0): Promise<{
    items: ResearchStatus[]
    total: number
    has_more: boolean
  }> {
    return apiClient.get('/api/research/history', {
      params: { limit, offset }
    })
  }

  // Delete research data (if implemented)
  async deleteResearch(researchId: string): Promise<void> {
    await apiClient.delete(`/api/research/${researchId}`)
  }

  // Export research results (if implemented)
  async exportResults(
    researchId: string,
    format: 'pdf' | 'json' | 'csv'
  ): Promise<Blob> {
    const response = await apiClient.get(`/api/research/${researchId}/export`, {
      params: { format },
      responseType: 'blob'
    })
    return response
  }

  // Transform API response to ProcessingState for UI components
  transformToProcessingState(
    researchId: string,
    apiResponse: ResearchStatusResponse
  ): ProcessingState {
    return {
      researchId,
      stages: apiResponse.stages || [],
      currentStage: apiResponse.current_stage || '',
      overallProgress: apiResponse.overall_progress || 0,
      estimatedTimeRemaining: apiResponse.estimated_time_remaining,
      error: apiResponse.error ? {
        type: 'unknown',
        message: apiResponse.error,
        retryable: true
      } : undefined,
      isMinimized: false
    }
  }
}

// Create default instance
export const researchApi = new ResearchApi()