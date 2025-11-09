import asyncio
from logging import getLogger

import grpc.aio

from speech_hub.auth.v1 import auth_service_pb2_grpc
from src.core.config.env import global_logger_name
from src.core.database.db import AsyncSessionLocal
from src.modules.auth.grpc.handler import AuthGRPCService

# Initialize logger
logger = getLogger(global_logger_name)

async def serve():
    """
    Start the gRPC server.
    """
    # Create a gRPC server with a thread pool executor
    server = grpc.aio.server()

    # Register services
    # The service will create sessions internally as needed
    auth_service_pb2_grpc.add_AuthServiceServicer_to_server(
        AuthGRPCService(session_factory=AsyncSessionLocal),
        server
    )

    # Serve the server on port 50051
    server.add_insecure_port('[::]:50051')
    await server.start()
    logger.info("gRPC server started on port 50051")

    try:
        await server.wait_for_termination()
    finally:
        logger.info("gRPC server stopping...")
        await server.stop(0)
        logger.info("gRPC server stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        logger.info("gRPC server stopped.")
