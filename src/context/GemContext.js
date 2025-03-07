import React, { createContext, useContext, useState } from 'react';

const GemContext = createContext();

export function GemProvider({ children }) {
  const [gemData, setGemData] = useState(null);

  return (
    <GemContext.Provider value={{ gemData, setGemData }}>
      {children}
    </GemContext.Provider>
  );
}

export function useGem() {
  const context = useContext(GemContext);
  if (!context) {
    throw new Error('useGem must be used within a GemProvider');
  }
  return context;
} 