import { motion } from "framer-motion";

const defaultPlaylistImage = "/default_playlist.jpg";

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

export default function PlaylistCard({ playlist, onClick }) {
  const isLikedSongs = playlist.name === "Liked Songs";

  return (
    <motion.div
      variants={item}
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      className={`
        bg-[var(--surface-light)] rounded-[var(--radius-lg)] p-[var(--spacing-md)]
        cursor-pointer transition-shadow hover:shadow-[var(--shadow-lg)]
        ${isLikedSongs ? "bg-gradient-to-br from-[var(--spotify-purple)] to-[var(--spotify-blue)]" : ""}
      `}
    >
      <div className="aspect-square mb-[var(--spacing-sm)]">
        <img
          src={playlist.playlist_dp || defaultPlaylistImage}
          alt={playlist.playlist_name}
          className="w-full h-full object-cover rounded-[var(--radius-md)]"
          onError={(e) => {
            e.target.src = defaultPlaylistImage;
          }}
        />
      </div>
      <h3 className="font-bold text-[var(--text-primary)] truncate">
        {playlist.name}
      </h3>
      <p className="text-sm text-[var(--text-secondary)] truncate">
        {playlist.tracks?.total || playlist.playlist_tracks_count || 0} tracks
      </p>
    </motion.div>
  );
}
