import { useState, useEffect, useCallback } from "react";
// import { motion } from 'framer-motion';
import { useAuth } from "../hooks/useAuth";
import api from "../utils/api";

const TRACKS_PER_PAGE = 50;

const PlaylistTracksTable = ({ playlistId, onEnhanceClick }) => {
  const [tracks, setTracks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);
  const [selectedTracks, setSelectedTracks] = useState([]);
  const [userCredits, setUserCredits] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const [isFetching, setIsFetching] = useState(false);
  const [contributorProfiles, setContributorProfiles] = useState({});
  const { user } = useAuth();

  // Function to fetch contributor profile
  const fetchContributorProfile = useCallback(
    async (contributorId) => {
      try {
        // Check if we already tried to fetch this profile
        if (contributorProfiles[contributorId]?.error) {
          return; // Don't retry failed fetches
        }

        const response = await api.get(`/users/${contributorId}/profile`);
        if (response.data.success) {
          setContributorProfiles((prev) => ({
            ...prev,
            [contributorId]: response.data.data,
          }));
        } else {
          // Mark this profile as failed to prevent retries
          setContributorProfiles((prev) => ({
            ...prev,
            [contributorId]: { error: true },
          }));
        }
      } catch (err) {
        console.error(
          `Error fetching contributor profile ${contributorId}:`,
          err
        );
        // Mark this profile as failed to prevent retries
        setContributorProfiles((prev) => ({
          ...prev,
          [contributorId]: { error: true },
        }));
      }
    },
    [contributorProfiles]
  );

  // Function to fetch all missing contributor profiles
  const fetchMissingContributorProfiles = useCallback(
    (tracksData) => {
      const missingContributors = tracksData
        .filter(
          (track) =>
            track.contributor && !contributorProfiles[track.contributor]
        )
        .map((track) => track.contributor);

      // Remove duplicates
      const uniqueMissingContributors = [...new Set(missingContributors)];

      // Fetch each missing contributor's profile
      uniqueMissingContributors.forEach((contributorId) => {
        fetchContributorProfile(contributorId);
      });
    },
    [contributorProfiles, fetchContributorProfile]
  );

  const fetchTracks = useCallback(
    async (currentOffset = 0, append = false) => {
      try {
        const loadingState = append ? setLoadingMore : setLoading;
        loadingState(true);

        const response = await api.get(
          `/me/playlists/${playlistId}/tracks/details?spotify_user_id=${user.spotify_user_id}&offset=${currentOffset}&limit=${TRACKS_PER_PAGE}`
        );

        if (response.data.success) {
          const newTracks = response.data.data.tracks;
          setTracks((prev) => (append ? [...prev, ...newTracks] : newTracks));
          setUserCredits(response.data.data.user_credits);
          setHasMore(response.data.data.has_more);
          setOffset(currentOffset + TRACKS_PER_PAGE);

          // Fetch missing contributor profiles
          fetchMissingContributorProfiles(newTracks);

          // If tracks are being fetched in the background, start polling
          if (response.data.data.is_fetching) {
            setIsFetching(true);
            // Poll every 3 seconds until we get some tracks
            setTimeout(() => {
              fetchTracks(0, false);
            }, 3000);
          } else {
            setIsFetching(false);
          }
        } else {
          setError(response.data.message);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        const loadingState = append ? setLoadingMore : setLoading;
        loadingState(false);
      }
    },
    [playlistId, user, fetchMissingContributorProfiles]
  );

  useEffect(() => {
    if (user?.spotify_user_id && playlistId) {
      fetchTracks(0, false);
    }
  }, [playlistId, user, fetchTracks]);

  const handleLoadMore = () => {
    if (!loadingMore && hasMore) {
      fetchTracks(offset, true);
    }
  };

  const handleTrackSelect = (trackId) => {
    setSelectedTracks((prev) => {
      const isSelected = prev.includes(trackId);
      if (isSelected) {
        return prev.filter((id) => id !== trackId);
      } else {
        return [...prev, trackId];
      }
    });
  };

  const handleEnhanceClick = () => {
    if (selectedTracks.length >= 10) {
      onEnhanceClick(selectedTracks);
    }
  };

  if (loading && tracks.length === 0) {
    return (
      <div className="animate-pulse">
        <div className="h-12 bg-[var(--surface-light)] rounded-lg mb-4"></div>
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="h-20 bg-[var(--surface-light)] rounded-lg mb-2"
          ></div>
        ))}
      </div>
    );
  }

  if (error && tracks.length === 0) {
    return (
      <div className="text-red-500 p-4 rounded-lg bg-red-100">
        Error loading tracks: {error}
      </div>
    );
  }

  if (isFetching && tracks.length === 0) {
    return (
      <div className="text-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[var(--spotify-green)] mx-auto mb-4"></div>
        <p className="text-[var(--text-secondary)]">
          Fetching tracks from Spotify...
        </p>
        <p className="text-sm text-[var(--text-secondary)] mt-2">
          This might take a moment for large playlists
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="bg-[var(--surface-light)] text-[var(--text-secondary)]">
            {userCredits > 0 && (
              <th className="p-4 text-left">
                <input
                  type="checkbox"
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedTracks(
                        tracks
                          .filter((t) => !t.is_enriched)
                          .map((t) => t.track_id)
                      );
                    } else {
                      setSelectedTracks([]);
                    }
                  }}
                  className="rounded border-[var(--text-secondary)]"
                />
              </th>
            )}
            <th className="p-4 text-left">Track</th>
            <th className="p-4 text-left">Artists</th>
            <th className="p-4 text-left">Album</th>
            <th className="p-4 text-left">Genre</th>
            <th className="p-4 text-left">Language</th>
            <th className="p-4 text-left">Contributor</th>
            <th className="p-4 text-left">Actions</th>
          </tr>
        </thead>
        <tbody>
          {tracks.map((track) => (
            <tr
              key={track.track_id}
              className="border-b border-[var(--surface-light)] hover:bg-[var(--surface-light)] transition-colors"
            >
              {userCredits > 0 && (
                <td className="p-4">
                  {!track.is_enriched && (
                    <input
                      type="checkbox"
                      checked={selectedTracks.includes(track.track_id)}
                      onChange={() => handleTrackSelect(track.track_id)}
                      className="rounded border-[var(--text-secondary)]"
                    />
                  )}
                </td>
              )}
              <td className="p-4">
                <div className="flex items-center space-x-3">
                  <img
                    src={track.album_image}
                    alt={track.album_name}
                    className="w-12 h-12 rounded object-cover"
                  />
                  <div>
                    <a
                      href={track.external_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium hover:text-[var(--spotify-green)]"
                    >
                      {track.name}
                    </a>
                    {track.preview_url && (
                      <audio controls className="mt-2 w-32 h-8">
                        <source src={track.preview_url} type="audio/mpeg" />
                      </audio>
                    )}
                  </div>
                </div>
              </td>
              <td className="p-4">{track.artists.join(", ")}</td>
              <td className="p-4">{track.album_name}</td>
              <td className="p-4">
                {track.is_enriched ? (
                  <div>
                    {track.genre[0] && (
                      <span className="block">{track.genre[0]}</span>
                    )}
                    {track.genre[1] && (
                      <span className="text-sm text-[var(--text-secondary)]">
                        {track.genre[1]}
                      </span>
                    )}
                  </div>
                ) : (
                  <span className="text-[var(--text-secondary)]">
                    Not enriched
                  </span>
                )}
              </td>
              <td className="p-4">
                {track.is_enriched ? (
                  track.language
                ) : (
                  <span className="text-[var(--text-secondary)]">
                    Not enriched
                  </span>
                )}
              </td>
              <td className="p-4">
                {track.contributor ? (
                  contributorProfiles[track.contributor] ? (
                    !contributorProfiles[track.contributor].error ? (
                      <a
                        href={
                          contributorProfiles[track.contributor]
                            .user_external_url
                        }
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center space-x-2 group"
                      >
                        <div className="relative">
                          <img
                            src={
                              contributorProfiles[track.contributor]
                                .profile_picture
                            }
                            alt={
                              contributorProfiles[track.contributor].username
                            }
                            className="w-8 h-8 rounded-full object-cover transition-transform group-hover:scale-110"
                          />
                          <div className="absolute inset-0 rounded-full border-2 border-[var(--spotify-green)] opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                        <span className="text-[var(--text-primary)] group-hover:text-[var(--spotify-green)] transition-colors">
                          {contributorProfiles[track.contributor].username}
                        </span>
                      </a>
                    ) : (
                      <span className="text-[var(--text-secondary)]">
                        Profile unavailable
                      </span>
                    )
                  ) : (
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 rounded-full bg-[var(--surface-light)] animate-pulse" />
                      <div className="w-20 h-4 bg-[var(--surface-light)] animate-pulse rounded" />
                    </div>
                  )
                ) : (
                  <span className="text-[var(--text-secondary)]">-</span>
                )}
              </td>
              <td className="p-4">
                {!track.is_enriched && userCredits > 0 && (
                  <button
                    onClick={() => onEnhanceClick([track.track_id])}
                    className="px-3 py-1 bg-[var(--spotify-green)] text-white rounded hover:bg-[var(--spotify-green-hover)] transition-colors"
                  >
                    Enhance
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {hasMore && (
        <div className="mt-4 text-center">
          <button
            onClick={handleLoadMore}
            disabled={loadingMore}
            className="px-6 py-2 bg-[var(--spotify-green)] text-white rounded-full hover:bg-[var(--spotify-green-hover)] transition-colors disabled:opacity-50"
          >
            {loadingMore ? "Loading more tracks..." : "Load More Tracks"}
          </button>
        </div>
      )}

      {userCredits > 0 && selectedTracks.length > 0 && (
        <div className="fixed bottom-4 right-4 bg-[var(--surface-light)] p-4 rounded-lg shadow-lg">
          <p className="mb-2">
            {selectedTracks.length} tracks selected
            {selectedTracks.length < 10 && (
              <span className="text-[var(--text-secondary)]">
                {" "}
                (minimum 10 required)
              </span>
            )}
          </p>
          <button
            onClick={handleEnhanceClick}
            disabled={selectedTracks.length < 10}
            className={`px-4 py-2 rounded ${
              selectedTracks.length >= 10
                ? "bg-[var(--spotify-green)] hover:bg-[var(--spotify-green-hover)]"
                : "bg-[var(--surface-dark)] cursor-not-allowed"
            } text-white transition-colors`}
          >
            Enhance Selected ({Math.ceil(selectedTracks.length / 10)} credits)
          </button>
        </div>
      )}
    </div>
  );
};

export default PlaylistTracksTable;
