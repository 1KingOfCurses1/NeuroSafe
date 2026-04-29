import { UploadZone } from '../components/UploadZone'

interface UploadPageProps {
  onJobCreated: (jobId: string) => void
}

export function UploadPage({ onJobCreated }: UploadPageProps) {
  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-xl space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">
            Neuro<span className="text-blue-400">Safe</span>
          </h1>
          <p className="text-slate-400 text-sm leading-relaxed">
            Screen any video for photosensitive epilepsy triggers using TRIBE v2 cortical modelling.
          </p>
        </div>

        <UploadZone onJobCreated={onJobCreated} />

        <p className="text-center text-xs text-slate-600">
          Analysis runs on your server · No data leaves your infrastructure
        </p>
      </div>
    </div>
  )
}
