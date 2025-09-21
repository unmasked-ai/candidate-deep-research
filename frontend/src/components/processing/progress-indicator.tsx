import * as React from "react"
import { Progress } from "@/components/ui/progress"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/utils/cn"
import type { ProcessingStage } from "./types"

interface ProgressIndicatorProps {
  stages: ProcessingStage[]
  currentStage: string
  overallProgress: number
  estimatedTimeRemaining?: number
}

const StatusIcon = ({ status }: { status: ProcessingStage['status'] }) => {
  switch (status) {
    case 'pending':
      return (
        <div className="flex items-center justify-center w-6 h-6 rounded-full bg-muted">
          <svg className="w-3 h-3 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
      )
    case 'in_progress':
      return (
        <div className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-500">
          <svg className="w-3 h-3 text-white animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        </div>
      )
    case 'completed':
      return (
        <div className="flex items-center justify-center w-6 h-6 rounded-full bg-green-500">
          <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
      )
    case 'error':
      return (
        <div className="flex items-center justify-center w-6 h-6 rounded-full bg-red-500">
          <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
      )
    default:
      return null
  }
}

const formatTime = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds} seconds`
  }
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (remainingSeconds === 0) {
    return `${minutes} minute${minutes !== 1 ? 's' : ''}`
  }
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

const ProgressIndicator = React.forwardRef<HTMLDivElement, ProgressIndicatorProps>(
  ({ stages, currentStage, overallProgress, estimatedTimeRemaining }, ref) => {
    const currentStageIndex = stages.findIndex(stage => stage.id === currentStage)
    const currentStageName = stages.find(stage => stage.id === currentStage)?.name || 'Processing'

    return (
      <Card ref={ref}>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>Analyzing Candidate</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Overall Progress */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Overall Progress</span>
              <span className="text-sm text-muted-foreground">{Math.round(overallProgress)}%</span>
            </div>
            <Progress value={overallProgress} className="h-3" />
          </div>

          {/* Current Stage Info */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm">
                <span className="font-medium">Current Stage:</span> {currentStageName}
              </span>
              {estimatedTimeRemaining && (
                <span className="text-sm text-muted-foreground">
                  {formatTime(estimatedTimeRemaining)} remaining
                </span>
              )}
            </div>
          </div>

          {/* Stages List */}
          <div className="space-y-3">
            {stages.map((stage, index) => {
              const isActive = stage.id === currentStage
              const isPast = index < currentStageIndex
              const isFuture = index > currentStageIndex

              return (
                <div
                  key={stage.id}
                  className={cn(
                    "flex items-center space-x-3 p-3 rounded-lg transition-colors",
                    isActive && "bg-blue-50 border border-blue-200",
                    isPast && "bg-green-50",
                    isFuture && "bg-gray-50"
                  )}
                >
                  <StatusIcon status={stage.status} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className={cn(
                        "text-sm font-medium truncate",
                        isActive && "text-blue-900",
                        isPast && "text-green-900",
                        isFuture && "text-muted-foreground"
                      )}>
                        {stage.name}
                      </p>
                      {stage.progress !== undefined && stage.status === 'in_progress' && (
                        <span className="text-xs text-muted-foreground ml-2">
                          {Math.round(stage.progress)}%
                        </span>
                      )}
                    </div>
                    <p className={cn(
                      "text-xs mt-1",
                      isActive && "text-blue-700",
                      isPast && "text-green-700",
                      isFuture && "text-muted-foreground"
                    )}>
                      {stage.description}
                    </p>
                    {stage.progress !== undefined && stage.status === 'in_progress' && (
                      <Progress value={stage.progress} className="h-1 mt-2" />
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Screen Reader Announcements */}
          <div className="sr-only" aria-live="polite" aria-atomic="true">
            {currentStageName} is {Math.round(overallProgress)}% complete
          </div>
        </CardContent>
      </Card>
    )
  }
)

ProgressIndicator.displayName = "ProgressIndicator"

export { ProgressIndicator }