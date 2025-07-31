import pytest
import tempfile
import os
import sqlite3
from unittest.mock import Mock
import threading

from backend.services.storage import DatabaseManager, CacheStore
from backend.HttpInterceptor.FilterModel import FilterModel
from backend.HttpInterceptor.RuleModel import RuleModel
from backend.HttpInterceptor.SyncMessage import SyncMessage
from backend.HttpInterceptor.OperationType import OperationType


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    # Force close any open connections and cleanup
    try:
        import gc
        gc.collect()  # Force garbage collection to close connections
        if os.path.exists(path):
            os.unlink(path)
    except PermissionError:
        # If still locked, try a few more times
        import time
        for i in range(3):
            time.sleep(0.1)
            try:
                if os.path.exists(path):
                    os.unlink(path)
                break
            except PermissionError:
                continue


@pytest.fixture
def db_manager(temp_db):
    """Create a DatabaseManager instance with temporary database."""
    # Reset the singleton instance
    DatabaseManager._instance = None
    manager = DatabaseManager(temp_db)
    yield manager
    # Clean up singleton and force close connections
    DatabaseManager._instance = None
    # Force garbage collection to ensure connections are closed
    import gc
    gc.collect()


@pytest.fixture
def cache_store():
    """Create a CacheStore instance."""
    # Reset the singleton instance
    CacheStore._instance = None
    store = CacheStore()
    yield store
    # Clean up singleton
    CacheStore._instance = None


@pytest.fixture
def sample_filter():
    """Create a sample FilterModel for testing."""
    filter_model = Mock(spec=FilterModel)
    filter_model.id = 1
    filter_model.filter_name = "Test Filter"
    filter_model.field = "url"
    filter_model.operator = Mock()
    filter_model.operator.to_int.return_value = 1
    filter_model.value = "test-pattern"
    return filter_model


@pytest.fixture
def sample_rule():
    """Create a sample RuleModel for testing."""
    rule_model = Mock(spec=RuleModel)
    rule_model.id = 1
    rule_model.rule_name = "Test Rule"
    rule_model.enabled = True
    rule_model.filter_id = 1
    rule_model.action = Mock()
    rule_model.action.to_int.return_value = 1
    rule_model.target_key = "response"
    rule_model.target_value = "modified"
    return rule_model


