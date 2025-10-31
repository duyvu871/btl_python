from logging import getLogger

import grpc
from concurrent import futures

from speech_hub.auth.v1 import auth_service_pb2_grpc
from src.core.database.db import AsyncSessionLocal
from src.modules.auth.grpc.main import AuthGRPCService
from src.modules.user.repository import UserRepository

# Initialize logger
logger = getLogger(__name__)

async def serve():
    """
    Start the gRPC server.
    """
    # Create a gRPC server with a thread pool executor
    server = grpc.server(thread_pool=futures.ThreadPoolExecutor(max_workers=10))

    # serve the server on port 50051
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("gRPC server started on port 50051")
    # Keep the server running
    async with AsyncSessionLocal() as session:
        # register services here
        auth_service_pb2_grpc.add_AuthServiceServicer_to_server(
            AuthGRPCService(
                user_repository=UserRepository(session)
            ),
            server
        )

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("gRPC server stopping...")
        server.stop(0)
        logger.info("gRPC server stopped.")

if __name__ == '__main__':
    serve()



