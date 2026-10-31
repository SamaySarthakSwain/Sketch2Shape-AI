/**
 * Core TypeScript Type Definitions for Sketch2Shape AI Frontend
 * Matches FastAPI backend contracts in Stage 5, Stage 6, and Stage 7.
 */

export interface PredictionCandidate {
  category: string;
  confidence: number;
}

export interface SketchIntelligenceResponse {
  predicted_category: string;
  top_prediction_confidence: number;
  top_5_predictions: PredictionCandidate[];
  is_ambiguous: boolean;
  margin_to_second: number;
  geometric_tags: string[];
  semantic_description: string;
  reconstruction_hints: {
    recommended_mode: string;
    prompt_template: string;
    aspect_ratio?: number;
    symmetry_prior?: boolean;
    orientation?: string;
  };
  preprocessing_summary?: Record<string, any>;
  inference_time_ms: number;
}

export interface ModelInfo {
  name: string;
  display_name: string;
  category: string;
  vram_required_gb: number;
  supports_texture: boolean;
  supports_text_conditioning: boolean;
  is_available: boolean;
  status_message: string;
}

export interface ReconstructionHealth {
  status: string;
  gpu_available: boolean;
  gpu_name: string;
  vram_total_gb: number;
  vram_free_gb: number;
  available_models: string[];
  all_registered_models: string[];
}

export interface MeshQualityReport {
  is_valid: boolean;
  error?: string | null;
  vertices: number;
  faces: number;
  is_watertight: boolean;
  euler_characteristic: number;
  components: number;
  degenerate_faces?: number;
  duplicate_vertices?: number;
  surface_area?: number;
  volume?: number | null;
  dimensions_xyz?: [number, number, number];
  bounding_box_min?: [number, number, number];
  bounding_box_max?: [number, number, number];
  file_path?: string;
  file_size_bytes?: number;
}

export interface ReconstructionResult {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  model_used?: string;
  inference_time_seconds?: number;
  vertices?: number;
  faces?: number;
  mesh_valid?: boolean;
  is_watertight?: boolean;
  formats?: Record<string, string>;
  downloads?: Record<string, string>;
  quality_report?: MeshQualityReport;
  error?: string | null;
}

export interface HistoryItem {
  id: string;
  timestamp: string;
  thumbnailUrl: string;
  category: string;
  confidence: number;
  modelUsed: string;
  vertices: number;
  faces: number;
  isWatertight: boolean;
  glbUrl: string;
  objUrl?: string;
  qualityReport?: MeshQualityReport;
}

export type ReconstructionStage = 
  | 'idle'
  | 'uploading'
  | 'analyzing'
  | 'preparing'
  | 'generating'
  | 'processing'
  | 'exporting'
  | 'completed'
  | 'failed';

// ==========================================
// STAGE 9: Geometry Intelligence & Refinement
// ==========================================

export interface TopologyMetrics {
  vertex_count: number;
  face_count: number;
  edge_count: number;
  is_watertight: boolean;
  is_volume: boolean;
  euler_characteristic: number;
  connected_components: number;
  boundary_edges_count: number;
  non_manifold_edges_count: number;
  duplicate_vertices_count: number;
  degenerate_faces_count: number;
  is_manifold: boolean;
}

export interface SurfaceMetrics {
  surface_area: number;
  volume: number | null;
  is_volume_valid: boolean;
  normal_consistency: boolean;
  inverted_normals_count: number;
  mean_curvature_estimate: number;
  gaussian_curvature_estimate: number;
  surface_roughness_std: number;
}

export interface SpatialMetrics {
  bounding_box_min: [number, number, number];
  bounding_box_max: [number, number, number];
  dimensions_xyz: [number, number, number];
  aspect_ratios: Record<string, number>;
  center_of_mass: [number, number, number];
  principal_extents: [number, number, number];
  approximate_symmetry_scores: {
    x_plane: number;
    y_plane: number;
    z_plane: number;
  };
}

export interface StructuralMetrics {
  component_sizes: number[];
  isolated_fragments_count: number;
  has_unexpected_protrusions: boolean;
  max_protrusion_distance: number;
  thin_structures_detected: boolean;
}

export interface TextureMetrics {
  has_vertex_colors: boolean;
  has_uv_coordinates: boolean;
  has_texture_image: boolean;
  texture_resolution: [number, number] | null;
  material_type: string;
  texture_mode: 'vertex_colored' | 'uv_mapped' | 'untextured_clay' | 'uv_without_texture';
  texture_status_message: string;
}

export interface ViewSilhouetteMetric {
  view_name: string;
  camera_eye: [number, number, number];
  camera_target: [number, number, number];
  occupancy_ratio: number;
  silhouette_pixels: number;
  rendered_image_path?: string;
  iou_with_sketch?: number | null;
}

export interface MultiViewMetrics {
  views: Record<string, ViewSilhouetteMetric>;
  front_sketch_iou?: number | null;
  cross_view_continuity_score: number;
  asymmetry_detected: boolean;
  structural_completeness_score: number;
}

export interface DefectReport {
  has_defects: boolean;
  defect_count: number;
  non_manifold_edges: number;
  boundary_holes: number;
  degenerate_triangles: number;
  duplicate_vertices: number;
  isolated_fragments: number;
  non_finite_coordinates: number;
  unoriented_normals: boolean;
  defect_list: string[];
}

export interface QualitySubscores {
  topology: number;
  geometry: number;
  surface: number;
  multiview?: number | null;
  texture: number;
  export: number;
}

export interface QualityScore {
  overall_score: number;
  subscores: QualitySubscores;
  warnings: string[];
  detected_defects: string[];
  recommendations: string[];
  confidence_level: 'high' | 'moderate' | 'heuristic_only';
}

export interface MeshComparison {
  asset_id: string;
  operation: string;
  duration_seconds: number;
  original_vertices: number;
  refined_vertices: number;
  vertex_delta: number;
  original_faces: number;
  refined_faces: number;
  face_delta: number;
  original_watertight: boolean;
  refined_watertight: boolean;
  original_surface_area: number;
  refined_surface_area: number;
  original_file_size_bytes: number;
  refined_file_size_bytes: number;
  is_degraded: boolean;
  summary: string;
}

export interface GeometryReport {
  asset_id: string;
  source_file: string;
  timestamp: number;
  topology: TopologyMetrics;
  surface: SurfaceMetrics;
  spatial: SpatialMetrics;
  structural: StructuralMetrics;
  texture: TextureMetrics;
  multiview?: MultiViewMetrics | null;
  defects: DefectReport;
  quality: QualityScore;
}

export interface RefineResponse {
  asset_id: string;
  status: string;
  preset: string;
  comparison: MeshComparison;
  downloads: Record<string, string>;
  refined_mesh_metrics: {
    vertices: number;
    faces: number;
    is_watertight: boolean;
    surface_area: number;
  };
}
