import { useRef, useEffect } from 'react'
import type { DangerSegment, VideoMetadata } from '../types'

interface VideoPlayerProps {
  videoUrl: string
  metadata: VideoMetadata
  dangerSegments: DangerSegment[]
  currentTime: number
  onTimeUpdate: (time: number) => void
}

export function VideoPlayer({ videoUrl, metadata, dangerSegments, currentTime, onTimeUpdate }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const handleTimeUpdate = () => {
      onTimeUpdate(video.currentTime)
    }

    video.addEventListener('timeupdate', handleTimeUpdate)
    return () => video.removeEventListener('timeupdate', handleTimeUpdate)
  }, [onTimeUpdate])

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = Number(e.target.value)
    if (videoRef.current) {
      videoRef.current.currentTime = time
    }
    onTimeUpdate(time)
  }

  const handleMarkerClick = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time
    }
    onTimeUpdate(time)
  }

  function fmtDuration(s: number) {
    return `${Math.floor(s / 60)}:${(s % 60).toFixed(0).padStart(2, '0')}`
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-lg">
      <video
        ref={videoRef}
        src={videoUrl}
        className="w-full aspect-video bg-black"
        controls={false}
        muted
        playsInline
      />
      <div className="p-4 space-y-3 bg-slate-900">
        <div className="flex items-center gap-4">
          <button
            onClick={() => videoRef.current?.paused ? videoRef.current.play() : videoRef.current?.pause()}
            className="w-10 h-10 flex items-center justify-center bg-slate-800 hover:bg-slate-700 rounded-full transition-colors"
          >
            {/* simple play/pause text since we don't have heroicons */}
            <span className="text-xs font-bold text-slate-300">P/P</span>
          </button>

          <div className="flex-1 relative flex items-center h-8 group">
            {/* Scrubber Background */}
            <div className="absolute left-0 right-0 h-2 bg-slate-800 rounded-full overflow-hidden">
               <div 
                 className="h-full bg-blue-500 transition-all duration-100 ease-linear" 
                 style={{ width: `${(currentTime / metadata.duration_seconds) * 100}%` }}
               />
            </div>
            
            {/* Danger Markers */}
            {dangerSegments.map((seg, i) => (
              <div
                key={i}
                onClick={() => handleMarkerClick(seg.peak_time)}
                className="absolute w-2 h-4 bg-red-500 rounded-sm cursor-pointer hover:scale-150 transition-transform -translate-y-1/2 top-1/2 z-10 animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.8)]"
                style={{ left: `calc(${(seg.peak_time / metadata.duration_seconds) * 100}% - 4px)` }}
                title={`Danger: ${seg.roi} at ${seg.peak_time}s`}
              />
            ))}

            {/* Native input for actual seeking behavior layered on top */}
            <input
              type="range"
              min={0}
              max={metadata.duration_seconds}
              step={0.1}
              value={currentTime}
              onChange={handleSeek}
              className="absolute inset-0 w-full opacity-0 cursor-pointer z-20"
            />
          </div>
          
          <div className="text-xs font-mono text-slate-400 min-w-[80px] text-right">
            {fmtDuration(currentTime)} / {fmtDuration(metadata.duration_seconds)}
          </div>
        </div>
      </div>
    </div>
  )
}
