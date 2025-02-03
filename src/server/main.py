""" Main module for the FastAPI application. """

import os
import asyncio
import logging
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, WebSocket
from fastapi.responses import HTMLResponse, Response, JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.websockets import WebSocketDisconnect
import websockets

from src.main import Terminus
from server.routers import terminal
from server.utils import lifespan, limiter, rate_limit_exception_handler
from server.state import terminus

# Load environment variables from .env file
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "WARNING"))

# Initialize the FastAPI application with lifespan
app = FastAPI(
    lifespan=lifespan,
    # Disable FastAPI's default logging of all requests
    docs_url=None if os.getenv("ENVIRONMENT", "production") == "production" else "/docs",
    redoc_url=None if os.getenv("ENVIRONMENT", "production") == "production" else "/redoc"
)
app.state.limiter = limiter

# Register the custom exception handler for rate limits
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)

# Set up API analytics middleware if an API key is provided
if app_analytics_key := os.getenv("API_ANALYTICS_KEY"):
    app.add_middleware(Analytics, api_key=app_analytics_key)

# Fetch allowed hosts from the environment or use the default values
allowed_hosts = os.getenv("ALLOWED_HOSTS")
if allowed_hosts:
    allowed_hosts = allowed_hosts.split(",")
else:
    # Define the default allowed hosts for the application
    default_allowed_hosts = ["terminus.run", "*.terminus.run", "localhost", "127.0.0.1"]
    allowed_hosts = default_allowed_hosts

# Add middleware to enforce allowed hosts
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint to verify that the server is running.

    Returns
    -------
    dict[str, str]
        A JSON object with a "status" key indicating the server's health status.
    """
    return {"status": "healthy"}


@app.head("/")
async def head_root() -> HTMLResponse:
    """
    Respond to HTTP HEAD requests for the root URL.

    Mirrors the headers and status code of the index page.

    Returns
    -------
    HTMLResponse
        An empty HTML response with appropriate headers.
    """
    return HTMLResponse(content=None, headers={"content-type": "text/html; charset=utf-8"})


@app.get("/terminals/{path}")
async def get_terminal(path: str, request: Request):
    """
    Proxy the ttyd web interface for the requested terminal.
    
    Parameters
    ----------
    path : str
        The terminal path/ID
    request : Request
        The FastAPI request object
        
    Returns
    -------
    Response
        The proxied ttyd web interface content
    """
    terminal = terminus.get_terminal(path)
    if not terminal:
        raise HTTPException(status_code=404, detail="Terminal not found")
    
    try:
        # Create a client session to fetch the ttyd interface
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:{terminal.port}",
                headers={
                    "Accept": request.headers.get("accept", "*/*"),
                    "Accept-Encoding": request.headers.get("accept-encoding", "")
                },
                follow_redirects=True
            )
            
            # Copy all relevant headers from the ttyd response
            headers = {
                k: v for k, v in response.headers.items()
                if k.lower() in {
                    "content-type", "content-length", "cache-control",
                    "etag", "last-modified"
                }
            }
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=headers
            )
    except httpx.RequestError as e:
        logger.error(f"Error proxying terminal {path}: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Error connecting to terminal: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error proxying terminal {path}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/terminals/{path}/token")
async def get_terminal_token(path: str):
    """
    Get the token for the ttyd WebSocket connection.
    """
    terminal = terminus.get_terminal(path)
    if not terminal:
        raise HTTPException(status_code=404, detail="Terminal not found")
    
    # ttyd doesn't actually require a real token, it just needs the endpoint to exist
    return JSONResponse({"token": "dummy-token"})

@app.websocket("/terminals/{path}/ws")
async def terminal_websocket(websocket: WebSocket, path: str):
    """
    Proxy WebSocket connection to ttyd.
    """
    terminal = terminus.get_terminal(path)
    if not terminal:
        logger.warning(f"WebSocket connection attempt to non-existent terminal: {path}")
        await websocket.close(code=4004)
        return

    await websocket.accept()
    logger.debug(f"WebSocket connection accepted for terminal {path}")
    
    try:
        # Connect to the ttyd WebSocket with the correct subprotocols
        uri = f"ws://localhost:{terminal.port}/ws"
        logger.debug(f"Connecting to ttyd WebSocket at {uri}")
        
        async with websockets.connect(uri, subprotocols=['tty']) as ttyd_ws:
            logger.debug(f"Connected to ttyd WebSocket for terminal {path}")
            
            # Create tasks for bidirectional communication
            async def forward_to_ttyd():
                try:
                    while True:
                        try:
                            # Receive any type of message (text/binary)
                            message = await websocket.receive()
                            if 'text' in message:
                                await ttyd_ws.send(message['text'])
                                if terminal.debug:
                                    logger.debug(f"Forwarded text to ttyd[{path}]: {message['text'][:50]}...")
                            elif 'bytes' in message:
                                await ttyd_ws.send(message['bytes'])
                                if terminal.debug:
                                    logger.debug(f"Forwarded {len(message['bytes'])} bytes to ttyd[{path}]")
                        except (WebSocketDisconnect, RuntimeError) as e:
                            logger.debug(f"Client disconnected from terminal {path}: {str(e)}")
                            return
                except Exception as e:
                    logger.error(f"Error in forward_to_ttyd for terminal {path}: {str(e)}")
                    return

            async def forward_from_ttyd():
                try:
                    while True:
                        try:
                            message = await ttyd_ws.recv()
                            try:
                                if isinstance(message, str):
                                    await websocket.send_text(message)
                                    if terminal.debug:
                                        logger.debug(f"Forwarded text from ttyd[{path}]: {message[:50]}...")
                                else:
                                    await websocket.send_bytes(message)
                                    if terminal.debug:
                                        logger.debug(f"Forwarded {len(message)} bytes from ttyd[{path}]")
                            except (WebSocketDisconnect, RuntimeError):
                                logger.debug(f"Client disconnected while sending from ttyd[{path}]")
                                return
                        except websockets.ConnectionClosed:
                            logger.debug(f"ttyd connection closed for terminal {path}")
                            return
                except Exception as e:
                    logger.error(f"Error in forward_from_ttyd for terminal {path}: {str(e)}")
                    return

            # Run both forwarding tasks concurrently
            forward_task = asyncio.create_task(forward_to_ttyd())
            backward_task = asyncio.create_task(forward_from_ttyd())
            
            # Wait for either task to complete (connection closed from either end)
            done, pending = await asyncio.wait(
                [forward_task, backward_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel the remaining task
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                
    except Exception as e:
        logger.error(f"WebSocket error for terminal {path}: {str(e)}")
    finally:
        try:
            await websocket.close()
            logger.debug(f"Closed WebSocket connection for terminal {path}")
        except:
            pass

# Include terminal router for API endpoints
app.include_router(terminal)

# Update lifespan to handle terminal cleanup
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    try:
        # Cleanup all terminals
        await terminus.cleanup()
        # Cancel all running tasks
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
