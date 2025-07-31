# Database manager
import sqlite3
from typing import List, Dict, Optional
import threading

from backend.utils.base_models import FilterModel, RuleModel, Operator, RuleAction, OperationType
from backend.HttpInterceptor.SyncMessage import SyncMessage
from backend.HttpInterceptor.CoreMessage import CoreMessage


class DatabaseManager:
    _instance = None

    def __new__(cls, db_path: str = "interceptor.db"):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "interceptor.db"):
        if self._initialized:
            return
        self.db_path = db_path
        self.init_database()
        self._initialized = True

    def init_database(self):
        """Initialize SQLite database with tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")

        # Filters table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS filters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filter_name TEXT NOT NULL UNIQUE,
                field TEXT NOT NULL,
                operator INTEGER NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Rules table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL UNIQUE,
                filter_id INTEGER NOT NULL,
                action INTEGER NOT NULL,
                target_key TEXT NOT NULL,
                target_value TEXT NOT NULL,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (filter_id) REFERENCES filters (id) ON DELETE CASCADE
            )
        """
        )

        conn.commit()
        conn.close()

    def get_filters(self) -> List[FilterModel]:
        """Get all filters from database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM filters ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        filters = []
        for row in rows:
            row_dict = dict(row)
            # Convert operator integer back to enum
            row_dict['operator'] = Operator.from_int(row_dict['operator'])
            filters.append(FilterModel(**row_dict))
        
        return filters

    def create_filter(self, filter_data: FilterModel) -> FilterModel:
        """Create a new filter"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO filters (filter_name, field, operator, value)
                VALUES (?, ?, ?, ?)
            """,
                (
                    filter_data.filter_name,
                    filter_data.field,
                    filter_data.operator.to_int(),  # Convert enum to integer
                    filter_data.value,
                ),
            )

            filter_id = cursor.lastrowid
            conn.commit()
            filter_data.id = filter_id
            return filter_data
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "UNIQUE constraint failed: filters.filter_name" in str(e):
                raise ValueError(f"Filter with name '{filter_data.filter_name}' already exists")
            raise e
        finally:
            conn.close()

    def update_filter(self, filter_id: int, filter_data: FilterModel) -> FilterModel:
        """Update an existing filter"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE filters 
                SET filter_name=?, field=?, operator=?, value=?
                WHERE id=?
            """,
                (
                    filter_data.filter_name,
                    filter_data.field,
                    filter_data.operator.to_int(),  # Convert enum to integer
                    filter_data.value,
                    filter_id,
                ),
            )

            # Check if any row was actually updated
            if cursor.rowcount == 0:
                raise ValueError(f"Filter with ID {filter_id} not found")

            conn.commit()
            filter_data.id = filter_id
            return filter_data
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "UNIQUE constraint failed: filters.filter_name" in str(e):
                raise ValueError(f"Filter with name '{filter_data.filter_name}' already exists")
            raise e
        finally:
            conn.close()

    def delete_filter(self, filter_id: int) -> bool:
        """Delete a filter and its associated rules"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # Delete the filter (CASCADE will handle associated rules)
        cursor.execute("DELETE FROM filters WHERE id=?", (filter_id,))

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return deleted

    def filter_name_exists(self, filter_name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if a filter name already exists (optionally excluding a specific ID)"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        if exclude_id:
            cursor.execute("SELECT 1 FROM filters WHERE filter_name = ? AND id != ?", (filter_name, exclude_id))
        else:
            cursor.execute("SELECT 1 FROM filters WHERE filter_name = ?", (filter_name,))
        
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def get_rules(self) -> List[RuleModel]:
        """Get all rules from database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM rules ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        rules = []
        for row in rows:
            row_dict = dict(row)
            # Convert action integer back to enum
            row_dict['action'] = RuleAction.from_int(row_dict['action'])
            rules.append(RuleModel(**row_dict))
        
        return rules

    def create_rule(self, rule_data: RuleModel) -> RuleModel:
        """Create a new rule"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO rules (rule_name, filter_id, action, target_key, target_value, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    rule_data.rule_name,
                    rule_data.filter_id,
                    rule_data.action.to_int(),  # Convert enum to integer
                    rule_data.target_key,
                    rule_data.target_value,
                    rule_data.enabled,
                ),
            )

            rule_id = cursor.lastrowid
            conn.commit()
            rule_data.id = rule_id
            return rule_data
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "UNIQUE constraint failed: rules.rule_name" in str(e):
                raise ValueError(f"Rule with name '{rule_data.rule_name}' already exists")
            elif "FOREIGN KEY constraint failed" in str(e):
                raise ValueError(f"Filter with ID {rule_data.filter_id} does not exist")
            raise e
        finally:
            conn.close()

    def update_rule(self, rule_id: int, rule_data: RuleModel) -> RuleModel:
        """Update an existing rule"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE rules 
                SET rule_name=?, filter_id=?, action=?, target_key=?, target_value=?, enabled=?
                WHERE id=?
            """,
                (
                    rule_data.rule_name,
                    rule_data.filter_id,
                    rule_data.action.to_int(),  # Convert enum to integer
                    rule_data.target_key,
                    rule_data.target_value,
                    rule_data.enabled,
                    rule_id,
                ),
            )

            # Check if any row was actually updated
            if cursor.rowcount == 0:
                raise ValueError(f"Rule with ID {rule_id} not found")

            conn.commit()
            rule_data.id = rule_id
            return rule_data
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "UNIQUE constraint failed: rules.rule_name" in str(e):
                raise ValueError(f"Rule with name '{rule_data.rule_name}' already exists")
            elif "FOREIGN KEY constraint failed" in str(e):
                raise ValueError(f"Filter with ID {rule_data.filter_id} does not exist")
            raise e
        finally:
            conn.close()

    def delete_rule(self, rule_id: int) -> bool:
        """Delete a rule"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        cursor.execute("DELETE FROM rules WHERE id=?", (rule_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return deleted

    def rule_name_exists(self, rule_name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if a rule name already exists (optionally excluding a specific ID)"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        if exclude_id:
            cursor.execute("SELECT 1 FROM rules WHERE rule_name = ? AND id != ?", (rule_name, exclude_id))
        else:
            cursor.execute("SELECT 1 FROM rules WHERE rule_name = ?", (rule_name,))
        
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def get_rule_by_id(self, rule_id: int) -> Optional[RuleModel]:
        """Get a rule by its ID"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM rules WHERE id = ?", (rule_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            row_dict = dict(row)
            # Convert action integer back to enum
            row_dict['action'] = RuleAction.from_int(row_dict['action'])
            return RuleModel(**row_dict)
        
        return None

    def get_filter_by_id(self, filter_id: int) -> Optional[FilterModel]:
        """Get a filter by its ID"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM filters WHERE id = ?", (filter_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            row_dict = dict(row)
            # Convert operator integer back to enum
            row_dict['operator'] = Operator.from_int(row_dict['operator'])
            return FilterModel(**row_dict)
        
        return None


class CacheStore:
    """
    Ultra-fast singleton cache store for rules and filters
    Thread-safe, optimized for high-frequency access
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CacheStore, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        self._rules_lock = threading.RLock()
        self._filters_lock = threading.RLock()

        # High-performance in-memory storage
        self._rules: Dict[int, RuleModel] = {}
        self._filters: Dict[int, FilterModel] = {}

        self._initialized = True
        print("CacheStore initialized - waiting for sync messages from queue")

    def update_rules(self, rules: List[RuleModel], clear_all: bool = False) -> None:
        """Update rules cache - optimized O(n) operation"""
        with self._rules_lock:
            if clear_all:
                self._rules.clear()

            for rule in rules:
                if rule.id is not None:
                    self._rules[rule.id] = rule

    def update_filters(self, filters: List[FilterModel], clear_all: bool = False) -> None:
        """Update filters cache - optimized O(n) operation"""
        with self._filters_lock:
            if clear_all:
                self._filters.clear()

            for filter_obj in filters:
                if filter_obj.id is not None:
                    self._filters[filter_obj.id] = filter_obj

    def get_active_rules(self) -> List[RuleModel]:
        """Get all enabled rules - returns proper List[RuleModel]"""
        with self._rules_lock:
            return [rule for rule in self._rules.values() if rule.enabled]

    def get_active_filters(self) -> List[FilterModel]:
        """Get all filters - returns proper List[FilterModel]"""
        with self._filters_lock:
            return list(self._filters.values())

    def get_filter_by_id(self, filter_id: int) -> Optional[FilterModel]:
        """Get filter by ID - O(1) hash lookup"""
        with self._filters_lock:
            return self._filters.get(filter_id)

    def get_rule_by_id(self, rule_id: int) -> Optional[RuleModel]:
        """Get rule by ID - O(1) hash lookup"""
        with self._rules_lock:
            return self._rules.get(rule_id)

    def delete_rules(self, rule_ids: List[int]) -> None:
        """Delete rules by ID list - O(n) operation"""
        with self._rules_lock:
            for rule_id in rule_ids:
                if rule_id in self._rules:
                    del self._rules[rule_id]
                    print(f"Deleted rule {rule_id} from cache")

    def delete_filters(self, filter_ids: List[int]) -> None:
        """Delete filters by ID list - O(n) operation"""
        with self._filters_lock:
            for filter_id in filter_ids:
                if filter_id in self._filters:
                    del self._filters[filter_id]
                    print(f"Deleted filter {filter_id} from cache")

    def add_single_rule(self, rule: RuleModel) -> None:
        """Add a single rule to cache"""
        if rule.id is not None:
            with self._rules_lock:
                self._rules[rule.id] = rule
                print(f"Added rule {rule.id} to cache")

    def add_single_filter(self, filter_obj: FilterModel) -> None:
        """Add a single filter to cache"""
        if filter_obj.id is not None:
            with self._filters_lock:
                self._filters[filter_obj.id] = filter_obj
                print(f"Added filter {filter_obj.id} to cache")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        with self._rules_lock:
            active_rules = len([r for r in self._rules.values() if r.enabled])
            total_rules = len(self._rules)
        
        with self._filters_lock:
            total_filters = len(self._filters)
        
        return {
            "total_rules": total_rules,
            "active_rules": active_rules,
            "total_filters": total_filters
        }

    def clear_cache(self) -> None:
        """Clear all cached data"""
        with self._rules_lock:
            self._rules.clear()
        with self._filters_lock:
            self._filters.clear()
        print("Cache cleared")

    def handle_sync_msg(self, raw_msg: bytes) -> None:
        """Handle sync message and update cache"""
        try:
            print(f"Received raw message of size: {len(raw_msg)} bytes")
            print(f"First 50 bytes: {raw_msg[:50]}")
            print(f"Last 50 bytes: {raw_msg[-50:]}")
            
            # First parse as CoreMessage, then extract the SyncMessage
            core_msg = CoreMessage.GetRootAsCoreMessage(raw_msg, 0)
            sync_msg_table = core_msg.Message()
            if sync_msg_table is None:
                print("Error: No sync message found in core message")
                return
                
            # Now we have the SyncMessage table
            sync_msg = SyncMessage()
            sync_msg.Init(sync_msg_table.Bytes, sync_msg_table.Pos)
            
            operation = sync_msg.Operation()
            rules_size = sync_msg.RulesListLength()
            filters_size = sync_msg.FiltersDataLength()

            print(f"Processing sync message: operation={operation}, rules={rules_size}, filters={filters_size}")

            # Parse rules from sync message
            rules_list: List[RuleModel] = []
            for i in range(rules_size):
                try:
                    rule = sync_msg.RulesList(i)
                    if rule is None:
                        continue
                        
                    rule_model = RuleModel(
                        id=rule.Id(),
                        rule_name=rule.RuleName().decode('utf-8') if rule.RuleName() else "",
                        filter_id=rule.FilterId(),
                        action=RuleAction.from_int(rule.Action()),
                        target_key=rule.TargetKey().decode('utf-8') if rule.TargetKey() else "",
                        target_value=rule.TargetValue().decode('utf-8') if rule.TargetValue() else "",
                        enabled=rule.Enabled()
                    )
                    rules_list.append(rule_model)
                except Exception as e:
                    print(f"Error parsing rule {i}: {e}")
                    continue

            # Parse filters from sync message
            filters_list: List[FilterModel] = []
            for i in range(filters_size):
                try:
                    filter_data = sync_msg.FiltersData(i)
                    if filter_data is None:
                        continue
                        
                    filter_model = FilterModel(
                        id=filter_data.Id(),
                        filter_name=filter_data.FilterName().decode('utf-8') if filter_data.FilterName() else "",
                        field=filter_data.Field().decode('utf-8') if filter_data.Field() else "",
                        operator=Operator.from_int(filter_data.Operator()),
                        value=filter_data.Value().decode('utf-8') if filter_data.Value() else ""
                    )
                    filters_list.append(filter_model)
                except Exception as e:
                    print(f"Error parsing filter {i}: {e}")
                    continue

            # Handle different operations
            if operation == OperationType.FULL_SYNC:
                print("Performing FULL_SYNC")
                self.update_filters(filters_list, clear_all=True)
                self.update_rules(rules_list, clear_all=True)
                
            elif operation == OperationType.ADD:
                print("Performing ADD operation")
                if filters_list:
                    self.update_filters(filters_list, clear_all=False)
                if rules_list:
                    self.update_rules(rules_list, clear_all=False)
                    
            elif operation == OperationType.UPDATE:
                print("Performing UPDATE operation")
                if filters_list:
                    self.update_filters(filters_list, clear_all=False)
                if rules_list:
                    self.update_rules(rules_list, clear_all=False)
                    
            elif operation == OperationType.DELETE:
                print("Performing DELETE operation")
                if filters_list:
                    filter_ids = [f.id for f in filters_list if f.id is not None]
                    self.delete_filters(filter_ids)
                if rules_list:
                    rule_ids = [r.id for r in rules_list if r.id is not None]
                    self.delete_rules(rule_ids)

            # Print final cache state
            stats = self.get_cache_stats()
            print(f"Cache updated: {stats['total_rules']} total rules ({stats['active_rules']} active), {stats['total_filters']} filters")
            
        except Exception as e:
            print(f"Error handling sync message: {e}")
            import traceback
            traceback.print_exc()
