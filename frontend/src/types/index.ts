// API Response Types
export interface ResearchResponse {
  research_id: string
  status: string
  message: string
}

export interface ResearchStatus {
  research_id: string
  status: 'initiated' | 'processing' | 'completed' | 'failed'
  message?: string
  result?: string
  error?: string
}

export interface FileUploadResponse {
  filename: string
  size: number
  content_type: string
  content: string
}

// Form Types
export interface ResearchFormData {
  linkedinUrl: string
  cvFile: File | null
  jobDescription: string
  jobDescriptionFile: File | null
  useJobDescriptionFile: boolean
}

// Match Evaluation Types
export interface MatchEvaluationResults {
  overall_score: number
  sub_scores: {
    skills: number
    experience: number
    culture: number
    domain: number
    logistics: number
  }
  decision: 'proceed' | 'maybe' | 'reject'
  justification: string
  reasons: string[]
  missing_data: string[]
  evidence: Evidence[]
}

export interface Evidence {
  source: 'candidate' | 'job' | 'company'
  quote: string
  field: string
}

// Error Types
export interface ApiError {
  type: 'network' | 'client' | 'server' | 'timeout' | 'validation'
  status: number
  message: string
  details?: any
}