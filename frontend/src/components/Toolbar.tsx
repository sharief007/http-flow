import React, { memo, useCallback } from 'react';
import { useAppStore } from '../store/useAppStore';

// Simple SVG icons to replace Tabler icons
const FilterIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
    <path d="M10 18h4v-2h-4v2zM3 6v2h18V6H3zm3 7h12v-2H6v2z"/>
  </svg>
);

const SettingsIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
    <path d="M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.07-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.74,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.36,4.82,11.69,4.82,12s0.02,0.64,0.07,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.44-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.47-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z"/>
  </svg>
);

const PlayIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
    <path d="M8 5v14l11-7z"/>
  </svg>
);

const StopIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
    <path d="M6 6h12v12H6z"/>
  </svg>
);

const TrashIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
  </svg>
);

const SearchIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
  </svg>
);

const SunIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
  </svg>
);

const MoonIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
    <path d="M9 2c-1.05 0-2.05.16-3 .46 4.06 1.27 7 5.06 7 9.54 0 4.48-2.94 8.27-7 9.54.95.3 1.95.46 3 .46 5.52 0 10-4.48 10-10S14.52 2 9 2z"/>
  </svg>
);

interface StatusIndicatorProps {
    isActive: boolean;
    label: string;
    tooltip?: string;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ isActive, label, tooltip }) => (
  <div className="flex items-center gap-2" title={tooltip}>
    <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-green-500' : 'bg-red-500'}`} />
    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</span>
  </div>
);

const Toolbar: React.FC = memo(() => {
    // Use selectors to prevent unnecessary re-renders
    const filters = useAppStore((state) => state.filters);
    const activeFilter = useAppStore((state) => state.activeFilter);
    const quickFilterText = useAppStore((state) => state.quickFilterText);
    const isIntercepting = useAppStore((state) => state.isIntercepting);
    const isConnected = useAppStore((state) => state.isConnected);
    const connectionStatus = useAppStore((state) => state.connectionStatus);
    const showFiltersPanel = useAppStore((state) => state.showFiltersPanel);
    const showRulesPanel = useAppStore((state) => state.showRulesPanel);

    const {
        setActiveFilter,
        setQuickFilterText,
        toggleFiltersPanel,
        toggleRulesPanel,
        startIntercepting,
        stopIntercepting,
        clearRequests,
    } = useAppStore();

    const handleFilterChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
        const value = e.target.value;
        if (value === 'all' || value === '' || value === undefined) {
            setActiveFilter(null);
        } else if (filters && filters.length > 0) {
            const filter = filters.find(f => f.id && f.id.toString() === value);
            setActiveFilter(filter || null);
        } else {
            setActiveFilter(null);
        }
    }, [filters, setActiveFilter]);

    const handleClearActiveFilter = useCallback(() => {
        setActiveFilter(null);
    }, [setActiveFilter]);

    const handleToggleIntercepting = useCallback(() => {
        if (isIntercepting) {
            stopIntercepting();
        } else {
            startIntercepting();
        }
    }, [isIntercepting, startIntercepting, stopIntercepting]);

    // Prepare filter options with truncation for long names
    const truncateText = (text: string, maxLength: number = 25) => {
        return text.length > maxLength ? `${text.substring(0, maxLength)}...` : text;
    };

    const filterOptions = [
        { value: 'all', label: 'All Requests', fullLabel: 'All Requests' },
        ...(filters || []).map(filter => ({
            value: filter.id?.toString() || '',
            label: truncateText(filter.filter_name || ''),
            fullLabel: filter.filter_name || ''
        }))
    ];

    return (
        <div className="flex items-center justify-between w-full px-4 py-2 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-4">
                <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
                    HTTP Flow
                </h1>

                <div className="w-px h-6 bg-gray-300 dark:bg-gray-600" />

                {/* Quick Search */}
                <div className="relative">
                    <div className="absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400">
                        <SearchIcon />
                    </div>
                    <input
                        type="text"
                        placeholder="Quick filter (URL, method, status...)"
                        value={quickFilterText}
                        onChange={(e) => setQuickFilterText(e.target.value)}
                        className="pl-8 pr-3 py-2 w-56 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                </div>

                {/* Filter Dropdown */}
                <select
                    value={activeFilter?.id?.toString() || 'all'}
                    onChange={handleFilterChange}
                    className="px-3 py-2 w-40 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 truncate"
                    title={filterOptions.find(opt => opt.value === (activeFilter?.id?.toString() || 'all'))?.fullLabel || 'All Requests'}
                >
                    {filterOptions.map(option => (
                        <option key={option.value} value={option.value} title={option.fullLabel}>
                            {option.label}
                        </option>
                    ))}
                </select>

                {/* Active Filter Badge */}
                {activeFilter && activeFilter.filter_name && (
                    <div 
                        className="flex items-center gap-1 px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-sm rounded-md max-w-48"
                        title={activeFilter.filter_name}
                    >
                        <FilterIcon />
                        <span className="truncate">{truncateText(activeFilter.filter_name, 20)}</span>
                        <button
                            onClick={handleClearActiveFilter}
                            className="ml-1 text-blue-600 hover:text-blue-800 dark:text-blue-300 dark:hover:text-blue-100 flex-shrink-0"
                        >
                            ✕
                        </button>
                    </div>
                )}
            </div>

            <div className="flex items-center gap-2">
                <div className="w-px h-6 bg-gray-300 dark:bg-gray-600" />

                {/* Panel Toggles */}
                <button
                    onClick={toggleFiltersPanel}
                    className={`p-2 rounded-md transition-colors ${
                        showFiltersPanel 
                            ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300' 
                            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                    title="Toggle Filters Panel"
                >
                    <FilterIcon />
                </button>

                <button
                    onClick={toggleRulesPanel}
                    className={`flex items-center gap-2 px-3 py-2 text-sm rounded-md transition-colors ${
                        showRulesPanel 
                            ? 'bg-blue-600 text-white' 
                            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                >
                    <SettingsIcon />
                    Rules
                </button>

                <div className="w-px h-6 bg-gray-300 dark:bg-gray-600" />

                {/* Action Buttons */}
                <button
                    onClick={handleToggleIntercepting}
                    className={`flex items-center gap-2 px-3 py-2 text-sm rounded-md transition-colors ${
                        isIntercepting 
                            ? 'bg-red-600 text-white hover:bg-red-700' 
                            : 'bg-green-600 text-white hover:bg-green-700'
                    }`}
                >
                    {isIntercepting ? <StopIcon /> : <PlayIcon />}
                    {isIntercepting ? 'Stop' : 'Start'}
                </button>

                <button
                    onClick={clearRequests}
                    className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors"
                    title="Clear all requests"
                >
                    <TrashIcon />
                </button>
            </div>
        </div>
    );
});

Toolbar.displayName = 'Toolbar';

export default Toolbar;
