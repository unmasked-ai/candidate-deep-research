import { useState, useEffect, useCallback, useRef } from 'react'
import type { ProcessingState, StatusMessage, ResearchError, ProcessingStage } from './types'
import { defaultStages } from './types'

interface UseProcessingOptions {
  pollingInterval?: number
  enableWebSocket?: boolean
}

export const useProcessing = (
  researchId: string,
  options: UseProcessingOptions = {}
) => {
  const { pollingInterval = 2000, enableWebSocket = false } = options

  const [processingState, setProcessingState] = useState<ProcessingState>({
    researchId,
    stages: defaultStages,
    currentStage: '',
    overallProgress: 0,
    isMinimized: false
  })

  const [statusMessages, setStatusMessages] = useState<StatusMessage[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<ResearchError | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Add status message
  const addStatusMessage = useCallback((message: Omit<StatusMessage, 'id'>) => {
    const newMessage: StatusMessage = {
      ...message,
      id: `${Date.now()}-${Math.random()}`
    }
    setStatusMessages(prev => [...prev, newMessage])
  }, [])

  // Update processing stage
  const updateStage = useCallback((stageId: string, updates: Partial<ProcessingStage>) => {
    setProcessingState(prev => ({
      ...prev,
      stages: prev.stages.map(stage =>
        stage.id === stageId ? { ...stage, ...updates } : stage
      ),
      currentStage: updates.status === 'in_progress' ? stageId : prev.currentStage
    }))
  }, [])

  // Calculate overall progress
  const calculateOverallProgress = useCallback((stages: ProcessingStage[]) => {
    const totalStages = stages.length
    const completedStages = stages.filter(stage => stage.status === 'completed').length
    const inProgressStages = stages.filter(stage => stage.status === 'in_progress')

    let progress = (completedStages / totalStages) * 100

    // Add partial progress for in-progress stages
    if (inProgressStages.length > 0) {
      const inProgressContribution = inProgressStages.reduce((sum, stage) => {
        return sum + (stage.progress || 0)
      }, 0) / inProgressStages.length

      progress += (inProgressContribution / totalStages)
    }

    return Math.min(progress, 100)
  }, [])

  // Estimate time remaining
  const estimateTimeRemaining = useCallback((stages: ProcessingStage[]) => {
    const pendingStages = stages.filter(stage => stage.status === 'pending')
    const inProgressStages = stages.filter(stage => stage.status === 'in_progress')

    let totalEstimate = 0

    // Add time for pending stages
    totalEstimate += pendingStages.reduce((sum, stage) => {
      return sum + (stage.estimatedDuration || 60)
    }, 0)

    // Add remaining time for in-progress stages
    inProgressStages.forEach(stage => {
      const remaining = ((100 - (stage.progress || 0)) / 100) * (stage.estimatedDuration || 60)
      totalEstimate += remaining
    })

    return Math.max(totalEstimate, 0)
  }, [])

  // Mock API call for polling
  const fetchResearchStatus = useCallback(async () => {
    try {
      // TODO: Replace with actual API call
      const response = await fetch(`/api/research/${researchId}/status`)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Error fetching research status:', error)
      throw error
    }
  }, [researchId])

  // Handle WebSocket message
  const handleWebSocketMessage = useCallback((event: MessageEvent) => {
    try {
      const message = JSON.parse(event.data)

      switch (message.type) {
        case 'stage_update':
          updateStage(message.data.stage, {
            status: message.data.status,
            progress: message.data.progress
          })

          addStatusMessage({
            stage: message.data.stage,
            message: message.data.message || `Stage ${message.data.status}`,
            timestamp: new Date(),
            type: message.data.status === 'error' ? 'error' : 'info'
          })
          break

        case 'progress_update':
          setProcessingState(prev => ({
            ...prev,
            overallProgress: message.data.progress
          }))
          break

        case 'completion':
          setProcessingState(prev => ({
            ...prev,
            overallProgress: 100
          }))

          addStatusMessage({
            stage: 'System',
            message: 'Research completed successfully',
            timestamp: new Date(),
            type: 'success'
          })
          break

        case 'error':
          const researchError: ResearchError = {
            type: message.data.errorType || 'unknown',
            stage: message.data.stage,
            message: message.data.message,
            retryable: message.data.retryable || false,
            details: message.data.details
          }

          setError(researchError)
          setProcessingState(prev => ({ ...prev, error: researchError }))

          addStatusMessage({
            stage: message.data.stage || 'System',
            message: message.data.message,
            timestamp: new Date(),
            type: 'error'
          })
          break
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error)
    }
  }, [updateStage, addStatusMessage])

  // Initialize WebSocket connection
  const initializeWebSocket = useCallback(() => {
    if (!enableWebSocket) return

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/ws/research/${researchId}`

      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = () => {
        setIsConnected(true)
        addStatusMessage({
          stage: 'System',
          message: 'Connected to real-time updates',
          timestamp: new Date(),
          type: 'info'
        })
      }

      wsRef.current.onmessage = handleWebSocketMessage

      wsRef.current.onclose = () => {
        setIsConnected(false)
        // Fallback to polling
        if (pollIntervalRef.current === null) {
          startPolling()
        }
      }

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        setIsConnected(false)
        // Fallback to polling
        if (pollIntervalRef.current === null) {
          startPolling()
        }
      }
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error)
      startPolling()
    }
  }, [researchId, enableWebSocket, handleWebSocketMessage, addStatusMessage])

  // Start polling
  const startPolling = useCallback(() => {
    if (pollIntervalRef.current) return

    pollIntervalRef.current = setInterval(async () => {
      try {
        const data = await fetchResearchStatus()

        // Update processing state based on API response
        setProcessingState(prev => ({
          ...prev,
          stages: data.stages || prev.stages,
          currentStage: data.currentStage || prev.currentStage,
          overallProgress: data.overallProgress || calculateOverallProgress(data.stages || prev.stages),
          estimatedTimeRemaining: estimateTimeRemaining(data.stages || prev.stages)
        }))

        if (data.status === 'completed') {
          stopPolling()
        }
      } catch (error) {
        console.error('Polling error:', error)
        // Continue polling on error
      }
    }, pollingInterval)
  }, [fetchResearchStatus, pollingInterval, calculateOverallProgress, estimateTimeRemaining])

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
  }, [])

  // Cleanup function
  const cleanup = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    stopPolling()
  }, [stopPolling])

  // Initialize connection on mount
  useEffect(() => {
    if (enableWebSocket) {
      initializeWebSocket()
    } else {
      startPolling()
    }

    return cleanup
  }, [initializeWebSocket, startPolling, cleanup, enableWebSocket])

  // Update derived values when stages change
  useEffect(() => {
    setProcessingState(prev => ({
      ...prev,
      overallProgress: calculateOverallProgress(prev.stages),
      estimatedTimeRemaining: estimateTimeRemaining(prev.stages)
    }))
  }, [processingState.stages, calculateOverallProgress, estimateTimeRemaining])

  return {
    processingState,
    statusMessages,
    isConnected,
    error,
    addStatusMessage,
    updateStage,
    cleanup
  }
}

// Debounced progress hook to prevent UI thrashing
export const useDebouncedProgress = (progress: number, delay = 100) => {
  const [debouncedProgress, setDebouncedProgress] = useState(progress)

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedProgress(progress)
    }, delay)

    return () => clearTimeout(timer)
  }, [progress, delay])

  return debouncedProgress
}