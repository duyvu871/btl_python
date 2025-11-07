import logging
from logging_loki import LokiHandler

logging.basicConfig(
    filename='app.log',
    filemode='a',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('grpc')
logger.setLevel(logging.DEBUG)


# Example log messages
logger.info("Application started successfully.")