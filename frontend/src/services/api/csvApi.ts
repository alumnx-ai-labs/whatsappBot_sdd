import { apiRequest } from './client';

export type CsvResult = {
  batchId: string;
  totalRows: number;
  accepted: number;
  rejected: number;
  rows: Array<{ rowNumber: number; outcome: string; reason?: string }>;
  ignoredColumns?: string[];
};

export function uploadCsv(file: File) {
  const data = new FormData();
  data.append('file', file);
  return apiRequest<CsvResult>('/metadata/csv', { method: 'POST', body: data });
}
