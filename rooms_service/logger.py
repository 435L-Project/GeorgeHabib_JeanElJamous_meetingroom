import logging
import os

def setup_logger():
    """
    Configures a logger to wrtie audit events to a file and the console

    :return: Configured logger instance.
    :rtype: logging.Logger
    """
    logger= logging.getLogger('audit_logger')
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # file handler
        file_handler = logging.FileHandler('audit.log')
        file_handler.setLevel(logging.INFO)

        # console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


audit_logger = setup_logger()