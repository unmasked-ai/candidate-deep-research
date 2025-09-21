# Input Form Components Specification

## Overview
This document defines the input form components that handle user data collection for the candidate research process. The main form collects LinkedIn URL, CV file, and job description (text or file).

## Main Form Structure

### Research Form Component

**File**: `src/components/forms/research-form.tsx`

```typescript
interface ResearchFormData {
  linkedinUrl: string
  cvFile: File | null
  jobDescription: string
  jobDescriptionFile: File | null
  useJobDescriptionFile: boolean
}

interface ResearchFormProps {
  onSubmit: (data: ResearchFormData) => void
  isLoading?: boolean
  initialData?: Partial<ResearchFormData>
}
```

**Form Layout**:
```
┌─────────────────────────────────────────┐
│  Candidate Research Portal              │
├─────────────────────────────────────────┤
│  📋 LinkedIn Profile                    │
│  [LinkedIn URL Input Component]         │
│                                         │
│  📄 CV Upload                          │
│  [CV Upload Component]                  │
│                                         │
│  📝 Job Description                     │
│  [Job Description Input Component]      │
│                                         │
│  [Submit Button - "Start Research"]     │
└─────────────────────────────────────────┘
```

## Individual Form Components

### 1. LinkedIn URL Input Component

**File**: `src/components/forms/linkedin-url-input.tsx`

```typescript
interface LinkedinUrlInputProps {
  value: string
  onChange: (value: string) => void
  error?: string
  disabled?: boolean
}
```

