import { useEffect, useState } from "react";
import axios from "axios";
import { useAuth } from "../hooks/useAuth";

export default function PlaylistsPage() {
  const [playlists, setPlaylists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { user } = useAuth();
  const backend_url = import.meta.env.VITE_BACKEND_URL;

  useEffect(() => {
    console.log("PlaylistsPage: Component mounted");
    console.log("PlaylistsPage: Current user state:", user);

    const fetchPlaylists = async () => {
      if (!user?.spotify_user_id) {
        console.log("PlaylistsPage: No user ID available, skipping fetch");
        setLoading(false);
        return;
      }

      console.log(
        "PlaylistsPage: Fetching playlists for user:",
        user.spotify_user_id
      );
      try {
        setLoading(true);
        const response = await axios.get(
          `${backend_url}/me/playlists?spotify_user_id=${user.spotify_user_id}`
        );
        console.log("PlaylistsPage: Backend response:", response.data);

        if (response.data.success) {
          console.log("PlaylistsPage: Setting playlists data");
          setPlaylists(response.data.details);
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
  }, [user, backend_url]);

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

  console.log("PlaylistsPage: Rendering with playlists:", playlists);

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Your Playlists</h1>
      {playlists.length === 0 ? (
        <p className="text-gray-500">No playlists found.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {playlists.map((playlist) => (
            <div
              key={playlist.id}
              className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow"
            >
              {playlist.images && playlist.images[0] && (
                <img
                  src={playlist.images[0].url}
                  alt={playlist.name}
                  className="w-full h-48 object-cover"
                />
              )}
              <div className="p-4">
                <h2 className="text-xl font-semibold mb-2">{playlist.name}</h2>
                <p className="text-gray-600">
                  {playlist.tracks?.total || 0} tracks
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
