""" Configuration file for the project. """

import os
from dataclasses import dataclass

@dataclass
class ServerConfig:
    """Server configuration settings."""
    host: str = os.getenv("GATEWAY_HOST", "127.0.0.1")
    port: int = int(os.getenv("GATEWAY_PORT", "8181"))

# Global config instance
config = ServerConfig()


