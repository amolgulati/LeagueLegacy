/**
 * YahooImportModal Component
 *
 * A modal for importing Yahoo Fantasy league data with:
 * - League selection from user's leagues
 * - Manual league key input option
 * - Loading spinner during import
 * - Progress indicator showing import steps
 * - Clear error messages with retry option
 * - Success message with import summary
 */

import { useState, useEffect, useCallback } from 'react';
import { LoadingSpinner } from './LoadingStates';

type ImportStep = 'idle' | 'loading_leagues' | 'selecting' | 'importing' | 'done' | 'error';

interface UserLeague {
  league_key: string;
  name: string;
  season: string;
  num_teams: number;
  scoring_type: string;
  is_finished: boolean;
}

interface ImportResult {
  success: boolean;
  message: string;
  details?: {
    league_name?: string;
    season_year?: number;
    teams_imported?: number;
    matchups_imported?: number;
    trades_imported?: number;
    champion_name?: string;
  };
}

interface YahooImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  sessionId?: string;
  initialLeagueKey?: string;
}

const API_BASE = 'http://localhost:8000';

export function YahooImportModal({
  isOpen,
  onClose,
  onSuccess,
  sessionId = 'default',
  initialLeagueKey = ''
}: YahooImportModalProps) {
  const [step, setStep] = useState<ImportStep>('idle');
  const [leagues, setLeagues] = useState<UserLeague[]>([]);
  const [selectedLeagueKey, setSelectedLeagueKey] = useState(initialLeagueKey);
  const [manualLeagueKey, setManualLeagueKey] = useState('');
  const [useManualEntry, setUseManualEntry] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string>('');

  const loadUserLeagues = useCallback(async () => {
    setStep('loading_leagues');
    setError('');

    try {
      const response = await fetch(`${API_BASE}/api/yahoo/leagues?session_id=${sessionId}`);

      if (response.status === 401) {
        setError('Not authenticated. Please login to Yahoo first.');
        setStep('error');
        return;
      }

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to fetch leagues');
      }

      const data = await response.json();
      setLeagues(data);
      setStep('selecting');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load leagues');
      setStep('error');
    }
  }, [sessionId]);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setStep('idle');
      setSelectedLeagueKey(initialLeagueKey);
      setManualLeagueKey('');
      setUseManualEntry(!!initialLeagueKey);
      setResult(null);
      setError('');
      setProgress(0);
      // Auto-load leagues when modal opens
      if (!initialLeagueKey) {
        loadUserLeagues();
      }
    }
  }, [isOpen, initialLeagueKey, loadUserLeagues]);

  const handleImport = async () => {
    const leagueKey = useManualEntry ? manualLeagueKey.trim() : selectedLeagueKey;

    if (!leagueKey) {
      setError('Please select or enter a league key');
      return;
    }

    setStep('importing');
    setProgress(0);
    setProgressMessage('Connecting to Yahoo API...');
    setResult(null);

    // Simulate progress steps
    const progressSteps = [
      { progress: 20, message: 'Fetching league data...' },
      { progress: 40, message: 'Importing standings...' },
      { progress: 60, message: 'Importing matchups...' },
      { progress: 80, message: 'Importing trades...' },
      { progress: 90, message: 'Detecting champion...' },
    ];

    let stepIndex = 0;
    const progressInterval = setInterval(() => {
      if (stepIndex < progressSteps.length) {
        setProgress(progressSteps[stepIndex].progress);
        setProgressMessage(progressSteps[stepIndex].message);
        stepIndex++;
      }
    }, 800);

    try {
      const response = await fetch(`${API_BASE}/api/yahoo/import?session_id=${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ league_key: leagueKey }),
      });

      clearInterval(progressInterval);

      if (response.status === 401) {
        setStep('error');
        setError('Session expired. Please login to Yahoo again.');
        return;
      }

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to import league');
      }

      const data = await response.json();
      setProgress(100);
      setProgressMessage('Import complete!');
      setStep('done');
      setResult({
        success: true,
        message: `Successfully imported "${data.league_name}"!`,
        details: {
          league_name: data.league_name,
          season_year: data.season_year,
          teams_imported: data.teams_imported,
          matchups_imported: data.matchups_imported,
          trades_imported: data.trades_imported,
          champion_name: data.champion_name,
        },
      });
      onSuccess();
    } catch (err) {
      clearInterval(progressInterval);
      setStep('error');
      setError(err instanceof Error ? err.message : 'Import failed');
      setResult({
        success: false,
        message: err instanceof Error ? err.message : 'Import failed',
      });
    }
  };

  const handleClose = () => {
    if (step === 'importing') return; // Don't allow closing during import
    setStep('idle');
    setLeagues([]);
    setSelectedLeagueKey('');
    setManualLeagueKey('');
    setResult(null);
    setError('');
    onClose();
  };

  const handleRetry = () => {
    setError('');
    setResult(null);
    if (leagues.length > 0) {
      setStep('selecting');
    } else {
      loadUserLeagues();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 animate-fade-in">
      <div className="bg-slate-800 rounded-xl p-6 w-full max-w-lg mx-4 border border-slate-700 shadow-xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-600/20 flex items-center justify-center">
              <span className="text-xl">🏈</span>
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Import Yahoo League</h3>
              <p className="text-slate-400 text-sm">
                {step === 'loading_leagues' && 'Loading your leagues...'}
                {step === 'selecting' && 'Select a league to import'}
                {step === 'importing' && progressMessage}
                {step === 'done' && 'Import complete!'}
                {step === 'error' && 'Something went wrong'}
                {step === 'idle' && 'Preparing...'}
              </p>
            </div>
          </div>
          {step !== 'importing' && (
            <button
              onClick={handleClose}
              className="text-slate-400 hover:text-white transition-colors p-1"
              aria-label="Close modal"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {/* Loading Leagues State */}
        {step === 'loading_leagues' && (
          <div className="space-y-6 animate-fade-in text-center py-8">
            <LoadingSpinner size="lg" color="purple" />
            <p className="text-slate-300">Fetching your Yahoo Fantasy leagues...</p>
          </div>
        )}

        {/* Selecting State */}
        {step === 'selecting' && (
          <div className="space-y-4 animate-fade-in">
            {/* Toggle between list and manual entry */}
            <div className="flex gap-2">
              <button
                onClick={() => setUseManualEntry(false)}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                  !useManualEntry
                    ? 'bg-purple-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                Select from List
              </button>
              <button
                onClick={() => setUseManualEntry(true)}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                  useManualEntry
                    ? 'bg-purple-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                Enter League Key
              </button>
            </div>

            {/* League List */}
            {!useManualEntry && (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {leagues.length === 0 ? (
                  <div className="text-center py-8 text-slate-400">
                    <p>No leagues found.</p>
                    <p className="text-sm mt-1">Try entering a league key manually.</p>
                  </div>
                ) : (
                  leagues.map((league) => (
                    <div
                      key={league.league_key}
                      onClick={() => setSelectedLeagueKey(league.league_key)}
                      className={`p-4 rounded-lg cursor-pointer transition-all ${
                        selectedLeagueKey === league.league_key
                          ? 'bg-purple-600/30 border-2 border-purple-500'
                          : 'bg-slate-700/50 border-2 border-transparent hover:border-slate-600'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-white font-medium">{league.name}</div>
                          <div className="text-slate-400 text-sm flex items-center gap-2">
                            <span>{league.season}</span>
                            <span className="text-slate-600">•</span>
                            <span>{league.num_teams} teams</span>
                            <span className="text-slate-600">•</span>
                            <span>{league.scoring_type}</span>
                          </div>
                        </div>
                        {league.is_finished && (
                          <span className="text-xs bg-green-600/20 text-green-400 px-2 py-1 rounded">
                            Completed
                          </span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* Manual League Key Entry */}
            {useManualEntry && (
              <div>
                <label className="block text-slate-300 text-sm font-medium mb-2">
                  Yahoo League Key
                </label>
                <input
                  type="text"
                  value={manualLeagueKey}
                  onChange={(e) => setManualLeagueKey(e.target.value)}
                  placeholder="e.g. 423.l.123456"
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-colors"
                  autoFocus
                />
                <p className="text-slate-500 text-xs mt-2">
                  Format: <code className="text-slate-400">[game_key].l.[league_id]</code> (e.g., 423.l.123456 for NFL 2024)
                </p>
              </div>
            )}

            {error && (
              <div className="bg-red-600/10 border border-red-600/30 rounded-lg p-3">
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            )}

            <button
              onClick={handleImport}
              disabled={useManualEntry ? !manualLeagueKey.trim() : !selectedLeagueKey}
              className="w-full py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              Import League
            </button>

            {/* Refresh leagues button */}
            {!useManualEntry && (
              <button
                onClick={loadUserLeagues}
                className="w-full py-2 text-slate-400 hover:text-white text-sm transition-colors flex items-center justify-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh Leagues
              </button>
            )}
          </div>
        )}

        {/* Importing State */}
        {step === 'importing' && (
          <div className="space-y-6 animate-fade-in">
            <div className="flex justify-center py-4">
              <LoadingSpinner size="lg" color="purple" />
            </div>

            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-300">{progressMessage}</span>
                <span className="text-purple-400 font-medium">{progress}%</span>
              </div>
              <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-purple-600 to-purple-400 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            {/* Step Indicators */}
            <div className="grid grid-cols-4 gap-2">
              {[
                { label: 'League', progress: 20 },
                { label: 'Standings', progress: 40 },
                { label: 'Matchups', progress: 60 },
                { label: 'Trades', progress: 80 },
              ].map((item, idx) => {
                const isActive = progress >= item.progress - 10 && progress < item.progress + 20;
                const isComplete = progress > item.progress;
                return (
                  <div
                    key={item.label}
                    className={`text-center p-2 rounded-lg transition-all ${
                      isComplete
                        ? 'bg-green-600/20 text-green-400'
                        : isActive
                        ? 'bg-purple-600/20 text-purple-400 animate-pulse'
                        : 'bg-slate-700/50 text-slate-500'
                    }`}
                  >
                    <div className="text-lg mb-1">
                      {isComplete ? '✓' : ['📡', '👥', '🏈', '🔄'][idx]}
                    </div>
                    <div className="text-xs">{item.label}</div>
                  </div>
                );
              })}
            </div>

            <p className="text-center text-slate-500 text-sm">
              Please wait while we import your league data...
            </p>
          </div>
        )}

        {/* Success State */}
        {step === 'done' && result?.success && (
          <div className="space-y-6 animate-fade-in">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto bg-green-600/20 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h4 className="text-xl font-bold text-white mb-2">{result.message}</h4>
            </div>

            {result.details && (
              <div className="bg-slate-700/50 rounded-lg p-4 space-y-3">
                <h5 className="text-slate-300 font-medium text-sm uppercase tracking-wider">Import Summary</h5>
                <div className="grid grid-cols-2 gap-3">
                  {result.details.season_year && (
                    <div className="flex items-center gap-2">
                      <span className="text-xl">📅</span>
                      <div>
                        <div className="text-white font-medium">{result.details.season_year}</div>
                        <div className="text-slate-400 text-xs">Season</div>
                      </div>
                    </div>
                  )}
                  {result.details.teams_imported !== undefined && (
                    <div className="flex items-center gap-2">
                      <span className="text-xl">👥</span>
                      <div>
                        <div className="text-white font-medium">{result.details.teams_imported}</div>
                        <div className="text-slate-400 text-xs">Teams</div>
                      </div>
                    </div>
                  )}
                  {result.details.matchups_imported !== undefined && (
                    <div className="flex items-center gap-2">
                      <span className="text-xl">🏈</span>
                      <div>
                        <div className="text-white font-medium">{result.details.matchups_imported}</div>
                        <div className="text-slate-400 text-xs">Matchups</div>
                      </div>
                    </div>
                  )}
                  {result.details.trades_imported !== undefined && (
                    <div className="flex items-center gap-2">
                      <span className="text-xl">🔄</span>
                      <div>
                        <div className="text-white font-medium">{result.details.trades_imported}</div>
                        <div className="text-slate-400 text-xs">Trades</div>
                      </div>
                    </div>
                  )}
                </div>
                {result.details.champion_name && (
                  <div className="pt-3 border-t border-slate-600 flex items-center gap-2">
                    <span className="text-xl">🏆</span>
                    <div>
                      <div className="text-yellow-400 font-medium">{result.details.champion_name}</div>
                      <div className="text-slate-400 text-xs">Champion</div>
                    </div>
                  </div>
                )}
              </div>
            )}

            <button
              onClick={handleClose}
              className="w-full py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-500 transition-colors"
            >
              Done
            </button>
          </div>
        )}

        {/* Error State */}
        {step === 'error' && (
          <div className="space-y-6 animate-fade-in">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto bg-red-600/20 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h4 className="text-xl font-bold text-white mb-2">Import Failed</h4>
              <p className="text-red-400 text-sm">{error}</p>
            </div>

            <div className="bg-slate-700/50 rounded-lg p-4 text-sm text-slate-300 space-y-2">
              <p className="font-medium">Troubleshooting tips:</p>
              <ul className="list-disc list-inside text-slate-400 space-y-1">
                <li>Verify the league key is correct</li>
                <li>Ensure you have access to this league</li>
                <li>Try re-authenticating with Yahoo</li>
                <li>Check that the backend server is running</li>
              </ul>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleClose}
                className="flex-1 py-3 bg-slate-700 text-white rounded-lg font-medium hover:bg-slate-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleRetry}
                className="flex-1 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-500 transition-colors flex items-center justify-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Try Again
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default YahooImportModal;
