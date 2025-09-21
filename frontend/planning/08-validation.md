# Validation Specification

## Overview
This document defines comprehensive validation patterns for user inputs, file uploads, and data processing using Zod schemas, custom validators, and real-time validation feedback.

## Validation Architecture

### Validation Layers
1. **Client-side Input Validation** - Real-time feedback for user inputs
2. **File Validation** - Type, size, and content validation for uploads
3. **Form Validation** - Complete form validation before submission
4. **API Response Validation** - Validate server responses
5. **Runtime Type Checking** - Ensure data integrity throughout the application

## Core Validation Schemas

### LinkedIn URL Validation

```typescript
// src/schemas/linkedin-validation.ts
import { z } from 'zod'

const linkedinUrlSchema = z
  .string()
  .min(1, 'LinkedIn URL is required')
  .url('Please enter a valid URL')
  .refine(
    (url) => {
      const domain = new URL(url).hostname
      return domain === 'linkedin.com' || domain === 'www.linkedin.com'
    },
    'URL must be from linkedin.com'
  )
  .refine(
    (url) => {
      // Check for profile URL pattern
      const profilePattern = /linkedin\.com\/(in|pub)\/[\w-]+\/?$/
      return profilePattern.test(url)
    },
    'Please provide a valid LinkedIn profile URL (e.g., linkedin.com/in/username)'
  )

// Custom LinkedIn URL validator with normalization
export const validateLinkedInUrl = (url: string) => {
  try {
    // Normalize URL
    let normalizedUrl = url.trim()

    // Add protocol if missing
    if (!normalizedUrl.startsWith('http')) {
      normalizedUrl = 'https://' + normalizedUrl
    }

    // Remove trailing slashes and query parameters
    const urlObj = new URL(normalizedUrl)
    urlObj.search = ''
    urlObj.hash = ''
    if (urlObj.pathname.endsWith('/')) {
      urlObj.pathname = urlObj.pathname.slice(0, -1)
    }

    const result = linkedinUrlSchema.safeParse(urlObj.toString())

    return {
      isValid: result.success,
      normalizedUrl: result.success ? urlObj.toString() : url,
      error: result.success ? null : result.error.issues[0].message
    }
  } catch (error) {
    return {
      isValid: false,
      normalizedUrl: url,
      error: 'Please enter a valid URL'
    }
  }
}
```

### File Upload Validation

```typescript
// src/schemas/file-validation.ts
interface FileValidationOptions {
  maxSizeBytes: number
  allowedTypes: string[]
  allowedExtensions: string[]
  customValidators?: Array<(file: File) => Promise<string | null>>
}

const createFileSchema = (options: FileValidationOptions) => {
  return z
    .instanceof(File, { message: 'Please select a file' })
    .refine(
      (file) => file.size <= options.maxSizeBytes,
      `File size must be less than ${formatFileSize(options.maxSizeBytes)}`
    )
    .refine(
      (file) => options.allowedTypes.includes(file.type),
      `File type not supported. Allowed types: ${options.allowedExtensions.join(', ')}`
    )
    .refine(
      (file) => {
        const extension = file.name.split('.').pop()?.toLowerCase()
        return extension && options.allowedExtensions.includes(`.${extension}`)
      },
      `File extension not supported. Allowed extensions: ${options.allowedExtensions.join(', ')}`
    )
}

// CV file validation
export const cvFileSchema = createFileSchema({
  maxSizeBytes: 10 * 1024 * 1024, // 10MB
  allowedTypes: [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain'
  ],
  allowedExtensions: ['.pdf', '.doc', '.docx', '.txt']
})

// Job description file validation
export const jobDescriptionFileSchema = createFileSchema({
  maxSizeBytes: 5 * 1024 * 1024, // 5MB
  allowedTypes: [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain'
  ],
  allowedExtensions: ['.pdf', '.doc', '.docx', '.txt']
})

// Advanced file content validation
export const validateFileContent = async (file: File): Promise<string | null> => {
  return new Promise((resolve) => {
    const reader = new FileReader()

    reader.onload = (event) => {
      const arrayBuffer = event.target?.result as ArrayBuffer

      // Check file signatures (magic numbers)
      const uint8Array = new Uint8Array(arrayBuffer.slice(0, 8))
      const signatures = {
        pdf: [0x25, 0x50, 0x44, 0x46], // %PDF
        docx: [0x50, 0x4B, 0x03, 0x04], // ZIP format (DOCX is ZIP)
        doc: [0xD0, 0xCF, 0x11, 0xE0] // OLE format
      }

      const isPDF = signatures.pdf.every((byte, i) => uint8Array[i] === byte)
      const isDocx = signatures.docx.every((byte, i) => uint8Array[i] === byte)
      const isDoc = signatures.doc.every((byte, i) => uint8Array[i] === byte)

      if (!isPDF && !isDocx && !isDoc && file.type !== 'text/plain') {
        resolve('File appears to be corrupted or not in the expected format')
      } else {
        resolve(null)
      }
    }

    reader.onerror = () => {
      resolve('Unable to read file. Please try again.')
    }

    reader.readAsArrayBuffer(file.slice(0, 100)) // Read first 100 bytes
  })
}
```

