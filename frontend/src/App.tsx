import { useEffect, useState } from 'react';

interface ApiStatus {
  name: string;
  version: string;
  status: string;
}

function App() {
  const [apiStatus, setApiStatus] = useState<ApiStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/')
      .then((res) => res.json())
      .then((data) => setApiStatus(data))
      .catch(() => setError('Could not connect to API'));
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-white mb-4">
          Fantasy League History Tracker
        </h1>
        <p className="text-slate-400 mb-8">
          Unified stats from Yahoo Fantasy and Sleeper
        </p>

        <div className="bg-slate-800 rounded-lg p-6 shadow-xl border border-slate-700">
          {error ? (
            <p className="text-red-400">{error}</p>
          ) : apiStatus ? (
            <div className="text-left">
              <p className="text-green-400 font-semibold">API Connected</p>
              <p className="text-slate-300 text-sm mt-2">
                Version: {apiStatus.version}
              </p>
              <p className="text-slate-300 text-sm">
                Status: {apiStatus.status}
              </p>
            </div>
          ) : (
            <p className="text-slate-400">Connecting to API...</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
