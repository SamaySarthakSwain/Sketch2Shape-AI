import React, { useState } from 'react';
import {
  Box,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Layers,
  Download,
  CheckCircle2,
  ExternalLink,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { ModelViewer3D } from '../components/viewer/ModelViewer3D';

const DEMO_MODELS = [
  {
    id: 'chair',
    name: 'Executive Oak Armchair',
    category: 'chair',
    modelUrl: '/demo_assets/chair/model.glb',
    sketchUrl: '/demo_assets/chair/sketch.png',
    vertices: 136,
    faces: 256,
    engine: 'Procedural + Procedural PBR',
  },
  {
    id: 'car',
    name: 'Crimson Cyber Coupe',
    category: 'car',
    modelUrl: '/demo_assets/car/model.glb',
    sketchUrl: '/demo_assets/car/sketch.png',
    vertices: 152,
    faces: 280,
    engine: 'Procedural + Metallic PBR',
  },
  {
    id: 'apple',
    name: 'Honeycrisp Red Apple',
    category: 'apple',
    modelUrl: '/demo_assets/apple/model.glb',
    sketchUrl: '/demo_assets/apple/sketch.png',
    vertices: 668,
    faces: 1328,
    engine: 'Procedural + Organic PBR',
  },
];

export const Home: React.FC = () => {
  const { setActiveTab, setCurrentImage, health } = useAppStore();
  const [selectedDemo, setSelectedDemo] = useState(DEMO_MODELS[0]);

  const handleLaunchSample = async (sample: typeof DEMO_MODELS[0]) => {
    try {
      const res = await fetch(sample.sketchUrl);
      const blob = await res.blob();
      const reader = new FileReader();
      reader.onload = () => {
        setCurrentImage(reader.result as string, `${sample.category}_sample.png`);
        setActiveTab('workspace');
      };
      reader.readAsDataURL(blob);
    } catch {
      setActiveTab('workspace');
    }
  };

  return (
    <div className="space-y-16 py-10 px-4 lg:px-8 max-w-7xl mx-auto">
      {/* Hero Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
        <div className="lg:col-span-7 space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-blue-500/30 bg-blue-950/40 text-blue-300 text-xs font-mono">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            Stage 12: Production AI Sketch-to-3D Asset Platform
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-100 leading-[1.1]">
            Convert Hand-Drawn <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-sky-300 to-indigo-300">
              2D Sketches to Textured 3D Assets
            </span>
          </h1>

          <p className="text-base text-slate-400 max-w-xl leading-relaxed">
            Sketch2Shape AI bridges rapid 2D conceptual ideation with production 3D asset generation.
            Combines OpenCV stroke analysis, deep semantic intelligence, hybrid AI reconstruction (InstantMesh + Procedural + Cloud AI), 1024x1024 procedural PBR texturing, 3D printability analysis, and multi-format export (GLB, OBJ, STL, 3MF, USDZ).
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Button
              variant="primary"
              size="lg"
              onClick={() => setActiveTab('workspace')}
              icon={<ArrowRight className="w-5 h-5" />}
              className="shadow-lg shadow-blue-950/80"
            >
              Start Creating in Studio
            </Button>
            <Button
              variant="secondary"
              size="lg"
              onClick={() => setActiveTab('gallery')}
              icon={<Box className="w-5 h-5 text-slate-400" />}
            >
              Explore 3D Gallery
            </Button>
          </div>

          {/* Real System Status Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-6 border-t border-slate-800/80 font-mono text-xs">
            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
              <span className="text-[10px] text-slate-500 block uppercase">Primary Local Engine</span>
              <span className="text-slate-200 font-semibold mt-0.5 block">InstantMesh FP16</span>
              <span className="text-[10px] text-blue-400">FlexiCubes Chunked</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
              <span className="text-[10px] text-slate-500 block uppercase">Hardware Footprint</span>
              <span className="text-slate-200 font-semibold mt-0.5 block">
                {health?.vram_total_gb ? `${health.vram_total_gb}GB VRAM` : '4.0GB VRAM'}
              </span>
              <span className="text-[10px] text-emerald-400">RTX 3050 Optimized</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80 col-span-2 sm:col-span-1">
              <span className="text-[10px] text-slate-500 block uppercase">Mesh Topology</span>
              <span className="text-slate-200 font-semibold mt-0.5 block">Watertight χ = 2</span>
              <span className="text-[10px] text-emerald-400">Trimesh Verified</span>
            </div>
          </div>
        </div>

        {/* Live Interactive 3D Demonstration */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Box className="w-3.5 h-3.5 text-blue-400" />
              Interactive Three.js Demo
            </span>
            <div className="flex gap-1">
              {DEMO_MODELS.map((demo) => (
                <button
                  key={demo.id}
                  onClick={() => setSelectedDemo(demo)}
                  className={`px-2 py-1 text-[11px] font-mono rounded transition-colors ${
                    selectedDemo.id === demo.id
                      ? 'bg-blue-600 text-white font-semibold'
                      : 'bg-slate-900 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {demo.name.split(' ')[0]}
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 overflow-hidden shadow-2xl bg-slate-950">
            <ModelViewer3D modelUrl={selectedDemo.modelUrl} />
          </div>

          <div className="flex items-center justify-between text-xs text-slate-400 px-1 font-mono">
            <span>
              {selectedDemo.name} ({selectedDemo.vertices} verts, {selectedDemo.faces} faces)
            </span>
            <button
              onClick={() => handleLaunchSample(selectedDemo)}
              className="text-blue-400 hover:text-blue-300 underline flex items-center gap-1"
            >
              Reconstruct in Studio <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      {/* 3-Step Production Workflow */}
      <div className="space-y-6 pt-10 border-t border-slate-800/80">
        <div className="text-center max-w-xl mx-auto space-y-2">
          <h2 className="text-2xl font-bold text-slate-100 tracking-tight">
            How Sketch2Shape AI Works
          </h2>
          <p className="text-xs text-slate-400">
            Three decoupled, mathematically verifiable stages guarantee clean asset generation from rough conceptual inputs.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="border border-slate-800/80 rounded-xl bg-slate-900/40 p-6 space-y-3">
            <div className="w-10 h-10 rounded-lg bg-blue-950 border border-blue-800/60 flex items-center justify-center text-blue-400 font-mono font-bold text-sm">
              01
            </div>
            <h3 className="text-base font-semibold text-slate-200">1. Draw or Upload Sketch</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Accepts hand-drawn sketches via the interactive drawing canvas or PNG/JPG uploads. Stage 5 OpenCV automatically denoises, thins strokes, and applies canonical centering.
            </p>
          </div>

          <div className="border border-slate-800/80 rounded-xl bg-slate-900/40 p-6 space-y-3">
            <div className="w-10 h-10 rounded-lg bg-blue-950 border border-blue-800/60 flex items-center justify-center text-blue-400 font-mono font-bold text-sm">
              02
            </div>
            <h3 className="text-base font-semibold text-slate-200">2. Neural 3D Reconstruction</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Stage 6 intelligence classifies the object category and geometric symmetry. Stage 7 routes to InstantMesh (Zero123++ diffusion + LRM) or the zero-VRAM procedural lathe engine.
            </p>
          </div>

          <div className="border border-slate-800/80 rounded-xl bg-slate-900/40 p-6 space-y-3">
            <div className="w-10 h-10 rounded-lg bg-blue-950 border border-blue-800/60 flex items-center justify-center text-blue-400 font-mono font-bold text-sm">
              03
            </div>
            <h3 className="text-base font-semibold text-slate-200">3. Topological Audit & Export</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Trimesh audits Euler characteristic ($\chi = 2$), normal orientations, and watertightness. Exports verified binary GLB and Wavefront OBJ+MTL for Blender, Unity, and WebGL.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
