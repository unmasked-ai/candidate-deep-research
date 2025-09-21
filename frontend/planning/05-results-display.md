# Results Display Components Specification

## Overview
This document defines the components responsible for displaying the match evaluation results from the match-evaluation agent, including the score visualization, detailed analysis, and candidate profile information.

## Results Data Structure

### Match Evaluation Response
```typescript
interface MatchEvaluationResults {
  overall_score: number           // 0-100
  sub_scores: {
    skills: number               // 0-100
    experience: number           // 0-100
    culture: number              // 0-100
    domain: number               // 0-100
    logistics: number            // 0-100
  }
  decision: 'proceed' | 'maybe' | 'reject'
  justification: string          // 100 words or less
  reasons: string[]              // Max 8 reasons
  missing_data: string[]         // What data was unavailable
  evidence: Evidence[]           // Max 6 evidence items
}

interface Evidence {
  source: 'candidate' | 'job' | 'company'
  quote: string
  field: string
}
```

## Core Display Components

### 1. Results Dashboard Component

**File**: `src/components/results/results-dashboard.tsx`

```typescript
interface ResultsDashboardProps {
  results: MatchEvaluationResults
  candidateData: CandidateProfile
  jobData: JobSpec
  onExport?: () => void
  onStartNewResearch?: () => void
}
```

**Layout Structure**:
```
┌─────────────────────────────────────────┐
│  📊 Research Results                    │
├─────────────────────────────────────────┤
│  [Match Score Component - Large]        │
│                                         │
│  ┌─────────────────┬─────────────────┐   │
│  │ Candidate Info  │ Score Breakdown │   │
│  │ Component       │ Component       │   │
│  └─────────────────┴─────────────────┘   │
│                                         │
│  [Detailed Analysis Component]          │
│                                         │
│  [Evidence & Reasoning Component]       │
│                                         │
│  [Action Buttons: Export, New Search]   │
└─────────────────────────────────────────┘
```

### 2. Match Score Display Component

**File**: `src/components/results/match-score-display.tsx`

```typescript
interface MatchScoreDisplayProps {
  score: number
  decision: 'proceed' | 'maybe' | 'reject'
  justification: string
  animated?: boolean
}
```

**Visual Design**:
- **Large circular progress indicator** showing overall score
- **Color-coded by decision**: Green (proceed), Yellow (maybe), Red (reject)
- **Animated fill** from 0 to final score on initial load
- **Decision badge** prominently displayed
- **Justification text** below the score

```typescript
<Card className="text-center">
  <CardContent className="pt-8 pb-6">
    <div className="relative w-32 h-32 mx-auto mb-6">
      <Progress
        value={score}
        className="w-32 h-32 rounded-full"
        variant={getVariantByDecision(decision)}
      />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <div className="text-3xl font-bold">{score}%</div>
          <div className="text-sm text-muted-foreground">Match</div>
        </div>
      </div>
    </div>

    <Badge variant={getBadgeVariant(decision)} className="mb-4">
      {decision.toUpperCase()}
    </Badge>

    <p className="text-sm text-muted-foreground max-w-md mx-auto">
      {justification}
    </p>
  </CardContent>
</Card>
```

### 3. Score Breakdown Component

**File**: `src/components/results/score-breakdown.tsx`

```typescript
interface ScoreBreakdownProps {
  subScores: {
    skills: number
    experience: number
    culture: number
    domain: number
    logistics: number
  }
  showDetails?: boolean
}
```

**Features**:
- **Horizontal bar charts** for each sub-score
- **Color-coded bars** based on score ranges
- **Expandable details** for each category
- **Tooltips** explaining what each score represents

```typescript
<Card>
  <CardHeader>
    <CardTitle>Score Breakdown</CardTitle>
  </CardHeader>
  <CardContent className="space-y-4">
    {Object.entries(subScores).map(([category, score]) => (
      <div key={category} className="space-y-2">
        <div className="flex justify-between items-center">
          <Label className="capitalize">{category}</Label>
          <span className="text-sm font-medium">{score}%</span>
        </div>
        <Progress value={score} className="h-2" />
      </div>
    ))}
  </CardContent>
</Card>
```

### 4. Candidate Profile Summary

**File**: `src/components/results/candidate-profile-summary.tsx`

```typescript
interface CandidateProfileSummaryProps {
  candidate: CandidateProfile
  linkedinUrl: string
  highlights: string[]
}
```

**Display Elements**:
- **Candidate name and title**
- **LinkedIn profile link**
- **Years of experience**
- **Key skills highlighted**
- **Education and certifications**
- **Top strengths from analysis**

