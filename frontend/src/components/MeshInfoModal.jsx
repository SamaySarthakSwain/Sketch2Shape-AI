import React from 'react';
import { X, CheckCircle, AlertTriangle, ShieldCheck, Box, Ruler, Activity } from 'lucide-react';

export default function MeshInfoModal({ validation, onClose }) {
  if (!validation) return null;

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-md w-full p-6 shadow-2xl relative flex flex-col gap-4">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-bold text-slate-100">Mesh Topology & Health</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Health Score Banner */}
        <div className="flex items-center justify-between p-4 rounded-2xl bg-slate-950 border border-slate-800">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-bold text-lg font-mono ${
              validation.health_score >= 80 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
            }`}>
              {validation.health_score}
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-200">
                {validation.is_watertight ? 'Certified Watertight Manifold' : 'Mesh Topology Repaired'}
              </h4>
              <p className="text-xs text-slate-400">
                {validation.is_valid_for_3d_print
                  ? 'Ready for direct 3D printing (STL/OBJ)'
                  : 'Requires slicer auto-fix for printing'}
              </p>
            </div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
            <span className="text-slate-500 text-[11px] block">Triangular Faces</span>
            <span className="text-slate-200 font-mono font-bold text-sm">
              {validation.face_count.toLocaleString()}
            </span>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
            <span className="text-slate-500 text-[11px] block">Vertices</span>
            <span className="text-slate-200 font-mono font-bold text-sm">
              {validation.vertex_count.toLocaleString()}
            </span>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
            <span className="text-slate-500 text-[11px] block">Euler Characteristic (χ)</span>
            <span className="text-cyan-400 font-mono font-bold text-sm">
              {validation.euler_characteristic} {validation.euler_characteristic === 2 ? '(Genus 0)' : ''}
            </span>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
            <span className="text-slate-500 text-[11px] block">Surface Area</span>
            <span className="text-slate-200 font-mono font-bold text-sm">
              {validation.surface_area} units²
            </span>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
            <span className="text-slate-500 text-[11px] block">Enclosed Volume</span>
            <span className="text-slate-200 font-mono font-bold text-sm">
              {validation.volume} units³
            </span>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
            <span className="text-slate-500 text-[11px] block">Degenerate Triangles</span>
            <span className="text-emerald-400 font-mono font-bold text-sm">
              {validation.degenerate_faces} (Clean)
            </span>
          </div>
        </div>

        {/* Bounding Extents */}
        {validation.bounds && (
          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 text-xs">
            <span className="text-slate-500 text-[11px] block mb-1">Dimensions (X, Y, Z extents)</span>
            <span className="text-slate-300 font-mono text-xs">
              [{validation.bounds.extents.join(', ')}]
            </span>
          </div>
        )}

        <button
          onClick={onClose}
          className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs transition-colors"
        >
          Close Inspector
        </button>
      </div>
    </div>
  );
}
