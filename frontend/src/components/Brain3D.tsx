import { Suspense, useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, useGLTF, PerspectiveCamera, Html } from '@react-three/drei'
import * as THREE from 'three'
import type { BrainFrame } from '../types'

interface Brain3DProps {
  frame: BrainFrame
  surfaceMode?: 'normal' | 'inflated'
  hemiMode?: 'open' | 'close'
}

/**
 * TRIBE v2-style brain mesh renderer.
 * Uses the real fsaverage5 pial surface (20,484 vertices)
 * exported from nilearn — the same cortical mesh Meta's TRIBE v2
 * uses for brain encoding visualization.
 *
 * Supports:
 *   - surfaceMode: "normal" (smooth pial) vs "inflated" (wireframe view)
 *   - hemiMode: "close" (both together) vs "open" (split apart)
 *   - Dynamic hot colormap activation (dark → orange → red → white)
 */
function BrainMesh({ frame, surfaceMode = 'normal', hemiMode = 'close' }: Brain3DProps) {
  const { scene } = useGLTF('/models/brain.glb')
  const meshRef = useRef<THREE.Group>(null)

  const activation = frame.max_activation || 0

  // Find peak ROI for label
  const peakRoi = useMemo(() => {
    if (!frame.roi_activations) return null
    let maxVal = -1
    let peak: string | null = null
    for (const [roi, val] of Object.entries(frame.roi_activations)) {
      if (val > maxVal) { maxVal = val; peak = roi }
    }
    return peak ? { name: peak, value: maxVal } : null
  }, [frame.roi_activations])

  // TRIBE v2 "hot" colormap: dark gray → orange → red → white
  const brainColor = useMemo(() => {
    if (activation < 0.15) return new THREE.Color('#3a3a3e')
    if (activation < 0.3) return new THREE.Color('#8B4513')
    if (activation < 0.5) return new THREE.Color('#CC4400')
    if (activation < 0.7) return new THREE.Color('#FF2200')
    if (activation < 0.85) return new THREE.Color('#FF6633')
    return new THREE.Color('#FFAA66')
  }, [activation])

  const emissiveColor = useMemo(() => {
    if (activation < 0.2) return new THREE.Color('#0a0a0a')
    if (activation < 0.5) return new THREE.Color('#993300')
    return new THREE.Color('#FF4400')
  }, [activation])

  // Gentle auto-rotation
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.002
      const pulse = 1 + Math.sin(state.clock.elapsedTime * 1.2) * 0.006
      meshRef.current.scale.set(pulse, pulse, pulse)
    }
  })

  // Apply material to the brain mesh based on mode
  useMemo(() => {
    const isInflated = surfaceMode === 'inflated'
    scene.traverse((child: any) => {
      if (child instanceof THREE.Mesh) {
        child.material = new THREE.MeshPhysicalMaterial({
          color: brainColor,
          emissive: emissiveColor,
          emissiveIntensity: activation * 0.8,
          roughness: isInflated ? 0.9 : 0.55,
          metalness: isInflated ? 0.0 : 0.1,
          clearcoat: isInflated ? 0 : 0.3,
          clearcoatRoughness: 0.4,
          transparent: true,
          opacity: isInflated ? 0.7 : 0.95,
          wireframe: isInflated,
          side: THREE.DoubleSide,
        })
        child.castShadow = true
        child.receiveShadow = true
      }
    })
  }, [scene, brainColor, emissiveColor, activation, surfaceMode])

  // Hemisphere separation for open/close
  const hemiOffset = hemiMode === 'open' ? 0.4 : 0

  return (
    <group ref={meshRef}>
      {/* When hemiMode is "open", we offset the brain to simulate hemispheres splitting.
          Since fsaverage is centered at origin, a simple X offset does the trick. */}
      <group position={[-hemiOffset, 0, 0]}>
        <primitive object={scene} scale={2.8} />
      </group>

      {peakRoi && peakRoi.value > 0.15 && (
        <Html distanceFactor={8} position={[0.5, 1.2, 0.5]} style={{ pointerEvents: 'none' }}>
          <div style={{
            background: 'rgba(0,0,0,0.8)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '8px',
            padding: '6px 12px',
            whiteSpace: 'nowrap',
            boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
          }}>
            <div style={{ fontSize: '7px', fontWeight: 700, color: 'rgba(255,255,255,0.35)', textTransform: 'uppercase', letterSpacing: '0.15em', marginBottom: '2px' }}>
              Peak Region
            </div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#F5F7FA', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#FF4400', display: 'inline-block', boxShadow: '0 0 8px #FF4400' }}></span>
              {peakRoi.name}
            </div>
          </div>
        </Html>
      )}
    </group>
  )
}