### Job Description Validation

```typescript
// src/schemas/job-description-validation.ts
const jobDescriptionTextSchema = z
  .string()
  .min(100, 'Job description must be at least 100 characters')
  .max(10000, 'Job description must be less than 10,000 characters')
  .refine(
    (text) => {
      // Check for minimum content quality
      const wordCount = text.trim().split(/\s+/).length
      return wordCount >= 20
    },
    'Job description must contain at least 20 words'
  )
  .refine(
    (text) => {
      // Check for basic job posting elements
      const keywords = ['responsibilities', 'requirements', 'qualifications', 'experience', 'skills']
      const lowerText = text.toLowerCase()
      const foundKeywords = keywords.filter(keyword => lowerText.includes(keyword))
      return foundKeywords.length >= 2
    },
    'Job description should include key sections like responsibilities, requirements, or qualifications'
  )

export const validateJobDescriptionText = (text: string) => {
  const result = jobDescriptionTextSchema.safeParse(text)

  return {
    isValid: result.success,
    error: result.success ? null : result.error.issues[0].message,
    warnings: generateJobDescriptionWarnings(text)
  }
}

const generateJobDescriptionWarnings = (text: string): string[] => {
  const warnings: string[] = []
  const lowerText = text.toLowerCase()

  // Check for common missing elements
  if (!lowerText.includes('salary') && !lowerText.includes('compensation')) {
    warnings.push('Consider including salary or compensation information')
  }

  if (!lowerText.includes('remote') && !lowerText.includes('office') && !lowerText.includes('location')) {
    warnings.push('Consider specifying work location or remote work options')
  }

  if (!lowerText.includes('benefits') && !lowerText.includes('perks')) {
    warnings.push('Consider mentioning benefits or company perks')
  }

  return warnings
}
```

## Form Validation Schema

### Complete Research Form Schema

```typescript
// src/schemas/research-form-schema.ts
export const researchFormSchema = z.object({
  linkedinUrl: linkedinUrlSchema,

  cvFile: cvFileSchema
    .nullable()
    .refine(file => file !== null, 'CV file is required'),

  jobDescription: jobDescriptionTextSchema.optional(),

  jobDescriptionFile: jobDescriptionFileSchema
    .nullable()
    .optional(),

  useJobDescriptionFile: z.boolean(),

  // Advanced options (future)
  includeSkillsAnalysis: z.boolean().default(true),
  includeCultureFit: z.boolean().default(true),
  prioritizeExperience: z.boolean().default(false)
}).refine(
  (data) => {
    // Ensure either text or file is provided for job description
    if (data.useJobDescriptionFile) {
      return data.jobDescriptionFile !== null
    } else {
      return data.jobDescription && data.jobDescription.length >= 100
    }
  },
  {
    message: 'Either job description text or file is required',
    path: ['jobDescription']
  }
)

export type ResearchFormData = z.infer<typeof researchFormSchema>
```

## Real-time Validation Hooks

