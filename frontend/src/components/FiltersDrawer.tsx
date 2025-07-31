import React, { memo, useState, useCallback, useMemo } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Filter } from '../store/types';

// Simple SVG icons
const FilterIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
    <path d="M10 18h4v-2h-4v2zM3 6v2h18V6H3zm3 7h12v-2H6v2z"/>
  </svg>
);

const PlusIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
    <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
  </svg>
);

const EditIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
  </svg>
);

const TrashIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
  </svg>
);

const AlertIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
  </svg>
);

const CheckIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
  </svg>
);

const SearchIcon = ({ className }: { className?: string }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
  </svg>
);

export interface FiltersDrawerProps {
  isOpened: boolean;
  onClose: () => void;
}

interface FormData {
  filter_name: string;
  field: string;
  headerName: string; // For when field is "header"
  operator: number;
  value: string;
}

// Operator enum mapping (matches backend Operator enum)
const OPERATORS = {
  CONTAINS: 0,
  EQUALS: 1,
  STARTS_WITH: 2,
  ENDS_WITH: 3,
  REGEX: 4
} as const;

// Toast notification component
const Toast = memo(({ message, type, onClose }: { message: string; type: 'success' | 'error'; onClose: () => void }) => (
  <div className={`fixed top-4 right-4 z-60 flex items-center gap-2 px-4 py-3 rounded-md shadow-lg transition-all duration-300 ${
    type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
  }`}>
    {type === 'success' ? <CheckIcon /> : <AlertIcon />}
    <span>{message}</span>
    <button onClick={onClose} className="ml-2 text-white hover:text-gray-200">✕</button>
  </div>
));

Toast.displayName = 'Toast';

// Memoized filter item component for better performance
const FilterItem = memo(({ 
  filter, 
  onEdit, 
  onDelete 
}: { 
  filter: Filter; 
  onEdit: (filter: Filter) => void; 
  onDelete: (filter: Filter) => void; 
}) => (
  <div className="p-3 border border-gray-200 dark:border-gray-700 rounded-md bg-gray-50 dark:bg-gray-800">
    <div className="flex justify-between items-center">
      <span className="font-medium text-gray-900 dark:text-white truncate">
        {filter.filter_name}
      </span>
      <div className="flex gap-1">
        <button
          onClick={() => onEdit(filter)}
          className="p-1 text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
          title="Edit filter"
        >
          <EditIcon />
        </button>
        <button
          onClick={() => onDelete(filter)}
          className="p-1 text-gray-600 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400"
          title="Delete filter"
        >
          <TrashIcon />
        </button>
      </div>
    </div>
  </div>
));

FilterItem.displayName = 'FilterItem';

