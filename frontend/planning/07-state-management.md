# State Management Specification

## Overview
This document defines the state management patterns using React Context API, useReducer, and Zustand for managing application state, form state, and real-time processing updates.

## State Architecture

### Application State Layers
1. **Global Application State** - Zustand stores for cross-component data
2. **Component State** - React useState for local component state
3. **Form State** - React Hook Form for form-specific state
4. **Server State** - TanStack Query for API data caching and synchronization

## Global State Management with Zustand

### Research Store

```typescript
// src/store/research-store.ts
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

interface ResearchState {
  // Current research session
  currentResearch: {
    id: string | null
    status: 'idle' | 'processing' | 'completed' | 'error'
    progress: number
    currentStage: string
    estimatedTimeRemaining?: number
    results?: MatchEvaluationResults
    error?: string
  }

  // Research history
  researchHistory: ResearchHistoryItem[]

  // UI state
  ui: {
    isProcessingMinimized: boolean
    showAdvancedOptions: boolean
    activeResultsTab: string
  }

  // Actions
  setCurrentResearch: (research: Partial<ResearchState['currentResearch']>) => void
  updateProgress: (progress: number, stage: string, timeRemaining?: number) => void
  completeResearch: (results: MatchEvaluationResults) => void
  failResearch: (error: string) => void
  resetCurrentResearch: () => void
  addToHistory: (item: ResearchHistoryItem) => void
  toggleProcessingMinimized: () => void
  setActiveResultsTab: (tab: string) => void
}

const useResearchStore = create<ResearchState>()(
  devtools(
    persist(
      (set, get) => ({
        currentResearch: {
          id: null,
          status: 'idle',
          progress: 0,
          currentStage: ''
        },

        researchHistory: [],

        ui: {
          isProcessingMinimized: false,
          showAdvancedOptions: false,
          activeResultsTab: 'overview'
        },

        setCurrentResearch: (research) =>
          set((state) => ({
            currentResearch: { ...state.currentResearch, ...research }
          })),

        updateProgress: (progress, stage, timeRemaining) =>
          set((state) => ({
            currentResearch: {
              ...state.currentResearch,
              progress,
              currentStage: stage,
              estimatedTimeRemaining: timeRemaining,
              status: 'processing'
            }
          })),

        completeResearch: (results) =>
          set((state) => ({
            currentResearch: {
              ...state.currentResearch,
              status: 'completed',
              progress: 100,
              results
            }
          })),

        failResearch: (error) =>
          set((state) => ({
            currentResearch: {
              ...state.currentResearch,
              status: 'error',
              error
            }
          })),

        resetCurrentResearch: () =>
          set({
            currentResearch: {
              id: null,
              status: 'idle',
              progress: 0,
              currentStage: ''
            }
          }),

        addToHistory: (item) =>
          set((state) => ({
            researchHistory: [item, ...state.researchHistory].slice(0, 50) // Keep last 50
          })),

        toggleProcessingMinimized: () =>
          set((state) => ({
            ui: {
              ...state.ui,
              isProcessingMinimized: !state.ui.isProcessingMinimized
            }
          })),

        setActiveResultsTab: (tab) =>
          set((state) => ({
            ui: { ...state.ui, activeResultsTab: tab }
          }))
      }),
      {
        name: 'research-store',
        partialize: (state) => ({
          researchHistory: state.researchHistory,
          ui: state.ui
        })
      }
    ),
    { name: 'research-store' }
  )
)

export default useResearchStore
```

### UI Store

