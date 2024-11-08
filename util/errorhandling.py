import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')

    log_filename = f"bot_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    log_path = os.path.join('logs', log_filename)

    log_handler = RotatingFileHandler(
        filename=log_path, 
        maxBytes=10**7,
        backupCount=6,
        encoding='utf-8'
    )
    log_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
    log_handler.setFormatter(log_formatter)

    logging.basicConfig(level=logging.INFO, handlers=[log_handler])

    clean_old_logs('logs', 10)

def clean_old_logs(directory, max_logs):
    log_files = sorted(
        [os.path.join(directory, f) for f in os.listdir(directory) if f.startswith("bot_") and f.endswith(".log")],
        key=os.path.getctime,
        reverse=True
    )

    while len(log_files) > max_logs:
        os.remove(log_files.pop())