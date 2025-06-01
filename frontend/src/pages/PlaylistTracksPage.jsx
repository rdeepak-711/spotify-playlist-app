import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "../hooks/useAuth";
import api from "../utils/api";
import PlaylistTracksTable from "../components/PlaylistTracksTable";

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
};

const defaultPlaylistImage = "/default_playlist.jpg";

export default function PlaylistTracksPage() {
  const { playlistId } = useParams();
  const [playlist, setPlaylist] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { user } = useAuth();

  useEffect(() => {
    const fetchPlaylistAndTracks = async () => {
      try {
        setLoading(true);

        // First get the playlist details - this should be fast as it's from DB
        const response = await api.get(
          `/me/playlists/${playlistId}?spotify_user_id=${user.spotify_user_id}`
        );

        if (response.data.success) {
          setPlaylist(response.data.data);

          // Then trigger the background fetch of tracks
          api
            .post(
              `/me/playlists/${playlistId}/fetch-tracks?spotify_user_id=${user.spotify_user_id}`
            )
            .catch((err) => {
              console.error(
                "Background fetch error:",
                err.response?.data || err.message
              );
            });
        } else {
          setError(response.data.message);
        }
      } catch (err) {
        console.error("Error:", err.response?.data || err.message);
        setError(err.response?.data?.message || err.message);
      } finally {
        setLoading(false);
      }
    };

    if (user?.spotify_user_id && playlistId) {
      fetchPlaylistAndTracks();
    }
  }, [playlistId, user]);

  const handleEnhanceClick = async (trackIds) => {
    try {
      const response = await api.post(`/me/playlists/${playlistId}/enhance`, {
        track_ids: trackIds,
        spotify_user_id: user.spotify_user_id,
      });

      if (response.data.success) {
        // Refresh the tracks table
        window.location.reload();
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--spotify-black)] text-[var(--text-primary)] pt-16">
        <div className="container mx-auto p-[var(--spacing-md)]">
          <div className="animate-pulse">
            <div className="h-32 bg-[var(--surface-light)] rounded-lg mb-8"></div>
            <div className="h-64 bg-[var(--surface-light)] rounded-lg"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[var(--spotify-black)] text-[var(--text-primary)] pt-16">
        <div className="container mx-auto p-[var(--spacing-md)]">
          <div className="bg-red-100 text-red-500 p-4 rounded-lg">
            Error: {error}
          </div>
        </div>
      </div>
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
            {playlist && (
              <div className="flex items-center space-x-6">
                {playlist.playlist_dp && (
                  <img
                    src={playlist.playlist_dp || defaultPlaylistImage}
                    alt={playlist.playlist_name}
                    className="w-32 h-32 rounded-lg shadow-lg"
                  />
                )}
                <div>
                  <h1 className="text-4xl font-bold mb-[var(--spacing-sm)] text-[var(--spotify-green)]">
                    {playlist.playlist_name}
                  </h1>
                  {playlist.playlist_description && (
                    <p className="text-[var(--text-secondary)] text-lg mb-2">
                      {playlist.playlist_description}
                    </p>
                  )}
                  <p className="text-[var(--text-secondary)]">
                    {playlist.playlist_tracks_count} tracks
                    {playlist.is_enriched && (
                      <span className="ml-2 text-[var(--spotify-green)]">
                        • Enriched
                      </span>
                    )}
                  </p>
                </div>
              </div>
            )}
          </motion.div>
        </div>
      </div>

      {/* Content Section */}
      <div className="container mx-auto py-[var(--spacing-xl)]">
        <div className="max-w-7xl mx-auto px-[var(--spacing-md)]">
          <PlaylistTracksTable
            playlistId={playlistId}
            onEnhanceClick={handleEnhanceClick}
          />
        </div>
      </div>
    </motion.div>
  );
}
