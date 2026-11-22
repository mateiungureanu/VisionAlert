import { useEffect, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { pathname } = useLocation();

  useEffect(() => {
    // Close the mobile drawer after every navigation.
    const timer = setTimeout(() => setMenuOpen(false), 0);
    return () => clearTimeout(timer);
  }, [pathname]);

  return (
    <div className="app-shell">
      <header className="app-topbar">
        <button
          className="app-topbar-button"
          type="button"
          aria-label="Deschide meniul"
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((current) => !current)}
        >
          ☰
        </button>
        <span className="app-topbar-name">VisionAlert</span>
      </header>
      <Sidebar open={menuOpen} onNavigate={() => setMenuOpen(false)} />
      {menuOpen && (
        <button
          className="app-scrim"
          type="button"
          aria-label="Închide meniul"
          onClick={() => setMenuOpen(false)}
        />
      )}
      <div className="app-content">
        <Outlet />
      </div>
    </div>
  );
}
