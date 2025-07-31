import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import App from '../../../ui/App'

// Mock the hooks and store
vi.mock('../../../ui/hooks/useInitialization', () => ({
  useInitialization: vi.fn(),
}))

vi.mock('../../../ui/store/useAppStore', () => ({
  useAppStore: vi.fn((selector) => 
    selector({
      selectedRequest: null,
      showRequestDetails: false,
      showFiltersPanel: false,
      showRulesPanel: false,
      toggleFiltersPanel: vi.fn(),
      toggleRulesPanel: vi.fn(),
    })
  ),
}))

// Mock the components
vi.mock('../../../ui/components/Toolbar', () => ({
  default: () => <div data-testid="toolbar">Toolbar</div>,
}))

vi.mock('../../../ui/components/RequestDetails', () => ({
  default: () => <div data-testid="request-details">Request Details</div>,
}))

vi.mock('../../../ui/components/RequestsTable', () => ({
  default: () => <div data-testid="requests-table">Requests Table</div>,
}))

vi.mock('../../../ui/components/RulesDrawer', () => ({
  default: ({ isOpened, onClose }: { isOpened: boolean; onClose: () => void }) => (
    <div data-testid="rules-drawer" data-opened={isOpened} onClick={onClose}>
      Rules Drawer
    </div>
  ),
}))

vi.mock('../../../ui/components/FiltersDrawer', () => ({
  default: ({ isOpened, onClose }: { isOpened: boolean; onClose: () => void }) => (
    <div data-testid="filters-drawer" data-opened={isOpened} onClick={onClose}>
      Filters Drawer
    </div>
  ),
}))

describe('App Component', () => {
  let mockUseAppStore: any

  beforeEach(() => {
    const { useAppStore } = vi.mocked(await import('../../../ui/store/useAppStore'))
    mockUseAppStore = useAppStore as any
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<App />)
    
    expect(screen.getByTestId('toolbar')).toBeInTheDocument()
    expect(screen.getByTestId('requests-table')).toBeInTheDocument()
  })

  it('does not show request details when no request is selected', () => {
    mockUseAppStore.mockImplementation((selector: any) =>
      selector({
        selectedRequest: null,
        showRequestDetails: false,
        showFiltersPanel: false,
        showRulesPanel: false,
        toggleFiltersPanel: vi.fn(),
        toggleRulesPanel: vi.fn(),
      })
    )

    render(<App />)
    
    expect(screen.queryByTestId('request-details')).not.toBeInTheDocument()
  })

  it('shows request details when a request is selected and showRequestDetails is true', () => {
    mockUseAppStore.mockImplementation((selector: any) =>
      selector({
        selectedRequest: { id: '1', method: 'GET', url: 'http://example.com' },
        showRequestDetails: true,
        showFiltersPanel: false,
        showRulesPanel: false,
        toggleFiltersPanel: vi.fn(),
        toggleRulesPanel: vi.fn(),
      })
    )

    render(<App />)
    
    expect(screen.getByTestId('request-details')).toBeInTheDocument()
  })

  it('shows filters drawer when showFiltersPanel is true', () => {
    mockUseAppStore.mockImplementation((selector: any) =>
      selector({
        selectedRequest: null,
        showRequestDetails: false,
        showFiltersPanel: true,
        showRulesPanel: false,
        toggleFiltersPanel: vi.fn(),
        toggleRulesPanel: vi.fn(),
      })
    )

    render(<App />)
    
    const filtersDrawer = screen.getByTestId('filters-drawer')
    expect(filtersDrawer).toBeInTheDocument()
    expect(filtersDrawer.getAttribute('data-opened')).toBe('true')
  })

  it('shows rules drawer when showRulesPanel is true', () => {
    mockUseAppStore.mockImplementation((selector: any) =>
      selector({
        selectedRequest: null,
        showRequestDetails: false,
        showFiltersPanel: false,
        showRulesPanel: true,
        toggleFiltersPanel: vi.fn(),
        toggleRulesPanel: vi.fn(),
      })
    )

    render(<App />)
    
    const rulesDrawer = screen.getByTestId('rules-drawer')
    expect(rulesDrawer).toBeInTheDocument()
    expect(rulesDrawer.getAttribute('data-opened')).toBe('true')
  })

  it('handles mouse events for split pane resizing', async () => {
    const user = userEvent.setup()
    
    mockUseAppStore.mockImplementation((selector: any) =>
      selector({
        selectedRequest: { id: '1', method: 'GET', url: 'http://example.com' },
        showRequestDetails: true,
        showFiltersPanel: false,
        showRulesPanel: false,
        toggleFiltersPanel: vi.fn(),
        toggleRulesPanel: vi.fn(),
      })
    )

    render(<App />)
    
    // Find resize handle (it should exist when request details are shown)
    const resizeHandle = screen.getByRole('button', { name: /resize/i })
    expect(resizeHandle).toBeInTheDocument()
    
    // Test mouse down on resize handle
    await user.pointer({ target: resizeHandle, keys: '[MouseLeft>]' })
    
    // The cursor style should change during drag
    expect(document.body.style.cursor).toBeTruthy()
  })
})
