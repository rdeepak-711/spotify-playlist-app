import { useEffect, useState, useCallback } from "react";
import { useAuth } from "../hooks/useAuth";
import api from "../utils/api";
import PlaylistGrid from "../components/PlaylistGrid";

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

          // Transform the data to match the SpotifyUserPlaylistDetails model
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
  }, []); // No dependencies since it's just logging

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Your Playlists</h1>
      {playlists.length === 0 ? (
        <p className="text-gray-500">No playlists found.</p>
      ) : (
        <PlaylistGrid
          playlists={playlists}
          onPlaylistClick={handlePlaylistClick}
        />
      )}
    </div>
  );
}
