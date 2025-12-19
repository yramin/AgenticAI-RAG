"""API routes."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.core.orchestrator import get_orchestrator
from src.memory.long_term_memory import LongTermMemory

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response models
class QueryRequest(BaseModel):
    """Query request model."""
    query: str
    tier: str = "basic"  # "basic", "agent", or "advanced"
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Query response model."""
    success: bool
    answer: Optional[str] = None
    tier: str
    error: Optional[str] = None
    sources: Optional[list] = None
    model: Optional[str] = None
    agent: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
    }


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Main query endpoint supporting all tiers.

    - **basic**: Simple RAG (retrieval + generation)
    - **agent**: Agent with tools (calculator, web search, database)
    - **advanced**: Multi-agent system with MCP servers
    """
    try:
        orchestrator = get_orchestrator()
        response = await orchestrator.process_query(
            query=request.query,
            tier=request.tier,
            session_id=request.session_id,
        )

        return QueryResponse(**response)

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def get_agents():
    """Get status of all agents."""
    try:
        orchestrator = get_orchestrator()
        status = orchestrator.get_agent_status()
        return status
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system")
async def get_system_info():
    """Get system information."""
    try:
        orchestrator = get_orchestrator()
        info = orchestrator.get_system_info()
        return info
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/{session_id}")
async def get_memory(session_id: str):
    """Get memory for a session."""
    try:
        long_term_memory = LongTermMemory()
        memories = long_term_memory.get_session_memories(session_id, limit=50)
        return {
            "session_id": session_id,
            "memories": memories,
            "count": len(memories),
        }
    except Exception as e:
        logger.error(f"Error getting memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/{session_id}")
async def delete_memory(session_id: str):
    """Delete memory for a session."""
    try:
        long_term_memory = LongTermMemory()
        deleted_count = long_term_memory.delete_session_memories(session_id)
        return {
            "session_id": session_id,
            "deleted": deleted_count,
        }
    except Exception as e:
        logger.error(f"Error deleting memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

