# Responsive Design & Accessibility Specification

## Overview
This document defines the responsive design patterns, accessibility requirements, and UI/UX guidelines for creating an inclusive and professional user experience across all devices and user capabilities.

## Responsive Design Strategy

### Breakpoint System

```css
/* Tailwind CSS Breakpoints */
sm: 640px    /* Small tablets and large phones */
md: 768px    /* Tablets */
lg: 1024px   /* Small laptops */
xl: 1280px   /* Desktops */
2xl: 1536px  /* Large desktops */
```

### Mobile-First Approach

```typescript
// Design progression: Mobile → Tablet → Desktop
const ResponsiveLayout = () => {
  return (
    <div className={`
      /* Mobile (default) */
      px-4 py-6 space-y-4

      /* Tablet */
      md:px-6 md:py-8 md:space-y-6

      /* Desktop */
      lg:px-8 lg:py-12 lg:space-y-8 lg:max-w-7xl lg:mx-auto

      /* Large Desktop */
      2xl:px-12
    `}>
      {/* Content */}
    </div>
  )
}
```

## Component Responsive Patterns

### Research Form Responsive Layout

```typescript
// src/components/forms/responsive-research-form.tsx
const ResponsiveResearchForm = () => {
  return (
    <form className="space-y-6">
      {/* LinkedIn URL - Full width on mobile, constrained on desktop */}
      <div className="w-full lg:max-w-2xl">
        <LinkedinUrlInput />
      </div>

      {/* CV Upload and Job Description - Stack on mobile, side-by-side on desktop */}
      <div className="space-y-6 lg:space-y-0 lg:grid lg:grid-cols-2 lg:gap-8">
        <div className="space-y-2">
          <CVUpload />
        </div>
        <div className="space-y-2">
          <JobDescriptionInput />
        </div>
      </div>

      {/* Submit button - Full width on mobile, auto width on desktop */}
      <div className="pt-4">
        <Button
          type="submit"
          className="w-full md:w-auto md:px-12"
          size="lg"
        >
          Start Research
        </Button>
      </div>
    </form>
  )
}
```

### Processing Screen Responsive Layout

```typescript
// src/components/processing/responsive-processing-screen.tsx
const ResponsiveProcessingScreen = () => {
  const isMobile = useMediaQuery('(max-width: 768px)')

  if (isMobile) {
    return (
      <div className="p-4 space-y-4">
        {/* Simplified mobile layout */}
        <Card>
          <CardContent className="p-4">
            <div className="text-center space-y-4">
              <CircularProgress value={progress} size="lg" />
              <div>
                <h3 className="font-semibold">{currentStage}</h3>
                <p className="text-sm text-muted-foreground">
                  {progress}% complete
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Collapsible stage details */}
        <Collapsible>
          <CollapsibleTrigger className="w-full">
            <Button variant="outline" className="w-full">
              View Details
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <StageDetails stages={stages} />
          </CollapsibleContent>
        </Collapsible>
      </div>
    )
  }

  // Desktop layout with side-by-side content
  return (
    <div className="container mx-auto p-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <ProgressIndicator />
        </div>
        <div>
          <AgentActivityMonitor />
        </div>
      </div>
    </div>
  )
}
```

### Results Dashboard Responsive Layout

```typescript
// src/components/results/responsive-results-dashboard.tsx
const ResponsiveResultsDashboard = ({ results }: ResultsProps) => {
  return (
    <div className="space-y-6">
      {/* Hero section - always full width */}
      <div className="w-full">
        <MatchScoreDisplay
          score={results.overall_score}
          decision={results.decision}
          justification={results.justification}
        />
      </div>

      {/* Content grid - stack on mobile, grid on desktop */}
      <div className="space-y-6 lg:space-y-0 lg:grid lg:grid-cols-12 lg:gap-8">

        {/* Main content - full width on mobile, 8 cols on desktop */}
        <div className="space-y-6 lg:col-span-8">
          <ScoreBreakdown subScores={results.sub_scores} />
          <EvidenceReasoning
            reasons={results.reasons}
            evidence={results.evidence}
            missingData={results.missing_data}
          />
        </div>

        {/* Sidebar - full width on mobile, 4 cols on desktop */}
        <div className="space-y-6 lg:col-span-4">
          <CandidateProfileSummary />
          <JobRequirementsComparison />
        </div>
      </div>

      {/* Actions - centered on mobile, left-aligned on desktop */}
      <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
        <ExportButton />
        <ShareButton />
        <StartNewResearchButton />
      </div>
    </div>
  )
}
```

## Mobile-Specific Optimizations

### Touch Targets and Interactions

