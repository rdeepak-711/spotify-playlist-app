import { useState } from "react";
import api from "../utils/api";

export default function AuthButton() {
  const backend_url = import.meta.env.VITE_BACKEND_URL;
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleLogin = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Try fetch first
      try {
        const response = await fetch(`${backend_url}/login`, {
          method: "GET",
          credentials: "include",
          headers: {
            Accept: "application/json",
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.redirectUrl) {
          window.location.href = data.redirectUrl;
          return;
        }
      } catch (fetchError) {
        console.log("Fetch failed, trying axios...", fetchError);
        // If fetch fails, try axios as fallback
        const axiosResponse = await api.get("/login");

        if (axiosResponse.data && axiosResponse.data.redirectUrl) {
          window.location.href = axiosResponse.data.redirectUrl;
          return;
        }
      }

      throw new Error("No redirect URL received from server");
    } catch (error) {
      console.error("Login error:", error);
      console.error("Error details:", {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
      });
      setError(
        error.response?.data?.message ||
          error.message ||
          "Failed to connect to Spotify"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center">
      <button
        onClick={handleLogin}
        disabled={isLoading}
        className="bg-green-500 hover:bg-green-600 text-white font-semibold py-2 px-6 rounded shadow transition disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? "Connecting..." : "Connect with Spotify"}
      </button>
      {error && <p className="text-red-500 mt-2 text-sm">{error}</p>}
    </div>
  );
}
