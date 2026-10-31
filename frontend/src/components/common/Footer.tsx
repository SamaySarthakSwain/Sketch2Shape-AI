import React from 'react';
import { Box, Cpu, ShieldCheck } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-slate-800/80 bg-slate-950/70 py-6 px-4 lg:px-8 text-xs text-slate-500">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Box className="w-3.5 h-3.5 text-blue-500" />
          <span className="font-semibold text-slate-400">Sketch2Shape AI</span>
          <span>•</span>
          <span>Open-Source 2D-to-3D Synthesis Platform</span>
        </div>

        <div className="flex items-center gap-4 text-[11px] font-mono">
          <span className="flex items-center gap-1.5 text-slate-400">
            <Cpu className="w-3 h-3 text-slate-500" />
            RTX 3050 4GB VRAM Optimized
          </span>
          <span>•</span>
          <span className="flex items-center gap-1 text-emerald-400">
            <ShieldCheck className="w-3.5 h-3.5" />
            Strict Manifold Validation Active
          </span>
        </div>
      </div>
    </footer>
  );
};
