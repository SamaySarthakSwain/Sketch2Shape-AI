import { create } from 'zustand';
import {
  SketchIntelligenceResponse,
  ModelInfo,
  ReconstructionHealth,
  ReconstructionResult,
  HistoryItem,
  ReconstructionStage,
  GeometryReport,
  MeshComparison,
} from '../types';

interface AppState {
  // Navigation
  activeTab: 'home' | 'workspace' | 'gallery' | 'about';
  setActiveTab: (tab: 'home' | 'workspace' | 'gallery' | 'about') => void;

  // Active Image & Sketch Input
  currentImageBase64: string | null;
  currentImageName: string | null;
  setCurrentImage: (b64: string | null, name?: string | null) => void;

  // Text-to-3D Prompt Mode
  textPrompt: string;
  setTextPrompt: (prompt: string) => void;

  // Sketch Intelligence
  intelligence: SketchIntelligenceResponse | null;
  isIntelligenceLoading: boolean;
  intelligenceError: string | null;
  overriddenCategory: string | null;
  setIntelligence: (data: SketchIntelligenceResponse | null) => void;
  setIntelligenceLoading: (loading: boolean) => void;
  setIntelligenceError: (err: string | null) => void;
  setOverriddenCategory: (cat: string | null) => void;

  // Reconstruction Configuration
  selectedModel: string; // 'auto' or specific model name
  qualityPreset: 'fast' | 'balanced' | 'high' | 'ultra_fast';
  exportFormats: string[];
  preprocessFirst: boolean;
  setSelectedModel: (model: string) => void;
  setQualityPreset: (preset: 'fast' | 'balanced' | 'high' | 'ultra_fast') => void;
  setExportFormats: (formats: string[]) => void;
  setPreprocessFirst: (pref: boolean) => void;

  // Backend Health & Model Registry
  health: ReconstructionHealth | null;
  models: ModelInfo[];
  setHealth: (health: ReconstructionHealth | null) => void;
  setModels: (models: ModelInfo[]) => void;

  // Active 3D Reconstruction Job
  currentMeshResult: ReconstructionResult | null;
  activeGlbUrl: string | null;
  reconstructionStage: ReconstructionStage;
  reconstructionProgressMsg: string;
  reconstructionError: string | null;
  setReconstructionStage: (stage: ReconstructionStage, msg?: string) => void;
  setCurrentMeshResult: (result: ReconstructionResult | null, glbUrl?: string | null) => void;
  setReconstructionError: (err: string | null) => void;

  // Stage 9: Geometry Intelligence & Refinement
  geometryReport: GeometryReport | null;
  isAnalyzingGeometry: boolean;
  meshComparison: MeshComparison | null;
  isRefining: boolean;
  activeMeshVariant: 'original' | 'refined' | 'pbr';
  refinedGlbUrl: string | null;
  pbrGlbUrl: string | null;
  setGeometryReport: (report: GeometryReport | null) => void;
  setIsAnalyzingGeometry: (val: boolean) => void;
  setMeshComparison: (comp: MeshComparison | null) => void;
  setIsRefining: (val: boolean) => void;
  setActiveMeshVariant: (variant: 'original' | 'refined' | 'pbr') => void;
  setRefinedGlbUrl: (url: string | null) => void;
  setPbrGlbUrl: (url: string | null) => void;

  // Stage 11: PBR Texturing, Materials & Viewer Aesthetics
  visualStyle: string;
  selectedMaterial: string | null;
  lightingPreset: 'studio' | 'product' | 'daylight' | 'cinematic' | 'inspection';
  backgroundPreset: 'dark' | 'white' | 'gradient' | 'transparent';
  shadingMode: 'pbr' | 'solid' | 'wireframe' | 'normal';
  bundleZipUrl: string | null;
  printabilityReport: any | null;
  availableProviders: any[];
  availableMaterials: any[];
  setVisualStyle: (style: string) => void;
  setSelectedMaterial: (mat: string | null) => void;
  setLightingPreset: (preset: 'studio' | 'product' | 'daylight' | 'cinematic' | 'inspection') => void;
  setBackgroundPreset: (preset: 'dark' | 'white' | 'gradient' | 'transparent') => void;
  setShadingMode: (mode: 'pbr' | 'solid' | 'wireframe' | 'normal') => void;
  setBundleZipUrl: (url: string | null) => void;
  setPrintabilityReport: (report: any | null) => void;
  setAvailableProviders: (providers: any[]) => void;
  setAvailableMaterials: (mats: any[]) => void;


  // Viewer Preferences
  wireframe: boolean;
  showGrid: boolean;
  autoRotate: boolean;
  setWireframe: (val: boolean) => void;
  setShowGrid: (val: boolean) => void;
  setAutoRotate: (val: boolean) => void;

  // Stage 10: Production Pipeline & Fallback Tracking
  pipelineJobId: string | null;
  pipelineStageHistory: any[];
  peakVramMb: number;
  fallbackOccurred: boolean;
  setPipelineJob: (jobId: string | null, history?: any[], peakVram?: number, fallback?: boolean) => void;

  // History
  history: HistoryItem[];
  addToHistory: (item: HistoryItem) => void;
  clearHistory: () => void;
}