**Features**:
- Real-time URL validation
- LinkedIn domain checking
- Visual feedback for valid/invalid URLs
- Auto-formatting (adding https:// if missing)
- Copy-paste detection and cleaning

**Validation Rules**:
- Must be a valid URL format
- Must contain "linkedin.com" domain
- Should match LinkedIn profile URL pattern
- Maximum length: 500 characters

**UI Elements**:
```typescript
<FormField
  label="LinkedIn Profile URL"
  error={error}
  required
  description="Enter the candidate's LinkedIn profile URL"
>
  <div className="relative">
    <LinkIcon className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
    <Input
      type="url"
      placeholder="https://linkedin.com/in/username"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      error={!!error}
      className="pl-10"
      disabled={disabled}
    />
    {isValidUrl && (
      <CheckCircleIcon className="absolute right-3 top-3 h-4 w-4 text-green-500" />
    )}
  </div>
</FormField>
```

### 2. CV Upload Component

**File**: `src/components/forms/cv-upload.tsx`

```typescript
interface CvUploadProps {
  onFileSelect: (file: File | null) => void
  error?: string
  disabled?: boolean
  maxSizeBytes?: number
  acceptedTypes?: string[]
}
```

**Features**:
- Drag and drop file upload
- Click to browse file picker
- File type validation (PDF, DOC, DOCX)
- File size validation (max 10MB)
- Preview of selected file
- Remove file functionality
- Progress indicator during upload

**Accepted File Types**:
- PDF (.pdf)
- Microsoft Word (.doc, .docx)
- Plain text (.txt) - as fallback

**UI States**:

**Empty State**:
```typescript
<Card className="border-dashed border-2 hover:border-primary/50 transition-colors">
  <CardContent className="flex flex-col items-center justify-center py-12">
    <UploadIcon className="h-12 w-12 text-muted-foreground mb-4" />
    <h3 className="text-lg font-semibold mb-2">Upload CV</h3>
    <p className="text-muted-foreground text-center mb-4">
      Drag and drop your CV here, or click to browse
    </p>
    <p className="text-sm text-muted-foreground">
      Supports PDF, DOC, DOCX (max 10MB)
    </p>
    <Button variant="outline" className="mt-4">
      Browse Files
    </Button>
  </CardContent>
</Card>
```

**File Selected State**:
```typescript
<Card>
  <CardContent className="flex items-center justify-between p-4">
    <div className="flex items-center space-x-3">
      <FileIcon className="h-8 w-8 text-blue-500" />
      <div>
        <p className="font-medium">{file.name}</p>
        <p className="text-sm text-muted-foreground">
          {formatFileSize(file.size)}
        </p>
      </div>
    </div>
    <Button
      variant="ghost"
      size="sm"
      onClick={() => onFileSelect(null)}
    >
      <XIcon className="h-4 w-4" />
    </Button>
  </CardContent>
</Card>
```

**Drag Active State**:
```typescript
<Card className="border-primary border-2 bg-primary/5">
  <CardContent className="flex flex-col items-center justify-center py-12">
    <DownloadIcon className="h-12 w-12 text-primary mb-4" />
    <p className="text-primary font-medium">Drop your CV here</p>
  </CardContent>
</Card>
```

### 3. Job Description Input Component

**File**: `src/components/forms/job-description-input.tsx`

```typescript
interface JobDescriptionInputProps {
  textValue: string
  fileValue: File | null
  useFile: boolean
  onTextChange: (value: string) => void
  onFileChange: (file: File | null) => void
  onModeChange: (useFile: boolean) => void
  error?: string
  disabled?: boolean
}
```

**Features**:
- Toggle between text input and file upload
- Rich text area for manual entry
- File upload for JD documents
- Character count display
- Auto-save to localStorage (future enhancement)
- Paste detection and formatting

**Mode Toggle**:
```typescript
<div className="flex items-center space-x-4 mb-4">
  <div className="flex items-center space-x-2">
    <Switch
      checked={useFile}
      onCheckedChange={onModeChange}
      disabled={disabled}
    />
    <Label>Upload job description file</Label>
  </div>
</div>
```

**Text Input Mode**:
```typescript
<FormField
  label="Job Description"
  error={error}
  required
  description="Enter the complete job description including requirements, responsibilities, and qualifications"
>
  <Textarea
    placeholder="Paste or type the job description here..."
    value={textValue}
    onChange={(e) => onTextChange(e.target.value)}
    error={!!error}
    className="min-h-[200px] resize-none"
    disabled={disabled}
  />
  <div className="flex justify-between items-center mt-2">
    <p className="text-sm text-muted-foreground">
      Minimum 100 characters required
    </p>
    <p className="text-sm text-muted-foreground">
      {textValue.length} / 10,000 characters
    </p>
  </div>
</FormField>
```

**File Upload Mode**:
```typescript
<FormField
  label="Job Description File"
  error={error}
  required
  description="Upload a document containing the job description"
>
  <FileUploadZone
    onFileSelect={onFileChange}
    accept=".pdf,.doc,.docx,.txt"
    maxSize={5 * 1024 * 1024} // 5MB
    error={error}
    disabled={disabled}
  />
</FormField>
```

## Form Validation

### Validation Schema (Zod)

```typescript
const researchFormSchema = z.object({
  linkedinUrl: z
    .string()
    .min(1, 'LinkedIn URL is required')
    .url('Must be a valid URL')
    .refine(
      (url) => url.includes('linkedin.com'),
      'Must be a LinkedIn profile URL'
    ),

  cvFile: z
    .instanceof(File)
    .nullable()
    .refine(
      (file) => file !== null,
      'CV file is required'
    )
    .refine(
      (file) => file && file.size <= 10 * 1024 * 1024,
      'File size must be less than 10MB'
    )
    .refine(
      (file) => file && ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type),
      'File must be PDF, DOC, or DOCX'
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
      (file) => file && file.size <= 5 * 1024 * 1024,
      'File size must be less than 5MB'
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
    message: 'Either job description text or file is required',
    path: ['jobDescription']
  }
)
```

### Real-time Validation

- **LinkedIn URL**: Validate on blur and provide immediate feedback
- **CV File**: Validate on file selection with clear error messages
- **Job Description**: Validate character count in real-time

## Form State Management

### Using React Hook Form

```typescript
const {
  register,
  handleSubmit,
  formState: { errors, isSubmitting },
  watch,
  setValue,
  clearErrors
} = useForm<ResearchFormData>({
  resolver: zodResolver(researchFormSchema),
  defaultValues: {
    linkedinUrl: '',
    cvFile: null,
    jobDescription: '',
    jobDescriptionFile: null,
    useJobDescriptionFile: false
  }
})
```

### Form Submission Flow

1. **Client-side validation** using Zod schema
2. **File preparation** for multipart form upload
3. **API call** with loading state management
4. **Error handling** with user-friendly messages
5. **Success handling** with navigation to processing screen

## Error Handling

### Error Types and Messages

```typescript
const errorMessages = {
  linkedinUrl: {
    required: 'LinkedIn URL is required',
    invalid: 'Please enter a valid LinkedIn profile URL',
    format: 'URL must be in format: https://linkedin.com/in/username'
  },
  cvFile: {
    required: 'Please upload your CV',
    size: 'File size must be less than 10MB',
    type: 'Only PDF, DOC, and DOCX files are supported',
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
```

### Error Display

- **Inline errors**: Show immediately below each field
- **Global errors**: Show at top of form for general issues
- **Toast notifications**: For network and unexpected errors

## Accessibility Features

### WCAG 2.1 AA Compliance

- **Keyboard Navigation**: All form elements accessible via keyboard
- **Screen Reader Support**: Proper labels and descriptions
- **Error Announcements**: Screen readers announce validation errors
- **Focus Management**: Logical tab order and focus indicators

### Specific Implementations

```typescript
// Proper labeling
<label htmlFor="linkedin-url" className="sr-only">
  LinkedIn Profile URL
</label>
<input
  id="linkedin-url"
  aria-describedby="linkedin-url-description linkedin-url-error"
  aria-invalid={!!errors.linkedinUrl}
  {...register('linkedinUrl')}
/>

// Error announcements
<div
  id="linkedin-url-error"
  role="alert"
  aria-live="polite"
>
  {errors.linkedinUrl?.message}
</div>
```

## Mobile Responsiveness

### Responsive Design Considerations

- **Touch-friendly targets**: Minimum 44px touch targets
- **Responsive file upload**: Adapted drag zones for mobile
- **Keyboard optimization**: Mobile keyboard types (url, text)
- **Viewport optimization**: Form fits mobile screens without scrolling

### Mobile-specific Features

```typescript
// Mobile-optimized file input
<input
  type="file"
  accept=".pdf,.doc,.docx"
  capture="environment" // Use camera for document scanning
  className="hidden"
  onChange={handleFileSelect}
/>
```

## Performance Optimization

### File Upload Optimization

- **Chunked uploads**: For large files (future enhancement)
- **Progress tracking**: Real-time upload progress
- **Compression**: Client-side image compression if needed
- **Caching**: Cache validation results

### Form Performance

- **Debounced validation**: Prevent excessive validation calls
- **Memoized components**: Prevent unnecessary re-renders
- **Lazy loading**: Load file processing utilities only when needed

## Integration Points

### API Integration

The form integrates with the backend API at:
- `POST /api/research` - Submit complete research request
- `POST /api/upload/cv` - Upload CV file (if separate endpoint needed)
- `POST /api/upload/job-description` - Upload JD file (if separate endpoint needed)

### State Management

Form data integrates with global application state for:
- **Research progress tracking**
- **Error state management**
- **User session persistence**

This specification provides a comprehensive foundation for implementing robust, accessible, and user-friendly input forms that handle all required data collection for the candidate research process.