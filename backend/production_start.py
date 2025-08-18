#!/usr/bin/env python3
"""
Production-level startup script for Doc KB backend server.
Comprehensive error handling, health checks, and monitoring.
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from loguru import logger

# Set environment variables
os.environ["MODEL_NAME"] = "jinaai/jina-embeddings-v3"

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class ProductionServer:
    """Production server with comprehensive error handling."""
    
    def __init__(self):
        self.server_process = None
        self.is_running = False
        
    def setup_logging(self):
        """Setup production logging."""
        # Remove default handler
        logger.remove()
        
        # Add production handlers
        logger.add(
            "logs/app.log",
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            level="INFO"
        )
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO"
        )
    
    def health_check(self) -> bool:
        """Perform health check on ChromaDB."""
        try:
            from production_chroma_client import get_chroma_manager
            manager = get_chroma_manager()
            
            # Test basic operations
            collections = manager.list_collections()
            logger.info(f"Health check passed - Found {len(collections)} collections")
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def preflight_checks(self) -> bool:
        """Perform preflight checks before starting server."""
        logger.info("🔍 Performing preflight checks...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            logger.error("Python 3.8+ required")
            return False
        
        # Check required directories
        required_dirs = ["data", "logs"]
        for dir_name in required_dirs:
            Path(dir_name).mkdir(exist_ok=True)
        
        # Check ChromaDB
        if not self.health_check():
            logger.error("ChromaDB health check failed")
            return False
        
        logger.info("✅ Preflight checks passed")
        return True
    
    def start_server(self):
        """Start the production server."""
        try:
            logger.info("🚀 Starting production server...")
            
            # Start uvicorn server
            cmd = [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--workers", "1",
                "--log-level", "info"
            ]
            
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            self.is_running = True
            logger.info(f"✅ Server started with PID: {self.server_process.pid}")
            
            # Monitor server output
            for line in iter(self.server_process.stdout.readline, ''):
                if line:
                    logger.info(f"SERVER: {line.strip()}")
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            self.is_running = False
    
    def stop_server(self):
        """Stop the production server."""
        if self.server_process and self.is_running:
            logger.info("🛑 Stopping server...")
            self.server_process.terminate()
            
            try:
                self.server_process.wait(timeout=10)
                logger.info("✅ Server stopped gracefully")
            except subprocess.TimeoutExpired:
                logger.warning("⚠️  Server didn't stop gracefully, forcing...")
                self.server_process.kill()
            
            self.is_running = False
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop_server()
        sys.exit(0)
    
    def run(self):
        """Run the production server."""
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Setup logging
        self.setup_logging()
        
        logger.info("🚀 Starting Doc KB Production Server...")
        logger.info("📁 Using local ChromaDB storage")
        logger.info("🤖 Using embedding model: jinaai/jina-embeddings-v3")
        logger.info("=" * 50)
        
        # Perform preflight checks
        if not self.preflight_checks():
            logger.error("❌ Preflight checks failed, exiting")
            sys.exit(1)
        
        # Start server
        try:
            self.start_server()
        except KeyboardInterrupt:
            logger.info("Received interrupt, shutting down...")
        finally:
            self.stop_server()

def main():
    """Main entry point."""
    server = ProductionServer()
    server.run()

if __name__ == "__main__":
    main()