export const FiltersDrawer: React.FC<FiltersDrawerProps> = memo((props: FiltersDrawerProps) => {
  const { isOpened, onClose } = props;
  const {
    filters,
    addFilter,
    updateFilter,
    deleteFilter,
  } = useAppStore();

  const [editingFilter, setEditingFilter] = useState<Filter | null>(null);
  const [loading, setLoading] = useState(false);
  const [createModalOpened, setCreateModalOpened] = useState(false);
  const [deleteModalOpened, setDeleteModalOpened] = useState(false);
  const [filterToDelete, setFilterToDelete] = useState<Filter | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Form state with proper types
  const [formData, setFormData] = useState<FormData>({
    filter_name: '',
    field: '',
    headerName: '',
    operator: OPERATORS.EQUALS,
    value: ''
  });

  // Filtered filters based on search query
  const filteredFilters = useMemo(() => {
    if (!searchQuery.trim()) return filters;
    
    const query = searchQuery.toLowerCase();
    return filters.filter(filter => 
      filter.filter_name?.toLowerCase().includes(query) ||
      filter.field?.toLowerCase().includes(query) ||
      filter.value?.toLowerCase().includes(query)
    );
  }, [filters, searchQuery]);

  // Memoized field options
  const fieldOptions = useMemo(() => [
    { value: 'url', label: 'URL' },
    { value: 'method', label: 'Method' },
    { value: 'body', label: 'Body' },
    { value: 'header', label: 'Header' },
  ], []);

  // Memoized operator options
  const operatorOptions = useMemo(() => [
    { value: OPERATORS.EQUALS, label: 'Equals' },
    { value: OPERATORS.CONTAINS, label: 'Contains' },
    { value: OPERATORS.STARTS_WITH, label: 'Starts With' },
    { value: OPERATORS.ENDS_WITH, label: 'Ends With' },
    { value: OPERATORS.REGEX, label: 'Regex' },
  ], []);

  // Show toast notification with auto-hide
  const showToast = useCallback((message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    // Auto-hide toast after 4 seconds
    const timeoutId = setTimeout(() => setToast(null), 4000);
    
    // Clear any existing timeout to prevent memory leaks
    return () => clearTimeout(timeoutId);
  }, []);

  // Reset form to initial state
  const resetForm = useCallback(() => {
    setFormData({
      filter_name: '',
      field: '',
      headerName: '',
      operator: OPERATORS.EQUALS,
      value: ''
    });
  }, []);

  const handleOpenCreateModal = useCallback(() => {
    setEditingFilter(null);
    resetForm();
    setCreateModalOpened(true);
  }, [resetForm]);

  const handleOpenEditModal = useCallback((filter: Filter) => {
    setEditingFilter(filter);
    
    // Parse field for header case
    let field = filter.field || '';
    let headerName = '';
    if (field.startsWith('header:')) {
      headerName = field.substring(7);
      field = 'header';
    }
    
    setFormData({
      filter_name: filter.filter_name || '',
      field,
      headerName,
      operator: typeof filter.operator === 'number' ? filter.operator : OPERATORS.EQUALS,
      value: filter.value || ''
    });
    setCreateModalOpened(true);
  }, []);

  const openDeleteConfirmation = useCallback((filter: Filter) => {
    setFilterToDelete(filter);
    setDeleteModalOpened(true);
  }, []);

  const handleSaveFilter = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!formData.filter_name.trim() || !formData.field || !formData.value.trim()) {
      showToast('All fields are required', 'error');
      return;
    }

    if (formData.field === 'header' && !formData.headerName.trim()) {
      showToast('Header name is required when field is Header', 'error');
      return;
    }

    // Prevent multiple submissions
    if (loading) return;
    
    setLoading(true);
    try {
      // Construct field value for backend
      const field = formData.field === 'header' 
        ? `header:${formData.headerName.trim()}`
        : formData.field;

      const filterPayload = {
        name: formData.filter_name.trim(),
        filter_name: formData.filter_name.trim(),
        field,
        operator: formData.operator,
        value: formData.value.trim()
      };

      if (editingFilter) {
        // Only use store method - it handles API call internally
        await updateFilter(editingFilter.id!, filterPayload);
        showToast('Filter updated successfully', 'success');
      } else {
        // Only use store method - it handles API call internally
        await addFilter(filterPayload);
        showToast('Filter created successfully', 'success');
      }
      
      setCreateModalOpened(false);
      setEditingFilter(null);
      resetForm();
    } catch (error) {
      console.error('Error saving filter:', error);
      showToast(
        editingFilter ? 'Failed to update filter' : 'Failed to create filter',
        'error'
      );
    } finally {
      setLoading(false);
    }
  }, [formData, loading, editingFilter, updateFilter, addFilter, showToast, resetForm]);

  const handleDeleteFilter = useCallback(async () => {
    if (!filterToDelete || loading) return;
    
    setLoading(true);
    try {
      // Only use store method - it handles API call internally
      await deleteFilter(filterToDelete.id!);
      setDeleteModalOpened(false);
      setFilterToDelete(null);
      showToast('Filter deleted successfully', 'success');
    } catch (error) {
      console.error('Error deleting filter:', error);
      showToast('Failed to delete filter', 'error');
    } finally {
      setLoading(false);
    }
  }, [filterToDelete, loading, deleteFilter, showToast]);

  // Optimized form field update handlers to prevent unnecessary re-renders
  const handleFieldChange = useCallback((value: string) => {
    setFormData(prev => ({
      ...prev,
      field: value,
      headerName: value === 'header' ? prev.headerName : '' // Reset header name if not header field
    }));
  }, []);

  const handleFormChange = useCallback((field: keyof FormData, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  // Close modal handler to prevent multiple event listeners
  const handleCloseModal = useCallback(() => {
    setEditingFilter(null);
    setCreateModalOpened(false);
    resetForm();
  }, [resetForm]);

  const handleCloseDeleteModal = useCallback(() => {
    setDeleteModalOpened(false);
    setFilterToDelete(null);
  }, []);

  // Determine if header name field should be shown
  const showHeaderNameField = useMemo(() => formData.field === 'header', [formData.field]);

  return (
    <>
      {/* Drawer Overlay */}
      <div
        className={`fixed inset-0 z-40 transition-all duration-300 ${
          isOpened ? "bg-black/40 visible" : "invisible"
        }`}
        onClick={onClose}
      />
      
      {/* Drawer Panel */}
      <div
        className={`fixed top-0 right-0 h-full w-96 bg-white dark:bg-gray-900 shadow-lg z-50 transform transition-transform duration-300 ${
          isOpened ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="p-4 flex justify-between items-center border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <FilterIcon />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Filters</h2>
          </div>
          <button 
            onClick={onClose} 
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="flex flex-col h-full">
          {/* Search and Add Section */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search filters..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <button
                onClick={handleOpenCreateModal}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors whitespace-nowrap"
              >
                <PlusIcon />
                Add Filter
              </button>
            </div>
          </div>

          {/* Filters List */}
          <div className="flex-1 overflow-y-auto p-4">
            {filteredFilters.length === 0 ? (
              <div className="text-center py-12">
                {searchQuery ? (
                  <>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      No filters found
                    </p>
                    <p className="text-gray-500 dark:text-gray-400 mt-2">
                      Try adjusting your search query
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      No filters created yet
                    </p>
                    <p className="text-gray-500 dark:text-gray-400 mt-2">
                      Click "Add Filter" to get started
                    </p>
                  </>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {filteredFilters.map((filter) => (
                  <FilterItem
                    key={filter.id}
                    filter={filter}
                    onEdit={handleOpenEditModal}
                    onDelete={openDeleteConfirmation}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Create/Edit Modal */}
      {createModalOpened && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg w-96 max-w-full">
            <h3 className="text-lg font-bold mb-4 text-gray-900 dark:text-white">
              {editingFilter ? 'Edit Filter' : 'Create Filter'}
            </h3>
            <form onSubmit={handleSaveFilter} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Filter Name *
                </label>
                <input
                  type="text"
                  value={formData.filter_name}
                  onChange={(e) => setFormData({...formData, filter_name: e.target.value})}
                  placeholder="Enter filter name"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Field *
                </label>
                <div className="flex gap-2">
                  <select
                    value={formData.field}
                    onChange={(e) => handleFieldChange(e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  >
                    <option value="">Select field</option>
                    {fieldOptions.map(option => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                  {showHeaderNameField && (
                    <input
                      type="text"
                      value={formData.headerName}
                      onChange={(e) => handleFormChange('headerName', e.target.value)}
                      placeholder="Header name (e.g., Content-Type)"
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      required
                    />
                  )}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Operator *
                </label>
                <select
                  value={formData.operator}
                  onChange={(e) => handleFormChange('operator', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  {operatorOptions.map(option => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Value *
                </label>
                <input
                  type="text"
                  value={formData.value}
                  onChange={(e) => handleFormChange('value', e.target.value)}
                  placeholder="Enter value"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Saving...' : (editingFilter ? 'Save Changes' : 'Create Filter')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteModalOpened && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg w-96 max-w-full">
            <h3 className="text-lg font-bold mb-4 text-gray-900 dark:text-white">Delete Filter</h3>
            <p className="text-gray-700 dark:text-gray-300 mb-4">
              Are you sure you want to delete the filter "{filterToDelete?.filter_name}"?
            </p>
            <div className="flex items-start gap-2 p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-md mb-4">
              <AlertIcon />
              <div>
                <p className="font-medium text-orange-800 dark:text-orange-200">Warning</p>
                <p className="text-sm text-orange-700 dark:text-orange-300">
                  If this filter is deleted, all related rules will also be deleted.
                </p>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={handleCloseDeleteModal}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteFilter}
                disabled={loading}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                {loading ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Toast Notification */}
      {toast && (
        <Toast 
          message={toast.message} 
          type={toast.type} 
          onClose={() => setToast(null)} 
        />
      )}
    </>
  );
});

FiltersDrawer.displayName = 'FiltersDrawer';

export default FiltersDrawer;
