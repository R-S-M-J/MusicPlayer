import logging

def setup_logger():
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
