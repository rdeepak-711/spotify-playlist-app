import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../hooks/useAuth";

export default function CallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  const backend_url = import.meta.env.VITE_BACKEND_URL;

  useEffect(() => {
    console.log("CallbackPage: Starting callback handling");
    const handleCallback = async () => {
      try {
        const spotify_user_id = searchParams.get("spotify_user_id");
        console.log("CallbackPage: Received spotify_user_id:", spotify_user_id);

        if (!spotify_user_id) {
          console.error("CallbackPage: No spotify_user_id in URL");
          navigate("/login");
          return;
        }

        // Get user data from /me endpoint
        console.log("CallbackPage: Fetching user data from /me endpoint");
        const response = await axios.get(
          `${backend_url}/me?spotify_user_id=${spotify_user_id}`
        );
        console.log("CallbackPage: Backend response:", response.data);

        if (response.data.success) {
          const userData = response.data.user_data;
          console.log("CallbackPage: Saving access token");
          // Save the access token
          await login(userData.access_token, spotify_user_id);
          console.log("CallbackPage: Redirecting to playlists");
          navigate("/playlists");
        } else {
          console.error(
            "CallbackPage: Error in response:",
            response.data.message
          );
          navigate("/login");
        }
      } catch (error) {
        console.error("CallbackPage: Error handling callback:", error);
        navigate("/login");
      }
    };

    handleCallback();
  }, [searchParams, navigate, login, backend_url]);

  return (
    <div className="flex justify-center items-center min-h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
    </div>
  );
}
