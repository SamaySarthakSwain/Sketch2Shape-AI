import React, { Suspense, useRef, useState, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Center, Grid } from '@react-three/drei';
import { useLoader } from '@react-three/fiber';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import {
  Maximize2,
  Minimize2,
  RotateCw,
  Layers,
  RefreshCw,
  Box,
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { ViewerErrorBoundary } from './ViewerErrorBoundary';

interface ModelMeshProps {
  url: string;
  wireframe: boolean;
  onLoaded?: (mesh: THREE.Object3D) => void;
}

const ModelMesh: React.FC<ModelMeshProps> = ({ url, wireframe, onLoaded }) => {
  const gltf = useLoader(GLTFLoader, url);
  const modelRef = useRef<THREE.Group>(null);

  useEffect(() => {
    if (gltf && gltf.scene) {
      gltf.scene.traverse((child) => {
        if ((child as THREE.Mesh).isMesh) {
          const mesh = child as THREE.Mesh;
          if (Array.isArray(mesh.material)) {
            mesh.material.forEach((m) => {
              m.wireframe = wireframe;
              m.needsUpdate = true;
            });
          } else if (mesh.material) {
            mesh.material.wireframe = wireframe;
            mesh.material.needsUpdate = true;
          }
        }
      });
      onLoaded?.(gltf.scene);
    }
  }, [gltf, wireframe, onLoaded]);

  return (
    <Center top>
      <primitive ref={modelRef} object={gltf.scene} scale={1.8} />
    </Center>
  );
};

export const ModelViewer3D: React.FC<{ modelUrl?: string }> = ({ modelUrl }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const controlsRef = useRef<any>(null);

  const {
    activeGlbUrl,
    refinedGlbUrl,
    pbrGlbUrl,
    wireframe,
    setWireframe,
    autoRotate,
    setAutoRotate,
  } = useAppStore();

  const [isFullscreen, setIsFullscreen] = useState(false);

  // Automatically pick best available 3D asset
  const resolvedUrl = modelUrl || pbrGlbUrl || refinedGlbUrl || activeGlbUrl;

  const handleResetCamera = () => {
    if (controlsRef.current) {
      controlsRef.current.object.position.set(2.5, 2.0, 3.5);
      controlsRef.current.target.set(0, 0.4, 0);
      controlsRef.current.update();
    }
  };

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(console.error);
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(console.error);
    }
  };

  return (
    <div
      ref={containerRef}
      className={`relative w-full rounded-2xl overflow-hidden border border-slate-800 bg-gradient-to-b from-slate-900/60 via-[#070b14] to-[#040711] flex flex-col transition-all ${
        isFullscreen ? 'h-screen fixed inset-0 z-50 rounded-none' : 'h-[440px]'
      }`}
    >
      {/* Sleek Floating Viewport Controls (Top Right) */}
      {resolvedUrl && (
        <div className="absolute top-3 right-3 z-10 flex items-center gap-1 p-1 rounded-xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-md">
          {/* Wireframe */}
          <button
            onClick={() => setWireframe(!wireframe)}
            className={`p-1.5 rounded-lg text-xs transition-colors ${
              wireframe ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
            title="Wireframe"
          >
            <Layers className="w-4 h-4" />
          </button>

          {/* Auto Rotate */}
          <button
            onClick={() => setAutoRotate(!autoRotate)}
            className={`p-1.5 rounded-lg text-xs transition-colors ${
              autoRotate ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
            title="Auto-Rotate"
          >
            <RotateCw className="w-4 h-4" />
          </button>

          {/* Reset Camera */}
          <button
            onClick={handleResetCamera}
            className="p-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            title="Reset View"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          {/* Fullscreen */}
          <button
            onClick={toggleFullscreen}
            className="p-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>
      )}

      {/* 3D Canvas */}
      {resolvedUrl ? (
        <ViewerErrorBoundary fallbackMessage="The 3D model could not be rendered.">
          <Canvas
            shadows
            camera={{ position: [2.5, 2.0, 3.5], fov: 45 }}
            className="w-full h-full cursor-grab active:cursor-grabbing"
          >
            {/* Studio Lighting */}
            <ambientLight intensity={0.9} />
            <directionalLight position={[5, 8, 5]} intensity={1.5} castShadow />
            <directionalLight position={[-5, 4, -4]} intensity={0.6} color="#90cdf4" />
            <pointLight position={[0, -2, 2]} intensity={0.4} />

            <Suspense
              fallback={
                <mesh>
                  <boxGeometry args={[0.5, 0.5, 0.5]} />
                  <meshStandardMaterial color="#3b82f6" wireframe />
                </mesh>
              }
            >
              <ModelMesh url={resolvedUrl} wireframe={wireframe} />
            </Suspense>

            <Grid
              position={[0, -0.01, 0]}
              infiniteGrid
              cellSize={0.2}
              sectionSize={1.0}
              sectionColor="#2563eb"
              cellColor="#1e293b"
              fadeDistance={25}
            />

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
          <div className="w-16 h-16 rounded-2xl bg-slate-900/60 border border-slate-800/80 flex items-center justify-center text-slate-500 mb-3 shadow-inner">
            <Box className="w-8 h-8 text-blue-500/70" />
          </div>
          <h4 className="text-sm font-semibold text-slate-300">Your 3D Model</h4>
          <p className="text-xs text-slate-500 max-w-xs mt-1">
            Draw, upload a sketch, or type a prompt, then click Generate 3D Model.
          </p>
        </div>
      )}
    </div>
  );
};
