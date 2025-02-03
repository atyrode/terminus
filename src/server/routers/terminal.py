"""Router for terminal-related endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import logging

from server.state import terminus
from src.console import console

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Only show WARNING and above

router = APIRouter(prefix="/api/terminals", tags=["terminals"])

class TerminalCreate(BaseModel):
    """Request model for terminal creation."""
    path: str
    command: str = "bash"

class TerminalResponse(BaseModel):
    """Response model for terminal information."""
    path: str
    port: int
    pid: int

class LogsResponse(BaseModel):
    """Response model for terminal logs."""
    logs: str | None

@router.post("/", response_model=TerminalResponse)
async def create_terminal(request: TerminalCreate):
    """Create a new terminal instance."""
    try:
        terminal = await terminus.create_terminal(request.path, request.command)
        return TerminalResponse(
            path=terminal.path,
            port=terminal.port,
            pid=terminal.process.pid
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        console.log(f"[[ko]Error[/]]: [bold dark]{str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=Dict[str, dict])
async def list_terminals():
    """List all active terminals."""
    return terminus.list_terminals()

@router.delete("/{path}")
async def remove_terminal(path: str):
    """Remove a terminal instance."""
    if not terminus.get_terminal(path):
        raise HTTPException(status_code=404, detail="Terminal not found")
    await terminus.remove_terminal(path)
    return {"message": "Terminal removed"}

@router.get("/{path}/logs", response_model=LogsResponse)
async def get_terminal_logs(path: str):
    """Get logs for a terminal instance."""
    terminal = terminus.get_terminal(path)
    if not terminal:
        raise HTTPException(status_code=404, detail="Terminal not found")
    
    logs = terminus.get_logs(path)
    return LogsResponse(logs=logs) 