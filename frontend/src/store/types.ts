
export interface HttpFlow {
  id: string;
  method: string;
  url: string;
  status: number;
  duration: string;
  requestHeaders: Record<string, string>[];
  responseHeaders: Record<string, string>[];
  requestBody: string;
  responseBody: string;
  cookies: Record<string, string>[];
  requestSize: string;
  responseSize: string;
  isIntercepted: boolean;
}

export interface Filter {
  id: string | number;
  field: string;
  operator: number;
  value: string;
  filter_name: string; 
}

export interface Rule {
  id?: string | number;
  rule_name: string;
  filter_id: number;
  action: number; // RuleAction enum value
  target_key: string;
  target_value: string;
  enabled: boolean;
}

export interface AppSettings {
  autoScroll: boolean;
  maxRequests: number;
  theme: 'light' | 'dark';
  preserveRequests: boolean;
}

export interface ConnectionStatus {
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  connectionError: string | null;
  isInitialized: boolean;
}

export interface AppState extends ConnectionStatus {
  // Request Management
  requests: HttpFlow[];
  selectedRequest: HttpFlow | null;
  isIntercepting: boolean;

  // Filter Management
  filters: Filter[];
  activeFilter: Filter | null;
  quickFilterText: string;
  filteredRequests: HttpFlow[];
  searchTimeout: NodeJS.Timeout | null;

  // Rule Management
  rules: Rule[];
  enabledRules: (string | number)[];

  // UI State
  showFiltersPanel: boolean;
  showRulesPanel: boolean;
  showRequestDetails: boolean;
  splitPaneSize: number;

  // Settings
  settings: AppSettings;
}

export interface AppActions {
  // Request Management
  addRequest: (request: Partial<HttpFlow>) => void;
  // updateRequest: (requestId: string | number, updates: Partial<HttpFlow>) => void;
  selectRequest: (request: HttpFlow | null) => void;
  clearRequests: () => void;
  updateFilteredRequests: () => void;

  // Filter Management
  loadFilters: () => Promise<void>;
  addFilter: (filter: Omit<Filter, 'id'>) => Promise<Filter>;
  updateFilter: (filterId: string | number, updates: Partial<Filter>) => Promise<Filter>;
  deleteFilter: (filterId: string | number) => Promise<void>;
  setActiveFilter: (filter: Filter | null) => void;
  setQuickFilterText: (text: string) => void;

  // Rule Management
  loadRules: () => Promise<void>;
  addRule: (rule: Omit<Rule, 'id'>) => Promise<Rule>;
  updateRule: (ruleId: string | number, updates: Partial<Rule>) => Promise<Rule>;
  deleteRule: (ruleId: string | number) => Promise<void>;
  toggleRule: (ruleId: string | number) => Promise<void>;

  // UI State
  toggleFiltersPanel: () => void;
  toggleRulesPanel: () => void;
  closePanels: () => void;
  closeRequestDetails: () => void;
  setSplitPaneSize: (size: number) => void;
  setShowRequestDetails: (show: boolean) => void;

  // Settings
  updateSettings: (updates: Partial<AppSettings>) => void;

  // WebSocket Actions
  initializeWebSocket: () => void;
  setConnectionStatus: (status: ConnectionStatus['connectionStatus']) => void;
  setConnectionError: (error: string) => void;
  setIntercepting: (intercepting: boolean) => void;

  // Interception Actions
  loadInterceptionStatus: () => Promise<any>;
  startIntercepting: () => Promise<void>;
  stopIntercepting: () => Promise<void>;

  // Mock Data (for development)
  initializeMockData: () => void;
}

export type AppStore = AppState & AppActions;
