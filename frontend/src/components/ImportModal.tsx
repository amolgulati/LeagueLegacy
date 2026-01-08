/**
 * ImportModal Component
 *
 * A modal for importing league data from Sleeper with:
 * - Loading spinner during import
 * - Progress indicator showing import steps
 * - Clear error messages with retry option
 * - Success message with import summary
 */

import { useState, useEffect } from 'react';
import { LoadingSpinner } from './LoadingStates';

type ImportStep = 'idle' | 'connecting' | 'fetching_league' | 'importing_seasons' | 'importing_teams' | 'importing_matchups' | 'importing_trades' | 'detecting_champion' | 'done' | 'error';

interface ImportProgress {
  step: ImportStep;
  message: string;
  progress: number; // 0-100
}

interface ImportResult {
  success: boolean;
  message: string;
  details?: {
    league_name?: string;
    seasons_imported?: number;
    teams_imported?: number;
    matchups_imported?: number;
    trades_imported?: number;
    champion_name?: string;
  };
}

interface ImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  initialLeagueId?: string;
}

const IMPORT_STEPS: Record<ImportStep, { label: string; progress: number }> = {
  idle: { label: '', progress: 0 },
  connecting: { label: 'Connecting to Sleeper API...', progress: 10 },
  fetching_league: { label: 'Fetching league data...', progress: 20 },
  importing_seasons: { label: 'Importing historical seasons...', progress: 40 },
  importing_teams: { label: 'Importing teams and rosters...', progress: 55 },
  importing_matchups: { label: 'Importing matchups...', progress: 70 },
  importing_trades: { label: 'Importing trades...', progress: 85 },
  detecting_champion: { label: 'Detecting champions...', progress: 95 },
  done: { label: 'Import complete!', progress: 100 },
  error: { label: 'Import failed', progress: 0 },
};