### LinkedIn URL Validation Hook

```typescript
// src/hooks/use-linkedin-validation.ts
const useLinkedInValidation = (url: string, debounceMs = 500) => {
  const [validation, setValidation] = useState<{
    isValid: boolean
    normalizedUrl: string
    error: string | null
    isValidating: boolean
  }>({
    isValid: false,
    normalizedUrl: url,
    error: null,
    isValidating: false
  })

  const debouncedUrl = useDebounce(url, debounceMs)

  useEffect(() => {
    if (!debouncedUrl.trim()) {
      setValidation(prev => ({
        ...prev,
        isValid: false,
        error: null,
        isValidating: false
      }))
      return
    }

    setValidation(prev => ({ ...prev, isValidating: true }))

    const result = validateLinkedInUrl(debouncedUrl)

    setValidation({
      isValid: result.isValid,
      normalizedUrl: result.normalizedUrl,
      error: result.error,
      isValidating: false
    })
  }, [debouncedUrl])

  return validation
}
```

### File Validation Hook

```typescript
// src/hooks/use-file-validation.ts
const useFileValidation = (schema: z.ZodSchema) => {
  const [validation, setValidation] = useState<{
    isValid: boolean
    error: string | null
    isValidating: boolean
    warnings: string[]
  }>({
    isValid: false,
    error: null,
    isValidating: false,
    warnings: []
  })

  const validateFile = useCallback(async (file: File | null) => {
    if (!file) {
      setValidation({
        isValid: false,
        error: null,
        isValidating: false,
        warnings: []
      })
      return
    }

    setValidation(prev => ({ ...prev, isValidating: true }))

    try {
      // Schema validation
      const schemaResult = schema.safeParse(file)

      if (!schemaResult.success) {
        setValidation({
          isValid: false,
          error: schemaResult.error.issues[0].message,
          isValidating: false,
          warnings: []
        })
        return
      }

      // Content validation
      const contentError = await validateFileContent(file)

      if (contentError) {
        setValidation({
          isValid: false,
          error: contentError,
          isValidating: false,
          warnings: []
        })
        return
      }

      // Generate warnings
      const warnings = generateFileWarnings(file)

      setValidation({
        isValid: true,
        error: null,
        isValidating: false,
        warnings
      })
    } catch (error) {
      setValidation({
        isValid: false,
        error: 'Failed to validate file',
        isValidating: false,
        warnings: []
      })
    }
  }, [schema])

  return { validation, validateFile }
}

const generateFileWarnings = (file: File): string[] => {
  const warnings: string[] = []

  // Size warnings
  if (file.size > 5 * 1024 * 1024) { // 5MB
    warnings.push('Large file size may slow down processing')
  }

  // Type-specific warnings
  if (file.type === 'text/plain') {
    warnings.push('Text files may not preserve formatting. PDF or DOC files are recommended.')
  }

  return warnings
}
```

## Validation UI Components

### Validation Feedback Component

```typescript
// src/components/validation/validation-feedback.tsx
interface ValidationFeedbackProps {
  isValid: boolean
  error: string | null
  warnings?: string[]
  isValidating?: boolean
  showSuccessIcon?: boolean
}

const ValidationFeedback: React.FC<ValidationFeedbackProps> = ({
  isValid,
  error,
  warnings = [],
  isValidating = false,
  showSuccessIcon = true
}) => {
  if (isValidating) {
    return (
      <div className=\"flex items-center text-sm text-muted-foreground\">
        <LoadingSpinner size=\"sm\" className=\"mr-2\" />
        Validating...
      </div>
    )
  }

  return (
    <div className=\"space-y-1\">
      {error && (
        <div className=\"flex items-center text-sm text-destructive\">
          <XCircleIcon className=\"h-4 w-4 mr-2\" />
          {error}
        </div>
      )}

      {isValid && showSuccessIcon && !error && (
        <div className=\"flex items-center text-sm text-green-600\">
          <CheckCircleIcon className=\"h-4 w-4 mr-2\" />
          Valid
        </div>
      )}

      {warnings.map((warning, index) => (
        <div key={index} className=\"flex items-center text-sm text-amber-600\">
          <AlertTriangleIcon className=\"h-4 w-4 mr-2\" />
          {warning}
        </div>
      ))}
    </div>
  )
}
```

