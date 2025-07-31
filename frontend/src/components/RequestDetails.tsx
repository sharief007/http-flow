import React, { useState, memo } from 'react';
import { useAppStore } from '../store/useAppStore';

// Simple SVG icons
const ClockIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M16.2,16.2L11,13V7H12.5V12.2L17,14.7L16.2,16.2Z"/>
  </svg>
);

const RequestDetails: React.FC = memo(() => {
  const selectedRequest = useAppStore((state) => state.selectedRequest);
  const [selectedTab, setSelectedTab] = useState<string>('request-headers');

  if (!selectedRequest) {
    return (
      <div className="h-full flex items-center justify-center bg-white dark:bg-gray-800">
        <p className="text-gray-500 dark:text-gray-400 italic">
          Select a request to view details
        </p>
      </div>
    );
  }

  const renderHeadersTable = (headers?: Record<string, string>[], emptyMessage?: string) => {
    if (!headers || headers.length === 0) {
      return (
        <div className="text-center py-8">
          <p className="text-gray-500 dark:text-gray-400">{emptyMessage}</p>
        </div>
      );
    }

    return (
      <div className="overflow-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="w-1/3 px-4 py-2 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                Header Name
              </th>
              <th className="px-4 py-2 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                Header Value
              </th>
            </tr>
          </thead>
          <tbody>
            {headers.map((entry, index) => (
              <tr key={entry.name || index} className="border-b border-gray-100 dark:border-gray-800">
                <td className="px-4 py-2 text-sm font-mono text-gray-900 dark:text-white">
                  {entry.name}
                </td>
                <td className="px-4 py-2 text-sm font-mono text-gray-900 dark:text-white break-all">
                  {entry.value}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderCodeBlock = (content: any, fallbackMessage: string) => {
    if (!content) {
      return (
        <div className="text-center py-8">
          <p className="text-gray-500 dark:text-gray-400">{fallbackMessage}</p>
        </div>
      );
    }

    const contentStr = typeof content === 'string' ? content : JSON.stringify(content, null, 2);
    return (
      <pre className="bg-gray-50 dark:bg-gray-900 p-4 rounded-md overflow-auto text-sm font-mono whitespace-pre-wrap">
        <code className="text-gray-900 dark:text-white">{contentStr}</code>
      </pre>
    );
  };

  const tabs = [
    { value: 'request-headers', label: 'Request Headers' },
    { value: 'response-headers', label: 'Response Headers' },
    { value: 'request-body', label: 'Request Body' },
    { value: 'response-body', label: 'Response Body' },
    { value: 'overview', label: 'Overview' },
  ];

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-800">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className={`px-2 py-1 text-xs font-medium rounded ${
              selectedRequest.method === 'GET' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
              selectedRequest.method === 'POST' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
              selectedRequest.method === 'PUT' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
              selectedRequest.method === 'DELETE' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
              'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
            }`}>
              {selectedRequest.method}
            </span>
            <span className={`px-2 py-1 text-xs font-medium rounded ${
              (selectedRequest.status && selectedRequest.status >= 200 && selectedRequest.status < 300) ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
              (selectedRequest.status && selectedRequest.status >= 300 && selectedRequest.status < 400) ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
              (selectedRequest.status && selectedRequest.status >= 400) ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
              'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
            }`}>
              {selectedRequest.status || 'pending'}
            </span>
            {selectedRequest.isIntercepted && (
              <span className="px-2 py-1 text-xs font-medium rounded bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
                INTERCEPTED
              </span>
            )}
            <div className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400">
              <ClockIcon />
              {selectedRequest.duration || 'N/A'}
            </div>
          </div>
        </div>
        <div className="mt-2">
          <p className="text-sm font-mono text-gray-900 dark:text-white break-all">
            {selectedRequest.url}
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex space-x-8 px-4">
          {tabs.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setSelectedTab(tab.value)}
              className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                selectedTab === tab.value
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="flex-1 p-4 overflow-auto">
        {selectedTab === 'request-headers' && (
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Request Headers</h3>
            {renderHeadersTable(selectedRequest.requestHeaders, 'No request headers available')}
          </div>
        )}

        {selectedTab === 'response-headers' && (
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Response Headers</h3>
            {renderHeadersTable(selectedRequest.responseHeaders, 'No response headers available')}
          </div>
        )}

        {selectedTab === 'request-body' && (
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Request Body</h3>
            {renderCodeBlock(selectedRequest.requestBody, 'No request body')}
          </div>
        )}

        {selectedTab === 'response-body' && (
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Response Body</h3>
            {renderCodeBlock(selectedRequest.responseBody, 'No response body')}
          </div>
        )}

        {selectedTab === 'overview' && (
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Overview</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Method</label>
                  <p className="text-sm text-gray-900 dark:text-white">{selectedRequest.method}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Status</label>
                  <p className="text-sm text-gray-900 dark:text-white">{selectedRequest.status || 'pending'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Duration</label>
                  <p className="text-sm text-gray-900 dark:text-white">{selectedRequest.duration || 'N/A'}</p>
                </div>
              </div>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Request Size</label>
                  <p className="text-sm text-gray-900 dark:text-white">{selectedRequest.requestSize || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Response Size</label>
                  <p className="text-sm text-gray-900 dark:text-white">{selectedRequest.responseSize || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">URL</label>
                  <p className="text-sm text-gray-900 dark:text-white break-all">{selectedRequest.url}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
});

export default RequestDetails;
