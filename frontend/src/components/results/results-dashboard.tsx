import * as React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { MatchScoreDisplay } from "./match-score-display"
import { ScoreBreakdown } from "./score-breakdown"
import { CandidateProfileSummary } from "./candidate-profile-summary"
import { EvidenceReasoning } from "./evidence-reasoning"
import { cn } from "@/utils/cn"
import type { MatchEvaluationResults, CandidateProfile } from "@/types"

interface ResultsDashboardProps {
  results: MatchEvaluationResults
  candidateData: CandidateProfile
  linkedinUrl: string
  onExport?: (format: 'pdf' | 'json' | 'csv') => void
  onStartNewResearch?: () => void
  className?: string
}

const ResultsDashboard = React.forwardRef<HTMLDivElement, ResultsDashboardProps>(
  ({ results, candidateData, linkedinUrl, onExport, onStartNewResearch, className }, ref) => {
    const [showExportDropdown, setShowExportDropdown] = React.useState(false)

    const handleExport = (format: 'pdf' | 'json' | 'csv') => {
      onExport?.(format)
      setShowExportDropdown(false)
    }

    const generateCandidateHighlights = (results: MatchEvaluationResults): string[] => {
      const highlights: string[] = []

      // Add highlights based on strong scores
      if (results.sub_scores.skills >= 80) {
        highlights.push("Strong technical skills alignment with job requirements")
      }
      if (results.sub_scores.experience >= 80) {
        highlights.push("Excellent experience level and background")
      }
      if (results.sub_scores.culture >= 80) {
        highlights.push("Great cultural fit and soft skills")
      }
      if (results.sub_scores.domain >= 80) {
        highlights.push("Strong domain knowledge and industry experience")
      }

      // Add evidence-based highlights
      results.evidence.forEach(evidence => {
        if (evidence.source === 'candidate' && evidence.field.toLowerCase().includes('skill')) {
          highlights.push(`Verified skill: ${evidence.field}`)
        }
      })

      return highlights.slice(0, 4) // Limit to top 4 highlights
    }

    const candidateHighlights = generateCandidateHighlights(results)

    return (
      <div ref={ref} className={cn("max-w-6xl mx-auto space-y-8", className)}>
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-foreground">
            Research Results
          </h1>
          <p className="text-muted-foreground text-lg">
            Comprehensive candidate analysis and match evaluation
          </p>
        </div>

        {/* Main Score Display */}
        <div className="flex justify-center">
          <MatchScoreDisplay
            score={results.overall_score}
            decision={results.decision}
            justification={results.justification}
            animated={true}
            className="w-full max-w-md"
          />
        </div>

        {/* Two-column layout for detailed information */}
        <div className="grid gap-8 lg:grid-cols-2">
          {/* Left Column - Candidate Information */}
          <div className="space-y-6">
            <CandidateProfileSummary
              candidate={candidateData}
              linkedinUrl={linkedinUrl}
              highlights={candidateHighlights}
            />
          </div>

          {/* Right Column - Score Breakdown */}
          <div className="space-y-6">
            <ScoreBreakdown
              subScores={results.sub_scores}
              showDetails={true}
              animated={true}
            />
          </div>
        </div>

        {/* Evidence and Analysis Section */}
        <EvidenceReasoning
          reasons={results.reasons}
          evidence={results.evidence}
          missingData={results.missing_data}
        />

        {/* Action Buttons */}
        <Card>
          <CardContent className="p-6">
            <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
              <div className="text-center sm:text-left">
                <h3 className="font-semibold text-lg mb-1">What's Next?</h3>
                <p className="text-muted-foreground text-sm">
                  Save these results or start a new candidate analysis
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                {/* Export Dropdown */}
                {onExport && (
                  <div className="relative">
                    <Button
                      variant="outline"
                      onClick={() => setShowExportDropdown(!showExportDropdown)}
                      className="w-full sm:w-auto"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Export Results
                      <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </Button>

                    {showExportDropdown && (
                      <div className="absolute right-0 mt-2 w-48 bg-background border border-border rounded-lg shadow-lg z-10">
                        <div className="py-1">
                          <button
                            onClick={() => handleExport('pdf')}
                            className="w-full text-left px-4 py-2 text-sm hover:bg-muted transition-colors"
                          >
                            <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Export as PDF
                          </button>
                          <button
                            onClick={() => handleExport('json')}
                            className="w-full text-left px-4 py-2 text-sm hover:bg-muted transition-colors"
                          >
                            <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            Export as JSON
                          </button>
                          <button
                            onClick={() => handleExport('csv')}
                            className="w-full text-left px-4 py-2 text-sm hover:bg-muted transition-colors"
                          >
                            <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
                            </svg>
                            Export as CSV
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* New Research Button */}
                {onStartNewResearch && (
                  <Button
                    onClick={onStartNewResearch}
                    className="w-full sm:w-auto"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    New Research
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer Info */}
        <div className="text-center text-sm text-muted-foreground">
          <p>
            Analysis powered by Coral Protocol Multi-Agent System
          </p>
          <p className="mt-1">
            Generated on {new Date().toLocaleDateString()} at {new Date().toLocaleTimeString()}
          </p>
        </div>

        {/* Screen Reader Summary */}
        <div className="sr-only">
          <h2>Results Summary</h2>
          <p>
            Overall match score: {results.overall_score} percent.
            Decision: {results.decision}.
            {results.justification}
          </p>
          <p>
            Score breakdown: Skills {results.sub_scores.skills} percent,
            Experience {results.sub_scores.experience} percent,
            Culture {results.sub_scores.culture} percent,
            Domain {results.sub_scores.domain} percent,
            Logistics {results.sub_scores.logistics} percent.
          </p>
        </div>

        {/* Click Outside Handler for Export Dropdown */}
        {showExportDropdown && (
          <div
            className="fixed inset-0 z-0"
            onClick={() => setShowExportDropdown(false)}
          />
        )}
      </div>
    )
  }
)

ResultsDashboard.displayName = "ResultsDashboard"

export { ResultsDashboard }