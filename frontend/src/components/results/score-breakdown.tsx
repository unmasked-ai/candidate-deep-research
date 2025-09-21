import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Label } from "@/components/ui/label"
import { cn } from "@/utils/cn"

interface ScoreBreakdownProps {
  subScores: {
    skills: number
    experience: number
    culture: number
    domain: number
    logistics: number
  }
  showDetails?: boolean
  animated?: boolean
  className?: string
}

const scoreDescriptions = {
  skills: "Technical and professional skills alignment",
  experience: "Years and depth of relevant experience",
  culture: "Cultural fit and soft skills assessment",
  domain: "Industry knowledge and domain expertise",
  logistics: "Location, availability, and practical considerations"
}

const getScoreColor = (score: number) => {
  if (score >= 80) return "text-green-600"
  if (score >= 60) return "text-yellow-600"
  if (score >= 40) return "text-orange-600"
  return "text-red-600"
}

const getProgressColor = (score: number) => {
  if (score >= 80) return "bg-green-500"
  if (score >= 60) return "bg-yellow-500"
  if (score >= 40) return "bg-orange-500"
  return "bg-red-500"
}

const formatScoreLabel = (key: string): string => {
  return key.charAt(0).toUpperCase() + key.slice(1)
}

const ScoreBreakdown = React.forwardRef<HTMLDivElement, ScoreBreakdownProps>(
  ({ subScores, showDetails = false, animated = true, className }, ref) => {
    const [animatedScores, setAnimatedScores] = React.useState<Record<string, number>>(
      animated ? Object.fromEntries(Object.keys(subScores).map(key => [key, 0])) : subScores
    )

    React.useEffect(() => {
      if (!animated) {
        setAnimatedScores(subScores)
        return
      }

      const duration = 1500
      const startTime = Date.now()

      const animate = () => {
        const elapsed = Date.now() - startTime
        const progress = Math.min(elapsed / duration, 1)
        const easeOut = 1 - Math.pow(1 - progress, 3)

        const newScores = Object.fromEntries(
          Object.entries(subScores).map(([key, finalScore]) => [
            key,
            Math.round(finalScore * easeOut)
          ])
        )

        setAnimatedScores(newScores)

        if (progress < 1) {
          requestAnimationFrame(animate)
        }
      }

      requestAnimationFrame(animate)
    }, [subScores, animated])

    const averageScore = Object.values(subScores).reduce((sum, score) => sum + score, 0) / Object.values(subScores).length

    return (
      <Card ref={ref} className={className}>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Score Breakdown</span>
            <span className={cn("text-sm font-normal", getScoreColor(averageScore))}>
              Avg: {Math.round(averageScore)}%
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {Object.entries(subScores).map(([category, finalScore]) => {
            const animatedScore = animatedScores[category] || 0
            const colorClass = getScoreColor(finalScore)

            return (
              <div key={category} className="space-y-3">
                <div className="flex justify-between items-center">
                  <div className="space-y-1">
                    <Label className="text-base font-medium">
                      {formatScoreLabel(category)}
                    </Label>
                    {showDetails && (
                      <p className="text-xs text-muted-foreground">
                        {scoreDescriptions[category as keyof typeof scoreDescriptions]}
                      </p>
                    )}
                  </div>
                  <div className="text-right">
                    <span className={cn("text-lg font-semibold", colorClass)}>
                      {animatedScore}%
                    </span>
                    <div className="text-xs text-muted-foreground">
                      {finalScore >= 80 && "Excellent"}
                      {finalScore >= 60 && finalScore < 80 && "Good"}
                      {finalScore >= 40 && finalScore < 60 && "Fair"}
                      {finalScore < 40 && "Poor"}
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Progress
                    value={animatedScore}
                    className="h-3"
                    style={{
                      background: `linear-gradient(to right, ${getProgressColor(finalScore)} ${animatedScore}%, #e5e7eb ${animatedScore}%)`
                    }}
                  />

                  {/* Detailed breakdown bars for high detail mode */}
                  {showDetails && (
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>0%</span>
                      <span>25%</span>
                      <span>50%</span>
                      <span>75%</span>
                      <span>100%</span>
                    </div>
                  )}
                </div>

                {/* Score interpretation */}
                {showDetails && (
                  <div className="text-xs">
                    {finalScore >= 90 && (
                      <div className="flex items-center text-green-700">
                        <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        Outstanding match
                      </div>
                    )}
                    {finalScore >= 70 && finalScore < 90 && (
                      <div className="flex items-center text-green-600">
                        <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        Strong match
                      </div>
                    )}
                    {finalScore >= 50 && finalScore < 70 && (
                      <div className="flex items-center text-yellow-600">
                        <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                        Moderate match
                      </div>
                    )}
                    {finalScore < 50 && (
                      <div className="flex items-center text-red-600">
                        <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                        Needs improvement
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}

          {/* Overall Assessment */}
          <div className="pt-4 border-t">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">Overall Assessment:</span>
              <span className={cn("font-semibold", getScoreColor(averageScore))}>
                {averageScore >= 80 && "Highly Recommended"}
                {averageScore >= 60 && averageScore < 80 && "Recommended"}
                {averageScore >= 40 && averageScore < 60 && "Consider with Caution"}
                {averageScore < 40 && "Not Recommended"}
              </span>
            </div>
          </div>

          {/* Screen Reader Summary */}
          <div className="sr-only">
            Score breakdown: {Object.entries(subScores).map(([category, score]) =>
              `${formatScoreLabel(category)}: ${score} percent`
            ).join(', ')}. Average score: {Math.round(averageScore)} percent.
          </div>
        </CardContent>
      </Card>
    )
  }
)

ScoreBreakdown.displayName = "ScoreBreakdown"

export { ScoreBreakdown }