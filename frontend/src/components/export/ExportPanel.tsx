import React from 'react';
import { Download, FileCode, CheckCircle2, Info, Share2, Box } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { Button } from '../common/Button';
import { triggerFileDownload } from '../../services/downloads';
import { formatBytes } from '../../utils/formatters';

export const ExportPanel: React.FC = () => {
  const { currentMeshResult } = useAppStore();

  if (!currentMeshResult || !currentMeshResult.downloads) {
    return null;
  }

  const glbUrl = currentMeshResult.downloads.glb;
  const objUrl = currentMeshResult.downloads.obj;
  const quality = currentMeshResult.quality_report;

  const handleDownloadGLB = () => {
    if (glbUrl) {
      triggerFileDownload(glbUrl, `sketch2shape_${currentMeshResult.job_id}.glb`);
    }
  };

  const handleDownloadOBJ = () => {
    if (objUrl) {
      triggerFileDownload(objUrl, `sketch2shape_${currentMeshResult.job_id}.obj`);
    }
  };

  return (
    <div className="border border-slate-800 rounded-xl bg-slate-950/70 p-4 space-y-3.5 backdrop-blur-sm">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
        <div className="flex items-center gap-2">
          <Download className="w-4 h-4 text-blue-400" />
          <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
            Export & Downloads
          </h4>
        </div>
        <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
          <CheckCircle2 className="w-3.5 h-3.5" />
          Production Assets Ready
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Binary GLB */}
        {glbUrl && (
          <div className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-blue-500/50 transition-all flex flex-col justify-between space-y-2">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-100 flex items-center gap-1.5">
                  <Box className="w-4 h-4 text-blue-400" />
                  Binary GLTF (.glb)
                </span>
                <span className="text-[11px] font-mono text-slate-400">
                  {formatBytes(quality?.file_size_bytes)}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Standard self-contained binary 3D container. Includes vertex coordinates, normals, colors, and textures for WebGL, Three.js, and AR.
              </p>
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={handleDownloadGLB}
              icon={<Download className="w-3.5 h-3.5" />}
              className="w-full justify-center"
            >
              Download .GLB
            </Button>
          </div>
        )}

        {/* Wavefront OBJ */}
        {objUrl && (
          <div className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between space-y-2">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-100 flex items-center gap-1.5">
                  <FileCode className="w-4 h-4 text-slate-400" />
                  Wavefront (.obj)
                </span>
                <span className="text-[11px] font-mono text-slate-400">ASCII Mesh</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Universally compatible with Blender, Maya, Unreal Engine, and Unity. Companion .mtl material definition exported.
              </p>
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleDownloadOBJ}
              icon={<Download className="w-3.5 h-3.5" />}
              className="w-full justify-center"
            >
              Download .OBJ
            </Button>
          </div>
        )}
      </div>

      <div className="text-[10px] text-slate-500 flex items-center gap-1.5 pt-1">
        <Info className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
        <span>
          Every exported asset is validated and reopen-verified via Trimesh prior to streaming.
        </span>
      </div>
    </div>
  );
};
