import React from 'react';
import { Box, Sparkles, Cpu, Cloud, HelpCircle, Activity } from 'lucide-react';

export default function Header({ gpuStatus, onOpenColab, colabConnected }) {
  return (
    <header className="bg-slate-900 border-b border-slate-800 px-6 py-3.5 flex items-center justify-between shadow-lg">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-cyan-500/20 shadow-lg">
          <Box className="w-6 h-6 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
              Sketch2Shape AI
            </h1>
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800/60">
              Hackathon Edition
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Intelligent 2D Sketch to Watertight 3D Mesh Reconstruction
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* GPU Accelerator Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/70 border border-slate-700/60 text-xs">
          <Cpu className={`w-3.5 h-3.5 ${gpuStatus?.cuda_available ? 'text-emerald-400' : 'text-amber-400'}`} />
          <span className="text-slate-300 font-medium">
            {gpuStatus?.cuda_available ? gpuStatus.device_name : 'CPU Fallback'}
          </span>
          {gpuStatus?.cuda_available && (
            <span className="text-[10px] text-emerald-400 font-mono bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/40">
              {gpuStatus.vram_total_mb} MB
            </span>
          )}
        </div>

        {/* Colab Remote Connector */}
        <button
          onClick={onOpenColab}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
            colabConnected
              ? 'bg-indigo-950/60 border-indigo-600 text-indigo-300 hover:bg-indigo-900/60'
              : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200 hover:bg-slate-700'
          }`}
          title="Connect Google Colab GPU Server"
        >
          <Cloud className={`w-3.5 h-3.5 ${colabConnected ? 'text-indigo-400 animate-pulse' : ''}`} />
          <span>{colabConnected ? 'Colab GPU Active' : 'Connect Colab GPU'}</span>
        </button>
      </div>
    </header>
  );
}
