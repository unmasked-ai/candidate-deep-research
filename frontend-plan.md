# Frontend UI Specification for Candidate Deep Research

## Overview
A clean, professional web interface that allows users to submit LinkedIn URLs, upload CVs, and provide job descriptions for candidate research analysis. The system should integrate with the existing FastAPI microservice and multi-agent architecture.

## Core Features

### 1. Input Form
*Primary Inputs:*
- *LinkedIn URL Field*: Text input with URL validation and LinkedIn domain checking
- *CV Upload*: Drag & drop file upload zone supporting PDF, DOC, DOCX formats
- *Job Description*: Rich text area with formatting options

### 2. Job Description Management
- *Template System*: Save processed job descriptions as reusable templates
- *Template Dropdown*: Select from previously saved job description templates
- *Template Management*: View, edit, and delete saved job descriptions
- *Auto-save*: Automatically save job descriptions after processing for future use

### 3. Processing Flow
- *Loading Screen*: Animated skeleton/spinner with progress indicators (placeholder for future enhancement)
- *Real-time Updates*: Progress tracking during agent processing
- *Status Messages*: Clear feedback on current processing stage
- *Results Display*: Structured output showing research findings

## Technical Implementation

### Frontend Framework
- *Framework*: React with TypeScript
- *Styling*: Tailwind CSS + shadcn/ui component library
- *State Management*: React Context API + useReducer for complex state
- *Form Handling*: react-hook-form with zod validation schemas
- *File Upload*: react-dropzone for drag & drop CV uploads
- *HTTP Client*: Axios for API communication

### UI/UX Design
- *Layout*: Clean, step-by-step wizard interface
- *Responsive*: Desktop-first with tablet support
- *Accessibility*: WCAG 2.1 AA compliant
- *Error Handling*: Inline validation with helpful error messages
- *Loading States*: Skeleton screens and progress indicators

## Component Structure


src/
├── components/
│   ├── forms/
│   │   ├── LinkedInUrlInput.tsx
│   │   ├── CVUpload.tsx
│   │   └── JobDescriptionInput.tsx
│   ├── templates/
│   │   ├── TemplateDropdown.tsx
│   │   ├── TemplateManager.tsx
│   │   └── TemplateCard.tsx
│   ├── processing/
│   │   ├── LoadingScreen.tsx
│   │   ├── ProgressIndicator.tsx
│   │   └── StatusMessage.tsx
│   ├── results/
│   │   ├── ResultsDashboard.tsx
│   │   ├── CandidateProfile.tsx
│   │   └── MatchAnalysis.tsx
│   └── ui/
│       ├── Button.tsx
│       ├── Input.tsx
│       ├── Card.tsx
│       └── Modal.tsx
├── hooks/
│   ├── useTemplates.ts
│   ├── useFileUpload.ts
│   └── useResearch.ts
├── services/
│   ├── api.ts
│   ├── templates.ts
│   └── validation.ts
└── types/
    ├── research.ts
    ├── templates.ts
    └── api.ts


## API Integration

### Endpoints
- *POST /research*: Submit research request (existing)
- *POST /templates*: Save job description template (new)
- *GET /templates*: Retrieve saved templates (new)
- *DELETE /templates/{id}*: Delete template (new)
- *POST /upload/cv*: Handle CV file upload (new)

### Data Flow
1. User fills form with LinkedIn URL, uploads CV, enters/selects job description
2. Frontend validates inputs and uploads CV to backend
3. API call to /research endpoint with form data
4. Real-time updates via WebSocket or polling
5. Results displayed in structured dashboard
6. Option to save job description as template

## User Interface Layout

### Main Form (Step 1)

