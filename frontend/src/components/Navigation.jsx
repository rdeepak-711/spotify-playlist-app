import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function Navigation() {
  const location = useLocation();
  const { logout } = useAuth();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="fixed top-0 left-0 right-0 z-[var(--z-modal)] bg-[var(--spotify-black)] bg-opacity-95 backdrop-blur-sm border-b border-[var(--surface-light)]">
      <div className="container mx-auto px-[var(--spacing-md)]">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link
            to="/playlists"
            className="text-[var(--spotify-green)] font-bold text-xl"
          >
            Spotify Enricher
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-[var(--spacing-md)]">
            <Link
              to="/playlists"
              className={`px-3 py-2 rounded-full transition-colors ${
                isActive("/playlists")
                  ? "bg-[var(--spotify-green)] text-[var(--text-primary)]"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
            >
              Playlists
            </Link>
            <Link
              to="/profile"
              className={`px-3 py-2 rounded-full transition-colors ${
                isActive("/profile")
                  ? "bg-[var(--spotify-green)] text-[var(--text-primary)]"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
            >
              Profile
            </Link>
            <button
              onClick={logout}
              className="px-3 py-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