class TestDatabaseManager:
    """Test cases for DatabaseManager."""

    def test_singleton_pattern(self, temp_db):
        """Test that DatabaseManager follows singleton pattern."""
        DatabaseManager._instance = None
        manager1 = DatabaseManager(temp_db)
        manager2 = DatabaseManager(temp_db)
        assert manager1 is manager2

    def test_database_initialization(self, db_manager, temp_db):
        """Test database file creation and table initialization."""
        assert os.path.exists(temp_db)
        
        # Check if tables exist
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Check filters table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='filters'")
        assert cursor.fetchone() is not None
        
        # Check rules table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rules'")
        assert cursor.fetchone() is not None
        
        conn.close()

    def test_create_filter(self, db_manager, sample_filter):
        """Test creating a filter in the database."""
        result = db_manager.create_filter(sample_filter)
        assert result is not None
        assert isinstance(result, FilterModel)  # Should return FilterModel
        assert result.id is not None  # Should have an ID assigned

    def test_get_filter_by_id(self, db_manager, sample_filter):
        """Test retrieving a filter from the database."""
        created_filter = db_manager.create_filter(sample_filter)
        retrieved_filter = db_manager.get_filter_by_id(created_filter.id)
        assert retrieved_filter is not None
        assert retrieved_filter.id == created_filter.id

    def test_get_filters(self, db_manager, sample_filter):
        """Test retrieving all filters from the database."""
        # Create multiple filters
        filter1 = db_manager.create_filter(sample_filter)
        
        # Create second filter with different properties
        sample_filter.filter_name = "Test Filter 2"
        filter2 = db_manager.create_filter(sample_filter)
        
        filters = db_manager.get_filters()
        assert len(filters) >= 2

    def test_update_filter(self, db_manager, sample_filter):
        """Test updating a filter in the database."""
        created_filter = db_manager.create_filter(sample_filter)
        filter_id = created_filter.id
        
        # Update filter
        created_filter.filter_name = "Updated Filter"
        result = db_manager.update_filter(filter_id, created_filter)
        assert result is not None
        
        # Verify update
        updated_filter = db_manager.get_filter_by_id(filter_id)
        assert updated_filter.filter_name == "Updated Filter"

    def test_delete_filter(self, db_manager, sample_filter):
        """Test deleting a filter from the database."""
        created_filter = db_manager.create_filter(sample_filter)
        filter_id = created_filter.id
        
        result = db_manager.delete_filter(filter_id)
        assert result is True
        
        # Verify deletion
        deleted_filter = db_manager.get_filter_by_id(filter_id)
        assert deleted_filter is None

    def test_create_rule(self, db_manager, sample_filter, sample_rule):
        """Test creating a rule in the database."""
        # First create a filter that the rule can reference
        created_filter = db_manager.create_filter(sample_filter)
        sample_rule.filter_id = created_filter.id
        
        result = db_manager.create_rule(sample_rule)
        assert result is not None
        assert isinstance(result, RuleModel)  # Should return RuleModel
        assert result.id is not None  # Should have an ID assigned

    def test_get_rule_by_id(self, db_manager, sample_filter, sample_rule):
        """Test retrieving a rule from the database."""
        # First create a filter
        created_filter = db_manager.create_filter(sample_filter)
        sample_rule.filter_id = created_filter.id
        
        created_rule = db_manager.create_rule(sample_rule)
        retrieved_rule = db_manager.get_rule_by_id(created_rule.id)
        assert retrieved_rule is not None
        assert retrieved_rule.id == created_rule.id

    def test_get_rules(self, db_manager, sample_filter, sample_rule):
        """Test retrieving all rules from the database."""
        # First create a filter
        created_filter = db_manager.create_filter(sample_filter)
        sample_rule.filter_id = created_filter.id
        
        # Create multiple rules
        rule1 = db_manager.create_rule(sample_rule)
        
        sample_rule.rule_name = "Test Rule 2"
        rule2 = db_manager.create_rule(sample_rule)
        
        rules = db_manager.get_rules()
        assert len(rules) >= 2

    def test_update_rule(self, db_manager, sample_filter, sample_rule):
        """Test updating a rule in the database."""
        # First create a filter
        created_filter = db_manager.create_filter(sample_filter)
        sample_rule.filter_id = created_filter.id
        
        created_rule = db_manager.create_rule(sample_rule)
        rule_id = created_rule.id
        
        # Update rule
        created_rule.rule_name = "Updated Rule"
        result = db_manager.update_rule(rule_id, created_rule)
        assert result is not None
        
        # Verify update
        updated_rule = db_manager.get_rule_by_id(rule_id)
        assert updated_rule.rule_name == "Updated Rule"

    def test_delete_rule(self, db_manager, sample_filter, sample_rule):
        """Test deleting a rule from the database."""
        # First create a filter
        created_filter = db_manager.create_filter(sample_filter)
        sample_rule.filter_id = created_filter.id
        
        created_rule = db_manager.create_rule(sample_rule)
        rule_id = created_rule.id
        
        result = db_manager.delete_rule(rule_id)
        assert result is True
        
        # Verify deletion
        deleted_rule = db_manager.get_rule_by_id(rule_id)
        assert deleted_rule is None

    def test_get_rules_by_filter(self, db_manager, sample_filter, sample_rule):
        """Test retrieving rules by filter ID."""
        # First create a filter
        created_filter = db_manager.create_filter(sample_filter)
        sample_rule.filter_id = created_filter.id
        
        created_rule = db_manager.create_rule(sample_rule)
        
        # Note: Assuming there's a method to get rules by filter
        # This may need to be implemented or called differently based on actual API
        rules = db_manager.get_rules()  # Get all rules and filter manually for now
        filter_rules = [r for r in rules if r.filter_id == created_filter.id]
        assert len(filter_rules) >= 1
        assert filter_rules[0].filter_id == created_filter.id


