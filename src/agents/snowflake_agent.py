"""Snowflake data warehouse agent."""

import logging
from typing import Dict, List, Optional
import json
from src.agents.base_agent import BaseAgent
from src.mcp.snowflake_server import SnowflakeMCPServer

logger = logging.getLogger(__name__)


class SnowflakeAgent(BaseAgent):
    """Agent specialized in querying Snowflake data warehouse."""

    def __init__(self, snowflake_config: Optional[Dict] = None, use_planning: bool = False):
        """Initialize Snowflake agent."""
        super().__init__(
            name="snowflake_agent",
            description=(
                "You are a specialized agent for querying Snowflake data warehouse. "
                "You can convert natural language queries to SQL and execute them "
                "on Snowflake databases."
            ),
            use_memory=True,
            use_planning=use_planning,
        )
        
        # Initialize Snowflake MCP server
        self.snowflake_server = SnowflakeMCPServer(config=snowflake_config)
        self.tables_cache: Optional[List[str]] = None

    def get_available_tables(self) -> List[str]:
        """Cache and return available tables."""
        if not self.tables_cache:
            try:
                self.tables_cache = self.snowflake_server.get_tables()
            except Exception as e:
                logger.error(f"Error getting tables: {e}")
                self.tables_cache = []
        return self.tables_cache

    def get_context_for_query(self, user_query: str) -> str:
        """Build context about available tables and schemas."""
        try:
            tables = self.get_available_tables()
            
            if not tables:
                return "No tables available in Snowflake database."
            
            # Get schema for relevant tables (limit to avoid token overflow)
            context = "Available Snowflake tables:\n\n"
            for table in tables[:10]:  # Limit to first 10 tables
                try:
                    schema = self.snowflake_server.get_table_schema(table)
                    context += f"Table: {table}\n"
                    if schema:
                        context += "Columns: " + ", ".join([
                            f"{col.get('COLUMN_NAME', 'unknown')} ({col.get('DATA_TYPE', 'unknown')})"
                            for col in schema[:5]  # First 5 columns
                        ]) + "\n\n"
                    else:
                        context += "Columns: (schema not available)\n\n"
                except Exception as e:
                    logger.warning(f"Error getting schema for {table}: {e}")
                    context += f"Table: {table}\nColumns: (error retrieving schema)\n\n"
            
            return context
        except Exception as e:
            logger.error(f"Error building context: {e}")
            return f"Error building context: {str(e)}"

    def natural_language_to_sql(self, user_query: str) -> str:
        """Convert natural language query to SQL using LLM."""
        context = self.get_context_for_query(user_query)
        
        prompt = f"""You are a Snowflake SQL expert. Convert this natural language query to SQL.

Database context:
{context}

User query: {user_query}

Requirements:
1. Generate ONLY valid Snowflake SQL
2. Use proper table and column names from the context
3. Include appropriate filters and aggregations
4. Limit results to 100 rows for safety
5. Return ONLY the SQL query, no explanation

SQL Query:"""

        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a Snowflake SQL expert. Generate only valid SQL queries.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,  # Lower temperature for more deterministic SQL
            )

            sql = response.choices[0].message.content.strip()
            
            # Clean up any markdown code blocks
            sql = sql.replace("```sql", "").replace("```", "").strip()
            
            return sql
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            raise

    async def retrieve_context(self, query: str) -> str:
        """
        Retrieve relevant context from Snowflake.

        Args:
            query: User query

        Returns:
            Context string from Snowflake
        """
        try:
            # Get available tables context
            context = self.get_context_for_query(query)
            
            # If query seems to be asking for data, try to generate and execute SQL
            if any(keyword in query.lower() for keyword in ['show', 'list', 'get', 'find', 'select']):
                try:
                    sql = self.natural_language_to_sql(query)
                    results = self.snowflake_server.query(sql)
                    
                    if results and not any('error' in str(r).lower() for r in results):
                        # Format results for context
                        context += f"\n\nQuery Results:\n"
                        context += json.dumps(results[:5], indent=2)  # First 5 rows
                except Exception as e:
                    logger.warning(f"Could not execute query for context: {e}")
            
            return context
        except Exception as e:
            logger.error(f"Error retrieving Snowflake context: {e}")
            return f"Error retrieving Snowflake context: {str(e)}"

    async def process(
        self,
        query: str,
        session_id: Optional[str] = None,
        context: Optional[str] = None,
    ) -> dict:
        """
        Process query with Snowflake data warehouse.

        Args:
            query: User query
            session_id: Optional session ID
            context: Optional additional context

        Returns:
            Response dictionary
        """
        try:
            # Convert natural language to SQL
            sql_query = self.natural_language_to_sql(query)
            
            logger.info(f"Generated SQL: {sql_query}")
            
            # Execute query
            results = self.snowflake_server.query(sql_query)
            
            # Check for errors
            if results and isinstance(results, list) and len(results) > 0:
                if isinstance(results[0], dict) and 'error' in results[0]:
                    return {
                        "success": False,
                        "error": results[0].get('error', 'Unknown error'),
                        "sql_query": sql_query,
                        "agent": self.name,
                    }
            
            # Format results for LLM
            summary = await self._summarize_results(query, results)
            
            # Build full context with results
            snowflake_context = f"SQL Query: {sql_query}\n\nResults ({len(results)} rows):\n{json.dumps(results[:10], indent=2)}"
            full_context = f"{context}\n\n{snowflake_context}" if context else snowflake_context
            
            # Process using base agent
            return await super().process(query, session_id, full_context)
            
        except Exception as e:
            logger.error(f"Error processing Snowflake query: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
            }

    async def _summarize_results(self, query: str, results: List[Dict]) -> str:
        """Use LLM to summarize query results."""
        if not results:
            return "No results found."

        # Convert results to readable format
        results_text = json.dumps(results[:10], indent=2)

        prompt = f"""Summarize these Snowflake query results for the user.

Original question: {query}
Number of results: {len(results)}

Sample data:
{results_text}

Provide a clear, concise summary of the findings."""

        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes database query results.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error summarizing results: {e}")
            return f"Found {len(results)} results. (Summary generation failed: {str(e)})"
