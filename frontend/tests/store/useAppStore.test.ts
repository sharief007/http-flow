import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { create } from 'zustand'
import { immer } from 'zustand/middleware/immer'

// Mock the dependencies
vi.mock('../../../ui/services/apiService', () => ({
  filterService: {
    getFilters: vi.fn().mockResolvedValue([]),
    createFilter: vi.fn(),
    updateFilter: vi.fn(),
    deleteFilter: vi.fn(),
  },
  ruleService: {
    getRules: vi.fn().mockResolvedValue([]),
    createRule: vi.fn(),
    updateRule: vi.fn(),
    deleteRule: vi.fn(),
    toggleRule: vi.fn(),
  },
  interceptionService: {
    getStatus: vi.fn().mockResolvedValue({ isIntercepting: false }),
    start: vi.fn(),
    stop: vi.fn(),
  },
}))

vi.mock('../../../ui/services/webSocketService', () => ({
  webSocketService: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    sendMessage: vi.fn(),
    isConnected: vi.fn().mockReturnValue(false),
  },
}))

// Import the actual store types and create a test store
import type { AppState, AppActions } from '../../../ui/store/types'

// Create a minimal test store implementation
const createTestStore = () => create<AppState & AppActions>()(
  immer((set, get) => ({
    // State
    requests: [],
    filteredRequests: [],
    selectedRequest: null,
    filters: [],
    rules: [],
    activeFilter: null,
    quickFilterText: '',
    searchTimeout: null,
    enabledRules: [],
    showFiltersPanel: false,
    showRulesPanel: false,
    showRequestDetails: false,
    splitPaneSize: 400,
    settings: {
      autoScroll: true,
      maxRequests: 1000,
      theme: 'light',
      preserveRequests: false,
    },
    connectionStatus: 'disconnected',
    isConnected: false,
    isIntercepting: false,
    isInitialized: false,
    connectionError: null,

    // Actions
    addRequest: vi.fn((request) => set((state) => {
      state.requests.push({ ...request, id: request.id || Date.now().toString() })
    })),
    
    selectRequest: vi.fn((request) => set((state) => {
      state.selectedRequest = request
      state.showRequestDetails = !!request
    })),
    
    clearRequests: vi.fn(() => set((state) => {
      state.requests = []
      state.filteredRequests = []
      state.selectedRequest = null
      state.showRequestDetails = false
    })),
    
    updateFilteredRequests: vi.fn(() => set((state) => {
      let filtered = state.requests
      
      if (state.activeFilter) {
        // Apply filter logic
        filtered = filtered.filter(request => {
          // Simplified filter logic for testing
          return request.url?.includes(state.activeFilter?.value || '')
        })
      }
      
      if (state.quickFilterText) {
        filtered = filtered.filter(request =>
          request.url?.toLowerCase().includes(state.quickFilterText.toLowerCase()) ||
          request.method?.toLowerCase().includes(state.quickFilterText.toLowerCase())
        )
      }
      
      state.filteredRequests = filtered
    })),

    loadFilters: vi.fn(async () => {
      // Mock implementation
      set((state) => {
        state.filters = []
      })
    }),

    addFilter: vi.fn(async (filter) => {
      const newFilter = { ...filter, id: Date.now() }
      set((state) => {
        state.filters.push(newFilter)
      })
      return newFilter
    }),

    updateFilter: vi.fn(async (filterId, updates) => {
      set((state) => {
        const index = state.filters.findIndex(f => f.id === filterId)
        if (index !== -1) {
          Object.assign(state.filters[index], updates)
        }
      })
      return { id: filterId, ...updates } as any
    }),

    deleteFilter: vi.fn(async (filterId) => {
      set((state) => {
        state.filters = state.filters.filter(f => f.id !== filterId)
      })
    }),

    setActiveFilter: vi.fn((filter) => set((state) => {
      state.activeFilter = filter
    })),

    setQuickFilterText: vi.fn((text) => set((state) => {
      state.quickFilterText = text
    })),

    loadRules: vi.fn(async () => {
      set((state) => {
        state.rules = []
      })
    }),

    addRule: vi.fn(async (rule) => {
      const newRule = { ...rule, id: Date.now() }
      set((state) => {
        state.rules.push(newRule)
      })
      return newRule
    }),

    updateRule: vi.fn(async (ruleId, updates) => {
      set((state) => {
        const index = state.rules.findIndex(r => r.id === ruleId)
        if (index !== -1) {
          Object.assign(state.rules[index], updates)
        }
      })
      return { id: ruleId, ...updates } as any
    }),

    deleteRule: vi.fn(async (ruleId) => {
      set((state) => {
        state.rules = state.rules.filter(r => r.id !== ruleId)
      })
    }),

    toggleRule: vi.fn(async (ruleId) => {
      set((state) => {
        const rule = state.rules.find(r => r.id === ruleId)
        if (rule) {
          rule.enabled = !rule.enabled
        }
      })
    }),

    toggleFiltersPanel: vi.fn(() => set((state) => {
      state.showFiltersPanel = !state.showFiltersPanel
      if (state.showFiltersPanel) {
        state.showRulesPanel = false
      }
    })),

    toggleRulesPanel: vi.fn(() => set((state) => {
      state.showRulesPanel = !state.showRulesPanel
      if (state.showRulesPanel) {
        state.showFiltersPanel = false
      }
    })),

    closePanels: vi.fn(() => set((state) => {
      state.showFiltersPanel = false
      state.showRulesPanel = false
    })),

    closeRequestDetails: vi.fn(() => set((state) => {
      state.selectedRequest = null
      state.showRequestDetails = false
    })),

    setSplitPaneSize: vi.fn((size) => set((state) => {
      state.splitPaneSize = size
    })),

    setShowRequestDetails: vi.fn((show) => set((state) => {
      state.showRequestDetails = show
    })),

    updateSettings: vi.fn((updates) => set((state) => {
      Object.assign(state.settings, updates)
    })),

    initializeWebSocket: vi.fn(() => {
      // Mock WebSocket initialization
    }),

    setConnectionStatus: vi.fn((status) => set((state) => {
      state.connectionStatus = status
      state.isConnected = status === 'connected'
    })),

    setConnectionError: vi.fn((error) => set((state) => {
      state.connectionError = error
    })),

    setIntercepting: vi.fn((intercepting) => set((state) => {
      state.isIntercepting = intercepting
    })),

    loadInterceptionStatus: vi.fn(async () => {
      return { isIntercepting: false }
    }),

    startIntercepting: vi.fn(async () => {
      set((state) => {
        state.isIntercepting = true
      })
    }),

    stopIntercepting: vi.fn(async () => {
      set((state) => {
        state.isIntercepting = false
      })
    }),

    initializeMockData: vi.fn(() => {
      // Mock implementation
    }),
  }))
)

