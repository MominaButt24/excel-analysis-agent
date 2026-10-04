import logging
import os
import sys


class ReadableFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.DEBUG: "\033[36m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[1;31m",
    }
    RESET = "\033[0m"
    DIM = "\033[2m"
    CYAN = "\033[36m"

    def __init__(self):
        super().__init__(datefmt="%Y-%m-%d %H:%M:%S")
        self.use_colors = "NO_COLOR" not in os.environ

    def format(self, record):
        timestamp = self.formatTime(record, self.datefmt)
        level = f"{record.levelname:<8}"
        logger_name = record.name
        message = record.getMessage()

        if self.use_colors:
            level_color = self.LEVEL_COLORS.get(record.levelno, "")
            timestamp = f"{self.DIM}{timestamp}{self.RESET}"
            level = f"{level_color}{level}{self.RESET}"
            logger_name = f"{self.CYAN}{logger_name}{self.RESET}"

        formatted = f"{timestamp} │ {level} │ {logger_name} │ {message}"
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        if record.stack_info:
            formatted += "\n" + self.formatStack(record.stack_info)
        return formatted


def configure_logging():
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    for logger_name in ("httpx", "httpcore"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    if not any(
        getattr(handler, "_excel_agent_handler", False)
        for handler in root_logger.handlers
    ):
        handler = logging.StreamHandler(sys.stdout)
        handler._excel_agent_handler = True
        handler.setFormatter(ReadableFormatter())
        root_logger.addHandler(handler)

    return logging.getLogger("excel_analysis_agent")