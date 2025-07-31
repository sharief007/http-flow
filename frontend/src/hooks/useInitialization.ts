import { useEffect, useRef } from 'react';
import { useAppStore } from '../store/useAppStore';

export const useInitialization = (): void => {
  const initialized = useRef<boolean>(false);
  const {
    isInitialized,
    isConnected,
    initializeWebSocket,
    initializeMockData,
    loadInterceptionStatus,
  } = useAppStore();

  useEffect(() => {
    if (!initialized.current && !isInitialized) {
      initialized.current = true;
      initializeWebSocket();

      // Load current interception status
      loadInterceptionStatus();

      // Initialize with mock data for development (fallback if WebSocket fails)
      const timer = setTimeout(() => {
        if (!isConnected) {
          console.log('WebSocket not connected, using mock data');
          initializeMockData();
        }
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, [isInitialized, isConnected, initializeWebSocket, initializeMockData, loadInterceptionStatus]);
};

