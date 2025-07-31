// ui/store/useAppStore.ts
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import webSocketService from '../services/webSocketService';
import apiService from '../services/apiService';
import type { AppStore, HttpFlow, Filter, AppSettings } from './types';

export const useAppStore = create<AppStore>()(
  immer((set, get) => {
    // Helper function to update filtered requests
    const updateFilteredRequestsInline = (state: any) => {
      let filtered = state.requests;

      // Apply active filter
      if (state.activeFilter) {
        const { field, operator, value } = state.activeFilter;
        const lowerValue = value.toLowerCase();
        
        filtered = filtered.filter((request: HttpFlow) => {
          let requestValue = '';
          
          // Optimize field extraction
          switch (field) {
            case 'url':
              requestValue = request.url?.toLowerCase() || '';
              break;
            case 'method':
              requestValue = request.method?.toLowerCase() || '';
              break;
            case 'body':
              requestValue = request.requestBody?.toLowerCase() || '';
              break;
            default:
              if (field.startsWith('header:')) {
                const headerName = field.substring(7).toLowerCase();
                const header = request.requestHeaders?.find((h: any) => h.name.toLowerCase() === headerName);
                requestValue = header?.value.toLowerCase() || '';
              } else {
                return false; // Unsupported field
              }
          }

          // Optimize operator switch
          switch (operator) {
            case 0: return requestValue.includes(lowerValue); // contains
            case 1: return requestValue === lowerValue; // equals
            case 2: return requestValue.startsWith(lowerValue); // starts_with
            case 3: return requestValue.endsWith(lowerValue); // ends_with
            case 4: // regex
              try {
                return new RegExp(lowerValue, 'i').test(requestValue);
              } catch (e) {
                console.error('Invalid regex:', lowerValue, e);
                return false;
              }
            default:
              return false;
          }
        });
      }

      // Apply quick filter text
      if (state.quickFilterText) {
        const quickText = state.quickFilterText.toLowerCase();
        filtered = filtered.filter((request: HttpFlow) =>
          request.url?.toLowerCase().includes(quickText) ||
          request.method?.toLowerCase().includes(quickText) ||
          request.status?.toString().includes(quickText)
        );
      }

      // Only update if different (avoid unnecessary re-renders)
      if (filtered !== state.filteredRequests) {
        state.filteredRequests = filtered;
      }
    };

    return {
      // Request Management
      requests: [],
      selectedRequest: null,
      isIntercepting: false,

      // Filter Management
      filters: [],
      activeFilter: null,
      quickFilterText: '',
      filteredRequests: [], // Cached filtered requests
      searchTimeout: null, // Debounce timeout for search

      // Rule Management
      rules: [],
      enabledRules: [],

      // UI State
      showFiltersPanel: false,
      showRulesPanel: false,
      showRequestDetails: false,
      splitPaneSize: 60,

      // Settings
      settings: {
        autoScroll: true,
        maxRequests: 1000,
        theme: 'dark',
        preserveRequests: false,
      } as AppSettings,

      // WebSocket Connection State
      isConnected: false,
      connectionStatus: 'disconnected',
      connectionError: null,
      isInitialized: false, // Track if WebSocket has been initialized

      // Actions - Request Management
      addRequest: (newRequest: HttpFlow) =>
        set((state) => {
          // Apply max requests limit
          if (state.requests.length >= state.settings.maxRequests) {
            state.requests = state.requests.slice(-(state.settings.maxRequests - 1));
          }

          state.requests.push(newRequest);
          // Use the helper function instead of duplicating logic
          updateFilteredRequestsInline(state);
        }),

      selectRequest: (request) =>
        set((state) => {
          state.selectedRequest = request;
          state.showRequestDetails = !!request;
        }),

      clearRequests: () =>
        set((state) => {
          state.requests = [];
          state.selectedRequest = null;
          state.showRequestDetails = false;
          state.filteredRequests = [];
        }),

      // Update filtered requests efficiently
      updateFilteredRequests: () =>
        set((state) => {
          updateFilteredRequestsInline(state);
        }),

      // Actions - Filter Management (now using API)
      loadFilters: async () => {
        let filters: Filter[] = [];
        try {
          filters = await apiService.getFilters();
        } catch (error) {
          console.error('Failed to load filters:', error);
        }
        set((state) => {
          state.filters = filters;
        });
      },

      addFilter: async (filter) => {
        try {
          const newFilter = await apiService.createFilter(filter);
          set((state) => {
            state.filters.push(newFilter);
          });
          return newFilter;
        } catch (error) {
          console.error('Failed to create filter:', error);
          throw error;
        }
      },

      updateFilter: async (filterId, updates) => {
        try {
          const updatedFilter = await apiService.updateFilter(filterId, updates);
          set((state) => {
            const index = state.filters.findIndex(f => f.id === filterId);
            if (index !== -1) {
              state.filters[index] = updatedFilter;
            }
          });
          return updatedFilter;
        } catch (error) {
          console.error('Failed to update filter:', error);
          throw error;
        }
      },

      deleteFilter: async (filterId) => {
        try {
          await apiService.deleteFilter(filterId);
          set((state) => {
            state.filters = state.filters.filter(f => f.id !== filterId);
            if (state.activeFilter && state.activeFilter.id === filterId) {
              state.activeFilter = null;
            }
          });
        } catch (error) {
          console.error('Failed to delete filter:', error);
          throw error;
        }
      },

      setActiveFilter: (filter) =>
        set((state) => {
          state.activeFilter = filter;
          updateFilteredRequestsInline(state);
        }),

      // openFiltersDrawer: () =>
      //   set((state) => {
      //     state.isFilterDrawerOpen = true;
      //   }),

      // closeFiltersDrawer: () =>
      //   set((state) => {
      //     state.isFilterDrawerOpen = false;
      //   }),

      setQuickFilterText: (text) =>
        set((state) => {
          state.quickFilterText = text;
          // Debounce the filter update
          if (state.searchTimeout) {
            clearTimeout(state.searchTimeout);
          }
          state.searchTimeout = setTimeout(() => {
            // Use a separate set call for the debounced update
            set((state) => {
              updateFilteredRequestsInline(state);
            });
          }, 300);
        }),

      // Actions - Rule Management (now using API)
      loadRules: async () => {
        try {
          const rules: any[] = await apiService.getRules();
          set((state) => {
            state.rules = rules;
            state.enabledRules = rules.filter((r: any) => r.enabled).map((r: any) => r.id);
          });
        } catch (error) {
          console.error('Failed to load rules:', error);
        }
      },

      addRule: async (rule) => {
        try {
          const newRule = await apiService.createRule(rule);
          set((state) => {
            state.rules.push(newRule);
            if (newRule.enabled) {
              state.enabledRules.push(newRule.id);
            }
          });
          return newRule;
        } catch (error) {
          console.error('Failed to create rule:', error);
          throw error;
        }
      },

      updateRule: async (ruleId, updates) => {
        try {
          const updatedRule = await apiService.updateRule(ruleId, updates);
          set((state) => {
            const index = state.rules.findIndex(r => r.id === ruleId);
            if (index !== -1) {
              state.rules[index] = updatedRule;
              if (updatedRule.enabled && !state.enabledRules.includes(ruleId)) {
                state.enabledRules.push(ruleId);
              } else if (!updatedRule.enabled) {
                state.enabledRules = state.enabledRules.filter(id => id !== ruleId);
              }
            }
          });
          return updatedRule;
        } catch (error) {
          console.error('Failed to update rule:', error);
          throw error;
        }
      },

      deleteRule: async (ruleId) => {
        try {
          await apiService.deleteRule(ruleId);
          set((state) => {
            state.rules = state.rules.filter(r => r.id !== ruleId);
            state.enabledRules = state.enabledRules.filter(id => id !== ruleId);
          });
        } catch (error) {
          console.error('Failed to delete rule:', error);
          throw error;
        }
      },

      toggleRule: async (ruleId) => {
        const rule = get().rules.find(r => r.id === ruleId);
        if (rule) {
          await get().updateRule(ruleId, { ...rule, enabled: !rule.enabled });
        }
      },

      // Actions - UI State
      toggleFiltersPanel: () =>
        set((state) => {
          state.showFiltersPanel = !state.showFiltersPanel;
          if (state.showFiltersPanel) {
            state.showRulesPanel = false;
          }
        }),

      toggleRulesPanel: () =>
        set((state) => {
          state.showRulesPanel = !state.showRulesPanel;
          if (state.showRulesPanel) {
            state.showFiltersPanel = false;
          }
        }),

      closePanels: () =>
        set((state) => {
          state.showFiltersPanel = false;
          state.showRulesPanel = false;
        }),

      closeRequestDetails: () =>
        set((state) => {
          state.selectedRequest = null;
          state.showRequestDetails = false;
        }),

      setSplitPaneSize: (size) =>
        set((state) => {
          state.splitPaneSize = size;
        }),

      setShowRequestDetails: (show) =>
        set((state) => {
          state.showRequestDetails = show;
        }),

      // Actions - Settings
      updateSettings: (updates) =>
        set((state) => {
          Object.assign(state.settings, updates);
        }),

      // WebSocket Actions
      initializeWebSocket: () => {
        const state = get();
        if (state.isInitialized) {
          console.log('WebSocket already initialized');
          return;
        }

        set((state) => {
          state.isInitialized = true;
          state.connectionStatus = 'connecting';
        });

        console.log('Initializing WebSocket connection...');

        // Set up event listeners only once
        webSocketService.on('connected', () => {
          console.log('WebSocket connected');
          get().setConnectionStatus('connected');
          // Load initial data when connected
          get().loadFilters();
          get().loadRules();
        });

        webSocketService.on('disconnected', () => {
          console.log('WebSocket disconnected');
          get().setConnectionStatus('disconnected');
        });

        webSocketService.on('error', (error: any) => {
          console.error('WebSocket error:', error);
          get().setConnectionError(error.error || 'Connection error');
        });

        webSocketService.on('http_flow', (request: any) => {
          get().addRequest(request);
        });

        webSocketService.on('intercepting_started', () => {
          get().setIntercepting(true);
        });

        webSocketService.on('intercepting_stopped', () => {
          get().setIntercepting(false);
        });

        // Connect to the server
        webSocketService.connect();
      },

      setConnectionStatus: (status) =>
        set((state) => {
          state.connectionStatus = status;
          state.isConnected = status === 'connected';
          if (status === 'connected') {
            state.connectionError = null;
          }
        }),

      setConnectionError: (error) =>
        set((state) => {
          state.connectionError = error;
          state.connectionStatus = 'error';
          state.isConnected = false;
        }),

      setIntercepting: (intercepting) =>
        set((state) => {
          state.isIntercepting = intercepting;
        }),

      // Interception Actions (now using API)
      loadInterceptionStatus: async () => {
        let isIntercepting = false;
        try {
          const result = await apiService.getInterceptionStatus();
          console.log('Interception status loaded:', result);
          isIntercepting = result.is_running || false;
        } catch (error) {
          console.error('Failed to load interception status:', error);
        }
        set((state) => { state.isIntercepting = isIntercepting; });
      },

      startIntercepting: async () => {
        let isSuccess = false;
        try {
          const result = await apiService.startInterception();
          console.log('Interception started:', result);
          // The WebSocket will receive the status update
          isSuccess = result.status === "started"
        } catch (error) {
          console.error('Failed to start interception:', error);
        }
        if (isSuccess) {
          set((state) => {
            state.isIntercepting = true;
          });
        }
      },

      stopIntercepting: async () => {
        let isSuccess = false;
        try {
          const result = await apiService.stopInterception();
          console.log('Interception stopped:', result);
          // The WebSocket will receive the status update
          isSuccess = result.status === "stopped"
        } catch (error) {
          console.error('Failed to stop interception:', error);
        }
        if (isSuccess) {
          set((state) => {
            state.isIntercepting = false;
          });
        }
      },

      // Add this to the store after the other actions
      initializeMockData: () =>
        set((state) => {
          console.log('Initializing mock data...');
          const mockRequests: HttpFlow[] = [];
          state.requests = mockRequests;
          updateFilteredRequestsInline(state);
        }),
    };
  })
);
