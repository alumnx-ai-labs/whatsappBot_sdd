import { FormEvent, useEffect, useState } from 'react';
import { listMetadata, saveMetadata, type Metadata } from '../services/api/metadataApi';

const empty: Metadata = { businessName: '', contactPerson: '', whatsappPhone: '', address: '', sector: '', businessDescription: '' };

export function MetadataPage() {
  const [records, setRecords] = useState<Metadata[]>([]);
  const [form, setForm] = useState<Metadata>(empty);
  const [editingId, setEditingId] = useState<string>();
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => { listMetadata().then((result) => setRecords(result.records)).catch(() => setError('Unable to load metadata.')); }, []);

  function update(field: keyof Metadata, value: string) { setForm((current) => ({ ...current, [field]: value })); }
  async function submit(event: FormEvent) {
    event.preventDefault(); setError(''); setMessage('');
    if (!form.businessName || !form.contactPerson || !form.whatsappPhone) { setError('Business name, contact person, and WhatsApp phone are required.'); return; }
    try {
      const result = await saveMetadata(form, editingId);
      setRecords((current) => editingId ? current.map((item) => item.id === editingId ? result.record : item) : [...current, result.record]);
      setForm(empty); setEditingId(undefined); setMessage(`${result.outcome.toLowerCase()} successfully.`);
    } catch { setError('Metadata could not be saved. Check the submitted values.'); }
  }

  return <main className="shell"><header className="topbar"><div><p className="eyebrow">DIRECTORY</p><h1>Business metadata</h1></div></header><section className="admin-grid"><form className="panel" onSubmit={submit}><h2>{editingId ? 'Update record' : 'Add record'}</h2>{(['businessName', 'contactPerson', 'whatsappPhone', 'address', 'sector', 'businessDescription'] as const).map((field) => <label key={field}>{field.replace(/[A-Z]/g, (letter) => ` ${letter}`).replace(/^./, (letter) => letter.toUpperCase())}<input value={form[field] ?? ''} onChange={(event) => update(field, event.target.value)} required={['businessName', 'contactPerson', 'whatsappPhone'].includes(field)} /></label>)}{error && <p className="error">{error}</p>}{message && <p className="success">{message}</p>}<button>Save metadata</button></form><section className="panel"><h2>Saved records</h2>{records.length === 0 ? <p className="state">No metadata records yet.</p> : records.map((record) => <article className="record" key={record.id}><strong>{record.businessName}</strong><span>{record.contactPerson} · {record.whatsappPhone}</span><button className="quiet" onClick={() => { setEditingId(record.id); setForm(record); }}>Edit</button></article>)}</section></section></main>;
}