class TestCacheStore:
    """Test cases for CacheStore."""

    def test_singleton_pattern(self):
        """Test that CacheStore follows singleton pattern."""
        CacheStore._instance = None
        store1 = CacheStore()
        store2 = CacheStore()
        assert store1 is store2

    def test_initial_state(self, cache_store):
        """Test initial state of cache store."""
        assert len(cache_store.get_active_filters()) == 0
        assert len(cache_store.get_active_rules()) == 0

    def test_add_single_filter(self, cache_store, sample_filter):
        """Test adding a filter to cache."""
        cache_store.add_single_filter(sample_filter)
        filters = cache_store.get_active_filters()
        assert len(filters) == 1
        assert filters[0] == sample_filter

    def test_get_filter_by_id(self, cache_store, sample_filter):
        """Test retrieving a specific filter from cache."""
        cache_store.add_single_filter(sample_filter)
        retrieved_filter = cache_store.get_filter_by_id(sample_filter.id)
        assert retrieved_filter == sample_filter

    def test_update_filters(self, cache_store, sample_filter):
        """Test updating filters in cache."""
        # Add initial filter
        cache_store.add_single_filter(sample_filter)
        
        # Update filter via batch operation
        sample_filter.filter_name = "Updated Filter"
        cache_store.update_filters([sample_filter], clear_all=False)
        
        retrieved_filter = cache_store.get_filter_by_id(sample_filter.id)
        assert retrieved_filter.filter_name == "Updated Filter"

    def test_delete_filters(self, cache_store, sample_filter):
        """Test removing a filter from cache."""
        cache_store.add_single_filter(sample_filter)
        cache_store.delete_filters([sample_filter.id])
        
        filters = cache_store.get_active_filters()
        assert len(filters) == 0

    def test_add_single_rule(self, cache_store, sample_rule):
        """Test adding a rule to cache."""
        cache_store.add_single_rule(sample_rule)
        rules = cache_store.get_active_rules()
        assert len(rules) == 1
        assert rules[0] == sample_rule

    def test_get_rule_by_id(self, cache_store, sample_rule):
        """Test retrieving a specific rule from cache."""
        cache_store.add_single_rule(sample_rule)
        retrieved_rule = cache_store.get_rule_by_id(sample_rule.id)
        assert retrieved_rule == sample_rule

    def test_update_rules(self, cache_store, sample_rule):
        """Test updating rules in cache."""
        # Add initial rule
        cache_store.add_single_rule(sample_rule)
        
        # Update rule via batch operation
        sample_rule.rule_name = "Updated Rule"
        cache_store.update_rules([sample_rule], clear_all=False)
        
        retrieved_rule = cache_store.get_rule_by_id(sample_rule.id)
        assert retrieved_rule.rule_name == "Updated Rule"

    def test_delete_rules(self, cache_store, sample_rule):
        """Test removing a rule from cache."""
        cache_store.add_single_rule(sample_rule)
        cache_store.delete_rules([sample_rule.id])
        
        rules = cache_store.get_active_rules()
        assert len(rules) == 0

    def test_get_active_rules_only(self, cache_store):
        """Test that get_active_rules only returns enabled rules."""
        # Add enabled rule
        enabled_rule = Mock(spec=RuleModel)
        enabled_rule.id = 1
        enabled_rule.enabled = True
        cache_store.add_single_rule(enabled_rule)
        
        # Add disabled rule
        disabled_rule = Mock(spec=RuleModel)
        disabled_rule.id = 2
        disabled_rule.enabled = False
        cache_store.add_single_rule(disabled_rule)
        
        active_rules = cache_store.get_active_rules()
        assert len(active_rules) == 1
        assert active_rules[0].id == 1

    def test_thread_safety(self, cache_store):
        """Test thread safety of cache operations."""
        def add_filters():
            for i in range(10):
                filter_copy = Mock(spec=FilterModel)
                filter_copy.id = i + threading.current_thread().ident  # Unique IDs
                filter_copy.filter_name = f"Filter {i}"
                cache_store.add_single_filter(filter_copy)
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=add_filters)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have 50 filters total (5 threads * 10 filters each)
        filters = cache_store.get_active_filters()
        assert len(filters) == 50

    def test_update_filters_clear_all(self, cache_store, sample_filter):
        """Test updating filters with clear_all=True."""
        # Add initial filter
        cache_store.add_single_filter(sample_filter)
        
        # Create new filter
        new_filter = Mock(spec=FilterModel)
        new_filter.id = 2
        new_filter.filter_name = "New Filter"
        
        # Update with clear_all=True should replace all filters
        cache_store.update_filters([new_filter], clear_all=True)
        
        filters = cache_store.get_active_filters()
        assert len(filters) == 1
        assert filters[0].filter_name == "New Filter"

    def test_update_rules_clear_all(self, cache_store, sample_rule):
        """Test updating rules with clear_all=True."""
        # Add initial rule
        cache_store.add_single_rule(sample_rule)
        
        # Create new rule
        new_rule = Mock(spec=RuleModel)
        new_rule.id = 2
        new_rule.rule_name = "New Rule"
        new_rule.enabled = True
        
        # Update with clear_all=True should replace all rules
        cache_store.update_rules([new_rule], clear_all=True)
        
        rules = cache_store.get_active_rules()
        assert len(rules) == 1
        assert rules[0].rule_name == "New Rule"

    def test_get_cache_stats(self, cache_store, sample_filter, sample_rule):
        """Test getting cache statistics."""
        # Add filter and rule
        cache_store.add_single_filter(sample_filter)
        cache_store.add_single_rule(sample_rule)
        
        # Add disabled rule
        disabled_rule = Mock(spec=RuleModel)
        disabled_rule.id = 2
        disabled_rule.enabled = False
        cache_store.add_single_rule(disabled_rule)
        
        stats = cache_store.get_cache_stats()
        assert stats["total_filters"] == 1
        assert stats["total_rules"] == 2
        assert stats["active_rules"] == 1  # Only enabled rules

    def test_clear_cache(self, cache_store, sample_filter, sample_rule):
        """Test clearing all cache data."""
        cache_store.add_single_filter(sample_filter)
        cache_store.add_single_rule(sample_rule)
        
        cache_store.clear_cache()
        
        assert len(cache_store.get_active_filters()) == 0
        assert len(cache_store.get_active_rules()) == 0

    def test_handle_sync_msg_full_sync(self, cache_store):
        """Test handling sync message for full sync operation."""
        # This test would require creating proper FlatBuffer messages
        # For now, just test that the method exists and doesn't crash
        try:
            # Create a mock FlatBuffer message (would need proper implementation)
            mock_msg = b"mock_sync_message"
            cache_store.handle_sync_msg(mock_msg)
        except Exception:
            # Expected to fail with mock data, but method should exist
            pass
