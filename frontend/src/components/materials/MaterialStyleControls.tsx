import React, { useState, useEffect } from 'react';
import { Palette, Sparkles, RefreshCw, Wand2, Layers, Check } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { fetchMaterials, fetchStyles, retextureJob } from '../../services/pipeline';

const STYLES = [
  { id: 'realistic', name: 'Realistic' },
  { id: 'stylized', name: 'Stylized' },
  { id: 'cartoon', name: 'Cartoon' },
  { id: 'product_render', name: 'Product Render' },
  { id: 'futuristic', name: 'Futuristic' },
  { id: 'metallic', name: 'Metallic' },
  { id: 'matte', name: 'Matte' },
  { id: 'glossy', name: 'Glossy' },
];

export const MaterialStyleControls: React.FC = () => {
  const {
    intelligence,
    overriddenCategory,
    visualStyle,
    setVisualStyle,
    selectedMaterial,
    setSelectedMaterial,
    pipelineJobId,
    activeGlbUrl,
    refinedGlbUrl,
    setPbrGlbUrl,
    setActiveMeshVariant,
  } = useAppStore();

  const [availableMaterials, setAvailableMaterials] = useState<any[]>([]);
  const [recommended, setRecommended] = useState<any[]>([]);
  const [isRetexturing, setIsRetexturing] = useState(false);
  const [retextureNotice, setRetextureNotice] = useState<string | null>(null);

  const activeCategory = overriddenCategory || intelligence?.predicted_category || 'chair';

  useEffect(() => {
    fetchMaterials(activeCategory)
      .then((data) => {
        if (data && data.materials) {
          setAvailableMaterials(data.materials);
          setRecommended(data.recommended_for_category || []);
          if (!selectedMaterial && data.recommended_for_category?.length > 0) {
            setSelectedMaterial(data.recommended_for_category[0].id);
          }
        }
      })
      .catch((err) => console.error('Failed to load materials', err));
  }, [activeCategory, setSelectedMaterial]);

  const handleApplyRetexture = async () => {
    if (!pipelineJobId) {
      setRetextureNotice('Generate or load a 3D model first.');
      return;
    }

    setIsRetexturing(true);
    setRetextureNotice(null);

    try {
      const res = await retextureJob(pipelineJobId, visualStyle, selectedMaterial);
      if (res && res.web_artifacts?.pbr_glb_url) {
        setPbrGlbUrl(res.web_artifacts.pbr_glb_url);
        setActiveMeshVariant('pbr');
        setRetextureNotice(`Baked ${visualStyle} ${selectedMaterial || 'default'} textures successfully!`);
      }
    } catch (err: any) {
      setRetextureNotice(`Retexture failed: ${err.message || 'Unknown error'}`);
    } finally {
      setIsRetexturing(false);
    }
  };

  const hasActiveModel = Boolean(activeGlbUrl || refinedGlbUrl);

  return (
    <div className="border border-slate-800 rounded-xl bg-slate-950/60 p-4 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <Palette className="w-4 h-4 text-amber-400" />
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Material & Visual Style
          </h3>
        </div>
        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-amber-950/40 border border-amber-900/60 text-amber-300">
          PBR Metallic-Roughness
        </span>
      </div>

      {/* Visual Style Selector */}
      <div className="space-y-1.5">
        <label className="text-[11px] font-medium text-slate-400 flex items-center justify-between">
          <span>Aesthetic Render Style</span>
          <span className="text-amber-400 font-mono capitalize">{visualStyle}</span>
        </label>
        <div className="grid grid-cols-4 gap-1.5">
          {STYLES.map((st) => (
            <button
              key={st.id}
              onClick={() => setVisualStyle(st.id)}
              className={`px-2 py-1.5 rounded-lg text-xs font-medium transition-all text-center ${
                visualStyle === st.id
                  ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-sm'
                  : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-850'
              }`}
            >
              {st.name}
            </button>
          ))}
        </div>
      </div>

      {/* Recommended Physical Materials for Category */}
      <div className="space-y-1.5">
        <label className="text-[11px] font-medium text-slate-400 flex items-center justify-between">
          <span>Physical Material ({activeCategory})</span>
          {recommended.length > 0 && (
            <span className="text-[10px] text-emerald-400 font-mono">
              {recommended.length} Category Presets
            </span>
          )}
        </label>

        <div className="grid grid-cols-2 gap-1.5 max-h-36 overflow-y-auto pr-1">
          {availableMaterials.map((mat) => {
            const isRec = recommended.some((r) => r.id === mat.id);
            const isSel = selectedMaterial === mat.id;
            const r = mat.base_color_rgb?.[0] || 150;
            const g = mat.base_color_rgb?.[1] || 150;
            const b = mat.base_color_rgb?.[2] || 150;

            return (
              <button
                key={mat.id}
                onClick={() => setSelectedMaterial(mat.id)}
                className={`p-2 rounded-lg border text-left text-xs transition-all flex items-center gap-2 ${
                  isSel
                    ? 'border-amber-500 bg-amber-950/20 text-white'
                    : 'border-slate-800 bg-slate-900/60 text-slate-300 hover:border-slate-700'
                }`}
              >
                {/* Color swatch */}
                <div
                  className="w-4 h-4 rounded-full border border-white/20 flex-shrink-0 shadow-sm"
                  style={{ backgroundColor: `rgb(${r}, ${g}, ${b})` }}
                />
                <div className="flex-1 min-w-0">
                  <div className="truncate font-medium text-[11px]">{mat.display_name}</div>
                  <div className="text-[9px] text-slate-500 font-mono capitalize">
                    {mat.pattern_type} • R:{(mat.roughness || 0.5).toFixed(2)}
                  </div>
                </div>
                {isSel && <Check className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* Retexture Action Button */}
      {hasActiveModel && (
        <div className="pt-2 border-t border-slate-800/80 space-y-2">
          <button
            onClick={handleApplyRetexture}
            disabled={isRetexturing}
            className={`w-full py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
              isRetexturing
                ? 'bg-amber-800/60 text-amber-200 cursor-not-allowed'
                : 'bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white shadow-md shadow-amber-600/20'
            }`}
          >
            {isRetexturing ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Synthesizing PBR Maps...
              </>
            ) : (
              <>
                <Wand2 className="w-3.5 h-3.5" />
                Re-Bake PBR Textures
              </>
            )}
          </button>
          {retextureNotice && (
            <p className="text-[11px] text-amber-400 font-mono text-center">{retextureNotice}</p>
          )}
        </div>
      )}
    </div>
  );
};
