"""MCP Server for Snowflake data warehouse."""

import logging
from typing import Any, Dict, List, Optional

try:
    from mcp.types import Tool
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    class Tool:
        def __init__(self, **kwargs):
            pass

from src.mcp.mcp_server import BaseMCPServer

logger = logging.getLogger(__name__)

try:
    import snowflake.connector
    import pandas as pd
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False
    logger.warning("snowflake-connector-python not installed")


class SnowflakeMCPServer(BaseMCPServer):
    """MCP Server for Snowflake data warehouse operations."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize Snowflake MCP server."""
        super().__init__("snowflake_server")
        self.config = config or {}
        self.connection = None
        self.cursor = None
        if SNOWFLAKE_AVAILABLE:
            self._register_tools()

    def _register_tools(self):
        """Register Snowflake tools with MCP server."""
        if not SNOWFLAKE_AVAILABLE:
            logger.warning("Snowflake connector not available, skipping tool registration")
            return

        # Query tool
        query_tool = Tool(
            name="snowflake_query",
            description="Execute SQL query on Snowflake data warehouse",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL query to execute",
                    },
                },
                "required": ["sql"],
            },
        )
        self.register_tool(query_tool)

        # List tables tool
        list_tables_tool = Tool(
            name="snowflake_list_tables",
            description="List all tables in the current schema",
            inputSchema={"type": "object", "properties": {}},
        )
        self.register_tool(list_tables_tool)

        # Get table schema tool
        schema_tool = Tool(
            name="snowflake_get_schema",
            description="Get schema information for a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table",
                    },
                },
                "required": ["table_name"],
            },
        )
        self.register_tool(schema_tool)

    def connect(self):
        """Establish connection to Snowflake."""
        if not SNOWFLAKE_AVAILABLE:
            return False

        try:
            self.connection = snowflake.connector.connect(
                account=self.config.get('account'),
                user=self.config.get('user'),
                password=self.config.get('password'),
                warehouse=self.config.get('warehouse'),
                database=self.config.get('database'),
                schema=self.config.get('schema'),
                role=self.config.get('role', 'ACCOUNTADMIN'),
            )
            self.cursor = self.connection.cursor()
            logger.info(f"Connected to Snowflake account: {self.config.get('account')}")
            return True
        except Exception as e:
            logger.error(f"Snowflake connection failed: {e}")
            return False

    def query(self, sql_query: str) -> List[Dict]:
        """Execute SQL query on Snowflake."""
        if not SNOWFLAKE_AVAILABLE:
            return [{"error": "Snowflake connector not available"}]

        if not self.connection:
            if not self.connect():
                return [{"error": "Failed to connect to Snowflake"}]

        try:
            self.cursor.execute(sql_query)
            columns = [desc[0] for desc in self.cursor.description]
            results = self.cursor.fetchall()
            return [dict(zip(columns, row)) for row in results]
        except Exception as e:
            logger.error(f"Query error: {e}")
            return [{"error": str(e), "query": sql_query}]

    def get_tables(self) -> List[str]:
        """List all tables in the current schema."""
        if not self.config.get('database') or not self.config.get('schema'):
            return []

        query = f"""
        SELECT TABLE_NAME 
        FROM {self.config['database']}.INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = '{self.config['schema']}'
        """
        results = self.query(query)
        return [row['TABLE_NAME'] for row in results if 'TABLE_NAME' in row]

    def get_table_schema(self, table_name: str) -> List[Dict]:
        """Get schema information for a table."""
        if not self.config.get('database') or not self.config.get('schema'):
            return []

        query = f"""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM {self.config['database']}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{self.config['schema']}'
        AND TABLE_NAME = '{table_name}'
        """
        return self.query(query)

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a Snowflake tool."""
        if not self.config:
            return {"error": "Snowflake configuration not provided"}

        if name == "snowflake_query":
            sql = arguments.get("sql", "")
            return {"results": self.query(sql)}

        elif name == "snowflake_list_tables":
            return {"tables": self.get_tables()}

        elif name == "snowflake_get_schema":
            table_name = arguments.get("table_name")
            if not table_name:
                return {"error": "table_name is required"}
            return {"schema": self.get_table_schema(table_name)}

        else:
            raise ValueError(f"Unknown tool: {name}")

    def close(self):
        """Close Snowflake connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def __del__(self):
        """Cleanup on deletion."""
        self.close()

