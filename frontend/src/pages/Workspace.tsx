import React, { useState } from 'react';
import { Upload, PenTool, Brain, Box, Sparkles, AlertCircle } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { UploadPanel } from '../components/upload/UploadPanel';
import { DrawingCanvas } from '../components/canvas/DrawingCanvas';
import { IntelligencePanel } from '../components/intelligence/IntelligencePanel';
import { ReconstructionControls } from '../components/reconstruction/ReconstructionControls';
import { MaterialStyleControls } from '../components/materials/MaterialStyleControls';
import { ModelViewer3D } from '../components/viewer/ModelViewer3D';
import { ModelInfoPanel } from '../components/viewer/ModelInfoPanel';
import { GeometryIntelligencePanel } from '../components/geometry/GeometryIntelligencePanel';
import { PrintabilityAndExportPanel } from '../components/packaging/PrintabilityAndExportPanel';
import { VisualPipelineTracker } from '../components/pipeline/VisualPipelineTracker';
import { DemoModeSelector } from '../components/demo/DemoModeSelector';


export const Workspace: React.FC = () => {
  const [inputMode, setInputMode] = useState<'upload' | 'draw'>('upload');
  const {
    currentMeshResult,
    reconstructionStage,
    reconstructionProgressMsg,
    reconstructionError,
  } = useAppStore();

  return (
    <div className="py-6 px-4 lg:px-8 max-w-[1600px] mx-auto w-full space-y-6">
      {/* Workspace Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
            <Box className="w-5 h-5 text-blue-500" />
            Studio Workspace
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Transform 2D sketch input into an interactive, watertight 3D model with real-time semantic analysis.
          </p>
        </div>

        {/* Status Message / Pipeline Stage */}
        {reconstructionStage !== 'idle' && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/80 text-xs font-mono">
            {reconstructionStage === 'completed' ? (
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
            ) : reconstructionStage === 'failed' ? (
              <span className="w-2 h-2 rounded-full bg-rose-500" />
            ) : (
              <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping" />
            )}
            <span className="text-slate-300 capitalize">{reconstructionStage}:</span>
            <span className="text-slate-400 truncate max-w-[260px]">
              {reconstructionProgressMsg}
            </span>
          </div>
        )}
      </div>

      {reconstructionError && (
        <div className="p-3 bg-rose-950/40 border border-rose-900/60 rounded-xl text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{reconstructionError}</span>
        </div>
      )}

      {/* Stage 12: Hackathon Demonstration Mode Preset Selector */}
      <DemoModeSelector />

      {/* Visual Generation Pipeline Tracker */}
      <VisualPipelineTracker />

      {/* Main Studio Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Input, Intelligence, and Reconstruction Controls */}
        <div className="lg:col-span-5 space-y-6">
          {/* Sketch Input Mode Switcher */}
          <div className="border border-slate-800 rounded-xl bg-slate-950/60 p-4 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div className="flex items-center gap-2">
                <PenTool className="w-4 h-4 text-blue-400" />
                <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  2D Sketch Source
                </h3>
              </div>
              <div className="flex p-0.5 rounded-lg bg-slate-900 border border-slate-800">
                <button
                  onClick={() => setInputMode('upload')}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 ${
                    inputMode === 'upload'
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Upload className="w-3 h-3" />
                  Upload
                </button>
                <button
                  onClick={() => setInputMode('draw')}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 ${
                    inputMode === 'draw'
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <PenTool className="w-3 h-3" />
                  Draw
                </button>
              </div>
            </div>

            {/* Input Component */}
            {inputMode === 'upload' ? <UploadPanel /> : <DrawingCanvas />}
          </div>

          {/* Sketch Intelligence Panel */}
          <IntelligencePanel />

          {/* Reconstruction Engine Controls */}
          <ReconstructionControls />

          {/* Stage 11: PBR Material & Visual Style Controls */}
          <MaterialStyleControls />
        </div>

        {/* Right Column: Interactive 3D Viewport, Quality Metrics, and Export */}
        <div className="lg:col-span-7 space-y-5 lg:sticky lg:top-20">
          {/* 3D Viewport */}
          <ModelViewer3D />

          {/* Stage 11: 3D Print Diagnostics & Multi-Format Packaging */}
          <PrintabilityAndExportPanel />

          {/* Geometric & Topological Quality Report */}
          <ModelInfoPanel
            report={currentMeshResult?.quality_report}
            modelName={currentMeshResult?.model_used}
            inferenceSeconds={currentMeshResult?.inference_time_seconds}
          />

          {/* Stage 9: Geometry Intelligence, Multi-View Audit & Refinement */}
          <GeometryIntelligencePanel />
        </div>
      </div>

    </div>
  );
};
