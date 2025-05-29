import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { getAuthData, isTokenExpired } from "../utils/secureStorage";

export default function HomePage() {
  const { isAuthenticated, loading, refreshToken } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const validateAndRedirect = async () => {
      if (!loading && isAuthenticated) {
        try {
          // Get the current auth data
          const authData = await getAuthData();
          if (!authData) {
            return; // No auth data found, stay on homepage
          }

          // Check if token is expired
          const tokenExpired = await isTokenExpired(authData.access_token);

          if (tokenExpired) {
            // Try to refresh the token
            const refreshSuccess = await refreshToken();
            if (!refreshSuccess) {
              return; // Token refresh failed, stay on homepage
            }
          }

          // Token is valid or was successfully refreshed, redirect to playlists
          navigate("/playlists", { replace: true });
        } catch (error) {
          console.error("Error validating authentication:", error);
          // Stay on homepage if there's an error
        }
      }
    };

    validateAndRedirect();
  }, [isAuthenticated, loading, navigate, refreshToken]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-400 to-blue-600">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-white"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-green-400 to-blue-600">
      <div className="text-center text-white">
        <h1 className="text-5xl font-bold mb-6">
          Welcome to Spotify Playlist Enricher
        </h1>
        <p className="text-xl mb-8">
          Organize and enrich your Spotify playlists with advanced filtering
        </p>
        <button
          onClick={() => navigate("/login")}
          className="bg-white text-green-600 font-semibold py-3 px-8 rounded-full hover:bg-opacity-90 transition"
        >
          Get Started
        </button>
      </div>
    </div>
  );
}
