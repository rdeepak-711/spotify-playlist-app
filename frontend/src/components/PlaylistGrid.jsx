import { useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import PlaylistCard from "./PlaylistCard";
import Skeleton from "./Skeleton";

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

export default function PlaylistGrid({ playlists, isLoading }) {
  // Memoize the sorted playlists to prevent unnecessary re-renders
  const sorted = useMemo(() => {
    const sortedPlaylists = [
      ...playlists.filter((p) => p.playlist_spotify_id === "liked_songs"),
      ...playlists.filter((p) => p.playlist_spotify_id !== "liked_songs"),
    ];

    // Debug: Check for duplicate or missing playlist IDs
    const playlistIds = new Set();
    const duplicateIds = new Set();
    const invalidPlaylists = [];

    sortedPlaylists.forEach((playlist, index) => {
      const id = playlist.playlist_spotify_id;
      if (!id) {
        invalidPlaylists.push({ index, playlist });
      } else if (playlistIds.has(id)) {
        duplicateIds.add(id);
      } else {
        playlistIds.add(id);
      }
    });

    if (invalidPlaylists.length > 0) {
      console.error("Playlists with missing IDs:", invalidPlaylists);
    }
    if (duplicateIds.size > 0) {
      console.error("Duplicate playlist IDs found:", Array.from(duplicateIds));
    }

    return sortedPlaylists;
  }, [playlists]);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-[var(--spacing-md)] p-[var(--spacing-md)]">
        {[...Array(8)].map((_, i) => (
          <Skeleton
            key={i}
            className="aspect-square rounded-[var(--radius-lg)]"
          />
        ))}
      </div>
    );
  }

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-[var(--spacing-md)] p-[var(--spacing-md)]"
    >
      <AnimatePresence>
        {sorted.map((playlist, index) => (
          <PlaylistCard
            key={playlist.playlist_spotify_id}
            playlist={playlist}
            index={index}
          />
        ))}
      </AnimatePresence>
    </motion.div>
  );
}
