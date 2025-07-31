import { AbstractApiService } from "../models/types";

const API_BASE_URL = 'http://localhost:8000/api';

interface RequestOptions extends RequestInit {
  headers?: Record<string, string>;
}

class ApiService implements AbstractApiService {
  private baseURL: string;

  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request<T = any>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        'X-Interceptor-Internal': 'true',  // Mark as internal request
        'User-Agent': 'HTTP-Interceptor-UI/1.0',  // Custom user agent
        ...options.headers,
      },
      ...options,
    };

    if (config.body && typeof config.body === 'object') {
      config.body = JSON.stringify(config.body);
    }

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.toLowerCase().includes('application/json')) {
        return await response.json();
      }
      
      return await response.text() as T;
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Filter-related methods
  async getFilters(): Promise<any[]> {
    return this.request('/filters');
  }

  async createFilter(filterData: any): Promise<any> {
    return this.request('/filters', {
      method: 'POST',
      body: filterData,
    });
  }

  async updateFilter(filterId: string | number, filterData: any): Promise<any> {
    return this.request(`/filters/${filterId}`, {
      method: 'PUT',
      body: filterData,
    });
  }

  async deleteFilter(filterId: string | number): Promise<void> {
    return this.request(`/filters/${filterId}`, {
      method: 'DELETE',
    });
  }

  // Rule-related methods
  async getRules(): Promise<any[]> {
    return this.request('/rules');
  }

  async createRule(ruleData: any): Promise<any> {
    return this.request('/rules', {
      method: 'POST',
      body: ruleData,
    });
  }

  async updateRule(ruleId: string | number, ruleData: any): Promise<any> {
    return this.request(`/rules/${ruleId}`, {
      method: 'PUT',
      body: ruleData,
    });
  }

  async deleteRule(ruleId: string | number): Promise<void> {
    return this.request(`/rules/${ruleId}`, {
      method: 'DELETE',
    });
  }

  // Interception control methods
  async startInterception(): Promise<any> {
    return this.request('/interception/start', {
      method: 'POST',
    });
  }

  async stopInterception(): Promise<any> {
    return this.request('/interception/stop', {
      method: 'POST',
    });
  }

  async getInterceptionStatus(): Promise<any> {
    return this.request('/interception/status');
  }
}

export default new ApiService();
