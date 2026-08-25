import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import * as authApi from '../services/api/authApi';

export type AuthContextValue = {
  session: authApi.AdminSession | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<authApi.AdminSession | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    authApi
      .getSession()
      .then(setSession)
      .catch(() => setSession({ authenticated: false }))
      .finally(() => setLoading(false));
  }, []);

  async function signIn(email: string, password: string) {
    const profile = await authApi.login(email, password);
    setSession({ authenticated: true, ...profile });
  }

  async function signOut() {
    await authApi.logout();
    setSession({ authenticated: false });
  }

  return <AuthContext.Provider value={{ session, loading, signIn, signOut }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
