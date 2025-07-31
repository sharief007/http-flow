import React, { memo, useCallback, useMemo, useRef, useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { HttpFlow } from '../store/types';

const RequestsTable: React.FC = memo(() => {
    const {
        selectedRequest,
        selectRequest,
        filteredRequests,
        settings,
    } = useAppStore();
    
    const tableContainerRef = useRef<HTMLDivElement>(null);
    const isUserScrollingRef = useRef(false);
    const lastScrollTimeRef = useRef(0);

    const handleRowClick = useCallback((request: HttpFlow) => {
        selectRequest(request);
        // When user selects a row, they're interacting with the table, so don't auto-scroll
        isUserScrollingRef.current = true;
        lastScrollTimeRef.current = Date.now();
    }, [selectRequest]);

    // Track when user manually scrolls
    const handleScroll = useCallback(() => {
        if (!tableContainerRef.current) return;
        
        const { scrollTop, scrollHeight, clientHeight } = tableContainerRef.current;
        const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10; // 10px tolerance
        
        // If user is not at the bottom, they're manually scrolling
        if (!isAtBottom) {
            isUserScrollingRef.current = true;
            lastScrollTimeRef.current = Date.now();
        } else {
            // Reset user scrolling flag if they scroll back to bottom
            isUserScrollingRef.current = false;
        }
    }, []);

    // Auto-scroll when new requests are added
    useEffect(() => {
        if (!settings.autoScroll || !tableContainerRef.current) return;
        
        const now = Date.now();
        const timeSinceLastUserAction = now - lastScrollTimeRef.current;
        
        // Don't auto-scroll if user has recently interacted (within 5 seconds)
        // or if they have selected a request
        if (!isUserScrollingRef.current && 
            !selectedRequest && 
            timeSinceLastUserAction > 5000) {
            
            setTimeout(() => {
                if (tableContainerRef.current) {
                    tableContainerRef.current.scrollTop = tableContainerRef.current.scrollHeight;
                }
            }, 100); // Small delay to ensure DOM is updated
        }
    }, [filteredRequests.length, settings.autoScroll, selectedRequest]);

    // Memoize color mapping functions for better performance
    const getMethodColorClass = useMemo(() => (method: string) => {
        switch (method) {
            case 'GET': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
            case 'POST': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
            case 'PUT': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
            case 'DELETE': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
            default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
        }
    }, []);

    const getStatusColorClass = useMemo(() => (status: number | undefined) => {
        if (!status) return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
        if (status >= 200 && status < 300) return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
        if (status >= 300 && status < 400) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
        if (status >= 400) return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }, []);

    if (filteredRequests.length === 0) {
        return (
            <div className="h-full w-full flex items-center justify-center">
                <div className="text-center">
                    <p className="text-lg font-medium text-gray-900 dark:text-white">
                        No requests captured yet
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                        Start intercepting to see HTTP requests here
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div 
            ref={tableContainerRef}
            onScroll={handleScroll}
            className="h-full w-full overflow-auto"
        >
            <table className="w-full border-collapse bg-white dark:bg-gray-800">
                <thead className="sticky top-0 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
                    <tr>
                        <th className="w-20 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            Method
                        </th>
                        <th className="w-20 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            Status
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            URL
                        </th>
                        <th className="w-20 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider whitespace-nowrap">
                            Duration
                        </th>
                        <th className="w-22 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider whitespace-nowrap">
                            Req Size
                        </th>
                        <th className="w-22 px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider whitespace-nowrap">
                            Res Size
                        </th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {filteredRequests.map((request) => (
                        <tr
                            key={request.id}
                            onClick={() => handleRowClick(request)}
                            className={`cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                                selectedRequest?.id === request.id 
                                    ? 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-l-blue-500' 
                                    : ''
                            }`}
                        >
                            <td className="px-4 py-3 whitespace-nowrap">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getMethodColorClass(request.method)}`}>
                                    {request.method}
                                </span>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap">
                                <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getStatusColorClass(request.status)}`}>
                                    {request.status || 'pending'}
                                </span>
                            </td>
                            <td className="px-4 py-3">
                                <div className="truncate text-sm text-gray-900 dark:text-white" title={request.url}>
                                    {request.url}
                                </div>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                {request.duration}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                {request.requestSize}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                {request.responseSize}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
});

export default RequestsTable;
