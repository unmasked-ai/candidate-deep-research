import { z } from 'zod'
import { validateLinkedInUrl, validateFile } from '@/utils/error-handling'

export const researchFormSchema = z.object({
  linkedinUrl: z
    .string()
    .min(1, 'LinkedIn URL is required')
    .refine(
      (url) => {
        try {
          validateLinkedInUrl(url)
          return true
        } catch (error: any) {
          throw new z.ZodError([{
            code: z.ZodIssueCode.custom,
            message: error.message,
            path: ['linkedinUrl']
          }])
        }
      },
      'Invalid LinkedIn URL'
    ),

  cvFile: z
    .instanceof(File)
    .nullable()
    .refine(
      (file) => file !== null,
      'CV file is required'
    )
    .refine(
      (file) => {
        if (!file) return false
        try {
          validateFile(file, 10 * 1024 * 1024, ['.pdf', '.doc', '.docx', '.txt'])
          return true
        } catch (error: any) {
          throw new z.ZodError([{
            code: z.ZodIssueCode.custom,
            message: error.message,
            path: ['cvFile']
          }])
        }
      },
      'Invalid CV file'
    ),

  jobDescription: z
    .string()
    .min(100, 'Job description must be at least 100 characters')
    .max(10000, 'Job description must be less than 10,000 characters')
    .optional(),

  jobDescriptionFile: z
    .instanceof(File)
    .nullable()
    .refine(
      (file) => {
        if (!file) return true
        try {
          validateFile(file, 5 * 1024 * 1024, ['.pdf', '.doc', '.docx', '.txt'])
          return true
        } catch (error: any) {
          throw new z.ZodError([{
            code: z.ZodIssueCode.custom,
            message: error.message,
            path: ['jobDescriptionFile']
          }])
        }
      },
      'Invalid job description file'
    )
    .optional(),

  useJobDescriptionFile: z.boolean()
}).refine(
  (data) => {
    if (data.useJobDescriptionFile) {
      return data.jobDescriptionFile !== null
    } else {
      return data.jobDescription && data.jobDescription.length >= 100
    }
  },
  {
    message: 'Either job description text (min 100 characters) or file is required',
    path: ['jobDescription']
  }
)

export type ResearchFormData = z.infer<typeof researchFormSchema>

export const errorMessages = {
  linkedinUrl: {
    required: 'LinkedIn URL is required',
    invalid: 'Please enter a valid LinkedIn profile URL',
    format: 'URL must be in format: https://linkedin.com/in/username'
  },
  cvFile: {
    required: 'Please upload your CV',
    size: 'File size must be less than 10MB',
    type: 'Only PDF, DOC, DOCX, and TXT files are supported',
    corrupted: 'File appears to be corrupted. Please try another file.'
  },
  jobDescription: {
    required: 'Job description is required',
    tooShort: 'Job description must be at least 100 characters',
    tooLong: 'Job description must be less than 10,000 characters'
  },
  network: {
    timeout: 'Request timed out. Please check your connection and try again.',
    offline: 'You appear to be offline. Please check your connection.',
    server: 'Server error. Please try again later.'
  }
}