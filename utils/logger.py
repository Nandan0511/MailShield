
import logging
import os

# ---------------------------------------------------
# LOG FILE PATH
# ---------------------------------------------------
LOG_PATH = os.path.join(
    os.getcwd(),
    "mailshield.log"
)

# ---------------------------------------------------
# CREATE LOGGER
# ---------------------------------------------------
logger = logging.getLogger("MailShield")

logger.setLevel(logging.INFO)

# avoid duplicate handlers
if not logger.handlers:

    file_handler = logging.FileHandler(
        LOG_PATH,
        encoding="utf-8"
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

# ---------------------------------------------------
# INFO LOGGER
# ---------------------------------------------------
def log_info(message):

    logger.info(message)

    for handler in logger.handlers:
        handler.flush()

# ---------------------------------------------------
# ERROR LOGGER
# ---------------------------------------------------
def log_error(message):

    logger.error(message)

    for handler in logger.handlers:
        handler.flush()