export function ImportModal({ isOpen, onClose, onSuccess, initialLeagueId = '' }: ImportModalProps) {
  const [leagueId, setLeagueId] = useState(initialLeagueId);
  const [progress, setProgress] = useState<ImportProgress>({ step: 'idle', message: '', progress: 0 });
  const [result, setResult] = useState<ImportResult | null>(null);

  // Sync leagueId with initialLeagueId when modal opens
  useEffect(() => {
    if (isOpen) {
      setLeagueId(initialLeagueId);
    }
  }, [isOpen, initialLeagueId]);

  const resetModal = () => {
    setLeagueId('');
    setProgress({ step: 'idle', message: '', progress: 0 });
    setResult(null);
  };

  const handleClose = () => {
    if (progress.step !== 'idle' && progress.step !== 'done' && progress.step !== 'error') {
      // Don't allow closing during import
      return;
    }
    resetModal();
    onClose();
  };

  const simulateProgress = () => {
    // Simulate progress steps for visual feedback
    // The actual import happens in one API call, but we show stepped progress
    const steps: ImportStep[] = [
      'connecting',
      'fetching_league',
      'importing_seasons',
      'importing_teams',
      'importing_matchups',
      'importing_trades',
      'detecting_champion',
    ];

    let currentStep = 0;
    const interval = setInterval(() => {
      if (currentStep < steps.length) {
        const step = steps[currentStep];
        setProgress({
          step,
          message: IMPORT_STEPS[step].label,
          progress: IMPORT_STEPS[step].progress,
        });
        currentStep++;
      } else {
        clearInterval(interval);
      }
    }, 600);

    return () => clearInterval(interval);
  };

  const handleImport = async () => {
    if (!leagueId.trim()) return;

    setResult(null);

    // Start progress simulation
    const cleanup = simulateProgress();

    try {
      const response = await fetch('http://localhost:8000/api/sleeper/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ league_id: leagueId.trim() }),
      });

      // Clear the progress simulation
      cleanup();

      if (response.ok) {
        const data = await response.json();
        setProgress({
          step: 'done',
          message: IMPORT_STEPS.done.label,
          progress: 100,
        });
        setResult({
          success: true,
          message: `Successfully imported "${data.league_name}"!`,
          details: {
            league_name: data.league_name,
            seasons_imported: data.seasons_imported || 1,
            teams_imported: data.teams_imported,
            matchups_imported: data.matchups_imported,
            trades_imported: data.trades_imported,
            champion_name: data.champion_name,
          },
        });
        onSuccess();
      } else {
        const error = await response.json();
        setProgress({
          step: 'error',
          message: IMPORT_STEPS.error.label,
          progress: 0,
        });
        setResult({
          success: false,
          message: error.detail || 'Failed to import league. Please check the league ID and try again.',
        });
      }
    } catch (err) {
      cleanup();
      setProgress({
        step: 'error',
        message: IMPORT_STEPS.error.label,
        progress: 0,
      });
      setResult({
        success: false,
        message: 'Network error - please ensure the backend server is running on port 8000.',
      });
    }
  };

  const handleRetry = () => {
    setProgress({ step: 'idle', message: '', progress: 0 });
    setResult(null);
  };

  const handleDismissSuccess = () => {
    resetModal();
    onClose();
  };

  if (!isOpen) return null;

  const isImporting = progress.step !== 'idle' && progress.step !== 'done' && progress.step !== 'error';
  const showInput = progress.step === 'idle';
  const showProgress = isImporting;
  const showResult = result !== null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 animate-fade-in">
      <div className="bg-slate-800 rounded-xl p-6 w-full max-w-md mx-4 border border-slate-700 shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-600/20 flex items-center justify-center">
              <span className="text-xl">🌙</span>
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Import Sleeper League</h3>
              <p className="text-slate-400 text-sm">
                {isImporting ? 'Importing...' : 'Enter your league ID to get started'}
              </p>
            </div>
          </div>
          {!isImporting && (
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

        {/* Input Form */}
        {showInput && !showResult && (
          <div className="space-y-4 animate-fade-in">
            <div>
              <label className="block text-slate-300 text-sm font-medium mb-2">
                Sleeper League ID
              </label>
              <input
                type="text"
                value={leagueId}
                onChange={(e) => setLeagueId(e.target.value)}
                placeholder="e.g. 123456789012345678"
                className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                autoFocus
              />
              <p className="text-slate-500 text-xs mt-2">
                Find your league ID in the Sleeper app URL: <code className="text-slate-400">sleeper.app/leagues/<span className="text-blue-400">[LEAGUE_ID]</span></code>
              </p>
            </div>

            <button
              onClick={handleImport}
              disabled={!leagueId.trim()}
              className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              Start Import
            </button>
          </div>
        )}

        {/* Progress Indicator */}
        {showProgress && (
          <div className="space-y-6 animate-fade-in">
            {/* Loading Spinner */}
            <div className="flex justify-center py-4">
              <LoadingSpinner size="lg" color="blue" />
            </div>

            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-300">{progress.message}</span>
                <span className="text-blue-400 font-medium">{progress.progress}%</span>
              </div>
              <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-600 to-blue-400 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${progress.progress}%` }}
                />
              </div>
            </div>

            {/* Step Indicators */}
            <div className="grid grid-cols-4 gap-2">
              {(['fetching_league', 'importing_seasons', 'importing_matchups', 'importing_trades'] as ImportStep[]).map((step, idx) => {
                const stepProgress = IMPORT_STEPS[step].progress;
                const isActive = progress.progress >= stepProgress - 10 && progress.progress < stepProgress + 15;
                const isComplete = progress.progress > stepProgress;
                return (
                  <div
                    key={step}
                    className={`text-center p-2 rounded-lg transition-all ${
                      isComplete
                        ? 'bg-green-600/20 text-green-400'
                        : isActive
                        ? 'bg-blue-600/20 text-blue-400 animate-pulse'
                        : 'bg-slate-700/50 text-slate-500'
                    }`}
                  >
                    <div className="text-lg mb-1">
                      {isComplete ? '✓' : ['📡', '📅', '🏈', '🔄'][idx]}
                    </div>
                    <div className="text-xs">
                      {['League', 'Seasons', 'Matchups', 'Trades'][idx]}
                    </div>
                  </div>
                );
              })}
            </div>

            <p className="text-center text-slate-500 text-sm">
              This may take a few moments for leagues with many seasons...
            </p>
          </div>
        )}

        {/* Success Result */}
        {showResult && result?.success && (
          <div className="space-y-6 animate-fade-in">
            {/* Success Icon */}
            <div className="text-center">
              <div className="w-16 h-16 mx-auto bg-green-600/20 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h4 className="text-xl font-bold text-white mb-2">{result.message}</h4>
            </div>

            {/* Import Summary */}
            {result.details && (
              <div className="bg-slate-700/50 rounded-lg p-4 space-y-3">
                <h5 className="text-slate-300 font-medium text-sm uppercase tracking-wider">Import Summary</h5>
                <div className="grid grid-cols-2 gap-3">
                  {result.details.seasons_imported !== undefined && (
                    <div className="flex items-center gap-2">
                      <span className="text-xl">📅</span>
                      <div>
                        <div className="text-white font-medium">{result.details.seasons_imported}</div>
                        <div className="text-slate-400 text-xs">Seasons</div>
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
              onClick={handleDismissSuccess}
              className="w-full py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-500 transition-colors"
            >
              Done
            </button>
          </div>
        )}

        {/* Error Result */}
        {showResult && !result?.success && (
          <div className="space-y-6 animate-fade-in">
            {/* Error Icon */}
            <div className="text-center">
              <div className="w-16 h-16 mx-auto bg-red-600/20 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h4 className="text-xl font-bold text-white mb-2">Import Failed</h4>
              <p className="text-red-400 text-sm">{result?.message}</p>
            </div>

            {/* Error Suggestions */}
            <div className="bg-slate-700/50 rounded-lg p-4 text-sm text-slate-300 space-y-2">
              <p className="font-medium">Troubleshooting tips:</p>
              <ul className="list-disc list-inside text-slate-400 space-y-1">
                <li>Verify the league ID is correct</li>
                <li>Ensure the league is public or you have access</li>
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
                className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-500 transition-colors flex items-center justify-center gap-2"
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

export default ImportModal;
