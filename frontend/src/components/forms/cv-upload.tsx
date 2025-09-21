import * as React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { cn } from "@/utils/cn"

interface CvUploadProps {
  onFileSelect: (file: File | null) => void
  error?: string
  disabled?: boolean
  maxSizeBytes?: number
  acceptedTypes?: string[]
  selectedFile?: File | null
}

const CvUpload = React.forwardRef<HTMLInputElement, CvUploadProps>(
  ({ onFileSelect, error, disabled, maxSizeBytes = 10 * 1024 * 1024, acceptedTypes = ['.pdf', '.doc', '.docx'], selectedFile }, ref) => {
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
      // Check file size
      if (file.size > maxSizeBytes) {
        return `File size must be less than ${formatFileSize(maxSizeBytes)}`
      }

      // Check file type
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
      onFileSelect(file)
    }

    const handleDragOver = (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      if (!disabled) {
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

      if (disabled) return

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
      onFileSelect(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }

    return (
      <div className="space-y-2">
        <Label required>CV Upload</Label>

        <input
          ref={fileInputRef}
          type="file"
          accept={acceptedTypes.join(',')}
          onChange={handleInputChange}
          className="hidden"
          disabled={disabled}
          aria-describedby={error ? "cv-upload-error" : "cv-upload-description"}
        />

        {selectedFile ? (
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
                  <p className="font-medium">{selectedFile.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {formatFileSize(selectedFile.size)}
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
            <CardContent className="flex flex-col items-center justify-center py-12">
              {isDragActive ? (
                <>
                  <svg
                    className="h-12 w-12 text-primary mb-4"
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
                  <p className="text-primary font-medium">Drop your CV here</p>
                </>
              ) : (
                <>
                  <svg
                    className="h-12 w-12 text-muted-foreground mb-4"
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
                  <h3 className="text-lg font-semibold mb-2">Upload CV</h3>
                  <p className="text-muted-foreground text-center mb-4">
                    Drag and drop your CV here, or click to browse
                  </p>
                  <p className="text-sm text-muted-foreground mb-4">
                    Supports PDF, DOC, DOCX (max {formatFileSize(maxSizeBytes)})
                  </p>
                  <Button variant="outline" disabled={disabled}>
                    Browse Files
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        )}

        <p id="cv-upload-description" className="text-sm text-muted-foreground">
          Upload your resume or CV in PDF, DOC, or DOCX format
        </p>

        {error && (
          <p
            id="cv-upload-error"
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

CvUpload.displayName = "CvUpload"

export { CvUpload }