```typescript
// src/store/ui-store.ts
interface UIState {
  // Global loading states
  isLoading: boolean
  loadingMessage: string

  // Error handling
  globalError: string | null
  notifications: Notification[]

  // Theme and preferences
  theme: 'light' | 'dark' | 'system'
  language: string
  compactMode: boolean

  // Actions
  setLoading: (loading: boolean, message?: string) => void
  setGlobalError: (error: string | null) => void
  addNotification: (notification: Omit<Notification, 'id'>) => void
  removeNotification: (id: string) => void
  setTheme: (theme: UIState['theme']) => void
  toggleCompactMode: () => void
}

const useUIStore = create<UIState>()(
  devtools(
    persist(
      (set, get) => ({
        isLoading: false,
        loadingMessage: '',
        globalError: null,
        notifications: [],
        theme: 'system',
        language: 'en',
        compactMode: false,

        setLoading: (loading, message = '') =>
          set({ isLoading: loading, loadingMessage: message }),

        setGlobalError: (error) =>
          set({ globalError: error }),

        addNotification: (notification) =>
          set((state) => ({
            notifications: [
              ...state.notifications,
              { ...notification, id: Date.now().toString() }
            ]
          })),

        removeNotification: (id) =>
          set((state) => ({
            notifications: state.notifications.filter(n => n.id !== id)
          })),

        setTheme: (theme) => set({ theme }),

        toggleCompactMode: () =>
          set((state) => ({ compactMode: !state.compactMode }))
      }),
      {
        name: 'ui-store',
        partialize: (state) => ({
          theme: state.theme,
          language: state.language,
          compactMode: state.compactMode
        })
      }
    )
  )
)

export default useUIStore
```

## Form State Management

### Research Form State

```typescript
// src/hooks/use-research-form.ts
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const researchFormSchema = z.object({
  linkedinUrl: z.string().url().refine(url => url.includes('linkedin.com')),
  cvFile: z.instanceof(File).nullable(),
  jobDescription: z.string().min(100).optional(),
  jobDescriptionFile: z.instanceof(File).nullable().optional(),
  useJobDescriptionFile: z.boolean()
}).refine((data) => {
  if (data.useJobDescriptionFile) {
    return data.jobDescriptionFile !== null
  } else {
    return data.jobDescription && data.jobDescription.length >= 100
  }
})

type ResearchFormData = z.infer<typeof researchFormSchema>

const useResearchForm = (onSubmit: (data: ResearchFormData) => void) => {
  const form = useForm<ResearchFormData>({
    resolver: zodResolver(researchFormSchema),
    defaultValues: {
      linkedinUrl: '',
      cvFile: null,
      jobDescription: '',
      jobDescriptionFile: null,
      useJobDescriptionFile: false
    },
    mode: 'onBlur'
  })

  const { formState: { errors, isSubmitting, isValid } } = form

  // Auto-save form data to localStorage
  const watchedValues = form.watch()

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      localStorage.setItem('research-form-draft', JSON.stringify({
        linkedinUrl: watchedValues.linkedinUrl,
        jobDescription: watchedValues.jobDescription,
        useJobDescriptionFile: watchedValues.useJobDescriptionFile
      }))
    }, 1000)

    return () => clearTimeout(timeoutId)
  }, [watchedValues])

  // Load draft on mount
  useEffect(() => {
    const draft = localStorage.getItem('research-form-draft')
    if (draft) {
      try {
        const parsedDraft = JSON.parse(draft)
        form.reset(parsedDraft, { keepDefaultValues: true })
      } catch (error) {
        console.warn('Invalid form draft in localStorage')
      }
    }
  }, [form])

  const clearDraft = useCallback(() => {
    localStorage.removeItem('research-form-draft')
  }, [])

  const handleSubmit = form.handleSubmit((data) => {
    clearDraft()
    onSubmit(data)
  })

  return {
    form,
    errors,
    isSubmitting,
    isValid,
    handleSubmit,
    clearDraft
  }
}
```

## Server State Management with TanStack Query

### Query Configuration

```typescript
// src/lib/query-client.ts
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 30, // 30 minutes
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors
        if (error.status >= 400 && error.status < 500) {
          return false
        }
        return failureCount < 3
      },
      refetchOnWindowFocus: false
    },
    mutations: {
      retry: false
    }
  }
})
```

### Research Queries and Mutations

