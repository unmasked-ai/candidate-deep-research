export interface ProcessingStage {
  id: string
  name: string
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'error'
  progress?: number
  estimatedDuration?: number
  startTime?: Date
  endTime?: Date
}

export interface AgentStatus {
  id: string
  name: string
  status: 'idle' | 'active' | 'completed' | 'error'
  currentTask?: string
  progress?: number
  lastUpdate?: Date
}

export interface ResearchError {
  type: 'network' | 'agent_failure' | 'timeout' | 'validation' | 'unknown'
  stage?: string
  message: string
  retryable: boolean
  details?: Record<string, any>
}

export interface ProcessingState {
  researchId: string
  stages: ProcessingStage[]
  currentStage: string
  overallProgress: number
  estimatedTimeRemaining?: number
  error?: ResearchError
  isMinimized: boolean
}

export interface StatusMessage {
  id: string
  stage: string
  message: string
  timestamp: Date
  type: 'info' | 'success' | 'warning' | 'error'
}

export const defaultStages: ProcessingStage[] = [
  {
    id: 'interface',
    name: 'Interface Agent',
    description: 'Orchestrating research process',
    status: 'pending',
    estimatedDuration: 30
  },
  {
    id: 'linkedin',
    name: 'LinkedIn Agent',
    description: 'Analyzing LinkedIn profile',
    status: 'pending',
    estimatedDuration: 60
  },
  {
    id: 'company-research',
    name: 'Company Research',
    description: 'Researching target company',
    status: 'pending',
    estimatedDuration: 90
  },
  {
    id: 'person-research',
    name: 'Person Research',
    description: 'Additional candidate research',
    status: 'pending',
    estimatedDuration: 120
  },
  {
    id: 'role-requirements',
    name: 'Role Analysis',
    description: 'Analyzing job requirements',
    status: 'pending',
    estimatedDuration: 45
  },
  {
    id: 'match-evaluation',
    name: 'Match Evaluation',
    description: 'Calculating match score',
    status: 'pending',
    estimatedDuration: 30
  }
]