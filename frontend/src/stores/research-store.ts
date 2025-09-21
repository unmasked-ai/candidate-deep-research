import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import type { ResearchFormData, ResearchResponse, MatchEvaluationResults, CandidateProfile, ApiError } from '@/types'
import type { ProcessingState } from '@/components/processing'
import type { StatusMessage as StatusMessageType } from '@/components/processing/types'

export interface ResearchSession {
  id: string
  formData: ResearchFormData
  linkedinUrl: string
  submittedAt: Date
  status: 'submitted' | 'processing' | 'completed' | 'failed' | 'cancelled'
  processingState?: ProcessingState
  results?: MatchEvaluationResults
  candidateProfile?: CandidateProfile
  error?: ApiError
}

interface ResearchStore {
  // Current session state
  currentSession: ResearchSession | null
  isSubmitting: boolean
  uploadProgress: number
  statusMessages: StatusMessageType[]

  // Session history
  sessions: ResearchSession[]

  // UI state
  isProcessingMinimized: boolean
  activeTab: 'form' | 'processing' | 'results'

  // Actions
  startResearch: (formData: ResearchFormData, response: ResearchResponse) => void
  updateProcessingState: (state: Partial<ProcessingState>) => void
  addStatusMessage: (message: Omit<StatusMessageType, 'id'>) => void
  completeResearch: (results: MatchEvaluationResults, candidateProfile?: CandidateProfile) => void
  failResearch: (error: ApiError) => void
  cancelResearch: () => void
  setSubmitting: (isSubmitting: boolean) => void
  setUploadProgress: (progress: number) => void
  setProcessingMinimized: (minimized: boolean) => void
  setActiveTab: (tab: 'form' | 'processing' | 'results') => void
  clearCurrentSession: () => void
  loadSession: (sessionId: string) => void
  deleteSession: (sessionId: string) => void
  clearAllSessions: () => void
}

export const useResearchStore = create<ResearchStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        currentSession: null,
        isSubmitting: false,
        uploadProgress: 0,
        statusMessages: [],
        sessions: [],
        isProcessingMinimized: false,
        activeTab: 'form',

        // Actions
        startResearch: (formData, response) => {
          const session: ResearchSession = {
            id: response.research_id,
            formData,
            linkedinUrl: formData.linkedinUrl,
            submittedAt: new Date(),
            status: 'submitted',
            processingState: {
              researchId: response.research_id,
              stages: [],
              currentStage: '',
              overallProgress: 0,
              isMinimized: false
            }
          }

          set({
            currentSession: session,
            isSubmitting: false,
            uploadProgress: 0,
            statusMessages: [],
            activeTab: 'processing'
          })

          // Add to sessions history
          const { sessions } = get()
          const updatedSessions = [session, ...sessions.slice(0, 9)] // Keep last 10 sessions
          set({ sessions: updatedSessions })
        },

        updateProcessingState: (stateUpdate) => {
          const { currentSession } = get()
          if (!currentSession) return

          const updatedSession: ResearchSession = {
            ...currentSession,
            status: stateUpdate.error ? 'failed' :
                   stateUpdate.overallProgress === 100 ? 'completed' : 'processing',
            processingState: {
              ...currentSession.processingState!,
              ...stateUpdate
            }
          }

          set({ currentSession: updatedSession })

          // Update in sessions history
          const { sessions } = get()
          const updatedSessions = sessions.map(session =>
            session.id === currentSession.id ? updatedSession : session
          )
          set({ sessions: updatedSessions })
        },

        addStatusMessage: (messageData) => {
          const message: StatusMessageType = {
            ...messageData,
            id: `${Date.now()}-${Math.random()}`
          }

          set(state => ({
            statusMessages: [...state.statusMessages, message]
          }))
        },

        completeResearch: (results, candidateProfile) => {
          const { currentSession } = get()
          if (!currentSession) return

          const updatedSession: ResearchSession = {
            ...currentSession,
            status: 'completed',
            results,
            candidateProfile,
            processingState: {
              ...currentSession.processingState!,
              overallProgress: 100
            }
          }

          set({
            currentSession: updatedSession,
            activeTab: 'results'
          })

          // Update in sessions history
          const { sessions } = get()
          const updatedSessions = sessions.map(session =>
            session.id === currentSession.id ? updatedSession : session
          )
          set({ sessions: updatedSessions })
        },

        failResearch: (error) => {
          const { currentSession } = get()
          if (!currentSession) return

          const updatedSession: ResearchSession = {
            ...currentSession,
            status: 'failed',
            error,
            processingState: {
              ...currentSession.processingState!,
              error: {
                type: error.type,
                message: error.message,
                retryable: error.status < 500
              }
            }
          }

          set({ currentSession: updatedSession })

          // Update in sessions history
          const { sessions } = get()
          const updatedSessions = sessions.map(session =>
            session.id === currentSession.id ? updatedSession : session
          )
          set({ sessions: updatedSessions })
        },

        cancelResearch: () => {
          const { currentSession } = get()
          if (!currentSession) return

          const updatedSession: ResearchSession = {
            ...currentSession,
            status: 'cancelled'
          }

          set({
            currentSession: updatedSession,
            activeTab: 'form'
          })

          // Update in sessions history
          const { sessions } = get()
          const updatedSessions = sessions.map(session =>
            session.id === currentSession.id ? updatedSession : session
          )
          set({ sessions: updatedSessions })
        },

        setSubmitting: (isSubmitting) => set({ isSubmitting }),

        setUploadProgress: (progress) => set({ uploadProgress: progress }),

        setProcessingMinimized: (minimized) => {
          set({ isProcessingMinimized: minimized })

          // Also update current session's processing state
          const { currentSession } = get()
          if (currentSession?.processingState) {
            set({
              currentSession: {
                ...currentSession,
                processingState: {
                  ...currentSession.processingState,
                  isMinimized: minimized
                }
              }
            })
          }
        },

        setActiveTab: (tab) => set({ activeTab: tab }),

        clearCurrentSession: () => set({
          currentSession: null,
          statusMessages: [],
          uploadProgress: 0,
          isSubmitting: false,
          isProcessingMinimized: false,
          activeTab: 'form'
        }),

        loadSession: (sessionId) => {
          const { sessions } = get()
          const session = sessions.find(s => s.id === sessionId)
          if (session) {
            set({
              currentSession: session,
              statusMessages: [], // Fresh status messages for loaded session
              activeTab: session.status === 'completed' ? 'results' :
                        session.status === 'processing' ? 'processing' : 'form'
            })
          }
        },

        deleteSession: (sessionId) => {
          const { sessions, currentSession } = get()
          const updatedSessions = sessions.filter(s => s.id !== sessionId)
          set({ sessions: updatedSessions })

          // Clear current session if it's the one being deleted
          if (currentSession?.id === sessionId) {
            get().clearCurrentSession()
          }
        },

        clearAllSessions: () => set({
          sessions: [],
          currentSession: null,
          statusMessages: [],
          uploadProgress: 0,
          isSubmitting: false,
          isProcessingMinimized: false,
          activeTab: 'form'
        })
      }),
      {
        name: 'research-store',
        version: 2,
        // Remove currentSession from persistence to avoid auto-resuming/polling
        partialize: (state) => ({
          sessions: state.sessions,
        }),
        migrate: (persistedState: any, version) => {
          // Clear any previously persisted currentSession
          try {
            const s = persistedState?.state ?? persistedState
            if (s && 'currentSession' in s) {
              s.currentSession = null
            }
            return persistedState
          } catch {
            return persistedState
          }
        }
      }
    ),
    {
      name: 'research-store'
    }
  )
)
