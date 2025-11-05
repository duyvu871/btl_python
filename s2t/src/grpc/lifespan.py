"""
gRPC Clients Lifecycle Manager

This module provides lifecycle management for all gRPC clients.
"""
import logging
from contextlib import asynccontextmanager

from src.grpc.auth_client import AuthGRPCClient
# from src.grpc.speech_client import SpeechGRPCClient

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan_grpc_clients(app):
    """
    FastAPI lifespan context manager to manage all gRPC clients lifecycle.
    """
    # Startup - Connect to all gRPC services
    logger.info("=" * 60)
    logger.info("Starting gRPC clients...")
    logger.info("=" * 60)
    
    clients = []
    
    try:
        # Connect Auth client
        auth_client = AuthGRPCClient.get_instance()
        await auth_client.connect()
        clients.append(("Auth", auth_client))
        logger.info("✓ Auth gRPC client connected")
        
        # Connect Speech client (when available)
        speech_client = SpeechGRPCClient.get_instance()
        await speech_client.connect()
        clients.append(("Speech", speech_client))
        logger.info("✓ Speech gRPC client connected")

        logger.info("=" * 60)
        logger.info(f"All {len(clients)} gRPC clients started successfully")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Failed to start gRPC clients: {e}")
        # Cleanup already connected clients
        for name, client in clients:
            try:
                await client.disconnect()
                logger.info(f"✓ {name} gRPC client disconnected (cleanup)")
            except Exception as cleanup_error:
                logger.error(f"Failed to disconnect {name} client: {cleanup_error}")
        raise
    
    yield
    name
    # Shutdown - Disconnect from all gRPC services
    logger.info("=" * 60)
    logger.info("Stopping gRPC clients...")
    logger.info("=" * 60)
    
    for name, client in clients:
        try:
            await client.disconnect()
            logger.info(f"✓ {name} gRPC client disconnected")
        except Exception as e:
            logger.error(f"Failed to disconnect {name} client: {e}")
    
    logger.info("=" * 60)
    logger.info("All gRPC clients stopped")
    logger.info("=" * 60)

