import type { ChatResult, DocumentRecord } from './types';

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000/api/v1';

async function request<T>(path: string, options: RequestInit = {}, retries = 2): Promise<T> {
  let last: unknown;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: { Accept: 'application/json', ...(options.headers ?? {}) },
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data?.detail ?? `Request failed (${response.status})`);
      return data as T;
    } catch (error) {
      last = error;
      if (attempt < retries) await new Promise(r => setTimeout(r, 350 * (attempt + 1)));
    }
  }
  throw last instanceof Error ? last : new Error('Request failed');
}

export function uploadDocument(file: File, onProgress?: (value: number) => void): Promise<DocumentRecord> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE}/upload`);
    xhr.responseType = 'json';
    xhr.upload.onprogress = e => {
      if (e.lengthComputable) onProgress?.(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve(xhr.response);
      else reject(new Error(xhr.response?.detail ?? `Upload failed (${xhr.status})`));
    };
    xhr.onerror = () => reject(new Error('Network error during upload'));
    const body = new FormData();
    body.append('file', file);
    xhr.send(body);
  });
}

export const ingestDocument = (id: string) =>
  request<Record<string, unknown>>(`/ingest/${id}`, { method: 'POST' });

export const analyzeImage = (id: string) =>
  request<Record<string, unknown>>(`/vision/${id}`, { method: 'POST' });

export const sendChat = (message: string, imageId?: string): Promise<ChatResult> =>
  request<ChatResult>('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, image_id: imageId }),
  });

export const listDocuments = () =>
  request<{ items?: DocumentRecord[] } | DocumentRecord[]>('/documents');

export const getReadiness = () =>
  request<Record<string, unknown>>('/system/ready');

export const getJob = (id: string) => request<Record<string, any>>(`/jobs/${id}`);

export const enqueueIngestion = (id: string) => request<Record<string, any>>(`/ingest/${id}/async`, { method: 'POST' });

export const cancelJob = (id: string) => request<Record<string, any>>(`/jobs/${id}/cancel`, { method: 'POST' });

export const getDiagnostics = () => request<Record<string, any>>('/system/diagnostics');

export const getCompliance = () => request<Record<string, any>>('/system/compliance');

export const checkPolicy = (dataClass: string, actor: string, purpose: string, consentGranted = false, admin = false) => request<Record<string, any>>(`/system/policy/check?data_class=${encodeURIComponent(dataClass)}&actor=${encodeURIComponent(actor)}&purpose=${encodeURIComponent(purpose)}&consent_granted=${consentGranted}&admin=${admin}`, { method: 'POST' });

export const exportPolicy = (actor: string, purpose: string, consentGranted = false, admin = false) => request<Record<string, any>>(`/system/policy/export?actor=${encodeURIComponent(actor)}&purpose=${encodeURIComponent(purpose)}&consent_granted=${consentGranted}&admin=${admin}`, { method: 'POST' });

export const getRecovery = () => request<Record<string, any>>('/system/recovery');

export const getReleaseReadiness = () => request<Record<string, any>>('/system/release-readiness');

export const getReleaseManifest = () => request<Record<string, any>>('/system/release');

export const getApiContract = () => request<Record<string, any>>('/system/contract');

export const getIncidentCenter = () => request<Record<string, any>>('/system/incident-center');

export const getPreflight = () => request<Record<string, any>>('/system/preflight');
