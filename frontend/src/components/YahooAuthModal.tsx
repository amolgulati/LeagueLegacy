/**
 * YahooAuthModal Component
 *
 * A modal for Yahoo OAuth2 authentication flow:
 * - Displays login instructions
 * - Opens Yahoo authorization URL in new window
 * - Polls for authentication status
 * - Shows success/error states
 */

import { useState, useEffect, useCallback } from 'react';
import { LoadingSpinner } from './LoadingStates';

type AuthStep = 'idle' | 'redirecting' | 'waiting' | 'success' | 'error';

interface YahooAuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  sessionId?: string;
}

const API_BASE = 'http://localhost:8000';

export function YahooAuthModal({ isOpen, onClose, onSuccess, sessionId = 'default' }: YahooAuthModalProps) {
  const [step, setStep] = useState<AuthStep>('idle');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [authWindow, setAuthWindow] = useState<Window | null>(null);

  // Check authentication status
  const checkAuthStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/yahoo/auth/status?session_id=${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.authenticated) {
          setStep('success');
          return true;
        }
      }
      return false;
    } catch {
      return false;
    }
  }, [sessionId]);

  // Handle URL parameters from OAuth callback redirect
  useEffect(() => {
    if (!isOpen) return;

    const urlParams = new URLSearchParams(window.location.search);
    const yahooAuth = urlParams.get('yahoo_auth');

    if (yahooAuth === 'success') {
      setStep('success');
      // Clean up URL parameters
      window.history.replaceState({}, '', window.location.pathname);
    } else if (yahooAuth === 'error') {
      setStep('error');
      setErrorMessage(urlParams.get('message') || 'Authentication failed');
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [isOpen]);

  // Poll for auth status when waiting
  useEffect(() => {
    if (step !== 'waiting') return;

    const interval = setInterval(async () => {
      const isAuthenticated = await checkAuthStatus();
      if (isAuthenticated) {
        clearInterval(interval);
        if (authWindow && !authWindow.closed) {
          authWindow.close();
        }
      }
    }, 2000);

    // Also check if popup was closed without completing auth
    const windowCheckInterval = setInterval(() => {
      if (authWindow && authWindow.closed) {
        checkAuthStatus().then(isAuthenticated => {
          if (!isAuthenticated) {
            setStep('idle');
          }
        });
        clearInterval(windowCheckInterval);
      }
    }, 500);

    return () => {
      clearInterval(interval);
      clearInterval(windowCheckInterval);
    };
  }, [step, authWindow, checkAuthStatus]);

  const handleStartAuth = async () => {
    setStep('redirecting');
    setErrorMessage('');

    try {
      // Get the authorization URL from the backend
      const response = await fetch(`${API_BASE}/api/yahoo/auth/url?session_id=${sessionId}`);

      if (!response.ok) {
        throw new Error('Failed to get authorization URL');
      }

      const data = await response.json();

      // Open Yahoo auth in a popup window
      const width = 600;
      const height = 700;
      const left = window.screenX + (window.outerWidth - width) / 2;
      const top = window.screenY + (window.outerHeight - height) / 2;

      const popup = window.open(
        data.authorization_url,
        'yahoo_auth',
        `width=${width},height=${height},left=${left},top=${top},toolbar=no,menubar=no,scrollbars=yes`
      );

      if (popup) {
        setAuthWindow(popup);
        setStep('waiting');
      } else {
        // Popup was blocked, redirect in same window
        window.location.href = data.authorization_url;
      }
    } catch (error) {
      setStep('error');
      setErrorMessage(error instanceof Error ? error.message : 'Failed to start authentication');
    }
  };

  const handleClose = () => {
    if (authWindow && !authWindow.closed) {
      authWindow.close();
    }
    setStep('idle');
    setErrorMessage('');
    setAuthWindow(null);
    onClose();
  };

  const handleSuccess = () => {
    onSuccess();
    handleClose();
  };

  const handleRetry = () => {
    setStep('idle');
    setErrorMessage('');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 animate-fade-in">
      <div className="bg-slate-800 rounded-xl p-6 w-full max-w-md mx-4 border border-slate-700 shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-600/20 flex items-center justify-center">
              <span className="text-xl">🏈</span>
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Yahoo Fantasy Login</h3>
              <p className="text-slate-400 text-sm">
                {step === 'idle' && 'Connect your Yahoo account'}
                {step === 'redirecting' && 'Redirecting...'}
                {step === 'waiting' && 'Waiting for authorization...'}
                {step === 'success' && 'Authentication successful!'}
                {step === 'error' && 'Authentication failed'}
              </p>
            </div>
          </div>
          {(step === 'idle' || step === 'success' || step === 'error') && (
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

        {/* Idle State - Start Auth */}
        {step === 'idle' && (
          <div className="space-y-6 animate-fade-in">
            <div className="bg-slate-700/50 rounded-lg p-4">
              <h4 className="text-white font-medium mb-2">How it works:</h4>
              <ol className="text-slate-400 text-sm space-y-2 list-decimal list-inside">
                <li>Click "Login with Yahoo" below</li>
                <li>A popup window will open to Yahoo</li>
                <li>Sign in and authorize the app</li>
                <li>You'll be redirected back here</li>
              </ol>
            </div>

            <div className="bg-purple-600/10 border border-purple-600/30 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-purple-400 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="text-sm text-purple-300">
                  <p className="font-medium">Privacy Note</p>
                  <p className="text-purple-400 mt-1">
                    We only request read access to your fantasy leagues. Your Yahoo password is never shared with us.
                  </p>
                </div>
              </div>
            </div>

            <button
              onClick={handleStartAuth}
              className="w-full py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-500 transition-colors flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
              </svg>
              Login with Yahoo
            </button>
          </div>
        )}

        {/* Redirecting State */}
        {step === 'redirecting' && (
          <div className="space-y-6 animate-fade-in text-center py-8">
            <LoadingSpinner size="lg" color="purple" />
            <p className="text-slate-300">Opening Yahoo login...</p>
          </div>
        )}

        {/* Waiting State */}
        {step === 'waiting' && (
          <div className="space-y-6 animate-fade-in">
            <div className="text-center py-4">
              <LoadingSpinner size="lg" color="purple" />
            </div>

            <div className="bg-slate-700/50 rounded-lg p-4 text-center">
              <p className="text-white font-medium mb-2">Complete login in the popup window</p>
              <p className="text-slate-400 text-sm">
                After authorizing, you'll be automatically redirected back here.
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleClose}
                className="flex-1 py-3 bg-slate-700 text-white rounded-lg font-medium hover:bg-slate-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleStartAuth}
                className="flex-1 py-3 bg-purple-600/50 text-white rounded-lg font-medium hover:bg-purple-600 transition-colors"
              >
                Reopen Popup
              </button>
            </div>
          </div>
        )}

        {/* Success State */}
        {step === 'success' && (
          <div className="space-y-6 animate-fade-in">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto bg-green-600/20 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h4 className="text-xl font-bold text-white mb-2">Connected to Yahoo!</h4>
              <p className="text-slate-400">You can now import your Yahoo Fantasy leagues.</p>
            </div>

            <button
              onClick={handleSuccess}
              className="w-full py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-500 transition-colors"
            >
              Continue to Import
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
              <h4 className="text-xl font-bold text-white mb-2">Authentication Failed</h4>
              <p className="text-red-400 text-sm">{errorMessage}</p>
            </div>

            <div className="bg-slate-700/50 rounded-lg p-4 text-sm text-slate-300 space-y-2">
              <p className="font-medium">Troubleshooting tips:</p>
              <ul className="list-disc list-inside text-slate-400 space-y-1">
                <li>Make sure you approved the authorization</li>
                <li>Check that Yahoo credentials are configured on the server</li>
                <li>Try clearing your browser cache</li>
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

export default YahooAuthModal;
