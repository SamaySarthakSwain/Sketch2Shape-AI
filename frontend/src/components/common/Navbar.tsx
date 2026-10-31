import React, { useEffect } from 'react';
import { Box, Sparkles, Layers, History } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { getReconstructionHealth, getReconstructionModels } from '../../services/reconstruction';

interface NavbarProps {
  onOpenHistory?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenHistory }) => {
  const { activeTab, setActiveTab, health, setHealth, setModels, history } = useAppStore();

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const [healthRes, modelsRes] = await Promise.all([
          getReconstructionHealth(),
          getReconstructionModels(),
        ]);
        setHealth(healthRes);
        setModels(modelsRes.models);
      } catch (e) {
        // Backend connecting
      }
    };
    checkBackend();
  }, [setHealth, setModels]);

  return (
    <header className="h-14 border-b border-slate-800/60 bg-slate-950/80 backdrop-blur-md sticky top-0 z-40 px-4 lg:px-8 flex items-center justify-between">
      {/* Brand */}
      <div className="flex items-center gap-6">
        <button
          onClick={() => setActiveTab('workspace')}
          className="flex items-center gap-2.5 group focus:outline-none"
        >
          <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 group-hover:bg-blue-600/30 transition-all">
            <Box className="w-4 h-4" />
          </div>
          <span className="font-semibold text-sm tracking-tight text-white">
            Sketch2Shape
          </span>
        </button>

        {/* Minimal Navigation */}
        <nav className="flex items-center gap-1 pl-4 border-l border-slate-800">
          <button
            onClick={() => setActiveTab('workspace')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'workspace'
                ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            Studio
          </button>
          <button
            onClick={() => setActiveTab('gallery')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'gallery'
                ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            Gallery
          </button>
        </nav>
      </div>

      {/* Status & History */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-slate-800/80 bg-slate-900/50 text-[11px] text-slate-300">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-slate-400 font-medium">Ready</span>
        </div>

        {onOpenHistory && history.length > 0 && (
          <button
            onClick={onOpenHistory}
            className="px-2.5 py-1 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition-colors"
          >
            <History className="w-3.5 h-3.5" />
            <span>History</span>
            <span className="px-1.5 py-0.2 rounded-full bg-blue-600 text-white text-[10px] font-bold">
              {history.length}
            </span>
          </button>
        )}
      </div>
    </header>
  );
};
