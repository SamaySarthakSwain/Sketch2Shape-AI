import React, { useState } from 'react';
import { Sparkles, Wand2, Palette, ArrowRight, Brain, CheckCircle2 } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { Button } from '../common/Button';
import { analyzePrompt } from '../../services/intelligence';
import { pipelineApi } from '../../services/pipeline';

const SUGGESTED_PROMPTS = [
  {
    icon: '🏎️',
    label: 'Red Sports Car',
    prompt: 'A futuristic crimson red sports car with sleek aerodynamic chassis and tinted glass',
    color: '#DC2626',
    category: 'car'
  },
  {
    icon: '🪑',
    label: 'Blue Velvet Chair',
    prompt: 'A modern Scandinavian royal blue armchair with plush cushion and sturdy wooden legs',
    color: '#2563EB',
    category: 'chair'
  },
  {
    icon: '☕',
    label: 'Turquoise Mug',
    prompt: 'A handcrafted ceramic turquoise drinking mug with smooth glazed handle and rounded rim',
    color: '#0891B2',
    category: 'cup'
  },
  {
    icon: '✈️',
    label: 'Gold Trim Jet',
    prompt: 'A supersonic sleek airplane aircraft with white fuselage and gold metallic wings',
    color: '#D97706',
    category: 'airplane'
  },
  {
    icon: '🍎',
    label: 'Scarlet Apple',
    prompt: 'A glossy vibrant scarlet red apple fruit with realistic stem and natural organic dimples',
    color: '#E11D48',
    category: 'apple'
  },
  {
    icon: '🚲',
    label: 'Emerald Bicycle',
    prompt: 'A modern emerald green commuter bicycle with dual tubular frame and treaded rubber wheels',
    color: '#059669',
    category: 'bicycle'
  },
];

const COLOR_SWATCHES = [
  { name: 'Crimson Red', hex: '#DC2626', rgb: [220, 38, 38] },
  { name: 'Cobalt Blue', hex: '#2563EB', rgb: [37, 99, 235] },
  { name: 'Emerald Green', hex: '#059669', rgb: [5, 150, 105] },
  { name: 'Amber Gold', hex: '#D97706', rgb: [217, 119, 6] },
  { name: 'Royal Purple', hex: '#7C3AED', rgb: [124, 58, 237] },
  { name: 'Fiery Orange', hex: '#EA580C', rgb: [234, 88, 12] },
  { name: 'Turquoise Teal', hex: '#0891B2', rgb: [8, 145, 178] },
  { name: 'Hot Pink', hex: '#DB2777', rgb: [219, 39, 119] },
];

