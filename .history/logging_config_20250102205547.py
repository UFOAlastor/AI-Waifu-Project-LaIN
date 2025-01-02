# logging_config.py

import os
import logging
import logging.config


def setup_logging():
    # 确保 logs 目录存在
    log_directory = "logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    LOG_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(module)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "verbose": {
                "format": "%(levelname)s [%(asctime)s]: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
            "file": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/app.log",
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "default",
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "main": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "ui_module": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "vits_module": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "model_module": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "replyParser_module": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }

    # 日志初始化
    logging.config.dictConfig(LOG_CONFIG)
    logging.info("Logging setup complete.")
