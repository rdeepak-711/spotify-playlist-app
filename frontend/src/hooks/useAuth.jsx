import { useState, useEffect, createContext, useContext } from "react";
import axios from "axios";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const backend_url = import.meta.env.VITE_BACKEND_URL;

  useEffect(() => {
    console.log("AuthProvider: Checking authentication status");
    const checkAuth = async () => {
      try {
        // First check if we have a token in localStorage
        const token = localStorage.getItem("access_token");
        const spotify_user_id = localStorage.getItem("spotify_user_id");

        if (token && spotify_user_id) {
          console.log("AuthProvider: Found token and user ID in localStorage");
          // Verify the token with the backend
          const response = await axios.get(`${backend_url}/auth/me`);
          console.log(
            "AuthProvider: Backend auth check response:",
            response.data
          );

          if (response.data.success) {
            console.log("AuthProvider: Setting authenticated state to true");
            setIsAuthenticated(true);
            setUser({ spotify_user_id });
          } else {
            console.log("AuthProvider: Token invalid, clearing storage");
            localStorage.removeItem("access_token");
            localStorage.removeItem("spotify_user_id");
            setIsAuthenticated(false);
            setUser(null);
          }
        } else {
          console.log("AuthProvider: No token found in localStorage");
          setIsAuthenticated(false);
          setUser(null);
        }
      } catch (error) {
        console.error("AuthProvider: Error checking auth status:", error);
        setIsAuthenticated(false);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, [backend_url]);

  const login = async (token, spotify_user_id) => {
    console.log("AuthProvider: Logging in user");
    localStorage.setItem("access_token", token);
    localStorage.setItem("spotify_user_id", spotify_user_id);
    setIsAuthenticated(true);
    setUser({ spotify_user_id });
  };

  const logout = () => {
    console.log("AuthProvider: Logging out user");
    localStorage.removeItem("access_token");
    localStorage.removeItem("spotify_user_id");
    setIsAuthenticated(false);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        loading,
        user,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
