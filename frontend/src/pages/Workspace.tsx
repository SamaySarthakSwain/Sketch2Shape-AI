import React, { useState } from 'react';
import { Upload, PenTool, Wand2, Sparkles, Download, Box, Loader2, AlertCircle } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { UploadPanel } from '../components/upload/UploadPanel';
import { DrawingCanvas } from '../components/canvas/DrawingCanvas';
import { PromptTo3DPanel } from '../components/prompt/PromptTo3DPanel';
import { ModelViewer3D } from '../components/viewer/ModelViewer3D';
import { analyzeSketch, analyzePrompt } from '../services/intelligence';
import { submitPipelineJob, getPipelineStatus, getPipelineResult } from '../services/pipeline';
import { triggerFileDownload } from '../services/downloads';

export const Workspace: React.FC = () => {
  const [inputMode, setInputMode] = useState<'draw' | 'upload' | 'prompt'>('draw');
  const [isGenerating, setIsGenerating] = useState(false);
  const [statusText, setStatusText] = useState('');
  const [errorText, setErrorText] = useState<string | null>(null);

  const [detectedResult, setDetectedResult] = useState<{
    name: string;
    primaryHex?: string;
    secondaryHex?: string;
    duration?: number;
  } | null>(null);

  const {
    currentImageBase64,
    textPrompt,
    pbrGlbUrl,
    activeGlbUrl,
    setCurrentMeshResult,
    setPbrGlbUrl,
    setRefinedGlbUrl,
    setReconstructionStage,
    currentMeshResult,
  } = useAppStore();

  const handleGenerate = async () => {
    setErrorText(null);
    setIsGenerating(true);
    setStatusText('Preparing...');

    try {
      let category: string | undefined = undefined;
      let primaryRgb: number[] | undefined = undefined;
      let secondaryRgb: number[] | undefined = undefined;
      let primaryHex: string | undefined = undefined;
      let secondaryHex: string | undefined = undefined;
      let objectLabel = '3D Object';

      // 1. Semantic & Color Analysis
      if (inputMode === 'prompt') {
        if (!textPrompt.trim()) {
          throw new Error('Please enter a description for your 3D model.');
        }
        setStatusText('Analyzing prompt & colors with AI...');
        const promptRes = await analyzePrompt(textPrompt);
        category = promptRes.category;
        primaryRgb = promptRes.primary_color_rgb;
        secondaryRgb = promptRes.secondary_color_rgb;
        primaryHex = promptRes.primary_color_hex;
        secondaryHex = promptRes.secondary_color_hex;
        objectLabel = promptRes.predicted_object || promptRes.category || 'Object';
      } else {
        if (!currentImageBase64) {
          throw new Error(
            inputMode === 'draw'
              ? 'Please draw a sketch on the canvas first.'
              : 'Please upload an image first.'
          );
        }
        setStatusText('Analyzing sketch & colors...');
        const intel = await analyzeSketch(currentImageBase64);
        category = intel.predicted_category;
        primaryRgb = intel.primary_color_rgb;
        secondaryRgb = intel.secondary_color_rgb;
        primaryHex = intel.primary_color_hex;
        secondaryHex = intel.secondary_color_hex;
        objectLabel = intel.predicted_category || 'Object';
      }

      setDetectedResult({
        name: objectLabel,
        primaryHex,
        secondaryHex,
      });

      // 2. Submit to Reconstruction Pipeline with Best Quality Settings
      setStatusText('Generating 3D model & PBR textures...');

      const payload: any = {
        preferred_model: 'auto',
        quality_preset: 'high',
        preprocess_first: inputMode !== 'prompt',
        auto_refine: true,
        refine_preset: 'high',
        export_formats: ['glb', 'obj'],
        allow_fallback: true,
        category_override: category,
        enable_pbr: true,
        enable_packaging: true,
        async_execution: true,
      };

      if (inputMode === 'prompt') {
        payload.prompt = textPrompt;
        if (primaryRgb) payload.primary_color_rgb = primaryRgb;
        if (secondaryRgb) payload.secondary_color_rgb = secondaryRgb;
      } else {
        payload.image_b64 = currentImageBase64;
      }

      const submitRes = await submitPipelineJob(payload);
      const jobId = submitRes.job_id;

      // 3. Poll until completed
      let isDone = false;
      let polls = 0;
      const maxPolls = 180;

      while (!isDone && polls < maxPolls) {
        await new Promise((r) => setTimeout(r, 1000));
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
              model_used: result.metrics?.model_used || 'Procedural / PBR Engine',
              downloads: {
                glb: finalGlb,
                obj: finalObj,
              },
              inference_time_seconds: result.metrics?.total_duration_seconds || polls,
            },
            finalGlb
          );

          if (finalPbr) setPbrGlbUrl(finalPbr);
          if (finalRefined) setRefinedGlbUrl(finalRefined);

          setDetectedResult((prev) => ({
            name: prev?.name || objectLabel,
            primaryHex: prev?.primaryHex || primaryHex,
            secondaryHex: prev?.secondaryHex || secondaryHex,
            duration: result.metrics?.total_duration_seconds || polls,
          }));

          setReconstructionStage('completed', '3D model generated successfully!');
        } else if (statusRes.status === 'failed') {
          throw new Error(statusRes.error || 'Failed to generate 3D model.');
        } else {
          setStatusText('Creating 3D geometry & baking materials...');
        }
      }
    } catch (err: any) {
      console.error(err);
      setErrorText(err.message || 'An error occurred during 3D generation.');
    } finally {
      setIsGenerating(false);
    }
  };

  const activeGlb = pbrGlbUrl || activeGlbUrl || currentMeshResult?.downloads?.glb;
  const activeObj = currentMeshResult?.downloads?.obj;

  const handleDownload = (format: 'glb' | 'obj') => {
    const url = format === 'glb' ? activeGlb : activeObj;
    if (!url) return;
    const filename = `${(detectedResult?.name || 'model').replace(/\s+/g, '_').toLowerCase()}.${format}`;
    triggerFileDownload(url, filename);
  };

  return (
    <div className="py-6 px-4 lg:px-8 max-w-6xl mx-auto w-full space-y-6">
      {/* Studio Header */}
      <div className="text-center max-w-xl mx-auto space-y-1">
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Create 3D Model
        </h1>
        <p className="text-xs text-slate-400">
          Draw, upload a sketch, or describe what you want in 3D.
        </p>
      </div>

      {errorText && (
        <div className="max-w-xl mx-auto p-3 bg-rose-950/40 border border-rose-900/60 rounded-xl text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{errorText}</span>
        </div>
      )}

      {/* Main Studio: 2 Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Input Card */}
        <div className="lg:col-span-5 bg-slate-950/70 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl">
          {/* 3 Input Tabs */}
          <div className="grid grid-cols-3 p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <button
              onClick={() => setInputMode('draw')}
              className={`py-2 rounded-lg font-medium transition-all flex items-center justify-center gap-1.5 ${
                inputMode === 'draw'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <PenTool className="w-3.5 h-3.5" />
              Draw
            </button>
            <button
              onClick={() => setInputMode('upload')}
              className={`py-2 rounded-lg font-medium transition-all flex items-center justify-center gap-1.5 ${
                inputMode === 'upload'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Upload className="w-3.5 h-3.5" />
              Upload
            </button>
            <button
              onClick={() => setInputMode('prompt')}
              className={`py-2 rounded-lg font-medium transition-all flex items-center justify-center gap-1.5 ${
                inputMode === 'prompt'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Wand2 className="w-3.5 h-3.5" />
              Prompt
            </button>
          </div>

          {/* Active Input Mode Component */}
          <div className="min-h-[280px]">
            {inputMode === 'draw' && <DrawingCanvas />}
            {inputMode === 'upload' && <UploadPanel />}
            {inputMode === 'prompt' && <PromptTo3DPanel />}
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
                <span>{statusText || 'Generating 3D model...'}</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Generate 3D Model</span>
              </>
            )}
          </button>

          {/* Result Summary Pill */}
          {detectedResult && !isGenerating && (
            <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className="text-slate-400">Object:</span>
                <span className="font-semibold text-slate-200 capitalize">
                  {detectedResult.name}
                </span>
                {detectedResult.primaryHex && (
                  <span
                    className="w-3.5 h-3.5 rounded-full border border-slate-700 shadow-sm inline-block"
                    style={{ backgroundColor: detectedResult.primaryHex }}
                    title={`Primary Color: ${detectedResult.primaryHex}`}
                  />
                )}
                {detectedResult.secondaryHex && (
                  <span
                    className="w-3.5 h-3.5 rounded-full border border-slate-700 shadow-sm inline-block"
                    style={{ backgroundColor: detectedResult.secondaryHex }}
                    title={`Secondary Color: ${detectedResult.secondaryHex}`}
                  />
                )}
              </div>
              {detectedResult.duration && (
                <span className="text-[11px] text-slate-500 font-mono">
                  {detectedResult.duration.toFixed(1)}s
                </span>
              )}
            </div>
          )}
        </div>

        {/* Right Column: 3D Studio Viewport & Download */}
        <div className="lg:col-span-7 space-y-4">
          <ModelViewer3D />

          {/* Download Buttons */}
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
