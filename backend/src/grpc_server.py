from logging import getLogger
import asyncio

import grpc
from concurrent import futures

from speech_hub.auth.v1 import auth_service_pb2_grpc
from src.core.database.db import AsyncSessionLocal
from src.modules.auth.grpc.main import AuthGRPCService

# Initialize logger
logger = getLogger(__name__)

def serve():
    """
    Start the gRPC server.
    """
    # Create a gRPC server with a thread pool executor
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Register services
    # The service will create sessions internally as needed
    auth_service_pb2_grpc.add_AuthServiceServicer_to_server(
        AuthGRPCService(session_factory=AsyncSessionLocal),
        server
    )

    # Serve the server on port 50051
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("gRPC server started on port 50051")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("gRPC server stopping...")
        server.stop(0)
        logger.info("gRPC server stopped.")

if __name__ == "__main__":
    serve()


