import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

// Theme types
export type ThemeType = 'dark' | 'light' | 'espn-retro';

export interface ThemeContextType {
  theme: ThemeType;
  setTheme: (theme: ThemeType) => void;
  cycleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_STORAGE_KEY = 'fantasy-league-theme';

// Ordered list of themes for cycling
const THEME_ORDER: ThemeType[] = ['dark', 'light', 'espn-retro'];

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<ThemeType>(() => {
    // Check for saved theme preference
    const saved = localStorage.getItem(THEME_STORAGE_KEY) as ThemeType | null;
    if (saved && THEME_ORDER.includes(saved)) {
      return saved;
    }
    // Migrate from old dark mode setting
    const oldDarkMode = localStorage.getItem('fantasy-league-dark-mode');
    if (oldDarkMode !== null) {
      return oldDarkMode === 'false' ? 'light' : 'dark';
    }
    // Default to dark
    return 'dark';
  });

  // Apply theme class to html element
  useEffect(() => {
    // Remove all theme classes
    document.documentElement.classList.remove('dark', 'light', 'espn-retro');
    // Add current theme class
    document.documentElement.classList.add(theme);
    // Persist to localStorage
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  const setTheme = (newTheme: ThemeType) => {
    setThemeState(newTheme);
  };

  const cycleTheme = () => {
    const currentIndex = THEME_ORDER.indexOf(theme);
    const nextIndex = (currentIndex + 1) % THEME_ORDER.length;
    setThemeState(THEME_ORDER[nextIndex]);
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme, cycleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
