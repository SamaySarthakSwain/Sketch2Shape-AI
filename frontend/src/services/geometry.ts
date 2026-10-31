import { request } from './api';
import { GeometryReport, MeshComparison, RefineResponse } from '../types';

export interface AnalyzeMeshPayload {
  mesh_path?: string;
  asset_id?: string;
  run_multiview?: boolean;
  sketch_path?: string;
}

export interface RefineMeshPayload {
  mesh_path?: string;
  asset_id?: string;
  preset: 'fast' | 'balanced' | 'high';
  remove_isolated_shards?: boolean;
  export_formats?: string[];
}

export async function analyzeMeshGeometry(payload: AnalyzeMeshPayload): Promise<GeometryReport> {
  return request<GeometryReport>('/api/v1/geometry/analyze', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function refineMeshGeometry(payload: RefineMeshPayload): Promise<RefineResponse> {
  return request<RefineResponse>('/api/v1/geometry/refine', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getGeometryReport(assetId: string): Promise<GeometryReport> {
  return request<GeometryReport>(`/api/v1/geometry/report/${assetId}`);
}

export async function getGeometryComparison(assetId: string): Promise<MeshComparison> {
  return request<MeshComparison>(`/api/v1/geometry/compare/${assetId}`);
}
