# Processing Flow Components Specification

## Overview
This document defines the components that handle the user experience during the multi-agent processing pipeline, including loading states, progress tracking, and status updates.

## Processing Flow Architecture

### Overall Flow
1. **Form Submission** → Research request initiated
2. **Processing Screen** → Multi-agent pipeline execution
3. **Progress Tracking** → Real-time status updates
4. **Results Display** → Match evaluation and analysis

### Agent Pipeline Stages
1. **Interface Agent** → Orchestrates the research process
2. **LinkedIn Agent** → Scrapes LinkedIn profile data
3. **Company Research Agent** → Researches target company
4. **Person Research Agent** → Additional candidate research
5. **Role Requirements Builder** → Structures job requirements
6. **Match Evaluation Agent** → Calculates final match score

## Core Components

### 1. Processing Screen Component

**File**: `src/components/processing/processing-screen.tsx`

```typescript
interface ProcessingScreenProps {
  researchId: string
  onComplete: (results: ResearchResults) => void
  onError: (error: ResearchError) => void
}

interface ProcessingStage {
  id: string
  name: string
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'error'
  progress?: number
  estimatedDuration?: number
  startTime?: Date
  endTime?: Date
}
```

**Layout**:
```
┌─────────────────────────────────────────┐
│  🔄 Analyzing Candidate                 │
├─────────────────────────────────────────┤
│                                         │
│  [Overall Progress Bar: 45%]            │
│                                         │
│  Current Stage: Company Research        │
│  Estimated time remaining: 2 minutes    │
│                                         │
│  ✓ LinkedIn profile analyzed            │
│  🔄 Company research in progress...     │
│  ⏳ Person research pending             │
│  ⏳ Role analysis pending               │
│  ⏳ Match evaluation pending            │
│                                         │
│  [Cancel Research] [Minimize]           │
└─────────────────────────────────────────┘
```

### 2. Progress Indicator Component

**File**: `src/components/processing/progress-indicator.tsx`

```typescript
interface ProgressIndicatorProps {
  stages: ProcessingStage[]
  currentStage: string
  overallProgress: number
  estimatedTimeRemaining?: number
}
```

**Features**:
- Multi-stage progress visualization
- Individual stage status indicators
- Overall progress percentage
- Time estimation display
- Visual feedback for each agent's work

**Stage Status Icons**:
- ⏳ **Pending**: Gray circle with clock icon
- 🔄 **In Progress**: Blue circle with spinning icon
- ✓ **Completed**: Green circle with checkmark
- ❌ **Error**: Red circle with X icon

### 3. Status Message Component

**File**: `src/components/processing/status-message.tsx`

```typescript
interface StatusMessageProps {
  stage: ProcessingStage
  message: string
  timestamp: Date
  type: 'info' | 'success' | 'warning' | 'error'
}
```

**Message Types**:
- **Info**: General progress updates
- **Success**: Stage completion notifications
- **Warning**: Non-critical issues or delays
- **Error**: Failed operations or critical issues

### 4. Agent Activity Monitor

**File**: `src/components/processing/agent-activity-monitor.tsx`

```typescript
interface AgentActivityProps {
  agents: AgentStatus[]
  showDetails?: boolean
}

interface AgentStatus {
  id: string
  name: string
  status: 'idle' | 'active' | 'completed' | 'error'
  currentTask?: string
  progress?: number
  lastUpdate?: Date
}
```

**Display Format**:
```typescript
<Card>
  <CardHeader>
    <h3>Agent Pipeline Status</h3>
  </CardHeader>
  <CardContent>
    {agents.map(agent => (
      <div key={agent.id} className="flex items-center justify-between py-2">
        <div className="flex items-center space-x-3">
          <StatusIcon status={agent.status} />
          <div>
            <p className="font-medium">{agent.name}</p>
            {agent.currentTask && (
              <p className="text-sm text-muted-foreground">{agent.currentTask}</p>
            )}
          </div>
        </div>
        {agent.progress && (
          <Progress value={agent.progress} className="w-20" />
        )}
      </div>
    ))}
  </CardContent>
</Card>
```

## Real-time Updates

### WebSocket Integration

