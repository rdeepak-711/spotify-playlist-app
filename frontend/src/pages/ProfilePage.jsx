import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useAuth } from "../hooks/useAuth";
import api from "../utils/api";

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
};

export default function ProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await api.get(
          `/me?spotify_user_id=${user.spotify_user_id}`
        );
        if (response.data.success) {
          setProfile(response.data.user_data);
        } else {
          setError("Failed to load profile data");
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (user?.spotify_user_id) {
      fetchProfile();
    }
  }, [user]);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-[var(--spotify-black)] pt-16">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[var(--spotify-green)]"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[var(--spotify-black)] text-[var(--text-primary)] p-[var(--spacing-md)] pt-16">
        <div className="container mx-auto">
          <div className="bg-[var(--surface-light)] rounded-[var(--radius-lg)] p-[var(--spacing-md)] text-center">
            <p className="text-red-500">{error}</p>
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
      {/* Header with profile info */}
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-to-b from-[var(--spotify-green)] via-[var(--surface-light)] to-[var(--spotify-black)] opacity-20" />
        <div className="relative container mx-auto px-[var(--spacing-md)] py-[var(--spacing-xl)]">
          <div className="max-w-4xl mx-auto flex items-center gap-[var(--spacing-xl)]">
            {/* Profile Picture */}
            <div className="relative">
              <img
                src={profile?.profile_picture || "/default-avatar.png"}
                alt={profile?.username}
                className="w-32 h-32 rounded-full border-4 border-[var(--spotify-green)]"
              />
              <div className="absolute -bottom-2 -right-2 bg-[var(--spotify-green)] text-white p-2 rounded-full">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                  />
                </svg>
              </div>
            </div>

            {/* Profile Info */}
            <div>
              <h1 className="text-4xl font-bold mb-2">
                {profile?.username || "User"}
              </h1>
              <p className="text-[var(--text-secondary)] mb-4">
                {profile?.email}
              </p>
              <div className="flex items-center gap-[var(--spacing-md)]">
                <span className="bg-[var(--spotify-green)] px-3 py-1 rounded-full text-sm font-medium">
                  {profile?.credits || 0} Credits
                </span>
                <span className="bg-[var(--surface-light)] px-3 py-1 rounded-full text-sm font-medium">
                  {profile?.country || "Unknown"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content Section */}
      <div className="container mx-auto py-[var(--spacing-xl)]">
        <div className="max-w-4xl mx-auto">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-[var(--spacing-md)] mb-[var(--spacing-xl)]">
            {[
              {
                label: "Available Credits",
                value: profile?.credits || 0,
                icon: "💎",
                color: "var(--spotify-green)",
              },
              {
                label: "Enriched Playlists",
                value: "Coming Soon",
                icon: "✨",
                color: "var(--spotify-green-hover)",
              },
              {
                label: "Member Since",
                value: new Date(profile?.created_at).toLocaleDateString(),
                icon: "📅",
                color: "var(--spotify-green)",
              },
            ].map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * index }}
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
                      className="text-xl font-bold"
                      style={{ color: stat.color }}
                    >
                      {stat.value}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Credits Section */}
          <div className="bg-[var(--surface-light)] rounded-[var(--radius-lg)] p-[var(--spacing-xl)]">
            <h2 className="text-2xl font-bold mb-[var(--spacing-md)]">
              Get More Credits
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-[var(--spacing-md)]">
              <motion.div
                whileHover={{ scale: 1.02 }}
                className="bg-gradient-to-br from-[var(--spotify-green)] to-[var(--spotify-green-hover)] p-[var(--spacing-md)] rounded-[var(--radius-lg)] cursor-pointer"
              >
                <h3 className="text-xl font-bold mb-2">Basic Package</h3>
                <p className="text-[var(--text-secondary)] mb-4">
                  Perfect for personal use
                </p>
                <ul className="space-y-2 mb-6">
                  <li className="flex items-center">
                    <svg
                      className="w-5 h-5 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    100 Credits
                  </li>
                  <li className="flex items-center">
                    <svg
                      className="w-5 h-5 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    Valid for 30 days
                  </li>
                </ul>
                <button className="w-full bg-white text-[var(--spotify-green)] font-bold py-2 rounded-full hover:bg-opacity-90 transition">
                  Get Started
                </button>
              </motion.div>

              <motion.div
                whileHover={{ scale: 1.02 }}
                className="bg-gradient-to-br from-purple-500 to-blue-600 p-[var(--spacing-md)] rounded-[var(--radius-lg)] cursor-pointer"
              >
                <h3 className="text-xl font-bold mb-2">Pro Package</h3>
                <p className="text-[var(--text-secondary)] mb-4">
                  For power users
                </p>
                <ul className="space-y-2 mb-6">
                  <li className="flex items-center">
                    <svg
                      className="w-5 h-5 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    500 Credits
                  </li>
                  <li className="flex items-center">
                    <svg
                      className="w-5 h-5 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    Valid for 90 days
                  </li>
                </ul>
                <button className="w-full bg-white text-blue-600 font-bold py-2 rounded-full hover:bg-opacity-90 transition">
                  Upgrade Now
                </button>
              </motion.div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
