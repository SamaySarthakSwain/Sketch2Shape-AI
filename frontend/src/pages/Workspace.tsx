import React, { useState } from 'react';
import { Upload, PenTool, Sparkles, Download, Box, Loader2, AlertCircle, Sliders, CheckCircle2 } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { UploadPanel } from '../components/upload/UploadPanel';
import { DrawingCanvas } from '../components/canvas/DrawingCanvas';
import { ModelViewer3D } from '../components/viewer/ModelViewer3D';
import { analyzeSketch, analyzePrompt } from '../services/intelligence';
import { submitPipelineJob, getPipelineStatus, getPipelineResult } from '../services/pipeline';
import { triggerFileDownload } from '../services/downloads';

export const Workspace: React.FC = () => {
  const [sketchMode, setSketchMode] = useState<'draw' | 'upload'>('draw');
  const [isGenerating, setIsGenerating] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    currentImageBase64,
    textPrompt,
    setTextPrompt,
    preprocessFirst,
    setPreprocessFirst,
    pbrGlbUrl,
    activeGlbUrl,
    setCurrentMeshResult,
    setPbrGlbUrl,
    setRefinedGlbUrl,
    setReconstructionStage,
    currentMeshResult,
  } = useAppStore();

  const [generationSummary, setGenerationSummary] = useState<{
    objectName: string;
    primaryHex?: string;
    secondaryHex?: string;
    durationSeconds?: number;
  } | null>(null);

  const handleGenerate = async () => {
    setErrorMessage(null);
    setIsGenerating(true);
    setStatusMessage('Preparing input...');

    try {
      // Validate that at least a sketch or prompt is provided
      const hasSketch = !!currentImageBase64;
      const hasPrompt = !!textPrompt.trim();

      if (!hasSketch && !hasPrompt) {
        throw new Error(
          sketchMode === 'draw'
            ? 'Please create a sketch on the canvas first.'
            : 'Please upload a sketch image first.'
        );
      }

      let category: string | undefined = undefined;
      let primaryRgb: number[] | undefined = undefined;
      let secondaryRgb: number[] | undefined = undefined;
      let primaryHex: string | undefined = undefined;
      let secondaryHex: string | undefined = undefined;
      let objectLabel = '3D Asset';

      // 1. Analyze Sketch / Prompt for object type & colors
      if (hasPrompt && !hasSketch) {
        setStatusMessage('Analyzing prompt characteristics with AI...');
        const pRes = await analyzePrompt(textPrompt);
        category = pRes.category;
        primaryRgb = pRes.primary_color_rgb;
        secondaryRgb = pRes.secondary_color_rgb;
        primaryHex = pRes.primary_color_hex;
        secondaryHex = pRes.secondary_color_hex;
        objectLabel = pRes.predicted_object || pRes.category || 'Object';
      } else if (hasSketch) {
        setStatusMessage(
          preprocessFirst
            ? 'Preprocessing sketch (resizing, contrast, noise reduction)...'
            : 'Analyzing sketch visual concept...'
        );
        const intel = await analyzeSketch(currentImageBase64!);
        category = intel.predicted_category;
        primaryRgb = intel.primary_color_rgb;
        secondaryRgb = intel.secondary_color_rgb;
        primaryHex = intel.primary_color_hex;
        secondaryHex = intel.secondary_color_hex;
        objectLabel = intel.predicted_category || 'Object';

        // If optional prompt also provided, merge prompt colors/attributes
        if (hasPrompt) {
          try {
            const pRes = await analyzePrompt(textPrompt);
            if (pRes.category) category = pRes.category;
            if (pRes.primary_color_rgb) {
              primaryRgb = pRes.primary_color_rgb;
              primaryHex = pRes.primary_color_hex;
            }
            if (pRes.secondary_color_rgb) {
              secondaryRgb = pRes.secondary_color_rgb;
              secondaryHex = pRes.secondary_color_hex;
            }
            if (pRes.predicted_object) objectLabel = pRes.predicted_object;
          } catch {
            // Fallback to sketch semantics
          }
        }
      }

      setGenerationSummary({
        objectName: objectLabel,
        primaryHex,
        secondaryHex,
      });

      // 2. Submit pipeline reconstruction job with optimal PBR settings
      setStatusMessage('Reconstructing 3D geometry & baking materials...');

      const payload: any = {
        preferred_model: 'auto',
        quality_preset: 'balanced',
        preprocess_first: preprocessFirst,
        auto_refine: true,
        refine_preset: 'balanced',
        export_formats: ['glb', 'obj'],
        allow_fallback: true,
        category_override: category,
        enable_pbr: true,
        enable_packaging: true,
        async_execution: true,
      };

      if (hasSketch) {
        payload.image_b64 = currentImageBase64;
      }
      if (hasPrompt) {
        payload.prompt = textPrompt;
      }
      if (primaryRgb) payload.primary_color_rgb = primaryRgb;
      if (secondaryRgb) payload.secondary_color_rgb = secondaryRgb;

      const submitRes = await submitPipelineJob(payload);
      const jobId = submitRes.job_id;

      // 3. Poll for pipeline completion with live stage feedback
      const STAGE_LABELS: Record<string, string> = {
        initialized: 'Initializing reconstruction pipeline...',
        validating_input: 'Validating visual concept input...',
        preprocessing: 'Preprocessing sketch (resizing, contrast, noise reduction)...',
        classifying_intent: 'Analyzing object type & visual semantics...',
        selecting_model: 'Selecting optimal 3D reconstruction model...',
        reconstructing_3d: 'Generating 3D geometry with AI neural model...',
        evaluating_mesh: 'Evaluating mesh quality & watertightness...',
        refining_mesh: 'Refining surfaces & topology...',
        synthesizing_pbr: 'Synthesizing realistic PBR textures & materials...',
        packaging_export: 'Packaging GLB & OBJ 3D assets...',
      };

      let isDone = false;
      let polls = 0;
      const maxPolls = 400;

      while (!isDone && polls < maxPolls) {
        await new Promise((r) => setTimeout(r, 1500));
        polls++;

        const statusRes = await getPipelineStatus(jobId);
        if (statusRes.status === 'completed') {
          isDone = true;
          const result = await getPipelineResult(jobId);

          const finalPbr = result.web_artifacts?.pbr_glb_url || result.artifacts?.pbr_glb;
          const finalRefined = result.web_artifacts?.refined_glb_url || result.artifacts?.refined_glb;
          const finalGlb =
            finalPbr ||
            finalRefined ||
            result.web_artifacts?.primary_glb_url ||
            result.artifacts?.primary_glb ||
            result.web_artifacts?.glb_url;
          const finalObj =
            result.web_artifacts?.primary_obj_url ||
            result.web_artifacts?.obj_url ||
            result.artifacts?.obj;

          setCurrentMeshResult(
            {
              status: 'completed',
              job_id: jobId,
              model_used: result.metrics?.model_used || 'InstantMesh / TRELLIS AI',
              downloads: {
                glb: finalGlb,
                obj: finalObj,
              },
              inference_time_seconds: result.metrics?.total_duration_seconds || Math.round(polls * 1.5),
            },
            finalGlb
          );

          if (finalPbr) setPbrGlbUrl(finalPbr);
          if (finalRefined) setRefinedGlbUrl(finalRefined);

          setGenerationSummary((prev) => ({
            objectName: prev?.objectName || objectLabel,
            primaryHex: prev?.primaryHex || primaryHex,
            secondaryHex: prev?.secondaryHex || secondaryHex,
            durationSeconds: result.metrics?.total_duration_seconds || Math.round(polls * 1.5),
          }));

          setReconstructionStage('completed', '3D asset generated successfully!');
        } else if (statusRes.status === 'failed') {
          throw new Error(statusRes.error || 'Failed to generate 3D model.');
        } else {
          const stageKey = statusRes.current_stage || '';
          const stageLabel = STAGE_LABELS[stageKey] || 'Generating 3D model...';
          const elapsed = Math.round(polls * 1.5);
          setStatusMessage(`${stageLabel} (${elapsed}s)`);
        }
      }

      if (!isDone) {
        throw new Error('Pipeline generation timed out. Please try again or check server logs.');
      }
    } catch (err: any) {
      console.error(err);
      setErrorMessage(err.message || 'An error occurred during 3D generation.');
    } finally {
      setIsGenerating(false);
    }
  };

  const activeGlb = pbrGlbUrl || activeGlbUrl || currentMeshResult?.downloads?.glb;
  const activeObj = currentMeshResult?.downloads?.obj;

  const handleDownload = (format: 'glb' | 'obj') => {
    const url = format === 'glb' ? activeGlb : activeObj;
    if (!url) return;
    const filename = `${(generationSummary?.objectName || 'model').replace(/\s+/g, '_').toLowerCase()}.${format}`;
    triggerFileDownload(url, filename);
  };

  return (
    <div className="py-6 px-4 lg:px-8 max-w-6xl mx-auto w-full space-y-5">
      {/* Page Title */}
      <div className="text-center max-w-xl mx-auto space-y-1">
        <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
          Sketch Input & 3D Model Generation
        </h1>
        <p className="text-xs text-slate-400">
          Supply a visual concept via in-app sketching or image upload to convert into 3D.
        </p>
      </div>

      {errorMessage && (
        <div className="max-w-xl mx-auto p-3 bg-rose-950/40 border border-rose-900/60 rounded-xl text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Studio Grid: Left = Visual Concept Input, Right = Resulting 3D Asset */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Sketch Input, Preprocessing & Optional Prompt */}
        <div className="lg:col-span-5 bg-slate-950/70 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl">
          {/* Section Heading & Mode Selector */}
          <div className="space-y-2">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
              1. Supply Visual Concept
            </span>

            {/* Toggle: In-app sketching vs Image upload */}
            <div className="grid grid-cols-2 p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs">
              <button
                onClick={() => setSketchMode('draw')}
                className={`py-2 rounded-lg font-medium transition-all flex items-center justify-center gap-1.5 ${
                  sketchMode === 'draw'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <PenTool className="w-3.5 h-3.5" />
                In-App Sketching
              </button>
              <button
                onClick={() => setSketchMode('upload')}
                className={`py-2 rounded-lg font-medium transition-all flex items-center justify-center gap-1.5 ${
                  sketchMode === 'upload'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Upload className="w-3.5 h-3.5" />
                Image Upload
              </button>
            </div>
          </div>

          {/* Active Sketch Input Component */}
          <div className="min-h-[260px]">
            {sketchMode === 'draw' ? <DrawingCanvas /> : <UploadPanel />}
          </div>

          {/* Input Preparation / Preprocessing */}
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-xs font-medium text-slate-200 flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5 text-blue-400" />
                Input Preprocessing
              </span>
              <p className="text-[11px] text-slate-500">
                Resizing, background handling, contrast & noise reduction
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={preprocessFirst}
                onChange={(e) => setPreprocessFirst(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {/* Optional Text Prompt */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-slate-200 flex items-center gap-1.5">
                <span>Optional Text Prompt</span>
                <span className="text-[10px] text-slate-400 bg-slate-900 px-1.5 py-0.2 rounded border border-slate-800">
                  Optional
                </span>
              </label>
              <span className="text-[10px] text-slate-500">
                Not a prerequisite
              </span>
            </div>
            <input
              type="text"
              value={textPrompt}
              onChange={(e) => setTextPrompt(e.target.value)}
              placeholder="Describe type, material, color, or style (e.g. Red sports car, wooden legs)..."
              className="w-full text-xs bg-slate-900 border border-slate-800 rounded-xl px-3 py-2.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
            />
          </div>

          {/* Primary Action Button */}
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full py-3.5 px-4 rounded-xl font-semibold text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white shadow-lg shadow-blue-900/30 transition-all flex items-center justify-center gap-2"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{statusMessage || 'Generating 3D model...'}</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Generate 3D Model</span>
              </>
            )}
          </button>

          {/* Result Summary (if generated) */}
          {generationSummary && !isGenerating && (
            <div className="p-2.5 rounded-xl bg-slate-900/70 border border-slate-800 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-slate-400">Object:</span>
                <span className="font-semibold text-slate-200 capitalize">
                  {generationSummary.objectName}
                </span>
                {generationSummary.primaryHex && (
                  <span
                    className="w-3.5 h-3.5 rounded-full border border-slate-700 inline-block shadow-sm"
                    style={{ backgroundColor: generationSummary.primaryHex }}
                    title={`Primary Color: ${generationSummary.primaryHex}`}
                  />
                )}
                {generationSummary.secondaryHex && (
                  <span
                    className="w-3.5 h-3.5 rounded-full border border-slate-700 inline-block shadow-sm"
                    style={{ backgroundColor: generationSummary.secondaryHex }}
                    title={`Secondary Color: ${generationSummary.secondaryHex}`}
                  />
                )}
              </div>
              {generationSummary.durationSeconds && (
                <span className="text-[11px] text-slate-500 font-mono">
                  {generationSummary.durationSeconds.toFixed(1)}s
                </span>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Resulting 3D Asset & Downloads */}
        <div className="lg:col-span-7 space-y-4">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
              2. Resulting 3D Asset
            </span>
          </div>

          <ModelViewer3D />

          {/* Download 3D Asset Buttons */}
          <div className="grid grid-cols-2 gap-3">
            <button
              disabled={!activeGlb || isGenerating}
              onClick={() => handleDownload('glb')}
              className="py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed font-medium text-xs text-white shadow-lg shadow-blue-900/20 flex items-center justify-center gap-2 transition-all"
            >
              <Download className="w-4 h-4" />
              <span>Download .GLB</span>
            </button>
            <button
              disabled={!activeObj || isGenerating}
              onClick={() => handleDownload('obj')}
              className="py-3 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed font-medium text-xs text-slate-200 border border-slate-800 flex items-center justify-center gap-2 transition-all"
            >
              <Box className="w-4 h-4" />
              <span>Download .OBJ</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
