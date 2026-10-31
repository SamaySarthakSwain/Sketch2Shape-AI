import React from 'react';
import { X, Trash2, Box, Download, Clock, ExternalLink, ShieldCheck } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { HistoryItem } from '../../types';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { triggerFileDownload } from '../../services/downloads';
import { capitalize } from '../../utils/formatters';

interface HistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HistoryDrawer: React.FC<HistoryDrawerProps> = ({ isOpen, onClose }) => {
  const { history, clearHistory, setCurrentMeshResult, setActiveTab } = useAppStore();

  if (!isOpen) return null;

  const handleOpenItem = (item: HistoryItem) => {
    setCurrentMeshResult(
      {
        job_id: item.id,
        status: 'completed',
        model_used: item.modelUsed,
        vertices: item.vertices,
        faces: item.faces,
        mesh_valid: true,
        is_watertight: item.isWatertight,
        downloads: {
          glb: item.glbUrl,
          ...(item.objUrl ? { obj: item.objUrl } : {}),
        },
        quality_report: item.qualityReport,
      },
      item.glbUrl
    );
    setActiveTab('workspace');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm flex justify-end transition-all">
      <div className="w-full max-w-md bg-slate-950 border-l border-slate-800 h-full flex flex-col shadow-2xl">
        {/* Drawer Header */}
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Box className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-semibold text-slate-100">Generation History</h3>
            <span className="text-xs text-slate-500 font-mono">({history.length})</span>
          </div>
          <div className="flex items-center gap-2">
            {history.length > 0 && (
              <button
                onClick={clearHistory}
                className="p-1.5 text-slate-400 hover:text-rose-400 rounded-md transition-colors"
                title="Clear All History"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-200 rounded-md transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Drawer List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {history.length === 0 ? (
            <div className="h-64 flex flex-col items-center justify-center text-center text-slate-500">
              <Box className="w-8 h-8 text-slate-600 mb-2" />
              <p className="text-xs">No 3D models generated yet.</p>
              <p className="text-[11px] text-slate-600 mt-1">
                Synthesize a model in the studio to populate history.
              </p>
            </div>
          ) : (
            history.map((item) => (
              <div
                key={item.id}
                className="border border-slate-800/80 rounded-xl bg-slate-900/60 p-3 hover:border-slate-700 transition-all space-y-2.5"
              >
                <div className="flex items-start gap-3">
                  {/* Thumbnail */}
                  <div className="w-14 h-14 rounded-lg bg-white overflow-hidden flex items-center justify-center p-1 border border-slate-700/50 flex-shrink-0">
                    <img
                      src={item.thumbnailUrl}
                      alt={item.category}
                      className="max-h-full max-w-full object-contain"
                    />
                  </div>

                  {/* Metadata */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-200 truncate">
                        {capitalize(item.category)}
                      </span>
                      {item.isWatertight && (
                        <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-0.5">
                          <ShieldCheck className="w-3 h-3" />
                          Watertight
                        </span>
                      )}
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                      {item.modelUsed} • {item.vertices}v / {item.faces}f
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1 font-mono">
                      <Clock className="w-2.5 h-2.5" />
                      {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-end gap-1.5 pt-2 border-t border-slate-800/60">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleOpenItem(item)}
                    icon={<ExternalLink className="w-3 h-3" />}
                  >
                    View 3D
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => triggerFileDownload(item.glbUrl, `sketch2shape_${item.id}.glb`)}
                    icon={<Download className="w-3 h-3" />}
                  >
                    GLB
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
