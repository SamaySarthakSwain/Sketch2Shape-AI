import React, { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { Card, CardHeader, CardContent } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { MultiViewGallery } from './MultiViewGallery';
import { refineMeshGeometry, analyzeMeshGeometry } from '../../services/geometry';
import { triggerFileDownload } from '../../services/downloads';
import {
  ShieldCheck,
  AlertTriangle,
  Sparkles,
  Layers,
  Activity,
  CheckCircle2,
  Wrench,
  Download,
  Eye,
  RefreshCw,
  Box,
} from 'lucide-react';

export const GeometryIntelligencePanel: React.FC = () => {
  const {
    currentMeshResult,
    geometryReport,
    isAnalyzingGeometry,
    meshComparison,
    isRefining,
    activeMeshVariant,
    refinedGlbUrl,
    setGeometryReport,
    setIsAnalyzingGeometry,
    setMeshComparison,
    setIsRefining,
    setActiveMeshVariant,
    setRefinedGlbUrl,
  } = useAppStore();

  const [refinementPreset, setRefinementPreset] = useState<'fast' | 'balanced' | 'high'>('balanced');
  const [refineError, setRefineError] = useState<string | null>(null);

  if (!currentMeshResult && !geometryReport) {
    return (
      <Card className="border-slate-800 bg-slate-900/40">
        <CardContent className="p-6 text-center text-slate-400">
          <Box className="w-10 h-10 mx-auto mb-3 text-slate-600 animate-pulse" />
          <p className="text-sm font-medium">3D Geometry Intelligence Ready</p>
          <p className="text-xs text-slate-500 mt-1">
            Generate or select a 3D asset to inspect topology, multi-view consistency, and run safe mesh refinement.
          </p>
        </CardContent>
      </Card>
    );
  }

  const activeAssetId = geometryReport?.asset_id || currentMeshResult?.job_id || 'asset';

  const handleRunFullAudit = async () => {
    setIsAnalyzingGeometry(true);
    try {
      const rep = await analyzeMeshGeometry({
        asset_id: activeAssetId,
        run_multiview: true,
      });
      setGeometryReport(rep);
    } catch (e: any) {
      console.error('Audit failed:', e);
    } finally {
      setIsAnalyzingGeometry(false);
    }
  };

  const handleApplyRefinement = async () => {
    setIsRefining(true);
    setRefineError(null);
    try {
      const res = await refineMeshGeometry({
        asset_id: activeAssetId,
        preset: refinementPreset,
        remove_isolated_shards: true,
        export_formats: ['glb', 'obj'],
      });

      setMeshComparison(res.comparison);
      if (res.downloads?.glb) {
        setRefinedGlbUrl(res.downloads.glb);
        setActiveMeshVariant('refined');
      }
    } catch (e: any) {
      setRefineError(e.message || 'Refinement failed');
    } finally {
      setIsRefining(false);
    }
  };

  const q = geometryReport?.quality;
  const t = geometryReport?.topology;
  const s = geometryReport?.surface;
  const tex = geometryReport?.texture;
  const defects = geometryReport?.defects;

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10';
    if (score >= 60) return 'text-amber-400 border-amber-500/40 bg-amber-500/10';
    return 'text-rose-400 border-rose-500/40 bg-rose-500/10';
  };

  return (
    <Card className="border-slate-800 bg-slate-900/60 shadow-xl overflow-hidden">
      <CardHeader className="border-b border-slate-800/80 pb-3 flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-blue-400" />
          <h3 className="text-sm font-semibold tracking-wide text-slate-100">
            3D Asset Intelligence & Quality Audit
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={handleRunFullAudit}
            disabled={isAnalyzingGeometry}
            className="text-xs h-7 gap-1 border-slate-700"
          >
            <RefreshCw className={`w-3 h-3 ${isAnalyzingGeometry ? 'animate-spin' : ''}`} />
            {isAnalyzingGeometry ? 'Auditing...' : 'Full 7-View Audit'}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-4 space-y-5">
        {/* Quality Score Header */}
        {q ? (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-3.5 rounded-xl border border-slate-800 bg-slate-950/60">
            <div className="flex items-center gap-4">
              <div
                className={`w-14 h-14 rounded-full border-2 flex items-center justify-center font-mono font-bold text-lg shadow-inner ${getScoreColor(
                  q.overall_score
                )}`}
              >
                {q.overall_score.toFixed(0)}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-semibold text-slate-100">Overall Quality Score</h4>
                  <Badge variant="outline" className="text-[10px]">
                    {q.confidence_level.toUpperCase()}
                  </Badge>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  Grounded multi-domain metric: topology, geometry, surface & multi-view consistency.
                </p>
              </div>
            </div>

            {/* Subscores Mini Bars */}
            <div className="w-full sm:w-auto grid grid-cols-3 sm:grid-cols-6 gap-2 text-center text-[10px]">
              <div className="p-1.5 rounded bg-slate-900 border border-slate-800">
                <span className="text-slate-500 block">Topology</span>
                <span className="font-mono font-semibold text-slate-200">{q.subscores.topology.toFixed(0)}</span>
              </div>
              <div className="p-1.5 rounded bg-slate-900 border border-slate-800">
                <span className="text-slate-500 block">Geometry</span>
                <span className="font-mono font-semibold text-slate-200">{q.subscores.geometry.toFixed(0)}</span>
              </div>
              <div className="p-1.5 rounded bg-slate-900 border border-slate-800">
                <span className="text-slate-500 block">Surface</span>
                <span className="font-mono font-semibold text-slate-200">{q.subscores.surface.toFixed(0)}</span>
              </div>
              <div className="p-1.5 rounded bg-slate-900 border border-slate-800">
                <span className="text-slate-500 block">Multi-View</span>
                <span className="font-mono font-semibold text-slate-200">
                  {q.subscores.multiview !== null && q.subscores.multiview !== undefined
                    ? q.subscores.multiview.toFixed(0)
                    : 'N/A'}
                </span>
              </div>
              <div className="p-1.5 rounded bg-slate-900 border border-slate-800">
                <span className="text-slate-500 block">Texture</span>
                <span className="font-mono font-semibold text-slate-200">{q.subscores.texture.toFixed(0)}</span>
              </div>
              <div className="p-1.5 rounded bg-slate-900 border border-slate-800">
                <span className="text-slate-500 block">Export</span>
                <span className="font-mono font-semibold text-slate-200">{q.subscores.export.toFixed(0)}</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-3 rounded-lg bg-blue-950/20 border border-blue-900/40 text-xs text-blue-300 flex items-center justify-between">
            <span>Detailed 7-view multi-domain geometry audit available for this mesh.</span>
            <Button size="sm" onClick={handleRunFullAudit} disabled={isAnalyzingGeometry} className="h-7 text-xs">
              Audit Now
            </Button>
          </div>
        )}

        {/* Multi-View Consistency Gallery */}
        {geometryReport?.multiview && (
          <MultiViewGallery multiview={geometryReport.multiview} assetId={activeAssetId} />
        )}

        {/* Texture & Material Diagnostic */}
        {tex && (
          <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3 flex items-start justify-between gap-3 text-xs">
            <div className="flex items-start gap-2.5">
              <Layers className="w-4 h-4 text-purple-400 mt-0.5 shrink-0" />
              <div>
                <span className="font-semibold text-slate-200">Material & Texture Status:</span>
                <p className="text-slate-400 text-[11px] mt-0.5">{tex.texture_status_message}</p>
              </div>
            </div>
            <Badge variant={tex.has_texture_image ? 'success' : tex.has_vertex_colors ? 'primary' : 'outline'}>
              {tex.texture_mode.replace('_', ' ')}
            </Badge>
          </div>
        )}

        {/* Defect Detection & Recommendations */}
        {defects && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-blue-400" />
                Defect Detection & Manifold Checks:
              </span>
              <Badge variant={defects.has_defects ? 'warning' : 'success'}>
                {defects.has_defects ? `${defects.defect_count} Defect(s)` : 'Clean Manifold'}
              </Badge>
            </div>

            {defects.has_defects ? (
              <ul className="rounded-lg border border-amber-900/30 bg-amber-950/10 p-2.5 space-y-1 text-xs text-amber-300">
                {defects.defect_list.map((d, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-[11px]">
                    <AlertTriangle className="w-3 h-3 text-amber-400 mt-0.5 shrink-0" />
                    <span>{d}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="rounded-lg border border-emerald-900/30 bg-emerald-950/10 p-2 text-xs text-emerald-300 flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Zero topological or geometric defects detected. 100% watertight closed manifold.</span>
              </div>
            )}
          </div>
        )}

        {/* Safe Mesh Refinement Engine */}
        <div className="pt-2 border-t border-slate-800/80 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-200">
              <Wrench className="w-3.5 h-3.5 text-blue-400" />
              Automated Safe Mesh Refinement
            </div>
            <div className="flex items-center gap-1 bg-slate-950 p-0.5 rounded-lg border border-slate-800 text-[11px]">
              {(['fast', 'balanced', 'high'] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setRefinementPreset(p)}
                  className={`px-2 py-0.5 rounded capitalize transition-colors ${
                    refinementPreset === p
                      ? 'bg-blue-600 text-white font-medium'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div className="text-[11px] text-slate-400">
            {refinementPreset === 'fast' && 'FAST: Purges duplicate vertices, zero-area faces, recalculates outward normals.'}
            {refinementPreset === 'balanced' && 'BALANCED: Non-destructive Taubin volume-preserving smoothing, topology repair & moderate quadric decimation.'}
            {refinementPreset === 'high' && 'HIGH: Adaptive curvature smoothing, feature preservation, isolated fragment pruning.'}
          </div>

          <Button
            onClick={handleApplyRefinement}
            disabled={isRefining}
            className="w-full h-8 text-xs font-medium gap-1.5 bg-blue-600 hover:bg-blue-500"
          >
            <Sparkles className={`w-3.5 h-3.5 ${isRefining ? 'animate-spin' : ''}`} />
            {isRefining ? 'Refining Geometry...' : `Apply Safe Refinement (${refinementPreset.toUpperCase()})`}
          </Button>

          {refineError && (
            <p className="text-xs text-rose-400 bg-rose-950/20 border border-rose-900/40 p-2 rounded">
              {refineError}
            </p>
          )}

          {/* Before-and-After Comparison Card */}
          {meshComparison && (
            <div className="rounded-xl border border-blue-900/40 bg-blue-950/10 p-3 space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-blue-300">Before vs After Comparison:</span>
                <Badge variant={meshComparison.is_degraded ? 'error' : 'success'}>
                  {meshComparison.is_degraded ? 'Degradation Flagged' : 'Topology Improved'}
                </Badge>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
                <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">Vertices</span>
                  <span className="font-mono font-medium text-slate-200">
                    {meshComparison.original_vertices} → {meshComparison.refined_vertices}
                  </span>
                  <span className="text-[10px] text-blue-400 block font-mono">
                    {meshComparison.vertex_delta >= 0 ? `+${meshComparison.vertex_delta}` : meshComparison.vertex_delta}
                  </span>
                </div>

                <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">Faces</span>
                  <span className="font-mono font-medium text-slate-200">
                    {meshComparison.original_faces} → {meshComparison.refined_faces}
                  </span>
                  <span className="text-[10px] text-blue-400 block font-mono">
                    {meshComparison.face_delta >= 0 ? `+${meshComparison.face_delta}` : meshComparison.face_delta}
                  </span>
                </div>

                <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">Watertight</span>
                  <span className="font-mono font-medium text-emerald-400">
                    {meshComparison.refined_watertight ? 'Preserved' : 'Lost'}
                  </span>
                </div>

                <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">File Size</span>
                  <span className="font-mono font-medium text-slate-200">
                    {(meshComparison.refined_file_size_bytes / 1024).toFixed(1)} KB
                  </span>
                </div>
              </div>

              {/* Viewport Switcher & Download Refined Buttons */}
              <div className="flex flex-wrap items-center gap-2 pt-1">
                {refinedGlbUrl && (
                  <Button
                    size="sm"
                    variant={activeMeshVariant === 'refined' ? 'primary' : 'outline'}
                    onClick={() => setActiveMeshVariant(activeMeshVariant === 'refined' ? 'original' : 'refined')}
                    className="text-xs h-7 gap-1"
                  >
                    <Eye className="w-3 h-3" />
                    {activeMeshVariant === 'refined' ? 'Viewing Refined Mesh' : 'View Refined in 3D'}
                  </Button>
                )}

                <Button
                  size="sm"
                  variant="outline"
                  onClick={() =>
                    triggerFileDownload(
                      `/api/v1/geometry/download/${activeAssetId}/glb`,
                      `sketch2shape_${activeAssetId}_refined.glb`
                    )
                  }
                  className="text-xs h-7 gap-1 border-slate-700 ml-auto"
                >
                  <Download className="w-3 h-3" />
                  Refined GLB
                </Button>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={() =>
                    triggerFileDownload(
                      `/api/v1/geometry/download/${activeAssetId}/obj`,
                      `sketch2shape_${activeAssetId}_refined.obj`
                    )
                  }
                  className="text-xs h-7 gap-1 border-slate-700"
                >
                  <Download className="w-3 h-3" />
                  Refined OBJ
                </Button>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
