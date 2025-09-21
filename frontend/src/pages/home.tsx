import { Button } from '@/components/ui/button'
import { useNavigate } from 'react-router-dom'
import { Branding } from '@/components/branding'

export default function HomePage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-background">
      <Branding />
      <div className="text-center max-w-xl w-full mx-auto px-4 py-16">
        <h1 className="text-4xl font-bold text-foreground mb-4">
          Candidate Research Portal
        </h1>
        <p className="text-muted-foreground mb-8">
          Start a new candidate research session or view results.
        </p>
        <div className="flex justify-center">
          <Button size="lg" onClick={() => navigate('/app')}>
            Open Research App
          </Button>
        </div>
      </div>
    </div>
  )
}