```typescript
// Ensure minimum 44px touch targets
const TouchFriendlyButton = ({ children, ...props }: ButtonProps) => {
  return (
    <Button
      className={cn(
        "min-h-[44px] min-w-[44px]", // Minimum touch target size
        "active:scale-95 transition-transform", // Touch feedback
        props.className
      )}
      {...props}
    >
      {children}
    </Button>
  )
}

// Mobile-optimized file upload
const MobileFileUpload = () => {
  return (
    <div className="relative">
      <input
        type="file"
        accept=".pdf,.doc,.docx"
        capture="environment" // Use camera for document scanning
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
      />
      <div className="border-2 border-dashed border-muted-foreground rounded-lg p-8 text-center">
        <div className="space-y-4">
          <CameraIcon className="h-12 w-12 mx-auto text-muted-foreground" />
          <div>
            <p className="font-medium">Upload or Scan Document</p>
            <p className="text-sm text-muted-foreground">
              Tap to browse files or use camera
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
```

### Mobile Navigation Patterns

```typescript
// Mobile-first navigation with progressive enhancement
const ResponsiveNavigation = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  return (
    <nav className="bg-background border-b">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">

          {/* Logo */}
          <div className="flex-shrink-0">
            <Logo />
          </div>

          {/* Desktop navigation */}
          <div className="hidden md:flex space-x-8">
            <NavigationItems />
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            >
              <MenuIcon className="h-6 w-6" />
            </Button>
          </div>
        </div>

        {/* Mobile menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden py-4 border-t">
            <div className="space-y-2">
              <MobileNavigationItems />
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}
```

## Accessibility Implementation

### WCAG 2.1 AA Compliance

#### Color and Contrast

```css
/* Ensure sufficient color contrast ratios */
:root {
  /* Text on background: 4.5:1 minimum */
  --foreground: hsl(222.2 84% 4.9%);
  --background: hsl(0 0% 100%);

  /* Interactive elements: 3:1 minimum */
  --primary: hsl(221.2 83.2% 53.3%);
  --primary-foreground: hsl(210 40% 98%);

  /* Error states: High contrast */
  --destructive: hsl(0 84.2% 60.2%);
  --destructive-foreground: hsl(210 40% 98%);
}

/* Dark mode variants */
@media (prefers-color-scheme: dark) {
  :root {
    --foreground: hsl(210 40% 98%);
    --background: hsl(222.2 84% 4.9%);
  }
}
```

#### Semantic HTML Structure

```typescript
// Proper heading hierarchy and landmark regions
const AccessibleLayout = ({ children }: LayoutProps) => {
  return (
    <>
      <header role="banner">
        <nav role="navigation" aria-label="Main navigation">
          <NavigationMenu />
        </nav>
      </header>

      <main role="main" id="main-content">
        <h1 className="sr-only">Candidate Research Portal</h1>
        {children}
      </main>

      <footer role="contentinfo">
        <FooterContent />
      </footer>
    </>
  )
}

// Skip to content link for keyboard users
const SkipToContent = () => {
  return (
    <a
      href="#main-content"
      className={cn(
        "sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4",
        "bg-primary text-primary-foreground px-4 py-2 rounded-md",
        "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
      )}
    >
      Skip to main content
    </a>
  )
}
```

#### Keyboard Navigation

```typescript
// Comprehensive keyboard support
const AccessibleForm = () => {
  const formRef = useRef<HTMLFormElement>(null)

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (event.key === 'Escape') {
      // Handle escape key - close modals, clear focus, etc.
      event.preventDefault()
      document.activeElement?.blur()
    }

    if (event.key === 'Enter' && event.ctrlKey) {
      // Ctrl+Enter to submit form
      event.preventDefault()
      formRef.current?.requestSubmit()
    }
  }, [])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  return (
    <form ref={formRef} className="space-y-6">
      {/* Form fields with proper tab order */}
      <div>
        <Label htmlFor="linkedin-url">LinkedIn Profile URL</Label>
        <Input
          id="linkedin-url"
          type="url"
          aria-describedby="linkedin-url-description linkedin-url-error"
          aria-invalid={!!errors.linkedinUrl}
        />
        <div id="linkedin-url-description" className="text-sm text-muted-foreground">
          Enter the candidate's LinkedIn profile URL
        </div>
        {errors.linkedinUrl && (
          <div id="linkedin-url-error" role="alert" className="text-sm text-destructive">
            {errors.linkedinUrl.message}
          </div>
        )}
      </div>
    </form>
  )
}
```

#### Screen Reader Support

```typescript
// Announcements and live regions
const ScreenReaderAnnouncements = () => {
  const [announcement, setAnnouncement] = useState('')

  const announceToScreenReader = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    setAnnouncement(message)

    // Clear announcement after delay to allow re-announcing the same message
    setTimeout(() => setAnnouncement(''), 1000)
  }, [])

  return (
    <div
      aria-live="polite"
      aria-atomic="true"
      className="sr-only"
    >
      {announcement}
    </div>
  )
}

// Progress announcements
const AccessibleProgressIndicator = ({ progress, stage }: ProgressProps) => {
  const prevProgress = useRef(progress)

  useEffect(() => {
    // Announce significant progress updates
    if (progress > prevProgress.current + 10 || progress === 100) {
      announceToScreenReader(`Progress update: ${stage} is ${progress}% complete`)
      prevProgress.current = progress
    }
  }, [progress, stage])

  return (
    <div role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
      <Progress value={progress} />
      <div className="sr-only">
        {stage} progress: {progress}% complete
      </div>
    </div>
  )
}
```

