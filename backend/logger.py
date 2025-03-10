import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    logger = logging.getLogger('PDFChat')
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File Handler
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger