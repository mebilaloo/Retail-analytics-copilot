"""
SQLite Tool for schema introspection and query execution.
Provides safe database operations for the retail analytics agent.
"""

import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class TableInfo:
    """Information about a database table."""
    name: str
    columns: List[Dict[str, Any]]
    row_count: int
    sample_data: List[Dict[str, Any]]


@dataclass
class ColumnInfo:
    """Information about a database column."""
    name: str
    type: str
    nullable: bool
    default_value: Any
    primary_key: bool
    foreign_key: Optional[str] = None


class SQLiteTool:
    """Tool for interacting with SQLite databases."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Establish connection to the database."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
        except Exception as e:
            raise RuntimeError(f"Failed to connect to database {self.db_path}: {e}")
    
    def __del__(self):
        """Close connection when object is destroyed."""
        if self.connection:
            self.connection.close()
    
    def get_schema(self) -> str:
        """Get schema description optimized for DSPy SQL generation."""
        if not self.connection:
            return "Database connection not available"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
            tables = [row[0] for row in cursor.fetchall()]
            
            schema_lines = [
                "=== NORTHWIND DATABASE SCHEMA ===",
                "This is a retail/e-commerce database with the following tables:\n"
            ]
            
            # Key tables with their relationships
            key_tables = {
                'Categories': 'Product categories (Beverages, Condiments, etc.)',
                'Products': 'Individual products with prices and stock',
                'Customers': 'Customer information and locations', 
                'Orders': 'Order headers with dates and customer info',
                'Order Details': 'Order line items with quantities and prices',
                'Suppliers': 'Product suppliers and vendors',
                'Employees': 'Company employees',
                'Shippers': 'Shipping companies'
            }
            
            for table in tables:
                if table in key_tables:
                    cursor.execute(f"PRAGMA table_info([{table}]);")
                    columns = cursor.fetchall()
                    
                    # Format key columns
                    key_cols = []
                    for col in columns:
                        col_name = col[1]
                        col_type = col[2]
                        is_pk = bool(col[5])
                        
                        if is_pk:
                            key_cols.append(f"{col_name} ({col_type}, PK)")
                        elif any(fk in col_name.lower() for fk in ['id', 'key']):
                            key_cols.append(f"{col_name} ({col_type}, FK)")
                        else:
                            key_cols.append(f"{col_name} ({col_type})")
                    
                    schema_lines.append(f"• {table}: {key_tables[table]}")
                    schema_lines.append(f"  Columns: {', '.join(key_cols)}")
                    schema_lines.append("")
            
            # Add important relationships and SQL patterns
            schema_lines.extend([
                "=== KEY RELATIONSHIPS ===",
                "• Products.CategoryID → Categories.CategoryID",
                "• Orders.CustomerID → Customers.CustomerID",
                "• [Order Details].OrderID → Orders.OrderID",
                "• [Order Details].ProductID → Products.ProductID",
                "",
                "=== COMMON SQL PATTERNS ===",
                "• Product revenue: JOIN Products p, [Order Details] od ON p.ProductID = od.ProductID",
                "• Customer orders: JOIN Customers c, Orders o ON c.CustomerID = o.CustomerID", 
                "• Category analysis: JOIN Categories c, Products p ON c.CategoryID = p.CategoryID",
                "• Revenue calculation: SUM(od.UnitPrice * od.Quantity * (1 - od.Discount))",
                "",
                "=== IMPORTANT NOTES ===",
                "• Use [Order Details] with brackets for table name (contains space)",
                "• Revenue = UnitPrice * Quantity * (1 - Discount)",
                "• CategoryName for 'Beverages', 'Condiments', 'Dairy Products', etc.",
                "• Country field in Customers for geographic analysis"
            ])
            
            return "\n".join(schema_lines)
            
        except Exception as e:
            return f"Error retrieving schema: {e}"
    
    def get_table_info(self, table_name: str) -> TableInfo:
        """Get detailed information about a specific table."""
        cursor = self.connection.cursor()
        
        # Get column information
        cursor.execute(f"PRAGMA table_info({table_name});")
        pragma_info = cursor.fetchall()
        
        columns = []
        for row in pragma_info:
            column_info = {
                'name': row[1],
                'type': row[2],
                'nullable': not bool(row[3]),
                'default_value': row[4],
                'primary_key': bool(row[5])
            }
            columns.append(column_info)
        
        # Get foreign key information
        cursor.execute(f"PRAGMA foreign_key_list({table_name});")
        fk_info = cursor.fetchall()
        
        fk_map = {}
        for fk_row in fk_info:
            column_name = fk_row[3]
            referenced_table = fk_row[2]
            referenced_column = fk_row[4]
            fk_map[column_name] = f"{referenced_table}.{referenced_column}"
        
        # Add foreign key info to columns
        for column in columns:
            if column['name'] in fk_map:
                column['foreign_key'] = fk_map[column['name']]
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        row_count = cursor.fetchone()[0]
        
        # Get sample data (first 3 rows)
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
        sample_rows = cursor.fetchall()
        sample_data = [dict(row) for row in sample_rows]
        
        return TableInfo(
            name=table_name,
            columns=columns,
            row_count=row_count,
            sample_data=sample_data
        )
    
    def _format_table_schema(self, table_info: TableInfo) -> str:
        """Format table information into a readable schema description."""
        lines = [f"Table: {table_info.name} ({table_info.row_count} rows)"]
        lines.append("Columns:")
        
        for col in table_info.columns:
            col_desc = f"  - {col['name']}: {col['type']}"
            
            details = []
            if col['primary_key']:
                details.append("PRIMARY KEY")
            if col.get('foreign_key'):
                details.append(f"REFERENCES {col['foreign_key']}")
            if not col['nullable']:
                details.append("NOT NULL")
            if col['default_value'] is not None:
                details.append(f"DEFAULT {col['default_value']}")
            
            if details:
                col_desc += f" ({', '.join(details)})"
            
            lines.append(col_desc)
        
        # Add sample data if available
        if table_info.sample_data:
            lines.append("Sample data:")
            for i, row in enumerate(table_info.sample_data, 1):
                sample_line = f"  Row {i}: "
                sample_items = [f"{k}={v}" for k, v in list(row.items())[:5]]  # First 5 columns
                if len(row) > 5:
                    sample_items.append("...")
                sample_line += ", ".join(sample_items)
                lines.append(sample_line)
        
        return "\n".join(lines)
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        if not self._is_safe_query(query):
            raise ValueError("Query contains potentially unsafe operations")
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            # For SELECT queries, return results
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                # For other queries, return affected rows count
                return [{"affected_rows": cursor.rowcount}]
                
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}")
    
    def execute_query_as_dataframe(self, query: str) -> pd.DataFrame:
        """Execute a SQL query and return results as a pandas DataFrame."""
        if not self._is_safe_query(query):
            raise ValueError("Query contains potentially unsafe operations")
        
        try:
            return pd.read_sql_query(query, self.connection)
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}")
    
    def _is_safe_query(self, query: str) -> bool:
        """Check if a query is safe to execute (read-only operations)."""
        query_upper = query.upper().strip()
        
        # Allow SELECT, WITH (for CTEs), and EXPLAIN
        safe_starts = ['SELECT', 'WITH', 'EXPLAIN']
        
        # Check if query starts with safe operations
        starts_safe = any(query_upper.startswith(start) for start in safe_starts)
        
        # Block dangerous keywords
        dangerous_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE',
            'TRUNCATE', 'REPLACE', 'PRAGMA'
        ]
        
        has_dangerous = any(keyword in query_upper for keyword in dangerous_keywords)
        
        return starts_safe and not has_dangerous
    
    def get_column_values(self, table: str, column: str, limit: int = 10) -> List[Any]:
        """Get unique values from a specific column."""
        query = f"SELECT DISTINCT {column} FROM {table} LIMIT {limit};"
        results = self.execute_query(query)
        return [row[column] for row in results]
    
    def search_tables(self, search_term: str) -> List[str]:
        """Search for tables containing the search term."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        # Simple substring search
        matching_tables = [
            table for table in all_tables 
            if search_term.lower() in table.lower()
        ]
        
        return matching_tables
    
    def search_columns(self, search_term: str) -> List[Tuple[str, str]]:
        """Search for columns containing the search term."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        matching_columns = []
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            
            for col_info in columns:
                column_name = col_info[1]
                if search_term.lower() in column_name.lower():
                    matching_columns.append((table, column_name))
        
        return matching_columns
    
    def get_table_relationships(self) -> Dict[str, List[Dict]]:
        """Get foreign key relationships between tables."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        relationships = {}
        
        for table in tables:
            cursor.execute(f"PRAGMA foreign_key_list({table});")
            fk_info = cursor.fetchall()
            
            if fk_info:
                relationships[table] = []
                for fk_row in fk_info:
                    relationships[table].append({
                        'column': fk_row[3],
                        'references_table': fk_row[2],
                        'references_column': fk_row[4]
                    })
        
        return relationships
    
    def validate_query_syntax(self, query: str) -> Tuple[bool, str]:
        """Validate SQL query syntax without executing it."""
        try:
            cursor = self.connection.cursor()
            # Use EXPLAIN QUERY PLAN to validate without execution
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            return True, "Query syntax is valid"
        except Exception as e:
            return False, f"Query syntax error: {e}"
    
    def get_query_suggestions(self, partial_query: str) -> List[str]:
        """Get suggestions for completing a partial query."""
        suggestions = []
        
        # Basic keyword suggestions
        keywords = [
            'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING',
            'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'ON',
            'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'DISTINCT'
        ]
        
        # Get table names
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = [row[0] for row in cursor.fetchall()]
        
        # Simple suggestion logic based on last word
        words = partial_query.split()
        if words:
            last_word = words[-1].upper()
            
            # Suggest keywords
            matching_keywords = [kw for kw in keywords if kw.startswith(last_word)]
            suggestions.extend(matching_keywords)
            
            # Suggest table names after FROM
            if len(words) >= 2 and words[-2].upper() == 'FROM':
                matching_tables = [t for t in table_names if t.upper().startswith(last_word)]
                suggestions.extend(matching_tables)
        
        return suggestions[:10]  # Return top 10 suggestions


