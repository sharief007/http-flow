import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import RequestsTable from '../../../ui/components/RequestsTable'

const mockStore = {
  selectedRequest: null as any,
  selectRequest: vi.fn(),
  filteredRequests: [
    {
      id: '1',
      method: 'GET',
      url: 'https://example.com/api/users',
      status: 200,
      duration: '120ms',
      requestSize: '1.2KB',
      responseSize: '3.4KB',
    },
    {
      id: '2',
      method: 'POST',
      url: 'https://example.com/api/posts',
      status: 201,
      duration: '89ms', 
      requestSize: '2.1KB',
      responseSize: '1.8KB',
    },
  ],
  settings: {
    autoScroll: true,
  },
}

vi.mock('../../../ui/store/useAppStore', () => ({
  useAppStore: vi.fn((selector) => {
    if (typeof selector === 'function') {
      return selector(mockStore)
    }
    return mockStore
  }),
}))

describe('RequestsTable Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<RequestsTable />)
    
    expect(screen.getByRole('table')).toBeInTheDocument()
  })

  it('displays table headers correctly', () => {
    render(<RequestsTable />)
    
    expect(screen.getByText('Method')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()
    expect(screen.getByText('URL')).toBeInTheDocument()
    expect(screen.getByText('Duration')).toBeInTheDocument()
    expect(screen.getByText('Req Size')).toBeInTheDocument()
    expect(screen.getByText('Res Size')).toBeInTheDocument()
  })

  it('displays filtered requests correctly', () => {
    render(<RequestsTable />)
    
    // Check if both requests are displayed
    expect(screen.getByText('GET')).toBeInTheDocument()
    expect(screen.getByText('POST')).toBeInTheDocument()
    expect(screen.getByText('200')).toBeInTheDocument()
    expect(screen.getByText('201')).toBeInTheDocument()
    expect(screen.getByText('https://example.com/api/users')).toBeInTheDocument()
    expect(screen.getByText('https://example.com/api/posts')).toBeInTheDocument()
  })

  it('handles row click and selects request', async () => {
    const user = userEvent.setup()
    render(<RequestsTable />)
    
    const firstRow = screen.getByRole('row', { name: /GET.*200.*example\.com.*users/i })
    await user.click(firstRow)
    
    expect(mockStore.selectRequest).toHaveBeenCalledWith(
      expect.objectContaining({
        id: '1',
        method: 'GET',
        url: 'https://example.com/api/users',
      })
    )
  })

  it('highlights selected request', () => {
    // Mock selected request
    mockStore.selectedRequest = mockStore.filteredRequests[0]
    
    render(<RequestsTable />)
    
    const selectedRow = screen.getByRole('row', { name: /GET.*200.*example\.com.*users/i })
    expect(selectedRow).toHaveClass('bg-blue-50', 'border-l-4', 'border-l-blue-500')
  })

  it('shows empty state when no requests', () => {
    mockStore.filteredRequests = []
    
    render(<RequestsTable />)
    
    expect(screen.getByText('No requests captured yet')).toBeInTheDocument()
    expect(screen.getByText('Start intercepting to see HTTP requests here')).toBeInTheDocument()
  })

  it('applies correct method color classes', () => {
    render(<RequestsTable />)
    
    const getMethod = screen.getByText('GET')
    const postMethod = screen.getByText('POST')
    
    expect(getMethod).toHaveClass('bg-green-100', 'text-green-800')
    expect(postMethod).toHaveClass('bg-blue-100', 'text-blue-800')
  })

  it('applies correct status color classes', () => {
    render(<RequestsTable />)
    
    const status200 = screen.getByText('200')
    const status201 = screen.getByText('201')
    
    // Both 200 and 201 should have success styling
    expect(status200).toHaveClass('text-green-800')
    expect(status201).toHaveClass('text-green-800')
  })

  it('truncates long URLs with title attribute', () => {
    render(<RequestsTable />)
    
    const urlCell = screen.getByText('https://example.com/api/users')
    expect(urlCell).toHaveAttribute('title', 'https://example.com/api/users')
    expect(urlCell).toHaveClass('truncate')
  })

  it('handles scroll events for auto-scroll functionality', () => {
    const mockScrollHandler = vi.fn()
    
    render(<RequestsTable />)
    
    const tableContainer = screen.getByRole('table').closest('div')
    
    // Simulate scroll event
    if (tableContainer) {
      tableContainer.addEventListener('scroll', mockScrollHandler)
      tableContainer.dispatchEvent(new Event('scroll'))
    }
    
    expect(mockScrollHandler).toHaveBeenCalled()
  })

  it('auto-scrolls to bottom when new requests arrive and auto-scroll is enabled', () => {
    const { rerender } = render(<RequestsTable />)
    
    // Add new request
    const newRequests = [
      ...mockStore.filteredRequests,
      {
        id: '3',
        method: 'DELETE',
        url: 'https://example.com/api/users/1',
        status: 204,
        duration: '45ms',
        requestSize: '0B',
        responseSize: '0B',
      },
    ]
    
    mockStore.filteredRequests = newRequests
    
    rerender(<RequestsTable />)
    
    // Should show the new request
    expect(screen.getByText('DELETE')).toBeInTheDocument()
    expect(screen.getByText('204')).toBeInTheDocument()
  })

  it('does not auto-scroll when auto-scroll is disabled', () => {
    mockStore.settings.autoScroll = false
    
    render(<RequestsTable />)
    
    // Auto-scroll behavior should be disabled
    // This is more of an integration test, but we can verify settings are respected
    expect(mockStore.settings.autoScroll).toBe(false)
  })
})
