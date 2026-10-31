/**
 * Pipeline V1 API Service
 * Coordinates end-to-end async job submission, stage polling, results retrieval, and cancellation.
 */

import { request } from './api';

export interface PipelineGeneratePayload {
  image_b64?: string;
  image_path?: string;
  preferred_model: 'auto' | 'instantmesh' | 'procedural' | string;
  quality_preset: 'fast' | 'balanced' | 'high' | 'ultra_fast';
  preprocess_first: boolean;
  auto_refine: boolean;
  refine_preset: 'fast' | 'balanced' | 'high';
  export_formats: string[];
  allow_fallback: boolean;
  category_override?: string;
  async_execution?: boolean;
}

export interface PipelineStageRecord {
  stage: string;
  start_time: number;
  end_time?: number;
  duration_seconds: number;
  success: boolean;
  message: string;
  artifacts?: Record<string, string>;
  metadata?: Record<string, any>;
  error?: string;
}

export interface PipelineStatusResponse {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
  current_stage: string;
  stage_history: PipelineStageRecord[];
  created_at: number;
  updated_at: number;
  total_duration_seconds: number;
  peak_vram_mb: number;
  is_cancelled: boolean;
  error?: string;
}

export interface PipelineResultResponse extends PipelineStatusResponse {
  config: Record<string, any>;
  artifacts: Record<string, any>;
  web_artifacts: Record<string, string>;
  metrics: {
    total_duration_seconds?: number;
    peak_vram_mb?: number;
    overall_quality_score?: number;
    predicted_category?: string;
    model_used?: string;
    fallback_occurred?: boolean;
    original_vertices?: number;
    original_faces?: number;
  };
}

export async function submitPipelineJob(payload: PipelineGeneratePayload): Promise<{
  status: string;
  job_id: string;
  current_stage: string;
  created_at: number;
  status_url: string;
  result_url: string;
  cancel_url: string;
}> {
  return request('/api/v1/pipeline/generate', {
    method: 'POST',
    body: JSON.stringify({ ...payload, async_execution: true }),
  });
}

export async function submitPipelineSync(payload: PipelineGeneratePayload): Promise<PipelineResultResponse> {
  return request('/api/v1/pipeline/generate', {
    method: 'POST',
    body: JSON.stringify({ ...payload, async_execution: false }),
  });
}

export async function getPipelineStatus(jobId: string): Promise<PipelineStatusResponse> {
  return request<PipelineStatusResponse>(`/api/v1/pipeline/status/${jobId}`);
}

export async function getPipelineResult(jobId: string): Promise<PipelineResultResponse> {
  return request<PipelineResultResponse>(`/api/v1/pipeline/result/${jobId}`);
}

export async function cancelPipelineJob(jobId: string): Promise<{ job_id: string; status: string; message: string }> {
  return request(`/api/v1/pipeline/cancel/${jobId}`, {
    method: 'POST',
  });
}

export async function listPipelineJobs(limit = 20): Promise<{ count: number; jobs: any[] }> {
  return request(`/api/v1/pipeline/jobs?limit=${limit}`);
}

export async function fetchProviders(): Promise<any> {
  return request('/api/v1/pipeline/providers');
}

export async function fetchMaterials(category?: string): Promise<any> {
  const query = category ? `?category=${encodeURIComponent(category)}` : '';
  return request(`/api/v1/pipeline/materials${query}`);
}

export async function fetchStyles(): Promise<any> {
  return request('/api/v1/pipeline/styles');
}

export async function retextureJob(
  jobId: string,
  visualStyle: string,
  materialOverride?: string | null
): Promise<PipelineResultResponse> {
  return request<PipelineResultResponse>(`/api/v1/pipeline/retexture/${jobId}`, {
    method: 'POST',
    body: JSON.stringify({
      visual_style: visualStyle,
      material_override: materialOverride,
    }),
  });
}

export function getBundleDownloadUrl(jobId: string): string {
  return `/api/v1/pipeline/download/bundle/${jobId}`;
}

