import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Label } from "@/components/ui/label"
import { cn } from "@/utils/cn"
import type { Evidence } from "@/types"

interface EvidenceReasoningProps {
  reasons: string[]
  evidence: Evidence[]
  missingData: string[]
  className?: string
}

const getSourceVariant = (source: Evidence['source']) => {
  switch (source) {
    case 'candidate':
      return 'bg-blue-100 text-blue-800 border-blue-200'
    case 'job':
      return 'bg-green-100 text-green-800 border-green-200'
    case 'company':
      return 'bg-purple-100 text-purple-800 border-purple-200'
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200'
  }
}

const getSourceIcon = (source: Evidence['source']) => {
  switch (source) {
    case 'candidate':
      return (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      )
    case 'job':
      return (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V8a2 2 0 012-2V6" />
        </svg>
      )
    case 'company':
      return (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      )
    default:
      return null
  }
}

const formatMissingDataLabel = (item: string): string => {
  return item
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
}

const EvidenceReasoning = React.forwardRef<HTMLDivElement, EvidenceReasoningProps>(
  ({ reasons, evidence, missingData, className }, ref) => {
    const [expandedEvidence, setExpandedEvidence] = React.useState<Set<number>>(new Set())

    const toggleEvidence = (index: number) => {
      const newExpanded = new Set(expandedEvidence)
      if (newExpanded.has(index)) {
        newExpanded.delete(index)
      } else {
        newExpanded.add(index)
      }
      setExpandedEvidence(newExpanded)
    }

    return (
      <Card ref={ref} className={className}>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>Analysis Details</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="reasons">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="reasons">
                Key Reasons ({reasons.length})
              </TabsTrigger>
              <TabsTrigger value="evidence">
                Evidence ({evidence.length})
              </TabsTrigger>
              <TabsTrigger value="missing">
                Missing Data ({missingData.length})
              </TabsTrigger>
            </TabsList>

            {/* Key Reasons Tab */}
            <TabsContent value="reasons" className="space-y-3 mt-4">
              {reasons.length > 0 ? (
                reasons.map((reason, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 rounded-lg bg-muted/50">
                    <div className="flex-shrink-0">
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-medium">
                        {index + 1}
                      </span>
                    </div>
                    <p className="text-sm leading-relaxed flex-1">{reason}</p>
                  </div>
                ))
              ) : (
                <div className="text-center text-muted-foreground py-6">
                  <svg className="w-8 h-8 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-sm">No specific reasons provided</p>
                </div>
              )}
            </TabsContent>

            {/* Evidence Tab */}
            <TabsContent value="evidence" className="space-y-3 mt-4">
              {evidence.length > 0 ? (
                evidence.map((item, index) => {
                  const isExpanded = expandedEvidence.has(index)
                  const quote = item.quote
                  const shouldTruncate = quote.length > 100

                  return (
                    <div key={index} className="border border-muted rounded-lg p-4 space-y-3">
                      {/* Evidence Header */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className={cn(
                            "inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border",
                            getSourceVariant(item.source)
                          )}>
                            {getSourceIcon(item.source)}
                            {item.source}
                          </span>
                          <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                            {item.field}
                          </span>
                        </div>
                        {shouldTruncate && (
                          <button
                            onClick={() => toggleEvidence(index)}
                            className="text-xs text-primary hover:text-primary/80 transition-colors"
                          >
                            {isExpanded ? 'Show Less' : 'Show More'}
                          </button>
                        )}
                      </div>

                      {/* Evidence Quote */}
                      <blockquote className="relative">
                        <div className="absolute top-0 left-0 w-1 h-full bg-primary/20 rounded-full" />
                        <p className="text-sm italic text-muted-foreground pl-4 leading-relaxed">
                          "{shouldTruncate && !isExpanded
                            ? `${quote.substring(0, 100)}...`
                            : quote}"
                        </p>
                      </blockquote>
                    </div>
                  )
                })
              ) : (
                <div className="text-center text-muted-foreground py-6">
                  <svg className="w-8 h-8 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  <p className="text-sm">No evidence was provided for this analysis</p>
                </div>
              )}
            </TabsContent>

            {/* Missing Data Tab */}
            <TabsContent value="missing" className="space-y-3 mt-4">
              {missingData.length > 0 ? (
                <div className="space-y-2">
                  <div className="flex items-center space-x-2 text-amber-600 mb-3">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L3.732 19c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                    <Label className="font-medium">
                      The following data was not available for analysis:
                    </Label>
                  </div>
                  {missingData.map((item, index) => (
                    <div key={index} className="flex items-center space-x-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                      <svg className="w-4 h-4 text-amber-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-sm text-amber-800">
                        {formatMissingDataLabel(item)}
                      </span>
                    </div>
                  ))}
                  <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>Note:</strong> Missing data may affect the accuracy of the analysis.
                      Consider gathering additional information for a more comprehensive evaluation.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="text-center text-muted-foreground py-6">
                  <svg className="w-8 h-8 mx-auto mb-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-sm font-medium text-green-700 mb-1">Complete Data Set</p>
                  <p className="text-sm text-green-600">
                    All required data was available for analysis
                  </p>
                </div>
              )}
            </TabsContent>
          </Tabs>

          {/* Screen Reader Summary */}
          <div className="sr-only">
            Analysis details: {reasons.length} key reasons, {evidence.length} evidence items,
            {missingData.length} missing data points.
          </div>
        </CardContent>
      </Card>
    )
  }
)

EvidenceReasoning.displayName = "EvidenceReasoning"

export { EvidenceReasoning }