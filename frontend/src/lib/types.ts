export type DocumentRecord = {
  id: string;
  filename: string;
  document_type: string;
  mime_type?: string;
  status?: string;
  storage_path?: string;
  metadata_json?: Record<string, unknown>;
};

export type Citation = {
  source_id?: string;
  document_id?: string;
  chunk_id?: string;
  filename?: string;
  page?: number;
  text?: string;
  score?: number;
};

export type ChatResult = {
  answer?: string;
  citations?: Citation[];
  sources?: Citation[];
  uncertainty?: string[];
  grounded?: boolean;
  [key: string]: unknown;
};
