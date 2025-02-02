""" This module contains the routers for the FastAPI application. """

from server.routers.dynamic import router as dynamic
from server.routers.index import router as index

__all__ = ["dynamic", "index"]
