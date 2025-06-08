import logging
import os

LOG_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}

def get_logger(name="doc_generator"):
    """
    Returns a project-wide logger instance, named per module.
    Controlled via DOCGEN_LOG_LEVEL (.env), default INFO.
    Logs to file if DOCGEN_LOG_TO_FILE is '1'.
    """
    logger = logging.getLogger(name)
    if getattr(logger, "_custom_configured", False):
        return logger

    level_str = os.getenv("DOCGEN_LOG_LEVEL", "INFO").upper()
    level = LOG_LEVELS.get(level_str, logging.INFO)
    logger.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    if os.getenv("DOCGEN_LOG_TO_FILE", "0") == "1":
        log_file = os.getenv("DOCGEN_LOG_FILE", "doc_generator.log")
        if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(fmt)
            logger.addHandler(file_handler)

    logger._custom_configured = True
    return logger

# Quiet googleapiclient discovery logs
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)
logging.getLogger("googleapiclient.discovery").setLevel(logging.ERROR)