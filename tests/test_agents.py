"""Unit tests for agents."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.agents.local_data_agent import LocalDataAgent
from src.agents.search_agent import SearchAgent
from src.agents.cloud_agent import CloudAgent
from src.agents.aggregator_agent import AggregatorAgent


@pytest.fixture
def mock_vector_store():
    """Mock vector store."""
    mock_store = Mock()
    mock_store.search.return_value = {
        "documents": ["Test document content"],
        "ids": ["doc1"],
        "metadatas": [{"source": "test"}],
        "distances": [0.1],
    }
    return mock_store


@pytest.fixture
def mock_web_search():
    """Mock web search."""
    mock_search = AsyncMock()
    mock_search.search.return_value = {
        "success": True,
        "results": [
            {
                "title": "Test Result",
                "url": "https://example.com",
                "content": "Test content",
            }
        ],
    }
    return mock_search


class TestLocalDataAgent:
    """Tests for LocalDataAgent."""

    @pytest.mark.asyncio
    async def test_retrieve_context(self, mock_vector_store):
        """Test context retrieval."""
        with patch("src.agents.local_data_agent.get_vector_store", return_value=mock_vector_store):
            agent = LocalDataAgent()
            context = await agent.retrieve_context("test query")
            assert "Test document content" in context
            assert "test" in context

    @pytest.mark.asyncio
    async def test_process_query(self, mock_vector_store):
        """Test query processing."""
        with patch("src.agents.local_data_agent.get_vector_store", return_value=mock_vector_store):
            with patch.object(LocalDataAgent, "_process_direct", new_callable=AsyncMock) as mock_process:
                mock_process.return_value = {
                    "success": True,
                    "answer": "Test answer",
                    "agent": "local_data_agent",
                }
                agent = LocalDataAgent()
                response = await agent.process("test query")
                assert response["success"] is True
                assert "answer" in response


class TestSearchAgent:
    """Tests for SearchAgent."""

    @pytest.mark.asyncio
    async def test_retrieve_context(self, mock_web_search):
        """Test web search context retrieval."""
        with patch("src.agents.search_agent.get_web_search", return_value=mock_web_search):
            agent = SearchAgent(use_planning=False)
            agent.web_search = mock_web_search
            context = await agent.retrieve_context("test query")
            assert "Test Result" in context or "test query" in context.lower()

    @pytest.mark.asyncio
    async def test_process_query(self, mock_web_search):
        """Test query processing with web search."""
        with patch("src.agents.search_agent.get_web_search", return_value=mock_web_search):
            with patch.object(SearchAgent, "_process_direct", new_callable=AsyncMock) as mock_process:
                mock_process.return_value = {
                    "success": True,
                    "answer": "Test answer from web",
                    "agent": "search_agent",
                }
                agent = SearchAgent(use_planning=False)
                agent.web_search = mock_web_search
                response = await agent.process("test query")
                assert response["success"] is True


class TestCloudAgent:
    """Tests for CloudAgent."""

    @pytest.mark.asyncio
    async def test_retrieve_context_no_config(self):
        """Test context retrieval when cloud is not configured."""
        agent = CloudAgent()
        context = await agent.retrieve_context("test query")
        assert "not configured" in context.lower()

    @pytest.mark.asyncio
    async def test_process_query(self):
        """Test query processing."""
        with patch.object(CloudAgent, "_process_direct", new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {
                "success": True,
                "answer": "Test answer",
                "agent": "cloud_agent",
            }
            agent = CloudAgent()
            response = await agent.process("test query")
            assert response["success"] is True


class TestAggregatorAgent:
    """Tests for AggregatorAgent."""

    @pytest.mark.asyncio
    async def test_select_agents(self):
        """Test agent selection logic."""
        agent = AggregatorAgent(use_planning=False)
        
        # Test local document query
        selected = agent._select_agents("What is in the document?")
        assert "local" in selected

        # Test web search query
        selected = agent._select_agents("What is the latest news?")
        assert "search" in selected

        # Test cloud query
        selected = agent._select_agents("What files are in S3?")
        assert "cloud" in selected

    @pytest.mark.asyncio
    async def test_process_query(self):
        """Test query processing with multiple agents."""
        with patch.object(LocalDataAgent, "process", new_callable=AsyncMock) as mock_local:
            mock_local.return_value = {
                "success": True,
                "answer": "Local answer",
            }
            with patch.object(SearchAgent, "process", new_callable=AsyncMock) as mock_search:
                mock_search.return_value = {
                    "success": True,
                    "answer": "Search answer",
                }
                agent = AggregatorAgent(use_planning=False)
                agent.local_agent.process = mock_local
                agent.search_agent.process = mock_search
                
                with patch.object(agent, "_synthesize_responses", new_callable=AsyncMock) as mock_synth:
                    mock_synth.return_value = {
                        "success": True,
                        "answer": "Synthesized answer",
                        "aggregated_by": "multiple_agents",
                    }
                    response = await agent.process("test query")
                    assert response["success"] is True
                    assert "aggregated_by" in response

    @pytest.mark.asyncio
    async def test_synthesize_responses(self):
        """Test response synthesis."""
        agent = AggregatorAgent(use_planning=False)
        
        agent_responses = {
            "local": {"success": True, "answer": "Answer 1"},
            "search": {"success": True, "answer": "Answer 2"},
        }

        with patch.object(agent.client.chat.completions, "create") as mock_llm:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Synthesized answer"
            mock_llm.return_value = mock_response

            result = await agent._synthesize_responses(
                query="test",
                agent_responses=agent_responses,
                session_id=None,
            )

            assert result["success"] is True
            assert "Synthesized answer" in result["answer"]


class TestBaseAgent:
    """Tests for BaseAgent functionality."""

    @pytest.mark.asyncio
    async def test_agent_status(self):
        """Test agent status retrieval."""
        agent = LocalDataAgent()
        status = agent.get_status()
        assert status["name"] == "local_data_agent"
        assert "tools" in status
        assert "memory_enabled" in status

    def test_add_tool(self):
        """Test adding tools to agent."""
        agent = LocalDataAgent()
        tool_schema = {
            "name": "test_tool",
            "description": "Test tool",
        }
        tool_func = lambda x: x

        agent.add_tool(tool_schema, tool_func)
        assert "test_tool" in agent.tool_functions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

