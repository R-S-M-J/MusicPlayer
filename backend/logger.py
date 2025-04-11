""" function to setup log file """
import logging

def setup_logger():
    """
    The function `setup_logger` creates a logger named 'my_logger' that logs messages with level ERROR
    to a file named 'player_log.log'.
    :return: The `setup_logger` function is returning a logger object configured with a file handler
    that logs messages with a specific format to a file named 'player_log.log'. The logger is set to log
    messages with a level of ERROR.
    """

    logger = logging.getLogger('my_logger')
    logger.setLevel(logging.ERROR)

    file_handler = logging.FileHandler('player_log.log')
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        '%(asctime)s - %(filename)s - Line: %(lineno)d - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

# ask chatgpt for handling this properly

"""# in the file u want logging in, 
from backend.logger import setup_logger
logger = setup_logger()
# put this under except block
logger.exception("An error occurred: %s",e)
"""