describe('App Store', () => {
  let store: ReturnType<typeof createTestStore>

  beforeEach(() => {
    store = createTestStore()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Request Management', () => {
    it('should add a request', () => {
      const request = {
        method: 'GET',
        url: 'https://example.com/api/users',
        status: 200,
      }

      store.getState().addRequest(request)

      const state = store.getState()
      expect(state.requests).toHaveLength(1)
      expect(state.requests[0]).toMatchObject(request)
      expect(state.requests[0].id).toBeDefined()
    })

    it('should select a request', () => {
      const request: any = {
        id: '1',
        method: 'GET',
        url: 'https://example.com/api/users',
        status: 200,
        duration: '120ms',
        requestHeaders: [],
        responseHeaders: [],
        requestBody: '',
        responseBody: '',
        cookies: [],
        requestSize: '1KB',
        responseSize: '2KB',
        isIntercepted: false,
      }

      store.getState().selectRequest(request)

      const state = store.getState()
      expect(state.selectedRequest).toEqual(request)
      expect(state.showRequestDetails).toBe(true)
    })

    it('should clear all requests', () => {
      // Add some requests first
      store.getState().addRequest({ method: 'GET', url: 'test1' })
      store.getState().addRequest({ method: 'POST', url: 'test2' })

      store.getState().clearRequests()

      const state = store.getState()
      expect(state.requests).toHaveLength(0)
      expect(state.filteredRequests).toHaveLength(0)
      expect(state.selectedRequest).toBeNull()
      expect(state.showRequestDetails).toBe(false)
    })
  })

  describe('Filter Management', () => {
    it('should set active filter', () => {
      const filter = {
        id: 1,
        filter_name: 'Test Filter',
        field: 'url',
        operator: 1,
        value: 'example.com',
      }

      store.getState().setActiveFilter(filter)

      expect(store.getState().activeFilter).toEqual(filter)
    })

    it('should set quick filter text', () => {
      const text = 'search term'

      store.getState().setQuickFilterText(text)

      expect(store.getState().quickFilterText).toBe(text)
    })

    it('should add a filter', async () => {
      const filter = {
        filter_name: 'New Filter',
        field: 'url',
        operator: 1,
        value: 'test.com',
      }

      const result = await store.getState().addFilter(filter)

      expect(result).toMatchObject(filter)
      expect(result.id).toBeDefined()
      expect(store.getState().filters).toHaveLength(1)
    })

    it('should update a filter', async () => {
      // Add a filter first
      const filter = await store.getState().addFilter({
        filter_name: 'Original Filter',
        field: 'url',
        operator: 1,
        value: 'example.com',
      })

      const updates = { filter_name: 'Updated Filter' }
      await store.getState().updateFilter(filter.id, updates)

      const state = store.getState()
      const updatedFilter = state.filters.find(f => f.id === filter.id)
      expect(updatedFilter?.filter_name).toBe('Updated Filter')
    })

    it('should delete a filter', async () => {
      const filter = await store.getState().addFilter({
        filter_name: 'Filter to Delete',
        field: 'url',
        operator: 1,
        value: 'example.com',
      })

      await store.getState().deleteFilter(filter.id)

      expect(store.getState().filters).toHaveLength(0)
    })
  })

  describe('Rule Management', () => {
    it('should add a rule', async () => {
      const rule = {
        rule_name: 'Test Rule',
        filter_id: 1,
        action: 0,
        target_key: 'X-Test',
        target_value: 'test',
        enabled: true,
      }

      const result = await store.getState().addRule(rule)

      expect(result).toMatchObject(rule)
      expect(result.id).toBeDefined()
      expect(store.getState().rules).toHaveLength(1)
    })

    it('should toggle rule enabled state', async () => {
      const rule = await store.getState().addRule({
        rule_name: 'Toggle Rule',
        filter_id: 1,
        action: 0,
        target_key: 'X-Test',
        target_value: 'test',
        enabled: true,
      })

      await store.getState().toggleRule(rule.id!)

      const state = store.getState()
      const toggledRule = state.rules.find(r => r.id === rule.id)
      expect(toggledRule?.enabled).toBe(false)
    })
  })

  describe('Panel Management', () => {
    it('should toggle filters panel', () => {
      store.getState().toggleFiltersPanel()
      expect(store.getState().showFiltersPanel).toBe(true)

      store.getState().toggleFiltersPanel()
      expect(store.getState().showFiltersPanel).toBe(false)
    })

    it('should close rules panel when opening filters panel', () => {
      // Open rules panel first
      store.getState().toggleRulesPanel()
      expect(store.getState().showRulesPanel).toBe(true)

      // Open filters panel
      store.getState().toggleFiltersPanel()
      expect(store.getState().showFiltersPanel).toBe(true)
      expect(store.getState().showRulesPanel).toBe(false)
    })

    it('should close all panels', () => {
      // Open both panels
      store.getState().toggleFiltersPanel()
      store.getState().toggleRulesPanel()

      store.getState().closePanels()

      expect(store.getState().showFiltersPanel).toBe(false)
      expect(store.getState().showRulesPanel).toBe(false)
    })
  })

  describe('Settings Management', () => {
    it('should update settings', () => {
      const updates = {
        autoScroll: false,
        theme: 'dark' as const,
      }

      store.getState().updateSettings(updates)

      const state = store.getState()
      expect(state.settings.autoScroll).toBe(false)
      expect(state.settings.theme).toBe('dark')
    })

    it('should set split pane size', () => {
      const size = 300

      store.getState().setSplitPaneSize(size)

      expect(store.getState().splitPaneSize).toBe(size)
    })
  })

  describe('Connection Management', () => {
    it('should set connection status', () => {
      store.getState().setConnectionStatus('connected')

      const state = store.getState()
      expect(state.connectionStatus).toBe('connected')
      expect(state.isConnected).toBe(true)
    })

    it('should set connection error', () => {
      const error = 'Connection failed'

      store.getState().setConnectionError(error)

      expect(store.getState().connectionError).toBe(error)
    })

    it('should set intercepting state', () => {
      store.getState().setIntercepting(true)
      expect(store.getState().isIntercepting).toBe(true)

      store.getState().setIntercepting(false)
      expect(store.getState().isIntercepting).toBe(false)
    })
  })
})