export function Brain3D({ frame, surfaceMode = 'normal', hemiMode = 'close' }: Brain3DProps) {
  return (
    <div
      className="w-full h-[380px] cursor-grab active:cursor-grabbing relative overflow-hidden"
      style={{
        background: 'radial-gradient(ellipse at center, #0d0d0d 0%, #000000 100%)',
        borderTopLeftRadius: '12px',
        borderTopRightRadius: '12px',
      }}
    >
      <Canvas
        shadows
        dpr={[1, 2]}
        gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping, toneMappingExposure: 1.2 }}
      >
        <PerspectiveCamera makeDefault position={[0, 0.3, 4.5]} fov={40} />

        {/* TRIBE v2-style lighting: warm key, cool fill, rim */}
        <ambientLight intensity={0.15} color="#1a1a2e" />
        <directionalLight position={[5, 5, 5]} intensity={1.2} color="#fff5ee" castShadow />
        <directionalLight position={[-3, 2, -4]} intensity={0.4} color="#334466" />
        <pointLight position={[0, -3, 2]} intensity={0.3} color="#FF4400" />
        <pointLight position={[-2, 1, -3]} intensity={0.2} color="#00A99D" />

        <Suspense fallback={
          <Html center>
            <div style={{ color: '#00A99D', fontFamily: 'monospace', fontSize: '10px', opacity: 0.6 }}>
              Loading cortical mesh...
            </div>
          </Html>
        }>
          <BrainMesh frame={frame} surfaceMode={surfaceMode} hemiMode={hemiMode} />
        </Suspense>

        <OrbitControls
          enableZoom={true}
          enablePan={false}
          autoRotate={false}
          minDistance={2.5}
          maxDistance={7}
          minPolarAngle={Math.PI / 5}
          maxPolarAngle={Math.PI / 1.3}
          makeDefault
        />
      </Canvas>

      {/* Bottom-left: model label */}
      <div className="absolute bottom-4 left-4 flex items-center gap-2.5 pointer-events-none">
        <div className="relative">
          <div className="w-2 h-2 rounded-full bg-[#FF4400] animate-ping absolute" style={{ animationDuration: '2s' }}></div>
          <div className="w-2 h-2 rounded-full bg-[#FF4400] relative"></div>
        </div>
        <span style={{ fontSize: '9px', fontWeight: 600, color: 'rgba(255,255,255,0.25)', textTransform: 'uppercase', letterSpacing: '0.2em', fontFamily: 'monospace' }}>
          fsaverage · TRIBE v2
        </span>
      </div>

      {/* Top-right: activation readout */}
      <div className="absolute top-4 right-4 text-right pointer-events-none">
        <div style={{ fontSize: '22px', fontWeight: 900, fontFamily: 'monospace', color: '#fff', letterSpacing: '-0.05em', fontVariantNumeric: 'tabular-nums' }}>
          {(frame.max_activation * 100).toFixed(1)}
          <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.3)', marginLeft: '2px' }}>%</span>
        </div>
        <div style={{ fontSize: '8px', fontWeight: 700, color: '#FF4400', textTransform: 'uppercase', letterSpacing: '0.15em', marginTop: '1px' }}>
          Cortical Activation
        </div>
      </div>

      {/* Color scale legend (TRIBE v2 Low → High bar) */}
      <div className="absolute bottom-4 right-4 pointer-events-none flex items-center gap-2">
        <span style={{ fontSize: '8px', color: 'rgba(255,255,255,0.3)', fontFamily: 'monospace' }}>Low</span>
        <div style={{
          width: '50px', height: '3px', borderRadius: '2px',
          background: 'linear-gradient(to right, #3a3a3e, #8B4513, #CC4400, #FF2200, #FFAA66)'
        }}></div>
        <span style={{ fontSize: '8px', color: 'rgba(255,255,255,0.3)', fontFamily: 'monospace' }}>High</span>
      </div>

      {/* Top-left: activity label */}
      <div className="absolute top-4 left-4 pointer-events-none">
        <span style={{ fontSize: '8px', fontWeight: 700, color: 'rgba(255,255,255,0.2)', textTransform: 'uppercase', letterSpacing: '0.2em', fontFamily: 'monospace' }}>
          Activity
        </span>
      </div>
    </div>
  )
}
