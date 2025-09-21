import * as React from "react"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { cn } from "@/utils/cn"

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

const JobDescriptionInput = React.forwardRef<HTMLTextAreaElement, JobDescriptionInputProps>(
  ({ textValue, fileValue, useFile, onTextChange, onFileChange, onModeChange, error, disabled }, ref) => {
    const [isDragActive, setIsDragActive] = React.useState(false)
    const fileInputRef = React.useRef<HTMLInputElement>(null)

    const formatFileSize = (bytes: number): string => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const validateFile = (file: File): string | null => {
      const maxSize = 5 * 1024 * 1024 // 5MB
      if (file.size > maxSize) {
        return `File size must be less than ${formatFileSize(maxSize)}`
      }

      const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
      if (!allowedTypes.includes(file.type)) {
        return 'Only PDF, DOC, DOCX, and TXT files are supported'
      }

      return null
    }

    const handleFileSelect = (file: File) => {
      const validationError = validateFile(file)
      if (validationError) {
        return
      }
      onFileChange(file)
    }

    const handleDragOver = (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      if (!disabled && useFile) {
        setIsDragActive(true)
      }
    }

    const handleDragLeave = (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragActive(false)
    }

    const handleDrop = (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragActive(false)

      if (disabled || !useFile) return

      const files = Array.from(e.dataTransfer.files)
      if (files.length > 0) {
        handleFileSelect(files[0])
      }
    }

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || [])
      if (files.length > 0) {
        handleFileSelect(files[0])
      }
    }

    const openFileDialog = () => {
      if (!disabled && fileInputRef.current) {
        fileInputRef.current.click()
      }
    }

    const removeFile = () => {
      onFileChange(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }

    const characterCount = textValue.length
    const maxCharacters = 10000
    const minCharacters = 100

    return (
      <div className="space-y-4">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <button
              type="button"
              role="switch"
              aria-checked={useFile}
              onClick={() => onModeChange(!useFile)}
              disabled={disabled}
              className={cn(
                "relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
                useFile ? "bg-primary" : "bg-input"
              )}
            >
              <span
                className={cn(
                  "inline-block h-4 w-4 rounded-full bg-background transition-transform",
                  useFile ? "translate-x-6" : "translate-x-1"
                )}
              />
            </button>
            <Label>Upload job description file</Label>
          </div>
        </div>

        {useFile ? (
          <div className="space-y-2">
            <Label required>Job Description File</Label>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={handleInputChange}
              className="hidden"
              disabled={disabled}
              aria-describedby={error ? "job-description-error" : "job-description-file-description"}
            />

            {fileValue ? (
              <Card>
                <CardContent className="flex items-center justify-between p-4">
                  <div className="flex items-center space-x-3">
                    <svg
                      className="h-8 w-8 text-blue-500"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    <div>
                      <p className="font-medium">{fileValue.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatFileSize(fileValue.size)}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={removeFile}
                    disabled={disabled}
                    aria-label="Remove file"
                  >
                    <svg
                      className="h-4 w-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <Card
                className={cn(
                  "border-dashed border-2 hover:border-primary/50 transition-colors cursor-pointer",
                  isDragActive && "border-primary border-2 bg-primary/5",
                  disabled && "opacity-50 cursor-not-allowed",
                  error && "border-destructive"
                )}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={openFileDialog}
              >
                <CardContent className="flex flex-col items-center justify-center py-8">
                  {isDragActive ? (
                    <>
                      <svg
                        className="h-8 w-8 text-primary mb-2"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"
                        />
                      </svg>
                      <p className="text-primary font-medium text-sm">Drop your job description here</p>
                    </>
                  ) : (
                    <>
                      <svg
                        className="h-8 w-8 text-muted-foreground mb-2"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                        />
                      </svg>
                      <p className="text-muted-foreground text-center text-sm mb-2">
                        Drag and drop job description file here, or click to browse
                      </p>
                      <p className="text-xs text-muted-foreground mb-3">
                        Supports PDF, DOC, DOCX, TXT (max 5MB)
                      </p>
                      <Button variant="outline" size="sm" disabled={disabled}>
                        Browse Files
                      </Button>
                    </>
                  )}
                </CardContent>
              </Card>
            )}

            <p id="job-description-file-description" className="text-sm text-muted-foreground">
              Upload a document containing the job description
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <Label htmlFor="job-description" required>
              Job Description
            </Label>
            <Textarea
              ref={ref}
              id="job-description"
              placeholder="Job description will be pre-filled with a sample..."
              value={textValue}
              onChange={(e) => onTextChange(e.target.value)}
              error={!!error}
              className="min-h-[200px] resize-none"
              disabled={disabled}
              aria-describedby={error ? "job-description-error" : "job-description-description"}
              aria-invalid={!!error}
            />
            <div className="flex justify-between items-center">
              <p className="text-sm text-muted-foreground">
                Minimum {minCharacters} characters required
              </p>
              <p className={cn(
                "text-sm",
                characterCount > maxCharacters ? "text-destructive" : "text-muted-foreground"
              )}>
                {characterCount} / {maxCharacters} characters
              </p>
            </div>
            <p id="job-description-description" className="text-sm text-muted-foreground">
              Enter the complete job description including requirements, responsibilities, and qualifications
            </p>
          </div>
        )}

        {error && (
          <p
            id="job-description-error"
            role="alert"
            aria-live="polite"
            className="text-sm text-destructive"
          >
            {error}
          </p>
        )}
      </div>
    )
  }
)

JobDescriptionInput.displayName = "JobDescriptionInput"

export { JobDescriptionInput }