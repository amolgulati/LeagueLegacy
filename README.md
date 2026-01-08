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
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`.

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
