import AuthButton from "../components/AuthButton";

export default function LoginPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-green-400 to-blue-600">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
        <h1 className="text-3xl font-bold mb-4 text-gray-800">
          Welcome to Spotify Playlist Enricher
        </h1>
        <p className="mb-6 text-gray-600">
          Connect your Spotify account to organize, filter and enrich your
          playlists
        </p>
        <AuthButton />
      </div>
    </div>
  );
}