```typescript
<Card>
  <CardHeader>
    <CardTitle>Candidate Profile</CardTitle>
  </CardHeader>
  <CardContent>
    <div className="space-y-4">
      <div>
        <h3 className="font-semibold text-lg">{candidate.name}</h3>
        {candidate.current_title && (
          <p className="text-muted-foreground">{candidate.current_title}</p>
        )}
        <a
          href={linkedinUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline text-sm"
        >
          View LinkedIn Profile →
        </a>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <Label>Experience</Label>
          <p>{candidate.years_experience} years</p>
        </div>
        <div>
          <Label>Industry</Label>
          <p>{candidate.industry_experience?.join(', ') || 'Not specified'}</p>
        </div>
      </div>

      {candidate.skills.length > 0 && (
        <div>
          <Label>Key Skills</Label>
          <div className="flex flex-wrap gap-1 mt-1">
            {candidate.skills.slice(0, 10).map(skill => (
              <Badge key={skill} variant="secondary" className="text-xs">
                {skill}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  </CardContent>
</Card>
```

### 5. Evidence and Reasoning Component

**File**: `src/components/results/evidence-reasoning.tsx`

```typescript
interface EvidenceReasoningProps {
  reasons: string[]
  evidence: Evidence[]
  missingData: string[]
}
```

**Features**:
- **Tabbed interface** for Reasons, Evidence, Missing Data
- **Source-coded evidence** (candidate, job, company)
- **Expandable items** for detailed viewing
- **Visual indicators** for data completeness

```typescript
<Card>
  <CardHeader>
    <CardTitle>Analysis Details</CardTitle>
  </CardHeader>
  <CardContent>
    <Tabs defaultValue="reasons">
      <TabsList>
        <TabsTrigger value="reasons">Key Reasons</TabsTrigger>
        <TabsTrigger value="evidence">Evidence</TabsTrigger>
        <TabsTrigger value="missing">Missing Data</TabsTrigger>
      </TabsList>

      <TabsContent value="reasons" className="space-y-2 mt-4">
        {reasons.map((reason, index) => (
          <div key={index} className="flex items-start space-x-2">
            <Badge variant="outline" className="mt-0.5 text-xs">
              {index + 1}
            </Badge>
            <p className="text-sm">{reason}</p>
          </div>
        ))}
      </TabsContent>

      <TabsContent value="evidence" className="space-y-3 mt-4">
        {evidence.map((item, index) => (
          <div key={index} className="border-l-2 border-muted pl-3">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant={getSourceVariant(item.source)} className="text-xs">
                {item.source}
              </Badge>
              <span className="text-xs text-muted-foreground">{item.field}</span>
            </div>
            <blockquote className="text-sm italic">"{item.quote}"</blockquote>
          </div>
        ))}
      </TabsContent>

      <TabsContent value="missing" className="space-y-2 mt-4">
        {missingData.length > 0 ? (
          missingData.map((item, index) => (
            <div key={index} className="flex items-center space-x-2">
              <AlertTriangleIcon className="h-4 w-4 text-amber-500" />
              <span className="text-sm">{item.replace('_', ' ')}</span>
            </div>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">All required data was available for analysis.</p>
        )}
      </TabsContent>
    </Tabs>
  </CardContent>
</Card>
```

### 6. Job Requirements Comparison

**File**: `src/components/results/job-requirements-comparison.tsx`

```typescript
interface JobRequirementsComparisonProps {
  jobSpec: JobSpec
  candidateProfile: CandidateProfile
  matchAnalysis: {
    mustHaveMatches: string[]
    mustHaveMissing: string[]
    niceToHaveMatches: string[]
    techStackMatches: string[]
  }
}
```

**Visual Elements**:
- **Side-by-side comparison** of requirements vs candidate
- **Check/X icons** for requirement matching
- **Highlighted matches** in green
- **Missing items** in red
- **Expandable sections** for detailed requirements

## Interactive Features

### 1. Export Functionality

```typescript
interface ExportOptionsProps {
  results: MatchEvaluationResults
  candidate: CandidateProfile
  onExport: (format: 'pdf' | 'json' | 'csv') => void
}

const ExportOptions = ({ results, candidate, onExport }: ExportOptionsProps) => {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline">
          <DownloadIcon className="h-4 w-4 mr-2" />
          Export Results
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuItem onClick={() => onExport('pdf')}>
          Export as PDF
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => onExport('json')}>
          Export as JSON
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => onExport('csv')}>
          Export as CSV
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```

### 2. Share Results

