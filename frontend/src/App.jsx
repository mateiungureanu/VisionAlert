import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import Home from './pages/Home';
import BrandOffers from './pages/BrandOffers';
import Profile from './pages/Profile';
import BrandSubscriptions from './pages/BrandSubscriptions';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
      <Route path="/offers" element={<ProtectedRoute><Home /></ProtectedRoute>} />
      <Route path="/offers/:brandId" element={<ProtectedRoute><BrandOffers /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" />} />
      <Route path="/subscriptions" element={<ProtectedRoute><BrandSubscriptions /></ProtectedRoute>} />
    </Routes>
  );
}