const STORAGE_KEY = 'sketch2shape_history_v1';

function loadInitialHistory(): HistoryItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (e) {
    console.error('Failed to load history from localStorage', e);
  }
  return [];
}

export const useAppStore = create<AppState>((set, get) => ({
  activeTab: 'workspace',
  setActiveTab: (tab) => set({ activeTab: tab }),

  currentImageBase64: null,
  currentImageName: null,
  textPrompt: '',
  setTextPrompt: (prompt) => set({ textPrompt: prompt }),
  setCurrentImage: (b64, name = null) =>
    set({
      currentImageBase64: b64,
      currentImageName: name,
      // Clear downstream predictions on new image
      intelligence: null,
      overriddenCategory: null,
      intelligenceError: null,
    }),

  intelligence: null,
  isIntelligenceLoading: false,
  intelligenceError: null,
  overriddenCategory: null,
  setIntelligence: (data) => set({ intelligence: data }),
  setIntelligenceLoading: (loading) => set({ isIntelligenceLoading: loading }),
  setIntelligenceError: (err) => set({ intelligenceError: err }),
  setOverriddenCategory: (cat) => set({ overriddenCategory: cat }),

  selectedModel: 'auto',
  qualityPreset: 'balanced',
  exportFormats: ['glb', 'obj'],
  preprocessFirst: true,
  setSelectedModel: (model) => set({ selectedModel: model }),
  setQualityPreset: (preset) => set({ qualityPreset: preset }),
  setExportFormats: (formats) => set({ exportFormats: formats }),
  setPreprocessFirst: (pref) => set({ preprocessFirst: pref }),

  health: null,
  models: [],
  setHealth: (health) => set({ health }),
  setModels: (models) => set({ models }),

  currentMeshResult: null,
  activeGlbUrl: null,
  reconstructionStage: 'idle',
  reconstructionProgressMsg: '',
  reconstructionError: null,
  setReconstructionStage: (stage, msg = '') =>
    set({ reconstructionStage: stage, reconstructionProgressMsg: msg }),
  setCurrentMeshResult: (result, glbUrl = null) =>
    set({
      currentMeshResult: result,
      activeGlbUrl: glbUrl,
      // Reset refined state on new generation
      refinedGlbUrl: null,
      activeMeshVariant: 'original',
      meshComparison: null,
    }),
  setReconstructionError: (err) => set({ reconstructionError: err }),

  // Stage 9: Geometry Intelligence & Refinement
  geometryReport: null,
  isAnalyzingGeometry: false,
  meshComparison: null,
  isRefining: false,
  activeMeshVariant: 'original',
  refinedGlbUrl: null,
  pbrGlbUrl: null,
  setGeometryReport: (report) => set({ geometryReport: report }),
  setIsAnalyzingGeometry: (val) => set({ isAnalyzingGeometry: val }),
  setMeshComparison: (comp) => set({ meshComparison: comp }),
  setIsRefining: (val) => set({ isRefining: val }),
  setActiveMeshVariant: (variant) => set({ activeMeshVariant: variant }),
  setRefinedGlbUrl: (url) => set({ refinedGlbUrl: url }),
  setPbrGlbUrl: (url) => set({ pbrGlbUrl: url }),

  // Stage 11: PBR Texturing, Materials & Viewer Aesthetics
  visualStyle: 'realistic',
  selectedMaterial: null,
  lightingPreset: 'studio',
  backgroundPreset: 'dark',
  shadingMode: 'pbr',
  bundleZipUrl: null,
  printabilityReport: null,
  availableProviders: [],
  availableMaterials: [],
  setVisualStyle: (style) => set({ visualStyle: style }),
  setSelectedMaterial: (mat) => set({ selectedMaterial: mat }),
  setLightingPreset: (preset) => set({ lightingPreset: preset }),
  setBackgroundPreset: (preset) => set({ backgroundPreset: preset }),
  setShadingMode: (mode) => set({ shadingMode: mode }),
  setBundleZipUrl: (url) => set({ bundleZipUrl: url }),
  setPrintabilityReport: (report) => set({ printabilityReport: report }),
  setAvailableProviders: (providers) => set({ availableProviders: providers }),
  setAvailableMaterials: (mats) => set({ availableMaterials: mats }),


  wireframe: false,
  showGrid: true,
  autoRotate: false,
  setWireframe: (val) => set({ wireframe: val }),
  setShowGrid: (val) => set({ showGrid: val }),
  setAutoRotate: (val) => set({ autoRotate: val }),

  // Stage 10: Production Pipeline & Fallback Tracking
  pipelineJobId: null,
  pipelineStageHistory: [],
  peakVramMb: 0,
  fallbackOccurred: false,
  setPipelineJob: (jobId, history = [], peakVram = 0, fallback = false) =>
    set({
      pipelineJobId: jobId,
      pipelineStageHistory: history,
      peakVramMb: peakVram,
      fallbackOccurred: fallback,
    }),

  history: loadInitialHistory(),
  addToHistory: (item) => {
    const updated = [item, ...get().history].slice(0, 30);
    set({ history: updated });
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (e) {
      console.error('Failed to save history to localStorage', e);
    }
  },
  clearHistory: () => {
    set({ history: [] });
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {}
  },
}));
