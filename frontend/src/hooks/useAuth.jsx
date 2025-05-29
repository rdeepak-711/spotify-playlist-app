import { useState, useEffect, createContext, useContext } from "react";
import api from "../utils/api";
import {
  saveAuthData,
  getAuthData,
  clearAuthData,
} from "../utils/secureStorage";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);

  const refreshToken = async () => {
    try {
      const authData = await getAuthData();
      if (!authData?.spotify_user_id) return false;

      const response = await api.post("/refresh-token", {
        spotify_user_id: authData.spotify_user_id,
      });

      if (response.data.success) {
        // Save the new auth data with updated access token
        await saveAuthData({
          ...authData,
          access_token: response.data.access_token,
        });
        return true;
      }
      return false;
    } catch (error) {
      console.error("Token refresh failed:", error);
      return false;
    }
  };

  const checkAuth = async () => {
    try {
      const authData = await getAuthData();

      if (!authData) {
        setIsAuthenticated(false);
        setUser(null);
        return;
      }

      // Try to verify the token with backend
      const response = await api.get("/auth/me");

      if (response.data.success) {
        setIsAuthenticated(true);
        setUser({ spotify_user_id: authData.spotify_user_id });
      } else {
        const refreshed = await refreshToken();
        if (!refreshed) {
          await clearAuthData();
          setIsAuthenticated(false);
          setUser(null);
        } else {
          // If refresh was successful, set authenticated state
          setIsAuthenticated(true);
          setUser({ spotify_user_id: authData.spotify_user_id });
        }
      }
    } catch (error) {
      console.error("AuthProvider: Auth check failed:", error);
      // Try token refresh on error
      const refreshed = await refreshToken();
      if (!refreshed) {
        await clearAuthData();
        setIsAuthenticated(false);
        setUser(null);
      } else {
        // If refresh was successful, set authenticated state
        const authData = await getAuthData();
        if (authData) {
          setIsAuthenticated(true);
          setUser({ spotify_user_id: authData.spotify_user_id });
        }
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const login = async (access_token, spotify_user_id) => {
    const authData = {
      access_token,
      spotify_user_id,
      timestamp: Date.now(),
    };

    try {
      await saveAuthData(authData);
      setIsAuthenticated(true);
      setUser({ spotify_user_id });
    } catch (error) {
      console.error("AuthProvider: Login failed:", error);
      setIsAuthenticated(false);
      setUser(null);
    }
  };

  const logout = async () => {
    try {
      await clearAuthData();
      setIsAuthenticated(false);
      setUser(null);
    } catch (error) {
      console.error("AuthProvider: Logout failed:", error);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        loading,
        user,
        login,
        logout,
        refreshToken,
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
