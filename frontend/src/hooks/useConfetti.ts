/**
 * useConfetti Hook
 *
 * Hook to trigger confetti celebration on demand.
 * Returns a trigger function and a component to render.
 */

import { useState, useCallback } from 'react';
import { Confetti } from '../components/Confetti';
import { createElement } from 'react';

export function useConfetti(options?: { duration?: number; pieceCount?: number }) {
  const [showConfetti, setShowConfetti] = useState(false);

  const triggerConfetti = useCallback(() => {
    setShowConfetti(true);
  }, []);

  const handleComplete = useCallback(() => {
    setShowConfetti(false);
  }, []);

  const ConfettiComponent = showConfetti
    ? createElement(Confetti, {
        active: showConfetti,
        duration: options?.duration,
        pieceCount: options?.pieceCount,
        onComplete: handleComplete,
      })
    : null;

  return { triggerConfetti, ConfettiComponent, isActive: showConfetti };
}

export default useConfetti;
