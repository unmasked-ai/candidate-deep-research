import * as React from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { cn } from "@/utils/cn"

interface LinkedinUrlInputProps {
  value: string
  onChange: (value: string) => void
  error?: string
  disabled?: boolean
}

const LinkedinUrlInput = React.forwardRef<HTMLInputElement, LinkedinUrlInputProps>(
  ({ value, onChange, error, disabled }, ref) => {
    const [isValidUrl, setIsValidUrl] = React.useState(false)

    React.useEffect(() => {
      const validateLinkedInUrl = (url: string) => {
        try {
          const urlObj = new URL(url)
          return urlObj.hostname.includes('linkedin.com') && url.includes('/in/')
        } catch {
          return false
        }
      }

      setIsValidUrl(value.length > 0 && validateLinkedInUrl(value))
    }, [value])

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      let newValue = e.target.value.trim()

      // Auto-format: add https:// if missing
      if (newValue && !newValue.startsWith('http://') && !newValue.startsWith('https://')) {
        newValue = `https://${newValue}`
      }

      onChange(newValue)
    }

    return (
      <div className="space-y-2">
        <Label htmlFor="linkedin-url" required>
          LinkedIn Profile URL
        </Label>
        <div className="relative">
          <svg
            className="absolute left-3 top-3 h-4 w-4 text-muted-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
            />
          </svg>
          <Input
            ref={ref}
            id="linkedin-url"
            type="url"
            placeholder="https://linkedin.com/in/johndoe"
            value={value}
            onChange={handleChange}
            error={!!error}
            disabled={disabled}
            className="pl-10"
            aria-describedby={error ? "linkedin-url-error" : "linkedin-url-description"}
            aria-invalid={!!error}
          />
          {isValidUrl && !error && (
            <svg
              className="absolute right-3 top-3 h-4 w-4 text-green-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          )}
        </div>
        <p id="linkedin-url-description" className="text-sm text-muted-foreground">
          Enter the candidate's LinkedIn profile URL
        </p>
        {error && (
          <p
            id="linkedin-url-error"
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

LinkedinUrlInput.displayName = "LinkedinUrlInput"

export { LinkedinUrlInput }