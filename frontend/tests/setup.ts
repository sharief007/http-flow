import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock WebSocket
const mockWebSocket = vi.fn(() => ({
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  send: vi.fn(),
  close: vi.fn(),
  readyState: 1,
})) as any

mockWebSocket.CONNECTING = 0
mockWebSocket.OPEN = 1
mockWebSocket.CLOSING = 2
mockWebSocket.CLOSED = 3

global.WebSocket = mockWebSocket

// Mock localStorage
Object.defineProperty(window, 'localStorage', {
  value: {
    store: {},
    getItem: vi.fn((key) => window.localStorage.store[key] || null),
    setItem: vi.fn((key, value) => {
      window.localStorage.store[key] = value.toString()
    }),
    removeItem: vi.fn((key) => {
      delete window.localStorage.store[key]
    }),
    clear: vi.fn(() => {
      window.localStorage.store = {}
    }),
  },
  writable: true,
})

// Mock scrollTo
window.scrollTo = vi.fn()

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock fetch
global.fetch = vi.fn()

// Mock console methods to avoid test noise
console.error = vi.fn()
console.warn = vi.fn()
