import { request } from './api';
import { ModelInfo, ReconstructionHealth, ReconstructionResult } from '../types';

export interface GenerateMeshPayload {
  image_path?: string;
  image_b64?: string;
  model_name?: string;
  quality_preset: 'fast' | 'balanced' | 'high' | 'ultra_fast';
  export_formats: string[];
  preprocess_first: boolean;
  metadata?: Record<string, any>;
  async_job?: boolean;
}

export async function getReconstructionHealth(): Promise<ReconstructionHealth> {
  return request<ReconstructionHealth>('/api/v1/reconstruction/health');
}

export async function getReconstructionModels(): Promise<{ count: number; models: ModelInfo[] }> {
  return request<{ count: number; models: ModelInfo[] }>('/api/v1/reconstruction/models');
}

export async function generate3DMesh(payload: GenerateMeshPayload): Promise<ReconstructionResult> {
  return request<ReconstructionResult>('/api/v1/reconstruction/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getJobStatus(jobId: string): Promise<{
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  result?: any;
  error?: string;
}> {
  return request(`/api/v1/reconstruction/result/${jobId}`);
}
