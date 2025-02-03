"""Terminal gateway implementation for web-based terminal access."""

from typing import Dict, Optional, Tuple
import subprocess
from dataclasses import dataclass
import asyncio
import os
from pathlib import Path
import logging
import httpx

logger = logging.getLogger(__name__)

@dataclass
class Terminal:
    """Represents a terminal instance."""
    process: subprocess.Popen
    port: int
    path: str
    log_file: Path
    
    def read_logs(self) -> str:
        """Read the ttyd logs for this terminal."""
        try:
            with open(self.log_file, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading logs: {str(e)}"
    
class Terminus:
    """Manages terminal instances and their lifecycle."""
    
    def __init__(self, base_port: int = 7681, debug: bool = False):
        self.terminals: Dict[str, Terminal] = {}
        self.base_port = base_port
        self.ttyd_path = '/home/linuxbrew/.linuxbrew/bin/ttyd'
        self.debug = debug
        
        # Create logs directory
        self.logs_dir = Path('logs')
        self.logs_dir.mkdir(exist_ok=True)
        
    async def create_terminal(self, path: str, command: str = "bash") -> Terminal:
        """Create a new terminal instance."""
        if path in self.terminals:
            raise ValueError(f"Terminal at path {path} already exists")
            
        safe_path = path.replace('/', '_').replace('\\', '_')
        log_file = self.logs_dir / f"ttyd_{safe_path}.log"
        
        self.debug = True # FIXME: Remove this, useful for dev and debug
        
        ttyd_cmd = [
            self.ttyd_path,
            "-W",  # Writable terminal
            "-d", "9" if self.debug else "1",  # More verbose logging in debug mode
            "-i", "127.0.0.1",  # Only listen on localhost
            command
        ]
        
        logger.debug(f"Starting ttyd with command: {' '.join(ttyd_cmd)}")
        
        try:
            process = subprocess.Popen(
                ttyd_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
                start_new_session=True  # Run in new session
            )
            
            # Wait for ttyd to start and capture its port
            port = None
            for _ in range(30):  # Try for 3 seconds (30 * 0.1)
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    raise RuntimeError(f"ttyd failed to start: {stderr}")
                
                line = process.stderr.readline()
                if "Listening on port:" in line:
                    try:
                        port = int(line.split(":")[-1].strip())
                        break
                    except (ValueError, IndexError) as e:
                        raise RuntimeError(f"Failed to parse ttyd port from output: {line}")
                
                await asyncio.sleep(0.1)
            
            if port is None:
                raise RuntimeError("ttyd started but port not found in output")
            
            # Try to connect to verify it's working
            async with httpx.AsyncClient() as client:
                for _ in range(3):  # Try 3 times
                    try:
                        await client.get(f"http://localhost:{port}", timeout=1.0)
                        break
                    except httpx.RequestError:
                        await asyncio.sleep(0.5)
                else:
                    raise RuntimeError(f"ttyd started but not responding on port {port}")
            
            terminal = Terminal(process=process, port=port, path=path, log_file=log_file)
            self.terminals[path] = terminal
            
            asyncio.create_task(self._collect_logs(terminal))
            return terminal
            
        except Exception as e:
            if 'process' in locals():
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            raise RuntimeError(f"Failed to create terminal: {str(e)}")
        
    async def _collect_logs(self, terminal: Terminal) -> None:
        """Collect logs from ttyd process."""
        try:
            with open(terminal.log_file, 'w') as log_file:
                while terminal.process.poll() is None:
                    for pipe, prefix in [(terminal.process.stdout, ''), (terminal.process.stderr, 'ERROR: ')]:
                        if pipe:
                            line = pipe.readline()
                            if line:
                                log_file.write(f"{prefix}{line}")
                                log_file.flush()
                                if self.debug:
                                    logger.debug(f"ttyd[{terminal.path}]: {prefix}{line.strip()}")
                    await asyncio.sleep(0.1)
                
                # Capture any remaining output after process ends
                stdout, stderr = terminal.process.communicate()
                if stdout:
                    log_file.write(stdout)
                    if self.debug:
                        logger.debug(f"ttyd[{terminal.path}] final stdout: {stdout}")
                if stderr:
                    log_file.write(f"ERROR: {stderr}")
                    if self.debug:
                        logger.debug(f"ttyd[{terminal.path}] final stderr: {stderr}")
                log_file.flush()
                
        except Exception as e:
            logger.error(f"Error collecting logs for terminal {terminal.path}: {str(e)}")
        
    async def remove_terminal(self, path: str) -> None:
        """Remove a terminal instance."""
        if terminal := self.terminals.get(path):
            terminal.process.terminate()
            try:
                terminal.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                terminal.process.kill()
            del self.terminals[path]
        
    def get_terminal(self, path: str) -> Optional[Terminal]:
        """Get a terminal instance by path."""
        return self.terminals.get(path)
        
    def list_terminals(self) -> Dict[str, dict]:
        """List all active terminals."""
        return {
            path: {
                "port": term.port,
                "pid": term.process.pid,
                "log_file": str(term.log_file)
            }
            for path, term in self.terminals.items()
        }
        
    def get_logs(self, path: str) -> Optional[str]:
        """Get logs for a specific terminal."""
        if terminal := self.terminals.get(path):
            return terminal.read_logs()
        return None
        
    async def cleanup(self) -> None:
        """Cleanup all terminal instances."""
        for path in list(self.terminals.keys()):
            try:
                await self.remove_terminal(path)
            except Exception as e:
                logger.error(f"Error cleaning up terminal {path}: {str(e)}")
                # Try to force kill if normal cleanup fails
                if terminal := self.terminals.get(path):
                    try:
                        terminal.process.kill()
                        del self.terminals[path]
                    except Exception as e2:
                        logger.error(f"Failed to force kill terminal {path}: {str(e2)}") 