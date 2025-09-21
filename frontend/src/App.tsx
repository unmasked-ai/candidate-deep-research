import { ResearchForm } from '@/components/forms'
import { ProcessingScreen } from '@/components/processing'
import { ResultsDashboard } from '@/components/results'
import { ErrorBoundary } from '@/components/error-boundary'
import { ToastProvider, useToast } from '@/components/ui/toast'
import { useResearch, useProcessingUpdates } from '@/hooks'
import { getUserFriendlyErrorMessage } from '@/utils/error-handling'
import type { CandidateProfile } from '@/types'
import { Branding } from '@/components/branding'

const AppContent = () => {
  const {
    currentSession,
    isSubmitting,
    uploadProgress,
    statusMessages,
    isProcessingMinimized,
    activeTab,
    submitResearch,
    cancelResearch,
    exportResults,
    setProcessingMinimized,
    setActiveTab,
    clearCurrentSession
  } = useResearch()

  const { addToast } = useToast()

  // Set up real-time updates when processing
  useProcessingUpdates(currentSession?.id)

  const handleFormSubmit = async (data: any) => {
    try {
      await submitResearch(data)
      addToast({
        type: 'success',
        title: 'Research Started',
        description: 'Your candidate research has been submitted successfully.'
      })
    } catch (error) {
      console.error('Failed to submit research:', error)
      addToast({
        type: 'error',
        title: 'Submission Failed',
        description: getUserFriendlyErrorMessage(error)
      })
    }
  }

  const handleStartNewResearch = () => {
    clearCurrentSession()
    setActiveTab('form')
  }

  const handleExport = async (format: 'pdf' | 'json' | 'csv') => {
    try {
      await exportResults(format)
      addToast({
        type: 'success',
        title: 'Export Successful',
        description: `Results exported as ${format.toUpperCase()}`
      })
    } catch (error) {
      addToast({
        type: 'error',
        title: 'Export Failed',
        description: getUserFriendlyErrorMessage(error)
      })
    }
  }

  // Mock candidate profile - in real implementation this would come from the API response
  const mockCandidateProfile: CandidateProfile = {
    name: "John Doe",
    current_title: "Senior Software Engineer",
    years_experience: 8,
    industry_experience: ["Technology", "E-commerce"],
    skills: ["React", "TypeScript", "Node.js", "Python", "AWS", "Docker"],
    education: ["B.S. Computer Science - MIT"],
    certifications: ["AWS Solutions Architect", "Google Cloud Professional"],
    location: "San Francisco, CA",
    company: "Tech Corp"
  }

  const renderContent = () => {
    // Show results if research is completed
    if (currentSession?.status === 'completed' && currentSession.results) {
      return (
        <ResultsDashboard
          results={currentSession.results}
          candidateData={currentSession.candidateProfile || mockCandidateProfile}
          linkedinUrl={currentSession.linkedinUrl}
          onExport={handleExport}
          onStartNewResearch={handleStartNewResearch}
        />
      )
    }

    // Show processing screen if research is in progress
    if (currentSession && ['submitted', 'processing'].includes(currentSession.status)) {
      return (
        <ProcessingScreen
          researchId={currentSession.id}
          processingState={currentSession.processingState!}
          statusMessages={statusMessages}
          onCancel={cancelResearch}
          onMinimize={() => setProcessingMinimized(true)}
          onError={(error) => console.error('Processing error:', error)}
        />
      )
    }

    // Default to form
    return (
      <div className="max-w-2xl mx-auto">
        <ResearchForm
          onSubmit={handleFormSubmit}
          isLoading={isSubmitting}
        />

        {isSubmitting && uploadProgress > 0 && (
          <div className="mt-4 p-4 bg-muted rounded-lg">
            <div className="text-sm text-muted-foreground mb-2">
              Uploading files... {uploadProgress}%
            </div>
            <div className="w-full bg-muted-foreground/20 rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <Branding />
      <div className="container mx-auto py-8">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Candidate Research Portal
          </h1>
          <p className="text-muted-foreground text-lg">
            Professional candidate research and evaluation platform
          </p>
        </div>

        {/* Navigation Tabs (when session exists) */}
        {currentSession && (
          <div className="flex justify-center mb-8">
            <div className="flex space-x-1 bg-muted p-1 rounded-lg">
              <button
                onClick={() => setActiveTab('form')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'form'
                    ? 'bg-background text-foreground shadow'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Form
              </button>
              <button
                onClick={() => setActiveTab('processing')}
                disabled={!['submitted', 'processing'].includes(currentSession.status)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors disabled:opacity-50 ${
                  activeTab === 'processing'
                    ? 'bg-background text-foreground shadow'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Processing
              </button>
              <button
                onClick={() => setActiveTab('results')}
                disabled={currentSession.status !== 'completed'}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors disabled:opacity-50 ${
                  activeTab === 'results'
                    ? 'bg-background text-foreground shadow'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Results
              </button>
            </div>
          </div>
        )}

        {/* Main Content */}
        {renderContent()}

        {/* Footer */}
        <div className="text-center mt-8 text-sm text-muted-foreground">
          Powered by Coral Protocol Multi-Agent System
        </div>

        {/* Minimized Processing Indicator */}
        {isProcessingMinimized && currentSession && ['submitted', 'processing'].includes(currentSession.status) && (
          <div className="fixed bottom-4 right-4 z-50">
            <div
              className="bg-background border border-border rounded-lg shadow-lg cursor-pointer hover:shadow-xl transition-shadow p-4"
              onClick={() => {
                setProcessingMinimized(false)
                setActiveTab('processing')
              }}
            >
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse" />
                <div>
                  <p className="font-medium text-sm">Research in progress</p>
                  <p className="text-xs text-muted-foreground">
                    {currentSession.processingState?.overallProgress || 0}% complete
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <AppContent />
      </ToastProvider>
    </ErrorBoundary>
  )
}

export default App
