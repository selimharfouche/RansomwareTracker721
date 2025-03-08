// src/contexts/ThemeContext.tsx
'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>('light');
  
  // Function to update document with the correct theme
  const updateDocumentClass = useCallback((theme: Theme) => {
    if (typeof window === 'undefined') return;
    
    const root = window.document.documentElement;
    
    // Remove both theme classes first
    root.classList.remove('light');
    root.classList.remove('dark');
    
    // Add the current theme class
    root.classList.add(theme);
    
    // Update color scheme for system integration
    root.style.colorScheme = theme;
  }, []);
  
  // Effect to handle theme changes
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    // Set the theme based on user preference
    updateDocumentClass(theme);
    
    // Save theme to localStorage
    localStorage.setItem('theme', theme);
  }, [theme, updateDocumentClass]);
  
  // Load saved theme on initial render
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    const savedTheme = localStorage.getItem('theme') as Theme | null;
    if (savedTheme && ['light', 'dark'].includes(savedTheme)) {
      setTheme(savedTheme);
      updateDocumentClass(savedTheme);
    }
  }, [updateDocumentClass]);
  
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}