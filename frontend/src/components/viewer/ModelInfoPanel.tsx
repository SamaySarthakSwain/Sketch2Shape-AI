import React from 'react';
import {
  ShieldCheck,
  AlertCircle,
  Clock,
  HardDrive,
  Box,
  Layers,
  Maximize2,
  CheckCircle2,
} from 'lucide-react';
import { MeshQualityReport } from '../../types';
import { formatBytes, formatDuration } from '../../utils/formatters';
import { Badge } from '../common/Badge';

interface ModelInfoPanelProps {
  report?: MeshQualityReport;
  modelName?: string;
  inferenceSeconds?: number;
}

export const ModelInfoPanel: React.FC<ModelInfoPanelProps> = ({
  report,
  modelName,
  inferenceSeconds,
}) => {
  if (!report) {
    return (
      <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl text-center text-xs text-slate-500">
        No mesh geometry metadata available for current asset.
      </div>
    );
  }

  const dims = report.dimensions_xyz || [0, 0, 0];

  return (
    <div className="border border-slate-800 rounded-xl bg-slate-950/70 p-4 space-y-3.5 backdrop-blur-sm">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
        <div className="flex items-center gap-2">
          <Box className="w-4 h-4 text-blue-400" />
          <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
            Geometric & Topological Verification
          </h4>
        </div>
        <div>
          {report.is_watertight ? (
            <Badge variant="success" size="sm">
              <ShieldCheck className="w-3 h-3 text-emerald-400" />
              100% Watertight Manifold
            </Badge>
          ) : (
            <Badge variant="warning" size="sm">
              <AlertCircle className="w-3 h-3" />
              Open Surface Mesh
            </Badge>
          )}
        </div>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 font-mono">
        <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800/80">
          <span className="text-[10px] text-slate-500 block uppercase">Vertices</span>
          <span className="text-sm font-bold text-slate-200">{report.vertices.toLocaleString()}</span>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800/80">
          <span className="text-[10px] text-slate-500 block uppercase">Faces (Triangles)</span>
          <span className="text-sm font-bold text-slate-200">{report.faces.toLocaleString()}</span>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800/80">
          <span className="text-[10px] text-slate-500 block uppercase">Euler Characteristic</span>
          <span className="text-sm font-bold text-blue-400">χ = {report.euler_characteristic}</span>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800/80">
          <span className="text-[10px] text-slate-500 block uppercase">Components</span>
          <span className="text-sm font-bold text-slate-200">{report.components}</span>
        </div>
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
        {/* Dimensions */}
        <div className="p-2.5 rounded-lg bg-slate-900/40 border border-slate-800/60 space-y-1">
          <span className="text-[10px] text-slate-500 font-mono block">Bounding Dimensions (X×Y×Z)</span>
          <span className="font-mono text-slate-300 text-[11px]">
            {dims[0].toFixed(3)} × {dims[1].toFixed(3)} × {dims[2].toFixed(3)}
          </span>
        </div>

        {/* File Size */}
        <div className="p-2.5 rounded-lg bg-slate-900/40 border border-slate-800/60 space-y-1">
          <span className="text-[10px] text-slate-500 font-mono block">Binary Size</span>
          <span className="font-mono text-slate-300 text-[11px] flex items-center gap-1.5">
            <HardDrive className="w-3 h-3 text-slate-400" />
            {formatBytes(report.file_size_bytes)}
          </span>
        </div>

        {/* Model & Latency */}
        <div className="p-2.5 rounded-lg bg-slate-900/40 border border-slate-800/60 space-y-1">
          <span className="text-[10px] text-slate-500 font-mono block">Engine / Latency</span>
          <span className="font-mono text-slate-300 text-[11px] flex items-center gap-1.5">
            <Clock className="w-3 h-3 text-slate-400" />
            {modelName || 'Neural Engine'} ({formatDuration(inferenceSeconds)})
          </span>
        </div>
      </div>
    </div>
  );
};
