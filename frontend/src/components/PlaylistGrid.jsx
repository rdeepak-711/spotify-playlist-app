import PlaylistCard from "./PlaylistCard";
import { useMemo } from "react";

export default function PlaylistGrid({ playlists, onPlaylistClick }) {
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
  }, [playlists]); // Only re-sort when playlists change

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 mt-8">
      {sorted.map((playlist) => {
        const key = playlist.playlist_spotify_id;
        if (!key) {
          console.error("Playlist missing ID:", playlist);
        }
        return (
          <PlaylistCard
            key={key}
            playlist={playlist}
            onClick={onPlaylistClick}
          />
        );
      })}
    </div>
  );
}
