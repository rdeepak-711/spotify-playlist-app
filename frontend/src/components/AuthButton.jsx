import axios from "axios";
import { useState } from "react";

export default function AuthButton() {
  const backend_url = import.meta.env.VITE_BACKEND_URL;
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async () => {
    try {
      setIsLoading(true);
      // Get the Spotify auth URL
      const response = await axios.get(`${backend_url}/login`);

      if (response.data && response.data.redirectUrl) {
        // Redirect to Spotify auth
        window.location.href = response.data.redirectUrl;
      } else {
        console.error(
          "AuthButton: No redirect URL in response. Response data:",
          response.data
        );
      }
    } catch (error) {
      console.error(
        "AuthButton: Login failed:",
        error.response ? error.response.data : error.message
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button
      onClick={handleLogin}
      disabled={isLoading}
      className="bg-green-500 hover:bg-green-600 text-white font-semibold py-2 px-6 rounded shadow transition disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {isLoading ? "Connecting..." : "Connect with Spotify"}
    </button>
  );
}