```typescript
// src/hooks/use-research-queries.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { researchApi } from '@/services'

// Research status query
export const useResearchStatus = (researchId: string | null) => {
  return useQuery({
    queryKey: ['research', 'status', researchId],
    queryFn: () => researchApi.getResearchStatus(researchId!),
    enabled: !!researchId,
    refetchInterval: (data) => {
      // Stop polling when completed or failed
      return data?.status === 'processing' ? 2000 : false
    }
  })
}

// Research results query
export const useResearchResults = (researchId: string | null) => {
  return useQuery({
    queryKey: ['research', 'results', researchId],
    queryFn: () => researchApi.getResearchResults(researchId!),
    enabled: !!researchId,
    staleTime: Infinity // Results don't change once completed
  })
}

// Submit research mutation
export const useSubmitResearch = () => {
  const queryClient = useQueryClient()
  const setCurrentResearch = useResearchStore(state => state.setCurrentResearch)

  return useMutation({
    mutationFn: researchApi.submitResearch,
    onSuccess: (response) => {
      setCurrentResearch({
        id: response.researchId,
        status: 'processing'
      })

      // Invalidate and refetch research status
      queryClient.invalidateQueries({
        queryKey: ['research', 'status', response.researchId]
      })
    },
    onError: (error) => {
      useUIStore.getState().setGlobalError(
        `Failed to submit research: ${error.message}`
      )
    }
  })
}

// Cancel research mutation
export const useCancelResearch = () => {
  const queryClient = useQueryClient()
  const resetCurrentResearch = useResearchStore(state => state.resetCurrentResearch)

  return useMutation({
    mutationFn: researchApi.cancelResearch,
    onSuccess: (_, researchId) => {
      resetCurrentResearch()
      queryClient.invalidateQueries({
        queryKey: ['research', 'status', researchId]
      })
    }
  })
}
```

## Context Providers

### Application Context Provider

```typescript
// src/context/app-context.tsx
interface AppContextValue {
  user: User | null
  isAuthenticated: boolean
  permissions: string[]
}

const AppContext = createContext<AppContextValue | null>(null)

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [permissions, setPermissions] = useState<string[]>([])

  useEffect(() => {
    // Initialize authentication state
    const token = localStorage.getItem('auth_token')
    if (token) {
      // Validate token and set user
      validateTokenAndSetUser(token)
    }
  }, [])

  const value = {
    user,
    isAuthenticated,
    permissions
  }

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  )
}

export const useAppContext = () => {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider')
  }
  return context
}
```

### Research Context Provider

```typescript
// src/context/research-context.tsx
interface ResearchContextValue {
  currentResearchId: string | null
  startResearch: (data: ResearchFormData) => Promise<void>
  cancelCurrentResearch: () => Promise<void>
  isProcessing: boolean
}

const ResearchContext = createContext<ResearchContextValue | null>(null)

export const ResearchProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const currentResearch = useResearchStore(state => state.currentResearch)
  const submitMutation = useSubmitResearch()
  const cancelMutation = useCancelResearch()

  const startResearch = useCallback(async (data: ResearchFormData) => {
    try {
      await submitMutation.mutateAsync(data)
    } catch (error) {
      console.error('Failed to start research:', error)
      throw error
    }
  }, [submitMutation])

  const cancelCurrentResearch = useCallback(async () => {
    if (currentResearch.id) {
      await cancelMutation.mutateAsync(currentResearch.id)
    }
  }, [currentResearch.id, cancelMutation])

  const value = {
    currentResearchId: currentResearch.id,
    startResearch,
    cancelCurrentResearch,
    isProcessing: currentResearch.status === 'processing'
  }

  return (
    <ResearchContext.Provider value={value}>
      {children}
    </ResearchContext.Provider>
  )
}

export const useResearchContext = () => {
  const context = useContext(ResearchContext)
  if (!context) {
    throw new Error('useResearchContext must be used within ResearchProvider')
  }
  return context
}
```

## Custom Hooks for State Integration

### Research State Hook

