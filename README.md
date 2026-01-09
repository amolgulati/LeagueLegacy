# Fantasy League History Tracker

A unified fantasy league history tracker that combines data from Yahoo Fantasy and Sleeper into one place with rich statistics and an eye-catching UI.

## Features

- **Multi-Platform Support**: Import data from both Yahoo Fantasy and Sleeper
- **Owner Tracking**: Link the same person across platforms and seasons
- **Rich Statistics**: Career records, head-to-head rivalries, trade history
- **Hall of Fame**: Celebrate your league's champions
- **League Records**: Track all-time bests and records

## Tech Stack

- **Backend**: Python with FastAPI
- **Frontend**: React with Vite and Tailwind CSS
- **Database**: SQLite with SQLAlchemy
- **Charts**: Recharts for visualizations

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your configuration (see Environment Variables section)

uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Frontend Setup

```bash
cd frontend
npm install

# Copy and configure environment variables
cp .env.example .env
# Edit .env if needed (see Environment Variables section)

npm run dev
```

The frontend will be available at `http://localhost:5173`.

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `YAHOO_CLIENT_ID` | Yahoo OAuth2 Client ID | *Required for Yahoo import* |
| `YAHOO_CLIENT_SECRET` | Yahoo OAuth2 Client Secret | *Required for Yahoo import* |
| `YAHOO_REDIRECT_URI` | OAuth2 callback URL | `http://localhost:8000/api/yahoo/auth/callback` |
| `FRONTEND_URL` | Frontend URL for OAuth redirects | `http://localhost:5173` |
| `CORS_ORIGINS` | Comma-separated allowed CORS origins | `http://localhost:5173` |

#### Setting up Yahoo API Credentials

1. Go to [Yahoo Developer Console](https://developer.yahoo.com/apps/create/)
2. Create a new app with the following settings:
   - Application Type: **Web Application**
   - Redirect URI: `http://localhost:8000/api/yahoo/auth/callback`
   - API Permissions: **Fantasy Sports (Read)**
3. Copy your Client ID and Client Secret to your `.env` file

### Frontend (`frontend/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
fantasy-league-history/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   └── main.py       # FastAPI application
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx       # Main React component
│   │   └── index.css     # Tailwind CSS
│   └── package.json
└── README.md
```

## License

MIT
