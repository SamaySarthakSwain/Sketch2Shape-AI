import React, { Suspense, useRef, useState, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Center, Grid, Environment } from '@react-three/drei';
import { useLoader } from '@react-three/fiber';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import {
  Maximize2,
  Minimize2,
  RotateCw,
  Grid as GridIcon,
  RefreshCw,
  Box,
  Layers,
  Sun,
  Palette,
  Compass,
  Sparkles,
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { ViewerErrorBoundary } from './ViewerErrorBoundary';

interface ModelMeshProps {
  url: string;
  wireframe: boolean;
  shadingMode: 'pbr' | 'solid' | 'wireframe' | 'normal';
  onLoaded?: (mesh: THREE.Object3D) => void;
}

const ModelMesh: React.FC<ModelMeshProps> = ({ url, wireframe, shadingMode, onLoaded }) => {
  const gltf = useLoader(GLTFLoader, url);
  const modelRef = useRef<THREE.Group>(null);
  const originalMaterials = useRef<Map<THREE.Mesh, THREE.Material | THREE.Material[]>>(new Map());

  // Store original materials on first load
  useEffect(() => {
    if (gltf && gltf.scene) {
      gltf.scene.traverse((child) => {
        if ((child as THREE.Mesh).isMesh) {
          const mesh = child as THREE.Mesh;
          if (!originalMaterials.current.has(mesh)) {
            originalMaterials.current.set(mesh, mesh.material);
          }
        }
      });
      onLoaded?.(gltf.scene);
    }
  }, [gltf, onLoaded]);

  // Apply shading mode & wireframe
  useEffect(() => {
    if (!gltf || !gltf.scene) return;

    gltf.scene.traverse((child) => {
      if ((child as THREE.Mesh).isMesh) {
        const mesh = child as THREE.Mesh;
        const orig = originalMaterials.current.get(mesh);

        if (shadingMode === 'solid') {
          mesh.material = new THREE.MeshStandardMaterial({
            color: 0xc4c9d4,
            roughness: 0.65,
            metalness: 0.05,
            wireframe: wireframe,
          });
        } else if (shadingMode === 'normal') {
          mesh.material = new THREE.MeshNormalMaterial({
            wireframe: wireframe,
          });
        } else {
          // PBR / Original textured mode
          if (orig) {
            mesh.material = orig;
            if (Array.isArray(mesh.material)) {
              mesh.material.forEach((m) => {
                m.wireframe = wireframe;
                m.needsUpdate = true;
              });
            } else {
              mesh.material.wireframe = wireframe;
              mesh.material.needsUpdate = true;
            }
          }
        }
      }
    });
  }, [gltf, wireframe, shadingMode]);

  return (
    <Center top>
      <primitive ref={modelRef} object={gltf.scene} scale={1.8} />
    </Center>
  );
};

// Dynamic lighting rigs based on active preset
const LightingRig: React.FC<{ preset: string }> = ({ preset }) => {
  if (preset === 'product') {
    return (
      <>
        <ambientLight intensity={0.8} />
        <spotLight position={[0, 12, 0]} intensity={2.2} angle={0.6} penumbra={0.8} castShadow />
        <directionalLight position={[4, 5, 4]} intensity={0.9} />
        <directionalLight position={[-4, 3, -4]} intensity={0.6} />
        <Environment preset="studio" />
      </>
    );
  } else if (preset === 'daylight') {
    return (
      <>
        <ambientLight intensity={0.6} color="#e0f2fe" />
        <directionalLight position={[12, 18, 8]} intensity={2.4} color="#fef08a" castShadow />
        <directionalLight position={[-8, 4, -8]} intensity={0.5} color="#bae6fd" />
        <Environment preset="sunset" />
      </>
    );
  } else if (preset === 'cinematic') {
    return (
      <>
        <ambientLight intensity={0.2} />
        <directionalLight position={[8, 6, 6]} intensity={2.8} color="#f97316" castShadow />
        <directionalLight position={[-8, 4, -6]} intensity={2.0} color="#06b6d4" />
        <pointLight position={[0, -2, 4]} intensity={0.8} color="#ec4899" />
        <Environment preset="night" />
      </>
    );
  } else if (preset === 'inspection') {
    return (
      <>
        <ambientLight intensity={1.1} />
        <directionalLight position={[10, 0, 0]} intensity={1.0} />
        <directionalLight position={[-10, 0, 0]} intensity={1.0} />
        <directionalLight position={[0, 10, 0]} intensity={1.0} />
        <directionalLight position={[0, -10, 0]} intensity={0.8} />
        <directionalLight position={[0, 0, 10]} intensity={1.0} />
      </>
    );
  }

  // Default: Studio Lighting
  return (
    <>
      <ambientLight intensity={0.6} />
      <directionalLight position={[6, 12, 8]} intensity={1.6} castShadow />
      <directionalLight position={[-6, 6, -6]} intensity={0.8} color="#93c5fd" />
      <directionalLight position={[0, -4, -6]} intensity={0.5} color="#fed7aa" />
      <Environment preset="city" />
    </>
  );
};

export const ModelViewer3D: React.FC<{ modelUrl?: string | null }> = ({ modelUrl }) => {
  const {
    activeGlbUrl,
    refinedGlbUrl,
    pbrGlbUrl,
    activeMeshVariant,
    setActiveMeshVariant,
    wireframe,
    setWireframe,
    showGrid,
    setShowGrid,
    autoRotate,
    setAutoRotate,
    lightingPreset,
    setLightingPreset,
    backgroundPreset,
    setBackgroundPreset,
    shadingMode,
    setShadingMode,
  } = useAppStore();

  const containerRef = useRef<HTMLDivElement>(null);
  const controlsRef = useRef<any>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showLightingMenu, setShowLightingMenu] = useState(false);
  const [showViewMenu, setShowViewMenu] = useState(false);
  const [showBackgroundMenu, setShowBackgroundMenu] = useState(false);

  // Active GLB resolution hierarchy: explicit modelUrl -> selected variant (pbr / refined / original)
  let resolvedUrl = modelUrl;
  if (!resolvedUrl) {
    if (activeMeshVariant === 'pbr' && pbrGlbUrl) {
      resolvedUrl = pbrGlbUrl;
    } else if (activeMeshVariant === 'refined' && refinedGlbUrl) {
      resolvedUrl = refinedGlbUrl;
    } else {
      resolvedUrl = pbrGlbUrl || refinedGlbUrl || activeGlbUrl;
    }
  }

  // Camera View Alignment Gizmo
  const setCameraView = (pos: [number, number, number]) => {
    if (controlsRef.current) {
      const controls = controlsRef.current;
      controls.object.position.set(pos[0], pos[1], pos[2]);
      controls.target.set(0, 0.4, 0);
      controls.update();
    }
    setShowViewMenu(false);
  };

  const handleResetCamera = () => {
    setCameraView([2.5, 2.0, 3.5]);
  };

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(console.error);
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(console.error);
    }
  };

  // Background styling mapping
  const bgStyles: Record<string, string> = {
    dark: 'bg-[#060a12]',
    white: 'bg-[#f8fafc]',
    gradient: 'bg-gradient-to-b from-slate-900 via-[#0b1329] to-[#040814]',
    transparent: 'bg-transparent',
  };

  return (
    <div
      ref={containerRef}
      className={`relative w-full rounded-xl overflow-hidden border border-slate-800 flex flex-col transition-all ${
        bgStyles[backgroundPreset] || 'bg-[#060a12]'
      } ${isFullscreen ? 'h-screen fixed inset-0 z-50 rounded-none' : 'h-[490px]'}`}
    >
      {/* Top Left: Mesh Variant Tabs (Original vs Refined vs PBR) */}
      <div className="absolute top-3 left-3 z-10 flex items-center gap-1 p-1 rounded-lg bg-slate-900/85 border border-slate-800/80 backdrop-blur-md">
        {pbrGlbUrl && (
          <button
            onClick={() => setActiveMeshVariant('pbr')}
            className={`px-2.5 py-1 rounded text-[11px] font-medium flex items-center gap-1 transition-colors ${
              activeMeshVariant === 'pbr'
                ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sparkles className="w-3 h-3" /> PBR Textured
          </button>
        )}
        {refinedGlbUrl && (
          <button
            onClick={() => setActiveMeshVariant('refined')}
            className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${
              activeMeshVariant === 'refined'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Refined Mesh
          </button>
        )}
        {activeGlbUrl && (
          <button
            onClick={() => setActiveMeshVariant('original')}
            className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${
              activeMeshVariant === 'original'
                ? 'bg-slate-700 text-white'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Base Geometry
          </button>
        )}
      </div>

      {/* Top Right: 3D Viewport Controls HUD */}
      <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5 p-1 rounded-lg bg-slate-900/85 border border-slate-800/80 backdrop-blur-md">
        {/* Shading Mode Toggle (PBR vs Solid Clay vs Normal Map) */}
        <div className="flex items-center bg-slate-950/60 rounded p-0.5 border border-slate-800 text-[10px]">
          <button
            onClick={() => setShadingMode('pbr')}
            className={`px-2 py-0.5 rounded transition-colors ${
              shadingMode === 'pbr' ? 'bg-amber-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
            title="PBR Material Mode"
          >
            PBR
          </button>
          <button
            onClick={() => setShadingMode('solid')}
            className={`px-2 py-0.5 rounded transition-colors ${
              shadingMode === 'solid' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
            title="Solid Studio Clay"
          >
            Clay
          </button>
          <button
            onClick={() => setShadingMode('normal')}
            className={`px-2 py-0.5 rounded transition-colors ${
              shadingMode === 'normal' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
            title="Normal Map Visualizer"
          >
            Normals
          </button>
        </div>

        {/* Wireframe Toggle */}
        <button
          onClick={() => setWireframe(!wireframe)}
          className={`p-1.5 rounded text-xs transition-colors ${
            wireframe ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
          title="Toggle Wireframe Overlay"
        >
          <Layers className="w-4 h-4" />
        </button>

        {/* View Alignment Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowViewMenu(!showViewMenu)}
            className="p-1.5 rounded text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            title="Camera Perspective Gizmo"
          >
            <Compass className="w-4 h-4" />
          </button>
          {showViewMenu && (
            <div className="absolute right-0 mt-1 w-28 bg-slate-900 border border-slate-800 rounded-lg shadow-xl py-1 z-30 text-xs">
              <button onClick={() => setCameraView([0, 0.4, 4.0])} className="w-full text-left px-3 py-1 hover:bg-slate-800 text-slate-300">Front View</button>
              <button onClick={() => setCameraView([0, 0.4, -4.0])} className="w-full text-left px-3 py-1 hover:bg-slate-800 text-slate-300">Back View</button>
              <button onClick={() => setCameraView([-4.0, 0.4, 0])} className="w-full text-left px-3 py-1 hover:bg-slate-800 text-slate-300">Left View</button>
              <button onClick={() => setCameraView([4.0, 0.4, 0])} className="w-full text-left px-3 py-1 hover:bg-slate-800 text-slate-300">Right View</button>
              <button onClick={() => setCameraView([0.001, 4.5, 0])} className="w-full text-left px-3 py-1 hover:bg-slate-800 text-slate-300">Top View</button>
              <button onClick={() => setCameraView([2.5, 2.0, 3.5])} className="w-full text-left px-3 py-1 hover:bg-slate-800 text-blue-400 font-medium">Isometric</button>
            </div>
          )}
        </div>

        {/* Lighting Rig Selector */}
        <div className="relative">
          <button
            onClick={() => setShowLightingMenu(!showLightingMenu)}
            className="p-1.5 rounded text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            title="Lighting Presets"
          >
            <Sun className="w-4 h-4" />
          </button>
          {showLightingMenu && (
            <div className="absolute right-0 mt-1 w-36 bg-slate-900 border border-slate-800 rounded-lg shadow-xl py-1 z-30 text-xs">
              {['studio', 'product', 'daylight', 'cinematic', 'inspection'].map((preset) => (
                <button
                  key={preset}
                  onClick={() => {
                    setLightingPreset(preset as any);
                    setShowLightingMenu(false);
                  }}
                  className={`w-full text-left px-3 py-1 hover:bg-slate-800 capitalize ${
                    lightingPreset === preset ? 'text-blue-400 font-semibold' : 'text-slate-300'
                  }`}
                >
                  {preset}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Background Selector */}
        <div className="relative">
          <button
            onClick={() => setShowBackgroundMenu(!showBackgroundMenu)}
            className="p-1.5 rounded text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            title="Background Theme"
          >
            <Palette className="w-4 h-4" />
          </button>
          {showBackgroundMenu && (
            <div className="absolute right-0 mt-1 w-32 bg-slate-900 border border-slate-800 rounded-lg shadow-xl py-1 z-30 text-xs">
              {['dark', 'white', 'gradient', 'transparent'].map((bg) => (
                <button
                  key={bg}
                  onClick={() => {
                    setBackgroundPreset(bg as any);
                    setShowBackgroundMenu(false);
                  }}
                  className={`w-full text-left px-3 py-1 hover:bg-slate-800 capitalize ${
                    backgroundPreset === bg ? 'text-blue-400 font-semibold' : 'text-slate-300'
                  }`}
                >
                  {bg} Studio
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Ground Grid Toggle */}
        <button
          onClick={() => setShowGrid(!showGrid)}
          className={`p-1.5 rounded text-xs transition-colors ${
            showGrid ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
          title="Toggle Ground Grid"
        >
          <GridIcon className="w-4 h-4" />
        </button>

        {/* Turntable Auto-Rotate Toggle */}
        <button
          onClick={() => setAutoRotate(!autoRotate)}
          className={`p-1.5 rounded text-xs transition-colors ${
            autoRotate ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
          title="Toggle Turntable Rotation"
        >
          <RotateCw className="w-4 h-4" />
        </button>

        <div className="w-[1px] h-4 bg-slate-800 mx-0.5" />

        {/* Reset Camera */}
        <button
          onClick={handleResetCamera}
          className="p-1.5 rounded text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          title="Reset Camera Position"
        >
          <RefreshCw className="w-4 h-4" />
        </button>

        {/* Fullscreen Mode */}
        <button
          onClick={toggleFullscreen}
          className="p-1.5 rounded text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen View'}
        >
          {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
        </button>
      </div>

      {/* Viewport Info Watermark */}
      <div className="absolute bottom-3 left-3 z-10 pointer-events-none flex items-center gap-2">
        <div className="px-2.5 py-1 rounded bg-slate-900/70 border border-slate-800/70 text-[10px] font-mono text-slate-400 backdrop-blur-sm">
          WebGL • Three.js Studio • {lightingPreset.toUpperCase()} RIG
        </div>
      </div>

      {/* 3D Canvas */}
      {resolvedUrl ? (
        <ViewerErrorBoundary fallbackMessage="The 3D GLB file could not be rendered in Three.js.">
          <Canvas
            shadows
            camera={{ position: [2.5, 2.0, 3.5], fov: 45 }}
            className="w-full h-full cursor-grab active:cursor-grabbing"
          >
            <LightingRig preset={lightingPreset} />

            <Suspense
              fallback={
                <mesh>
                  <boxGeometry args={[0.5, 0.5, 0.5]} />
                  <meshStandardMaterial color="#3b82f6" wireframe />
                </mesh>
              }
            >
              <ModelMesh
                url={resolvedUrl}
                wireframe={wireframe}
                shadingMode={shadingMode}
              />
            </Suspense>

            {showGrid && (
              <Grid
                position={[0, -0.01, 0]}
                infiniteGrid
                cellSize={0.2}
                sectionSize={1.0}
                sectionColor={backgroundPreset === 'white' ? '#94a3b8' : '#2563eb'}
                cellColor={backgroundPreset === 'white' ? '#cbd5e1' : '#1e293b'}
                fadeDistance={25}
              />
            )}

            <OrbitControls
              ref={controlsRef}
              makeDefault
              autoRotate={autoRotate}
              autoRotateSpeed={1.5}
              enableDamping
              dampingFactor={0.05}
              minDistance={0.5}
              maxDistance={25}
            />
          </Canvas>
        </ViewerErrorBoundary>
      ) : (
        <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center text-slate-500">
          <div className="w-16 h-16 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-600 mb-3 shadow-inner">
            <Box className="w-8 h-8 text-blue-500/60 animate-pulse" />
          </div>
          <h4 className="text-sm font-semibold text-slate-300">No 3D Model Active</h4>
          <p className="text-xs text-slate-500 max-w-sm mt-1">
            Draw or upload a 2D sketch on the left and click "Generate 3D Asset" to inspect textured models in the studio.
          </p>
        </div>
      )}
    </div>
  );
};
