import PlaylistCard from "./PlaylistCard";

export default function PlaylistGrid({ playlists, onPlaylistClick }) {
  const sorted = [
    ...playlists.filter((p) => p.isLiked),
    ...playlists.filter((p) => !p.isLiked),
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 mt-8">
      {sorted.map((playlist, idx) => (
        <PlaylistCard
          key={playlist.playlist_spotify_id || idx}
          playlist={playlist}
          onClick={onPlaylistClick}
        />
      ))}
    </div>
  );
}
