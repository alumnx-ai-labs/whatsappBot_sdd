import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuth } from './AuthContext';

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { session, loading } = useAuth();
  if (loading) return <main className="state">Checking session...</main>;
  if (!session?.authenticated) return <Navigate to="/login" replace />;
  return children;
}
