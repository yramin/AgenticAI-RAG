"""Database query tool with safety checks."""

import logging
from typing import List, Dict, Any, Optional
import re
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from src.core.config import get_settings

logger = logging.getLogger(__name__)


class DatabaseQuery:
    """Database query tool with SQL injection prevention."""

    # Dangerous SQL keywords that should not be allowed
    DANGEROUS_KEYWORDS = {
        "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT",
        "UPDATE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "MERGE",
    }

    # Allowed SQL keywords (SELECT queries only)
    ALLOWED_KEYWORDS = {
        "SELECT", "FROM", "WHERE", "JOIN", "INNER", "LEFT", "RIGHT",
        "FULL", "OUTER", "ON", "GROUP", "BY", "ORDER", "HAVING",
        "LIMIT", "OFFSET", "AS", "AND", "OR", "NOT", "IN", "LIKE",
        "BETWEEN", "IS", "NULL", "DISTINCT", "COUNT", "SUM", "AVG",
        "MAX", "MIN", "CASE", "WHEN", "THEN", "ELSE", "END",
    }

    def __init__(self, database_url: Optional[str] = None):
        """Initialize database query tool."""
        self.settings = get_settings()
        self.database_url = database_url or self.settings.database_url

        if not self.database_url:
            logger.warning("No database URL configured")
            self.engine = None
        else:
            try:
                self.engine = create_engine(self.database_url)
                logger.info(f"Connected to database: {self.database_url.split('@')[-1] if '@' in self.database_url else 'local'}")
            except Exception as e:
                logger.error(f"Error connecting to database: {e}")
                self.engine = None

    def is_safe_query(self, query: str) -> tuple[bool, Optional[str]]:
        """
        Check if a SQL query is safe to execute.

        Args:
            query: SQL query string

        Returns:
            Tuple of (is_safe, error_message)
        """
        query_upper = query.upper().strip()

        # Must start with SELECT
        if not query_upper.startswith("SELECT"):
            return False, "Only SELECT queries are allowed"

        # Check for dangerous keywords
        for keyword in self.DANGEROUS_KEYWORDS:
            if re.search(rf"\b{keyword}\b", query_upper):
                return False, f"Dangerous keyword '{keyword}' is not allowed"

        # Check for semicolons (potential for multiple statements)
        if ";" in query and query.count(";") > 1:
            return False, "Multiple statements not allowed"

        # Check for comments that might hide malicious code
        if "--" in query or "/*" in query:
            return False, "SQL comments are not allowed"

        return True, None

    def query(
        self,
        sql: str,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Execute a safe SELECT query.

        Args:
            sql: SQL SELECT query
            limit: Maximum number of rows to return

        Returns:
            Dictionary with query results
        """
        if not self.engine:
            return {
                "success": False,
                "error": "Database not configured",
                "results": [],
            }

        # Check if query is safe
        is_safe, error = self.is_safe_query(sql)
        if not is_safe:
            return {
                "success": False,
                "error": error,
                "results": [],
            }

        try:
            # Add LIMIT if not present
            sql_upper = sql.upper()
            if "LIMIT" not in sql_upper:
                sql = f"{sql.rstrip(';')} LIMIT {limit}"

            # Execute query
            with self.engine.connect() as connection:
                result = connection.execute(text(sql))
                rows = result.fetchall()
                columns = result.keys()

                # Convert to list of dictionaries
                results = []
                for row in rows:
                    results.append(dict(zip(columns, row)))

                return {
                    "success": True,
                    "results": results,
                    "row_count": len(results),
                    "columns": list(columns),
                }
        except SQLAlchemyError as e:
            logger.error(f"Database query error: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
            }
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
            }

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Get schema information for a table.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with table schema
        """
        if not self.engine:
            return {
                "success": False,
                "error": "Database not configured",
            }

        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(table_name)
            primary_keys = inspector.get_primary_keys(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)

            return {
                "success": True,
                "table": table_name,
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", True),
                    }
                    for col in columns
                ],
                "primary_keys": primary_keys,
                "foreign_keys": [
                    {
                        "name": fk["name"],
                        "constrained_columns": fk["constrained_columns"],
                        "referred_table": fk["referred_table"],
                        "referred_columns": fk["referred_columns"],
                    }
                    for fk in foreign_keys
                ],
            }
        except Exception as e:
            logger.error(f"Error getting table schema: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def list_tables(self) -> List[str]:
        """List all tables in the database."""
        if not self.engine:
            return []

        try:
            inspector = inspect(self.engine)
            return inspector.get_table_names()
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return []

    def get_tool_schema(self) -> Dict[str, Any]:
        """Get tool schema for agent integration."""
        return {
            "name": "database_query",
            "description": "Execute safe SELECT queries on the database",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL SELECT query to execute",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of rows to return (default: 100)",
                        "default": 100,
                    },
                },
                "required": ["sql"],
            },
        }


# Global instance
_database_query: Optional[DatabaseQuery] = None


def get_database_query() -> DatabaseQuery:
    """Get or create the global database query instance."""
    global _database_query
    if _database_query is None:
        _database_query = DatabaseQuery()
    return _database_query

