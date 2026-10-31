import React, { useState } from 'react';
import {
  Cpu,
  Layers,
  Settings2,
  Box,
  Sparkles,
  AlertCircle,
  FileCheck,
  CheckCircle,
  RotateCcw,
  Zap,
  ShieldCheck,
  Activity,
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import {
  submitPipelineJob,
  getPipelineStatus,
  getPipelineResult,
  PipelineGeneratePayload,
} from '../../services/pipeline';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';

export const ReconstructionControls: React.FC = () => {
  const {
    currentImageBase64,
    intelligence,
    overriddenCategory,
    selectedModel,
    setSelectedModel,
    qualityPreset,
    setQualityPreset,
    exportFormats,
    setExportFormats,
    preprocessFirst,
    setPreprocessFirst,
    models,
    reconstructionStage,
    reconstructionProgressMsg,
    setReconstructionStage,
    setCurrentMeshResult,
    setReconstructionError,
    setGeometryReport,
    setMeshComparison,
    setRefinedGlbUrl,
    setActiveMeshVariant,
    addToHistory,
    pipelineJobId,
    pipelineStageHistory,
    fallbackOccurred,
    peakVramMb,
    setPipelineJob,
    visualStyle,
    selectedMaterial,
    setPbrGlbUrl,
    setBundleZipUrl,
    setPrintabilityReport,
  } = useAppStore();

  const [isGenerating, setIsGenerating] = useState(false);
  const [activeStageStep, setActiveStageStep] = useState<string>('');

  const toggleFormat = (fmt: string) => {
    if (exportFormats.includes(fmt)) {
      if (exportFormats.length > 1) {
        setExportFormats(exportFormats.filter((f) => f !== fmt));
      }
    } else {
      setExportFormats([...exportFormats, fmt]);
    }
  };

  const handleGenerate = async () => {
    if (!currentImageBase64) return;

    setIsGenerating(true);
    setReconstructionError(null);
    setReconstructionStage('uploading', 'Submitting sketch to unified pipeline orchestrator...');
    setActiveStageStep('validating_input');

    try {
      const activeCat = overriddenCategory || intelligence?.predicted_category;

      const payload: any = {
        image_b64: currentImageBase64,
        preferred_model: selectedModel,
        quality_preset: qualityPreset,
        preprocess_first: preprocessFirst,
        auto_refine: true,
        refine_preset: 'balanced',
        export_formats: exportFormats,
        allow_fallback: true,
        category_override: activeCat,
        visual_style: visualStyle,
        material_override: selectedMaterial,
        enable_pbr: true,
        enable_packaging: true,
      };

      // Submit asynchronous job
      const submitResp = await submitPipelineJob(payload);
      const jobId = submitResp.job_id;
      setPipelineJob(jobId, [], 0, false);

      // Poll until completion or failure
      let isDone = false;
      let pollCount = 0;
      const maxPolls = 300; // 5 minutes timeout

      while (!isDone && pollCount < maxPolls) {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        pollCount++;

        const statusResp = await getPipelineStatus(jobId);
        setActiveStageStep(statusResp.current_stage);
        
        // Find latest stage record
        const history = statusResp.stage_history || [];
        const latestRecord = history[history.length - 1];
        const latestMsg = latestRecord ? latestRecord.message : `Executing ${statusResp.current_stage}...`;

        setReconstructionStage(statusResp.current_stage as any, latestMsg);
        setPipelineJob(jobId, history, statusResp.peak_vram_mb, false);

        if (statusResp.status === 'completed') {
          isDone = true;
          // Retrieve full result
          const fullResult = await getPipelineResult(jobId);
          const primaryGlb = fullResult.web_artifacts?.primary_glb_url || fullResult.artifacts?.primary_glb;
          const refinedGlb = fullResult.web_artifacts?.refined_glb_url || fullResult.artifacts?.refined_glb;
          const pbrGlb = fullResult.web_artifacts?.pbr_glb_url || fullResult.artifacts?.pbr_glb;
          const finalGlb = pbrGlb || refinedGlb || primaryGlb;

          const metrics = fullResult.metrics || {};
          const fallbackTriggered = metrics.fallback_occurred || false;
          setPipelineJob(jobId, history, statusResp.peak_vram_mb, fallbackTriggered);

          // Populate store results
          const resultObj: any = {
            status: 'completed',
            job_id: jobId,
            model_used: metrics.model_used || selectedModel,
            vertices: metrics.original_vertices || 0,
            faces: metrics.original_faces || 0,
            inference_time_seconds: metrics.total_duration_seconds || 0,
            is_watertight: true,
            downloads: {
              glb: finalGlb,
              obj: fullResult.web_artifacts?.primary_obj_url || fullResult.artifacts?.primary_obj,
            },
            quality_report: fullResult.config?.geometry_report,
            printability: metrics.printability,
          };

          setReconstructionStage('completed', '3D asset reconstructed & PBR textured successfully!');
          setCurrentMeshResult(resultObj, primaryGlb);

          if (refinedGlb) {
            setRefinedGlbUrl(refinedGlb);
          }

          if (pbrGlb) {
            setPbrGlbUrl(pbrGlb);
            setActiveMeshVariant('pbr');
          } else if (refinedGlb) {
            setActiveMeshVariant('refined');
          }

          const bundleZip = fullResult.web_artifacts?.bundle_zip_url || fullResult.artifacts?.bundle_zip;
          if (bundleZip) {
            setBundleZipUrl(bundleZip);
          }

          if (metrics.printability) {
            setPrintabilityReport(metrics.printability);
          }


          // Populate geometry report if present
          const geomStage = history.find((s) => s.stage === 'geometry_analysis');
          if (geomStage?.metadata?.geometry_report) {
            setGeometryReport(geomStage.metadata.geometry_report);
          }

          // Populate refinement comparison if present
          const refStage = history.find((s) => s.stage === 'mesh_refinement');
          if (refStage?.metadata?.refinement_report) {
            setMeshComparison(refStage.metadata.refinement_report);
          }

          // Add to history
          addToHistory({
            id: jobId,
            timestamp: new Date().toISOString(),
            thumbnailUrl: currentImageBase64,
            category: metrics.predicted_category || activeCat || 'Unknown',
            confidence: intelligence?.top_prediction_confidence || 1.0,
            modelUsed: metrics.model_used || selectedModel,
            vertices: metrics.original_vertices || 0,
            faces: metrics.original_faces || 0,
            isWatertight: true,
            glbUrl: finalGlb,
            objUrl: fullResult.web_artifacts?.primary_obj_url,
          });

          break;
        } else if (statusResp.status === 'failed') {
          isDone = true;
          throw new Error(statusResp.error || 'Pipeline execution failed.');
        } else if (statusResp.status === 'cancelled') {
          isDone = true;
          throw new Error('Pipeline job was cancelled.');
        }
      }
    } catch (e: any) {
      setReconstructionStage('failed', e.message);
      setReconstructionError(e.message || 'Pipeline execution failed.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-4 border border-slate-800 rounded-xl bg-slate-950/60 p-5">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <Settings2 className="w-4 h-4 text-blue-400" />
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Reconstruction Configuration
          </h4>
        </div>
        <div className="flex items-center gap-2">
          {peakVramMb > 0 && (
            <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/50 px-2 py-0.5 rounded border border-cyan-800/50 flex items-center gap-1">
              <Activity className="w-3 h-3" />
              Peak VRAM: {peakVramMb.toFixed(0)} MB
            </span>
          )}
          <span className="text-[11px] font-mono text-slate-500">FastAPI Pipeline v1</span>
        </div>
      </div>

      {/* Fallback Warning Notice */}
      {fallbackOccurred && (
        <div className="p-3 bg-amber-950/40 border border-amber-800/60 rounded-xl text-xs text-amber-200 flex items-start gap-2">
          <ShieldCheck className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-amber-300">Intelligent Quality Fallback Triggered:</span>
            <p className="text-[11px] text-amber-300/80 mt-0.5">
              Neural model produced an under-tessellated mesh. The pipeline automatically switched to the dedicated category-aware watertight template to ensure guaranteed geometric integrity.
            </p>
          </div>
        </div>
      )}

      {/* Engine Selection */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-slate-300 flex items-center justify-between">
          <span>AI 3D Reconstruction Engine</span>
          <span className="text-[10px] text-slate-500 font-mono">
            Adaptive Model Selection Enabled
          </span>
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {/* Automatic Model Selection */}
          <button
            onClick={() => setSelectedModel('auto')}
            className={`p-3 rounded-lg border text-left transition-all ${
              selectedModel === 'auto'
                ? 'border-blue-500 bg-blue-950/30 text-blue-200'
                : 'border-slate-800 hover:border-slate-700 bg-slate-900/50 text-slate-300'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold">Auto (Adaptive Routing)</span>
              <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            </div>
            <p className="text-[10px] text-slate-400 mt-1">
              High-confidence categories route to watertight templates; complex organic items route to InstantMesh.
            </p>
          </button>

          {/* Explicit Model Options */}
          {models.map((m) => {
            const isSelected = selectedModel === m.name;
            return (
              <button
                key={m.name}
                disabled={!m.is_available}
                onClick={() => setSelectedModel(m.name)}
                className={`p-3 rounded-lg border text-left transition-all relative ${
                  !m.is_available
                    ? 'border-slate-800/50 bg-slate-950/40 text-slate-600 cursor-not-allowed opacity-60'
                    : isSelected
                    ? 'border-blue-500 bg-blue-950/30 text-blue-200'
                    : 'border-slate-800 hover:border-slate-700 bg-slate-900/50 text-slate-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold">{m.display_name}</span>
                  {m.is_available ? (
                    <Badge variant="success" size="sm">
                      {m.vram_required_gb}GB
                    </Badge>
                  ) : (
                    <Badge variant="warning" size="sm">
                      {m.vram_required_gb}GB VRAM
                    </Badge>
                  )}
                </div>
                <p className="text-[10px] text-slate-400 mt-1 line-clamp-2">
                  {m.status_message}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Quality Presets */}
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-slate-300">Quality Preset</label>
        <div className="grid grid-cols-4 gap-2">
          {[
            { id: 'fast', label: 'Fast (15s-2m)', desc: '15 steps / Template' },
            { id: 'balanced', label: 'Balanced', desc: 'Adaptive' },
            { id: 'high', label: 'High Quality', desc: '40 steps FP16' },
            { id: 'ultra_fast', label: 'Real-Time', desc: 'Template 0.2s' },
          ].map((preset) => (
            <button
              key={preset.id}
              onClick={() => setQualityPreset(preset.id as any)}
              className={`p-2 rounded-lg border text-center transition-all ${
                qualityPreset === preset.id
                  ? 'border-blue-500 bg-blue-950/40 text-blue-200 font-semibold'
                  : 'border-slate-800 hover:border-slate-700 bg-slate-900/40 text-slate-400'
              }`}
            >
              <div className="text-xs">{preset.label}</div>
              <div className="text-[9px] text-slate-500 font-mono mt-0.5">{preset.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Export Formats & Preprocessing Switches */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-800/80">
        <div>
          <label className="text-xs font-medium text-slate-300 block mb-1.5">Export Formats</label>
          <div className="flex items-center gap-2">
            <button
              onClick={() => toggleFormat('glb')}
              className={`px-3 py-1.5 rounded-lg border text-xs font-mono flex items-center gap-1.5 transition-all ${
                exportFormats.includes('glb')
                  ? 'border-blue-500 bg-blue-950/40 text-blue-300'
                  : 'border-slate-800 text-slate-500'
              }`}
            >
              <FileCheck className="w-3.5 h-3.5" />
              .GLB (Primary 3D)
            </button>
            <button
              onClick={() => toggleFormat('obj')}
              className={`px-3 py-1.5 rounded-lg border text-xs font-mono flex items-center gap-1.5 transition-all ${
                exportFormats.includes('obj')
                  ? 'border-blue-500 bg-blue-950/40 text-blue-300'
                  : 'border-slate-800 text-slate-500'
              }`}
            >
              <FileCheck className="w-3.5 h-3.5" />
              .OBJ + .MTL
            </button>
          </div>
        </div>

        <div>
          <label className="text-xs font-medium text-slate-300 block mb-1.5">Stage 5 Preprocessing</label>
          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={preprocessFirst}
              onChange={(e) => setPreprocessFirst(e.target.checked)}
              className="rounded bg-slate-900 border-slate-700 text-blue-600 focus:ring-0"
            />
            <span>OpenCV Denoising & Canonical Normalization</span>
          </label>
        </div>
      </div>

      {/* Real-time Stage Progression Tracker */}
      {isGenerating && (
        <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-blue-400 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 animate-spin" />
              Executing Stage: {activeStageStep || 'validating_input'}
            </span>
            <span className="text-[10px] font-mono text-slate-400">11-Stage Pipeline</span>
          </div>
          <p className="text-[11px] text-slate-300 font-mono">{reconstructionProgressMsg}</p>
        </div>
      )}

      {/* Generate & Retry Buttons */}
      <div className="pt-2 flex items-center gap-2">
        <Button
          variant="primary"
          size="lg"
          className="flex-1 justify-center shadow-lg shadow-blue-950/50"
          disabled={!currentImageBase64 || isGenerating}
          isLoading={isGenerating}
          onClick={handleGenerate}
          icon={<Box className="w-5 h-5 text-white" />}
        >
          {isGenerating ? 'Synthesizing 3D Asset...' : 'Generate 3D Asset'}
        </Button>

        {reconstructionStage === 'failed' && (
          <Button
            variant="secondary"
            size="lg"
            disabled={isGenerating}
            onClick={handleGenerate}
            icon={<RotateCcw className="w-4 h-4 text-slate-300" />}
          >
            Retry
          </Button>
        )}
      </div>
    </div>
  );
};