```typescript
interface WebSocketMessage {
  type: 'stage_update' | 'progress_update' | 'completion' | 'error'
  researchId: string
  data: {
    stage?: string
    progress?: number
    message?: string
    error?: string
    results?: ResearchResults
  }
}

const useProcessingUpdates = (researchId: string) => {
  const [stages, setStages] = useState<ProcessingStage[]>(defaultStages)
  const [currentStage, setCurrentStage] = useState<string>('')
  const [overallProgress, setOverallProgress] = useState<number>(0)

  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE_URL}/research/${researchId}`)

    ws.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data)
      handleWebSocketMessage(message)
    }

    return () => ws.close()
  }, [researchId])

  return { stages, currentStage, overallProgress }
}
```

### Polling Fallback

```typescript
const useProcessingPolling = (researchId: string, interval = 2000) => {
  const [processingState, setProcessingState] = useState<ProcessingState>()

  useEffect(() => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await api.getResearchStatus(researchId)
        setProcessingState(response.data)
      } catch (error) {
        console.error('Polling error:', error)
      }
    }, interval)

    return () => clearInterval(pollInterval)
  }, [researchId, interval])

  return processingState
}
```

## Error Handling

### Error Types

```typescript
interface ResearchError {
  type: 'network' | 'agent_failure' | 'timeout' | 'validation' | 'unknown'
  stage?: string
  message: string
  retryable: boolean
  details?: Record<string, any>
}
```

### Error Recovery

```typescript
const ErrorRecoveryComponent = ({ error, onRetry, onCancel }: ErrorRecoveryProps) => {
  return (
    <Alert variant="destructive">
      <AlertTriangleIcon className="h-4 w-4" />
      <AlertTitle>Processing Error</AlertTitle>
      <AlertDescription>
        {error.message}
        {error.retryable && (
          <div className="mt-3 space-x-2">
            <Button variant="outline" size="sm" onClick={onRetry}>
              Try Again
            </Button>
            <Button variant="ghost" size="sm" onClick={onCancel}>
              Cancel
            </Button>
          </div>
        )}
      </AlertDescription>
    </Alert>
  )
}
```

## Loading States

### Skeleton Components

```typescript
const ProcessingSkeleton = () => {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-3/4" />
      <Skeleton className="h-4 w-full" />
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center space-x-3">
            <Skeleton className="h-6 w-6 rounded-full" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        ))}
      </div>
    </div>
  )
}
```

### Progressive Enhancement

```typescript
const ProgressiveProcessingView = ({ hasWebSocket, researchId }: Props) => {
  if (hasWebSocket) {
    return <RealtimeProcessingView researchId={researchId} />
  }

  return <PollingProcessingView researchId={researchId} />
}
```

## User Interaction

### Cancel Research

```typescript
const CancelResearchDialog = ({ onConfirm, onCancel }: CancelDialogProps) => {
  return (
    <Dialog>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Cancel Research?</DialogTitle>
          <DialogDescription>
            This will stop the analysis in progress. You'll lose any partial results.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            Continue Research
          </Button>
          <Button variant="destructive" onClick={onConfirm}>
            Cancel Research
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
```

### Minimize/Background Processing

```typescript
const MinimizedProcessingIndicator = ({ onRestore }: MinimizedProps) => {
  return (
    <div className="fixed bottom-4 right-4 z-50">
      <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={onRestore}>
        <CardContent className="flex items-center space-x-3 p-4">
          <LoadingSpinner size="sm" />
          <div>
            <p className="font-medium text-sm">Research in progress</p>
            <p className="text-xs text-muted-foreground">Click to view details</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
```

## Performance Optimization

### Efficient Updates

```typescript
// Debounced progress updates to prevent UI thrashing
const useDebouncedProgress = (progress: number, delay = 100) => {
  const [debouncedProgress, setDebouncedProgress] = useState(progress)

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedProgress(progress)
    }, delay)

    return () => clearTimeout(timer)
  }, [progress, delay])

  return debouncedProgress
}
```

### Memory Management

```typescript
// Cleanup WebSocket connections and intervals
const useProcessingCleanup = (researchId: string) => {
  useEffect(() => {
    return () => {
      // Cleanup WebSocket
      // Clear intervals
      // Cancel pending requests
    }
  }, [researchId])
}
```

## Accessibility

### Screen Reader Support

```typescript
// Announce progress updates to screen readers
const ProgressAnnouncer = ({ stage, progress }: AnnouncerProps) => {
  return (
    <div className="sr-only" aria-live="polite" aria-atomic="true">
      {stage} is {progress}% complete
    </div>
  )
}
```

### Keyboard Navigation

```typescript
// Ensure all interactive elements are keyboard accessible
const ProcessingControls = ({ onCancel, onMinimize }: ControlsProps) => {
  return (
    <div className="flex space-x-2">
      <Button
        variant="outline"
        onClick={onCancel}
        onKeyDown={(e) => e.key === 'Enter' && onCancel()}
      >
        Cancel
      </Button>
      <Button
        variant="ghost"
        onClick={onMinimize}
        onKeyDown={(e) => e.key === 'Enter' && onMinimize()}
      >
        Minimize
      </Button>
    </div>
  )
}
```

## Integration Points

### API Endpoints

- `GET /api/research/{id}/status` - Get current research status
- `POST /api/research/{id}/cancel` - Cancel research process
- `WebSocket /ws/research/{id}` - Real-time updates

### State Management

```typescript
interface ProcessingState {
  researchId: string
  stages: ProcessingStage[]
  currentStage: string
  overallProgress: number
  estimatedTimeRemaining?: number
  error?: ResearchError
  isMinimized: boolean
}
```

This specification provides a comprehensive framework for handling the multi-agent processing flow with real-time updates, error handling, and excellent user experience during potentially long-running operations.