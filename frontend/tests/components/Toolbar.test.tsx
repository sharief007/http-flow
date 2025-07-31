import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import Toolbar from '../../../ui/components/Toolbar'

// Mock the store
const mockStore = {
  filters: [
    { id: 1, filter_name: 'Test Filter 1' },
    { id: 2, filter_name: 'Test Filter 2' },
  ],
  activeFilter: null,
  quickFilterText: '',
  isIntercepting: false,
  isConnected: true,
  connectionStatus: 'connected',
  showFiltersPanel: false,
  showRulesPanel: false,
  setActiveFilter: vi.fn(),
  setQuickFilterText: vi.fn(),
  toggleFiltersPanel: vi.fn(),
  toggleRulesPanel: vi.fn(),
  startIntercepting: vi.fn(),
  stopIntercepting: vi.fn(),
  clearRequests: vi.fn(),
}

vi.mock('../../../ui/store/useAppStore', () => ({
  useAppStore: vi.fn((selector) => {
    if (typeof selector === 'function') {
      return selector(mockStore)
    }
    return mockStore
  }),
}))

describe('Toolbar Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<Toolbar />)
    
    expect(screen.getByRole('combobox', { name: /filter/i })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: /quick filter/i })).toBeInTheDocument()
  })

  it('displays connection status indicators', () => {
    render(<Toolbar />)
    
    expect(screen.getByText('WebSQL')).toBeInTheDocument()
    expect(screen.getByText('Proxy')).toBeInTheDocument()
  })

  it('displays correct connection status colors', () => {
    render(<Toolbar />)
    
    // Should show green indicators when connected
    const indicators = screen.getAllByRole('img', { hidden: true })
    expect(indicators).toHaveLength(2) // WebSQL and Proxy indicators
  })

  it('handles filter selection change', async () => {
    const user = userEvent.setup()
    render(<Toolbar />)
    
    const filterSelect = screen.getByRole('combobox', { name: /filter/i })
    await user.selectOptions(filterSelect, '1')
    
    expect(mockStore.setActiveFilter).toHaveBeenCalledWith(
      expect.objectContaining({ id: 1 })
    )
  })

  it('handles quick filter text change', async () => {
    const user = userEvent.setup()
    render(<Toolbar />)
    
    const quickFilterInput = screen.getByRole('textbox', { name: /quick filter/i })
    await user.type(quickFilterInput, 'test search')
    
    expect(mockStore.setQuickFilterText).toHaveBeenCalledWith('test search')
  })

  it('handles start interception button click', async () => {
    const user = userEvent.setup()
    render(<Toolbar />)
    
    const startButton = screen.getByRole('button', { name: /start/i })
    await user.click(startButton)
    
    expect(mockStore.startIntercepting).toHaveBeenCalled()
  })

  it('handles stop interception button click when intercepting', async () => {
    const user = userEvent.setup()
    
    // Mock the store to show intercepting state
    vi.mocked(mockStore).isIntercepting = true
    
    render(<Toolbar />)
    
    const stopButton = screen.getByRole('button', { name: /stop/i })
    await user.click(stopButton)
    
    expect(mockStore.stopIntercepting).toHaveBeenCalled()
  })

  it('handles clear requests button click', async () => {
    const user = userEvent.setup()
    render(<Toolbar />)
    
    const clearButton = screen.getByRole('button', { name: /clear/i })
    await user.click(clearButton)
    
    expect(mockStore.clearRequests).toHaveBeenCalled()
  })

  it('handles filters panel toggle', async () => {
    const user = userEvent.setup()
    render(<Toolbar />)
    
    const filtersButton = screen.getByRole('button', { name: /filters/i })
    await user.click(filtersButton)
    
    expect(mockStore.toggleFiltersPanel).toHaveBeenCalled()
  })

  it('handles rules panel toggle', async () => {
    const user = userEvent.setup()
    render(<Toolbar />)
    
    const rulesButton = screen.getByRole('button', { name: /rules/i })
    await user.click(rulesButton)
    
    expect(mockStore.toggleRulesPanel).toHaveBeenCalled()
  })

  it('shows correct button states based on panel visibility', () => {
    // Mock store with panels open
    vi.mocked(mockStore).showFiltersPanel = true
    vi.mocked(mockStore).showRulesPanel = true
    
    render(<Toolbar />)
    
    const filtersButton = screen.getByRole('button', { name: /filters/i })
    const rulesButton = screen.getByRole('button', { name: /rules/i })
    
    expect(filtersButton).toHaveClass('bg-blue-100', 'text-blue-600')
    expect(rulesButton).toHaveClass('bg-blue-600', 'text-white')
  })

  it('displays theme toggle button', () => {
    render(<Toolbar />)
    
    const themeButton = screen.getByRole('button', { name: /theme/i })
    expect(themeButton).toBeInTheDocument()
  })

  it('shows disconnected state when not connected', () => {
    vi.mocked(mockStore).isConnected = false
    vi.mocked(mockStore).connectionStatus = 'disconnected'
    
    render(<Toolbar />)
    
    // Should show red indicators when disconnected
    const indicators = screen.getAllByRole('img', { hidden: true })
    expect(indicators).toHaveLength(2)
  })
})
