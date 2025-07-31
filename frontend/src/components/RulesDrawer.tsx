import React, { memo, useState, useCallback, useMemo } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Rule, Filter } from '../store/types';

// Simple SVG icons
const SettingsIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
    <path d="M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.07-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.74,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.36,4.82,11.69,4.82,12s0.02,0.64,0.07,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.44-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.47-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z"/>
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

export interface RulesDrawerProps {
  isOpened: boolean;
  onClose: () => void;
}

interface FormData {
  rule_name: string;
  filter_id: number;
  action: number;
  target_key: string;
  target_value: string;
  enabled: boolean;
}

// RuleAction enum mapping (matches backend RuleAction enum)
const RULE_ACTIONS = {
  ADD_HEADER: 0,
  MODIFY_HEADER: 1,
  DELETE_HEADER: 2,
  MODIFY_BODY: 3,
  BLOCK_REQUEST: 4,
  AUTO_RESPOND: 5
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

// Memoized rule item component for better performance
const RuleItem = memo(({ 
  rule, 
  onEdit, 
  onDelete,
  onToggle,
  filters
}: { 
  rule: Rule; 
  onEdit: (rule: Rule) => void; 
  onDelete: (rule: Rule) => void; 
  onToggle: (rule: Rule) => void;
  filters: Filter[];
}) => {
  const getFilterName = useCallback((filterId: number) => {
    const filter = filters.find(f => Number(f.id) === filterId);
    return filter?.filter_name|| `Filter ${filterId}`;
  }, [filters]);

  const getActionName = useCallback((action: number) => {
    const actionMap = {
      [RULE_ACTIONS.ADD_HEADER]: 'Add Header',
      [RULE_ACTIONS.MODIFY_HEADER]: 'Modify Header', 
      [RULE_ACTIONS.DELETE_HEADER]: 'Delete Header',
      [RULE_ACTIONS.MODIFY_BODY]: 'Modify Body',
      [RULE_ACTIONS.BLOCK_REQUEST]: 'Block Request',
      [RULE_ACTIONS.AUTO_RESPOND]: 'Auto Respond'
    };
    return actionMap[action] || `Action ${action}`;
  }, []);

  return (
    <div className="p-3 border border-gray-200 dark:border-gray-700 rounded-md bg-gray-50 dark:bg-gray-800">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-gray-900 dark:text-white">
              {rule.rule_name}
            </span>
            <button
              onClick={() => onToggle(rule)}
              className={`px-2 py-1 text-xs rounded-full transition-colors ${
                rule.enabled 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300'
                  : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
              }`}
            >
              {rule.enabled ? 'Enabled' : 'Disabled'}
            </button>
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">
            <div>Filter: {getFilterName(rule.filter_id)}</div>
            <div>Action: {getActionName(rule.action)}</div>
            {rule.target_key && <div>Target: {rule.target_key}</div>}
          </div>
        </div>
        <div className="flex gap-1">
          <button
            onClick={() => onEdit(rule)}
            className="p-1 text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
            title="Edit rule"
          >
            <EditIcon />
          </button>
          <button
            onClick={() => onDelete(rule)}
            className="p-1 text-gray-600 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400"
            title="Delete rule"
          >
            <TrashIcon />
          </button>
        </div>
      </div>
    </div>
  );
});

RuleItem.displayName = 'RuleItem';
RuleItem.displayName = 'RuleItem';

export const RulesDrawer: React.FC<RulesDrawerProps> = memo((props: RulesDrawerProps) => {
  const { isOpened, onClose } = props;
  const {
    rules,
    filters,
    addRule,
    updateRule,
    deleteRule,
    toggleRule,
  } = useAppStore();

  const [editingRule, setEditingRule] = useState<Rule | null>(null);
  const [loading, setLoading] = useState(false);
  const [createModalOpened, setCreateModalOpened] = useState(false);
  const [deleteModalOpened, setDeleteModalOpened] = useState(false);
  const [ruleToDelete, setRuleToDelete] = useState<Rule | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Form state with proper types
  const [formData, setFormData] = useState<FormData>({
    rule_name: '',
    filter_id: 0,
    action: RULE_ACTIONS.ADD_HEADER,
    target_key: '',
    target_value: '',
    enabled: true
  });

  // Filtered rules based on search query
  const filteredRules = useMemo(() => {
    if (!searchQuery.trim()) return rules;
    
    const query = searchQuery.toLowerCase();
    return rules.filter(rule => 
      rule.rule_name?.toLowerCase().includes(query) ||
      rule.target_key?.toLowerCase().includes(query) ||
      rule.target_value?.toLowerCase().includes(query)
    );
  }, [rules, searchQuery]);

  // Memoized action options
  const actionOptions = useMemo(() => [
    { value: RULE_ACTIONS.ADD_HEADER, label: 'Add Header' },
    { value: RULE_ACTIONS.MODIFY_HEADER, label: 'Modify Header' },
    { value: RULE_ACTIONS.DELETE_HEADER, label: 'Delete Header' },
    { value: RULE_ACTIONS.MODIFY_BODY, label: 'Modify Body' },
    { value: RULE_ACTIONS.BLOCK_REQUEST, label: 'Block Request' },
    { value: RULE_ACTIONS.AUTO_RESPOND, label: 'Auto Respond' },
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
      rule_name: '',
      filter_id: 0,
      action: RULE_ACTIONS.ADD_HEADER,
      target_key: '',
      target_value: '',
      enabled: true
    });
  }, []);

  const handleOpenCreateModal = useCallback(() => {
    setEditingRule(null);
    resetForm();
    setCreateModalOpened(true);
  }, [resetForm]);

  const handleOpenEditModal = useCallback((rule: Rule) => {
    setEditingRule(rule);
    setFormData({
      rule_name: rule.rule_name || '',
      filter_id: rule.filter_id || 0,
      action: typeof rule.action === 'number' ? rule.action : RULE_ACTIONS.ADD_HEADER,
      target_key: rule.target_key || '',
      target_value: rule.target_value || '',
      enabled: rule.enabled !== false
    });
    setCreateModalOpened(true);
  }, []);

  const openDeleteConfirmation = useCallback((rule: Rule) => {
    setRuleToDelete(rule);
    setDeleteModalOpened(true);
  }, []);

  const handleToggleRule = useCallback(async (rule: Rule) => {
    try {
      await toggleRule(rule.id!);
      showToast(`Rule ${rule.enabled ? 'disabled' : 'enabled'} successfully`, 'success');
    } catch (error) {
      console.error('Error toggling rule:', error);
      showToast('Failed to toggle rule', 'error');
    }
  }, [toggleRule, showToast]);

  const handleSaveRule = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!formData.rule_name.trim() || !formData.filter_id || !formData.target_key.trim() || !formData.target_value.trim()) {
      showToast('All fields are required', 'error');
      return;
    }

    // Prevent multiple submissions
    if (loading) return;
    
    setLoading(true);
    try {
      const rulePayload = {
        rule_name: formData.rule_name.trim(),
        filter_id: formData.filter_id,
        action: formData.action,
        target_key: formData.target_key.trim(),
        target_value: formData.target_value.trim(),
        enabled: formData.enabled
      };

      if (editingRule) {
        // Only use store method - it handles API call internally
        await updateRule(editingRule.id!, rulePayload);
        showToast('Rule updated successfully', 'success');
      } else {
        // Only use store method - it handles API call internally
        await addRule(rulePayload);
        showToast('Rule created successfully', 'success');
      }
      
      setCreateModalOpened(false);
      setEditingRule(null);
      resetForm();
    } catch (error) {
      console.error('Error saving rule:', error);
      showToast(
        editingRule ? 'Failed to update rule' : 'Failed to create rule',
        'error'
      );
    } finally {
      setLoading(false);
    }
  }, [formData, loading, editingRule, updateRule, addRule, showToast, resetForm]);

  const handleDeleteRule = useCallback(async () => {
    if (!ruleToDelete || loading) return;
    
    setLoading(true);
    try {
      // Only use store method - it handles API call internally
      await deleteRule(ruleToDelete.id!);
      setDeleteModalOpened(false);
      setRuleToDelete(null);
      showToast('Rule deleted successfully', 'success');
    } catch (error) {
      console.error('Error deleting rule:', error);
      showToast('Failed to delete rule', 'error');
    } finally {
      setLoading(false);
    }
  }, [ruleToDelete, loading, deleteRule, showToast]);

  // Optimized form field update handlers to prevent unnecessary re-renders
  const handleFormChange = useCallback((field: keyof FormData, value: string | number | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  // Close modal handler to prevent multiple event listeners
  const handleCloseModal = useCallback(() => {
    setEditingRule(null);
    setCreateModalOpened(false);
    resetForm();
  }, [resetForm]);

  const handleCloseDeleteModal = useCallback(() => {
    setDeleteModalOpened(false);
    setRuleToDelete(null);
  }, []);

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
            <SettingsIcon />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Rules</h2>
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
                  placeholder="Search rules..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <button
                onClick={handleOpenCreateModal}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors whitespace-nowrap"
              >
                <PlusIcon />
                Add Rule
              </button>
            </div>
          </div>

          {/* Rules List */}
          <div className="flex-1 overflow-y-auto p-4">
            {filteredRules.length === 0 ? (
              <div className="text-center py-12">
                {searchQuery ? (
                  <>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      No rules found
                    </p>
                    <p className="text-gray-500 dark:text-gray-400 mt-2">
                      Try adjusting your search query
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      No rules created yet
                    </p>
                    <p className="text-gray-500 dark:text-gray-400 mt-2">
                      Click "Add Rule" to get started
                    </p>
                  </>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {filteredRules.map((rule) => (
                  <RuleItem
                    key={rule.id}
                    rule={rule}
                    onEdit={handleOpenEditModal}
                    onDelete={openDeleteConfirmation}
                    onToggle={handleToggleRule}
                    filters={filters}
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
              {editingRule ? 'Edit Rule' : 'Create Rule'}
            </h3>
            <form onSubmit={handleSaveRule} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Rule Name *
                </label>
                <input
                  type="text"
                  value={formData.rule_name}
                  onChange={(e) => handleFormChange('rule_name', e.target.value)}
                  placeholder="Enter rule name"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Filter *
                </label>
                <select
                  value={formData.filter_id}
                  onChange={(e) => handleFormChange('filter_id', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value={0}>Select filter</option>
                  {filters.map(filter => (
                    <option key={filter.id} value={Number(filter.id)}>
                      {filter.filter_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Action *
                </label>
                <select
                  value={formData.action}
                  onChange={(e) => handleFormChange('action', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  {actionOptions.map(option => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Target Key *
                </label>
                <input
                  type="text"
                  value={formData.target_key}
                  onChange={(e) => handleFormChange('target_key', e.target.value)}
                  placeholder="e.g., Content-Type, body, etc."
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Target Value *
                </label>
                <input
                  type="text"
                  value={formData.target_value}
                  onChange={(e) => handleFormChange('target_value', e.target.value)}
                  placeholder="Enter target value"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>

              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.enabled}
                    onChange={(e) => handleFormChange('enabled', e.target.checked)}
                    className="mr-2 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Enabled</span>
                </label>
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
                  {loading ? 'Saving...' : (editingRule ? 'Save Changes' : 'Create Rule')}
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
            <h3 className="text-lg font-bold mb-4 text-gray-900 dark:text-white">Delete Rule</h3>
            <p className="text-gray-700 dark:text-gray-300 mb-4">
              Are you sure you want to delete the rule "{ruleToDelete?.rule_name}"?
            </p>
            <div className="flex items-start gap-2 p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-md mb-4">
              <AlertIcon />
              <div>
                <p className="font-medium text-orange-800 dark:text-orange-200">Warning</p>
                <p className="text-sm text-orange-700 dark:text-orange-300">
                  This action cannot be undone. The rule will be permanently deleted.
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
                onClick={handleDeleteRule}
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

RulesDrawer.displayName = 'RulesDrawer';

export default RulesDrawer;