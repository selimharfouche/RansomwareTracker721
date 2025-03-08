// src/components/DirectThemeController.tsx
'use client';

import { useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';

export default function DirectThemeController() {
  const { theme } = useTheme();
  
  useEffect(() => {
    // This component is now simplified since we're using CSS variables
    // for the main theme switching.
    // This is just an extra measure to ensure proper theme application
    if (typeof window !== 'undefined') {
      const root = document.documentElement;
      
      // Remove both theme classes first
      root.classList.remove('light', 'dark');
      
      // Add current theme class
      root.classList.add(theme);
    }
  }, [theme]);
  
  // This component doesn't render anything
  return null;
}