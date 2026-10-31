import React, { useState } from 'react';
import {
  Brain,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Tag,
  SlidersHorizontal,
  Compass,
  Edit2,
  Check,
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { analyzeSketch } from '../../services/intelligence';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { capitalize, formatPercent } from '../../utils/formatters';

const COMMON_OVERRIDE_CATEGORIES = [
  'chair',
  'car',
  'airplane',
  'cup',
  'bicycle',
  'apple',
  'table',
  'vase',
  'bottle',
  'tree',
  'guitar',
  'house',
  'fish',
  'bird',
];

export const IntelligencePanel: React.FC = () => {
  const {
    currentImageBase64,
    intelligence,
    isIntelligenceLoading,
    intelligenceError,
    overriddenCategory,
    setIntelligence,
    setIntelligenceLoading,
    setIntelligenceError,
    setOverriddenCategory,
  } = useAppStore();

  const [isEditingCategory, setIsEditingCategory] = useState(false);
  const [customCategoryInput, setCustomCategoryInput] = useState('');

  const handleRunAnalysis = async () => {
    if (!currentImageBase64) return;
    setIntelligenceLoading(true);
    setIntelligenceError(null);
    try {
      const result = await analyzeSketch(currentImageBase64);
      setIntelligence(result);
      setOverriddenCategory(null);
    } catch (e: any) {
      setIntelligenceError(e.message || 'Failed to analyze sketch intelligence.');
    } finally {
      setIntelligenceLoading(false);
    }
  };

  const handleSaveOverride = (cat: string) => {
    setOverriddenCategory(cat.toLowerCase().trim());
    setIsEditingCategory(false);
  };

  const activeCategory = overriddenCategory || intelligence?.predicted_category;

  return (
    <div className="space-y-4">
      {/* Action Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-blue-400" />
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Sketch Semantic Intelligence
          </h4>
        </div>
        <Button
          variant="secondary"
          size="sm"
          disabled={!currentImageBase64 || isIntelligenceLoading}
          isLoading={isIntelligenceLoading}
          onClick={handleRunAnalysis}
          icon={<Sparkles className="w-3.5 h-3.5 text-blue-400" />}
        >
          {intelligence ? 'Re-Analyze' : 'Run Semantic Analysis'}
        </Button>
      </div>

      {intelligenceError && (
        <div className="p-3 bg-rose-950/40 border border-rose-900/60 rounded-lg text-xs text-rose-300">
          {intelligenceError}
        </div>
      )}

      {!intelligence && !isIntelligenceLoading && (
        <div className="border border-slate-800/80 rounded-xl p-5 bg-slate-900/30 text-center">
          <Brain className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-xs text-slate-400">
            {currentImageBase64
              ? 'Click "Run Semantic Analysis" to classify object category, detect geometric symmetry, and extract 3D priors.'
              : 'Upload or draw a sketch to enable semantic intelligence analysis.'}
          </p>
        </div>
      )}

      {/* Intelligence Results */}
      {intelligence && (
        <div className="border border-slate-800 rounded-xl bg-slate-950/60 p-4 space-y-4">
          {/* Main Category & Confidence */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
            <div>
              <span className="text-[11px] text-slate-500 font-mono uppercase tracking-wide">
                Detected Category
              </span>
              <div className="flex items-center gap-2 mt-0.5">
                {isEditingCategory ? (
                  <div className="flex items-center gap-1.5 mt-1">
                    <input
                      type="text"
                      defaultValue={activeCategory || ''}
                      onChange={(e) => setCustomCategoryInput(e.target.value)}
                      placeholder="e.g. chair, car"
                      className="px-2 py-1 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                    <button
                      onClick={() => handleSaveOverride(customCategoryInput || activeCategory || '')}
                      className="p-1 rounded bg-blue-600 hover:bg-blue-500 text-white"
                      title="Save Override"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => setIsEditingCategory(false)}
                      className="text-xs text-slate-400 hover:text-slate-300 px-1"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <>
                    <span className="text-lg font-bold text-slate-100 tracking-tight">
                      {capitalize(activeCategory || 'Unknown')}
                    </span>
                    {overriddenCategory && (
                      <Badge variant="warning" size="sm">
                        Manual Override
                      </Badge>
                    )}
                    <button
                      onClick={() => {
                        setCustomCategoryInput(activeCategory || '');
                        setIsEditingCategory(true);
                      }}
                      className="text-slate-500 hover:text-slate-300 p-1 rounded"
                      title="Override category"
                    >
                      <Edit2 className="w-3 h-3" />
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Confidence & Ambiguity */}
            <div className="flex items-center gap-2">
              <div className="text-right">
                <span className="text-[10px] text-slate-500 font-mono block">Top Confidence</span>
                <span className="text-sm font-semibold font-mono text-blue-400">
                  {formatPercent(intelligence.top_prediction_confidence)}
                </span>
              </div>
              <div>
                {intelligence.is_ambiguous ? (
                  <Badge variant="warning" size="md">
                    <AlertTriangle className="w-3 h-3" /> Ambiguous
                  </Badge>
                ) : (
                  <Badge variant="success" size="md">
                    <CheckCircle2 className="w-3 h-3" /> High Confidence
                  </Badge>
                )}
              </div>
            </div>
          </div>

          {/* Top-5 Predictions Distribution */}
          <div>
            <span className="text-[11px] text-slate-400 font-mono uppercase tracking-wider block mb-2">
              Candidate Distribution (Top-5 Softmax)
            </span>
            <div className="space-y-1.5">
              {intelligence.top_5_predictions.map((p, idx) => (
                <div key={p.category} className="space-y-0.5">
                  <div className="flex justify-between text-xs text-slate-300">
                    <span className="capitalize flex items-center gap-1.5">
                      <span className="text-[10px] text-slate-500 font-mono">#{idx + 1}</span>
                      {p.category.replace(/_/g, ' ')}
                    </span>
                    <span className="font-mono text-slate-400">{formatPercent(p.confidence)}</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        idx === 0 ? 'bg-blue-500' : 'bg-slate-600'
                      }`}
                      style={{ width: `${Math.min(p.confidence * 100, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Geometric Feature Tags */}
          {intelligence.geometric_tags && intelligence.geometric_tags.length > 0 && (
            <div>
              <span className="text-[11px] text-slate-400 font-mono uppercase tracking-wider block mb-1.5">
                Geometric Prior Tags
              </span>
              <div className="flex flex-wrap gap-1.5">
                {intelligence.geometric_tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300"
                  >
                    <Tag className="w-2.5 h-2.5 text-blue-400" />
                    {tag.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Reconstruction Conditioning Hints */}
          {intelligence.reconstruction_hints && (
            <div className="p-3 bg-slate-900/80 border border-slate-800/80 rounded-lg text-xs space-y-1">
              <span className="text-slate-400 font-medium flex items-center gap-1.5">
                <Compass className="w-3.5 h-3.5 text-blue-400" />
                3D Reconstruction Guidance:
              </span>
              <p className="text-slate-300 text-[11px] pl-5">
                Mode: <span className="font-mono text-blue-300">{intelligence.reconstruction_hints.recommended_mode}</span>
              </p>
              <p className="text-slate-400 text-[11px] pl-5 italic">
                "{intelligence.reconstruction_hints.prompt_template}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
