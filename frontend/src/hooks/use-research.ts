import { useCallback, useEffect } from 'react'
import { useResearchStore } from '@/stores/research-store'
import { researchApi, createWebSocket, type WebSocketMessage } from '@/services'
import type { ResearchFormData, MatchEvaluationResults, CandidateProfile } from '@/types'
import { defaultStages } from '@/components/processing'
import { transformApiError, getUserFriendlyErrorMessage, shouldRetry, getRetryDelay } from '@/utils/error-handling'

export const useResearch = () => {
  const {
    currentSession,
    isSubmitting,
    uploadProgress,
    statusMessages,
    isProcessingMinimized,
    activeTab,
    startResearch,
    updateProcessingState,
    addStatusMessage,
    completeResearch,
    failResearch,
    cancelResearch,
    setSubmitting,
    setUploadProgress,
    setProcessingMinimized,
    setActiveTab,
    clearCurrentSession
  } = useResearchStore()

  // Submit research request with retry logic
  const submitResearch = useCallback(async (formData: ResearchFormData, retryCount = 0) => {
    const maxRetries = 3

    try {
      setSubmitting(true)
      setUploadProgress(0)

      const response = await researchApi.submitResearch(formData, (progress) => {
        setUploadProgress(progress)
      })

      startResearch(formData, response)

      addStatusMessage({
        stage: 'System',
        message: 'Research request submitted successfully',
        timestamp: new Date(),
        type: 'success'
      })

      return response
    } catch (error: any) {
      const transformedError = transformApiError(error)
      const userMessage = getUserFriendlyErrorMessage(error)

      // Attempt retry for retryable errors
      if (shouldRetry(error, retryCount, maxRetries)) {
        const delay = getRetryDelay(retryCount)

        addStatusMessage({
          stage: 'System',
          message: `Request failed, retrying in ${delay / 1000} seconds... (${retryCount + 1}/${maxRetries})`,
          timestamp: new Date(),
          type: 'warning'
        })

        await new Promise(resolve => setTimeout(resolve, delay))
        return submitResearch(formData, retryCount + 1)
      }

      setSubmitting(false)

      addStatusMessage({
        stage: 'System',
        message: userMessage,
        timestamp: new Date(),
        type: 'error'
      })

      throw transformedError
    }
  }, [startResearch, setSubmitting, setUploadProgress, addStatusMessage])

  // Cancel current research
  const handleCancelResearch = useCallback(async () => {
    if (!currentSession?.id) return

    try {
      await researchApi.cancelResearch(currentSession.id)
      cancelResearch()

      addStatusMessage({
        stage: 'System',
        message: 'Research cancelled',
        timestamp: new Date(),
        type: 'info'
      })
    } catch (error: any) {
      addStatusMessage({
        stage: 'System',
        message: error.message || 'Failed to cancel research',
        timestamp: new Date(),
        type: 'error'
      })
    }
  }, [currentSession?.id, cancelResearch, addStatusMessage])

  // Get research results
  const fetchResults = useCallback(async (researchId: string) => {
    try {
      const results = await researchApi.getResearchResults(researchId)

      // Mock candidate profile for now - in real implementation this would come from API
      const candidateProfile: CandidateProfile = {
        name: 'Loading...',
        years_experience: 0,
        skills: []
      }

      completeResearch(results, candidateProfile)
      return results
    } catch (error: any) {
      failResearch({
        type: 'client',
        status: error.status || 500,
        message: error.message || 'Failed to fetch results'
      })
      throw error
    }
  }, [completeResearch, failResearch])

  // Export results
  const exportResults = useCallback(async (format: 'pdf' | 'json' | 'csv') => {
    if (!currentSession?.id) return

    try {
      const blob = await researchApi.exportResults(currentSession.id, format)

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `research-results-${currentSession.id}.${format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      addStatusMessage({
        stage: 'System',
        message: `Results exported as ${format.toUpperCase()}`,
        timestamp: new Date(),
        type: 'success'
      })
    } catch (error: any) {
      addStatusMessage({
        stage: 'System',
        message: error.message || 'Failed to export results',
        timestamp: new Date(),
        type: 'error'
      })
    }
  }, [currentSession?.id, addStatusMessage])

  return {
    // State
    currentSession,
    isSubmitting,
    uploadProgress,
    statusMessages,
    isProcessingMinimized,
    activeTab,

    // Actions
    submitResearch,
    cancelResearch: handleCancelResearch,
    fetchResults,
    exportResults,
    setProcessingMinimized,
    setActiveTab,
    clearCurrentSession
  }
}

// Hook for real-time processing updates
export const useProcessingUpdates = (researchId?: string) => {
  const {
    updateProcessingState,
    addStatusMessage,
    completeResearch,
    failResearch,
    currentSession
  } = useResearchStore()

  useEffect(() => {
    if (!researchId) return

    const ws = createWebSocket()

    // Handle WebSocket messages
    ws.onMessage((message: WebSocketMessage) => {
      switch (message.type) {
        case 'stage_update':
          if (message.data.stage) {
            updateProcessingState({
              currentStage: message.data.stage,
              stages: defaultStages.map(stage => ({
                ...stage,
                status: stage.id === message.data.stage ? 'in_progress' :
                       defaultStages.findIndex(s => s.id === message.data.stage) >
                       defaultStages.findIndex(s => s.id === stage.id) ? 'pending' : 'completed'
              }))
            })

            addStatusMessage({
              stage: message.data.stage,
              message: message.data.message || `${message.data.stage} started`,
              timestamp: new Date(),
              type: 'info'
            })
          }
          break

        case 'progress_update':
          if (message.data.progress !== undefined) {
            updateProcessingState({
              overallProgress: message.data.progress
            })
          }
          break

        case 'completion':
          updateProcessingState({
            overallProgress: 100
          })

          addStatusMessage({
            stage: 'System',
            message: 'Research completed successfully',
            timestamp: new Date(),
            type: 'success'
          })

          // Fetch results
          if (message.data.results) {
            const candidateProfile: CandidateProfile = {
              name: 'Candidate Name',
              years_experience: 5,
              skills: []
            }
            completeResearch(message.data.results, candidateProfile)
          }
          break

        case 'error':
          failResearch({
            type: message.data.errorType as any || 'unknown',
            status: 500,
            message: message.data.message || 'An error occurred during processing',
            details: message.data.details
          })

          addStatusMessage({
            stage: message.data.stage || 'System',
            message: message.data.message || 'Processing error occurred',
            timestamp: new Date(),
            type: 'error'
          })
          break

        case 'agent_status':
          if (message.data.agent && message.data.currentTask) {
            addStatusMessage({
              stage: message.data.agent,
              message: message.data.currentTask,
              timestamp: new Date(),
              type: 'info'
            })
          }
          break
      }
    })

    ws.onError((error) => {
      console.error('WebSocket error:', error)
      addStatusMessage({
        stage: 'System',
        message: 'Connection error - falling back to polling',
        timestamp: new Date(),
        type: 'warning'
      })
    })

    ws.onClose((event) => {
      if (!event.wasClean) {
        addStatusMessage({
          stage: 'System',
          message: 'Connection lost - attempting to reconnect',
          timestamp: new Date(),
          type: 'warning'
        })
      }
    })

    // Connect to WebSocket
    ws.connect(researchId)

    // Cleanup on unmount
    return () => {
      ws.disconnect()
    }
  }, [researchId, updateProcessingState, addStatusMessage, completeResearch, failResearch])

  // Fallback polling when WebSocket is not available
  useEffect(() => {
    if (!researchId || !currentSession || currentSession.status === 'completed') return

    const pollInterval = setInterval(async () => {
      try {
        const status = await researchApi.getResearchStatus(researchId)
        const processingState = researchApi.transformToProcessingState(researchId, status)
        updateProcessingState(processingState)

        if (status.status === 'completed') {
          clearInterval(pollInterval)
          // Fetch results when completed
          await researchApi.getResearchResults(researchId)
        }
      } catch (error) {
        console.error('Polling error:', error)
      }
    }, 3000) // Poll every 3 seconds

    return () => clearInterval(pollInterval)
  }, [researchId, currentSession, updateProcessingState])
}