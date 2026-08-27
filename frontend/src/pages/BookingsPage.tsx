import { useEffect, useState } from 'react';
import { useAuth } from '../auth/AuthContext';
import { getConfirmedBookings, type Booking } from '../services/api/bookingsApi';

export function BookingsPage() {
  const { signOut } = useAuth();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  async function load(refresh = false) {
    refresh ? setRefreshing(true) : setLoading(true);
    setError('');
    try {
      const result = await getConfirmedBookings();
      setBookings(result.bookings);
    } catch {
      setError('Unable to load confirmed bookings.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => { void load(); }, []);

  return (
    <main className="shell">
      <header className="topbar"><div><p className="eyebrow">OPERATIONS</p><h1>Confirmed bookings</h1></div><div className="actions"><button onClick={() => void load(true)} disabled={refreshing}>{refreshing ? 'Refreshing...' : 'Refresh'}</button><button className="quiet" onClick={() => void signOut()}>Sign out</button></div></header>
      {loading && <p className="state">Loading bookings...</p>}
      {error && <div className="state error"><p>{error}</p><button onClick={() => void load()}>Try again</button></div>}
      {!loading && !error && bookings.length === 0 && <p className="state">No confirmed bookings yet.</p>}
      {!loading && !error && bookings.length > 0 && <section className="table-wrap"><table><thead><tr><th>Customer</th><th>Phone</th><th>Business</th><th>Date</th><th>Time</th><th>Location</th><th>Status</th><th>Created</th></tr></thead><tbody>{bookings.map((booking) => <tr key={booking.id}><td>{booking.customerName}</td><td>{booking.customerPhone}</td><td>{booking.businessName}</td><td>{booking.meetingDate}</td><td>{booking.meetingTime}</td><td>{booking.location}</td><td><span className="status">{booking.status}</span></td><td>{new Date(booking.createdAt).toLocaleString()}</td></tr>)}</tbody></table></section>}
    </main>
  );
}
