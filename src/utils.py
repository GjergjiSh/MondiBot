import logging
import os


def configure_logger(name, log_lvl=logging.INFO, log_file='../logs/soundboardbot.log') -> logging.Logger:
    if not os.path.exists(os.path.dirname(log_file)):
        os.makedirs(os.path.dirname(log_file))

    logger = logging.getLogger(name)
    logger.setLevel(log_lvl)
    formatter = logging.Formatter('%(asctime)s: %(levelname)s %(message)s')
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_lvl)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_lvl)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
