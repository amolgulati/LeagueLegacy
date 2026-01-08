/**
 * Confetti Component
 *
 * Celebratory confetti animation for championships and achievements.
 * Renders falling confetti pieces with various colors and animations.
 */

import { useEffect, useState, useCallback } from 'react';

interface ConfettiPiece {
  id: number;
  x: number;
  color: string;
  size: number;
  delay: number;
  duration: number;
  shape: 'square' | 'circle' | 'triangle';
}

const CONFETTI_COLORS = [
  '#FFD700', // Gold
  '#FFA500', // Orange
  '#FF6B6B', // Red
  '#4ECDC4', // Teal
  '#45B7D1', // Blue
  '#96E6A1', // Green
  '#DDA0DD', // Plum
  '#F7DC6F', // Yellow
  '#BB8FCE', // Purple
  '#85C1E9', // Light Blue
];

function ConfettiShape({ piece }: { piece: ConfettiPiece }) {
  const style: React.CSSProperties = {
    left: `${piece.x}%`,
    width: piece.size,
    height: piece.shape === 'triangle' ? 0 : piece.size,
    backgroundColor: piece.shape !== 'triangle' ? piece.color : 'transparent',
    borderRadius: piece.shape === 'circle' ? '50%' : '0',
    animationDelay: `${piece.delay}s`,
    animationDuration: `${piece.duration}s`,
    // Triangle specific styles
    ...(piece.shape === 'triangle' && {
      borderLeft: `${piece.size / 2}px solid transparent`,
      borderRight: `${piece.size / 2}px solid transparent`,
      borderBottom: `${piece.size}px solid ${piece.color}`,
    }),
  };

  return <div className="confetti-piece" style={style} />;
}

export function Confetti({
  active = true,
  duration = 3000,
  pieceCount = 50,
  onComplete
}: {
  active?: boolean;
  duration?: number;
  pieceCount?: number;
  onComplete?: () => void;
}) {
  const [pieces, setPieces] = useState<ConfettiPiece[]>([]);
  const [isActive, setIsActive] = useState(active);

  const generatePieces = useCallback(() => {
    const shapes: ConfettiPiece['shape'][] = ['square', 'circle', 'triangle'];
    return Array.from({ length: pieceCount }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
      size: 8 + Math.random() * 8,
      delay: Math.random() * 0.5,
      duration: 2 + Math.random() * 2,
      shape: shapes[Math.floor(Math.random() * shapes.length)],
    }));
  }, [pieceCount]);

  useEffect(() => {
    if (active && isActive) {
      setPieces(generatePieces());

      const timer = setTimeout(() => {
        setIsActive(false);
        setPieces([]);
        onComplete?.();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [active, isActive, duration, generatePieces, onComplete]);

  if (!isActive || pieces.length === 0) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
      {pieces.map((piece) => (
        <ConfettiShape key={piece.id} piece={piece} />
      ))}
    </div>
  );
}

// Hook to trigger confetti on demand
export function useConfetti(options?: { duration?: number; pieceCount?: number }) {
  const [showConfetti, setShowConfetti] = useState(false);

  const triggerConfetti = useCallback(() => {
    setShowConfetti(true);
  }, []);

  const handleComplete = useCallback(() => {
    setShowConfetti(false);
  }, []);

  const ConfettiComponent = showConfetti ? (
    <Confetti
      active={showConfetti}
      duration={options?.duration}
      pieceCount={options?.pieceCount}
      onComplete={handleComplete}
    />
  ) : null;

  return { triggerConfetti, ConfettiComponent, isActive: showConfetti };
}

// Trophy burst animation component - shows when clicking on championship items
export function TrophyBurst({ show, onComplete }: { show: boolean; onComplete?: () => void }) {
  const [visible, setVisible] = useState(show);

  useEffect(() => {
    if (show) {
      setVisible(true);
      const timer = setTimeout(() => {
        setVisible(false);
        onComplete?.();
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [show, onComplete]);

  if (!visible) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-50 flex items-center justify-center">
      {/* Central trophy with glow burst */}
      <div className="relative animate-pulse-scale">
        <div className="absolute inset-0 bg-yellow-500/30 blur-3xl rounded-full animate-ping" />
        <svg className="w-24 h-24 text-yellow-500 animate-trophy-glow" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M5 2a2 2 0 00-2 2v1a2 2 0 002 2h1v1H5a3 3 0 00-3 3v6a3 3 0 003 3h10a3 3 0 003-3v-6a3 3 0 00-3-3h-1V7h1a2 2 0 002-2V4a2 2 0 00-2-2H5zm0 2h10v1H5V4zm3 4h4v1H8V8z" clipRule="evenodd" />
        </svg>
      </div>

      {/* Radiating stars */}
      {Array.from({ length: 8 }).map((_, i) => (
        <div
          key={i}
          className="absolute"
          style={{
            transform: `rotate(${i * 45}deg) translateY(-80px)`,
            animation: 'fadeIn 0.3s ease-out forwards',
            animationDelay: `${i * 0.05}s`,
          }}
        >
          <svg className="w-6 h-6 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        </div>
      ))}
    </div>
  );
}

export default Confetti;
