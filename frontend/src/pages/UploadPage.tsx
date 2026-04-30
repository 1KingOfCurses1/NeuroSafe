import { UploadZone } from '../components/UploadZone'
import { Footer } from '../components/Footer'

interface UploadPageProps {
  onJobCreated: (jobId: string) => void
}

export function UploadPage({ onJobCreated }: UploadPageProps) {
  return (
    <div className="relative min-h-screen bg-[#000000] text-soft-white flex flex-col overflow-hidden selection:bg-clinical-teal/30">
      
      {/* Background Glow Effects */}
      <div className="absolute top-[-20%] left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-clinical-teal/15 blur-[120px] rounded-full opacity-60 pointer-events-none"></div>
      <div className="absolute bottom-[-10%] left-[-10%] w-[600px] h-[600px] bg-deep-navy/20 blur-[150px] rounded-full opacity-50 pointer-events-none"></div>

      <div className="relative z-10 w-full max-w-2xl space-y-12 flex-1 flex flex-col justify-center mx-auto px-4 py-20">
        {/* Hero Section */}
        <div className="text-center space-y-6 flex flex-col items-center">
          
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-deep-navy/40 border border-deep-navy/60 text-xs font-mono text-clinical-teal mb-2 tracking-wide uppercase shadow-[0_0_15px_rgba(0,169,157,0.15)] backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-clinical-teal animate-pulse"></span>
            Powered by Meta TRIBE v2
          </div>

          <h1 className="text-6xl md:text-7xl font-extrabold tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white via-white to-white/60 drop-shadow-sm pb-2">
            NeuroSafe.
          </h1>
          
          <p className="text-soft-white/60 text-lg md:text-xl max-w-lg mx-auto leading-relaxed font-light">
            Screen any video for photosensitive epilepsy triggers using real-time cortical fMRI modelling.
          </p>
        </div>

        {/* Upload Card */}
        <div className="relative group mx-auto w-full max-w-xl">
          <div className="absolute -inset-1 bg-gradient-to-r from-deep-navy/40 via-clinical-teal/20 to-deep-navy/40 rounded-3xl blur-md opacity-25 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
          <div className="relative bg-[#0A0A0B]/90 backdrop-blur-xl border border-white/5 rounded-2xl p-8 shadow-2xl">
            <UploadZone onJobCreated={onJobCreated} />
          </div>
        </div>

        <div className="flex items-center justify-center gap-6 text-xs font-mono text-soft-white/40 tracking-widest opacity-80 pt-4">
          <span>HIPAA COMPLIANT</span>
          <span className="w-1 h-1 rounded-full bg-soft-white/20"></span>
          <span>ZERO DATA RETENTION</span>
          <span className="w-1 h-1 rounded-full bg-soft-white/20"></span>
          <span>LOCAL INFERENCE</span>
        </div>
      </div>

      <div className="relative z-10 w-full mt-auto">
        <Footer />
      </div>
    </div>
  )
}
