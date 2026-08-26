import { apiRequest } from './client';

export type Metadata = {
  id?: string;
  businessName: string;
  contactPerson: string;
  whatsappPhone: string;
  address?: string;
  sector?: string;
  businessDescription?: string;
};

export function listMetadata() {
  return apiRequest<{ records: Metadata[] }>('/metadata');
}

export function saveMetadata(data: Metadata, id?: string) {
  return apiRequest<{ outcome: string; record: Metadata }>(id ? `/metadata/${id}` : '/metadata', {
    method: id ? 'PUT' : 'POST',
    body: JSON.stringify(data)
  });
}
