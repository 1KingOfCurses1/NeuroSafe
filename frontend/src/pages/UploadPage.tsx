import { UploadZone } from '../components/UploadZone'
import { Footer } from '../components/Footer'
import { motion } from 'framer-motion'

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
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-center space-y-6 flex flex-col items-center"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-deep-navy/40 border border-deep-navy/60 text-[10px] font-mono text-clinical-teal tracking-widest uppercase shadow-[0_0_15px_rgba(0,169,157,0.15)] backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-clinical-teal animate-pulse"></span>
            Powered by Meta TRIBE v2
          </div>

          <h1 className="text-6xl md:text-7xl font-extrabold tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white via-white to-white/60 drop-shadow-sm pb-2">
            NeuroSafe.
          </h1>
          
          <p className="text-soft-white/60 text-lg md:text-xl max-w-lg mx-auto leading-relaxed font-light">
            Screen any video for photosensitive epilepsy triggers using real-time cortical fMRI modelling.
          </p>
        </motion.div>

        {/* Upload Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
          className="relative group mx-auto w-full max-w-xl"
        >
          <div className="absolute -inset-1 bg-gradient-to-r from-deep-navy/40 via-clinical-teal/20 to-deep-navy/40 rounded-3xl blur-md opacity-25 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
          <div className="relative bg-[#0A0A0B]/90 backdrop-blur-xl border border-white/5 rounded-2xl p-8 shadow-2xl">
            <UploadZone onJobCreated={onJobCreated} />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="flex items-center justify-center gap-8 text-[10px] font-mono text-soft-white/30 tracking-widest opacity-80 pt-4"
        >
          <div className="flex items-center gap-2">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <span>HIPAA COMPLIANT</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            <span>ZERO DATA RETENTION</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>LOCAL INFERENCE</span>
          </div>
        </motion.div>
      </div>

      <div className="relative z-10 w-full mt-auto">
        <Footer />
      </div>
    </div>
  )
}
