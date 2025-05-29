import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "../hooks/useAuth";
import api from "../utils/api";
import PlaylistGrid from "../components/PlaylistGrid";

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
};

export default function PlaylistsPage() {
  const [playlists, setPlaylists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { user } = useAuth();

  useEffect(() => {
    const fetchPlaylists = async () => {
      if (!user?.spotify_user_id) {
        console.log("PlaylistsPage: No user ID available, skipping fetch");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const response = await api.get(
          `/me/playlists?spotify_user_id=${user.spotify_user_id}`
        );

        if (response.data.success) {
          // Check for invalid data before transformation
          const invalidData = response.data.details.filter(
            (playlist) =>
              !playlist.playlist_spotify_id || !playlist.playlist_name
          );
          if (invalidData.length > 0) {
            console.error(
              "PlaylistsPage: Invalid playlist data found:",
              invalidData
            );
          }

          const transformedPlaylists = response.data.details; // Data is already transformed by backend
          setPlaylists(transformedPlaylists);
        } else {
          console.error(
            "PlaylistsPage: Error in response:",
            response.data.message
          );
          setError(response.data.message);
        }
      } catch (err) {
        console.error(
          "PlaylistsPage: Error fetching playlists:",
          err.response ? err.response.data : err.message
        );
        setError(err.response?.data?.message || "Failed to fetch playlists");
      } finally {
        setLoading(false);
      }
    };

    fetchPlaylists();
  }, [user]);

  const handlePlaylistClick = useCallback((playlist) => {
    console.log("Playlist clicked:", playlist);
    // Add your playlist click handling logic here
    // For example, navigate to a playlist detail page
  }, []);

  if (error) {
    return (
      <motion.div
        className="flex flex-col items-center justify-center min-h-screen bg-[var(--spotify-black)] text-[var(--text-primary)] p-[var(--spacing-md)] pt-16"
        variants={pageVariants}
        initial="initial"
        animate="animate"
        exit="exit"
      >
        <div className="bg-[var(--surface-light)] rounded-[var(--radius-lg)] p-[var(--spacing-xl)] max-w-md w-full text-center">
          <svg
            className="w-12 h-12 text-red-500 mx-auto mb-[var(--spacing-md)]"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <h2 className="text-xl font-bold mb-2">Error Loading Playlists</h2>
          <p className="text-[var(--text-secondary)]">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-[var(--spacing-md)] px-[var(--spacing-md)] py-[var(--spacing-sm)] bg-[var(--spotify-green)] text-[var(--text-primary)] rounded-[var(--radius-full)] hover:bg-[var(--spotify-green-hover)] transition-colors"
          >
            Try Again
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className="min-h-screen bg-[var(--spotify-black)] text-[var(--text-primary)] pt-16"
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      {/* Header Section */}
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-to-b from-[var(--spotify-green)] via-[var(--surface-light)] to-[var(--spotify-black)] opacity-20" />
        <div className="relative container mx-auto px-[var(--spacing-md)] py-[var(--spacing-xl)]">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="max-w-4xl mx-auto"
          >
            <h1 className="text-4xl font-bold mb-[var(--spacing-sm)] text-[var(--spotify-green)]">
              Your Playlists
            </h1>
            <p className="text-[var(--text-secondary)] text-lg">
              Discover and manage your music collection
            </p>
          </motion.div>
        </div>
      </div>

      {/* Content Section */}
      <div className="container mx-auto py-[var(--spacing-xl)]">
        <div className="max-w-7xl mx-auto">
          {/* Stats Section */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-[var(--spacing-md)] mb-[var(--spacing-xl)] px-[var(--spacing-md)]">
            {[
              {
                label: "Total Playlists",
                value: playlists.length,
                icon: "📝",
                color: "var(--spotify-green)",
              },
              {
                label: "Enriched Playlists",
                value: playlists.filter((p) => p.is_enriched).length,
                icon: "✨",
                color: "var(--spotify-green-hover)",
              },
              {
                label: "Total Tracks",
                value: playlists.reduce(
                  (acc, p) => acc + p.playlist_tracks_count,
                  0
                ),
                icon: "🎵",
                color: "var(--spotify-green)",
              },
            ].map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + index * 0.1 }}
                className="bg-[var(--surface-light)] rounded-[var(--radius-lg)] p-[var(--spacing-md)] border-l-4"
                style={{ borderColor: stat.color }}
              >
                <div className="flex items-center space-x-[var(--spacing-sm)]">
                  <span className="text-2xl">{stat.icon}</span>
                  <div>
                    <h3 className="text-sm text-[var(--text-secondary)]">
                      {stat.label}
                    </h3>
                    <p
                      className="text-2xl font-bold"
                      style={{ color: stat.color }}
                    >
                      {stat.value}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Playlists Grid */}
          <PlaylistGrid
            playlists={playlists}
            onPlaylistClick={handlePlaylistClick}
            isLoading={loading}
          />
        </div>
      </div>
    </motion.div>
  );
}
