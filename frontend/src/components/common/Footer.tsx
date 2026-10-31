import React from 'react';
import { Box } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-slate-900 bg-slate-950/60 py-4 px-4 text-xs text-slate-500">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Box className="w-3.5 h-3.5 text-blue-500" />
          <span className="font-medium text-slate-400">Sketch2Shape</span>
          <span>•</span>
          <span>AI 3D Studio</span>
        </div>
        <p className="text-[11px] text-slate-600">Turn sketches & prompts into 3D models</p>
      </div>
    </footer>
  );
};
