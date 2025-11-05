#!/usr/bin/env python3
"""
Development wrapper for gRPC server with auto-reload.
Uses watchfiles to monitor file changes and restart the server.
"""
import sys
import logging
from pathlib import Path
from src.grpc_server import serve

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run():
    """
    Import and run the gRPC server.
    This allows watchfiles to restart the entire process on changes.
    """

    logger.info("Starting gRPC server with auto-reload enabled...")
    try:
        serve()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server...")
        sys.exit(0)

if __name__ == "__main__":
    run()

