import React from 'react';
import { Box } from 'lucide-react';

export const Navbar: React.FC = () => {
  return (
    <header className="h-14 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md sticky top-0 z-40 px-4 lg:px-8 flex items-center justify-between">
      {/* Brand */}
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
          <Box className="w-4 h-4" />
        </div>
        <div>
          <span className="font-semibold text-sm tracking-tight text-white">
            Sketch2Shape AI
          </span>
          <span className="text-[10px] text-slate-400 block -mt-0.5">
            2D Sketch to 3D Asset Generation
          </span>
        </div>
      </div>

      {/* Online Status */}
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-slate-800 bg-slate-900/60 text-[11px] text-slate-300">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-slate-400 font-medium">Ready</span>
      </div>
    </header>
  );
};
