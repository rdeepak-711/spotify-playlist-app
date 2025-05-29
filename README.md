# Spotify Playlist Enricher

A modern web application that enhances your Spotify playlists with advanced features, analytics, and enrichment capabilities.

## Features

- 🎵 View all your Spotify playlists in a beautiful, responsive grid
- 📊 Get insights about your music collection
- ✨ Enrich playlists with additional metadata
- 🔒 Secure authentication with Spotify
- 🎨 Modern, Spotify-inspired design system
- 📱 Fully responsive layout

## Tech Stack

### Frontend

- React with Vite
- Framer Motion for animations
- TailwindCSS for styling
- Axios for API calls
- React Router for navigation

### Backend

- FastAPI
- MongoDB with Motor (async driver)
- Anthropic's Claude API for enrichment
- Python 3.11+

## Getting Started

### Prerequisites

- Node.js 16+
- Python 3.11+
- MongoDB
- Spotify Developer Account
- Anthropic API Key

### Environment Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd spotify-playlist-app
```

2. Backend Setup:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the backend directory:

```env
CLIENT_ID=your_spotify_client_id
CLIENT_SECRET=your_spotify_client_secret
REDIRECT_URI=http://localhost:5000/callback
MONGODB_CONNECTION_URL=your_mongodb_url
FRONTEND_ORIGINS=http://localhost:5173
FRONTEND_URL=http://localhost:5173
ANTHROPIC_API_KEY=your_anthropic_api_key
FERNET_SECRET_KEY=your_fernet_key
```

3. Frontend Setup:

```bash
cd frontend
npm install
```

Create a `.env` file in the frontend directory:

```env
VITE_BACKEND_URL=http://localhost:5000
```

### Running the Application

1. Start the backend server:

```bash
cd backend
uvicorn main:app --reload --port 5000
```

2. Start the frontend development server:

```bash
cd frontend
npm run dev
```

The application will be available at `http://localhost:5173`

## Project Structure

### Frontend

```
frontend/
├── src/
│   ├── components/      # Reusable UI components
│   ├── hooks/          # Custom React hooks
│   ├── pages/          # Page components
│   ├── styles/         # Global styles and design tokens
│   ├── utils/          # Utility functions
│   ├── App.jsx         # Main app component
│   └── main.jsx        # Entry point
```

### Backend

```
backend/
├── core/              # Core business logic
├── database/          # Database models and operations
├── routes/           # API endpoints
├── config.py         # Configuration management
└── main.py          # FastAPI application setup
```

## Features in Development

- 👤 User profile page with credits system
- 📈 Advanced playlist analytics
- 🏷️ Custom tagging system
- 🎨 Theme customization
- 📱 Mobile app version

## Security

- Secure token management with encryption
- HTTP-only cookies for authentication
- CORS protection
- Rate limiting
- Input validation

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
