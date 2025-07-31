// Service type declarations
export interface AbstractApiService {
  getFilters(): Promise<any[]>;
  createFilter(filter: any): Promise<any>;
  updateFilter(filterId: string | number, updates: any): Promise<any>;
  deleteFilter(filterId: string | number, filterData: any): Promise<void>;
  getRules(): Promise<any[]>;
  createRule(rule: any): Promise<any>;
  updateRule(ruleId: string | number, updates: any): Promise<any>;
  deleteRule(ruleId: string | number): Promise<void>;
  startInterception(): Promise<any>;
  stopInterception(): Promise<any>;
}

export interface AbstractWebSocketService {
  on(event: string, callback: (data?: any) => void): void;
  connect(): void;
  disconnect(): void;
}

// declare const apiService: ApiService;
// declare const webSocketService: AbstractWebSocketService;

// export { apiService, webSocketService };
