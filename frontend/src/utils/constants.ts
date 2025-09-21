export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'
export const MAX_FILE_SIZE = import.meta.env.VITE_MAX_FILE_SIZE || 10485760 // 10MB
export const ALLOWED_FILE_TYPES = ['.pdf', '.doc', '.docx', '.txt']

export const VALIDATION_MESSAGES = {
  linkedinUrl: {
    required: 'LinkedIn URL is required',
    invalid: 'Please enter a valid LinkedIn profile URL',
    format: 'URL must be in format: https://linkedin.com/in/username'
  },
  cvFile: {
    required: 'Please upload your CV',
    size: 'File size must be less than 10MB',
    type: 'Only PDF, DOC, and DOCX files are supported'
  },
  jobDescription: {
    required: 'Job description is required',
    tooShort: 'Job description must be at least 100 characters',
    tooLong: 'Job description must be less than 10,000 characters'
  }
}