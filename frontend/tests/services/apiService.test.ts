import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import apiService from '../../../ui/services/apiService'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Filter Methods', () => {
    const mockFilter = {
      id: 1,
      filter_name: 'Test Filter',
      field: 'url',
      operator: 1,
      value: 'example.com'
    }

    it('should get all filters', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: () => 'application/json'
        },
        json: async () => [mockFilter]
      })

      const result = await apiService.getFilters()

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/filters', {
        headers: {
          'Content-Type': 'application/json',
          'X-Interceptor-Internal': 'true',
          'User-Agent': 'HTTP-Interceptor-UI/1.0'
        }
      })
      expect(result).toEqual([mockFilter])
    })

    it('should handle get filters error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500
      })

      await expect(apiService.getFilters()).rejects.toThrow('HTTP error! status: 500')
    })

    it('should create a filter', async () => {
      const newFilter = { 
        filter_name: 'New Filter',
        field: 'url',
        operator: 1,
        value: 'test.com'
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: () => 'application/json'
        },
        json: async () => ({ ...newFilter, id: 2 })
      })

      const result = await apiService.createFilter(newFilter)

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/filters', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Interceptor-Internal': 'true',
          'User-Agent': 'HTTP-Interceptor-UI/1.0'
        },
        body: JSON.stringify(newFilter)
      })
      expect(result).toEqual({ ...newFilter, id: 2 })
    })

    it('should update a filter', async () => {
      const updates = { filter_name: 'Updated Filter' }
      const updatedFilter = { ...mockFilter, ...updates }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: () => 'application/json'
        },
        json: async () => updatedFilter
      })

      const result = await apiService.updateFilter(1, updates)

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/filters/1', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Interceptor-Internal': 'true',
          'User-Agent': 'HTTP-Interceptor-UI/1.0'
        },
        body: JSON.stringify(updates)
      })
      expect(result).toEqual(updatedFilter)
    })

    it('should delete a filter', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: () => 'application/json'
        },
        json: async () => ({ success: true })
      })

      await apiService.deleteFilter(1)

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/filters/1', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-Interceptor-Internal': 'true',
          'User-Agent': 'HTTP-Interceptor-UI/1.0'
        }
      })
    })
  })

  describe('Rule Methods', () => {
    const mockRule = {
      id: 1,
      rule_name: 'Test Rule',
      filter_id: 1,
      action: 0,
      target_key: 'X-Test',
      target_value: 'test',
      enabled: true
    }

    it('should get all rules', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: () => 'application/json'
        },
        json: async () => [mockRule]
      })

      const result = await apiService.getRules()

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/rules', {
        headers: {
          'Content-Type': 'application/json',
          'X-Interceptor-Internal': 'true',
          'User-Agent': 'HTTP-Interceptor-UI/1.0'
        }
      })
      expect(result).toEqual([mockRule])
    })

    it('should create a rule', async () => {
      const newRule = {
        rule_name: 'New Rule',
        filter_id: 1,
        action: 0,
        target_key: 'X-New',
        target_value: 'new-value',
        enabled: true
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: () => 'application/json'
        },
        json: async () => ({ ...newRule, id: 2 })
      })

      const result = await apiService.createRule(newRule)

      expect(result).toEqual({ ...newRule, id: 2 })
    })

    it('should update a rule', async () => {
      const updates = { rule_name: 'Updated Rule' }
      const updatedRule = { ...mockRule, ...updates }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: () => 'application/json'
        },
        json: async () => updatedRule
      })

      const result = await apiService.updateRule(1, updates)

      expect(result).toEqual(updatedRule)
    })

    it('should delete a rule', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: () => 'application/json'
        },
        json: async () => ({ success: true })
      })

      await apiService.deleteRule(1)

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/rules/1', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-Interceptor-Internal': 'true',
          'User-Agent': 'HTTP-Interceptor-UI/1.0'
        }
      })
    })
  })

  describe('Interception Methods', () => {
    it('should get interception status', async () => {
      const status = { isIntercepting: true, proxyPort: 8080 }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: () => 'application/json'
        },
        json: async () => status
      })

      const result = await apiService.getInterceptionStatus()

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/interception/status', {
        headers: {
          'Content-Type': 'application/json',
          'X-Interceptor-Internal': 'true',
          'User-Agent': 'HTTP-Interceptor-UI/1.0'
        }
      })
      expect(result).toEqual(status)
    })

    it('should start interception', async () => {
      const response = { success: true, message: 'Interception started' }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: () => 'application/json'
        },
        json: async () => response
      })

      const result = await apiService.startInterception()

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/interception/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Interceptor-Internal': 'true',
          'User-Agent': 'HTTP-Interceptor-UI/1.0'
        }
      })
      expect(result).toEqual(response)
    })

    it('should stop interception', async () => {
      const response = { success: true, message: 'Interception stopped' }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: () => 'application/json'
        },
        json: async () => response
      })

      const result = await apiService.stopInterception()

      expect(result).toEqual(response)
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(apiService.getFilters()).rejects.toThrow('Network error')
    })

    it('should handle non-JSON responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: () => 'text/plain'
        },
        text: async () => 'Plain text response'
      })

      const result = await apiService.getFilters()

      expect(result).toBe('Plain text response')
    })

    it('should log errors to console', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      mockFetch.mockRejectedValueOnce(new Error('Test error'))

      try {
        await apiService.getFilters()
      } catch {
        // Expected to throw
      }

      expect(consoleSpy).toHaveBeenCalledWith(
        'API request failed: /filters',
        expect.any(Error)
      )

      consoleSpy.mockRestore()
    })
  })
})
