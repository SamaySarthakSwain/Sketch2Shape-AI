import React from 'react';
import { MultiViewMetrics } from '../../types';
import { Camera, CheckCircle2, AlertCircle } from 'lucide-react';
import { Badge } from '../common/Badge';

interface MultiViewGalleryProps {
  multiview: MultiViewMetrics;
  assetId: string;
}

export const MultiViewGallery: React.FC<MultiViewGalleryProps> = ({ multiview, assetId }) => {
  const viewsOrder = ['front', 'back', 'left', 'right', 'top', 'bottom', 'three_quarter'];

  const getCleanLabel = (vname: string) => {
    switch (vname) {
      case 'three_quarter':
        return '3/4 Perspective';
      default:
        return vname.charAt(0).toUpperCase() + vname.slice(1);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Camera className="w-4 h-4 text-blue-400" />
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Multi-View Consistency & Silhouette Audit
          </h4>
        </div>
        <div className="flex items-center gap-2">
          {multiview.front_sketch_iou !== null && multiview.front_sketch_iou !== undefined && (
            <Badge variant={multiview.front_sketch_iou > 0.4 ? 'success' : 'warning'}>
              Front IoU: {(multiview.front_sketch_iou * 100).toFixed(1)}%
            </Badge>
          )}
          <Badge variant="outline">
            Continuity: {(multiview.cross_view_continuity_score * 100).toFixed(0)}%
          </Badge>
        </div>
      </div>

      {/* 7 Views Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2">
        {viewsOrder.map((vname) => {
          const viewData = multiview.views[vname];
          if (!viewData) return null;

          const imgUrl = `/static/multiview/${assetId}_${vname}.png`;

          return (
            <div
              key={vname}
              className="group relative rounded-lg border border-slate-800 bg-slate-900/60 p-1.5 transition-all hover:border-blue-500/50"
            >
              <div className="aspect-square w-full overflow-hidden rounded bg-slate-950 flex items-center justify-center">
                <img
                  src={imgUrl}
                  alt={`${vname} view`}
                  className="h-full w-full object-contain transition-transform duration-300 group-hover:scale-105"
                  onError={(e) => {
                    // Fallback placeholder if image not found
                    (e.target as HTMLElement).style.display = 'none';
                  }}
                />
              </div>

              <div className="mt-1.5 flex items-center justify-between px-0.5 text-[10px]">
                <span className="font-medium text-slate-300">{getCleanLabel(vname)}</span>
                <span className="text-slate-500 font-mono">
                  {(viewData.occupancy_ratio * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Visible vs Hidden Surface Notice */}
      <div className="rounded-md border border-slate-800/80 bg-slate-900/30 p-2.5 text-[11px] text-slate-400 flex items-start gap-2">
        <AlertCircle className="w-3.5 h-3.5 text-blue-400 mt-0.5 shrink-0" />
        <p>
          <span className="font-semibold text-slate-300">Reconstruction Geometry Notice:</span> A 2D sketch constrains visible frontal contours. Hidden surface consistency (back/bottom) is estimated via cross-view continuity and geometric prior priors.
        </p>
      </div>
    </div>
  );
};
