import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import {
  Download,
  RotateCw,
  Maximize2,
  Palette,
  ShieldCheck,
  Box,
  Layers,
  Sparkles
} from 'lucide-react';

export default function Viewer3D({
  modelData,
  onOpenMeshDetails,
  isGenerating
}) {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const cameraRef = useRef(null);
  const controlsRef = useRef(null);
  const currentMeshRef = useRef(null);
  const animationFrameId = useRef(null);

  const [materialMode, setMaterialMode] = useState('clay'); // 'clay', 'metallic', 'normal'
  const [wireframe, setWireframe] = useState(false);
  const [autoRotate, setAutoRotate] = useState(true);
  const [loadingModel, setLoadingModel] = useState(false);

  // Initialize Three.js Scene
  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // Dimensions
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0b0f19);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(2.5, 2.0, 3.2);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    rendererRef.current = renderer;
    container.appendChild(renderer.domElement);

    // Orbit Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.autoRotate = autoRotate;
    controls.autoRotateSpeed = 2.0;
    controlsRef.current = controls;

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xffffff, 1.4);
    keyLight.position.set(5, 8, 5);
    keyLight.castShadow = true;
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0x38bdf8, 0.8);
    fillLight.position.set(-5, 3, -5);
    scene.add(fillLight);

    const rimLight = new THREE.DirectionalLight(0x818cf8, 0.6);
    rimLight.position.set(0, -5, -3);
    scene.add(rimLight);

    // Floor Grid Helper
    const grid = new THREE.GridHelper(6, 20, 0x1e293b, 0x0f172a);
    grid.position.y = -1.0;
    scene.add(grid);

    // Animation Loop
    const animate = () => {
      animationFrameId.current = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // Handle Resize
    const handleResize = () => {
      if (!container || !renderer || !camera) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId.current);
      renderer.dispose();
      if (container && renderer.domElement) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  // Update Auto-Rotate
  useEffect(() => {
    if (controlsRef.current) {
      controlsRef.current.autoRotate = autoRotate;
    }
  }, [autoRotate]);

  // Load Model when modelData updates
  useEffect(() => {
    if (!modelData?.downloads?.glb || !sceneRef.current) return;

    setLoadingModel(true);
    const loader = new GLTFLoader();
    const apiHost = window.location.port === '5173' ? '' : 'http://127.0.0.1:8000';
    const url = `${apiHost}${modelData.downloads.glb}`;

    loader.load(
      url,
      (gltf) => {
        // Remove previous model
        if (currentMeshRef.current) {
          sceneRef.current.remove(currentMeshRef.current);
        }

        const model = gltf.scene;
        // Center model geometry
        const box = new THREE.Box3().setFromObject(model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = 2.0 / (maxDim || 1);

        model.scale.setScalar(scale);
        model.position.sub(center.multiplyScalar(scale));

        // Traverse and apply initial material
        applyMaterialToModel(model, materialMode, wireframe);

        sceneRef.current.add(model);
        currentMeshRef.current = model;
        setLoadingModel(false);
      },
      undefined,
      (error) => {
        console.error('Error loading GLB into Three.js:', error);
        setLoadingModel(false);
      }
    );
  }, [modelData]);

  // Apply Material Changes
  useEffect(() => {
    if (currentMeshRef.current) {
      applyMaterialToModel(currentMeshRef.current, materialMode, wireframe);
    }
  }, [materialMode, wireframe]);

  const applyMaterialToModel = (root, mode, isWireframe) => {
    root.traverse((child) => {
      if (child.isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;

        if (mode === 'normal') {
          child.material = new THREE.MeshNormalMaterial({ wireframe: isWireframe });
        } else if (mode === 'metallic') {
          child.material = new THREE.MeshStandardMaterial({
            color: 0x94a3b8,
            metalness: 0.95,
            roughness: 0.15,
            wireframe: isWireframe
          });
        } else {
          // Clay mode
          child.material = new THREE.MeshStandardMaterial({
            color: 0xf1f5f9,
            metalness: 0.05,
            roughness: 0.45,
            wireframe: isWireframe
          });
        }
        child.material.needsUpdate = true;
      }
    });
  };

  const resetCamera = () => {
    if (cameraRef.current && controlsRef.current) {
      cameraRef.current.position.set(2.5, 2.0, 3.2);
      controlsRef.current.target.set(0, 0, 0);
      controlsRef.current.update();
    }
  };

  const handleDownload = (format) => {
    if (!modelData?.downloads?.[format]) return;
    const apiHost = window.location.port === '5173' ? '' : 'http://127.0.0.1:8000';
    const link = document.createElement('a');
    link.href = `${apiHost}${modelData.downloads[format]}`;
    link.download = `sketch2shape_${modelData.model_id}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl flex flex-col h-full overflow-hidden shadow-xl relative">
      {/* Viewport Top Header */}
      <div className="bg-slate-950/80 px-4 py-2.5 border-b border-slate-800/80 flex items-center justify-between z-10">
        <div className="flex items-center gap-2">
          <Box className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Interactive 3D Viewport
          </span>
          {modelData && (
            <span className="text-[10px] font-mono bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full border border-slate-700">
              ID: {modelData.model_id}
            </span>
          )}
        </div>

        {/* Viewport Actions */}
        <div className="flex items-center gap-1.5">
          {/* Material Mode Dropdown */}
          <select
            value={materialMode}
            onChange={(e) => setMaterialMode(e.target.value)}
            className="bg-slate-900 text-xs text-slate-300 border border-slate-700 rounded-lg px-2 py-1 outline-none"
          >
            <option value="clay">Studio Clay</option>
            <option value="metallic">Cyber Metal</option>
            <option value="normal">Surface Normals</option>
          </select>

          {/* Wireframe Toggle */}
          <button
            onClick={() => setWireframe(!wireframe)}
            className={`p-1.5 rounded-lg border text-xs transition-colors ${
              wireframe
                ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-300'
                : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
            title="Toggle Wireframe"
          >
            <Layers className="w-3.5 h-3.5" />
          </button>

          {/* Auto Rotate Toggle */}
          <button
            onClick={() => setAutoRotate(!autoRotate)}
            className={`p-1.5 rounded-lg border text-xs transition-colors ${
              autoRotate
                ? 'bg-indigo-500/20 border-indigo-500/50 text-indigo-300'
                : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
            title="Toggle Auto Rotation"
          >
            <RotateCw className="w-3.5 h-3.5" />
          </button>

          {/* Reset Camera */}
          <button
            onClick={resetCamera}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-400 hover:text-slate-200"
            title="Reset View"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Three.js Canvas Container */}
      <div ref={mountRef} className="flex-1 w-full relative min-h-[380px]">
        {/* Loading / Generating Overlay */}
        {(isGenerating || loadingModel) && (
          <div className="absolute inset-0 bg-slate-950/70 backdrop-blur-sm flex flex-col items-center justify-center gap-3 z-20">
            <div className="w-12 h-12 rounded-full border-4 border-cyan-500/30 border-t-cyan-400 animate-spin" />
            <p className="text-sm font-medium text-slate-200">
              {isGenerating ? 'Synthesizing 3D Geometry...' : 'Rendering 3D Model...'}
            </p>
          </div>
        )}

        {/* Empty Placeholder if no model generated yet */}
        {!modelData && !isGenerating && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-6 text-slate-500 pointer-events-none">
            <Sparkles className="w-10 h-10 mb-2 opacity-30 text-indigo-400 animate-pulse" />
            <p className="text-sm font-medium text-slate-400">3D Workspace Ready</p>
            <p className="text-xs text-slate-600 max-w-xs mt-1">
              Draw your sketch on the canvas and click "Reconstruct 3D Model" to generate and inspect a watertight 3D mesh.
            </p>
          </div>
        )}
      </div>

      {/* Bottom Export & Validation Toolbar */}
      {modelData && (
        <div className="bg-slate-950/90 border-t border-slate-800 p-3 flex items-center justify-between flex-wrap gap-2 z-10">
          {/* Mesh Health Badge */}
          <button
            onClick={onOpenMeshDetails}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700/80 hover:border-slate-600 transition-colors text-xs"
          >
            <ShieldCheck className={`w-4 h-4 ${modelData.validation?.is_watertight ? 'text-emerald-400' : 'text-amber-400'}`} />
            <span className="text-slate-300 font-medium">
              {modelData.validation?.is_watertight ? 'Watertight Manifold' : 'Mesh Repaired'}
            </span>
            <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded font-mono">
              Score: {modelData.validation?.health_score}/100
            </span>
          </button>

          {/* 1-Click Multi-Format Export Buttons */}
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => handleDownload('glb')}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs transition-colors shadow-sm"
              title="Download Binary glTF (.glb) for Web / AR / Three.js"
            >
              <Download className="w-3.5 h-3.5" />
              <span>GLB</span>
            </button>
            <button
              onClick={() => handleDownload('obj')}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs transition-colors"
              title="Download Wavefront OBJ for Blender / Maya"
            >
              <Download className="w-3.5 h-3.5" />
              <span>OBJ</span>
            </button>
            <button
              onClick={() => handleDownload('stl')}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs transition-colors"
              title="Download STL for 3D Printing / Slicers"
            >
              <Download className="w-3.5 h-3.5" />
              <span>STL</span>
            </button>
            <button
              onClick={() => handleDownload('ply')}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs transition-colors"
              title="Download Polygon File Format (.ply)"
            >
              <Download className="w-3.5 h-3.5" />
              <span>PLY</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
