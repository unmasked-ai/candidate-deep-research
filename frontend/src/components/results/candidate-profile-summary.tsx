import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { cn } from "@/utils/cn"
import type { CandidateProfile } from "@/types"

interface CandidateProfileSummaryProps {
  candidate: CandidateProfile
  linkedinUrl: string
  highlights?: string[]
  className?: string
}

const CandidateProfileSummary = React.forwardRef<HTMLDivElement, CandidateProfileSummaryProps>(
  ({ candidate, linkedinUrl, highlights = [], className }, ref) => {
    const formatExperience = (years: number): string => {
      if (years < 1) return "Less than 1 year"
      if (years === 1) return "1 year"
      return `${years} years`
    }

    const getExperienceLevel = (years: number): { label: string; color: string } => {
      if (years < 2) return { label: "Junior", color: "text-blue-600 bg-blue-50" }
      if (years < 5) return { label: "Mid-level", color: "text-green-600 bg-green-50" }
      if (years < 10) return { label: "Senior", color: "text-purple-600 bg-purple-50" }
      return { label: "Expert", color: "text-orange-600 bg-orange-50" }
    }

    const experienceLevel = getExperienceLevel(candidate.years_experience)

    return (
      <Card ref={ref} className={className}>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <span>Candidate Profile</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-3">
            <div>
              <h3 className="text-xl font-semibold text-foreground">{candidate.name}</h3>
              {candidate.current_title && (
                <p className="text-muted-foreground mt-1">{candidate.current_title}</p>
              )}
              {candidate.company && (
                <p className="text-sm text-muted-foreground">at {candidate.company}</p>
              )}
            </div>

            {/* LinkedIn Link */}
            <div>
              <a
                href={linkedinUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-blue-600 hover:text-blue-800 hover:underline text-sm transition-colors"
              >
                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
                </svg>
                View LinkedIn Profile
                <svg className="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            </div>
          </div>

          {/* Experience and Level */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Experience</Label>
              <div className="flex items-center space-x-2">
                <span className="text-lg font-semibold">
                  {formatExperience(candidate.years_experience)}
                </span>
                <span className={cn(
                  "px-2 py-1 rounded-full text-xs font-medium",
                  experienceLevel.color
                )}>
                  {experienceLevel.label}
                </span>
              </div>
            </div>

            {candidate.location && (
              <div className="space-y-2">
                <Label className="text-sm font-medium">Location</Label>
                <div className="flex items-center space-x-1">
                  <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span className="text-sm">{candidate.location}</span>
                </div>
              </div>
            )}
          </div>

          {/* Industry Experience */}
          {candidate.industry_experience && candidate.industry_experience.length > 0 && (
            <div className="space-y-2">
              <Label className="text-sm font-medium">Industry Experience</Label>
              <div className="flex flex-wrap gap-2">
                {candidate.industry_experience.map((industry, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-muted text-muted-foreground rounded text-sm"
                  >
                    {industry}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Key Skills */}
          {candidate.skills.length > 0 && (
            <div className="space-y-2">
              <Label className="text-sm font-medium">Key Skills</Label>
              <div className="flex flex-wrap gap-2">
                {candidate.skills.slice(0, 12).map((skill, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-primary/10 text-primary rounded text-sm font-medium"
                  >
                    {skill}
                  </span>
                ))}
                {candidate.skills.length > 12 && (
                  <span className="px-2 py-1 bg-muted text-muted-foreground rounded text-sm">
                    +{candidate.skills.length - 12} more
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Education */}
          {candidate.education && candidate.education.length > 0 && (
            <div className="space-y-2">
              <Label className="text-sm font-medium">Education</Label>
              <div className="space-y-1">
                {candidate.education.map((edu, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                    </svg>
                    <span className="text-sm">{edu}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Certifications */}
          {candidate.certifications && candidate.certifications.length > 0 && (
            <div className="space-y-2">
              <Label className="text-sm font-medium">Certifications</Label>
              <div className="space-y-1">
                {candidate.certifications.map((cert, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                    </svg>
                    <span className="text-sm">{cert}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Highlights from Analysis */}
          {highlights.length > 0 && (
            <div className="space-y-2">
              <Label className="text-sm font-medium">Analysis Highlights</Label>
              <div className="space-y-2">
                {highlights.map((highlight, index) => (
                  <div key={index} className="flex items-start space-x-2">
                    <svg className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="text-sm text-muted-foreground">{highlight}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Screen Reader Summary */}
          <div className="sr-only">
            Candidate profile for {candidate.name}.
            {candidate.current_title && `Current title: ${candidate.current_title}.`}
            Experience: {formatExperience(candidate.years_experience)}.
            {candidate.skills.length > 0 && `Skills include: ${candidate.skills.slice(0, 5).join(', ')}.`}
          </div>
        </CardContent>
      </Card>
    )
  }
)

CandidateProfileSummary.displayName = "CandidateProfileSummary"

export { CandidateProfileSummary }