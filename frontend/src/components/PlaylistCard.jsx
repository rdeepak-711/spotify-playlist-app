import { motion } from "framer-motion";

export default function PlaylistCard({ playlist, onClick }) {
  const defaultImage = "/default_playlist.jpeg"; // Make sure to add this image to your public folder
  const isLikedSongs = playlist.playlist_spotify_id === "liked_songs";

  return (
    <motion.div
      whileHover={{ scale: 1.05, boxShadow: "0 8px 32px rgba(0,0,0,0.15)" }}
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`cursor-pointer bg-white rounded-lg shadow-md p-4 flex flex-col items-center ${
        isLikedSongs ? "border-2 border-green-400" : ""
      }`}
      onClick={() => onClick(playlist)}
    >
      <div className="w-24 h-24 mb-3 flex items-center justify-center bg-gray-100 rounded-full overflow-hidden">
        {isLikedSongs ? (
          <svg
            className="w-12 h-12 text-green-500"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" />
          </svg>
        ) : (
          <img
            src={playlist.playlist_dp || defaultImage}
            alt={playlist.playlist_name}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = defaultImage;
            }}
          />
        )}
      </div>
      <h3 className="text-lg font-semibold text-gray-800 text-center line-clamp-2">
        {playlist.playlist_name}
      </h3>
      <p className="text-sm text-gray-500">
        {playlist.playlist_tracks_count}{" "}
        {playlist.playlist_tracks_count === 1 ? "track" : "tracks"}
      </p>
      {playlist.is_enriched && (
        <span className="mt-2 px-2 py-1 text-xs bg-green-100 text-green-700 rounded">
          Enriched
        </span>
      )}
    </motion.div>
  );
}
