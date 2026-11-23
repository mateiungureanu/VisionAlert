import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './components/AppLayout';
import Login from './pages/Login';
import Register from './pages/Register';
import Home from './pages/Home';
import FollowedBrands from './pages/FollowedBrands';
import BrandOffers from './pages/BrandOffers';
import FavoriteOffers from './pages/FavoriteOffers';
import Profile from './pages/Profile';
import BrandSubscriptions from './pages/BrandSubscriptions';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route path="/" element={<Home />} />
        <Route path="/brands" element={<FollowedBrands />} />
        <Route path="/offers" element={<Navigate to="/brands" replace />} />
        <Route path="/offers/:brandId" element={<BrandOffers />} />
        <Route path="/favorite-offers" element={<FavoriteOffers />} />
        <Route path="/subscriptions" element={<BrandSubscriptions />} />
        <Route path="/profile" element={<Profile />} />
      </Route>
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}
