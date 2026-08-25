import { ChangeEvent, useState } from 'react';
import { uploadCsv, type CsvResult } from '../services/api/csvApi';

export function CsvUploadPage() {
  const [result, setResult] = useState<CsvResult>();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  async function onChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]; if (!file) return;
    setLoading(true); setError(''); setResult(undefined);
    try { setResult(await uploadCsv(file)); } catch { setError('The CSV could not be processed.'); } finally { setLoading(false); }
  }
  return <main className="shell"><header className="topbar"><div><p className="eyebrow">IMPORT</p><h1>Upload metadata CSV</h1></div></header><section className="panel upload"><p>Select a UTF-8 CSV with businessName, contactPerson, and whatsappPhone columns.</p><input type="file" accept=".csv,text/csv" onChange={onChange} />{loading && <p className="state">Processing upload...</p>}{error && <p className="error">{error}</p>}{result && <><p className="success">Processed {result.totalRows} rows: {result.accepted} accepted, {result.rejected} rejected.</p><table><thead><tr><th>Row</th><th>Outcome</th><th>Reason</th></tr></thead><tbody>{result.rows.map((row) => <tr key={row.rowNumber}><td>{row.rowNumber}</td><td>{row.outcome}</td><td>{row.reason ?? '—'}</td></tr>)}</tbody></table></>}</section></main>;
}
