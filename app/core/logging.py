import logging
import sys

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configures application-wide logging format and level."""
    logging_level = getattr(logging, log_level.upper(), logging.INFO)
    
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    logger = logging.getLogger("ai_content_platform")
    logger.setLevel(logging_level)
    
    # Avoid adding duplicate handlers if re-initialized
    if not logger.handlers:
        logger.addHandler(handler)
        
    return logger

logger = setup_logging()