### Validated Input Component

```typescript
// src/components/validation/validated-input.tsx
interface ValidatedInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  validation?: {
    isValid: boolean
    error: string | null
    isValidating: boolean
  }
  onValidationChange?: (isValid: boolean) => void
}

const ValidatedInput = React.forwardRef<HTMLInputElement, ValidatedInputProps>(
  ({ validation, onValidationChange, className, ...props }, ref) => {
    useEffect(() => {
      onValidationChange?.(validation?.isValid ?? false)
    }, [validation?.isValid, onValidationChange])

    const getInputClassName = () => {
      const baseClass = \"flex h-10 w-full rounded-md border px-3 py-2\"

      if (validation?.isValidating) {
        return cn(baseClass, \"border-blue-300 focus:border-blue-500\", className)
      }

      if (validation?.error) {
        return cn(baseClass, \"border-destructive focus:border-destructive\", className)
      }

      if (validation?.isValid) {
        return cn(baseClass, \"border-green-500 focus:border-green-600\", className)
      }

      return cn(baseClass, \"border-input\", className)
    }

    return (
      <div className=\"space-y-2\">
        <div className=\"relative\">
          <input
            ref={ref}
            className={getInputClassName()}
            {...props}
          />

          {validation?.isValidating && (
            <LoadingSpinner
              size=\"sm\"
              className=\"absolute right-3 top-1/2 transform -translate-y-1/2\"
            />
          )}

          {validation?.isValid && !validation.isValidating && (
            <CheckCircleIcon className=\"absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-green-500\" />
          )}
        </div>

        {validation && (
          <ValidationFeedback
            isValid={validation.isValid}
            error={validation.error}
            isValidating={validation.isValidating}
            showSuccessIcon={false}
          />
        )}
      </div>
    )
  }
)
```

## API Response Validation

### Response Schema Validation

```typescript
// src/schemas/api-response-schemas.ts
export const researchResponseSchema = z.object({
  researchId: z.string().uuid(),
  status: z.enum(['initiated', 'processing', 'completed', 'failed']),
  estimatedDuration: z.number().optional(),
  progress: z.number().min(0).max(100).optional(),
  currentStage: z.string().optional(),
  error: z.string().optional()
})

export const matchEvaluationResultsSchema = z.object({
  overall_score: z.number().min(0).max(100),
  sub_scores: z.object({
    skills: z.number().min(0).max(100),
    experience: z.number().min(0).max(100),
    culture: z.number().min(0).max(100),
    domain: z.number().min(0).max(100),
    logistics: z.number().min(0).max(100)
  }),
  decision: z.enum(['proceed', 'maybe', 'reject']),
  justification: z.string().max(500),
  reasons: z.array(z.string()).max(8),
  missing_data: z.array(z.string()),
  evidence: z.array(z.object({
    source: z.enum(['candidate', 'job', 'company']),
    quote: z.string(),
    field: z.string()
  })).max(6)
})

// API response validator
export const validateApiResponse = <T>(
  schema: z.ZodSchema<T>,
  data: unknown
): { success: true; data: T } | { success: false; error: string } => {
  const result = schema.safeParse(data)

  if (result.success) {
    return { success: true, data: result.data }
  } else {
    console.error('API response validation failed:', result.error)
    return {
      success: false,
      error: 'Invalid response format from server'
    }
  }
}
```

## Validation Utilities

### Common Validation Helpers

```typescript
// src/utils/validation-utils.ts
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let timeoutId: NodeJS.Timeout

  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func.apply(null, args), delay)
  }
}

export const useDebounce = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

export const sanitizeInput = (input: string): string => {
  return input
    .trim()
    .replace(/[<>\"']/g, '') // Remove potentially dangerous characters
    .substring(0, 10000) // Limit length
}
```

This comprehensive validation specification ensures robust data integrity, user-friendly feedback, and secure handling of all user inputs throughout the application.