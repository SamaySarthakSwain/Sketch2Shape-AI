import React, { useState } from 'react';
import { Layers, Download, Sparkles } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { ModelViewer3D } from '../components/viewer/ModelViewer3D';
import { triggerFileDownload } from '../services/downloads';

const GALLERY_MODELS = [
  {
    id: 'car',
    title: 'Crimson Sports Car',
    category: 'car',
    glbUrl: '/demo_assets/car/model.glb',
    sketchUrl: '/demo_assets/car/sketch.png',
  },
  {
    id: 'chair',
    title: 'Oak Armchair',
    category: 'chair',
    glbUrl: '/demo_assets/chair/model.glb',
    sketchUrl: '/demo_assets/chair/sketch.png',
  },
  {
    id: 'apple',
    title: 'Honeycrisp Apple',
    category: 'apple',
    glbUrl: '/demo_assets/apple/model.glb',
    sketchUrl: '/demo_assets/apple/sketch.png',
  },
  {
    id: 'airplane',
    title: 'Supersonic Jet',
    category: 'airplane',
    glbUrl: '/models/instantmesh_quickdraw_airplane_normalized.glb',
    sketchUrl: '/examples/quickdraw_airplane_normalized.png',
  },
];

export const Gallery: React.FC = () => {
  const { setCurrentMeshResult, setActiveTab, setPbrGlbUrl } = useAppStore();
  const [selected, setSelected] = useState(GALLERY_MODELS[0]);

  const handleOpenInStudio = (item: typeof GALLERY_MODELS[0]) => {
    setPbrGlbUrl(item.glbUrl);
    setCurrentMeshResult(
      {
        job_id: item.id,
        status: 'completed',
        model_used: 'PBR Engine',
        downloads: { glb: item.glbUrl },
      },
      item.glbUrl
    );
    setActiveTab('workspace');
  };

  return (
    <div className="py-6 px-4 lg:px-8 max-w-6xl mx-auto space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Layers className="w-5 h-5 text-blue-500" />
          Model Gallery
        </h1>
        <p className="text-xs text-slate-400">
          Explore textured 3D models generated from sketches and prompts.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: Model List */}
        <div className="lg:col-span-5 space-y-2">
          {GALLERY_MODELS.map((item) => (
            <div
              key={item.id}
              onClick={() => setSelected(item)}
              className={`p-3 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${
                selected.id === item.id
                  ? 'border-blue-500/80 bg-blue-950/20 shadow-md'
                  : 'border-slate-800 bg-slate-900/40 hover:bg-slate-800/40'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-lg bg-white p-1 flex items-center justify-center overflow-hidden">
                  <img src={item.sketchUrl} alt={item.title} className="max-h-full max-w-full object-contain" />
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-white">{item.title}</h3>
                  <span className="text-[11px] text-slate-400 capitalize">{item.category}</span>
                </div>
              </div>

              <div className="flex items-center gap-1.5">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleOpenInStudio(item);
                  }}
                  className="px-2.5 py-1 text-xs font-medium rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors"
                >
                  Open in Studio
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Right: 3D Preview */}
        <div className="lg:col-span-7 space-y-3">
          <ModelViewer3D modelUrl={selected.glbUrl} />
          <div className="flex justify-end">
            <button
              onClick={() => triggerFileDownload(selected.glbUrl, `${selected.id}.glb`)}
              className="py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white flex items-center gap-2 shadow-lg shadow-blue-900/20 transition-all"
            >
              <Download className="w-4 h-4" /> Download .GLB
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
