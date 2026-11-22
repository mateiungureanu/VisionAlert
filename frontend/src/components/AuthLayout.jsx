import ThemeToggle from './ThemeToggle';
import { useTheme } from '../useTheme';

// The logo file lives in frontend/public. The image is zoomed in CSS (.auth-logo)
// because the source has a lot of empty margin around the symbol.
const LOGO_SRC = '/logo.jpg';

export default function AuthLayout({ title, wide = false, children }) {
  const { preference, setPreference } = useTheme();

  return (
    <div className="auth-page">
      <div className="auth-theme-switch">
        <ThemeToggle preference={preference} onChange={setPreference} />
      </div>
      <main className="auth-main">
        <div className="auth-brand">
          <span className="auth-logo-frame">
            <img className="auth-logo" src={LOGO_SRC} alt="" width="56" height="56" />
          </span>
          <span className="auth-brand-name">VisionAlert</span>
        </div>
        <p className="auth-tagline">Nicio ofertă bună nu-ți mai scapă</p>
        <section className={`auth-card${wide ? ' wide' : ''}`}>
          <h1 className="auth-title">{title}</h1>
          {children}
        </section>
      </main>
    </div>
  );
}
