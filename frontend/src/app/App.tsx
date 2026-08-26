import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '../auth/AuthContext';
import { ProtectedRoute } from '../auth/ProtectedRoute';
import { BookingsPage } from '../pages/BookingsPage';
import { CsvUploadPage } from '../pages/CsvUploadPage';
import { LoginPage } from '../pages/LoginPage';
import { MetadataPage } from '../pages/MetadataPage';
import './styles.css';

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/bookings" element={<ProtectedRoute><BookingsPage /></ProtectedRoute>} />
          <Route path="/metadata" element={<ProtectedRoute><MetadataPage /></ProtectedRoute>} />
          <Route path="/metadata/csv" element={<ProtectedRoute><CsvUploadPage /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/bookings" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
