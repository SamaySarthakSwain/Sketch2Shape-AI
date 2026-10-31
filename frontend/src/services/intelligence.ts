import { request } from './api';
import { SketchIntelligenceResponse } from '../types';

export async function analyzeSketch(
  fileOrBase64: File | string,
  bypassPreprocessing = false
): Promise<SketchIntelligenceResponse> {
  const formData = new FormData();
  if (typeof fileOrBase64 === 'string') {
    formData.append('image_base64', fileOrBase64);
  } else {
    formData.append('file', fileOrBase64);
  }
  formData.append('bypass_preprocessing', String(bypassPreprocessing));

  return request<SketchIntelligenceResponse>('/api/v1/intelligence/analyze', {
    method: 'POST',
    body: formData,
  });
}

export async function analyzePrompt(prompt: string): Promise<any> {
  return request<any>('/api/v1/intelligence/analyze-prompt', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ prompt }),
  });
}