```typescript
// src/hooks/use-research-state.ts
const useResearchState = () => {
  const store = useResearchStore()
  const { currentResearchId } = useResearchContext()

  // Combine store state with server state
  const statusQuery = useResearchStatus(currentResearchId)
  const resultsQuery = useResearchResults(
    store.currentResearch.status === 'completed' ? currentResearchId : null
  )

  // Sync server state with local store
  useEffect(() => {
    if (statusQuery.data) {
      store.updateProgress(
        statusQuery.data.progress,
        statusQuery.data.currentStage,
        statusQuery.data.estimatedTimeRemaining
      )
    }
  }, [statusQuery.data, store])

  useEffect(() => {
    if (resultsQuery.data) {
      store.completeResearch(resultsQuery.data)
    }
  }, [resultsQuery.data, store])

  return {
    currentResearch: store.currentResearch,
    isLoading: statusQuery.isLoading || resultsQuery.isLoading,
    error: statusQuery.error || resultsQuery.error,
    progress: store.currentResearch.progress,
    currentStage: store.currentResearch.currentStage,
    results: store.currentResearch.results,
    ui: store.ui
  }
}
```

### Notification System Hook

```typescript
// src/hooks/use-notifications.ts
const useNotifications = () => {
  const { notifications, addNotification, removeNotification } = useUIStore()

  const showSuccess = useCallback((message: string) => {
    addNotification({
      type: 'success',
      message,
      duration: 5000
    })
  }, [addNotification])

  const showError = useCallback((message: string) => {
    addNotification({
      type: 'error',
      message,
      duration: 8000
    })
  }, [addNotification])

  const showWarning = useCallback((message: string) => {
    addNotification({
      type: 'warning',
      message,
      duration: 6000
    })
  }, [addNotification])

  const showInfo = useCallback((message: string) => {
    addNotification({
      type: 'info',
      message,
      duration: 4000
    })
  }, [addNotification])

  // Auto-remove notifications after duration
  useEffect(() => {
    notifications.forEach(notification => {
      if (notification.duration) {
        setTimeout(() => {
          removeNotification(notification.id)
        }, notification.duration)
      }
    })
  }, [notifications, removeNotification])

  return {
    notifications,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    removeNotification
  }
}
```

## State Persistence

### Local Storage Persistence

```typescript
// src/utils/storage.ts
class StorageManager {
  private prefix = 'candidate-research-'

  setItem<T>(key: string, value: T): void {
    try {
      localStorage.setItem(
        `${this.prefix}${key}`,
        JSON.stringify(value)
      )
    } catch (error) {
      console.warn('Failed to save to localStorage:', error)
    }
  }

  getItem<T>(key: string): T | null {
    try {
      const item = localStorage.getItem(`${this.prefix}${key}`)
      return item ? JSON.parse(item) : null
    } catch (error) {
      console.warn('Failed to read from localStorage:', error)
      return null
    }
  }

  removeItem(key: string): void {
    localStorage.removeItem(`${this.prefix}${key}`)
  }

  clear(): void {
    Object.keys(localStorage)
      .filter(key => key.startsWith(this.prefix))
      .forEach(key => localStorage.removeItem(key))
  }
}

export const storage = new StorageManager()
```

## Performance Optimization

### Memoization and Selectors

```typescript
// src/hooks/use-research-selectors.ts
const useResearchSelectors = () => {
  // Memoized selectors to prevent unnecessary re-renders
  const currentResearchId = useResearchStore(
    useCallback(state => state.currentResearch.id, [])
  )

  const isProcessing = useResearchStore(
    useCallback(state => state.currentResearch.status === 'processing', [])
  )

  const processingProgress = useResearchStore(
    useCallback(state => ({
      progress: state.currentResearch.progress,
      stage: state.currentResearch.currentStage,
      timeRemaining: state.currentResearch.estimatedTimeRemaining
    }), [])
  )

  const hasResults = useResearchStore(
    useCallback(state => !!state.currentResearch.results, [])
  )

  return {
    currentResearchId,
    isProcessing,
    processingProgress,
    hasResults
  }
}
```

This comprehensive state management specification provides a robust, scalable, and performant foundation for managing all application state, including form data, server state, UI state, and real-time updates.