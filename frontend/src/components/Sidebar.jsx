import { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { useTheme } from '../useTheme';
import ThemeToggle from './ThemeToggle';

const ICON = {
  width: 18,
  height: 18,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  'aria-hidden': true,
};

const HomeIcon = () => (
  <svg {...ICON}><path d="M3 11l9-8 9 8" /><path d="M5 10v10h5v-6h4v6h5V10" /></svg>
);
const BrandsIcon = () => (
  <svg {...ICON}>
    <path d="M4 9l1.5-5h13L20 9" />
    <path d="M4 9a2.67 2.67 0 0 0 5.33 0 2.67 2.67 0 0 0 5.34 0A2.67 2.67 0 0 0 20 9" />
    <path d="M5 12v8h14v-8" />
    <path d="M10 20v-4h4v4" />
  </svg>
);
const SubscriptionsIcon = () => (
  <svg {...ICON}><path d="M18 8a6 6 0 1 0-12 0c0 7-3 8-3 8h18s-3-1-3-8" /><path d="M13.7 20a2 2 0 0 1-3.4 0" /></svg>
);
const UserIcon = () => (
  <svg {...ICON}><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 3.6-7 8-7s8 3 8 7" /></svg>
);
const LogoutIcon = () => (
  <svg {...ICON}><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="M16 17l5-5-5-5M21 12H9" /></svg>
);
const ChevronIcon = () => (
  <svg {...ICON} width="14" height="14"><path d="M6 9l6 6 6-6" /></svg>
);

const SECTIONS = [
  {
    title: 'Oferte',
    items: [
      { to: '/', label: 'Acasă', icon: <HomeIcon />, match: (path) => path === '/' },
      {
        to: '/brands',
        label: 'Brandurile urmărite',
        icon: <BrandsIcon />,
        match: (path) => path.startsWith('/brands') || path.startsWith('/offers'),
      },
    ],
  },
  {
    title: 'Gestionare',
    items: [
      {
        to: '/subscriptions',
        label: 'Abonamente',
        icon: <SubscriptionsIcon />,
        match: (path) => path.startsWith('/subscriptions'),
      },
    ],
  },
];

function UserMenu({ onNavigate }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    function handlePointerDown(event) {
      if (rootRef.current && !rootRef.current.contains(event.target)) setOpen(false);
    }
    function handleKeyDown(event) {
      if (event.key === 'Escape') setOpen(false);
    }
    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open]);

  const displayName = user?.username || 'Cont';
  const initial = displayName[0]?.toUpperCase() ?? '?';

  function handleLogout() {
    setOpen(false);
    logout();
    navigate('/login');
  }

  return (
    <div className="user-menu" ref={rootRef}>
      {open && (
        <div className="user-menu-popover" role="menu">
          <Link
            className="user-menu-item"
            to="/profile"
            role="menuitem"
            onClick={() => {
              setOpen(false);
              onNavigate?.();
            }}
          >
            <UserIcon /> Profil
          </Link>
          <button className="user-menu-item" type="button" role="menuitem" onClick={handleLogout}>
            <LogoutIcon /> Deconectare
          </button>
        </div>
      )}
      <button
        className="user-menu-trigger"
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <span className="user-avatar" aria-hidden="true">{initial}</span>
        <span className="user-name">{displayName}</span>
        <ChevronIcon />
      </button>
    </div>
  );
}

export default function Sidebar({ open, onNavigate }) {
  const { pathname } = useLocation();
  const { preference, setPreference } = useTheme();

  return (
    <aside className={`app-sidebar${open ? ' open' : ''}`}>
      <Link className="sidebar-brand" to="/" onClick={onNavigate}>
        <span className="sidebar-logo-frame">
          <img className="sidebar-logo" src="/logo.jpg" alt="" width="40" height="40" />
        </span>
        <span>
          <span className="sidebar-brand-name">VisionAlert</span>
          <span className="sidebar-tagline">Nicio ofertă bună nu-ți mai scapă</span>
        </span>
      </Link>

      <nav className="sidebar-nav" aria-label="Navigare principală">
        {SECTIONS.map((section) => (
          <div className="sidebar-section" key={section.title}>
            <p className="sidebar-section-title">{section.title}</p>
            {section.items.map((item) => (
              <Link
                className={`sidebar-link${item.match(pathname) ? ' active' : ''}`}
                key={item.to}
                to={item.to}
                aria-current={item.match(pathname) ? 'page' : undefined}
                onClick={onNavigate}
              >
                {item.icon}
                {item.label}
              </Link>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <UserMenu onNavigate={onNavigate} />
        <ThemeToggle preference={preference} onChange={setPreference} />
      </div>
    </aside>
  );
}
