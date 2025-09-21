import * as React from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LinkedinUrlInput } from "./linkedin-url-input"
import { CvUpload } from "./cv-upload"
import { JobDescriptionInput } from "./job-description-input"
import { researchFormSchema, type ResearchFormData } from "./validation"

interface ResearchFormProps {
  onSubmit: (data: ResearchFormData) => void
  isLoading?: boolean
  initialData?: Partial<ResearchFormData>
}

const ResearchForm = React.forwardRef<HTMLFormElement, ResearchFormProps>(
  ({ onSubmit, isLoading = false, initialData }, ref) => {
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
        linkedinUrl: initialData?.linkedinUrl || 'https://linkedin.com/in/johndoe',
        cvFile: initialData?.cvFile || null,
        jobDescription: initialData?.jobDescription || `Senior Software Engineer - React & Node.js

We are seeking a talented Senior Software Engineer to join our growing team. The ideal candidate will have strong experience in modern web technologies and a passion for building scalable applications.

Key Responsibilities:
• Develop and maintain web applications using React, TypeScript, and Node.js
• Collaborate with cross-functional teams to deliver high-quality software solutions
• Write clean, maintainable, and well-tested code
• Participate in code reviews and contribute to technical decisions
• Mentor junior developers and share knowledge

Required Qualifications:
• 5+ years of experience in software development
• Strong proficiency in JavaScript/TypeScript, React, and Node.js
• Experience with modern development tools and practices (Git, CI/CD, testing frameworks)
• Bachelor's degree in Computer Science or equivalent experience
• Excellent communication and problem-solving skills

Nice to Have:
• Experience with cloud platforms (AWS, Azure, GCP)
• Knowledge of microservices architecture
• Experience with Docker and Kubernetes
• Previous experience in a startup environment

We offer competitive compensation, comprehensive benefits, and opportunities for professional growth in a dynamic, collaborative environment.`,
        jobDescriptionFile: initialData?.jobDescriptionFile || null,
        useJobDescriptionFile: initialData?.useJobDescriptionFile || false
      }
    })

    const watchedValues = watch()
    const isFormDisabled = isLoading || isSubmitting

    const handleLinkedInUrlChange = (value: string) => {
      setValue('linkedinUrl', value)
      if (errors.linkedinUrl) {
        clearErrors('linkedinUrl')
      }
    }

    const handleCvFileChange = (file: File | null) => {
      setValue('cvFile', file)
      if (errors.cvFile) {
        clearErrors('cvFile')
      }
    }

    const handleJobDescriptionTextChange = (value: string) => {
      setValue('jobDescription', value)
      if (errors.jobDescription) {
        clearErrors('jobDescription')
      }
    }

    const handleJobDescriptionFileChange = (file: File | null) => {
      setValue('jobDescriptionFile', file)
      if (errors.jobDescription || errors.jobDescriptionFile) {
        clearErrors(['jobDescription', 'jobDescriptionFile'])
      }
    }

    const handleJobDescriptionModeChange = (useFile: boolean) => {
      setValue('useJobDescriptionFile', useFile)
      // Clear the opposite field when switching modes
      if (useFile) {
        setValue('jobDescription', '')
      } else {
        setValue('jobDescriptionFile', null)
      }
      clearErrors(['jobDescription', 'jobDescriptionFile'])
    }

    const onFormSubmit = (data: ResearchFormData) => {
      onSubmit(data)
    }

    return (
      <div className="max-w-2xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>Research Form</CardTitle>
            <CardDescription>
              Submit candidate information for comprehensive analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form
              ref={ref}
              onSubmit={handleSubmit(onFormSubmit)}
              className="space-y-6"
              noValidate
            >
              <LinkedinUrlInput
                value={watchedValues.linkedinUrl}
                onChange={handleLinkedInUrlChange}
                error={errors.linkedinUrl?.message}
                disabled={isFormDisabled}
              />

              <CvUpload
                onFileSelect={handleCvFileChange}
                selectedFile={watchedValues.cvFile}
                error={errors.cvFile?.message}
                disabled={isFormDisabled}
                maxSizeBytes={10 * 1024 * 1024}
                acceptedTypes={['.pdf', '.doc', '.docx', '.txt']}
              />

              <JobDescriptionInput
                textValue={watchedValues.jobDescription || ''}
                fileValue={watchedValues.jobDescriptionFile}
                useFile={watchedValues.useJobDescriptionFile}
                onTextChange={handleJobDescriptionTextChange}
                onFileChange={handleJobDescriptionFileChange}
                onModeChange={handleJobDescriptionModeChange}
                error={errors.jobDescription?.message || errors.jobDescriptionFile?.message}
                disabled={isFormDisabled}
              />

              <div className="pt-4">
                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  disabled={isFormDisabled}
                >
                  {isFormDisabled ? (
                    <>
                      <svg
                        className="animate-spin -ml-1 mr-3 h-5 w-5"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                      Starting Research...
                    </>
                  ) : (
                    'Start Research'
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    )
  }
)

ResearchForm.displayName = "ResearchForm"

export { ResearchForm }