#### Focus Management

```typescript
// Focus trap for modal dialogs
const FocusTrap = ({ children }: FocusTrapProps) => {
  const trapRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const trap = trapRef.current
    if (!trap) return

    const focusableElements = trap.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )

    const firstElement = focusableElements[0] as HTMLElement
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Tab') {
        if (event.shiftKey) {
          if (document.activeElement === firstElement) {
            event.preventDefault()
            lastElement.focus()
          }
        } else {
          if (document.activeElement === lastElement) {
            event.preventDefault()
            firstElement.focus()
          }
        }
      }
    }

    trap.addEventListener('keydown', handleKeyDown)
    firstElement?.focus()

    return () => {
      trap.removeEventListener('keydown', handleKeyDown)
    }
  }, [])

  return (
    <div ref={trapRef} className="focus-trap">
      {children}
    </div>
  )
}
```

## Performance Optimizations

### Responsive Images and Assets

```typescript
// Responsive image component with lazy loading
const ResponsiveImage = ({ src, alt, className }: ImageProps) => {
  return (
    <img
      src={src}
      alt={alt}
      className={cn("w-full h-auto", className)}
      loading="lazy"
      decoding="async"
      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
    />
  )
}

// Lazy load heavy components on mobile
const LazyDesktopFeatures = lazy(() => import('./DesktopFeatures'))

const ConditionalFeatures = () => {
  const isDesktop = useMediaQuery('(min-width: 1024px)')

  return (
    <div>
      {/* Always render core features */}
      <CoreFeatures />

      {/* Lazy load desktop-only features */}
      {isDesktop && (
        <Suspense fallback={<FeaturesSkeleton />}>
          <LazyDesktopFeatures />
        </Suspense>
      )}
    </div>
  )
}
```

### Viewport and Meta Tags

```html
<!-- Essential viewport and accessibility meta tags -->
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#3b82f6" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#1e40af" media="(prefers-color-scheme: dark)">

<!-- Accessibility improvements -->
<meta name="description" content="Professional candidate research and evaluation platform">
<link rel="preload" href="/fonts/inter-var.woff2" as="font" type="font/woff2" crossorigin>
```

## Media Queries and Responsive Utilities

### Custom Hook for Media Queries

```typescript
// src/hooks/use-media-query.ts
export const useMediaQuery = (query: string): boolean => {
  const [matches, setMatches] = useState(false)

  useEffect(() => {
    const media = window.matchMedia(query)

    if (media.matches !== matches) {
      setMatches(media.matches)
    }

    const listener = (event: MediaQueryListEvent) => {
      setMatches(event.matches)
    }

    media.addListener(listener)
    return () => media.removeListener(listener)
  }, [matches, query])

  return matches
}

// Breakpoint-specific hooks
export const useIsMobile = () => useMediaQuery('(max-width: 767px)')
export const useIsTablet = () => useMediaQuery('(min-width: 768px) and (max-width: 1023px)')
export const useIsDesktop = () => useMediaQuery('(min-width: 1024px)')
export const useReducedMotion = () => useMediaQuery('(prefers-reduced-motion: reduce)')
```

### Responsive Component Variants

```typescript
// Container with responsive padding and max-width
const ResponsiveContainer = ({ children, className }: ContainerProps) => {
  return (
    <div className={cn(
      "mx-auto px-4 sm:px-6 lg:px-8",
      "max-w-7xl",
      className
    )}>
      {children}
    </div>
  )
}

// Responsive grid system
const ResponsiveGrid = ({ children, cols }: GridProps) => {
  const gridCols = {
    1: "grid-cols-1",
    2: "grid-cols-1 md:grid-cols-2",
    3: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
    4: "grid-cols-1 md:grid-cols-2 lg:grid-cols-4"
  }

  return (
    <div className={cn("grid gap-4 lg:gap-6", gridCols[cols])}>
      {children}
    </div>
  )
}
```

## Testing Responsive Design

### Visual Regression Testing

```typescript
// Responsive design test scenarios
const responsiveTestCases = [
  { name: 'Mobile Portrait', width: 375, height: 667 },
  { name: 'Mobile Landscape', width: 667, height: 375 },
  { name: 'Tablet Portrait', width: 768, height: 1024 },
  { name: 'Tablet Landscape', width: 1024, height: 768 },
  { name: 'Desktop', width: 1440, height: 900 },
  { name: 'Large Desktop', width: 1920, height: 1080 }
]

// Accessibility audit checklist
const accessibilityChecklist = [
  'Color contrast ratios meet WCAG AA standards',
  'All interactive elements have focus indicators',
  'Form labels are properly associated',
  'Error messages are announced to screen readers',
  'Page has proper heading hierarchy',
  'Skip links are available for keyboard users',
  'All images have descriptive alt text',
  'Progress updates are announced',
  'Modal dialogs trap focus properly'
]
```

This specification ensures the application provides an excellent user experience across all devices and is fully accessible to users with diverse abilities and assistive technologies.