def create_sample_data(db_path: str):
    """Create sample Northwind-style data for testing."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create sample tables (simplified Northwind schema)
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS Categories (
        CategoryID INTEGER PRIMARY KEY,
        CategoryName TEXT NOT NULL,
        Description TEXT
    );
    
    CREATE TABLE IF NOT EXISTS Products (
        ProductID INTEGER PRIMARY KEY,
        ProductName TEXT NOT NULL,
        CategoryID INTEGER,
        UnitPrice REAL,
        UnitsInStock INTEGER,
        FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID)
    );
    
    CREATE TABLE IF NOT EXISTS Customers (
        CustomerID TEXT PRIMARY KEY,
        CompanyName TEXT NOT NULL,
        ContactName TEXT,
        Country TEXT,
        City TEXT
    );
    
    CREATE TABLE IF NOT EXISTS Orders (
        OrderID INTEGER PRIMARY KEY,
        CustomerID TEXT,
        OrderDate TEXT,
        ShippedDate TEXT,
        FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
    );
    
    CREATE TABLE IF NOT EXISTS OrderDetails (
        OrderID INTEGER,
        ProductID INTEGER,
        UnitPrice REAL,
        Quantity INTEGER,
        Discount REAL,
        PRIMARY KEY (OrderID, ProductID),
        FOREIGN KEY (OrderID) REFERENCES Orders(OrderID),
        FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
    );
    """)
    
    # Insert sample data
    cursor.executescript("""
    INSERT OR REPLACE INTO Categories VALUES 
    (1, 'Beverages', 'Soft drinks, coffees, teas, beers, and ales'),
    (2, 'Condiments', 'Sweet and savory sauces, relishes, spreads, and seasonings'),
    (3, 'Dairy Products', 'Cheeses');
    
    INSERT OR REPLACE INTO Products VALUES
    (1, 'Chai', 1, 18.00, 39),
    (2, 'Chang', 1, 19.00, 17),
    (3, 'Chef Anton''s Cajun Seasoning', 2, 22.00, 53),
    (4, 'Queso Cabrales', 3, 21.00, 22);
    
    INSERT OR REPLACE INTO Customers VALUES
    ('ALFKI', 'Alfreds Futterkiste', 'Maria Anders', 'Germany', 'Berlin'),
    ('ANATR', 'Ana Trujillo Emparedados y helados', 'Ana Trujillo', 'Mexico', 'México D.F.'),
    ('ANTON', 'Antonio Moreno Taquería', 'Antonio Moreno', 'Mexico', 'México D.F.');
    
    INSERT OR REPLACE INTO Orders VALUES
    (10248, 'ALFKI', '2023-01-01', '2023-01-05'),
    (10249, 'ANATR', '2023-01-02', '2023-01-06'),
    (10250, 'ANTON', '2023-01-03', '2023-01-07');
    
    INSERT OR REPLACE INTO OrderDetails VALUES
    (10248, 1, 18.00, 12, 0.0),
    (10248, 2, 19.00, 10, 0.0),
    (10249, 3, 22.00, 5, 0.0);
    """)
    
    conn.commit()
    conn.close()
    print(f"Sample data created in {db_path}")


if __name__ == "__main__":
    # Test the SQLite tool
    import tempfile
    import os
    
    # Create temporary database with sample data
    with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
        db_path = f.name
    
    create_sample_data(db_path)
    
    # Test the tool
    tool = SQLiteTool(db_path)
    
    print("Schema:")
    print(tool.get_schema())
    
    print("\nQuery results:")
    results = tool.execute_query("SELECT * FROM Products LIMIT 2")
    for row in results:
        print(row)
    
    # Cleanup
    os.unlink(db_path)
