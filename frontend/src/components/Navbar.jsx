import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const initials = user
    ? `${user.first_name?.[0] ?? ''}${user.last_name?.[0] ?? ''}`.toUpperCase()
    : '?';

  return (
    <nav className="navbar">
      <Link to="/" className="brand">VisionAlert</Link>
      <div className="nav-right">
        <Link to="/">Ofertele mele</Link>
        <Link to="/subscriptions">Abonamente</Link>
        <Link to="/profile" className="avatar" title="Profilul meu">{initials}</Link>
        <button onClick={() => { logout(); navigate('/login'); }}>Logout</button>
      </div>
    </nav>
  );
}