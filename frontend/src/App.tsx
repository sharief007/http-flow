import React, { useRef, useState } from 'react';
import { useInitialization } from './hooks/useInitialization';
import { useAppStore } from './store/useAppStore';
import Toolbar from './components/Toolbar';
import RequestDetails from './components/RequestDetails';
import RequestsTable from './components/RequestsTable';
import RulesDrawer from './components/RulesDrawer';
import FiltersDrawer from './components/FiltersDrawer';

const AppContent: React.FC = () => {
  // Initialize the app
  useInitialization();
  
  // Use selectors to prevent unnecessary re-renders
  const selectedRequest = useAppStore((state) => state.selectedRequest);
  const showRequestDetails = useAppStore((state) => state.showRequestDetails);
  
  const { showFiltersPanel, toggleFiltersPanel, showRulesPanel, toggleRulesPanel } = useAppStore();

  // Split pane state - using Tailwind implementation
  const [splitHeight, setSplitHeight] = useState(400); // px
  const dragging = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const onMouseDown = () => {
    dragging.current = true;
    document.body.style.cursor = "row-resize";
  };

  const onMouseUp = () => {
    dragging.current = false;
    document.body.style.cursor = "";
  };

  const onMouseMove = (e: MouseEvent) => {
    if (dragging.current && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const newHeight = e.clientY - rect.top;
      if (newHeight > 100 && newHeight < rect.height - 100) {
        setSplitHeight(newHeight);
      }
    }
  };

  React.useEffect(() => {
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, []);

  return (
    <>
      <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
        {/* Toolbar */}
        <header className="h-12 flex items-center px-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
          <Toolbar />
        </header>
        
        {/* Main content area */}
        <main ref={containerRef} className="flex-1 min-h-0 flex flex-col">
          {/* Requests Table - Always visible */}
          <div 
            style={{ height: selectedRequest && showRequestDetails ? splitHeight : '100%' }}
            className="bg-white dark:bg-gray-800 overflow-auto"
          >
            <RequestsTable />
          </div>
          
          {/* Resize Handle - Only visible when the bottom panel is shown */}
          {selectedRequest && showRequestDetails && (
            <div 
              className="h-2 bg-gray-300 dark:bg-gray-700 cursor-row-resize flex items-center justify-center hover:bg-gray-400 dark:hover:bg-gray-600 transition-colors"
              onMouseDown={onMouseDown}
            >
              <div className="w-8 h-0.5 bg-gray-500 dark:bg-gray-400 rounded" />
            </div>
          )}
          
          {/* Request Details Panel - Only visible when a request is selected */}
          {selectedRequest && showRequestDetails && (
            <div 
              style={{ height: `calc(100% - ${splitHeight}px - 8px)` }}
              className="bg-white dark:bg-gray-800 overflow-auto border-t border-gray-200 dark:border-gray-700"
            >
              <RequestDetails />
            </div>
          )}
        </main>
      </div>
      
      {/* Render Drawers outside main layout to avoid z-index issues */}
      <FiltersDrawer isOpened={showFiltersPanel} onClose={toggleFiltersPanel} />
      <RulesDrawer isOpened={showRulesPanel} onClose={toggleRulesPanel} />
    </>
  );
};

function App() {
  return (
      <AppContent />
  );
}

export default App;
