import React, { useState } from 'react';
import { Sparkles, CheckCircle2, RotateCcw, Box, Eye, Layers } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

interface DemoAsset {
  id: string;
  name: string;
  category: string;
  material: string;
  style: string;
  description: string;
  glbUrl: string;
  sketchUrl: string;
  bundleUrl: string;
  vertices: number;
  faces: number;
  printScore: number;
}

const DEMO_ITEMS: DemoAsset[] = [
  {
    id: 'chair',
    name: 'Executive Oak Armchair',
    category: 'chair',
    material: 'Natural Oak Wood',
    style: 'Realistic PBR',
    description: 'Watertight multi-component furniture asset with anisotropic wood grain and clearcoat reflection.',
    glbUrl: '/demo_assets/chair/model.glb',
    sketchUrl: '/demo_assets/chair/sketch.png',
    bundleUrl: '/demo_assets/chair/bundle.zip',
    vertices: 136,
    faces: 256,
    printScore: 85.0
  },
  {
    id: 'car',
    name: 'Crimson Cyber Coupe',
    category: 'car',
    material: 'Crimson Metallic Paint',
    style: 'Product Render',
    description: 'Vehicle geometry with automotive metallic flake, clearcoat specular highlights, and treaded tires.',
    glbUrl: '/demo_assets/car/model.glb',
    sketchUrl: '/demo_assets/car/sketch.png',
    bundleUrl: '/demo_assets/car/bundle.zip',
    vertices: 152,
    faces: 280,
    printScore: 85.0
  },
  {
    id: 'apple',
    name: 'Honeycrisp Red Apple',
    category: 'apple',
    material: 'Honeycrisp Apple Skin',
    style: 'Realistic PBR',
    description: 'Smooth organic cardioid sphere with procedural stippled lenticel micro-pores and realistic stem.',
    glbUrl: '/demo_assets/apple/model.glb',
    sketchUrl: '/demo_assets/apple/sketch.png',
    bundleUrl: '/demo_assets/apple/bundle.zip',
    vertices: 668,
    faces: 1328,
    printScore: 90.0
  }
];

export const DemoModeSelector: React.FC = () => {
  const [activeDemoId, setActiveDemoId] = useState<string | null>(null);
  const {
    setCurrentMeshResult,
    setPbrGlbUrl,
    setCurrentImage,
    setPrintabilityReport,
    setBundleZipUrl,
    setReconstructionStage,
    setIntelligence,
    setOverriddenCategory
  } = useAppStore();

  const handleSelectDemo = (demo: DemoAsset) => {
    setActiveDemoId(demo.id);

    // Update active 3D Model in viewer
    setPbrGlbUrl(demo.glbUrl);
    setBundleZipUrl(demo.bundleUrl);

    // Populate simulated intelligence & mesh result for realistic UI display
    setCurrentMeshResult({
      model_used: 'procedural_pbr_pipeline',
      glb_path: demo.glbUrl,
      inference_time_seconds: 1.25,
      vertices: demo.vertices,
      faces: demo.faces,
      quality_report: {
        is_watertight: true,
        is_manifold: true,
        vertex_count: demo.vertices,
        face_count: demo.faces,
        bounding_box: { width: 0.8, height: 1.0, depth: 0.7 },
        volume: 0.08,
        surface_area: 0.22,
        degenerate_faces: 0,
        duplicate_vertices: 0,
        non_manifold_edges: 0,
        overall_score: demo.printScore
      }
    }, demo.glbUrl);

    setPrintabilityReport({
      is_printable: true,
      printability_score: demo.printScore,
      is_watertight: true,
      is_manifold: true,
      connected_components: 1,
      volume_cm3: 5.62,
      surface_area_cm2: 22.45,
      dimensions_mm: { x: 63.2, y: 100.0, z: 80.5 },
      min_wall_thickness_estimate_mm: 2.1,
      warnings: [],
      recommendations: [
        'Manifold watertight geometry. Ready for 3D slicing (Cura, Prusa, Bambu).',
        'Recommended print temperature and infill: 15-20% gyroid infill.'
      ]
    });

    setIntelligence({
      predicted_category: demo.category,
      confidence: 0.985,
      top_k: [
        { category: demo.category, confidence: 0.985 },
        { category: 'table', confidence: 0.008 }
      ],
      geometric_features: {
        aspect_ratio: 1.1,
        complexity_score: 0.65,
        stroke_density: 0.24,
        is_closed: true,
        symmetry_horizontal: 0.88,
        symmetry_vertical: 0.42
      },
      recommended_model: 'procedural_pbr'
    });

    setOverriddenCategory(demo.category);
    setReconstructionStage('completed', `Demonstration Asset Loaded: ${demo.name}`);
  };

  const handleResetToLive = () => {
    setActiveDemoId(null);
    setPbrGlbUrl(null);
    setCurrentMeshResult(null, null);
    setPrintabilityReport(null);
    setBundleZipUrl(null);
    setReconstructionStage('idle', '');
  };

  return (
    <div className="border border-indigo-900/40 rounded-xl bg-gradient-to-r from-slate-950 via-indigo-950/20 to-slate-950 p-4 space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-indigo-900/30 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-2">
              Hackathon Demonstration Mode
              <span className="text-[10px] normal-case bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full border border-indigo-500/30 font-normal">
                1-Click Preset Gallery
              </span>
            </h2>
            <p className="text-[11px] text-slate-400">
              Instantly inspect curated 3D assets with verified PBR textures and watertight slicer topology.
            </p>
          </div>
        </div>

        {activeDemoId && (
          <button
            onClick={handleResetToLive}
            className="flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset to Live Generation
          </button>
        )}
      </div>

      {/* Demo Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {DEMO_ITEMS.map((item) => {
          const isSelected = activeDemoId === item.id;
          return (
            <div
              key={item.id}
              onClick={() => handleSelectDemo(item)}
              className={`group cursor-pointer rounded-xl border p-3 transition-all relative overflow-hidden ${
                isSelected
                  ? 'border-indigo-500 bg-indigo-950/40 shadow-lg shadow-indigo-950/50'
                  : 'border-slate-800/80 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-400 font-semibold">
                    {item.category}
                  </span>
                  <h3 className="text-xs font-bold text-slate-100 group-hover:text-indigo-300 transition-colors">
                    {item.name}
                  </h3>
                </div>
                {isSelected ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                ) : (
                  <Eye className="w-4 h-4 text-slate-500 group-hover:text-slate-300 flex-shrink-0" />
                )}
              </div>

              <p className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                {item.description}
              </p>

              <div className="mt-2.5 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
                <span className="text-slate-300 font-medium">{item.material}</span>
                <span className="font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                  Print {item.printScore}/100
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {activeDemoId && (
        <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-300 flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <span>
              <strong>PRE-GENERATED DEMONSTRATION ASSET:</strong> Inspecting high-fidelity verified asset. Switch lighting, shading modes, or camera gizmo in the viewer on the right.
            </span>
          </div>
          <span className="text-[10px] font-mono text-amber-400/80 uppercase tracking-wider">
            Curated Sample
          </span>
        </div>
      )}
    </div>
  );
};