```typescript
const ShareResults = ({ results, candidate }: ShareResultsProps) => {
  const shareUrl = generateShareableUrl(results.id)

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">
          <ShareIcon className="h-4 w-4 mr-2" />
          Share Results
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Share Research Results</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Shareable Link</Label>
            <div className="flex space-x-2">
              <Input value={shareUrl} readOnly />
              <Button onClick={() => copyToClipboard(shareUrl)}>
                Copy
              </Button>
            </div>
          </div>
          <p className="text-sm text-muted-foreground">
            This link expires in 7 days and requires access permissions.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  )
}
```

## Responsive Design

### Mobile Layout Adaptations

```typescript
const ResponsiveResultsLayout = ({ results }: ResponsiveLayoutProps) => {
  const isMobile = useMediaQuery('(max-width: 768px)')

  if (isMobile) {
    return (
      <div className="space-y-4">
        <MatchScoreDisplay {...results} />
        <Accordion type="single" collapsible>
          <AccordionItem value="breakdown">
            <AccordionTrigger>Score Breakdown</AccordionTrigger>
            <AccordionContent>
              <ScoreBreakdown subScores={results.sub_scores} />
            </AccordionContent>
          </AccordionItem>
          <AccordionItem value="profile">
            <AccordionTrigger>Candidate Profile</AccordionTrigger>
            <AccordionContent>
              <CandidateProfileSummary {...candidateProps} />
            </AccordionContent>
          </AccordionItem>
          <AccordionItem value="analysis">
            <AccordionTrigger>Analysis Details</AccordionTrigger>
            <AccordionContent>
              <EvidenceReasoning {...evidenceProps} />
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </div>
    )
  }

  return <DesktopResultsLayout results={results} />
}
```

## Animation and Transitions

### Score Animation

```typescript
const useScoreAnimation = (finalScore: number, duration = 2000) => {
  const [currentScore, setCurrentScore] = useState(0)

  useEffect(() => {
    const startTime = Date.now()
    const animate = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / duration, 1)
      const easeOut = 1 - Math.pow(1 - progress, 3)

      setCurrentScore(Math.round(finalScore * easeOut))

      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }

    requestAnimationFrame(animate)
  }, [finalScore, duration])

  return currentScore
}
```

### Progressive Enhancement

```typescript
const ProgressiveResultsReveal = ({ children }: ProgressiveRevealProps) => {
  const [revealed, setRevealed] = useState<number>(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setRevealed(prev => prev + 1)
    }, 300)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-4">
      {React.Children.map(children, (child, index) => (
        <div
          key={index}
          className={`transition-all duration-500 ${
            index <= revealed
              ? 'opacity-100 translate-y-0'
              : 'opacity-0 translate-y-4'
          }`}
        >
          {child}
        </div>
      ))}
    </div>
  )
}
```

## Error States

### Results Error Handling

```typescript
const ResultsErrorBoundary = ({ children }: ErrorBoundaryProps) => {
  return (
    <ErrorBoundary
      fallback={
        <Card>
          <CardContent className="text-center py-12">
            <AlertTriangleIcon className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Unable to Display Results</h3>
            <p className="text-muted-foreground mb-4">
              There was an error processing the research results.
            </p>
            <Button onClick={() => window.location.reload()}>
              Try Again
            </Button>
          </CardContent>
        </Card>
      }
    >
      {children}
    </ErrorBoundary>
  )
}
```

## Accessibility Features

### Screen Reader Support

```typescript
// Proper heading hierarchy and landmark regions
<main role="main" aria-labelledby="results-heading">
  <h1 id="results-heading" className="sr-only">
    Candidate Research Results
  </h1>

  <section aria-labelledby="match-score-heading">
    <h2 id="match-score-heading">Match Score</h2>
    <div
      role="img"
      aria-label={`Match score: ${score} percent, Decision: ${decision}`}
    >
      {/* Score visualization */}
    </div>
  </section>

  <section aria-labelledby="breakdown-heading">
    <h2 id="breakdown-heading">Score Breakdown</h2>
    {/* Breakdown content */}
  </section>
</main>
```

### Keyboard Navigation

```typescript
// Ensure all interactive elements are keyboard accessible
const AccessibleResultsNavigation = ({ sections }: NavigationProps) => {
  return (
    <nav aria-label="Results sections">
      <ul role="list">
        {sections.map((section, index) => (
          <li key={section.id}>
            <a
              href={`#${section.id}`}
              className="focus:outline-none focus:ring-2 focus:ring-primary"
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  document.getElementById(section.id)?.scrollIntoView()
                }
              }}
            >
              {section.title}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}
```

This specification provides a comprehensive framework for displaying match evaluation results in an accessible, visually appealing, and highly functional interface that effectively communicates the analysis outcomes to users.