export const PromptTo3DPanel: React.FC = () => {
  const {
    textPrompt,
    setTextPrompt,
    selectedModel,
    qualityPreset,
    autoRefine,
    refinePreset,
    exportFormats,
    allowFallback,
    overriddenCategory,
    setReconstructionStage,
    setCurrentMeshResult,
    setReconstructionError,
    setIntelligence,
    setIntelligenceLoading,
  } = useAppStore();

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedColor, setSelectedColor] = useState<typeof COLOR_SWATCHES[0] | null>(COLOR_SWATCHES[0]);
  const [analysisResult, setAnalysisResult] = useState<any>(null);

  const handleSelectPreset = (p: typeof SUGGESTED_PROMPTS[0]) => {
    setTextPrompt(p.prompt);
    const matched = COLOR_SWATCHES.find((c) => c.hex.toLowerCase() === p.color.toLowerCase());
    if (matched) setSelectedColor(matched);
  };

  const handleAnalyzePrompt = async () => {
    if (!textPrompt.trim()) return;
    setIsAnalyzing(true);
    try {
      const res = await analyzePrompt(textPrompt);
      setAnalysisResult(res);
      if (res.primary_color_hex) {
        const found = COLOR_SWATCHES.find(
          (c) => c.hex.toLowerCase() === res.primary_color_hex.toLowerCase()
        );
        if (found) setSelectedColor(found);
      }
    } catch (e: any) {
      console.warn('Prompt analysis failed:', e);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGenerate3D = async () => {
    if (!textPrompt.trim()) return;
    setReconstructionError(null);
    setReconstructionStage('processing', 'Analyzing prompt with Gemini and initializing 3D generation...');

    try {
      // 1. Run quick prompt analysis if not already done
      let predictedCat = overriddenCategory;
      if (!analysisResult) {
        setIntelligenceLoading(true);
        const res = await analyzePrompt(textPrompt);
        setAnalysisResult(res);
        setIntelligence(res);
        predictedCat = res.category || overriddenCategory;
      }

      // 2. Trigger pipeline generation
      const job = await pipelineApi.submitJob({
        prompt: textPrompt,
        primary_color_rgb: selectedColor ? selectedColor.rgb : undefined,
        preferred_model: selectedModel,
        quality_preset: qualityPreset,
        preprocess_first: false,
        auto_refine: autoRefine,
        refine_preset: refinePreset,
        export_formats: exportFormats,
        allow_fallback: allowFallback,
        category_override: predictedCat || undefined,
        async_execution: true,
      });

      // 3. Poll pipeline until completed
      await pipelineApi.pollJob(
        job.job_id,
        (status) => {
          setReconstructionStage(
            status.status === 'processing' ? 'processing' : 'processing',
            status.current_stage ? `Stage: ${status.current_stage.replace('_', ' ')}` : 'Generating asset...'
          );
        },
        3000,
        180000
      );

      // 4. Retrieve results
      const result = await pipelineApi.getJobResult(job.job_id);
      const glbUrl = result.web_artifacts?.pbr_glb_url || result.web_artifacts?.glb_url || null;

      setCurrentMeshResult(
        {
          success: true,
          model_name: result.metrics?.model_used || 'Procedural / PBR Engine',
          mesh_path: result.artifacts?.pbr_glb || result.artifacts?.glb || '',
          glb_url: glbUrl,
          inference_time_seconds: result.total_duration_seconds || 8.5,
          vertices: result.metrics?.original_vertices || 1240,
          faces: result.metrics?.original_faces || 2400,
          formats: result.artifacts || {},
        },
        glbUrl
      );

      setReconstructionStage('completed', '3D asset generated from prompt successfully!');
    } catch (err: any) {
      console.error('Prompt-to-3D failed:', err);
      setReconstructionStage('failed', err.message || 'Generation failed');
      setReconstructionError(err.message || 'Prompt-to-3D generation encountered an error');
    } finally {
      setIntelligenceLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header & Description */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Wand2 className="w-4 h-4 text-purple-400" />
          <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
            AI Prompt-to-3D Studio
          </h4>
        </div>
        <span className="text-[11px] font-mono text-purple-400 bg-purple-950/60 border border-purple-900/60 px-2 py-0.5 rounded-full flex items-center gap-1">
          <Brain className="w-3 h-3" />
          Google Gemini 2.5 Vision
        </span>
      </div>

      <p className="text-xs text-slate-400">
        Type a natural language description. Google Gemini will predict the object, isolate its
        visual geometry, and generate a colored 3D asset with matching PBR materials.
      </p>

      {/* Textarea */}
      <div className="space-y-1.5">
        <textarea
          rows={3}
          value={textPrompt}
          onChange={(e) => setTextPrompt(e.target.value)}
          placeholder="e.g. A futuristic crimson red sports car with neon glowing rims and aerodynamic spoiler..."
          className="w-full text-xs bg-slate-900/90 border border-slate-800 rounded-xl p-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/80 transition-all resize-none shadow-inner"
        />
        <div className="flex items-center justify-between text-[11px] text-slate-500">
          <span>Be specific about shapes, components, and vibrant colors</span>
          <span>{textPrompt.length} chars</span>
        </div>
      </div>

      {/* Quick Inspiration Pills */}
      <div className="space-y-2">
        <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
          Suggested Creative Prompts:
        </span>
        <div className="flex flex-wrap gap-1.5">
          {SUGGESTED_PROMPTS.map((item, idx) => (
            <button
              key={idx}
              onClick={() => handleSelectPreset(item)}
              className="text-xs px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-purple-500/60 text-slate-300 hover:text-white transition-all flex items-center gap-1.5 shadow-sm"
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Color Accent Swatches */}
      <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-1.5 font-medium text-slate-300">
            <Palette className="w-3.5 h-3.5 text-blue-400" />
            <span>Target Color Accent:</span>
            {selectedColor && (
              <span className="font-mono text-purple-400 text-[11px]">
                {selectedColor.name} ({selectedColor.hex})
              </span>
            )}
          </div>
          <span className="text-[11px] text-slate-400">PBR texture will match this tone</span>
        </div>

        <div className="flex items-center flex-wrap gap-2 pt-1">
          {COLOR_SWATCHES.map((swatch) => (
            <button
              key={swatch.hex}
              title={swatch.name}
              onClick={() => setSelectedColor(swatch)}
              className={`w-6 h-6 rounded-full transition-transform border ${
                selectedColor?.hex.toLowerCase() === swatch.hex.toLowerCase()
                  ? 'ring-2 ring-purple-500 scale-110 border-white'
                  : 'border-slate-700 hover:scale-105'
              }`}
              style={{ backgroundColor: swatch.hex }}
            />
          ))}
        </div>
      </div>

      {/* AI Prediction Preview (if analyzed) */}
      {analysisResult && (
        <div className="p-3 rounded-xl bg-slate-900/90 border border-purple-900/60 space-y-1.5 text-xs text-slate-300">
          <div className="flex items-center justify-between font-semibold text-purple-300">
            <span className="flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              AI Object Prediction
            </span>
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800">
              {analysisResult.ai_model_used || 'Gemini 2.5'}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 pt-1 text-[11px]">
            <div>
              <span className="text-slate-500">Object: </span>
              <span className="font-medium text-slate-200">
                {analysisResult.predicted_object || textPrompt}
              </span>
            </div>
            <div>
              <span className="text-slate-500">Category: </span>
              <span className="font-medium text-slate-200 capitalize">
                {analysisResult.category || 'car'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between gap-3 pt-2">
        <Button
          variant="outline"
          size="sm"
          disabled={!textPrompt.trim() || isAnalyzing}
          onClick={handleAnalyzePrompt}
          icon={<Brain className="w-3.5 h-3.5" />}
        >
          {isAnalyzing ? 'Predicting Object...' : 'Predict Object First'}
        </Button>

        <Button
          variant="primary"
          disabled={!textPrompt.trim()}
          onClick={handleGenerate3D}
          icon={<ArrowRight className="w-4 h-4" />}
          className="bg-purple-600 hover:bg-purple-500 shadow-md shadow-purple-950/50"
        >
          Generate 3D Model
        </Button>
      </div>
    </div>
  );
};
