import * as React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ProgressIndicator } from "./progress-indicator"
import { StatusMessage } from "./status-message"
import { cn } from "@/utils/cn"
import type { ProcessingState, StatusMessage as StatusMessageType, ResearchError } from "./types"

interface ProcessingScreenProps {
  researchId: string
  processingState: ProcessingState
  statusMessages: StatusMessageType[]
  onCancel: () => void
  onMinimize: () => void
  onError: (error: ResearchError) => void
  className?: string
}

const ProcessingScreen = React.forwardRef<HTMLDivElement, ProcessingScreenProps>(
  ({ researchId, processingState, statusMessages, onCancel, onMinimize, onError, className }, ref) => {
    const [showAllMessages, setShowAllMessages] = React.useState(false)
    const [isConfirmingCancel, setIsConfirmingCancel] = React.useState(false)

    const visibleMessages = React.useMemo(() => {
      if (showAllMessages) {
        return statusMessages
      }
      return statusMessages.slice(-3) // Show last 3 messages
    }, [statusMessages, showAllMessages])

    const handleCancelClick = () => {
      if (isConfirmingCancel) {
        onCancel()
      } else {
        setIsConfirmingCancel(true)
        // Auto-reset confirmation after 3 seconds
        setTimeout(() => setIsConfirmingCancel(false), 3000)
      }
    }

    const hasError = processingState.error !== undefined
    const isCompleted = processingState.overallProgress >= 100

    return (
      <div ref={ref} className={cn("max-w-4xl mx-auto space-y-6", className)}>
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Research in Progress
          </h1>
          <p className="text-muted-foreground">
            Research ID: <span className="font-mono text-sm">{researchId}</span>
          </p>
        </div>

        {/* Error Banner */}
        {hasError && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="p-4">
              <div className="flex items-start space-x-3">
                <svg className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L3.732 19c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                <div className="flex-1">
                  <h3 className="font-medium text-red-900">Processing Error</h3>
                  <p className="text-sm text-red-800 mt-1">{processingState.error?.message}</p>
                  {processingState.error?.retryable && (
                    <div className="mt-3 space-x-2">
                      <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
                        Try Again
                      </Button>
                      <Button variant="ghost" size="sm" onClick={onCancel}>
                        Cancel
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Main Content */}
        <div className="grid gap-6 md:grid-cols-2">
          {/* Progress Section */}
          <div className="space-y-6">
            <ProgressIndicator
              stages={processingState.stages}
              currentStage={processingState.currentStage}
              overallProgress={processingState.overallProgress}
              estimatedTimeRemaining={processingState.estimatedTimeRemaining}
            />

            {/* Controls */}
            <Card>
              <CardContent className="p-4">
                <div className="flex justify-between items-center">
                  <div className="flex space-x-2">
                    <Button
                      variant={isConfirmingCancel ? "destructive" : "outline"}
                      onClick={handleCancelClick}
                      disabled={isCompleted}
                    >
                      {isConfirmingCancel ? "Confirm Cancel" : "Cancel Research"}
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={onMinimize}
                      disabled={isCompleted}
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                      </svg>
                      Minimize
                    </Button>
                  </div>

                  {isConfirmingCancel && (
                    <p className="text-xs text-muted-foreground">
                      Click "Confirm Cancel" again to stop research
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Status Messages Section */}
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Activity Log</CardTitle>
                  {statusMessages.length > 3 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowAllMessages(!showAllMessages)}
                    >
                      {showAllMessages ? "Show Less" : `Show All (${statusMessages.length})`}
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-3 max-h-96 overflow-y-auto">
                {visibleMessages.length === 0 ? (
                  <div className="text-center text-muted-foreground py-6">
                    <svg className="w-8 h-8 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-sm">Waiting for status updates...</p>
                  </div>
                ) : (
                  visibleMessages.map((message) => (
                    <StatusMessage key={message.id} message={message} />
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Completion Banner */}
        {isCompleted && !hasError && (
          <Card className="border-green-200 bg-green-50">
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <h3 className="font-medium text-green-900">Research Complete!</h3>
                  <p className="text-sm text-green-800">
                    All agents have finished processing. View your results below.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    )
  }
)

ProcessingScreen.displayName = "ProcessingScreen"

export { ProcessingScreen }