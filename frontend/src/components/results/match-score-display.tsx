import * as React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/utils/cn"

interface MatchScoreDisplayProps {
  score: number
  decision: 'proceed' | 'maybe' | 'reject'
  justification: string
  animated?: boolean
  className?: string
}

const useScoreAnimation = (finalScore: number, duration = 2000, enabled = true) => {
  const [currentScore, setCurrentScore] = React.useState(enabled ? 0 : finalScore)

  React.useEffect(() => {
    if (!enabled) {
      setCurrentScore(finalScore)
      return
    }

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
  }, [finalScore, duration, enabled])

  return currentScore
}

const getDecisionStyles = (decision: MatchScoreDisplayProps['decision']) => {
  switch (decision) {
    case 'proceed':
      return {
        badge: 'bg-green-100 text-green-800 border-green-200',
        progress: 'text-green-600',
        ring: 'ring-green-200'
      }
    case 'maybe':
      return {
        badge: 'bg-yellow-100 text-yellow-800 border-yellow-200',
        progress: 'text-yellow-600',
        ring: 'ring-yellow-200'
      }
    case 'reject':
      return {
        badge: 'bg-red-100 text-red-800 border-red-200',
        progress: 'text-red-600',
        ring: 'ring-red-200'
      }
  }
}

const MatchScoreDisplay = React.forwardRef<HTMLDivElement, MatchScoreDisplayProps>(
  ({ score, decision, justification, animated = true, className }, ref) => {
    const animatedScore = useScoreAnimation(score, 2000, animated)
    const styles = getDecisionStyles(decision)

    return (
      <Card ref={ref} className={cn("text-center", className)}>
        <CardContent className="pt-8 pb-6">
          {/* Circular Progress Score */}
          <div className="relative w-32 h-32 mx-auto mb-6">
            {/* Background circle */}
            <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 128 128">
              <circle
                cx="64"
                cy="64"
                r="56"
                fill="none"
                stroke="currentColor"
                strokeWidth="8"
                className="text-muted opacity-20"
              />
              <circle
                cx="64"
                cy="64"
                r="56"
                fill="none"
                stroke="currentColor"
                strokeWidth="8"
                strokeDasharray={`${(animatedScore / 100) * 352} 352`}
                strokeLinecap="round"
                className={cn("transition-all duration-500", styles.progress)}
                style={{
                  strokeDashoffset: 0
                }}
              />
            </svg>

            {/* Score Text Overlay */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="text-3xl font-bold">
                  {animatedScore}%
                </div>
                <div className="text-sm text-muted-foreground">Match</div>
              </div>
            </div>

            {/* Pulsing ring for high scores */}
            {decision === 'proceed' && (
              <div className={cn(
                "absolute inset-0 rounded-full border-4 animate-pulse",
                styles.ring
              )} />
            )}
          </div>

          {/* Decision Badge */}
          <div className="mb-4">
            <span className={cn(
              "inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border",
              styles.badge
            )}>
              {decision === 'proceed' && (
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              )}
              {decision === 'maybe' && (
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
              {decision === 'reject' && (
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              )}
              {decision.toUpperCase()}
            </span>
          </div>

          {/* Justification */}
          <p className="text-sm text-muted-foreground max-w-md mx-auto leading-relaxed">
            {justification}
          </p>

          {/* Screen Reader Content */}
          <div className="sr-only">
            Match score: {score} percent. Decision: {decision}. Justification: {justification}
          </div>
        </CardContent>
      </Card>
    )
  }
)

MatchScoreDisplay.displayName = "MatchScoreDisplay"

export { MatchScoreDisplay }