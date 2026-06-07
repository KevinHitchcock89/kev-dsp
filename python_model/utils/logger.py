import os
import logging
from colorama import Fore, Style, just_fix_windows_console


just_fix_windows_console() 

class ColorFormatter(logging.Formatter):
    # Using Colorama's built-in constants is safer than raw ANSI strings
    FORMATS = {
        logging.DEBUG:    f"{Fore.GREEN}[%(levelname)s] %(filename)s:%(lineno)d:{Style.RESET_ALL} %(message)s",
        logging.INFO:     f"{Fore.GREEN}[%(levelname)s] %(filename)s:%(lineno)d:{Style.RESET_ALL} %(message)s",
        logging.WARNING:  f"{Fore.YELLOW}[%(levelname)s] %(filename)s:%(lineno)d:{Style.RESET_ALL} %(message)s",
        logging.ERROR:    f"{Fore.RED}[%(levelname)s] %(filename)s:%(lineno)d:{Style.RESET_ALL} %(message)s",
        logging.CRITICAL: f"{Style.BRIGHT}{Fore.RED}[%(levelname)s] %(filename)s:%(lineno)d:{Style.RESET_ALL} %(message)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def get_logger(name: str = "python_model"):
    logger = logging.getLogger(name)

    if not logger.handlers:  # prevents duplicate handlers
        handler = logging.StreamHandler()
        handler.setFormatter(ColorFormatter())
        logger.addHandler(handler)

        log_level = os.environ.get("LOGLEVEL", "INFO").upper()
        logger.setLevel(log_level)

    return logger
