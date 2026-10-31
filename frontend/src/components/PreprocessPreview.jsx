import React from 'react';
import { Layers, Activity, Compass, Cpu, FileText } from 'lucide-react';

export default function PreprocessPreview({ processedData }) {
  if (!processedData) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 text-center text-slate-500 text-xs flex flex-col items-center justify-center min-h-[140px]">
        <Layers className="w-8 h-8 mb-2 opacity-40 text-cyan-400" />
        <p>Draw a sketch on the canvas to trigger real-time OpenCV preprocessing and feature analysis.</p>
      </div>
    );
  }

  const { cleaned_image_b64, depth_map_b64, normal_map_b64, stroke_density, intelligence } = processedData;
  const classification = intelligence?.classification;
  const symmetry = intelligence?.symmetry;
  const geometry = intelligence?.geometry;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col gap-4 shadow-xl">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
          <Layers className="w-4 h-4 text-cyan-400" />
          <span>OpenCV Preprocessing & Intelligence</span>
        </h3>
        {classification && (
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-semibold">
            {classification.category} ({Math.round(classification.confidence * 100)}%)
          </span>
        )}
      </div>

      {/* 3 Processed Visual Passes */}
      <div className="grid grid-cols-3 gap-2.5">
        <div className="flex flex-col items-center gap-1">
          <div className="aspect-square w-full rounded-xl overflow-hidden border border-slate-800 bg-white">
            <img src={cleaned_image_b64} alt="Cleaned" className="w-full h-full object-contain" />
          </div>
          <span className="text-[10px] text-slate-400 font-medium">Clean Silhouette</span>
        </div>

        <div className="flex flex-col items-center gap-1">
          <div className="aspect-square w-full rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
            <img src={depth_map_b64} alt="Depth Map" className="w-full h-full object-contain" />
          </div>
          <span className="text-[10px] text-slate-400 font-medium">Pseudo-Depth</span>
        </div>

        <div className="flex flex-col items-center gap-1">
          <div className="aspect-square w-full rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
            <img src={normal_map_b64} alt="Normal Map" className="w-full h-full object-contain" />
          </div>
          <span className="text-[10px] text-slate-400 font-medium">Surface Normals</span>
        </div>
      </div>

      {/* Intelligence Metrics */}
      <div className="grid grid-cols-2 gap-2 bg-slate-950/70 p-3 rounded-xl border border-slate-800/80 text-xs">
        <div>
          <span className="text-[10px] text-slate-400 block">Vertical Symmetry:</span>
          <span className="text-slate-200 font-mono font-medium">
            {symmetry ? `${(symmetry.vertical_symmetry * 100).toFixed(1)}%` : '--'}
          </span>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 block">Aspect Ratio:</span>
          <span className="text-slate-200 font-mono font-medium">
            {geometry ? geometry.aspect_ratio : '--'}
          </span>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 block">Solidity / Hull:</span>
          <span className="text-slate-200 font-mono font-medium">
            {geometry ? `${(geometry.solidity * 100).toFixed(1)}%` : '--'}
          </span>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 block">Recommended Mode:</span>
          <span className="text-cyan-400 font-mono font-medium text-[11px] truncate block">
            {intelligence?.recommended_3d_mode || 'rotational'}
          </span>
        </div>
      </div>

      {/* Synthesized Prompt */}
      {intelligence?.synthesis_prompt && (
        <div className="bg-slate-950/50 p-2.5 rounded-xl border border-slate-800 text-[11px]">
          <span className="text-[10px] text-slate-500 font-semibold uppercase block mb-0.5">Synthesized 3D Prompt:</span>
          <p className="text-slate-300 italic">"{intelligence.synthesis_prompt}"</p>
        </div>
      )}
    </div>
  );
}
