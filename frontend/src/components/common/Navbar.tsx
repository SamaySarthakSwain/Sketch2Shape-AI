import React, { useEffect } from 'react';
import { Box, Activity, History, Layers, Info, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { getReconstructionHealth, getReconstructionModels } from '../../services/reconstruction';

interface NavbarProps {
  onOpenHistory?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenHistory }) => {
  const { activeTab, setActiveTab, health, setHealth, setModels, history } = useAppStore();

  useEffect(() => {
    // Initial fetch of health and models
    const checkBackend = async () => {
      try {
        const [healthRes, modelsRes] = await Promise.all([
          getReconstructionHealth(),
          getReconstructionModels(),
        ]);
        setHealth(healthRes);
        setModels(modelsRes.models);
      } catch (e) {
        console.warn('Backend not responding yet:', e);
      }
    };
    checkBackend();
    const interval = setInterval(checkBackend, 15000);
    return () => clearInterval(interval);
  }, [setHealth, setModels]);

  return (
    <header className="h-14 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md sticky top-0 z-40 px-4 lg:px-8 flex items-center justify-between">
      {/* Brand Identity */}
      <div className="flex items-center gap-6">
        <button
          onClick={() => setActiveTab('home')}
          className="flex items-center gap-2.5 text-left group focus:outline-none"
        >
          <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 group-hover:bg-blue-600/30 transition-all">
            <Box className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-semibold text-sm tracking-tight text-slate-100">Sketch2Shape</span>
              <span className="text-xs px-1.5 py-0.2 text-blue-400 font-mono bg-blue-950/70 border border-blue-800/40 rounded">
                AI
              </span>
            </div>
            <p className="text-[10px] text-slate-400 -mt-0.5 font-mono">Stage 8 • Neural 3D Engine</p>
          </div>
        </button>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center gap-1 pl-4 border-l border-slate-800/80">
          <button
            onClick={() => setActiveTab('home')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              activeTab === 'home'
                ? 'bg-slate-800/90 text-slate-100 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('workspace')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors flex items-center gap-1.5 ${
              activeTab === 'workspace'
                ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            Studio Workspace
          </button>
          <button
            onClick={() => setActiveTab('gallery')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors flex items-center gap-1.5 ${
              activeTab === 'gallery'
                ? 'bg-slate-800/90 text-slate-100 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            3D Gallery
          </button>
          <button
            onClick={() => setActiveTab('about')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors flex items-center gap-1.5 ${
              activeTab === 'about'
                ? 'bg-slate-800/90 text-slate-100 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
            }`}
          >
            <Info className="w-3.5 h-3.5" />
            Architecture & Models
          </button>
        </nav>
      </div>

      {/* Hardware Status & Actions */}
      <div className="flex items-center gap-3">
        {/* Hardware Status Pill */}
        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full border border-slate-800 bg-slate-900/80 text-[11px] font-mono text-slate-300">
          {health?.gpu_available ? (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-slate-400 truncate max-w-[150px]">{health.gpu_name}</span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-300">{health.vram_total_gb}GB VRAM</span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              <span className="text-slate-400">CPU / Connecting...</span>
            </>
          )}
        </div>

        {/* History Button */}
        <button
          onClick={onOpenHistory}
          className="relative px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-xs text-slate-300 flex items-center gap-1.5 transition-colors"
          title="View Generation History"
        >
          <History className="w-3.5 h-3.5 text-slate-400" />
          <span className="hidden sm:inline">History</span>
          {history.length > 0 && (
            <span className="w-4 h-4 rounded-full bg-blue-600 text-white text-[10px] flex items-center justify-center font-bold">
              {history.length}
            </span>
          )}
        </button>
      </div>
    </header>
  );
};
