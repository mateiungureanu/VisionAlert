import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../AuthContext';

export default function ProtectedRoute({ children }) {
  const { token, loading } = useAuth();
  const location = useLocation();
  if (loading) return <p className="center">Se încarcă...</p>;
  return token
    ? children
    : <Navigate to="/login" replace state={{ from: location }} />;
}