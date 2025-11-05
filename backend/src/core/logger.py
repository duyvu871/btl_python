import logging
from logging_loki import LokiHandler

from src.core.config.env import env, global_logger_name

logging.basicConfig(
    filename='app.log',
    filemode='a',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configure the logger
logger = logging.getLogger(global_logger_name)
logger.setLevel(logging.DEBUG)

# Define Loki connection details
LOKI_URL = env.LOKI_URL  # Replace with your Loki instance URL
ENABLE_LOKI = env.ENABLE_LOKI_LOGGING
LABELS = {"application": "my_python_app", "environment": "development"}

# Create and add the LokiHandler
if ENABLE_LOKI and LOKI_URL:
    handler = LokiHandler(url=LOKI_URL, tags=LABELS)
    logger.addHandler(handler)

# Example log messages
logger.info("Application started successfully.")