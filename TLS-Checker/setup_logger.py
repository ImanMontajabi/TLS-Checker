import os
import json
import atexit
import logging.config
import logging.handlers


this_path: str = os.getcwd()


def setup_logger_for_this_file():
    """
    This function initiates logger using dict_config file by dictConfig method
    """

    config_file: str = os.path.join(this_path, 'logger_config.json')
    with open(config_file) as f:
        config = json.load(f)

    logging.config.dictConfig(config)
    queue_handler = logging.getHandlerByName('queue_handler')
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)