┌─────────────────────────────────────────┐
│  Candidate Research Portal              │
├─────────────────────────────────────────┤
│  📋 LinkedIn Profile                    │
│  [________________________]            │
│                                         │
│  📄 CV Upload                          │
│  ┌─────────────────────────────────────┐ │
│  │  Drag & drop CV here or click      │ │
│  │  Supports: PDF, DOC, DOCX          │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  📝 Job Description                     │
│  [Template Dropdown ▼] [+ New]         │
│  ┌─────────────────────────────────────┐ │
│  │                                     │ │
│  │  Rich text editor area...          │ │
│  │                                     │ │
│  └─────────────────────────────────────┘ │
│                                         │
│                    [Start Research]     │
└─────────────────────────────────────────┘


### Loading Screen (Step 2)

┌─────────────────────────────────────────┐
│  🔄 Analyzing Candidate                 │
├─────────────────────────────────────────┤
│                                         │
│  [████████░░░░░░░░░░] 40%              │
│                                         │
│  Current Status:                        │
│  ✓ LinkedIn profile scraped             │
│  ✓ CV processed                         │
│  🔄 Company research in progress...     │
│  ⏳ Skills analysis pending             │
│  ⏳ Final assessment pending            │
│                                         │
│  [Space for enhanced loading animation] │
│                                         │
└─────────────────────────────────────────┘


### Results Display (Step 3)

┌─────────────────────────────────────────┐
│  📊 Research Results                    │
├─────────────────────────────────────────┤
│  Candidate: John Doe                    │
│  Match Score: 85% ⭐⭐⭐⭐⭐             │
│                                         │
│  📋 Summary                            │
│  📈 Skills Analysis                    │
│  🏢 Experience                         │
│  🎯 Job Fit Assessment                 │
│  📱 Social Presence                    │
│                                         │
│  [Export Report] [Save Template]        │
└─────────────────────────────────────────┘


## Data Storage

### Local Storage (Initial Implementation)
- *Templates*: Store job description templates in browser localStorage
- *Recent Searches*: Cache recent research queries
- *User Preferences*: UI settings and preferences

### Future Enhancement
- *Database*: PostgreSQL for persistent template storage
- *User Accounts*: Authentication and personal template libraries
- *Analytics*: Research history and success metrics

## Validation Rules

### LinkedIn URL
- Must be valid URL format
- Must contain "linkedin.com" domain
- Should be profile URL pattern

### CV Upload
- File size limit: 10MB maximum
- Supported formats: PDF, DOC, DOCX
- Virus scanning (future enhancement)

### Job Description
- Minimum 100 characters
- Maximum 10,000 characters
- Required fields validation

## Error Handling

### Frontend Errors
- Network connectivity issues
- File upload failures
- Validation errors
- API timeout handling

### User Feedback
- Clear error messages
- Retry mechanisms
- Graceful degradation
- Progress recovery

## Performance Considerations

### Optimization
- Lazy loading for components
- Image optimization for CV previews
- Debounced API calls
- Progressive loading for results

### Caching
- Template caching
- API response caching
- Asset caching with service worker

## Security Considerations

### Data Protection
- Client-side input validation
- File type verification
- XSS protection
- HTTPS enforcement

### Privacy
- Temporary file storage
- Data retention policies
- User consent handling
- GDPR compliance ready

## Future Enhancements

### Phase 2 Features
- Advanced loading animations and micro-interactions
- Real-time collaboration on job descriptions
- Template sharing between users
- Advanced filtering and search in results
- Export to various formats (PDF, Excel, etc.)
- Integration with ATS systems
- Batch processing for multiple candidates

### Analytics Dashboard
- Research success metrics
- Template usage statistics
- Performance analytics
- User behavior insights

## Implementation Timeline

### Phase 1 (MVP) - 2 weeks
- Basic form with three inputs
- Simple template system
- Integration with existing API
- Basic loading and results display

### Phase 2 (Enhanced) - 1 week
- Advanced UI components
- Enhanced loading experience
- Template management features
- Error handling improvements

### Phase 3 (Future) - TBD
- Advanced analytics
- User authentication
- Enhanced export options
- Performance optimizations