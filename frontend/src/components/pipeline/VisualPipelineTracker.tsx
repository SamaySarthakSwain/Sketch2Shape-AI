import React from 'react';
import { CheckCircle2, Circle, Clock, Sparkles } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

interface PipelineStep {
  id: string;
  label: string;
  stageMatch: string[];
}

const STEPS: PipelineStep[] = [
  { id: 'upload', label: 'Sketch Uploaded', stageMatch: ['validating_input'] },
  { id: 'analyze', label: 'Sketch Analyzed', stageMatch: ['opencv_preprocessing', 'sketch_intelligence'] },
  { id: 'select', label: 'AI Model Selected', stageMatch: ['model_selection'] },
  { id: 'generate', label: '3D Generated', stageMatch: ['reconstructing_3d', 'mesh_validation'] },
  { id: 'texture', label: 'Texture Generated', stageMatch: ['pbr_texturing'] },
  { id: 'refine', label: 'Geometry Refined', stageMatch: ['geometry_analysis', 'mesh_refinement'] },
  { id: 'ready', label: 'Final Asset Ready', stageMatch: ['exporting_assets', 'asset_packaging', 'completed'] },
];

export const VisualPipelineTracker: React.FC = () => {
  const { pipelineStageHistory, reconstructionStage } = useAppStore();

  const completedStages = new Set(
    pipelineStageHistory.filter((s) => s.success).map((s) => s.stage)
  );

  return (
    <div className="w-full bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 backdrop-blur-md">
      <div className="flex items-center justify-between overflow-x-auto gap-2 py-1 scrollbar-none">
        {STEPS.map((step, idx) => {
          const isDone =
            reconstructionStage === 'completed' ||
            step.stageMatch.some((sm) => completedStages.has(sm));

          const isCurrent =
            reconstructionStage !== 'completed' &&
            reconstructionStage !== 'idle' &&
            step.stageMatch.includes(reconstructionStage);

          return (
            <React.Fragment key={step.id}>
              <div className="flex items-center gap-1.5 flex-shrink-0">
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold transition-all ${
                    isDone
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow-sm shadow-emerald-500/20'
                      : isCurrent
                      ? 'bg-blue-600 text-white animate-pulse border border-blue-400 shadow-md shadow-blue-500/30'
                      : 'bg-slate-800/80 text-slate-500 border border-slate-700/60'
                  }`}
                >
                  {isDone ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  ) : isCurrent ? (
                    <Sparkles className="w-3 h-3 text-white" />
                  ) : (
                    idx + 1
                  )}
                </div>
                <span
                  className={`text-[11px] font-medium whitespace-nowrap ${
                    isDone
                      ? 'text-slate-200'
                      : isCurrent
                      ? 'text-blue-400 font-semibold'
                      : 'text-slate-500'
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {idx < STEPS.length - 1 && (
                <div
                  className={`flex-1 min-w-[14px] h-[2px] rounded-full transition-colors ${
                    isDone ? 'bg-emerald-500/50' : 'bg-slate-800'
                  }`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
